from typing import Optional, List
from uuid import UUID
from django.utils import timezone
from certificate.models import Certificate, CertificateAttachment
from certificate.schemas.requests import CertificateSchema, AdminFilterCertificateSchema, BaseCertificateFilterSchema, CertificateAttachmentReorderSchema
from utils.enums import CertificateStatusEnum
from utils.types import TUser

class CertificateORM:
    @staticmethod
    def create_certificate(user: TUser, certificate_data: dict) -> Certificate:
        """Tạo certificate (attachment được thêm qua endpoint riêng)"""
        return Certificate.objects.create(
            **certificate_data, owner=user
        )

    @staticmethod
    def get_certificate_by_uid(uid: UUID) -> Optional[Certificate]:
        try:
            return Certificate.objects.prefetch_related('attachment_fk_certificate').get(uid=uid, deleted=False)
        except Certificate.DoesNotExist:
            return None
        
    @staticmethod
    def get_deleted_certificate_by_uid(uid: UUID) -> Optional[Certificate]:
        try:
            return Certificate.objects.prefetch_related('attachment_fk_certificate').get(uid=uid)
        except Certificate.DoesNotExist:
            return None

        
    @staticmethod
    def get_all_certificates_of_chef(user: TUser, filter=BaseCertificateFilterSchema):
        query = Certificate.objects.filter(owner=user, deleted=False).prefetch_related('attachment_fk_certificate')
        if filter:
            query = query.filter(filter.get_filter_expression())
        return query
    
    @staticmethod
    def get_all_certificates(filter=AdminFilterCertificateSchema):
        query = Certificate.objects.filter(deleted=False).prefetch_related('attachment_fk_certificate').select_related('owner')
        if filter:
            query = query.filter(filter.get_filter_expression())
        return query
        
    @staticmethod
    def update_certificate(certificate: Certificate, payload: CertificateSchema):
        """Update certificate - chỉ update thông tin, không touch attachments"""
        
        # Update các trường thông tin
        certificate.name = payload.name
        certificate.description = payload.description
        certificate.issued_by = payload.issued_by
        certificate.issue_date = payload.issue_date
        certificate.expiration_date = payload.expiration_date
        certificate.certificate_type = payload.certificate_type
        
        certificate.save()
        
        # Refresh để lấy dữ liệu mới nhất từ DB
        certificate.refresh_from_db()
        return certificate
    
    @staticmethod
    def add_attachments_to_certificate(certificate: Certificate, attachments: List) -> Certificate:
        """Thêm attachments vào certificate"""
        for attachment in attachments:
            CertificateAttachment.objects.create(
                certificate=certificate,
                attachment=attachment
            )
        
        certificate.refresh_from_db()
        return certificate
    
    @staticmethod
    def remove_attachment_from_certificate(certificate: Certificate, attachment_uid: UUID) -> bool:
        """Xóa 1 attachment khỏi certificate"""
        try:
            cert_attachment = CertificateAttachment.objects.get(
                certificate=certificate,
                attachment__uid=attachment_uid
            )
            cert_attachment.delete()
            return True
        except CertificateAttachment.DoesNotExist:
            return False
    
    @staticmethod
    def reorder_certificate_attachments(certificate, payload):
        from django.db import transaction
        
        with transaction.atomic():
            # 1️⃣ Xóa hết attachments cũ
            CertificateAttachment.objects.filter(certificate=certificate).delete()
            
            # 2️⃣ Tạo mới theo thứ tự mới
            for idx, item in enumerate(payload):
                CertificateAttachment.objects.create(
                    certificate=certificate,
                    attachment_id=item.attachment_uid,  # attachment uid
                    position=idx  # position theo thứ tự mới
                )
        
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
