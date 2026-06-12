from typing import Optional
from uuid import UUID
from django.utils import timezone
from certificate.models import Certificate
from certificate.schemas.requests import CertificateSchema
from utils.enums import CertificateStatusEnum
from certificate.schemas.requests import AdminFilterCertificateSchema, BaseCertificateFilterSchema
from utils.types import TUser

class CertificateORM:
    @staticmethod
    def create_certificate(user: TUser, certificate_data: dict, attachment=None, ) -> Certificate:
        """Tạo certificate với attachment (presigned URL flow)"""
        return Certificate.objects.create(
            **certificate_data, owner=user,attachment=attachment
        )

    @staticmethod
    def get_certificate_by_uid(uid: UUID) -> Optional[Certificate]:
        try:
            return Certificate.objects.select_related('attachment').get(uid=uid, deleted=False)
        except Certificate.DoesNotExist:
            return None
        
    @staticmethod
    def get_deleted_certificate_by_uid  (uid: UUID) -> Optional[Certificate]:
        try:
            return Certificate.objects.select_related('attachment').get(uid=uid)
        except Certificate.DoesNotExist:
            return None

        
    @staticmethod
    def get_all_certificates_of_chef(user: TUser, filter=BaseCertificateFilterSchema):
        query = Certificate.objects.filter(owner=user, deleted=False).select_related('attachment')
        if filter:
            query = query.filter(filter.get_filter_expression())
        return query
    
    @staticmethod
    def get_all_certificates(filter=AdminFilterCertificateSchema):
        query = Certificate.objects.filter(deleted=False).select_related('attachment', 'owner')
        if filter:
            query = query.filter(filter.get_filter_expression())
        return query
        
    @staticmethod
    def update_certificate(certificate: Certificate, payload: CertificateSchema, attachment=None):
        """Update certificate - chỉ update attachment nếu được cung cấp"""
        
        # Update các trường thông tin
        certificate.name = payload.name
        certificate.description = payload.description
        certificate.issued_by = payload.issued_by
        certificate.issue_date = payload.issue_date
        certificate.expiration_date = payload.expiration_date
        certificate.certificate_type = payload.certificate_type
        
        # Chỉ update attachment nếu được cung cấp
        if attachment:
            certificate.attachment = attachment
        
        certificate.save()
        # Refresh để lấy dữ liệu mới nhất từ DB
        certificate.refresh_from_db()
        return certificate
        
    @staticmethod
    def set_certificate_status(uid: str, status: CertificateStatusEnum, verified_by: TUser, rejection_reason: Optional[str] = None):
        certificate = Certificate.objects.get(uid=uid, deleted=False)
        certificate.status = status
        certificate.verified_by = verified_by
        certificate.verified_at = timezone.now()
        
        # Lưu rejection_reason nếu có
        if rejection_reason:
            certificate.rejection_reason = rejection_reason
        
        certificate.save(update_fields=['status', 'verified_by', 'verified_at', 'rejection_reason', 'updated_at'])
        certificate.refresh_from_db()
        return certificate
    
    @staticmethod
    def soft_delete_certificate(uid: str) -> bool:
        certificate = Certificate.objects.get(uid=uid, deleted=False)
        certificate.deleted = True
        certificate.save(update_fields=['deleted', 'updated_at'])
        return True
    
    @staticmethod
    def restore_certificate(certificate: Certificate):
        if not certificate.deleted:
            return False
        certificate.deleted = False
        certificate.save()
        return True
