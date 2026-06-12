from django.db import models
from django.utils import timezone
from decimal import Decimal
from utils.models import BaseModel
from utils.types import User
from utils.enums import VoucherDiscountTypeEnum, VoucherTypeEnum, VoucherReservationStatus
from django.db.models import Q, UniqueConstraint


class Voucher(BaseModel):
    
    chef = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="voucher_fk_chef",
        help_text="Chef tạo voucher này, dùng cho SHOP_SUBTOTAL",
        db_column="chef_id",
        null=True,
        blank=True
    )
    
    code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Mã voucher (vd: SUMMER2024)"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Tên voucher"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Mô tả chi tiết voucher"
    )
    
    voucher_type = models.CharField(
        max_length=30,
        choices=VoucherTypeEnum.choices,
        help_text="Loại voucher: SHOP_VOUCHER, PLATFORM_SUBTOTAL, PLATFORM_SHIPPING"
    )

    discount_type = models.CharField(
        max_length=20,
        choices=VoucherDiscountTypeEnum.choices,
        default=VoucherDiscountTypeEnum.PERCENTAGE,
        help_text="Loại giảm giá: % hoặc số tiền cố định"
    )
    
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Giá trị giảm (% hoặc số tiền)"
    )
    
    max_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Số tiền giảm tối đa (cho voucher %)"
    )
    
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Giá trị đơn hàng tối thiểu để áp dụng"
    )
    
    start_date = models.DateTimeField(
        help_text="Ngày bắt đầu hiệu lực"
    )
    
    end_date = models.DateTimeField(
        help_text="Ngày hết hạn"
    )
    
    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Số lần sử dụng tối đa (null = không giới hạn)"
    )
    
    usage_limit_per_user = models.PositiveIntegerField(
        default=1,
        help_text="Số lần mỗi user có thể dùng"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Voucher có đang hoạt động không"
    )
    
    class Meta:
        db_table = "voucher"
        ordering = ["-created_at"]
        unique_together = [["chef", "code"]]
        indexes = [
            models.Index(fields=["chef", "code"]),
            models.Index(fields=["chef", "is_active", "start_date", "end_date"]),
        ]
        
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def is_valid(self):
        """Kiểm tra voucher còn hiệu lực không (không check usage_limit - đã check bằng reservation system)"""
        now = timezone.now()
        
        if not self.is_active:
            return False, "Voucher không còn hoạt động"
            
        if now < self.start_date:
            return False, "Voucher chưa đến ngày hiệu lực"
            
        if now > self.end_date:
            return False, "Voucher đã hết hạn"
            
        # NOTE: usage_limit check is done in apply_voucher functions using reservation system
        # We count RESERVED + USED AppliedVoucher records instead of usage_count field
            
        return True, "Voucher hợp lệ"
    
    def calculate_discount(self, sub_total_amount):
        """Tính số tiền giảm giá (chỉ áp dụng cho sub_total, không bao gồm phí vận chuyển/thuế)"""
        # Convert to Decimal for consistent calculation
        sub_total = Decimal(str(sub_total_amount))
        
        if sub_total < self.min_order_amount:
            return Decimal('0')
            
        if self.discount_type == VoucherDiscountTypeEnum.FIXED_AMOUNT:
            return min(self.discount_value, sub_total)
        else:  # PERCENTAGE
            discount = sub_total * (self.discount_value / Decimal('100'))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            return discount
    
    def calculate_shipping_discount(self, delivery_fee_amount, checkout_subtotal):
        """
        Tính số tiền giảm cho phí vận chuyển
        
        Args:
            delivery_fee_amount: Phí vận chuyển cần tính discount
            checkout_subtotal: Subtotal của checkout để validate min_order_amount
            
        Returns:
            Decimal: Số tiền được giảm
        """
        delivery_fee = Decimal(str(delivery_fee_amount))
        subtotal = Decimal(str(checkout_subtotal))
        
        # Validate min_order_amount based on checkout subtotal, not delivery fee
        if subtotal < self.min_order_amount:
            return Decimal('0')
        
        # Calculate discount on delivery fee
        if self.discount_type == VoucherDiscountTypeEnum.FIXED_AMOUNT:
            # Fixed amount: discount up to delivery fee amount
            return min(self.discount_value, delivery_fee)
        else:  # PERCENTAGE
            # Percentage: apply to delivery fee
            discount = delivery_fee * (self.discount_value / Decimal('100'))
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
            # Can't discount more than the delivery fee itself
            return min(discount, delivery_fee)

class AppliedVoucher(models.Model):
    """Model lưu trữ thông tin voucher đã apply vào Checkout hoặc Order với reservation system"""
    voucher = models.ForeignKey(
        to="voucher.Voucher", 
        on_delete=models.CASCADE,
        related_name="applied_vouchers"
    )
    checkout = models.ForeignKey(
        to="order.Checkout", 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name="checkout_applied_vouchers"
    )
    order = models.ForeignKey(
        to="order.Order", 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        related_name="order_applied_vouchers"
    )
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="user_applied_vouchers",
        help_text="User đã apply voucher này"
    )
    voucher_type = models.CharField(
        max_length=30,
        choices=VoucherTypeEnum.choices,
        help_text="Loại voucher: SHOP_VOUCHER, PLATFORM_SUBTOTAL, PLATFORM_SHIPPING"
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Số tiền giảm giá thực tế"
    )
    status = models.CharField(
        max_length=20,
        choices=VoucherReservationStatus.choices,
        default=VoucherReservationStatus.RESERVED,
        help_text="Trạng thái: RESERVED (giữ chỗ), USED (đã dùng), CANCELLED (hủy), EXPIRED (hết hạn)"
    )
    reservation_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Thời điểm hết hạn reservation (15 phút sau khi apply)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_expired(self):
        """Check if reservation has expired"""
        if self.status != VoucherReservationStatus.RESERVED:
            return False
        if not self.reservation_expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.reservation_expires_at
    
    class Meta:
        constraints = [
            # 1 SHOP voucher / order
            UniqueConstraint(
                fields=["order", "voucher_type"],
                condition=Q(voucher_type=VoucherTypeEnum.SHOP_VOUCHER),
                name="unique_shop_voucher_per_order"
            ),

            # 1 PLATFORM voucher / checkout
            UniqueConstraint(
                fields=["checkout", "voucher_type"],
                condition=Q(voucher_type=VoucherTypeEnum.PLATFORM_SUBTOTAL),
                name="unique_platform_subtotal_voucher_per_checkout"
            ),

            # 1 SHIPMENT voucher / checkout
            UniqueConstraint(
                fields=["checkout", "voucher_type"],
                condition=Q(voucher_type=VoucherTypeEnum.PLATFORM_SHIPPING),
                name="unique_platform_shipping_voucher_per_checkout"
            ),
        ]