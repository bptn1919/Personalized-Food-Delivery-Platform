"""
Order State Machine - Quản lý chuyển trạng thái đơn hàng với Escrow Payment
"""
from utils.enums import OrderStatusEnum, PaymentStatus, PaymentMethodEnum


class OrderStateMachine:
    """
    State Machine với Escrow Payment Flow:
    
    COD Flow:
    DRAFT -> PENDING -> CONFIRMED_SHOP -> PROCESSING -> DELIVERING -> COMPLETED
    
    PayOS Escrow Flow:
    DRAFT -> CONFIRMED_SYSTEM -> CONFIRMED_SHOP -> PROCESSING -> DELIVERING -> COMPLETED -> [RELEASE]
    
    Permissions:
    - Customer cancel: Before CONFIRMED_SHOP only (DRAFT, PENDING, CONFIRMED_SYSTEM)
    - Chef accept/reject: At CONFIRMED_SYSTEM only
    - Release: Move money to internal wallet when COMPLETED and payment is still held
    """
    
    # Các chuyển trạng thái hợp lệ
    VALID_TRANSITIONS = {
        OrderStatusEnum.DRAFT: [
            OrderStatusEnum.PENDING,  # COD place order
            OrderStatusEnum.CONFIRMED_SYSTEM,  # PayOS payment success
            OrderStatusEnum.CANCELLED,  # Cancel before payment
        ],
        OrderStatusEnum.PENDING: [
            OrderStatusEnum.CONFIRMED_SHOP,  # Shop confirms COD order
            OrderStatusEnum.CANCELLED,  # Customer/Shop cancels
        ],
        OrderStatusEnum.CONFIRMED_SYSTEM: [
            OrderStatusEnum.CONFIRMED_SHOP,  # Shop confirms PayOS order
            OrderStatusEnum.CANCELLED,  # Shop cancels (REQUIRES REFUND), Customer cancels (REQUIRES REFUND)
        ],
        OrderStatusEnum.CONFIRMED_SHOP: [
            OrderStatusEnum.PROCESSING,  # Chef starts cooking
            OrderStatusEnum.CANCELLED,  #  🔥 CHANGED: allow system/admin cancel only (not chef/customer)
        ],
        OrderStatusEnum.PROCESSING: [
            OrderStatusEnum.DELIVERING,  # Start delivery
            OrderStatusEnum.CANCELLED,  # Emergency cancel (REQUIRES REFUND if paid)
        ],
        OrderStatusEnum.DELIVERING: [
            OrderStatusEnum.COMPLETED,  # Delivered successfully
            OrderStatusEnum.CANCELLED,  # Delivery failed (REQUIRES REFUND if paid)
        ],
        OrderStatusEnum.COMPLETED: [],  # Final state
        OrderStatusEnum.CANCELLED: [],  # Final state
    }
    
    # Các trạng thái YÊU CẦU REFUND khi cancel
    REFUND_REQUIRED_STATUSES = [
        OrderStatusEnum.CONFIRMED_SYSTEM,
        OrderStatusEnum.PROCESSING,
        OrderStatusEnum.DELIVERING,
        # 🔥 CHANGED: CONFIRMED_SHOP removed (no customer cancel here)
    ]
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """
        Kiểm tra xem có thể chuyển từ trạng thái này sang trạng thái khác không
        
        Args:
            from_status: Trạng thái hiện tại
            to_status: Trạng thái muốn chuyển đến
            
        Returns:
            True nếu hợp lệ, False nếu không
        """
        valid_next_statuses = cls.VALID_TRANSITIONS.get(from_status, [])
        return to_status in valid_next_statuses
    
    @classmethod
    def requires_refund(cls, current_status: str, payment_method: str, payment_status: str) -> bool:
        """
        Kiểm tra xem việc cancel order có yêu cầu refund không
        
        Args:
            current_status: Trạng thái hiện tại của order
            payment_method: Phương thức thanh toán
            payment_status: Trạng thái payment
            
        Returns:
            True nếu cần refund, False nếu không
        """
        # Chỉ refund nếu:
        # 1. Payment method là PayOS (online payment)
        # 2. Payment đã thành công
        # 3. Order ở trạng thái yêu cầu refund


        return (
            payment_method == PaymentMethodEnum.PAYOS and
            # chỉ refund nếu tiền đang HOLDING trong escrow
            payment_status == PaymentStatus.HOLDING and

            current_status in cls.REFUND_REQUIRED_STATUSES
        )
    
    @classmethod
    def get_next_valid_statuses(cls, current_status: str) -> list:
        """
        Lấy danh sách các trạng thái hợp lệ tiếp theo
        
        Args:
            current_status: Trạng thái hiện tại
            
        Returns:
            List các trạng thái có thể chuyển đến
        """
        return cls.VALID_TRANSITIONS.get(current_status, [])
    
    @classmethod
    def validate_transition(cls, from_status: str, to_status: str) -> tuple[bool, str]:
        """
        Validate và trả về kết quả chi tiết
        
        Args:
            from_status: Trạng thái hiện tại
            to_status: Trạng thái muốn chuyển đến
            
        Returns:
            (is_valid, error_message)
        """
        if from_status == to_status:
            return False, f"Order is already in {to_status} status"
        
        if not cls.can_transition(from_status, to_status):
            valid_statuses = cls.get_next_valid_statuses(from_status)
            return False, f"Cannot transition from {from_status} to {to_status}. Valid transitions: {valid_statuses}"
        
        return True, ""
    
    @classmethod
    def can_customer_cancel(cls, order_status: str) -> bool:
        """
        Check if customer can cancel order at current status
        Customer can only cancel before chef confirms (CONFIRMED_SHOP)
        
        Args:
            order_status: Current order status
            
        Returns:
            True if customer can cancel
        """
        allowed_statuses = [
            OrderStatusEnum.DRAFT,
            OrderStatusEnum.PENDING,
            OrderStatusEnum.CONFIRMED_SYSTEM,
        ]
        return order_status in allowed_statuses
    
    @classmethod
    def can_chef_decide(cls, order_status: str) -> bool:
        """
        Check if chef can accept/reject order
        Chef can decide at:
        - PENDING (COD payment - waiting for chef confirmation)
        - CONFIRMED_SYSTEM (PayOS - already paid, waiting for chef confirmation)
        
        Args:
            order_status: Current order status
            
        Returns:
            True if chef can make decision
        """
        allowed_statuses = [
            OrderStatusEnum.PENDING,  # COD flow
            OrderStatusEnum.CONFIRMED_SYSTEM,  # PayOS flow
        ]
        return order_status in allowed_statuses
    
    @classmethod
    def should_trigger_payout(
        cls,
        order_status: str,
        payment_status: str | None = None,
        is_refunded: bool = False
    ) -> bool:

        # 🔥 CHANGED: HOLDING → RELEASED is missing step in your logic
        # payout MUST happen after RELEASED, not HOLDING

        return (
            order_status == OrderStatusEnum.COMPLETED and

            # 🔥 CHANGED:
            # HOLDING is escrow state → NOT payout yet
            payment_status == PaymentStatus.RELEASED and

            not is_refunded
        )


    @classmethod
    def can_release_funds(cls, order_status: str, payment_status: str) -> bool:
        """
        🔥 NEW (recommended)

        RELEASE step tách riêng khỏi payout
        """

        return (
            order_status == OrderStatusEnum.COMPLETED and
            payment_status == PaymentStatus.HOLDING
        )