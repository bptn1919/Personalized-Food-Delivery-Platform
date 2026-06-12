from utils.router.authenticate import AuthBear
from utils.router.controller import Controller, api, get, post
from utils.types import AuthenticatedRequest
from utils.permissions.decorators import require_group
from utils.enums import UserTypeEnum

from exceptions.verification import (
    CrossValidationFailed,
    CrossValidationNotReady,
    DocumentNotReadyToConfirm,
    SelfieCodeExpired,
    SelfieCodeMismatch,
    VerificationAlreadyCompleted,
    VerificationDocumentError,
    VerificationSessionNotFound,
)
from exceptions.attachments import AttachmentNotFound, AttachmentIsNotCompleted

from .schemas.requests import AnalyzeCCCDRequest, AnalyzeDocumentRequest, AnalyzeSelfieRequest
from .schemas.responses import (
    AnalyzeCCCDResponse,
    AnalyzeBusinessResponse,
    AnalyzeFoodSafetyResponse,
    ConfirmResponse,
    CrossValidationResponse,
    VerificationCodeResponse,
    VerificationDecisionResponse,
    SessionStatusResponse,
)
from .services.verification import VerificationService


@api(prefix_or_class="verification", tags=["Chef Verification"], auth=AuthBear())
class VerificationController(Controller):
    def __init__(self, service: VerificationService) -> None:
        self.service = service

    # ── CCCD ──────────────────────────────────────────────────────────────────

    @post(
        "/cccd/analyze",
        response=AnalyzeCCCDResponse,
        exceptions=(AttachmentNotFound, AttachmentIsNotCompleted, VerificationDocumentError),
    )
    @require_group(UserTypeEnum.CHEF)
    def analyze_cccd(self, request: AuthenticatedRequest, payload: AnalyzeCCCDRequest):
        """
        [CHEF] Giai đoạn 1 — Phân tích ảnh CCCD (1-2 ảnh: mặt trước, mặt sau).
        """
        result = self.service.analyze_cccd(
            user=request.user,
            attachment_uids=payload.attachment_uids,
        )
        return AnalyzeCCCDResponse(
            session_id=result["session_id"],
            extracted=result["extracted"],
        )

    @post(
        "/cccd/confirm",
        response=ConfirmResponse,
        exceptions=(DocumentNotReadyToConfirm,),
    )
    @require_group(UserTypeEnum.CHEF)
    def confirm_cccd(self, request: AuthenticatedRequest):
        """
        [CHEF] Giai đoạn 2 — Chef xác nhận thông tin CCCD đã phân tích là đúng.
        """
        self.service.confirm_cccd(user=request.user)
        return ConfirmResponse(status="CONFIRMED")

    # ── Giấy đăng ký kinh doanh ───────────────────────────────────────────────

    @post(
        "/business/analyze",
        response=AnalyzeBusinessResponse,
        exceptions=(AttachmentNotFound, AttachmentIsNotCompleted, VerificationDocumentError),
    )
    @require_group(UserTypeEnum.CHEF)
    def analyze_business(self, request: AuthenticatedRequest, payload: AnalyzeDocumentRequest):
        """
        [CHEF] Giai đoạn 1 — Phân tích Giấy đăng ký kinh doanh (hỗ trợ nhiều trang).
        """
        result = self.service.analyze_business(
            user=request.user,
            attachment_uids=payload.attachment_uids,
        )
        return AnalyzeBusinessResponse(
            session_id=result["session_id"],
            extracted=result["extracted"],
        )

    @post(
        "/business/confirm",
        response=ConfirmResponse,
        exceptions=(DocumentNotReadyToConfirm,),
    )
    @require_group(UserTypeEnum.CHEF)
    def confirm_business(self, request: AuthenticatedRequest):
        """
        [CHEF] Giai đoạn 2 — Chef xác nhận thông tin ĐKKD đã phân tích là đúng.
        """
        self.service.confirm_business(user=request.user)
        return ConfirmResponse(status="CONFIRMED")

    # ── Giấy chứng nhận ATTP ──────────────────────────────────────────────────

    @post(
        "/food-safety/analyze",
        response=AnalyzeFoodSafetyResponse,
        exceptions=(AttachmentNotFound, AttachmentIsNotCompleted, VerificationDocumentError),
    )
    @require_group(UserTypeEnum.CHEF)
    def analyze_food_safety(self, request: AuthenticatedRequest, payload: AnalyzeDocumentRequest):
        """
        [CHEF] Giai đoạn 1 — Phân tích Giấy chứng nhận ATTP (hỗ trợ nhiều trang).
        """
        result = self.service.analyze_food_safety(
            user=request.user,
            attachment_uids=payload.attachment_uids,
        )
        return AnalyzeFoodSafetyResponse(
            session_id=result["session_id"],
            extracted=result["extracted"],
        )

    @post(
        "/food-safety/confirm",
        response=ConfirmResponse,
        exceptions=(DocumentNotReadyToConfirm,),
    )
    @require_group(UserTypeEnum.CHEF)
    def confirm_food_safety(self, request: AuthenticatedRequest):
        """
        [CHEF] Giai đoạn 2 — Chef xác nhận thông tin ATTP đã phân tích là đúng.
        """
        self.service.confirm_food_safety(user=request.user)
        return ConfirmResponse(status="CONFIRMED")

    # ── Cross Validation ──────────────────────────────────────────────────────

    @post(
        "/cross-validate",
        response=CrossValidationResponse,
        exceptions=(CrossValidationNotReady, CrossValidationFailed),
    )
    @require_group(UserTypeEnum.CHEF)
    def cross_validate(self, request: AuthenticatedRequest):
        """
        [CHEF] Giai đoạn 3 — Kiểm tra chéo thông tin giữa CCCD, ĐKKD và ATTP.

        Yêu cầu: cả 3 tài liệu phải ở trạng thái CONFIRMED.
        Thành công: trả về next_step = "SELFIE".
        Thất bại: trả lỗi với chi tiết từng điểm không khớp và danh sách tài liệu liên quan.
        """
        result = self.service.cross_validate(user=request.user)
        return CrossValidationResponse(
            passed=result["passed"],
            next_step=result.get("next_step"),
        )

    # ── Selfie ────────────────────────────────────────────────────────────────

    @get("/selfie/code", response=VerificationCodeResponse)
    @require_group(UserTypeEnum.CHEF)
    def request_selfie_code(self, request: AuthenticatedRequest):
        """
        [CHEF] Lấy mã xác thực (dạng VERIFY-XXXXXX) để viết ra giấy và cầm khi chụp selfie.
        Mã hết hạn sau 10 phút.
        """
        result = self.service.request_selfie_code(user=request.user)
        return VerificationCodeResponse(**result)

    @post(
        "/selfie/analyze",
        response=VerificationDecisionResponse,
        exceptions=(VerificationAlreadyCompleted, SelfieCodeExpired, SelfieCodeMismatch,
                    VerificationDocumentError, AttachmentNotFound, AttachmentIsNotCompleted),
    )
    @require_group(UserTypeEnum.CHEF)
    def analyze_selfie(self, request: AuthenticatedRequest, payload: AnalyzeSelfieRequest):
        """
        [CHEF] Bước cuối — Selfie 1 ảnh duy nhất. Gemini đọc → verify mã → face match → decision.
        """
        session = self.service.analyze_selfie(
            user=request.user,
            attachment_uid=payload.attachment_uid,
        )
        return VerificationDecisionResponse(
            decision=session.decision,
            risk_score=session.risk_score,
            risk_flags=session.risk_flags,
            face_similarity_score=session.face_similarity_score,
            status=session.status,
        )

    # ── Status ────────────────────────────────────────────────────────────────

    @get(
        "/status",
        response=SessionStatusResponse,
        exceptions=(VerificationSessionNotFound,),
    )
    @require_group(UserTypeEnum.CHEF)
    def get_status(self, request: AuthenticatedRequest):
        """
        [CHEF] Lấy trạng thái hiện tại của phiên xác minh (để frontend biết chef đang ở bước nào).
        """
        session = self.service.get_status(user=request.user)
        selfie_url = None
        if session.decision == "PENDING_REVIEW" and session.selfie_attachment_id:
            selfie_url = session.selfie_attachment.public_url

        return SessionStatusResponse(
            status=session.status,
            cccd_status=session.cccd_status,
            business_status=session.business_status,
            food_safety_status=session.food_safety_status,
            cross_validation_passed=session.cross_validation_passed,
            decision=session.decision,
            risk_score=session.risk_score,
            risk_flags=session.risk_flags or [],
            face_similarity_score=session.face_similarity_score,
            cccd_number_masked=session.cccd_number_masked,
            verified_identity=session.verified_identity,
            verified_at=session.verified_at.isoformat() if session.verified_at else None,
            selfie_url=selfie_url,
        )
