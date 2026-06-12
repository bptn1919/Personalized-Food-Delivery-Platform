from typing import Any, List, Optional
from uuid import UUID
from django.db.models import Q
from ninja import Schema, FilterSchema, ModelSchema
from utils.schemas.fields import FilterField
from utils.enums import UserTypeEnum, OrderStatusEnum, PaymentMethodEnum, PaymentStatus, VoucherReservationStatus
from voucher.models import AppliedVoucher
from payment.models import CustomerPaymentInfo
from profile.models import ChefPaymentInfo


# ── Verification review schemas ───────────────────────────────────────────────

class CertAttachmentItemSchema(Schema):
    attachment_uid: UUID
    position: int
    url: str


class AdminCertificateDetailSchema(Schema):
    uid: UUID
    name: str
    certificate_type: str
    status: str
    issued_by: str
    issue_date: str | None = None
    expiry_date: str | None = None
    rejection_reason: str | None = None
    verified_by_email: str | None = None
    verified_at: str | None = None
    attachments: List[CertAttachmentItemSchema] = []


class VerificationReviewSchema(Schema):
    """Dữ liệu admin cần xem để review verification của 1 chef."""
    user_id: int
    user_email: str
    decision: str | None = None
    risk_score: int = 0
    risk_flags: List[str] = []
    face_similarity_score: float | None = None
    verified_identity: Any | None = None       # {full_name, date_of_birth}
    cccd_number_masked: str | None = None
    selfie_url: str | None = None
    cccd_image_urls: List[str] = []            # Chỉ có khi PENDING_REVIEW chưa bị xóa
    certificates: List[AdminCertificateDetailSchema] = []
    verified_at: str | None = None

class VerifyBankAccountRequestSchema(Schema):
    """Schema cho request body khi admin verify/reject bank account"""
    status: bool 

class UserBankAccountSchema(Schema):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str

class CustomerPaymentInfoSchema(ModelSchema):
    account_number: str
    account_holder_name: str
    email: str | None = None
    user: Optional[UserBankAccountSchema] = None

    class Meta:
        model = CustomerPaymentInfo
        fields = [
            "id",
            "bank_name",
            "bank_code",
            "bank_branch",
            "is_verified",
            "verified_at",
            "created_at",
            "updated_at",
        ]

    @staticmethod
    def resolve_account_number(obj):
        return obj.bank_account_number

    @staticmethod
    def resolve_account_holder_name(obj):
        return obj.bank_account_name

    @staticmethod
    def resolve_email(obj):
        return obj.user.email if obj.user else None

    @staticmethod
    def resolve_user(obj):
        if obj.user:
            return {
                "id": obj.user.id,
                "email": obj.user.email,
                "username": obj.user.username,
                "first_name": obj.user.first_name,
                "last_name": obj.user.last_name,
            }
        return None

class ChefPaymentInfoSchema(ModelSchema):
    account_number: str
    account_holder_name: str
    email: str | None = None
    user: Optional[UserBankAccountSchema] = None

    class Meta:
        model = ChefPaymentInfo
        fields = [
            "id",
            "bank_name",
            "bank_code",
            "bank_branch",
            "citizen_id",
            "tax_code",
            "is_verified",
            "verified_at",
            "created_at",
            "updated_at",
            "deleted",
        ]

    @staticmethod
    def resolve_account_number(obj):
        return obj.bank_account_number

    @staticmethod
    def resolve_account_holder_name(obj):
        return obj.bank_account_name

    @staticmethod
    def resolve_email(obj):
        return obj.user.email if obj.user else None

    @staticmethod
    def resolve_user(obj):
        if obj.user:
            return {
                "id": obj.user.id,
                "email": obj.user.email,
                "username": obj.user.username,
                "first_name": obj.user.first_name,
                "last_name": obj.user.last_name,
            }
        return None


class DashboardOverviewSchema(Schema):
    """Schema cho thống kê tổng quan dashboard"""
    total_revenue: float  # Tổng doanh thu
    total_orders: int  # Tổng số đơn hàng
    new_users: int  # Số user mới (trong 30 ngày gần đây)
    active_chefs: int  # Số chef đang hoạt động (có ít nhất 1 đơn)
    cancellation_rate: float  # Tỉ lệ hủy đơn (%)


class RevenueChartItemSchema(Schema):
    """Schema cho mỗi điểm dữ liệu trong biểu đồ"""
    date: str  # Ngày (YYYY-MM-DD)
    revenue: float  # Doanh thu trong ngày
    orders: int  # Số đơn hàng trong ngày


class RevenueChartResponseSchema(Schema):
    """Schema response cho biểu đồ doanh thu"""
    from_date: str
    to_date: str
    data: List[RevenueChartItemSchema]


class PaymentMethodStatItemSchema(Schema):
    """Schema cho thống kê từng phương thức thanh toán"""
    payment_method: str  # Tên phương thức thanh toán
    count: int  # Số lượng đơn hàng sử dụng phương thức này
    percentage: float  # Tỷ lệ phần trăm
    total_amount: float  # Tổng số tiền qua phương thức này


class PaymentMethodStatsResponseSchema(Schema):
    """Schema response cho thống kê phương thức thanh toán"""
    total_orders: int  # Tổng số đơn hàng
    data: List[PaymentMethodStatItemSchema]


class OrderStatusStatItemSchema(Schema):
    """Schema cho thống kê từng trạng thái đơn hàng"""
    status: str  # Trạng thái đơn hàng
    count: int  # Số lượng đơn hàng ở trạng thái này
    percentage: float  # Tỷ lệ phần trăm


class OrderStatusStatsResponseSchema(Schema):
    """Schema response cho thống kê trạng thái đơn hàng"""
    total_orders: int  # Tổng số đơn hàng
    data: List[OrderStatusStatItemSchema]


class DistrictSuccessOrderStatItemSchema(Schema):
    """Schema cho thống kê đơn thành công theo quận"""
    district: str
    success_orders: int
    percentage: float


class DistrictSuccessOrderStatsResponseSchema(Schema):
    """Schema response cho thống kê đơn thành công theo quận"""
    total_success_orders: int
    data: List[DistrictSuccessOrderStatItemSchema]


class TopChefItemSchema(Schema):
    """Schema cho thông tin chef trong top bán chạy"""
    chef_id: int  # ID của chef
    chef_name: str  # Tên chef (username hoặc full name)
    chef_email: str  # Email chef
    total_orders: int  # Tổng số đơn hàng đã bán
    total_revenue: float  # Tổng doanh thu từ chef này
    avatar_url: str | None = None  # URL avatar của chef


class OrderItemSchema(Schema):
    """Schema cho món ăn trong đơn hàng"""
    dish_name: str
    dish_image_url: str | None = None
    quantity: int
    price: float
    subtotal: float


class OrderListItemSchema(Schema):
    """Schema cho item trong danh sách orders"""
    uid: UUID
    customer_name: str | None = None
    customer_email: str | None = None
    chef_name: str | None = None
    chef_email: str | None = None
    total_price: float
    platform_subtotal_discount: float = 0.0
    platform_shipping_discount: float = 0.0
    shop_discount: float = 0.0
    total_discount: float = 0.0
    voucher_code: str | None = None
    status: str
    payment_status: str
    payment_method: str
    created_at: str
    delivery_date: str | None = None
    
    @staticmethod
    def resolve_customer_name(obj):
        if obj.owner:
            full_name = f"{obj.owner.first_name} {obj.owner.last_name}".strip()
            return full_name if full_name else obj.owner.username
        return None
    
    @staticmethod
    def resolve_customer_email(obj):
        return obj.owner.email if obj.owner else None
    
    @staticmethod
    def resolve_chef_name(obj):
        if obj.chef:
            full_name = f"{obj.chef.first_name} {obj.chef.last_name}".strip()
            return full_name if full_name else obj.chef.username
        return None
    
    @staticmethod
    def resolve_chef_email(obj):
        return obj.chef.email if obj.chef else None
    
    @staticmethod
    def resolve_total_price(obj):
        return float(obj.total_price)
    
    @staticmethod
    def resolve_platform_subtotal_discount(obj):
        return float(obj.platform_subtotal_discount or 0)
    
    @staticmethod
    def resolve_platform_shipping_discount(obj):
        return float(obj.platform_shipping_discount or 0)
    
    @staticmethod
    def resolve_shop_discount(obj):
        return float(obj.shop_discount or 0)
    
    @staticmethod
    def resolve_total_discount(obj):
        return float((obj.platform_subtotal_discount or 0) + (obj.platform_shipping_discount or 0) + (obj.shop_discount or 0))
    
    @staticmethod
    def resolve_voucher_code(obj):
        applied_vouchers = AppliedVoucher.objects.filter(
            order=obj,
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).select_related('voucher')
        return ', '.join([av.voucher.code for av in applied_vouchers]) if applied_vouchers.exists() else None
    
    @staticmethod
    def resolve_payment_method(obj):
        return obj.checkout.payment_method if obj.checkout else None
    
    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat()
    
    @staticmethod
    def resolve_delivery_date(obj):
        if obj.checkout and obj.checkout.delivery_date:
            return obj.checkout.delivery_date.isoformat()
        return None


class OrderDetailSchema(Schema):
    """Schema chi tiết đơn hàng"""
    uid: UUID
    
    # Customer info
    customer_id: int | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    
    # Chef info
    chef_id: int | None = None
    chef_name: str | None = None
    chef_email: str | None = None
    
    # Order items
    items: List[OrderItemSchema]
    
    # Pricing
    sub_total: float
    tax_and_fees: float
    delivery_fee: float
    platform_subtotal_discount: float = 0.0
    platform_shipping_discount: float = 0.0
    shop_discount: float = 0.0
    total_discount: float = 0.0
    voucher_code: str | None = None
    total_price: float
    
    # Status
    status: str
    payment_status: str
    payment_method: str
    
    # Delivery info
    delivery_address: str | None = None
    delivery_date: str | None = None
    delivery_time: str | None = None
    
    # Timestamps
    created_at: str
    updated_at: str
    
    @staticmethod
    def resolve_customer_id(obj):
        return obj.owner.id if obj.owner else None
    
    @staticmethod
    def resolve_customer_name(obj):
        if obj.owner:
            full_name = f"{obj.owner.first_name} {obj.owner.last_name}".strip()
            return full_name if full_name else obj.owner.username
        return None
    
    @staticmethod
    def resolve_customer_email(obj):
        return obj.owner.email if obj.owner else None
    
    @staticmethod
    def resolve_customer_phone(obj):
        return obj.owner.phone_number if obj.owner else None
    
    @staticmethod
    def resolve_chef_id(obj):
        return obj.chef.id if obj.chef else None
    
    @staticmethod
    def resolve_chef_name(obj):
        if obj.chef:
            full_name = f"{obj.chef.first_name} {obj.chef.last_name}".strip()
            return full_name if full_name else obj.chef.username
        return None
    
    @staticmethod
    def resolve_chef_email(obj):
        return obj.chef.email if obj.chef else None
    
    @staticmethod
    def resolve_items(obj):
        from order.models import OrderItem
        items = OrderItem.objects.filter(order=obj)
        return [
            {
                'dish_name': item.dish_name,
                'dish_image_url': item.dish_image_url,
                'quantity': item.quantity,
                'price': float(item.price),
                'subtotal': float(item.quantity * item.price)
            }
            for item in items
        ]
    
    @staticmethod
    def resolve_sub_total(obj):
        return float(obj.sub_total)
    
    @staticmethod
    def resolve_tax_and_fees(obj):
        return float(obj.tax_and_fees)
    
    @staticmethod
    def resolve_delivery_fee(obj):
        return float(obj.delivery_fee)
    
    @staticmethod
    def resolve_platform_subtotal_discount(obj):
        return float(obj.platform_subtotal_discount or 0)
    
    @staticmethod
    def resolve_platform_shipping_discount(obj):
        return float(obj.platform_shipping_discount or 0)
    
    @staticmethod
    def resolve_shop_discount(obj):
        return float(obj.shop_discount or 0)
    
    @staticmethod
    def resolve_total_discount(obj):
        return float((obj.platform_subtotal_discount or 0) + (obj.platform_shipping_discount or 0) + (obj.shop_discount or 0))
    
    @staticmethod
    def resolve_voucher_code(obj):
        from voucher.models import AppliedVoucher
        from utils.enums import VoucherReservationStatus
        applied_vouchers = AppliedVoucher.objects.filter(
            order=obj,
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).select_related('voucher')
        return ', '.join([av.voucher.code for av in applied_vouchers]) if applied_vouchers.exists() else None
    
    @staticmethod
    def resolve_total_price(obj):
        return float(obj.total_price)
    
    @staticmethod
    def resolve_payment_method(obj):
        return obj.checkout.payment_method if obj.checkout else None
    
    @staticmethod
    def resolve_delivery_address(obj):
        if obj.checkout and obj.checkout.delivery_address:
            addr = obj.checkout.delivery_address
            return f"{addr.street}, {addr.ward}, {addr.district}, {addr.city}"
        return None
    
    @staticmethod
    def resolve_delivery_date(obj):
        if obj.checkout and obj.checkout.delivery_date:
            return obj.checkout.delivery_date.isoformat()
        return None
    
    @staticmethod
    def resolve_delivery_time(obj):
        if obj.checkout and obj.checkout.delivery_time:
            return obj.checkout.delivery_time.isoformat()
        return None
    
    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat()
    
    @staticmethod
    def resolve_updated_at(obj):
        return obj.updated_at.isoformat()


class FilterOrderSchema(FilterSchema):
    """Filter schema cho danh sách orders"""
    customer_email: Optional[str] = FilterField(
        default=None,
        description="Filter by customer email"
    )
    chef_email: Optional[str] = FilterField(
        default=None,
        description="Filter by chef email"
    )
    status: Optional[str] = FilterField(
        default=None,
        description="Filter by order status",
        json_schema_extra={"enum": [e.value for e in OrderStatusEnum]}
    )
    payment_status: Optional[str] = FilterField(
        default=None,
        description="Filter by payment status",
        json_schema_extra={"enum": [e.value for e in PaymentStatus]}
    )
    payment_method: Optional[str] = FilterField(
        default=None,
        description="Filter by payment method",
        json_schema_extra={"enum": [e.value for e in PaymentMethodEnum]}
    )
    from_date: Optional[str] = FilterField(
        default=None,
        description="Filter orders from date (YYYY-MM-DD)"
    )
    to_date: Optional[str] = FilterField(
        default=None,
        description="Filter orders to date (YYYY-MM-DD)"
    )
    
    def filter_customer_email(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(owner__email__icontains=value)
    
    def filter_chef_email(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(chef__email__icontains=value)
    
    def filter_status(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(status=value.upper())
    
    def filter_payment_status(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(payment_status=value.upper())
    
    def filter_payment_method(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(checkout__payment_method=value.upper())
    
    def filter_from_date(self, value: Optional[str]):
        if value is None:
            return Q()
        from datetime import datetime
        try:
            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
            return Q(created_at__date__gte=date_obj)
        except ValueError:
            return Q()
    
    def filter_to_date(self, value: Optional[str]):
        if value is None:
            return Q()
        from datetime import datetime
        try:
            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
            return Q(created_at__date__lte=date_obj)
        except ValueError:
            return Q()


class FilterUserSchema(FilterSchema):
    """Filter schema cho danh sách users"""
    user_type: Optional[str] = FilterField(
        default=None, 
        description="Filter by user type",
        json_schema_extra={"enum": [e.value for e in UserTypeEnum]}
    )
    search: Optional[str] = FilterField(
        default=None,
        description="Search by username or email"
    )
    is_active: Optional[bool] = FilterField(
        default=None,
        description="Filter by active status"
    )
    from_date: Optional[str] = FilterField(
        default=None,
        description="Filter by joined date from (YYYY-MM-DD)"
    )
    to_date: Optional[str] = FilterField(
        default=None,
        description="Filter by joined date to (YYYY-MM-DD)"
    )
    
    def filter_user_type(self, value: Optional[str]):
        if value is None:
            return Q()
        # So sánh với enum values (case-insensitive)
        value_upper = value.upper()
        if value_upper == UserTypeEnum.CUSTOMER.value:
            return Q(groups__name=UserTypeEnum.CUSTOMER.value)
        elif value_upper == UserTypeEnum.CHEF.value:
            return Q(groups__name=UserTypeEnum.CHEF.value)
        return Q()
    
    def filter_search(self, value: Optional[str]):
        if value is None:
            return Q()
        return Q(username__icontains=value) | Q(email__icontains=value)
    
    def filter_is_active(self, value: Optional[bool]):
        if value is None:
            return Q()
        return Q(is_active=value)
    
    def filter_from_date(self, value: Optional[str]):
        if value is None:
            return Q()
        from datetime import datetime
        try:
            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
            return Q(date_joined__date__gte=date_obj)
        except ValueError:
            return Q()
    
    def filter_to_date(self, value: Optional[str]):
        if value is None:
            return Q()
        from datetime import datetime
        try:
            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
            return Q(date_joined__date__lte=date_obj)
        except ValueError:
            return Q()


class UserListItemSchema(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone_number: str | None = None
    is_active: bool
    is_staff: bool
    groups: List[str] = []  # Danh sách tên các group mà user thuộc về
    date_joined: str
    
    @staticmethod
    def resolve_groups(obj):
        """Resolve groups từ User object"""
        return [group.name for group in obj.groups.all()]
    
    @staticmethod
    def resolve_date_joined(obj):
        """Resolve date_joined thành ISO format string"""
        return obj.date_joined.isoformat()