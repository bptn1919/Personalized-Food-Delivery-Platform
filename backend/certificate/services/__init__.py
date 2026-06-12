from typing import Optional, List
from uuid import UUID

from certificate.schemas.requests import CertificateAttachmentReorderSchema, CertificateSchema
from utils.enums import CertificateStatusEnum
from utils.exceptions import PermissionDeniedError
from certificate.orm.certificate import CertificateORM
from certificate.schemas.requests import BaseCertificateFilterSchema, AdminFilterCertificateSchema
from utils.types import TUser
from attachment.queries import Query as AttachmentQuery
from attachment.services import AttachmentService
from exceptions.attachments import AttachmentIsNotCompleted, AttachmentNotFound
from exceptions.certificates import CertificateNotFoundException
from certificate.models import CertificateAttachment
from utils.enums import UserTypeEnum
from django.db import transaction
from certificate.models import Certificate


class CertificateService:
    def __init__(self):
        self.orm = CertificateORM()
        self.attachment_service = AttachmentService()
    
    def create_certificate(self, user: TUser, payload: CertificateSchema):
        """Tạo certificate mới (attachment được thêm qua endpoint riêng)"""
        certificate_data = payload.dict()
        return self.orm.create_certificate(user=user, certificate_data=certificate_data)
    
    def get_certificate_by_uid(self, uid: UUID):
        """Lấy certificate theo uid - không check permission (do decorator đảm nhiệm)"""
        certificate = self.orm.get_certificate_by_uid(uid=uid)
        if not certificate:
            raise CertificateNotFoundException
        return certificate
    
    def get_all_certificates_of_chef(self, filter=BaseCertificateFilterSchema, user: TUser = None):
        """Lấy tất cả certificates của chef hiện đang login, có thể filter theo status"""
        return self.orm.get_all_certificates_of_chef(user=user, filter=filter)
    
    def get_all_certificates(self, filter=AdminFilterCertificateSchema):
        """Admin lấy tất cả certificates, có thể filter theo status và chef"""
        return self.orm.get_all_certificates(filter=filter)
    
    def update_certificate(self, uid: UUID, payload: CertificateSchema):
        """Chef cập nhật thông tin certificate (không update attachments)"""
        # Chef chỉ có thể update khi status = PENDING
        certificate = self.get_certificate_by_uid(uid=uid)
        if certificate.status != CertificateStatusEnum.PENDING:
            raise PermissionDeniedError("Chỉ có thể chỉnh sửa certificate khi đang ở trạng thái PENDING.")
        
        self.orm.update_certificate(certificate=certificate, payload=payload)
        # Return certificate đã được update
        return self.get_certificate_by_uid(uid=uid)
    
    def add_certificate_attachments(self, uid: UUID, attachment_uids: List[UUID]):
        """Thêm attachments vào certificate"""
        certificate = self.get_certificate_by_uid(uid=uid)
        
        attachment_query = AttachmentQuery()
        attachments = []
        
        for attachment_uid in attachment_uids:
            # Kiểm tra attachment đã complete chưa
            self.attachment_service.handle_attachment(uid=attachment_uid)
            
            # Check attachment không được thêm vào certificate này 2 lần
            existing = CertificateAttachment.objects.filter(
                certificate=certificate,
                attachment__uid=attachment_uid
            ).exists()
            if existing:
                raise Exception(f"Attachment {attachment_uid} đã tồn tại trong certificate này")
            
            # Lấy attachment object - dùng đúng method name
            attachment = attachment_query.get_instance_by_uid(uid=attachment_uid)
            if not attachment:
                raise AttachmentNotFound(f"Attachment {attachment_uid} không tồn tại")
            
            attachments.append(attachment)
        
        return self.orm.add_attachments_to_certificate(certificate=certificate, attachments=attachments)
    
    def remove_certificate_attachment(self, uid: UUID, attachment_uid: UUID):
        """Xóa 1 attachment khỏi certificate"""
        certificate = self.get_certificate_by_uid(uid=uid)
        
        success = self.orm.remove_attachment_from_certificate(
            certificate=certificate,
            attachment_uid=attachment_uid
        )
        
        if not success:
            raise AttachmentNotFound(f"Attachment {attachment_uid} không tồn tại trong certificate này")
        
        return self.get_certificate_by_uid(uid=uid)
    

    def reorder_certificate_attachments(self, uid: UUID, payload: list[CertificateAttachmentReorderSchema]):
        """Sắp xếp lại thứ tự attachments"""
        certificate = self.get_certificate_by_uid(uid=uid)
        for item in payload:
            exists = CertificateAttachment.objects.filter(
                certificate=certificate,
                attachment__uid=item.attachment_uid
            ).exists()

            if not exists:
                raise AttachmentNotFound(f"{item.attachment_uid} not found")
    
        return self.orm.reorder_certificate_attachments(certificate=certificate, payload=payload)

    def set_certificate_status(self, uid: UUID, status: CertificateStatusEnum, verified_by: TUser, rejection_reason: Optional[str] = None):
        """Admin active/deactivate/revoke certificate"""
        if status == CertificateStatusEnum.REVOKED and not rejection_reason:
            raise PermissionDeniedError("Vui lòng cung cấp lý do từ chối khi REVOKE certificate.")

        self.get_certificate_by_uid(uid=uid)
        result = self.orm.set_certificate_status(
            uid=uid,
            status=status,
            verified_by=verified_by,
            rejection_reason=rejection_reason
        )

        # Sau khi admin duyệt xong, kiểm tra xem còn certificate nào PENDING không.
        # Nếu không còn → xóa selfie khỏi S3 (không cần giữ nữa).
        self._cleanup_selfie_if_fully_reviewed(uid=uid)

        return result

    def _cleanup_selfie_if_fully_reviewed(self, uid: UUID) -> None:
        """
        Khi admin review certificate cuối cùng của 1 session PENDING_REVIEW:
        Lên lịch xóa CCCD images + selfie khỏi S3 sau 30 ngày.
        """
        import logging
        _log = logging.getLogger("django")
        try:
            from verification.models import ChefVerificationSession
            from utils.enums import CertificateStatusEnum
            from attachment.queries import Query as AttachmentQuery
            from verification.services.verification import _schedule_s3_deletion

            # Tìm session liên kết với certificate này
            session = (
                ChefVerificationSession.objects
                .select_related("selfie_attachment")
                .filter(business_certificate__uid=uid)
                .first()
                or ChefVerificationSession.objects
                .select_related("selfie_attachment")
                .filter(food_safety_certificate__uid=uid)
                .first()
            )
            if not session:
                return

            # Kiểm tra còn certificate nào đang PENDING không
            pending_exists = any(
                cert and cert.status == CertificateStatusEnum.PENDING
                for cert in [session.business_certificate, session.food_safety_certificate]
            )
            if pending_exists:
                return  # Chưa review hết — chưa schedule

            # Tất cả đã được review → schedule xóa sau 30 ngày
            aq = AttachmentQuery()

            # Schedule CCCD images
            for uid_str in list(session.cccd_attachment_uids or []):
                try:
                    att = aq.get_instance_by_uid(uid=uid_str)
                    if att:
                        _schedule_s3_deletion(att, delay_days=30)
                except Exception as exc:
                    _log.error("Schedule CCCD deletion failed for %s: %s", uid_str, exc)

            # Schedule selfie
            if session.selfie_attachment_id:
                try:
                    _schedule_s3_deletion(session.selfie_attachment, delay_days=30)
                except Exception as exc:
                    _log.error("Schedule selfie deletion failed: %s", exc)

            # Xóa references trong session ngay (file vẫn còn, chỉ clear FK)
            session.cccd_attachment_uids = []
            session.selfie_attachment = None
            session.save(update_fields=["cccd_attachment_uids", "selfie_attachment", "updated_at"])

        except Exception as exc:
            import logging
            logging.getLogger("django").error("_cleanup_selfie_if_fully_reviewed failed: %s", exc)
    
    def soft_delete_certificate(self, uid: UUID, user: TUser):
        certificate = self.get_certificate_by_uid(uid=uid)
        if certificate.status != CertificateStatusEnum.PENDING:
            raise PermissionDeniedError("Chỉ có thể xóa certificate khi đang ở trạng thái PENDING.")
        return self.orm.soft_delete_certificate(uid=uid)
    
    def restore_certificate(self, user: TUser, uid: UUID):
        """Khôi phục certificate đã bị xóa - chỉ owner hoặc admin"""
        certificate = self.orm.get_deleted_certificate_by_uid(uid=uid)
        if not certificate:
            raise CertificateNotFoundException
        
        # Check quyền: chỉ owner hoặc admin
        is_owner = certificate.owner_id == user.id
        is_admin = user.groups.filter(name=UserTypeEnum.ADMIN).exists()
        if not (is_owner or is_admin):
            raise PermissionDeniedError("Bạn không có quyền khôi phục certificate này.")
        
        return self.orm.restore_certificate(certificate=certificate)