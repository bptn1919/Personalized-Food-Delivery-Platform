from typing import Optional, Tuple
from uuid import UUID
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from voucher.models import Voucher, AppliedVoucher
from voucher.orm import VoucherORM
from utils.types import TUser
from utils.enums import VoucherTypeEnum, VoucherReservationStatus
from exceptions.vouchers import (
    VoucherNotFoundException,
    VoucherCodeAlreadyExistsException,
    VoucherInvalidException,
    VoucherExpiredException,
    VoucherMinOrderException,
    VoucherNotOwnedException,
    VoucherChefMismatchException,
)
from voucher.schemas import CreateVoucherSchema

class VoucherService:
    """Service xử lý logic voucher"""
    
    def __init__(self):
        self.orm = VoucherORM()
    
    def create_voucher(
        self,
        chef: TUser,
        payload: CreateVoucherSchema
    ) -> Voucher:
       
        # Check code đã tồn tại chưa
        if self.orm.check_code_exists(payload.code):
            raise VoucherCodeAlreadyExistsException
        
        # Validate dates
        if payload.start_date >= payload.end_date:
            raise VoucherInvalidException("Ngày bắt đầu phải trước ngày kết thúc")
        
        # Validate discount_value cho voucher percentage
        if payload.discount_type == "PERCENTAGE":
            if payload.discount_value <= 0 or payload.discount_value > 100:
                raise VoucherInvalidException("Giá trị giảm giá phần trăm phải trong khoảng (0, 100]")
        
        # Create voucher
        voucher = self.orm.create_voucher(
            chef=chef,
            code=payload.code,
            name=payload.name,
            description=payload.description,
            discount_type=payload.discount_type,
            discount_value=Decimal(str(payload.discount_value)),
            max_discount_amount=Decimal(str(payload.max_discount_amount)) if payload.max_discount_amount else None,
            min_order_amount=Decimal(str(payload.min_order_amount)),
            start_date=payload.start_date,
            end_date=payload.end_date,
            usage_limit=payload.usage_limit,
            usage_limit_per_user=payload.usage_limit_per_user,
            is_active=payload.is_active,
        )
        
        return voucher
    
    def get_voucher_by_uid(self, uid: UUID) -> Voucher:
        """Lấy voucher theo UID"""
        voucher = self.orm.get_voucher_by_uid(uid)
        if not voucher:
            raise VoucherNotFoundException
        return voucher
    
    def get_voucher_by_code(self, code: str) -> Voucher:
        """Lấy voucher theo code"""
        voucher = self.orm.get_voucher_by_code(code)
        if not voucher:
            raise VoucherNotFoundException
        return voucher
    
    def get_my_vouchers(self, chef: TUser):
        """Lấy danh sách voucher của chef"""
        return self.orm.get_vouchers_by_chef(chef)
    
    def get_vouchers_by_chef(
        self, 
        chef_id: int, 
        available_only: bool = True,
        user: Optional[TUser] = None
    ):
        """
        Lấy danh sách voucher của một chef
        
        Args:
            chef_id: ID của chef
            available_only: Chỉ lấy voucher còn hiệu lực (default: True)
            user: User để check usage limit per user (nếu available_only=True)
        
        Returns:
            QuerySet voucher
        """
        if available_only:
            return self.get_available_vouchers_by_chef(chef_id, user)
        else:
            # Lấy tất cả voucher active của chef
            return self.orm.get_active_vouchers_by_chef(chef_id)
    
    def get_available_vouchers_by_chef(self, chef_id: int, user: Optional[TUser] = None):
        """
        Lấy danh sách voucher còn hiệu lực của chef
        
        Args:
            chef_id: ID của chef
            user: User để check usage limit per user
        
        Returns:
            QuerySet voucher còn hiệu lực
        """
        vouchers = self.orm.get_active_vouchers_by_chef(chef_id)
        
        # Filter voucher còn lượt sử dụng
        valid_vouchers = []
        for voucher in vouchers:
            # Check tổng usage limit
            active_count = self.orm.count_active_reservations(voucher)
            if voucher.usage_limit and active_count >= voucher.usage_limit:
                continue
            
            # Check user usage limit nếu có user
            if user:
                user_usage = self.orm.get_voucher_usage_count_by_user(voucher, user)
                if user_usage >= voucher.usage_limit_per_user:
                    continue
            
            valid_vouchers.append(voucher.pk)
        
        return vouchers.filter(pk__in=valid_vouchers)
    
    def update_voucher(
        self,
        voucher_uid: UUID,
        chef: TUser,
        **update_data
    ) -> Voucher:
        """
        Cập nhật voucher
        
        Args:
            voucher_uid: UID của voucher
            chef: TUser (chef) cập nhật
            **update_data: Dữ liệu cần cập nhật
        
        Returns:
            Voucher đã cập nhật
        
        Raises:
            VoucherNotFoundException: Nếu voucher không tồn tại
            VoucherNotOwnedException: Nếu chef không sở hữu voucher
        """
        voucher = self.get_voucher_by_uid(voucher_uid)
        
        # Check ownership (Bypass if user is an ADMIN)
        is_admin = chef.groups.filter(name="ADMIN").exists() or chef.is_staff
        if not is_admin and voucher.chef_id != chef.id:
            raise VoucherNotOwnedException()
        
        # Check code conflict nếu update code
        if 'code' in update_data:
            new_code = update_data['code']
            if self.orm.check_code_exists(new_code, exclude_uid=voucher_uid):
                raise VoucherCodeAlreadyExistsException()
        
        # Validate discount_value nếu update voucher_type hoặc discount_value
        voucher_type = update_data.get('voucher_type', voucher.voucher_type)
        if 'discount_value' in update_data:
            discount_value = update_data['discount_value']
            if voucher_type == "PERCENTAGE":
                if discount_value <= 0 or discount_value > 100:
                    raise VoucherInvalidException("Giá trị giảm giá phần trăm phải trong khoảng (0, 100]")
        
        # Update voucher
        return self.orm.update_voucher(voucher, **update_data)
    
    def delete_voucher(self, voucher_uid: UUID, chef: TUser) -> None:
        """
        Xóa voucher
        
        Args:
            voucher_uid: UID của voucher
            chef: TUser (chef) xóa
        
        Raises:
            VoucherNotFoundException: Nếu voucher không tồn tại
            VoucherNotOwnedException: Nếu chef không sở hữu voucher
        """
        voucher = self.get_voucher_by_uid(voucher_uid)
        
        # Check ownership (Bypass if user is an ADMIN)
        is_admin = chef.groups.filter(name="ADMIN").exists() or chef.is_staff
        if not is_admin and voucher.chef_id != chef.id:
            raise VoucherNotOwnedException()
        
        self.orm.delete_voucher(voucher)
    
    def validate_voucher_for_order(
        self,
        code: str,
        order_amount: Decimal,
        chef_id: int,
        user: Optional[TUser] = None
    ) -> Tuple[bool, str, Decimal]:
        """
        Validate voucher cho order
        
        Args:
            code: Mã voucher
            order_amount: Giá trị order (sub_total)
            chef_id: ID của chef (order)
            user: TUser đang sử dụng
        
        Returns:
            Tuple (is_valid, message, discount_amount)
        """
        # Get voucher
        voucher = self.orm.get_voucher_by_code(code)
        if not voucher:
            return False, "Mã voucher không tồn tại", Decimal("0")
        
        # Check voucher thuộc chef của order
        if voucher.chef_id != chef_id:
            return False, "Voucher này không áp dụng cho chef của đơn hàng", Decimal("0")
        
        # Check active
        if not voucher.is_active:
            return False, "Voucher không còn hoạt động", Decimal("0")
        
        # Check date range
        now = timezone.now()
        if now < voucher.start_date:
            return False, "Voucher chưa đến ngày hiệu lực", Decimal("0")
        if now > voucher.end_date:
            return False, "Voucher đã hết hạn", Decimal("0")
        
        # Check usage limit
        active_count = self.orm.count_active_reservations(voucher)
        if voucher.usage_limit and active_count >= voucher.usage_limit:
            return False, "Voucher đã hết lượt sử dụng", Decimal("0")
        
        # Check user usage limit
        if user:
            user_usage = self.orm.get_voucher_usage_count_by_user(voucher, user)
            if user_usage >= voucher.usage_limit_per_user:
                return False, "Bạn đã sử dụng hết lượt cho voucher này", Decimal("0")
        
        # Check min order amount
        if order_amount < Decimal(str(voucher.min_order_amount)):
            return False, f"Đơn hàng tối thiểu phải từ {voucher.min_order_amount:,.0f}đ", Decimal("0")
        
        # Calculate discount
        discount_amount = voucher.calculate_discount(order_amount)
        
        return True, "Voucher hợp lệ", discount_amount
    
    @transaction.atomic
    def apply_voucher_to_order(
        self,
        voucher_code: str,
        order,
        user: TUser
    ) -> Tuple[bool, str, Decimal]:
        """
        Áp dụng voucher cho order
        
        Args:
            voucher_code: Mã voucher
            order: Order instance
            user: TUser đang đặt hàng
        
        Returns:
            Tuple (success, message, discount_amount)
        """
        # Validate voucher
        is_valid, message, discount_amount = self.validate_voucher_for_order(
            code=voucher_code,
            order_amount=order.sub_total,
            chef_id=order.chef_id,
            user=user
        )
        
        if not is_valid:
            raise VoucherInvalidException(message)
        
        # Get voucher for update
        voucher = self.orm.get_voucher_by_code(voucher_code)
        
        # Update order (discount tracked in AppliedVoucher model)
        # Note: order.voucher field is deprecated, use AppliedVoucher instead
        order.discount_amount = discount_amount
        order.total_price = (
            order.sub_total + 
            order.tax_and_fees + 
            order.delivery_fee - 
            discount_amount
        )
        order.save()
        
        # Create usage record
        self.orm.create_voucher_usage(
            voucher=voucher,
            user=user,
            order=order,
            discount_amount=discount_amount
        )
        
        return True, "Áp dụng voucher thành công", discount_amount
    
    # ========== Voucher Reservation Methods ==========
    
    def _calculate_net_subtotal(self, checkout):
        from django.db import models
        orders = checkout.order_fk_checkout.all()
        shop_discounts = (
            AppliedVoucher.objects
            .filter(
                order__in=orders,
                voucher_type=VoucherTypeEnum.SHOP_VOUCHER,
                status__in=[VoucherReservationStatus.RESERVED, VoucherReservationStatus.USED]
            )
            .values("order_id")
            .annotate(total=models.Sum("discount_amount"))
        )

        shop_discount_map = {x["order_id"]: x["total"] for x in shop_discounts}

        net_subtotal = Decimal(0)

        for o in orders:
            shop_discount = shop_discount_map.get(o.uid, Decimal(0))
            net_subtotal += max(o.sub_total - shop_discount, Decimal(0))

        return net_subtotal
    @transaction.atomic
    def apply_platform_voucher_reservation(
        self,
        user: TUser,
        checkout,  # order.models.Checkout
        voucher_code: str,
        voucher_type: str
    ) -> Tuple[AppliedVoucher, Decimal]:
        """
        Apply platform voucher với reservation system
        
        Returns:
            Tuple[AppliedVoucher, Decimal]: (reservation record, discount_amount)
        
        Raises:
            VoucherNotFoundException: Voucher không tồn tại
            VoucherInvalidException: Voucher không hợp lệ hoặc hết quota
        """
        # Validate voucher_type
        if voucher_type not in [VoucherTypeEnum.PLATFORM_SUBTOTAL, VoucherTypeEnum.PLATFORM_SHIPPING]:
            raise VoucherInvalidException("Chỉ platform vouchers (PLATFORM_SUBTOTAL, PLATFORM_SHIPPING) mới có thể apply vào checkout")
        
        # Get voucher with lock
        voucher = self.orm.get_voucher_with_lock(voucher_code, voucher_type)
        if not voucher:
            raise VoucherNotFoundException(f"Voucher không tồn tại hoặc không phải loại {voucher_type}")
        
        # Auto-expire old reservations
        self.orm.expire_old_reservations(voucher)
        
        # Check if THIS CHECKOUT already has a RESERVED platform voucher from this voucher
        existing_reservation = AppliedVoucher.objects.filter(
            voucher=voucher,
            checkout=checkout,
            user=user,
            status=VoucherReservationStatus.RESERVED
        ).first()

        if existing_reservation:
            print(f"Reusing existing platform voucher reservation for checkout {checkout.uid}")
            # Reuse existing reservation (recalculate discount in case checkout changed)
            if voucher_type == VoucherTypeEnum.PLATFORM_SUBTOTAL:
                net_subtotal = self._calculate_net_subtotal(checkout)
                discount_amount = voucher.calculate_discount(net_subtotal)
            else:  # PLATFORM_SHIPPING
                discount_amount = voucher.calculate_shipping_discount(
                    checkout.delivery_fee,
                    checkout.sub_total
                )
            
            reservation = self.orm.update_reservation(
                existing_reservation,
                discount_amount=discount_amount,
                checkout=checkout
            )
            return reservation, discount_amount
        else:
            # Create new reservation - check quotas first
            active_count = self.orm.count_active_reservations(voucher)
            if voucher.usage_limit and active_count >= voucher.usage_limit:
                raise VoucherInvalidException("Voucher đã hết lượt sử dụng")
            
            # Validate voucher (dates, active status)
            is_valid, message = voucher.is_valid()
            if not is_valid:
                raise VoucherInvalidException(message)
            
            # Check user usage limit
            user_count = self.orm.count_user_active_reservations(voucher, user)
            if user_count >= voucher.usage_limit_per_user:
                raise VoucherInvalidException(
                    f"Bạn đã sử dụng voucher này {user_count} lần (giới hạn: {voucher.usage_limit_per_user})"
                )
            
            # Calculate discount
            if voucher_type == VoucherTypeEnum.PLATFORM_SUBTOTAL:
                net_subtotal = self._calculate_net_subtotal(checkout)
                discount_amount = voucher.calculate_discount(net_subtotal)
            else:  # PLATFORM_SHIPPING
                discount_amount = voucher.calculate_shipping_discount(
                    checkout.delivery_fee,
                    checkout.sub_total
                )
            
            # Create reservation
            reservation = self.orm.create_voucher_reservation(
                voucher=voucher,
                user=user,
                voucher_type=voucher_type,
                discount_amount=discount_amount,
                checkout=checkout
            )
            return reservation, discount_amount
    
    @transaction.atomic
    def apply_shop_voucher_reservation(
        self,
        user: TUser,
        order,  # order.models.Order
        voucher_code: str
    ) -> Tuple[AppliedVoucher, Decimal]:
        """
        Apply shop voucher với reservation system
        
        Returns:
            Tuple[AppliedVoucher, Decimal]: (reservation record, discount_amount)
        
        Raises:
            VoucherNotFoundException: Voucher không tồn tại
            VoucherInvalidException: Voucher không hợp lệ hoặc hết quota
        """
        # Get voucher with lock
        voucher = self.orm.get_shop_voucher_with_lock(voucher_code, order.chef)
        if not voucher:
            raise VoucherNotFoundException(
                "Voucher không tồn tại hoặc không phải SHOP_VOUCHER của chef này" + voucher_code
            )
        
        # Auto-expire old reservations
        self.orm.expire_old_reservations(voucher)
        
        # Check if THIS ORDER already has a RESERVED shop voucher from this voucher
        existing_reservation = AppliedVoucher.objects.filter(
            voucher=voucher,
            order=order,
            user=user,
            status=VoucherReservationStatus.RESERVED
        ).first()
        
        if existing_reservation:
            print(f"Reusing existing shop voucher reservation for order {order.uid}")
            # Reuse existing reservation (recalculate discount in case order changed)
            discount_amount = voucher.calculate_discount(order.sub_total)
            reservation = self.orm.update_reservation(
                existing_reservation,
                discount_amount=discount_amount,
                order=order
            )
            return reservation, discount_amount
        else:
            # Create new reservation - check quotas first
            active_count = self.orm.count_active_reservations(voucher)
            if voucher.usage_limit and active_count >= voucher.usage_limit:
                raise VoucherInvalidException("Voucher đã hết lượt sử dụng")
            
            # Validate voucher
            is_valid, message = voucher.is_valid()
            if not is_valid:
                raise VoucherInvalidException(message)
            
            # Check user usage limit
            user_count = self.orm.count_user_active_reservations(voucher, user)
            if user_count >= voucher.usage_limit_per_user:
                raise VoucherInvalidException(
                    f"Bạn đã sử dụng voucher này {user_count} lần (giới hạn: {voucher.usage_limit_per_user})"
                )
            
            # Calculate discount
            discount_amount = voucher.calculate_discount(order.sub_total)
            
            # Create reservation
            reservation = self.orm.create_voucher_reservation(
                voucher=voucher,
                user=user,
                voucher_type=VoucherTypeEnum.SHOP_VOUCHER,
                discount_amount=discount_amount,
                order=order
            )
            return reservation, discount_amount
