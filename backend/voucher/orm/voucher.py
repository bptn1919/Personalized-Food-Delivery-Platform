from typing import Optional
from uuid import UUID
from decimal import Decimal
from django.db.models import QuerySet
from django.utils import timezone
from voucher.models import Voucher, AppliedVoucher
from utils.types import User
from order.models import Order, Checkout
from utils.types import TUser
from utils.enums import VoucherTypeEnum, VoucherReservationStatus
from datetime import timedelta

class VoucherORM:
    """ORM layer for Voucher operations"""
    
    def create_voucher(
        self,
        chef: User,
        code: str,
        name: str,
        discount_type: str,
        discount_value: float,
        min_order_amount: float,
        start_date,
        end_date,
        description: Optional[str] = None,
        max_discount_amount: Optional[float] = None,
        usage_limit: Optional[int] = None,
        usage_limit_per_user: int = 1,
        is_active: bool = True,
    ) -> Voucher:
        """Tạo voucher mới"""
        return Voucher.objects.create(
            chef=chef,
            code=code.upper(),
            name=name,
            description=description,
            discount_type=discount_type,
            voucher_type=VoucherTypeEnum.SHOP_VOUCHER, 
            discount_value=discount_value,
            max_discount_amount=max_discount_amount,
            min_order_amount=min_order_amount,
            start_date=start_date,
            end_date=end_date,
            usage_limit=usage_limit,
            usage_limit_per_user=usage_limit_per_user,
            is_active=is_active,
        )
    
    def get_voucher_by_uid(self, uid: UUID) -> Optional[Voucher]:
        """Lấy voucher theo UID"""
        try:
            return Voucher.objects.get(uid=uid)
        except Voucher.DoesNotExist:
            return None
    
    def get_voucher_by_code(self, code: str) -> Optional[Voucher]:
        """Lấy voucher theo code"""
        try:
            return Voucher.objects.get(code=code.upper())
        except Voucher.DoesNotExist:
            return None
    
    def get_vouchers_by_chef(self, chef: User) -> QuerySet[Voucher]:
        """Lấy tất cả voucher của chef"""
        return Voucher.objects.filter(chef=chef).order_by('-created_at')
    
    def get_active_vouchers_by_chef(self, chef_id: int) -> QuerySet[Voucher]:
        """Lấy voucher đang active của chef"""
        now = timezone.now()
        return Voucher.objects.filter(
            chef_id=chef_id,
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-created_at')
    
    def update_voucher(self, voucher: Voucher, **kwargs) -> Voucher:
        """Cập nhật voucher"""
        for key, value in kwargs.items():
            if value is not None:
                setattr(voucher, key, value)
        voucher.save()
        return voucher
    
    def delete_voucher(self, voucher: Voucher) -> None:
        """Xóa voucher"""
        voucher.delete()
    
    def get_voucher_usage_count_by_user(self, voucher: Voucher, user: User) -> int:
        """Đếm số lần user đã dùng voucher"""
        return AppliedVoucher.objects.filter(voucher=voucher, user=user).count()
    
    def check_code_exists(self, code: str, exclude_uid: Optional[UUID] = None) -> bool:
        """Kiểm tra code đã tồn tại chưa"""
        queryset = Voucher.objects.filter(code=code.upper())
        if exclude_uid:
            queryset = queryset.exclude(uid=exclude_uid)
        return queryset.exists()
    
    # ========== Voucher Reservation Methods ==========
    
    def get_voucher_with_lock(self, code: str, voucher_type: str) -> Optional[Voucher]:
        """Get voucher với lock (select_for_update) cho reservation system"""
        try:
            return Voucher.objects.select_for_update().get(
                code=code.upper(),
                voucher_type=voucher_type,
                is_active=True
            )
        except Voucher.DoesNotExist:
            return None
    
    def get_shop_voucher_with_lock(self, code: str, chef: User) -> Optional[Voucher]:
        """Get shop voucher với lock"""
        try:
            return Voucher.objects.select_for_update().get(
                code=code.upper(),
                chef=chef,
                voucher_type=VoucherTypeEnum.SHOP_VOUCHER,
                is_active=True
            )
        except Voucher.DoesNotExist:
            return None
    
    def expire_old_reservations(self, voucher: Voucher) -> int:
        """Auto-expire các reservations đã hết hạn"""
        return AppliedVoucher.objects.filter(
            voucher=voucher,
            status=VoucherReservationStatus.RESERVED,
            reservation_expires_at__lt=timezone.now()
        ).update(status=VoucherReservationStatus.EXPIRED)
    
    def get_existing_reservation(self, voucher: Voucher, user: User) -> Optional[AppliedVoucher]:
        """Get existing RESERVED voucher của user"""
        return AppliedVoucher.objects.filter(
            voucher=voucher,
            user=user,
            status=VoucherReservationStatus.RESERVED
        ).first()
    
    def count_active_reservations(self, voucher: Voucher) -> int:
        """Đếm số lượng reservations đang active (RESERVED + USED)"""
        return AppliedVoucher.objects.filter(
            voucher=voucher,
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).count()
    
    def count_user_active_reservations(self, voucher: Voucher, user: User) -> int:
        """Đếm số lượng reservations của user (RESERVED + USED)"""
        return AppliedVoucher.objects.filter(
            voucher=voucher,
            user=user,
            status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
        ).count()
    
    def create_voucher_reservation(
        self,
        voucher: Voucher,
        user: User,
        voucher_type: str,
        discount_amount: Decimal,
        checkout: Optional[Checkout] = None,
        order: Optional[Order] = None
    ) -> AppliedVoucher:
        """Tạo voucher reservation mới"""
        
        # For shop vouchers applied to orders, also store checkout reference
        if order and not checkout:
            checkout = order.checkout
        
        return AppliedVoucher.objects.create(
            voucher=voucher,
            checkout=checkout,
            order=order,
            user=user,
            voucher_type=voucher_type,
            discount_amount=discount_amount,
            status=VoucherReservationStatus.RESERVED,
            reservation_expires_at=timezone.now() + timedelta(minutes=15)
        )
    
    def update_reservation(
        self,
        reservation: AppliedVoucher,
        discount_amount: Decimal,
        checkout: Optional[Checkout] = None,
        order: Optional[Order] = None
    ) -> AppliedVoucher:
        """Update existing reservation với checkout/order mới"""
        
        
        if checkout:
            reservation.checkout = checkout
            reservation.order = None
        if order:
            reservation.order = order
            # Keep checkout reference for shop vouchers
            if not reservation.checkout:
                reservation.checkout = order.checkout
        
        reservation.discount_amount = discount_amount
        reservation.reservation_expires_at = timezone.now() + timedelta(minutes=15)
        reservation.save()
        return reservation
