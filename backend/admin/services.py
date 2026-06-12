from decimal import Decimal

from django.contrib import auth as django_auth
from django.db.models import Q
from django.utils import timezone
from exceptions.vouchers import VoucherCodeAlreadyExistsException, VoucherInvalidException
from ninja.errors import HttpError
from payment.models import CustomerPaymentInfo
from profile.models import ChefPaymentInfo
from certificate.models import Certificate
from certificate.orm.certificate import CertificateORM
from voucher.models import Voucher
from voucher.orm.voucher import VoucherORM
from voucher.schemas.request import AdminCreateVoucherSchema
from utils.enums import CertificateStatusEnum
from utils.services.base import BaseService
from utils.types import  TUser
from .queries import Query


class Service(BaseService):
    auth = django_auth

    def __init__(self):
        self.query = Query()
        self.voucher_orm= VoucherORM()

    def get_users_list(self, filter=None):
        """
        Lấy danh sách users với filter (chỉ dành cho admin)
        Trả về queryset để @paginate decorator xử lý
        """
        return self.query.get_users_list(filter=filter)
    
    def deactivate_user(self, user_id: int) -> bool:
        """Admin deactive user (soft delete)"""
        return self.query.set_user_active_status(user_id=user_id, is_active=False)


    def activate_user(self, user_id: int) -> bool:
        """Admin activate user (soft delete)"""
        return self.query.set_user_active_status(user_id=user_id, is_active=True)
    
    def get_dashboard_overview(self):
        """Lấy thống kê tổng quan cho dashboard"""
        return self.query.get_dashboard_overview()
    
    def get_revenue_chart(self, from_date, to_date):
        """Lấy dữ liệu doanh thu theo ngày cho biểu đồ"""
        return self.query.get_revenue_chart(from_date=from_date, to_date=to_date)
    
    def get_payment_method_stats(self):
        """Lấy thống kê tỷ lệ sử dụng phương thức thanh toán"""
        return self.query.get_payment_method_stats()
    
    def get_order_status_stats(self):
        """Lấy thống kê tỷ lệ trạng thái đơn hàng"""
        return self.query.get_order_status_stats()

    def get_success_orders_by_district(self, from_date=None, to_date=None):
        """Lấy thống kê đơn thành công theo quận"""
        return self.query.get_success_orders_by_district(from_date=from_date, to_date=to_date)
    
    def get_top_chefs(self, limit=5):
        """Lấy top chefs có lượt bán cao nhất"""
        return self.query.get_top_chefs(limit=limit)
    
    def get_orders_list(self, filter=None):
        """Lấy danh sách orders với filter"""
        return self.query.get_orders_list(filter=filter)
    
    def get_order_detail(self, order_uid: str):
        """Lấy chi tiết một order"""
        return self.query.get_order_detail(order_uid=order_uid)

    def set_certificate_status(
        self,
        certificate_uid: str,
        status: CertificateStatusEnum,
        verified_by: TUser,
    ):
        """Admin update trạng thái certificate"""
        try:
            certificate = CertificateORM.set_certificate_status(
                uid=certificate_uid,
                status=status,
                verified_by=verified_by,
            )
        except Certificate.DoesNotExist:
            raise HttpError(404, "Certificate not found")

        # Khi admin review xong, kiểm tra xem đây có phải certificate cuối không.
        # Nếu hết PENDING → schedule xóa CCCD + selfie sau 30 ngày.
        try:
            from certificate.services import CertificateService
            CertificateService()._cleanup_selfie_if_fully_reviewed(uid=certificate.uid)
        except Exception as exc:
            import logging
            logging.getLogger("django").error("cleanup after admin review failed: %s", exc)

        return bool(certificate)

    def verify_bank_account(
        self,
        bank_account_id: int,
        verified_by: TUser,
        status: bool,
    ):
        """Admin verify/reject bank account cho customer hoặc chef"""
        customer_bank = (
            CustomerPaymentInfo.objects.select_related("user")
            .filter(pk=bank_account_id)
            .first()
        )
        if customer_bank:
            customer_bank.is_verified = status
            customer_bank.verified_at = timezone.now() if status else None
            customer_bank.save(update_fields=["is_verified", "verified_at", "updated_at"])
            return customer_bank

        chef_bank = (
            ChefPaymentInfo.objects.select_related("user")
            .filter(pk=bank_account_id, deleted=False)
            .first()
        )
        if chef_bank:
            chef_bank.is_verified = status
            chef_bank.verified_at = timezone.now() if status else None
            chef_bank.save(update_fields=["is_verified", "verified_at", "updated_at"])
            return chef_bank

        raise HttpError(404, "Bank account not found")

    def get_chefs_bank_accounts(self, status=None, search=None):
        """Lấy danh sách bank account của chef để admin duyệt"""
        queryset = ChefPaymentInfo.objects.select_related("user").filter(deleted=False).order_by("-created_at")
        if status is not None:
            queryset = queryset.filter(is_verified=status)
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search)
                | Q(user__username__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )
        return queryset

    def get_customers_bank_accounts(self, status=None, search=None):
        """Lấy danh sách bank account của customer để admin duyệt"""
        queryset = CustomerPaymentInfo.objects.select_related("user").order_by("-created_at")
        if status is not None:
            queryset = queryset.filter(is_verified=status)
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search)
                | Q(user__username__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )
        return queryset
    

    def create_voucher(
        self,
        chef: TUser,
        payload: AdminCreateVoucherSchema
    ) -> Voucher:
       
        # Check code đã tồn tại chưa
        if self.voucher_orm.check_code_exists(payload.code):
            raise VoucherCodeAlreadyExistsException
        
        # Validate dates
        if payload.start_date >= payload.end_date:
            raise VoucherInvalidException("Ngày bắt đầu phải trước ngày kết thúc")
        
        # Validate discount_value cho voucher percentage
        if payload.discount_type == "PERCENTAGE":
            if payload.discount_value <= 0 or payload.discount_value > 100:
                raise VoucherInvalidException("Giá trị giảm giá phần trăm phải trong khoảng (0, 100]")
        
        #Validate voucher type
        if payload.voucher_type not in ["PLATFORM_SUBTOTAL", "PLATFORM_SHIPPING"]:
            raise VoucherInvalidException("Admin chỉ được tạo voucher loại PLATFORM_SUBTOTAL hoặc PLATFORM_SHIPPING")
        
        # Create voucher
        voucher = self.query.create_voucher(
            chef=chef,
            code=payload.code,
            name=payload.name,
            description=payload.description,
            voucher_type=payload.voucher_type,
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
    
    def list_vouchers(self):
        """Lấy danh sách tất cả voucher (Admin only)"""
        return self.query.list_vouchers()

    def get_verification_review_data(self, user_id: int):
        """Lấy dữ liệu verification của 1 chef để admin review"""
        return self.query.get_verification_review_data(user_id=user_id)
    