from typing import List
from uuid import UUID
from ninja import Query

from mongo_chat.notifications import send_order_notification
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, delete, get, post, put, patch
# from utils.router.paginate import paginate
from utils.types import AuthenticatedRequest
from .schemas.requests import PersonalInfoSchema, FilterOrderSchema, OrderByOrderSchema, ApplyVoucherSchema, ApplyPlatformVoucherSchema, SubOrderDeliverySchema, UpdateDeliveryTypesPayload
from .schemas.responses import CheckoutResponse, OrderListResponse, OrderResponeWithInfo, ChefOrderGroupResponse
from .services import OrderService
from utils.enums import PaymentMethodEnum, OrderStatusEnum
from exceptions.orders import OrderNotFoundException
from datetime import time


@api(prefix_or_class="orders", tags=["Order"], auth=AuthBear())
class OrderController(Controller):
    def __init__(self, service: OrderService) -> None:
        self.service = service
    
    # API dành cho customer, chef để kiểm tra đơn hàng (Order)
    @get("/", response=List[OrderListResponse])
    def get_my_orders(self, request: AuthenticatedRequest, filter: FilterOrderSchema = Query(...), order_by: OrderByOrderSchema = Query(...)):
        return self.service.get_my_orders(user=request.user, filter=filter, order_by=order_by)
    
    @get("/customer", response=List[OrderListResponse])
    def get_customer_orders(self, request: AuthenticatedRequest, filter: FilterOrderSchema = Query(...), order_by: OrderByOrderSchema = Query(...)):
        return self.service.get_customer_orders(user=request.user, filter=filter, order_by=order_by)
    
    @get("/{uid}", response=OrderResponeWithInfo)
    def get_order_by_uid(self, request: AuthenticatedRequest, uid: UUID):
        return self.service.get_order_by_uid(uid=uid)
    
    @post("/{uid}/cancel", response=OrderResponeWithInfo)
    def cancel_order_by_customer(self, request: AuthenticatedRequest, uid: UUID, reason: str = None):
        """
        Cancel order (Customer only)
        
        Customer can only cancel before chef confirms (before CONFIRMED_SHOP).
        If payment was made via PayOS, refund will be processed automatically.
        """
        order = self.service.cancel_order(
            order_uid=uid, 
            reason=reason, 
            cancelled_by="customer"
        )
        
        order_obj = self.service.orm.get_order_by_uid(uid)
        
        chef_id = order_obj.chef_id
        
        send_order_notification(
            customer_id=chef_id, 
            order_id=order.uid, 
            title="Order Cancelled", 
            body=f"Your order has been cancelled by the customer: {reason or 'No reason provided'}",
            chef_name=request.user.username
        ) 
            
        
        return order
    
    @post("/{uid}/apply-voucher", response=OrderResponeWithInfo)
    def apply_voucher_to_order(self, request: AuthenticatedRequest, uid: UUID, payload: ApplyVoucherSchema):
        """
        Apply SHOP voucher to a specific order (only after order is created from checkout)
        
        Args:
            uid: Order UUID
            payload: Voucher code (must be SHOP_VOUCHER type)
            
        Note: Platform vouchers (PLATFORM_SUBTOTAL, PLATFORM_SHIPPING) must be applied at checkout level
        """
        return self.service.apply_shop_voucher_to_order(
            user=request.user,
            order_uid=uid,
            voucher_code=payload.voucher_code
        )


@api(prefix_or_class="chef/orders", tags=["Chef Order"], auth=AuthBear())
class ChefOrderController(Controller):
    """API endpoints cho Chef quản lý đơn hàng"""
    
    def __init__(self, service: OrderService) -> None:
        self.service = service
    
    @get("/", response=List[OrderResponeWithInfo])
    def get_all_orders_of_chef(
        self, 
        request: AuthenticatedRequest, 
        filter: FilterOrderSchema = Query(...), 
        order_by: OrderByOrderSchema = Query(...)
    ):
        """
        Lấy tất cả đơn hàng của chef
        
        Chef có thể xem tất cả đơn hàng thuộc các món ăn của mình.
        Hỗ trợ filter theo status và sắp xếp.
        """
        return self.service.get_all_orders_of_chef(
            chef=request.user, 
            filter=filter, 
            order_by=order_by
        )
    
    @post("/{uid}/confirm", response=OrderResponeWithInfo)
    def confirm_order(self, request: AuthenticatedRequest, uid: UUID):
        """
        Chef xác nhận đơn hàng
        
        - COD Flow: PENDING → CONFIRMED_SHOP (chef xác nhận đơn COD)
        - PayOS Flow: CONFIRMED_SYSTEM → CONFIRMED_SHOP (đã thanh toán, tiền giữ trong escrow)
        - Sau khi xác nhận, đơn hàng chuyển sang CONFIRMED_SHOP
        - Với PayOS: Tiền vẫn giữ trong escrow cho đến khi đơn hàng COMPLETED
        """
        # Kiểm tra quyền
        order_obj = self.service.orm.get_order_by_uid(uid)
        if not order_obj:
            raise OrderNotFoundException
        if order_obj.chef != request.user:
            from ninja.errors import HttpError
            raise HttpError(403, "You don't have permission to confirm this order")
        
        confirm_order = self.service.chef_confirm_order(order_uid=uid)
        
        try:
            customer_id = order_obj.owner.id
            chef_name = order_obj.chef.username
            send_order_notification(
                customer_id=customer_id,
                order_id = uid,
                title="Order Confirmed",
                body=f"Your order has been confirmed by the chef {chef_name}. It is now being prepared.",
                chef_name=chef_name
            )
        except Exception as e:
            print(f"🚨 Failed to send order confirmation notification: {e}")
            
        return confirm_order
    
    @post("/{uid}/reject", response=OrderResponeWithInfo)
    def reject_order(self, request: AuthenticatedRequest, uid: UUID, reason: str = None):
        """
        Chef từ chối đơn hàng
        
        - Chef có thể từ chối ở trạng thái PENDING (COD) hoặc CONFIRMED_SYSTEM (PayOS)
        - Với PayOS: Hệ thống sẽ tự động hoàn tiền vào wallet cho khách hàng
        - Số lượng món ăn sẽ được hoàn lại
        """
        # Kiểm tra quyền
        order_obj = self.service.orm.get_order_by_uid(uid)
        if not order_obj:
            raise OrderNotFoundException
        if order_obj.chef != request.user:
            from ninja.errors import HttpError
            raise HttpError(403, "You don't have permission to reject this order")
        
        cancel_order = self.service.cancel_order(
            order_uid=uid,
            reason=reason or "Chef rejected order",
            cancelled_by="chef"
        )
        
        try:
            customer_id = order_obj.owner.id
            chef_name = order_obj.chef.username
            send_order_notification(
                customer_id=customer_id,
                order_id = uid,
                title="Order Rejected",
                body=f"Your order has been rejected by the chef {chef_name}.",
                chef_name=chef_name
            )
        except Exception as e:
            print(f"🚨 Failed to send order rejection notification: {e}")
        
        return cancel_order
    
    @post("/{uid}/start-processing", response=OrderResponeWithInfo)
    def start_processing(self, request: AuthenticatedRequest, uid: UUID):
        """
        Chef bắt đầu xử lý đơn hàng (nấu ăn)
        
        Chuyển từ CONFIRMED_SHOP -> PROCESSING
        """
        # Kiểm tra quyền
        order_obj = self.service.orm.get_order_by_uid(uid)
        if not order_obj:
            raise OrderNotFoundException
        if order_obj.chef != request.user:
            from ninja.errors import HttpError
            raise HttpError(403, "You don't have permission to process this order")
        
        from order.services.order_state_machine import OrderStateMachine
        is_valid, error_msg = OrderStateMachine.validate_transition(
            order_obj.status,
            OrderStatusEnum.PROCESSING
        )
        
        if not is_valid:
            raise ValueError(error_msg)
        
        order_obj.status = OrderStatusEnum.PROCESSING
        order_obj.save()
        
        try:
            customer_id = order_obj.owner.id
            chef_name = order_obj.chef.username
            send_order_notification(
                customer_id=customer_id,
                order_id = uid,
                title="Order Started Processing",
                body=f"Your order has started processing by the chef {chef_name}.",
                chef_name=chef_name
            )
        except Exception as e:
            print(f"🚨 Failed to send order started processing notification: {e}")
        
        return self.service.get_order_by_uid(uid=uid)
    
    @post("/{uid}/start-delivery", response=OrderResponeWithInfo)
    def start_delivery(self, request: AuthenticatedRequest, uid: UUID):
        """
        Chef bắt đầu giao hàng
        
        Chuyển từ PROCESSING -> DELIVERING
        """
        # Kiểm tra quyền
        order_obj = self.service.orm.get_order_by_uid(uid)
        if not order_obj:
            raise OrderNotFoundException
        if order_obj.chef != request.user:
            from ninja.errors import HttpError
            raise HttpError(403, "You don't have permission to deliver this order")
        
        from order.services.order_state_machine import OrderStateMachine
        is_valid, error_msg = OrderStateMachine.validate_transition(
            order_obj.status,
            OrderStatusEnum.DELIVERING
        )
        
        if not is_valid:
            raise ValueError(error_msg)
        
        order_obj.status = OrderStatusEnum.DELIVERING
        order_obj.save()
        
        try:
            customer_id = order_obj.owner.id
            chef_name = order_obj.chef.username
            send_order_notification(
                customer_id=customer_id,
                order_id = uid,
                title="Order Started Delivery",
                body=f"Your order has started delivery by the chef {chef_name}.",
                chef_name=chef_name
            )
        except Exception as e:
            print(f"🚨 Failed to send order started delivery notification: {e}")
        
        return self.service.get_order_by_uid(uid=uid)
    
    @post("/{uid}/complete", response=OrderResponeWithInfo)
    def complete_order(self, request: AuthenticatedRequest, uid: UUID):
        """
        Chef đánh dấu đơn hàng hoàn thành
        
        Chuyển từ DELIVERING -> COMPLETED
        - Với PayOS: Trigger payout để chuyển tiền từ escrow cho chef
        - Với COD: Chỉ cập nhật trạng thái
        """
        # Kiểm tra quyền
        order_obj = self.service.orm.get_order_by_uid(uid)
        if not order_obj:
            raise OrderNotFoundException
        if order_obj.chef != request.user:
            from ninja.errors import HttpError
            raise HttpError(403, "You don't have permission to complete this order")
        
        try:
            customer_id = order_obj.owner.id
            chef_name = order_obj.chef.username
            send_order_notification(
                customer_id=customer_id,
                order_id = uid,
                title="Order Completed",
                body=f"Your order has been completed by the chef {chef_name}.",
                chef_name=chef_name
            )
        except Exception as e:
            print(f"🚨 Failed to send order completion notification: {e}")
        
        return self.service.complete_order_with_release(order_uid=uid)


@api(prefix_or_class="checkouts", tags=["Checkout"], auth=AuthBear())
class CheckoutController(Controller):
    def __init__(self, service: OrderService) -> None:
        self.service = service
        
    @post("/", response=CheckoutResponse)
    def checkout(self, request: AuthenticatedRequest):
        return self.service.checkout(user=request.user)
    
    @patch("/{uid}/profile", response=CheckoutResponse)
    def edit_profile_of_checkout(self, request: AuthenticatedRequest, uid: UUID, payload: PersonalInfoSchema):
        return self.service.edit_profile_of_checkout(uid=uid, payload=payload)
    
    @patch("/{uid}/payment-method", response=CheckoutResponse)
    def edit_payment_method_of_checkout(self, request: AuthenticatedRequest, uid: UUID, payload: PaymentMethodEnum):
        return self.service.edit_payment_method_of_checkout(uid=uid, payload=payload)
    
    @patch("/{uid}/delivery-time", response=CheckoutResponse)
    def edit_delivery_time_of_checkout(self, request: AuthenticatedRequest, uid: UUID, payload: time):
        return self.service.edit_delivery_time_of_checkout(uid=uid, payload=payload)
    
    @patch("/{uid}/delivery-address/{address_id}", response=CheckoutResponse)
    def edit_deliver_address_of_checkout(self, request: AuthenticatedRequest, uid: UUID, address_id: int):
        return self.service.edit_deliver_address_of_checkout(user=request.user, uid=uid, address_id=address_id)
    
    @patch("/{uid}/delivery-types", response=CheckoutResponse)
    def edit_delivery_types_of_checkout(self, request: AuthenticatedRequest, uid: UUID, payload: UpdateDeliveryTypesPayload):
        # API này sẽ nhận một list các sub_orders và gọi xuống service để:
        # 1. Update delivery_type cho từng Order
        # 2. Tính lại phí ship (Gọi AhaMove/Lalamove nếu là THIRD_PARTY)
        # 3. Tính lại tổng tiền Checkout
        return self.service.edit_delivery_types_of_checkout(uid=uid, payload=payload)
    
    # @post("/{uid}/apply-voucher", response=CheckoutResponse)
    # def apply_voucher_to_order(self, request: AuthenticatedRequest, uid: UUID, payload: ApplyVoucherSchema):
    #     """Apply voucher cho order trong checkout"""
    #     return self.service.apply_platform_voucher_to_checkout(user=request.user, checkout_uid=uid, voucher_code=payload.voucher_code)
    
    @post("/{uid}/place-order", response=CheckoutResponse)
    def place_order(self, request: AuthenticatedRequest, uid: UUID, bank_code: str = None):
        checkout_response = self.service.place_order(uid=uid, bank_code=bank_code)
        print(f"✅ Order placed with UID {uid}. Preparing to send notification to chef...")
        if hasattr(checkout_response, 'orders') and checkout_response.orders:
            for order_item in checkout_response.orders:
                
                try:
                    # Lấy uid của từng order con
                    individual_order_uid = order_item.uid 
                    
                    order_obj = self.service.orm.get_order_by_uid(individual_order_uid)
                    
                    if order_obj:
                        chef_id = order_obj.chef_id
                        customer_name = order_obj.owner.username
                        
                        # Tùy thuộc vào cách bạn định nghĩa Enum PaymentMethod
                        is_cod = checkout_response.payment_method == PaymentMethodEnum.COD
                        
                        if is_cod:
                            send_order_notification(
                                customer_id=chef_id,
                                order_id=individual_order_uid,
                                title="New COD Order",
                                body=f"You have a new COD order from {customer_name}. Please check and confirm the order.",
                                # Dùng tham số sender_name mà chúng ta đã chuẩn hóa ở bài trước
                                chef_name=customer_name 
                            )
                            print(f"✅ New COD Order {individual_order_uid} placed. Notification sent to chef {chef_id}.")
                        else:
                            print(f"⏳ Order {individual_order_uid} placed with PayOS. Waiting for webhook before sending Noti.")
                            
                except Exception as e:
                    print(f"🚨 Failed to send new order notification for order {order_item.uid}: {e}")

        return checkout_response
    
    @post("/{uid}/apply-platform-voucher", response=CheckoutResponse)
    def apply_platform_voucher(self, request: AuthenticatedRequest, uid: UUID, payload: ApplyPlatformVoucherSchema):
        """
        Apply platform voucher to checkout (PLATFORM_SUBTOTAL or PLATFORM_SHIPPING)
        
        Args:
            uid: Checkout UUID
            payload: Contains voucher_code and voucher_type
            
        Voucher types:
        - PLATFORM_SUBTOTAL: Giảm giá trên sub_total (do admin tạo)
        - PLATFORM_SHIPPING: Giảm phí ship (do admin tạo)
        
        Note: Mỗi checkout có thể apply tối đa 1 voucher mỗi loại
        """
        return self.service.apply_platform_voucher_to_checkout(
            user=request.user,
            checkout_uid=uid,
            voucher_code=payload.voucher_code,
            voucher_type=payload.voucher_type
        )
