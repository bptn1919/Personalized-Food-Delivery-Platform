from uuid import UUID
from dish.models import Dish
from order.models import Order
from order.orm.order import OrderORM, OrderMapper
from cart.orm.cart import CartORM
from order.services.shipping_service import AhamoveAdapter
from profile.orm.profile import CustomerORM
from dish.orm.dish import DishORM
from exceptions.orders import OrderNotFoundException
from exceptions.carts import CartItemNotFoundException
from exceptions.profiles import CustomerAddressNotFoundException
from utils.types import TUser
from django.utils import timezone
from datetime import timedelta
from order.schemas.requests import PersonalInfoSchema, FilterOrderSchema, OrderByOrderSchema, UpdateDeliveryTypesPayload
from utils.enums import DeliveryTypeEnum, PaymentMethodEnum, OrderStatusEnum, PaymentStatus, VoucherTypeEnum, VoucherReservationStatus
from datetime import time
from django.db import transaction, models
from ninja.errors import HttpError
from cart.services import CartService
from payment.services import PaymentService
from decimal import Decimal
from typing import Optional
from order.services.order_state_machine import OrderStateMachine
from voucher.services import VoucherService
from voucher.models import AppliedVoucher
from exceptions.vouchers import VoucherInvalidException
from collections import defaultdict
from order.schemas.responses import ChefOrderGroupResponse, ChefInfoSchema, OrderListResponse
from exceptions.dishes import DishNotFoundInOrderException
from django.db.models import Sum

class OrderService:
    def __init__(self):
        self.orm = OrderORM()
        self.cart_orm = CartORM()
        self.customer_orm = CustomerORM()
        self.cart_service = CartService()
        self.payment_service = PaymentService()
        self.order_mapper = OrderMapper()
        self.dish_orm = DishORM()
        self.voucher_service = VoucherService()
        
    def checkout(self, user):
        cart_items = self.cart_orm.get_selected_cart_items_by_user(user=user)
        if not cart_items.exists():
            raise CartItemNotFoundException

        cart = self.cart_orm.get_cart_by_user(user=user)
        delivery_date = self.cart_orm.get_delivery_dates_of_selected_items(cart=cart)
        delivery_time = (timezone.now() + timedelta(minutes=30)).time()
        
        # Get delivery address and validate
        delivery_address = self.customer_orm.get_one_customer_address_instance(user=user)
        if not delivery_address:
            raise CustomerAddressNotFoundException("Please add a delivery address before checkout")
        
        self.customer_orm.selected_address(user=user, address_id=delivery_address.id)
        
        # Clean up old draft checkouts for this user (not placed yet)
        # NOTE: KHÔNG cancel vouchers ở đây - VoucherService sẽ reuse existing reservations
        # Vouchers đã reserved sẽ được update với checkout_id mới khi user apply lại
        from order.models import Checkout, Order
        
        # Delete old draft orders and checkouts only
        Order.objects.filter(
            owner=user,
            status=OrderStatusEnum.DRAFT
        ).delete()
        
        print(f"[Checkout] Cleaned up old draft orders for user {user.email}")

        grouped_by_chef = {}
        for item in cart_items:
            chef = item.dish.owner
            grouped_by_chef.setdefault(chef, []).append(item)

        checkout = self.orm.create_checkout(
          user=user,
          full_name=user.get_full_name(),
          phone_number=user.phone_number,                   
          delivery_date=delivery_date,
          delivery_time=delivery_time,
          delivery_address=delivery_address,
          payment_method=PaymentMethodEnum.COD,
            )

        orders = []
        total_sub = Decimal("0.00")
        total_tax = Decimal("0.00")
        total_delivery = Decimal("0.00")

        for chef, items in grouped_by_chef.items():
            order = self.orm.create_order_draft(
                user=user,
                cart_items=items,
                chef=chef,
                checkout=checkout, 
            )
            orders.append(order)
            total_sub += order.sub_total
            total_tax += order.tax_and_fees
            total_delivery += order.delivery_fee

        total_price = total_sub + total_tax + total_delivery

        # ✅ Cập nhật tổng vào Checkout
        checkout.sub_total = total_sub
        checkout.tax_and_fees = total_tax
        checkout.delivery_fee = total_delivery
        checkout.total_price = total_price
        checkout.save()

        return OrderMapper.to_checkout_response(orders)
    
    def get_order_by_uid_not_transfer(self, uid: UUID):
        order = self.orm.get_order_by_uid(uid)
        if not order:
            raise OrderNotFoundException
        return order

    def get_order_by_uid(self, uid: UUID):
        order = self.orm.get_order_by_uid(uid)
        if not order:
            raise OrderNotFoundException
        
        # Sync payment status nếu có payment và đang PENDING
        if (order.checkout and 
            hasattr(order.checkout, 'payment_transaction') and 
            order.status == 'DRAFT'):
            
            try:
                # Sync với PayOS để cập nhật status mới nhất
                payment = self.payment_service.get_payment_status(
                    order.checkout.payment_transaction.uid,
                    sync_with_gateway=True
                )
                
                # Reload order để lấy status mới nhất sau khi sync
                order.refresh_from_db()
            except Exception as e:
                print(f"[Order] Failed to sync payment status: {e}")
        
        return OrderMapper.to_response_with_info(order)
    
    def edit_profile_of_checkout(self, uid: UUID, payload: PersonalInfoSchema):
        # ✅ Lấy danh sách tất cả orders thuộc checkout này
        orders = self.orm.get_orders_by_checkout_uid(uid)
        if not orders:
            raise OrderNotFoundException
        # 3. Cập nhật profile
        self.orm.edit_profile_of_checkout(uid=uid, payload=payload)
        return self.order_mapper.to_checkout_response(orders)
    
    def edit_payment_method_of_checkout(self, uid: UUID, payload: PaymentMethodEnum):
        orders = self.orm.get_orders_by_checkout_uid(uid)
        if not orders:
            raise OrderNotFoundException
        if payload == PaymentMethodEnum.PAYOS:
            from profile.models import ChefPaymentInfo

            chef_ids = {order.chef_id for order in orders if order.chef_id}
            if chef_ids:
                verified_chefs = set(
                    ChefPaymentInfo.objects.filter(
                        user_id__in=chef_ids,
                        is_verified=True,
                    ).values_list("user_id", flat=True)
                )
                missing_verified = chef_ids - verified_chefs
                if missing_verified:
                    raise HttpError(
                        400,
                        "Some chefs are not verified for bank transfer. Please choose COD payment method.",
                    )
        self.orm.edit_payment_method_of_checkout(uid=uid, payload=payload)
        return self.order_mapper.to_checkout_response(orders)
    
    def edit_delivery_time_of_checkout(self, uid: UUID, payload: time):
        orders = self.orm.get_orders_by_checkout_uid(uid=uid)
        if not (orders):
            raise OrderNotFoundException
        self.orm.edit_delivery_time_of_checkout(uid=uid, payload=payload)
        return self.order_mapper.to_checkout_response(orders)
    
    @transaction.atomic
    def edit_deliver_address_of_checkout(self, user:TUser, uid: UUID, address_id: int):
        orders = self.orm.get_orders_by_checkout_uid(uid=uid)
        if not (orders):
            raise OrderNotFoundException
        addr = self.customer_orm.get_one_customer_address_instance_by_id(user=user, address_id=address_id)
        if not addr:
            raise CustomerAddressNotFoundException  # hoặc custom exception của bạn
        try:
            # Both operations will be in the same transaction
            self.customer_orm.selected_address(user=user, address_id=address_id)
            self.orm.edit_deliver_address_of_checkout(uid=uid, addr=addr)
            return self.order_mapper.to_checkout_response(orders)
        except Exception as e:
            # Transaction will automatically rollback
            raise e
        
    def edit_delivery_types_of_checkout(self, uid: UUID, payload: UpdateDeliveryTypesPayload):
        orders = self.orm.get_orders_by_checkout_uid(uid=uid)
        if not orders:
            raise OrderNotFoundException
            
        delivery_map = {item.chef_id: item.delivery_type for item in payload.sub_orders}
        checkout = orders[0].checkout
        
        # --- PHASE 1: GỌI API EXTERNAL (KHÔNG LOCK DATABASE) ---
        # Tính toán trước toàn bộ phí ship cần thiết
        estimated_fees = {}
        
        for order in orders:
            new_delivery_type = delivery_map.get(order.chef_id)
            
            if new_delivery_type == DeliveryTypeEnum.THIRD_PARTY:
                # 💡 Gọi Adapter lấy giá thật từ API
                if not checkout.delivery_address:
                    raise ValueError("Checkout missing delivery address")
                
                fee = AhamoveAdapter.estimate_fee(
                    pickup_lat=order.chef.chef_profile.kitchen_latitude,
                    pickup_lng=order.chef.chef_profile.kitchen_longitude,
                    dropoff_lat=checkout.delivery_address.latitude,  
                    dropoff_lng=checkout.delivery_address.longitude
                )
                estimated_fees[order.uid] = fee
                
            elif new_delivery_type == DeliveryTypeEnum.SELF_PICKUP:
                estimated_fees[order.uid] = 0
                
            else:
                estimated_fees[order.uid] = order.delivery_fee # Giữ nguyên nếu không đổi
                
        # --- PHASE 2: CẬP NHẬT DATABASE (MỞ TRANSACTION NHỎ NHẤT) ---
        try:
            with transaction.atomic():
                new_checkout_delivery_fee = 0
                new_checkout_total_price = 0
                
                for order in orders:
                    if order.chef_id in delivery_map:
                        order.delivery_type = delivery_map[order.chef_id]
                        order.delivery_fee = estimated_fees[order.uid]
                        
                        order.total_price = (
                            order.sub_total + 
                            order.tax_and_fees + 
                            order.delivery_fee - 
                            order.total_discount
                        )
                        order.save(update_fields=['delivery_type', 'delivery_fee', 'total_price'])
                    
                    new_checkout_delivery_fee += order.delivery_fee
                    new_checkout_total_price += order.total_price
                        
                checkout.delivery_fee = new_checkout_delivery_fee
                checkout.total_price = new_checkout_total_price
                checkout.save(update_fields=['delivery_fee', 'total_price'])
                
            return self.order_mapper.to_checkout_response(orders)
            
        except Exception as e:
            print(f"🚨 Database update failed for checkout {uid}: {e}")
            raise e

    def place_order(self, uid: UUID, bank_code: Optional[str] = None):
        """
        Place order with payment integration
        """

        from payment.services import PaymentService

        orders = self.orm.get_orders_by_checkout_uid(uid)
        if not orders:
            raise OrderNotFoundException

        checkout = orders[0].checkout
        address = checkout.delivery_address
        
        if not address:
            raise ValueError("Checkout missing delivery address")
        
        for order in orders:
            order.delivery_name = checkout.full_name
            order.delivery_phone = checkout.phone_number
            order.delivery_address_text = address.full_address()
            order.delivery_latitude = address.latitude
            order.delivery_longitude = address.longitude

        # =========================
        # 🔥 FIX 1: ALWAYS RESERVE INVENTORY FIRST (UNIFIED LOGIC)
        # =========================
        reserved_items = []
        try:
            for order in orders:
                for item in order.orderitem_fk_order.all():
                    self.dish_orm.reduce_quantity(
                        dish=item.dish,
                        available_date=order.checkout.delivery_date,
                        quantity=item.quantity
                    )
                    reserved_items.append((item.dish, order.checkout.delivery_date, item.quantity))
        except Exception as exc:
            # Roll back any inventory that was already reserved
            for dish, delivery_date, quantity in reserved_items:
                self.dish_orm.increase_quantity(
                    dish=dish,
                    available_date=delivery_date,
                    quantity=quantity
                )
            raise exc

        # =========================
        # COD FLOW
        # =========================
        if checkout.payment_method == PaymentMethodEnum.COD:

            # 🔥 KEEP: voucher mark USED is correct
            applied_vouchers = AppliedVoucher.objects.filter(
                models.Q(checkout=checkout) | models.Q(order__in=orders),
                status=VoucherReservationStatus.RESERVED
            )

            applied_vouchers.update(
                status=VoucherReservationStatus.USED,
                reservation_expires_at=None
            )

            print(f"[Order] COD vouchers marked USED")

            # 🔥 FIX 2: COD payment stays PENDING (OK)
            try:
                payment = self.payment_service.create_cod_payment(
                    checkout_uid=checkout.uid
                )

                # mark orders
                for order in orders:
                    self.orm.place_order(order)

                self.cart_service.clear_selected_items(user=orders[0].owner)

                return self.order_mapper.to_checkout_response(orders)
            except Exception as exc:
                for dish, delivery_date, quantity in reserved_items:
                    self.dish_orm.increase_quantity(
                        dish=dish,
                        available_date=delivery_date,
                        quantity=quantity
                    )
                for order in orders:
                    if order.status == OrderStatusEnum.PENDING:
                        order.status = OrderStatusEnum.DRAFT
                        order.save(update_fields=["status"])
                raise exc

        # =========================
        # PAYOS FLOW
        # =========================
        elif checkout.payment_method == PaymentMethodEnum.PAYOS:
            payment = None
            try:
                payment = self.payment_service.create_payment(
                    checkout_uid=checkout.uid,
                    payment_method=PaymentMethodEnum.PAYOS,
                    bank_code=bank_code
                )

                for order in orders:
                    self.orm.place_order(order)

                self.cart_service.clear_selected_items(user=orders[0].owner)

                response = self.order_mapper.to_checkout_response(orders)
                _pay_state = getattr(payment, "state", None)
                _gw = (_pay_state.gateway_response or {}) if _pay_state else {}
                response.payment_url = _pay_state.payment_url if _pay_state else None
                response.payment_uid = payment.uid
                response.transaction_id = _pay_state.transaction_id if _pay_state else None
                response.qr_code = _gw.get("qrCode") or _gw.get("qr_code")

                return response
            except Exception as exc:
                for dish, delivery_date, quantity in reserved_items:
                    self.dish_orm.increase_quantity(
                        dish=dish,
                        available_date=delivery_date,
                        quantity=quantity
                    )
                for order in orders:
                    if order.status == OrderStatusEnum.PENDING:
                        order.status = OrderStatusEnum.DRAFT
                        order.save(update_fields=["status"])
                if payment:
                    self.payment_service.cancel_payment(
                        payment_uid=payment.uid,
                        reason="Order placement failed after payment session creation"
                    )
                raise exc

        else:
            raise ValueError(f"Unsupported payment method: {checkout.payment_method}")

    def get_my_orders(self, user:TUser, filter: FilterOrderSchema, order_by: OrderByOrderSchema):
        orders = self.orm.get_my_orders(user=user, filter=filter, order_by=order_by)
        
        valid_orders = []
        
        # Sync payment status cho các orders đang DRAFT
        for order in orders:
            if (order.checkout and 
                hasattr(order.checkout, 'payment_transaction') and 
                order.status == 'DRAFT'):
                try:
                    self.payment_service.get_payment_status(
                        order.checkout.payment_transaction.uid,
                        sync_with_gateway=True
                    )
                    order.refresh_from_db()
                except Exception as e:
                    print(f"[Order] Failed to sync payment for order {order.uid}: {e}")
        
        # Group orders by chef
            if order.status != 'DRAFT':
                valid_orders.append(order)
        
        # grouped = defaultdict(list)
        # for order in orders:
        #     chef_id = order.chef.id if order.chef else None
        #     if chef_id:
        #         grouped[chef_id].append(order)
        
        # from collections import defaultdict
        # grouped = defaultdict(list)
        # for order in valid_orders:
        #     chef_id = order.chef.id if order.chef else None
        #     if chef_id:
        #         grouped[chef_id].append(order)
        
        # # Build response
        # result = []
        # for chef_id, chef_orders in grouped.items():
        #     first_order = chef_orders[0]
        #     chef_info = ChefInfoSchema(
        #         chef_id=first_order.chef.id,
        #         chef_name=first_order.chef.get_full_name()
        #     )
        #     result.append(OrderListResponse(
        #         chef_info=chef_info,
        #         orders=[OrderMapper.to_response_with_info(o) for o in chef_orders]
        #     ))
        
        result = []
        for order in valid_orders:
            # Lấy thông tin Chef của chính cái Order này
            chef_info = ChefInfoSchema(
                chef_id=order.chef.id if order.chef else None,
                chef_name=order.chef.get_full_name() if order.chef else "Unknown"
            )
            
            # Bọc 1 Order duy nhất vào trong cấu trúc OrderListResponse
            # Như vậy Frontend vẫn nhận được List[OrderListResponse] bình thường
            result.append(OrderListResponse(
                chef_info=chef_info,
                orders=[OrderMapper.to_response_with_info(order)] # <-- Array chỉ có 1 phần tử
            ))
        
        return result
    
    def get_customer_orders(self, user:TUser, filter: FilterOrderSchema, order_by: OrderByOrderSchema):
        orders = self.orm.get_customer_orders(user=user, filter=filter, order_by=order_by)
        
        valid_orders = []
        
        # Sync payment status cho các orders đang DRAFT
        for order in orders:
            if (order.checkout and 
                hasattr(order.checkout, 'payment_transaction') and 
                order.status == 'DRAFT'):
                try:
                    self.payment_service.get_payment_status(
                        order.checkout.payment_transaction.uid,
                        sync_with_gateway=True
                    )
                    order.refresh_from_db()
                except Exception as e:
                    print(f"[Order] Failed to sync payment for order {order.uid}: {e}")
        
        # Group orders by chef
            if order.status != 'DRAFT':
                valid_orders.append(order)
        
        result = []
        for order in valid_orders:
            # Lấy thông tin Chef của chính cái Order này
            chef_info = ChefInfoSchema(
                chef_id=order.chef.id if order.chef else None,
                chef_name=order.chef.get_full_name() if order.chef else "Unknown"
            )
            
            # Bọc 1 Order duy nhất vào trong cấu trúc OrderListResponse
            # Như vậy Frontend vẫn nhận được List[OrderListResponse] bình thường
            result.append(OrderListResponse(
                chef_info=chef_info,
                orders=[OrderMapper.to_response_with_info(order)] # <-- Array chỉ có 1 phần tử
            ))
        
        return result
    
    def get_all_orders_of_chef(self, chef:TUser, filter: FilterOrderSchema, order_by: OrderByOrderSchema):
        """Lấy tất cả đơn hàng của chef"""
        orders = self.orm.get_orders_by_chef(chef=chef, filter=filter, order_by=order_by)
        
        # Sync payment status cho các orders đang DRAFT
        for order in orders:
            if (order.checkout and 
                hasattr(order.checkout, 'payment_transaction') and 
                order.status == 'DRAFT'):
                try:
                    self.payment_service.get_payment_status(
                        order.checkout.payment_transaction.uid,
                        sync_with_gateway=True
                    )
                    order.refresh_from_db()
                except Exception as e:
                    print(f"[Order] Failed to sync payment for order {order.uid}: {e}")
        
        return [OrderMapper.to_response_with_info(order) for order in orders]
    
    @transaction.atomic
    def cancel_order(
        self,
        order_uid: UUID,
        reason: Optional[str] = None,
        cancelled_by: str = "customer"
    ):
        """
        Cancel order with automatic refund if needed.

        FLOW (FIXED):
        1. Get order + payment
        2. Validate permission
        3. Process refund FIRST (decision step)
        4. Update order status CANCELLED
        5. Rollback inventory
        6. Cancel vouchers
        7. Sync payment status
        """

        # =========================
        # 1. GET ORDER + PAYMENT
        # =========================
        order = self.orm.get_order_by_uid(order_uid)
        if not order:
            raise OrderNotFoundException

        payment = getattr(order.checkout, "payment_transaction", None)

        # =========================
        # 2. PERMISSION CHECK
        # =========================
        if cancelled_by == "customer":
            if not OrderStateMachine.can_customer_cancel(order.status):
                raise ValueError(
                    f"Customer cannot cancel order after CONFIRMED_SHOP. "
                    f"Current status: {order.status}"
                )

        elif cancelled_by == "chef":
            # 🔥 CHANGED: chef reject luôn allowed ở 2 trạng thái này
            allowed_statuses = [
                OrderStatusEnum.PENDING,
                OrderStatusEnum.CONFIRMED_SYSTEM
            ]

            if order.status not in allowed_statuses:
                raise ValueError(
                    f"Chef can only reject at PENDING or CONFIRMED_SYSTEM. "
                    f"Current status: {order.status}"
                )

        # =========================
        # 3. REFUND PROCESS FIRST (IMPORTANT FIX)
        # =========================
        refund_result = self.payment_service.handle_order_cancellation_refund(
            order_uid=order_uid,
            reason=reason or f"Order cancelled by {cancelled_by}"
        )

        if not refund_result.get("success"):
            print(f"[Order] Refund warning: {refund_result.get('error')}")

        # =========================
        # 4. UPDATE ORDER STATUS
        # =========================
        order.status = OrderStatusEnum.CANCELLED
        order.save()

        # =========================
        # 5. ROLLBACK INVENTORY
        # =========================
        for item in order.orderitem_fk_order.all():
            self.dish_orm.increase_quantity(
                dish=item.dish,
                available_date=order.checkout.delivery_date,
                quantity=item.quantity
            )

        print(f"[Order] Inventory restored for order {order_uid}")

        # =========================
        # 6. CANCEL VOUCHERS
        # =========================
        cancelled_count = AppliedVoucher.objects.filter(
            order=order,
            status__in=[
                VoucherReservationStatus.RESERVED,
                VoucherReservationStatus.USED
            ]
        ).update(status=VoucherReservationStatus.CANCELLED)

        print(f"[Order] Cancelled {cancelled_count} voucher(s)")

        # =========================
        # 7. SYNC PAYMENT STATUS
        # =========================
        if payment:
            payment.refresh_from_db()
            state = getattr(payment, "state", None)
            order.payment_status = state.status if state else order.payment_status
            order.save(update_fields=["payment_status"])

        # =========================
        # RETURN
        # =========================
        print(f"[Order] Cancelled order {order_uid} by {cancelled_by}")

        return OrderMapper.to_response_with_info(order)
    @transaction.atomic
    def chef_confirm_order(self, order_uid: UUID):
        """
        Chef confirms order at PENDING (COD) or CONFIRMED_SYSTEM (PayOS) status
        
        - COD: PENDING -> CONFIRMED_SHOP (payment on delivery)
        - PayOS: CONFIRMED_SYSTEM -> CONFIRMED_SHOP (money stays in escrow until COMPLETED)
        
        Args:
            order_uid: Order UUID
            
        Returns:
            Order response
        """
        order = self.orm.get_order_by_uid(order_uid)
        if not order:
            raise OrderNotFoundException
        
        # Check permission
        # if not OrderStateMachine.can_chef_decide(order.status):
        #     raise ValueError(
        #         f"Chef can only confirm order at PENDING (COD) or CONFIRMED_SYSTEM (PayOS) status. "
        #         f"Current status: {order.status}"
        #     )
        
        # ✅ Validate payment method và status phải match
        payment_method = order.checkout.payment_method
        
        if payment_method == PaymentMethodEnum.COD:
            # COD chỉ được confirm khi ở PENDING
            if order.status != OrderStatusEnum.PENDING:
                raise ValueError(
                    f"COD order can only be confirmed at PENDING status. "
                    f"Current status: {order.status}"
                )
        elif payment_method == PaymentMethodEnum.PAYOS:
            # PayOS chỉ được confirm khi ở CONFIRMED_SYSTEM (đã thanh toán)
            if order.status != OrderStatusEnum.CONFIRMED_SYSTEM:
                raise ValueError(
                    f"PayOS order can only be confirmed at CONFIRMED_SYSTEM status (after payment). "
                    f"Current status: {order.status}. Please wait for payment confirmation."
                )
        
        # Transition to CONFIRMED_SHOP
        is_valid, error_msg = OrderStateMachine.validate_transition(
            order.status,
            OrderStatusEnum.CONFIRMED_SHOP
        )
        
        if not is_valid:
            raise ValueError(error_msg)
        
        order.status = OrderStatusEnum.CONFIRMED_SHOP
        order.save()
        
        print(f"[Order] Chef confirmed order {order_uid}")
        return OrderMapper.to_response_with_info(order)
    
    @transaction.atomic
    def complete_order_with_release(self, order_uid: UUID):
        """
        COMPLETE ORDER ONLY:
        - Update status COMPLETED
        - Trigger RELEASE nếu PayOS escrow
        - COD: KHÔNG release escrow (vì không có escrow)
        """

        order = self.orm.get_order_by_uid(order_uid)
        if not order:
            raise OrderNotFoundException

        # =========================
        # 1. VALIDATE TRANSITION
        # =========================
        is_valid, error_msg = OrderStateMachine.validate_transition(
            order.status,
            OrderStatusEnum.COMPLETED
        )

        if not is_valid:
            raise ValueError(error_msg)

        # =========================
        # 2. UPDATE ORDER STATUS
        # =========================
        order.status = OrderStatusEnum.COMPLETED

        # 🔥 CHANGED: nên set payment_status ngay tại đây để tránh mismatch state
        # (trước bạn để sau payment block)
        payment = getattr(order.checkout, "payment_transaction", None)

        order.save()

        # =========================
        # 3. SETTLEMENT
        # =========================
        settlement_record = None
        chef_payout = Decimal(0)

        try:
            settlement_record = self.payment_service.create_settlement_record(
                order_uid,
                order.chef
            )
            chef_payout = settlement_record.chef_payout_amount or Decimal(0)
        except Exception as e:
            print(f"[Order] Warning settlement error: {e}")

        # =========================
        # 4. PAYOS ESCROW RELEASE
        # =========================
        if order.checkout.payment_method == PaymentMethodEnum.PAYOS:

            # 🔥 CHANGED: check HOLDING OR SUCCESS (tránh case SUCCESS do sync lỗi)
            state = getattr(payment, "state", None)
            if payment and state and state.status in [PaymentStatus.HOLDING, PaymentStatus.SUCCESS]:
                from utils.enums import WalletTransactionTypeEnum
                self.payment_service.credit_internal_wallet(
                    user=order.chef,
                    amount=chef_payout,
                    transaction_type=WalletTransactionTypeEnum.RELEASE,
                    order=order,
                    reference_id=f"release_{order.uid}",
                    description=f"Escrow release for order {order.uid}",
                    metadata={
                        "payment_method": "PAYOS",
                        "stage": "ESCROW_RELEASE"
                    },
                )

                self.payment_service.set_payment_state(
                    payment,
                    PaymentStatus.RELEASED,
                    reason="escrow_release",
                    source="order_complete",
                )

        # =========================
        # 5. COD FLOW
        # =========================
        elif order.checkout.payment_method == PaymentMethodEnum.COD:

            # COD không escrow
            if payment:
                self.payment_service.set_payment_state(
                    payment,
                    PaymentStatus.SUCCESS,
                    reason="cod_complete",
                    source="order_complete",
                )

        # =========================
        # 6. POST PROCESS
        # =========================
        def _sync_daily_meal_logs():
            try:
                from recommendation.services.recommendation import RecommendationService

                RecommendationService().sync_order_meal_logs(order_uid=str(order.uid))
            except Exception as exc:
                print(f"[Order] Warning: failed to sync daily meal logs: {exc}")

        transaction.on_commit(_sync_daily_meal_logs)

        return OrderMapper.to_response_with_info(order)
    
    
    @transaction.atomic
    def apply_platform_voucher_to_checkout(
        self,
        user: TUser,
        checkout_uid: UUID,
        voucher_code: str,
        voucher_type: str
    ):
        """
        Apply platform voucher (PLATFORM_SUBTOTAL or PLATFORM_SHIPPING) to checkout
        
        Args:
            user: User applying voucher
            checkout_uid: Checkout UUID
            voucher_code: Voucher code
            voucher_type: "PLATFORM_SUBTOTAL" or "PLATFORM_SHIPPING"
            
        Returns:
            CheckoutResponse with updated prices
        """
        # Get checkout
        orders = self.orm.get_orders_by_checkout_uid(checkout_uid)
        if not orders:
            raise OrderNotFoundException
        
        checkout = orders[0].checkout
        
        # Check if this type of voucher already applied
        existing = AppliedVoucher.objects.filter(
            checkout=checkout,
            voucher_type=voucher_type,
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).exists()
        
        if existing:
            raise VoucherInvalidException(f"Đã apply {voucher_type} voucher cho checkout này rồi")
        
        # Delegate to VoucherService for reservation logic
        reservation, discount_amount = self.voucher_service.apply_platform_voucher_reservation(
            user=user,
            checkout=checkout,
            voucher_code=voucher_code,
            voucher_type=voucher_type
        )
        
        print(f"[Voucher] Applied {voucher_type} voucher {voucher_code} to checkout {checkout.uid} - Discount: {discount_amount}")
        
        # Recalculate checkout total
        self._recalculate_checkout_total(checkout)
        
        # Refresh orders to get updated data
        orders = self.orm.get_orders_by_checkout_uid(checkout_uid)
        return self.order_mapper.to_checkout_response(orders)
    
    def _recalculate_order_total(self, order):
        """
        Recalculate order total_price including all discounts.

        Principles:
        - NEVER recalculate voucher discount → use AppliedVoucher.discount_amount
        - Shop voucher applied first (affects net subtotal)
        - Platform subtotal distributed by net subtotal
        - Platform shipping distributed by delivery fee
        - Deterministic: apply order does NOT affect result
        """

        checkout = order.checkout
        orders = list(checkout.order_fk_checkout.all())

        # ==============================
        # 1. LOAD ALL VOUCHERS (1 query)
        # ==============================
        applied_vouchers = list(
            AppliedVoucher.objects.filter(
                checkout=checkout,
                status__in=[
                    VoucherReservationStatus.RESERVED,
                    VoucherReservationStatus.USED
                ]
            )
        )

        # ==============================
        # 2. GROUP VOUCHERS
        # ==============================
        platform_subtotal_discount = Decimal(0)
        platform_shipping_discount = Decimal(0)
        shop_discount_map = {}  # order_uid -> discount

        for av in applied_vouchers:
            if av.voucher_type == VoucherTypeEnum.PLATFORM_SUBTOTAL:
                platform_subtotal_discount += av.discount_amount

            elif av.voucher_type == VoucherTypeEnum.PLATFORM_SHIPPING:
                platform_shipping_discount += av.discount_amount

            elif av.voucher_type == VoucherTypeEnum.SHOP_VOUCHER and av.order_id:
                shop_discount_map[av.order_id] = (
                    shop_discount_map.get(av.order_id, Decimal(0)) + av.discount_amount
                )

        # ==============================
        # 3. COMPUTE NET SUBTOTAL
        # ==============================
        net_subtotal_map = {}
        total_net_subtotal = Decimal(0)

        for o in orders:
            shop_discount = shop_discount_map.get(o.uid, Decimal(0))
            net = max(o.sub_total - shop_discount, Decimal(0))

            net_subtotal_map[o.uid] = net
            total_net_subtotal += net

        # ==============================
        # 4. TOTAL DELIVERY
        # ==============================
        total_delivery_fee = sum(o.delivery_fee for o in orders)

        # ==============================
        # 5. APPLY TO CURRENT ORDER
        # ==============================
        # Shop discount
        order.shop_discount = shop_discount_map.get(order.uid, Decimal(0))

        # Platform subtotal discount (proportional by net subtotal)
        if total_net_subtotal > 0:
            order.platform_subtotal_discount = (
                platform_subtotal_discount
                * net_subtotal_map[order.uid]
                / total_net_subtotal
            ).quantize(Decimal("0.01"))
        else:
            order.platform_subtotal_discount = Decimal(0)

        # Platform shipping discount (proportional by delivery fee)
        if total_delivery_fee > 0:
            order.platform_shipping_discount = (
                platform_shipping_discount
                * order.delivery_fee
                / total_delivery_fee
            ).quantize(Decimal("0.01"))
        else:
            order.platform_shipping_discount = Decimal(0)

        # ==============================
        # 6. TOTAL DISCOUNT
        # ==============================
        order.total_discount = (
            order.shop_discount
            + order.platform_subtotal_discount
            + order.platform_shipping_discount
        )

        # ==============================
        # 7. FINAL PRICE
        # ==============================
        order.total_price = (
            order.sub_total
            + order.tax_and_fees
            + order.delivery_fee
            - order.total_discount
        )

        # ==============================
        # 8. SAVE
        # ==============================
        order.save(update_fields=[
            "shop_discount",
            "platform_subtotal_discount",
            "platform_shipping_discount",
            "total_discount",
            "total_price",
        ])
    def _recalculate_checkout_total(self, checkout):
        """Recalculate checkout total after applying vouchers"""

        orders = list(checkout.order_fk_checkout.all())

        total_price = Decimal(0)
        total_discount = Decimal(0)

        for order in orders:
            self._recalculate_order_total(order)

            total_price += order.total_price
            total_discount += order.total_discount  # ✅ cộng từ order

        checkout.total_price = total_price
        checkout.total_discount = total_discount  # ✅ FIX

        checkout.save(update_fields=[
            "total_price",
            "total_discount"   # ✅ FIX
        ])
    
    @transaction.atomic
    def apply_shop_voucher_to_order(
        self,
        user: TUser,
        order_uid: UUID,
        voucher_code: str
    ):
        """
        Apply SHOP voucher to a specific order (only SHOP_VOUCHER allowed)
        Platform vouchers must be applied at checkout level
        
        Args:
            user: User applying voucher
            order_uid: Order UUID
            voucher_code: Voucher code (must be SHOP_VOUCHER)
            
        Returns:
            OrderResponeWithInfo with updated prices
        """
        
        # Get order
        order = self.orm.get_order_by_uid(order_uid)
        if not order:
            raise OrderNotFoundException
        
        # Check if shop voucher already applied
        existing = AppliedVoucher.objects.filter(
            order=order,
            voucher_type=VoucherTypeEnum.SHOP_VOUCHER,
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).exists()
        
        if existing:
            raise VoucherInvalidException("Order đã có shop voucher rồi")
        
        #CHECK xem subtotal của order có đủ điều kiện áp voucher không
        #lazy import voucher service để tránh circular import
        from voucher.services import VoucherService
        voucher = VoucherService().get_voucher_by_code(voucher_code)
        #CHECK xem subtotal của order có đủ điều kiện áp voucher không
        if order.sub_total < voucher.min_order_amount:
            raise VoucherInvalidException(
                f"Giá trị của đơn hàng không đủ điều kiện áp voucher. "
                f"Yêu cầu tối thiểu: {voucher.min_order_amount}, "
                f"Giá trị hiện tại: {order.sub_total}"
            )
        # Delegate to VoucherService for reservation logic
        reservation, discount_amount = self.voucher_service.apply_shop_voucher_reservation(
            user=user,
            order=order,
            voucher_code=voucher_code
        )
        
        print(f"[Voucher] Applied SHOP voucher {voucher_code} to order {order.uid} - Discount: {discount_amount}")
        
        # Recalculate order total (includes platform + shop discounts)
   
        self._recalculate_checkout_total(order.checkout)
        order.refresh_from_db()
        # Update checkout total
        checkout = order.checkout
        checkout.total_price = sum(
            o.total_price for o in checkout.order_fk_checkout.all()
        )
        checkout.total_discount = sum(
            o.total_discount for o in checkout.order_fk_checkout.all()
        )
        checkout.save()
        
        return OrderMapper.to_response_with_info(order)
    
    def check_dish_in_order(self, order:Order, dish:Dish) -> bool:
        """Kiểm tra dish có trong order không"""
        dish_in_order = self.orm.check_dish_in_order(dish=dish, order=order)
        if not (dish_in_order):
            raise DishNotFoundInOrderException
        return dish_in_order
  