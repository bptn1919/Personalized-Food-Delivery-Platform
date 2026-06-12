
from typing import Optional

from voucher.models import Voucher
from utils.types import User
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from order.models import Order
from utils.enums import OrderStatusEnum, PaymentStatus, VoucherTypeEnum
from django.db.models.functions import TruncDate

class Query:

    @staticmethod
    def get_users_list(filter=None):
        """
        Lấy danh sách users với filter expression
        Chỉ trả về users thuộc CUSTOMER hoặc CHEF (không bao gồm ADMIN)
        Trả về queryset để sử dụng với @paginate decorator
        """
        queryset = User.objects.filter(
            groups__name__in=['CUSTOMER', 'CHEF']
        ).distinct().select_related().prefetch_related('groups').order_by('-date_joined')
        
        if filter:
            queryset = queryset.filter(filter.get_filter_expression())
        
        return queryset
    
    def set_user_active_status(self, user_id: int, is_active: bool) -> bool:
        """Set active status cho user (dành cho admin)"""
        try:
            user = User.objects.get(id=user_id)
            user.is_active = is_active
            user.save(update_fields=['is_active'])
            return True
        except User.DoesNotExist:
            return False
    
    @staticmethod
    def get_dashboard_overview():
        """Lấy thống kê tổng quan cho dashboard"""
        # Tổng doanh thu (chỉ đơn đã hoàn thành và thanh toán thành công)
        total_revenue = Order.objects.filter(
            status=OrderStatusEnum.COMPLETED,
            payment_status__in=[
                PaymentStatus.SUCCESS,
                PaymentStatus.HOLDING,
                PaymentStatus.RELEASED,
            ],
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Tổng số đơn hàng
        total_orders = Order.objects.count()
        
        # Số user mới trong 30 ngày gần đây
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_users = User.objects.filter(
            date_joined__gte=thirty_days_ago,
            groups__name__in=['CUSTOMER', 'CHEF']
        ).distinct().count()
        
        # Số chef đang hoạt động (có ít nhất 1 đơn hàng)
        active_chefs = User.objects.filter(
            groups__name='CHEF',
            order_fk_chef__isnull=False
        ).distinct().count()
        
        # Tỉ lệ hủy đơn
        cancelled_orders = Order.objects.filter(status=OrderStatusEnum.CANCELLED).count()
        cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0
        
        return {
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'new_users': new_users,
            'active_chefs': active_chefs,
            'cancellation_rate': round(cancellation_rate, 2)
        }
    
    @staticmethod
    def get_revenue_chart(from_date, to_date):
        """Lấy dữ liệu doanh thu theo ngày cho biểu đồ"""
        
        
        # Query doanh thu theo ngày
        daily_revenue = Order.objects.filter(
            status=OrderStatusEnum.COMPLETED,
            payment_status__in=[
                PaymentStatus.SUCCESS,
                PaymentStatus.HOLDING,
                PaymentStatus.RELEASED,
            ],
            created_at__date__gte=from_date,
            created_at__date__lte=to_date,
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            revenue=Sum('total_price'),
            orders=Count('uid')  # Sử dụng 'uid' thay vì 'id'
        ).order_by('date')
        
        # Convert to list of dict
        data = []
        for item in daily_revenue:
            data.append({
                'date': item['date'].strftime('%Y-%m-%d'),
                'revenue': float(item['revenue'] or 0),
                'orders': item['orders']
            })
        
        return {
            'from_date': from_date.strftime('%Y-%m-%d'),
            'to_date': to_date.strftime('%Y-%m-%d'),
            'data': data
        }
    
    @staticmethod
    def get_payment_method_stats():
        """Lấy thống kê tỷ lệ phần trăm sử dụng của từng phương thức thanh toán"""
        from payment.models import PaymentTransaction, PaymentTransactionState
        
        # Tổng số giao dịch (chỉ tính giao dịch thành công)
        total_transactions = PaymentTransactionState.objects.filter(
            status__in=[
                PaymentStatus.SUCCESS,
                PaymentStatus.HOLDING,
                PaymentStatus.RELEASED,
            ]
        ).count()
        print(f"Total successful transactions: {total_transactions}")
        # Thống kê theo phương thức thanh toán
        payment_stats = PaymentTransaction.objects.filter(
            state__status__in=[
                PaymentStatus.SUCCESS,
                PaymentStatus.HOLDING,
                PaymentStatus.RELEASED,
            ]
        ).values('payment_method').annotate(
            count=Count('uid'),
            total_amount=Sum('amount')
        ).order_by('-count')
        
        # Tính phần trăm và format data
        data = []
        for stat in payment_stats:
            percentage = (stat['count'] / total_transactions * 100) if total_transactions > 0 else 0
            data.append({
                'payment_method': stat['payment_method'],
                'count': stat['count'],
                'percentage': round(percentage, 2),
                'total_amount': float(stat['total_amount'] or 0)
            })
        
        return {
            'total_orders': total_transactions,
            'data': data
        }
    
    @staticmethod
    def get_order_status_stats():
        """Lấy thống kê tỷ lệ phần trăm từng trạng thái đơn hàng"""
        
        # Tổng số đơn hàng
        total_orders = Order.objects.count()
        
        # Thống kê theo trạng thái đơn hàng
        status_stats = Order.objects.values('status').annotate(
            count=Count('uid')
        ).order_by('-count')
        
        # Tính phần trăm và format data
        data = []
        for stat in status_stats:
            percentage = (stat['count'] / total_orders * 100) if total_orders > 0 else 0
            data.append({
                'status': stat['status'],
                'count': stat['count'],
                'percentage': round(percentage, 2)
            })
        
        return {
            'total_orders': total_orders,
            'data': data
        }
    
    @staticmethod
    def get_top_chefs(limit=5):
        """Lấy top chefs có lượt bán cao nhất (chỉ tính đơn đã hoàn thành)"""
        from django.db.models import F
        
        # Query top chefs theo số lượng đơn hàng đã hoàn thành
        top_chefs = Order.objects.filter(
            status=OrderStatusEnum.COMPLETED,
            chef__isnull=False
        ).values(
            'chef__id',
            'chef__username',
            'chef__email',
            'chef__first_name',
            'chef__last_name'
        ).annotate(
            total_orders=Count('uid'),
            total_revenue=Sum('total_price')
        ).order_by('-total_orders')[:limit]
        
        # Format data và lấy thêm avatar
        from profile.models import ChefProfile
        data = []
        for chef_stat in top_chefs:
            chef_id = chef_stat['chef__id']
            
            # Tạo tên hiển thị
            first_name = chef_stat.get('chef__first_name', '')
            last_name = chef_stat.get('chef__last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            chef_name = full_name if full_name else chef_stat['chef__username']
            
            # Lấy avatar từ ChefProfile
            avatar_url = None
            try:
                chef_profile = ChefProfile.objects.select_related('avatar').get(user_id=chef_id)
                if chef_profile.avatar:
                    avatar_url = chef_profile.avatar.public_url if chef_profile.avatar.public_url else None
            except ChefProfile.DoesNotExist:
                pass
            
            data.append({
                'chef_id': chef_id,
                'chef_name': chef_name,
                'chef_email': chef_stat['chef__email'],
                'total_orders': chef_stat['total_orders'],
                'total_revenue': float(chef_stat['total_revenue'] or 0),
                'avatar_url': avatar_url
            })
        
        return data

    @staticmethod
    def get_success_orders_by_district(from_date=None, to_date=None):
        """Lấy thống kê số lượng và tỷ lệ đơn thành công theo quận"""
        base_query = Order.objects.filter(
            status=OrderStatusEnum.COMPLETED,
            checkout__delivery_address__isnull=False,
        )

        if from_date:
            base_query = base_query.filter(created_at__date__gte=from_date)
        if to_date:
            base_query = base_query.filter(created_at__date__lte=to_date)

        total_success_orders = base_query.count()

        district_stats = (
            base_query
            .values('checkout__delivery_address__district')
            .annotate(success_orders=Count('uid'))
            .order_by('-success_orders', 'checkout__delivery_address__district')
        )

        data = []
        for stat in district_stats:
            district = stat['checkout__delivery_address__district']
            success_orders = stat['success_orders']
            percentage = (success_orders / total_success_orders * 100) if total_success_orders > 0 else 0
            data.append({
                'district': district,
                'success_orders': success_orders,
                'percentage': round(percentage, 2),
            })

        return {
            'total_success_orders': total_success_orders,
            'data': data,
        }
    
    @staticmethod
    def get_orders_list(filter=None):
        """
        Lấy danh sách orders với filter expression
        Trả về queryset để sử dụng với @paginate decorator
        """
        queryset = Order.objects.select_related(
            'owner', 'chef', 'checkout', 'checkout__delivery_address'
        ).prefetch_related(
            'orderitem_fk_order'
        ).order_by('-created_at')
        
        if filter:
            queryset = queryset.filter(filter.get_filter_expression())
        
        return queryset
    
    @staticmethod
    def get_order_detail(order_uid: str):
        """Lấy chi tiết một order"""
        try:
            order = Order.objects.select_related(
                'owner', 'chef', 'checkout', 'checkout__delivery_address'
            ).prefetch_related(
                'orderitem_fk_order'
            ).get(uid=order_uid)
            return order
        except Order.DoesNotExist:
            return None

    @staticmethod
    def create_voucher(
        chef: User,
        code: str,
        name: str,
        voucher_type: VoucherTypeEnum,
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
            voucher_type=voucher_type, 
            discount_value=discount_value,
            max_discount_amount=max_discount_amount,
            min_order_amount=min_order_amount,
            start_date=start_date,
            end_date=end_date,
            usage_limit=usage_limit,
            usage_limit_per_user=usage_limit_per_user,
            is_active=is_active,
        )
    
    @staticmethod
    def list_vouchers():
        """Lấy danh sách tất cả voucher (Admin only)"""
        return Voucher.objects.select_related('chef').order_by('-created_at')

    @staticmethod
    def get_verification_review_data(user_id: int) -> dict | None:
        """
        Lấy toàn bộ dữ liệu verification của 1 chef để admin review:
        - Thông tin session (decision, risk, identity)
        - Selfie URL (nếu còn tồn tại)
        - CCCD image URLs (nếu còn — PENDING_REVIEW chưa bị xóa)
        - Danh sách certificates kèm attachment URLs
        """
        from verification.models import ChefVerificationSession
        from certificate.models import Certificate, CertificateAttachment
        from attachment.queries import Query as AttachmentQuery

        try:
            session = (
                ChefVerificationSession.objects
                .select_related("user", "selfie_attachment",
                                "business_certificate", "food_safety_certificate")
                .get(user_id=user_id)
            )
        except ChefVerificationSession.DoesNotExist:
            return None

        user = session.user

        # CCCD image URLs (chỉ có khi session PENDING_REVIEW + chưa bị clear)
        aq = AttachmentQuery()
        cccd_urls = []
        for uid_str in session.cccd_attachment_uids or []:
            try:
                att = aq.get_instance_by_uid(uid=uid_str)
                if att and not att.is_file_deleted:
                    cccd_urls.append(att.public_url)
            except Exception:
                pass

        # Selfie URL
        selfie_url = None
        if session.selfie_attachment_id and not session.selfie_attachment.is_file_deleted:
            selfie_url = session.selfie_attachment.public_url

        # Certificates
        cert_uids = [
            c.uid for c in [session.business_certificate, session.food_safety_certificate]
            if c is not None
        ]
        certs_data = []
        for cert in Certificate.objects.filter(uid__in=cert_uids).prefetch_related(
            "attachment_fk_certificate__attachment"
        ):
            attachments = []
            for ca in cert.attachment_fk_certificate.order_by("position"):
                if not ca.attachment.is_file_deleted:
                    attachments.append({
                        "attachment_uid": ca.attachment.uid,
                        "position": ca.position,
                        "url": ca.attachment.public_url,
                    })
            certs_data.append({
                "uid": cert.uid,
                "name": cert.name,
                "certificate_type": cert.certificate_type,
                "status": cert.status,
                "issued_by": cert.issued_by,
                "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
                "expiry_date": cert.expiration_date.isoformat() if cert.expiration_date else None,
                "rejection_reason": cert.rejection_reason,
                "verified_by_email": cert.verified_by.email if cert.verified_by else None,
                "verified_at": cert.verified_at.isoformat() if cert.verified_at else None,
                "attachments": attachments,
            })

        return {
            "user_id": user.id,
            "user_email": user.email,
            "decision": session.decision,
            "risk_score": session.risk_score,
            "risk_flags": session.risk_flags or [],
            "face_similarity_score": session.face_similarity_score,
            "verified_identity": session.verified_identity,
            "cccd_number_masked": session.cccd_number_masked,
            "selfie_url": selfie_url,
            "cccd_image_urls": cccd_urls,
            "certificates": certs_data,
            "verified_at": session.verified_at.isoformat() if session.verified_at else None,
        }
    