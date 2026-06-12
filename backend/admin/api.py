from ninja import Query
from datetime import date

from voucher.schemas.request import AdminCreateVoucherSchema, CreateVoucherSchema
from voucher.schemas.response import VoucherDetailSchema
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, get, patch, post, put
from utils.router.paginate import paginate
from utils.types import AuthenticatedRequest
from utils.exceptions import PermissionDeniedError
from utils.enums import CertificateStatusEnum

from .schemas import (
    TopChefItemSchema,
    UserListItemSchema,
    FilterUserSchema,
    DashboardOverviewSchema,
    RevenueChartResponseSchema,
    PaymentMethodStatsResponseSchema,
    OrderStatusStatsResponseSchema,
    DistrictSuccessOrderStatsResponseSchema,
    OrderListItemSchema,
    OrderDetailSchema,
    FilterOrderSchema,
    CustomerPaymentInfoSchema,
    ChefPaymentInfoSchema,
    VerifyBankAccountRequestSchema,
    VerificationReviewSchema,
)
from .services import Service
from .permissions import require_admin
from typing import List 

@api(prefix_or_class="admin", tags=["Admin"], auth=AuthBear())
class AdminController(Controller):
    def __init__(self, service: Service):
        self.service = service

    @get("/users", auth=True, response=UserListItemSchema, paginate=True, exceptions=(PermissionDeniedError,))
    @paginate
    @require_admin
    def get_users_list(
        self, 
        request: AuthenticatedRequest, 
        filter: FilterUserSchema = Query(...)
    ):
        """
        API lấy danh sách users cho admin với pagination và filter
        
        Query Parameters:
        - user_type: 'customer' hoặc 'chef' (filter theo role)
        - search: tìm kiếm theo username hoặc email
        - is_active: true/false (filter theo trạng thái active)
        - from_date: lọc user từ ngày (YYYY-MM-DD)
        - to_date: lọc user đến ngày (YYYY-MM-DD)
        - page: trang hiện tại (pagination)
        - per_page: số lượng items per page (pagination)
        
        Example: /auth/admin/users?user_type=customer&search=john&from_date=2026-01-01&to_date=2026-03-01&page=1&per_page=20
        """
        # Trả về queryset, @paginate decorator sẽ tự động xử lý pagination
        return self.service.get_users_list(filter=filter)

    @patch("/users/{user_id}/deactivate", auth=True, response=bool, exceptions=(PermissionDeniedError,))
    @require_admin
    def deactivate_user(self, request: AuthenticatedRequest, user_id: int):
        """API để admin deactivate một user (soft delete)"""
        return self.service.deactivate_user(user_id=user_id)
    
    @patch("/users/{user_id}/activate", auth=True, response=bool, exceptions=(PermissionDeniedError,))
    @require_admin
    def activate_user(self, request: AuthenticatedRequest, user_id: int):
        """API để admin activate một user đã bị deactivate"""
        return self.service.activate_user(user_id=user_id)

    @get("/dashboard/overview", auth=True, response=DashboardOverviewSchema, exceptions=(PermissionDeniedError,))
    @require_admin
    def get_dashboard_overview(self, request: AuthenticatedRequest):
        """
        API lấy thống kê tổng quan cho admin dashboard
        
        Trả về:
        - total_revenue: Tổng doanh thu (đơn đã hoàn thành và đã thu tiền)
        - total_orders: Tổng số đơn hàng
        - new_users: Số user mới trong 30 ngày gần đây
        - active_chefs: Số chef đang hoạt động (có ít nhất 1 đơn hàng)
        - cancellation_rate: Tỉ lệ hủy đơn (%)
        """
        return self.service.get_dashboard_overview()
    
    @get("/dashboard/revenue-chart", auth=True, response=RevenueChartResponseSchema, exceptions=(PermissionDeniedError,))
    @require_admin
    def get_revenue_chart(
        self, 
        request: AuthenticatedRequest,
        from_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
        to_date: str = Query(..., description="End date (YYYY-MM-DD)")
    ):
        """
        API lấy dữ liệu doanh thu theo ngày cho biểu đồ
        
        Query Parameters:
        - from_date: Ngày bắt đầu (format: YYYY-MM-DD)
        - to_date: Ngày kết thúc (format: YYYY-MM-DD)
        
        Example: /api/admin/dashboard/revenue-chart?from_date=2026-01-01&to_date=2026-01-31
        
        Trả về:
        - Doanh thu và số đơn hàng theo từng ngày trong khoảng thời gian
        """
        from datetime import datetime
        
        # Parse dates
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
        
        return self.service.get_revenue_chart(from_date=from_date_obj, to_date=to_date_obj)
    
    @get("/dashboard/payment-methods", auth=True, response=PaymentMethodStatsResponseSchema, exceptions=(PermissionDeniedError,))
    @require_admin
    def get_payment_method_stats(self, request: AuthenticatedRequest):
        """
        API lấy thống kê tỷ lệ phần trăm sử dụng của từng phương thức thanh toán
        
        Trả về:
        - total_orders: Tổng số giao dịch đã thu tiền
        - data: Danh sách thống kê cho từng phương thức thanh toán
          + payment_method: Tên phương thức (COD, PAYOS)
          + count: Số lượng giao dịch
          + percentage: Tỷ lệ phần trăm sử dụng
          + total_amount: Tổng số tiền qua phương thức này
        """
        return self.service.get_payment_method_stats()
    
    @get("/dashboard/order-status", auth=True, response=OrderStatusStatsResponseSchema, exceptions=(PermissionDeniedError,))
    @require_admin
    def get_order_status_stats(self, request: AuthenticatedRequest):
        """
        API lấy thống kê tỷ lệ phần trăm từng trạng thái đơn hàng
        
        Trả về:
        - total_orders: Tổng số đơn hàng
        - data: Danh sách thống kê cho từng trạng thái
          + status: Trạng thái đơn hàng (DRAFT, PENDING, CONFIRMED_SYSTEM, CONFIRMED_SHOP, PROCESSING, DELIVERING, COMPLETED, CANCELLED)
          + count: Số lượng đơn hàng ở trạng thái này
          + percentage: Tỷ lệ phần trăm
        """
        return self.service.get_order_status_stats()

    @get("/dashboard/success-orders-by-district", auth=True, response=DistrictSuccessOrderStatsResponseSchema, exceptions=(PermissionDeniedError,))
    @require_admin
    def get_success_orders_by_district(
        self,
        request: AuthenticatedRequest,
        from_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
        to_date: date = Query(None, description="End date (YYYY-MM-DD)")
    ):
        """
        API lấy số lượng và tỉ lệ (%) đơn hàng thành công theo từng quận

        Query Parameters (optional):
        - from_date: Ngày bắt đầu (YYYY-MM-DD)
        - to_date: Ngày kết thúc (YYYY-MM-DD)

        Chỉ tính đơn hàng thành công (status = COMPLETED).
        """
        return self.service.get_success_orders_by_district(from_date=from_date, to_date=to_date)
    
    @get("/dashboard/top-chefs", auth=True, response=List[TopChefItemSchema], exceptions=(PermissionDeniedError,))
    @require_admin
    def get_top_chefs(
        self, 
        request: AuthenticatedRequest,
        limit: int = Query(5, description="Số lượng chef cần lấy (mặc định 5)")
    ):
        """
        API lấy top chefs có lượt bán cao nhất
        
        Query Parameters:
        - limit: Số lượng chef cần lấy (mặc định 5, tối đa 20)
        
        Trả về:
        - data: Danh sách top chefs
          + chef_id: ID của chef
          + chef_name: Tên chef
          + chef_email: Email chef
          + total_orders: Tổng số đơn hàng đã hoàn thành
          + total_revenue: Tổng doanh thu
          + avatar_url: URL avatar (nếu có)
        
        Chỉ tính các đơn hàng đã hoàn thành (COMPLETED)
        """
        # Giới hạn limit tối đa 20
        limit = min(limit, 20)
        return self.service.get_top_chefs(limit=limit)
    
    @get("/orders", auth=True, response=OrderListItemSchema, paginate=True, exceptions=(PermissionDeniedError,))
    @paginate
    @require_admin
    def get_orders_list(
        self,
        request: AuthenticatedRequest,
        filter: FilterOrderSchema = Query(...)
    ):
        """
        API lấy danh sách orders cho admin với pagination và filter
        
        Query Parameters:
        - customer_email: Tìm kiếm theo email khách hàng
        - chef_email: Tìm kiếm theo email chef
        - status: Lọc theo trạng thái đơn (DRAFT, PENDING, CONFIRMED_SYSTEM, CONFIRMED_SHOP, PROCESSING, DELIVERING, COMPLETED, CANCELLED)
        - payment_status: Lọc theo trạng thái thanh toán (PENDING, SUCCESS, HOLDING, RELEASED, REFUND_PENDING, REFUNDED, FAILED, CANCELLED)
        - payment_method: Lọc theo phương thức thanh toán (COD, PAYOS)
        - from_date: Lọc đơn hàng từ ngày (YYYY-MM-DD)
        - to_date: Lọc đơn hàng đến ngày (YYYY-MM-DD)
        - page: Trang hiện tại (pagination)
        - per_page: Số lượng items per page (pagination)
        
        Example: /api/admin/orders?customer_email=john@example.com&status=COMPLETED&from_date=2026-01-01&to_date=2026-03-01&page=1&per_page=20
        """
        return self.service.get_orders_list(filter=filter)
    
    @get("/orders/{order_uid}", auth=True, response=OrderDetailSchema, exceptions=(PermissionDeniedError,))
    @require_admin
    def get_order_detail(
        self,
        request: AuthenticatedRequest,
        order_uid: str
    ):
        """
        API lấy chi tiết một order
        
        Path Parameters:
        - order_uid: UID của order
        
        Trả về:
        - Thông tin chi tiết đầy đủ về order bao gồm:
          + Thông tin khách hàng và chef
          + Danh sách món ăn
          + Thông tin giá cả
          + Trạng thái và phương thức thanh toán
          + Địa chỉ và thời gian giao hàng
        """
        order = self.service.get_order_detail(order_uid=order_uid)
        if not order:
            raise PermissionDeniedError("Order not found")
        return order
    
    @post("/voucher", response=VoucherDetailSchema)
    @require_admin
    def create_voucher(self, request: AuthenticatedRequest, payload: AdminCreateVoucherSchema):
        """
        Tạo voucher mới (Admin only)
        
        Admin tạo voucher áp dụng cho các món ăn của các chef hoặc chi phí vận chuyển
        """
        return self.service.create_voucher(chef=request.user, payload=payload)

    @get("/voucher", response=List[VoucherDetailSchema])
    @require_admin
    def list_vouchers(self, request: AuthenticatedRequest):
        """
        Lấy danh sách tất cả voucher (Admin only)
        """
        return self.service.list_vouchers()
    
    @get("/verification/{user_id}", auth=True, response=VerificationReviewSchema, exceptions=(PermissionDeniedError,))
    @require_admin
    def get_verification_review(self, request: AuthenticatedRequest, user_id: int):
        """
        [Admin] Lấy toàn bộ dữ liệu verification của 1 chef để review.

        Trả về:
        - decision, risk_score, risk_flags, face_similarity_score
        - verified_identity: {full_name, date_of_birth}
        - cccd_number_masked
        - selfie_url: URL ảnh selfie (nếu còn — PENDING_REVIEW)
        - cccd_image_urls: URLs ảnh CCCD mặt trước/sau (nếu còn — PENDING_REVIEW)
        - certificates: danh sách ĐKKD + ATTP kèm attachment URLs
        """
        data = self.service.get_verification_review_data(user_id=user_id)
        if data is None:
            raise PermissionDeniedError("Không tìm thấy phiên xác minh cho user này.")
        return data

    @patch("/certificate/{certificate_uid}", auth=True, response=bool, exceptions=(PermissionDeniedError,))
    @require_admin
    def set_certificate_status(
        self,
        request: AuthenticatedRequest,
        certificate_uid: str,
        status: CertificateStatusEnum = Query(..., description="Certificate status")
    ):
        """Admin active/deactive certificate"""
        return self.service.set_certificate_status(certificate_uid=certificate_uid, status=status, verified_by=request.user)
    
    #admin verifed customer bank 
    @patch("/bank-accounts/customers/{bank_account_id}/verification", auth=True, response=CustomerPaymentInfoSchema)
    @require_admin
    def verify_bank_account(self, request: AuthenticatedRequest, bank_account_id: int, payload: VerifyBankAccountRequestSchema):
        """Admin verified customer bank account or chef bank account"""
        return self.service.verify_bank_account(bank_account_id=bank_account_id, verified_by=request.user, status=payload.status)
    
    #admin verifed chef bank account
    @patch("/bank-accounts/chefs/{bank_account_id}/verification", auth=True, response=ChefPaymentInfoSchema)
    @require_admin
    def verify_chef_bank_account(self, request: AuthenticatedRequest, bank_account_id: int, payload: VerifyBankAccountRequestSchema):
        """Admin verified chef bank account"""
        return self.service.verify_bank_account(bank_account_id=bank_account_id, verified_by=request.user, status=payload.status)

    
    #admin get list bank chef, paginate, filter status, search by chef email
    @get("/bank-accounts/chefs", auth=True, response=ChefPaymentInfoSchema, paginate=True)
    @paginate
    @require_admin
    def get_chefs_bank_accounts(
        self, 
        request: AuthenticatedRequest, 
        status: bool | None = Query(None, description="Filter by verification status"),
        search: str | None = Query(None, description="Search by chef email")
    ):
        """Admin get list bank chef, paginate, filter by status, search by chef email"""
        return self.service.get_chefs_bank_accounts(status=status, search=search)
    
    #admin get list bank customer, paginate, filter status, search by chef email
    @get("/bank-accounts/customers", auth=True, response=CustomerPaymentInfoSchema, paginate=True)
    @paginate
    @require_admin
    def get_customers_bank_accounts(
        self, 
        request: AuthenticatedRequest, 
        status: bool | None = Query(None, description="Filter by verification status"),
        search: str | None = Query(None, description="Search by customer email")
    ):
        """Admin get list bank customer, paginate, filter by status, search by customer email"""
        return self.service.get_customers_bank_accounts(status=status, search=search)


