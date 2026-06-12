from uuid import UUID

from ninja import Query

from admin.permissions import require_admin
from exceptions.certificates import CertificateNotFoundException
from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, get, patch
from utils.router.paginate import paginate
from utils.types import AuthenticatedRequest
from utils.permissions.decorators import require_owner_or_admin
from utils.exceptions import PermissionDeniedError
from certificate.models import Certificate

from .schemas.requests import (
    AdminFilterCertificateSchema,
    BaseCertificateFilterSchema,
    CertificateAttachmentReorderSchema,
    SetCertificateStatusSchema,
)
from .schemas.responses import CertificateResponse
from .services import CertificateService


@api(prefix_or_class="certificates", tags=["Certificate"], auth=AuthBear())
class CertificateController(Controller):
    def __init__(self, service: CertificateService) -> None:
        self.service = service

    # ── Các route static phải khai báo TRƯỚC /{uid} để tránh bị match nhầm ───

    @get("/", auth=True, response=CertificateResponse, paginate=True)
    @paginate
    def get_all_certificates_of_chef(
        self,
        request: AuthenticatedRequest,
        filter: BaseCertificateFilterSchema = Query(...),
    ):
        """[CHEF] Lấy danh sách certificates của mình (tạo từ quá trình xác minh)."""
        return self.service.get_all_certificates_of_chef(user=request.user, filter=filter)

    @get("/all", auth=True, response=CertificateResponse, paginate=True)
    @require_admin
    @paginate
    def get_all_certificates(
        self,
        request: AuthenticatedRequest,
        filter: AdminFilterCertificateSchema = Query(...),
    ):
        """[ADMIN] Lấy tất cả certificates, filter theo status / chef."""
        return self.service.get_all_certificates(filter=filter)

    @get(
        "/{uid}",
        response=CertificateResponse,
        exceptions=(CertificateNotFoundException, PermissionDeniedError),
    )
    @require_owner_or_admin(Certificate)
    def get_certificate_by_uid(self, request: AuthenticatedRequest, uid: UUID):
        """[CHEF / ADMIN] Xem chi tiết một certificate."""
        return self.service.get_certificate_by_uid(uid=uid)

    @patch(
        "/{uid}/status",
        auth=True,
        response=CertificateResponse,
        exceptions=(PermissionDeniedError, CertificateNotFoundException),
    )
    @require_admin
    def set_certificate_status(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
        payload: SetCertificateStatusSchema,
    ):
        """[ADMIN] Duyệt (ACTIVE) hoặc thu hồi (REVOKED) certificate.
        Lưu ý: REVOKED bắt buộc truyền rejection_reason.
        """
        return self.service.set_certificate_status(
            uid=uid,
            status=payload.status,
            verified_by=request.user,
            rejection_reason=payload.rejection_reason,
        )

    @patch(
        "/{uid}/deleted",
        response=bool,
        exceptions=(PermissionDeniedError,),
    )
    @require_admin
    def soft_delete_certificate(self, request: AuthenticatedRequest, uid: UUID):
        """[ADMIN] Ẩn certificate (soft delete)."""
        return self.service.soft_delete_certificate(uid=uid, user=request.user)

    @patch(
        "/{uid}/restored",
        response=bool,
        exceptions=(PermissionDeniedError, CertificateNotFoundException),
    )
    @require_admin
    def restore_certificate(self, request: AuthenticatedRequest, uid: UUID):
        """[ADMIN] Khôi phục certificate đã bị ẩn."""
        return self.service.restore_certificate(user=request.user, uid=uid)

    # ── Attachment: chỉ sắp xếp lại thứ tự hiển thị ──────────────────────────

    @patch("/{uid}/attachments/reorder", response=CertificateResponse)
    @require_admin
    def reorder_certificate_attachments(
        self,
        request: AuthenticatedRequest,
        uid: UUID,
        payload: list[CertificateAttachmentReorderSchema],
    ):
        """[ADMIN] Sắp xếp lại thứ tự ảnh trong certificate (chỉ ảnh hưởng UI)."""
        return self.service.reorder_certificate_attachments(uid=uid, payload=payload)

    # ── CÁC API ĐÃ BỎ — lý do ghi ở đây để tránh nhầm lẫn ──────────────────
    #
    # POST /                    → BỎ: Certificate chỉ được tạo tự động từ verification flow,
    #                                  không cho chef tạo thủ công để tránh giả mạo.
    #
    # PATCH /{uid}/             → BỎ: Không cho phép sửa thông tin (name, issued_by, dates)
    #                                  sau khi đã được OCR từ ảnh gốc. Sửa = gian lận.
    #
    # POST /{uid}/attachments/  → BỎ: Ảnh được set trong verification, không cho thêm sau.
    #
    # DELETE /{uid}/attachments/{uid} → BỎ: Không cho xóa ảnh gốc đã được xác minh.
