
from django.db import transaction
from uuid import UUID
from dish.models import Dish
from order.models import Order, OrderItem, Checkout
from order.schemas.responses import OrderResponse, OrderItemResponse, CheckoutResponse, OrderResponeWithInfo
from order.schemas.requests import PersonalInfoSchema, FilterOrderSchema, OrderByOrderSchema
from decimal import Decimal
from utils.enums import PaymentMethodEnum, OrderStatusEnum, UserTypeEnum
from datetime import time
from profile.orm.profile import CustomerAddress
from utils.types import TUser
from typing import Optional
from voucher.models import AppliedVoucher
from utils.enums import VoucherTypeEnum, VoucherReservationStatus
from utils.permissions.roles import get_user_role

class OrderMapper:
    @staticmethod
    def to_response(
        order: "Order", 
        platform_subtotal_discount: Decimal = Decimal(0),
        platform_shipping_discount: Decimal = Decimal(0)
    ) -> OrderResponse:
        items = [
            OrderItemResponse(
                dish_uid=item.dish.uid if item.dish else None,
                dish_name=item.dish_name,
                image_url=item.dish.attachment.public_url if item.dish and item.dish.attachment else None,
                quantity=item.quantity,
                price=item.price,
                subtotal=item.subtotal(),
            )
            for item in order.orderitem_fk_order.all()
        ]
        
        # Get discount values from order model (already calculated and stored)
        platform_subtotal = order.platform_subtotal_discount or Decimal(0)
        platform_shipping = order.platform_shipping_discount or Decimal(0)
        shop_discount = order.shop_discount or Decimal(0)
        
        # Total discount for this order
        total_order_discount = order.total_discount or Decimal(0)
        
        # Get voucher codes from AppliedVoucher (only RESERVED or USED)
        applied_vouchers = AppliedVoucher.objects.filter(
            order=order,
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).select_related('voucher')
        voucher_codes = ', '.join([av.voucher.code for av in applied_vouchers]) if applied_vouchers.exists() else None
        
        return OrderResponse(
            uid=order.uid,
            chef_id=order.chef.id,
            chef_name=order.chef.get_full_name(),
            sub_total=order.sub_total,
            tax_and_fees=order.tax_and_fees,
            delivery_fee=order.delivery_fee,
            platform_subtotal_discount=platform_subtotal,
            platform_shipping_discount=platform_shipping,
            shop_discount=shop_discount,
            total_discount=total_order_discount,
            total_price=order.total_price,
            voucher_code=voucher_codes,
            items=items,
        )

    @staticmethod
    def to_checkout_response(orders: list["Order"]) -> CheckoutResponse:
        if not orders:
            raise ValueError("No orders provided")

        first_order = orders[0]
        checkout = first_order.checkout
        
        # Use checkout model values (already calculated)
        sub_total = checkout.sub_total
        tax_and_fees = checkout.tax_and_fees
        delivery_fee = checkout.delivery_fee
        total_price = checkout.total_price
        
        # Calculate platform voucher discounts from AppliedVoucher records
        
        # Only count RESERVED or USED vouchers (not CANCELLED or EXPIRED)
        # applied_vouchers = AppliedVoucher.objects.filter(
        #     checkout=checkout,
        #     status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        # )
        
        platform_subtotal_discount = sum(
            (order.platform_subtotal_discount or Decimal(0))
            for order in orders
        )

        platform_shipping_discount = sum(
            (order.platform_shipping_discount or Decimal(0))
            for order in orders
        )
        total_discount = checkout.total_discount or Decimal(0)
        # Allocate platform discounts proportionally to each order
        order_responses = []
        for order in orders:
            # Use stored discount values from order model (already calculated by _recalculate_order_total)
            order_responses.append(OrderMapper.to_response(order))

        return CheckoutResponse(
            uid=checkout.uid,
            full_name=checkout.full_name,
            phone_number=checkout.phone_number,
            delivery_date=checkout.delivery_date,
            delivery_time=checkout.delivery_time,
            delivery_address=checkout.delivery_address.full_address() if checkout.delivery_address else None,
            payment_method=checkout.payment_method,
            sub_total=sub_total,
            tax_and_fees=tax_and_fees,
            delivery_fee=delivery_fee,
            platform_subtotal_discount=platform_subtotal_discount,
            platform_shipping_discount=platform_shipping_discount,
            total_discount=total_discount,
            total_price=total_price,
            orders=order_responses,
        )

    @staticmethod
    def to_response_with_info(order) -> OrderResponeWithInfo:
        checkout = order.checkout
        
        # Get voucher codes from AppliedVoucher (only RESERVED or USED)
        applied_vouchers = AppliedVoucher.objects.filter(
            order=order,
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).select_related('voucher')
        voucher_codes = ', '.join([av.voucher.code for av in applied_vouchers]) if applied_vouchers.exists() else None
        
        # Get discount values from order model
        platform_subtotal = order.platform_subtotal_discount or Decimal(0)
        platform_shipping = order.platform_shipping_discount or Decimal(0)
        shop_discount = order.shop_discount or Decimal(0)
        total_discount = order.total_discount or Decimal(0)

        # Get refund status from payment transaction
        refund_status = None
        if hasattr(checkout, 'payment_transaction'):
            payment = checkout.payment_transaction
            state = getattr(payment, "state", None)
            if state and state.status == 'CANCELLED':
                refund_status = state.gateway_response.get('refund_status', 'PROCESSING') if state.gateway_response else 'PROCESSING'

        chef_name = ""
        if order.chef:
            # Tuỳ theo model User của bạn dùng fullname hay username
            chef_name = getattr(order.chef, 'full_name', getattr(order.chef, 'username', 'Unknown Chef'))
            
            
        if hasattr(order.chef, 'chef_profile'):
            profile = order.chef.chef_profile
            
            chef_address = getattr(profile, 'kitchen_address', None)
            chef_lat = getattr(profile, 'kitchen_latitude', None)
            chef_lng = getattr(profile, 'kitchen_longitude', None)

            # Nối chuỗi địa chỉ chi tiết nếu kitchen_address (Số nhà) bị trống hoặc muốn hiển thị đầy đủ
            if not chef_address:
                street = getattr(profile, 'kitchen_street', '')
                ward = getattr(profile, 'kitchen_ward', '')
                district = getattr(profile, 'kitchen_district', '')
                city = getattr(profile, 'kitchen_city', '')
                
                components = [c for c in [street, ward, district, city] if c]
                if components:
                    chef_address = ", ".join(components)
                    
            if not chef_address:
                chef_address = "Chưa cập nhật địa chỉ bếp"
        else:
            chef_address = "Chưa thiết lập hồ sơ bếp"
            
        return OrderResponeWithInfo(
            uid=order.uid,
            full_name=checkout.full_name if checkout else None,
            phone_number=checkout.phone_number if checkout else None,
            delivery_date=checkout.delivery_date if checkout else None,
            delivery_time=checkout.delivery_time if checkout else None,
            delivery_address=checkout.delivery_address.full_address() if checkout and checkout.delivery_address else None,
            delivery_latitude=order.delivery_latitude,
            delivery_longitude=order.delivery_longitude,
            delivery_type=order.delivery_type, 
            chef_name=chef_name,
            chef_address=chef_address,
            chef_latitude=chef_lat,
            chef_longitude=chef_lng,
            payment_method=checkout.payment_method if checkout else None,
            sub_total=order.sub_total or Decimal(0),
            tax_and_fees=order.tax_and_fees or Decimal(0),
            delivery_fee=order.delivery_fee or Decimal(0),
            platform_subtotal_discount=platform_subtotal,
            platform_shipping_discount=platform_shipping,
            shop_discount=shop_discount,
            total_discount=total_discount,
            total_price=order.total_price or Decimal(0),
            status=order.status,
            refund_status=refund_status,
            voucher_code=voucher_codes,
     
            items = [
                OrderItemResponse(
                    dish_uid=item.dish.uid if item.dish else None,
                    dish_name=item.dish_name,
                    chef_name=item.dish.owner.get_full_name() if item.dish and item.dish.owner else None,
                    image_url=item.dish.attachment.public_url if item.dish and item.dish.attachment else None,
                    quantity=item.quantity,
                    price=item.price,
                    subtotal=item.subtotal(),
                )
                for item in order.orderitem_fk_order.all()
            ]
        )
        
class OrderORM:
  
    @staticmethod
    def create_checkout(user, full_name, phone_number, delivery_date, delivery_time, delivery_address, payment_method):
        """Tạo Checkout mới"""
        checkout = Checkout.objects.create(
            owner=user,
            full_name=full_name,
            phone_number=phone_number,
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            delivery_address=delivery_address,
            payment_method=payment_method,
        )
        return checkout
      
    @staticmethod
    @transaction.atomic
    def create_order_draft(user, cart_items, chef, checkout):
        """Tạo Order draft từ CartItems"""
        order = Order.objects.create(
            checkout=checkout,
            owner=user,
            chef=chef,
            status=OrderStatusEnum.DRAFT,  
        )

        order_items = []
        sub_total = Decimal("0.00")
        for item in cart_items:
            subtotal_item = item.dish.price * item.quantity
            sub_total += subtotal_item
            
            # Get dish image URL from attachment
            dish_image_url = None
            if item.dish and item.dish.attachment:
                dish_image_url = item.dish.attachment.public_url
            
            order_items.append(
                OrderItem(
                    order=order,
                    dish=item.dish,
                    dish_name=item.dish.name,
                    dish_image_url=dish_image_url,
                    quantity=item.quantity,
                    price=item.dish.price,
                )
            )
        OrderItem.objects.bulk_create(order_items)

        tax_and_fees = Decimal("0.10") * sub_total
        delivery_fee = Decimal("15000") if sub_total >= Decimal("200000") else Decimal("30000")
        total_price = sub_total + tax_and_fees + delivery_fee

        order.sub_total = sub_total
        order.tax_and_fees = tax_and_fees
        order.delivery_fee = delivery_fee
        order.total_price = total_price
        order.save()
        return order

    @staticmethod
    def get_order(uid: UUID):
        try:
            order = Order.objects.get(uid=uid)
            return order
        except Order.DoesNotExist:
            return None

    @staticmethod
    def get_order_by_uid(uid: UUID):
        return (
            Order.objects
            .select_related(
                "checkout",
                "checkout__delivery_address",
                "chef",
            )
            .prefetch_related("orderitem_fk_order__dish__owner",
                              "orderitem_fk_order__dish__attachment")
            .filter(uid=uid)
            .first()
        )
        
    @staticmethod
    def edit_profile_of_checkout(uid:UUID, payload: PersonalInfoSchema):
        try:
            checkout = Checkout.objects.get(uid=uid)
            checkout.full_name = payload.full_name
            checkout.phone_number = payload.phone_number
            checkout.save()
        except Order.DoesNotExist:
            return None

    @staticmethod
    def edit_payment_method_of_checkout(uid:UUID, payload: PaymentMethodEnum):
        try:
            checkout = Checkout.objects.get(uid=uid)
            checkout.payment_method = payload
            checkout.save()
        except Order.DoesNotExist:
            return None
          
    @staticmethod
    def edit_delivery_time_of_checkout(uid:UUID, payload: time):
        # Nếu payload có timezone, loại bỏ nó
        if hasattr(payload, 'tzinfo') and payload.tzinfo is not None:
            payload = payload.replace(tzinfo=None)
        try:
            checkout = Checkout.objects.get(uid=uid)
            checkout.delivery_time = payload
            checkout.save()
        except Order.DoesNotExist:
            return None
          
    @staticmethod
    def edit_deliver_address_of_checkout(uid: UUID, addr: CustomerAddress):
        # Gọi hàm có sẵn để lấy địa chỉ
        try:
            checkout = Checkout.objects.get(uid=uid)
            checkout.delivery_address = addr
            checkout.save()
        except Order.DoesNotExist:
            return None
    
    @staticmethod
    def place_order(order: Order):
        order.status = OrderStatusEnum.PENDING
        order.save(update_fields=[
            "status",
            "delivery_name",
            "delivery_phone",
            "delivery_address_text",
            "delivery_latitude",
            "delivery_longitude"
        ])
        return order

    @staticmethod
    def get_orders_by_checkout_uid(uid: UUID):
        return Order.objects.filter(checkout__uid=uid).order_by('created_at')

    @staticmethod
    def get_my_orders(
        user: TUser,
        filter: Optional[FilterOrderSchema] = None,
        order_by: Optional[OrderByOrderSchema] = None
    ):
        # không lấy đơn ở trạng thái DRAFT vì đây là trạng thái tạm thời khi tạo đơn, chưa phải đơn thực sự của khách hàng hay chef nào cả
        query = Order.objects.exclude(status=OrderStatusEnum.DRAFT)

        role = get_user_role(user)
        if role == UserTypeEnum.CUSTOMER:
            query = query.filter(owner=user).select_related(
                "checkout",
                "checkout__delivery_address",
                "checkout__payment_transaction",
                "chef",
            )
        elif role == UserTypeEnum.CHEF:
            query = query.filter(chef=user).select_related(
                "checkout",
                "checkout__delivery_address",
                "checkout__payment_transaction",
                "owner",
            )
        else:
            query = query.select_related(
                "checkout",
                "checkout__delivery_address","checkout__payment_transaction",
                "owner",
                "chef",
            )

        query = query.prefetch_related("orderitem_fk_order__dish")

        if filter:
            query = query.filter(filter.get_filter_expression())

        if order_by:
            expr = order_by.get_order_by_expression()
            if isinstance(expr, str):
                query = query.order_by(expr, "-uid")
            elif isinstance(expr, (list, tuple)):
                query = query.order_by(*expr, "-uid")
        else:
            query = query.order_by("-created_at", "-uid")

        return query
    
    
    @staticmethod
    def get_customer_orders(
        user: TUser,
        filter: Optional[FilterOrderSchema] = None,
        order_by: Optional[OrderByOrderSchema] = None
    ):
        query = Order.objects.exclude(status=OrderStatusEnum.DRAFT)

        query = query.filter(owner=user).select_related(
            "checkout",
            "checkout__delivery_address",
            "checkout__payment_transaction",
            "chef",
        )
    
        query = query.prefetch_related("orderitem_fk_order__dish")

        if filter:
            query = query.filter(filter.get_filter_expression())

        if order_by:
            expr = order_by.get_order_by_expression()
            if isinstance(expr, str):
                query = query.order_by(expr, "-uid")
            elif isinstance(expr, (list, tuple)):
                query = query.order_by(*expr, "-uid")
        else:
            query = query.order_by("-created_at", "-uid")

        return query
      
    @staticmethod
    def get_orders_by_customer(
        user: TUser, 
        filter: Optional[FilterOrderSchema] = None, 
        order_by: Optional[OrderByOrderSchema] = None
    ):
        return OrderORM.get_my_orders(user=user, filter=filter, order_by=order_by)
    
    @staticmethod
    def get_orders_by_chef(
        chef: TUser, 
        filter: Optional[FilterOrderSchema] = None, 
        order_by: Optional[OrderByOrderSchema] = None
    ):
        """Lấy danh sách đơn hàng của chef, không lấy đơn hàng ở trạng thái DRAFT"""
        return OrderORM.get_my_orders(user=chef, filter=filter, order_by=order_by)
    
    # @staticmethod
    # def check_dish_in_order(order: Order , dish: Dish) -> bool:
    #     """Kiểm tra dish có trong order không"""
    #     try:
    #         return OrderItem.objects.filter(order=order, dish=dish).exists()
    #     except OrderItem.DoesNotExist:
    #         return False

    @staticmethod
    def check_dish_in_order(order: Order, dish: Dish) -> bool:
        return OrderItem.objects.filter(
            order_id=order.uid,
            dish_id=dish.uid
        ).exists()