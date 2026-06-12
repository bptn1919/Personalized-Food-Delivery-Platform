"""
VerificationService — Orchestrator cho toàn bộ Chef Verification Flow.

Luồng 3 giai đoạn:
  1. Upload & Analyze  → Gemini OCR → trả extracted fields hoặc document errors
  2. Confirm           → Chef xác nhận → backend lưu confirmed data
  3. Cross Validate    → Backend kiểm tra chéo (chỉ sau khi cả 3 tài liệu confirmed)
  + Selfie → Face Matching → Risk Score → Decision

Sau khi ra quyết định (finalize):
  - Ảnh CCCD bị xóa khỏi S3 (privacy — CCCD chỉ phục vụ xác thực)
  - CCCD number được mask (display) và hash Argon2id (DB)
  - Raw CCCD extracted/confirmed data bị xóa
  - Certificate records được tạo cho ĐKKD và ATTP (nếu không REJECTED)
"""

import logging
from datetime import date
from uuid import UUID

import boto3
import requests as http_requests
from argon2 import PasswordHasher
from django.conf import settings
from django.utils.timezone import now

from attachment.queries import Query as AttachmentQuery
from exceptions.attachments import AttachmentNotFound, AttachmentIsNotCompleted
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
from utils.enums import (
    CertificateStatusEnum,
    CertificateTypeEnum,
    DocumentStepStatusEnum,
    VerificationSessionStatusEnum,
)
from utils.types import TUser
from verification.models import ChefVerificationSession
from verification.services import engine as risk_engine
from verification.services import gemini as gemini_service
from verification.services.face import compare_faces

logger = logging.getLogger("django")

# Argon2id — same cost params as OTP hashing in users/models.py
_cccd_hasher = PasswordHasher(
    time_cost=2, memory_cost=65536, parallelism=1, hash_len=32, salt_len=16
)


class VerificationService:

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_or_create_session(self, user: TUser) -> ChefVerificationSession:
        session, _ = ChefVerificationSession.objects.get_or_create(user=user)
        return session

    def _require_session(self, user: TUser) -> ChefVerificationSession:
        try:
            return ChefVerificationSession.objects.get(user=user)
        except ChefVerificationSession.DoesNotExist:
            raise VerificationSessionNotFound()

    def _get_completed_attachment(self, attachment_uid: UUID):
        attachment = AttachmentQuery().get_instance_by_uid(uid=attachment_uid)
        if not attachment:
            raise AttachmentNotFound()
        if not attachment.is_completed:
            raise AttachmentIsNotCompleted()
        return attachment

    def _get_completed_attachments(self, attachment_uids: list[UUID]) -> list:
        return [self._get_completed_attachment(uid) for uid in attachment_uids]

    # ── Giai đoạn 1 + 2: CCCD ────────────────────────────────────────────────

    def analyze_cccd(self, user: TUser, attachment_uids: list[UUID]) -> dict:
        session = self._get_or_create_session(user)
        attachments = self._get_completed_attachments(attachment_uids)

        result = gemini_service.analyze_cccd([a.public_url for a in attachments])
        if result["errors"]:
            raise VerificationDocumentError(errors=result["errors"])

        extracted = result["extracted"]

        # Quét QR trên mặt sau (index 1) để đối chiếu với Gemini OCR
        if len(attachments) >= 2:
            try:
                back_bytes = http_requests.get(attachments[1].public_url, timeout=15).content
                from verification.services.qr import scan_cccd_qr
                qr_data = scan_cccd_qr(back_bytes)
                if qr_data:
                    ocr_number = extracted.get("cccd_number", "")
                    qr_number = qr_data.get("cccd_number", "")
                    if ocr_number and qr_number and ocr_number != qr_number:
                        raise VerificationDocumentError(errors=[{
                            "code": "CCCD_QR_NUMBER_MISMATCH",
                            "message": "Số CCCD trong mã QR không khớp với số in trên thẻ. "
                                       "CCCD có thể bị giả mạo. Vui lòng kiểm tra lại.",
                        }])
                    extracted["qr_verified"] = bool(qr_number)
                    extracted["qr_gender"] = qr_data.get("gender")
                    extracted["old_cmnd"] = qr_data.get("old_cmnd")
                else:
                    extracted["qr_verified"] = False
            except VerificationDocumentError:
                raise
            except Exception as exc:
                logger.warning("QR scan skipped: %s", exc)
                extracted["qr_verified"] = False

        session.cccd_attachment_uids = [str(a.uid) for a in attachments]
        session.cccd_extracted = extracted
        session.cccd_status = DocumentStepStatusEnum.EXTRACTED
        session.save(update_fields=["cccd_attachment_uids", "cccd_extracted", "cccd_status", "updated_at"])
        return {"session_id": session.id, "extracted": extracted}

    def confirm_cccd(self, user: TUser) -> ChefVerificationSession:
        session = self._get_or_create_session(user)
        if session.cccd_status != DocumentStepStatusEnum.EXTRACTED:
            raise DocumentNotReadyToConfirm()
        session.cccd_confirmed = session.cccd_extracted
        session.cccd_status = DocumentStepStatusEnum.CONFIRMED
        session.save(update_fields=["cccd_confirmed", "cccd_status", "updated_at"])
        return session

    # ── Giai đoạn 1 + 2: ĐKKD ────────────────────────────────────────────────

    def analyze_business(self, user: TUser, attachment_uids: list[UUID]) -> dict:
        session = self._get_or_create_session(user)
        attachments = self._get_completed_attachments(attachment_uids)

        result = gemini_service.analyze_business_license([a.public_url for a in attachments])
        if result["errors"]:
            raise VerificationDocumentError(errors=result["errors"])

        session.business_attachment_uids = [str(a.uid) for a in attachments]
        session.business_extracted = result["extracted"]
        session.business_status = DocumentStepStatusEnum.EXTRACTED
        session.save(update_fields=["business_attachment_uids", "business_extracted", "business_status", "updated_at"])
        return {"session_id": session.id, "extracted": result["extracted"]}

    def confirm_business(self, user: TUser) -> ChefVerificationSession:
        session = self._get_or_create_session(user)
        if session.business_status != DocumentStepStatusEnum.EXTRACTED:
            raise DocumentNotReadyToConfirm()
        session.business_confirmed = session.business_extracted
        session.business_status = DocumentStepStatusEnum.CONFIRMED
        session.save(update_fields=["business_confirmed", "business_status", "updated_at"])
        return session

    # ── Giai đoạn 1 + 2: ATTP ────────────────────────────────────────────────

    def analyze_food_safety(self, user: TUser, attachment_uids: list[UUID]) -> dict:
        session = self._get_or_create_session(user)
        attachments = self._get_completed_attachments(attachment_uids)

        result = gemini_service.analyze_food_safety([a.public_url for a in attachments])
        if result["errors"]:
            raise VerificationDocumentError(errors=result["errors"])

        session.food_safety_attachment_uids = [str(a.uid) for a in attachments]
        session.food_safety_extracted = result["extracted"]
        session.food_safety_status = DocumentStepStatusEnum.EXTRACTED
        session.save(update_fields=["food_safety_attachment_uids", "food_safety_extracted", "food_safety_status", "updated_at"])
        return {"session_id": session.id, "extracted": result["extracted"]}

    def confirm_food_safety(self, user: TUser) -> ChefVerificationSession:
        session = self._get_or_create_session(user)
        if session.food_safety_status != DocumentStepStatusEnum.EXTRACTED:
            raise DocumentNotReadyToConfirm()
        session.food_safety_confirmed = session.food_safety_extracted
        session.food_safety_status = DocumentStepStatusEnum.CONFIRMED
        session.save(update_fields=["food_safety_confirmed", "food_safety_status", "updated_at"])
        return session

    # ── Giai đoạn 3: Cross Validation ────────────────────────────────────────

    def cross_validate(self, user: TUser) -> dict:
        """
        Chỉ chạy khi cả 3 tài liệu đã CONFIRMED.
        Kiểm tra:
          - CCCD.full_name == ĐKKD.owner_name
          - ĐKKD.owner_name == ATTP.owner_name
          - ĐKKD.address == ATTP.address (approximate)
          - ATTP.expiry_date > today
        Nếu thất bại → raise CrossValidationFailed (Giai đoạn 3 error).
        Nếu thành công → session.status = AWAITING_SELFIE.
        """
        session = self._get_or_create_session(user)
        if not session.all_documents_confirmed():
            raise CrossValidationNotReady()

        cccd = session.cccd_confirmed or {}
        business = session.business_confirmed or {}
        food_safety = session.food_safety_confirmed or {}

        errors: list[dict] = []

        # Check 1: CCCD name vs Business owner name
        cccd_name = cccd.get("full_name", "")
        biz_name = business.get("owner_name", "")
        if cccd_name and biz_name and not _names_match(cccd_name, biz_name):
            errors.append({
                "code": "OWNER_NAME_MISMATCH_CCCD_BUSINESS",
                "message": (
                    "Thông tin chủ sở hữu trên giấy đăng ký kinh doanh không khớp "
                    "với thông tin trên CCCD. Vui lòng kiểm tra lại giấy tờ đã tải lên."
                ),
                "documents": ["cccd", "business"],
            })

        # Check 2: Business owner name vs Food Safety owner name
        fs_name = food_safety.get("owner_name", "")
        if biz_name and fs_name and not _names_match(biz_name, fs_name):
            errors.append({
                "code": "OWNER_NAME_MISMATCH_BUSINESS_FOOD_SAFETY",
                "message": (
                    "Thông tin chủ sở hữu trên giấy chứng nhận an toàn thực phẩm "
                    "không khớp với giấy đăng ký kinh doanh."
                ),
                "documents": ["business", "food_safety"],
            })

        # Check 3: Business address vs Food Safety address
        biz_addr = business.get("address", "")
        fs_addr = food_safety.get("address", "")
        if biz_addr and fs_addr and not _addresses_match(biz_addr, fs_addr):
            errors.append({
                "code": "ADDRESS_MISMATCH_BUSINESS_FOOD_SAFETY",
                "message": (
                    "Địa chỉ trên giấy chứng nhận an toàn thực phẩm không khớp "
                    "với địa chỉ trên giấy đăng ký kinh doanh."
                ),
                "documents": ["business", "food_safety"],
            })

        # Check 4: Food Safety certificate not expired
        expiry_str = food_safety.get("expiry_date")
        if expiry_str:
            try:
                if date.fromisoformat(expiry_str) < date.today():
                    errors.append({
                        "code": "FOOD_SAFETY_CERT_EXPIRED",
                        "message": "Giấy chứng nhận an toàn thực phẩm đã hết hạn.",
                        "documents": ["food_safety"],
                    })
            except (ValueError, TypeError):
                pass

        if errors:
            session.cross_validation_passed = False
            session.cross_validation_errors = errors
            session.save(update_fields=["cross_validation_passed", "cross_validation_errors", "updated_at"])
            raise CrossValidationFailed(errors=errors)

        session.cross_validation_passed = True
        session.cross_validation_errors = []
        session.status = VerificationSessionStatusEnum.AWAITING_SELFIE
        session.save(update_fields=[
            "cross_validation_passed", "cross_validation_errors", "status", "updated_at"
        ])
        return {"passed": True, "next_step": "SELFIE"}

    # ── Selfie + Face Matching + Decision ─────────────────────────────────────

    def request_selfie_code(self, user: TUser) -> dict:
        """Sinh mã xác thực cho bước selfie (TTL 10 phút)."""
        session = self._get_or_create_session(user)
        code = session.generate_verification_code()
        return {
            "verification_code": code,
            "expires_at": session.verification_code_expires_at.isoformat(),
        }

    def analyze_selfie(self, user: TUser, attachment_uid: UUID) -> ChefVerificationSession:
        """
        Bước 4–7:
          1. Gemini đọc selfie → kiểm tra face, ID card, verification_code
          2. Backend verify code match
          3. InsightFace so khuôn mặt CCCD vs selfie
          4. Risk Engine tính risk_score + decision
        """
        session = self._get_or_create_session(user)

        if session.status == VerificationSessionStatusEnum.COMPLETED:
            raise VerificationAlreadyCompleted()

        if not session.verification_code_is_valid():
            raise SelfieCodeExpired()

        attachment = self._get_completed_attachment(attachment_uid)

        # Step 1: Gemini analyze selfie
        selfie_result = gemini_service.analyze_selfie(
            public_url=attachment.public_url,
            expected_code=session.verification_code,
        )
        if selfie_result["errors"]:
            raise VerificationDocumentError(errors=selfie_result["errors"])

        # Step 2: Verify code
        code_read = (selfie_result.get("verification_code_read") or "").strip().upper()
        expected = session.verification_code.strip().upper()
        if code_read != expected:
            raise SelfieCodeMismatch()

        session.selfie_attachment = attachment
        session.selfie_extracted = selfie_result
        session.save(update_fields=["selfie_attachment", "selfie_extracted", "updated_at"])

        # Step 3: Face matching — dùng ảnh đầu tiên của CCCD (mặt trước)
        similarity: float | None = None
        try:
            cccd_primary_uid = (session.cccd_attachment_uids or [None])[0]
            if cccd_primary_uid:
                cccd_attachment = AttachmentQuery().get_instance_by_uid(uid=cccd_primary_uid)
                if cccd_attachment:
                    cccd_bytes = http_requests.get(cccd_attachment.public_url, timeout=15).content
                    selfie_bytes = http_requests.get(attachment.public_url, timeout=15).content
                    similarity = compare_faces(cccd_bytes, selfie_bytes)
        except Exception as exc:
            logger.warning("Face matching skipped due to error: %s", exc)

        session.face_similarity_score = similarity

        # Step 4: Risk engine
        risk_flags = risk_engine.collect_risk_flags(session)
        risk_score = risk_engine.calculate_risk_score(risk_flags)
        decision = risk_engine.make_decision(risk_score)

        session.risk_flags = risk_flags
        session.risk_score = risk_score
        session.decision = decision
        session.status = VerificationSessionStatusEnum.COMPLETED
        session.save(update_fields=[
            "face_similarity_score",
            "risk_flags",
            "risk_score",
            "decision",
            "status",
            "updated_at",
        ])

        # Bước 1: Xóa ảnh nhạy cảm khỏi S3 — ưu tiên cao nhất, tách riêng
        try:
            _delete_sensitive_images(session)
        except Exception as exc:
            logger.error("S3 sensitive image deletion failed: %s", exc, exc_info=True)

        # Bước 2: Lưu identity an toàn + tạo Certificate — có thể fail mà không ảnh hưởng bước 1
        try:
            _finalize_verification(session)
        except Exception as exc:
            logger.error("finalize_verification failed: %s", exc, exc_info=True)

        return session

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self, user: TUser) -> ChefVerificationSession:
        return self._require_session(user)


# ── Address / Name matching helpers ──────────────────────────────────────────

def _normalize(text: str) -> str:
    from utils.functions.remove_accents import remove_accents
    return remove_accents(text.strip().lower())


def _names_match(a: str, b: str) -> bool:
    return _normalize(a) == _normalize(b)


def _addresses_match(a: str, b: str) -> bool:
    """
    Dùng Gemini để so sánh ngữ nghĩa địa chỉ.
    Xử lý: viết tắt, mô tả khác nhau cùng nơi, format khác.
    Fail-safe: nếu Gemini không gọi được → coi là khớp (đẩy về risk score thay vì hard reject).
    """
    if not a or not b:
        return True
    return gemini_service.verify_same_address(a, b)


# ── Post-decision finalization ────────────────────────────────────────────────

def _mask_cccd_number(number: str) -> str:
    """079123456789 → 079******789 (keep first 3 + last 3, mask middle)."""
    if len(number) <= 6:
        return number
    return number[:3] + "*" * (len(number) - 6) + number[-3:]


def _delete_from_s3(attachment) -> None:
    """Delete the physical file from S3 and mark the Attachment record as deleted."""
    if not attachment or not getattr(settings, "USE_S3", False):
        return
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
        )
        key = f"{attachment.directory}/{attachment.hashed_name}"
        s3.delete_object(Bucket=attachment.bucket, Key=key)
        logger.info("Deleted CCCD file from S3: %s", key)
    except Exception as exc:
        logger.error("S3 delete failed for attachment %s: %s", attachment.uid, exc)
        raise

    attachment.is_file_deleted = True
    attachment.is_deleted = True
    attachment.save(update_fields=["is_file_deleted", "is_deleted"])


def _create_certificate_from_session(
    user, cert_type, confirmed_data, attachment_uids: list, decision: str
):
    """
    Tạo Certificate record trong app certificate từ dữ liệu Gemini đã confirmed.
    Tạo CertificateAttachment cho TẤT CẢ các trang (multi-page support).

        Certificate status theo decision:
            PENDING_REVIEW  → PENDING (vào queue admin review thủ công)
            REJECTED        → PENDING (không auto-approve; admin quyết định)
    """
    from certificate.models import Certificate, CertificateAttachment
    from attachment.queries import Query as AttachmentQuery

    if cert_type == CertificateTypeEnum.BUSINESS_LICENSE:
        name = confirmed_data.get("business_name") or confirmed_data.get("owner_name") or "Giấy ĐKKD"
        issued_by = "Cơ quan đăng ký kinh doanh"
        issue_date_str = confirmed_data.get("issue_date")
        expiry_date_str = None
    else:  # FOOD_SAFETY
        name = confirmed_data.get("facility_name") or confirmed_data.get("owner_name") or "Giấy ATTP"
        issued_by = "Cơ quan an toàn thực phẩm"
        issue_date_str = confirmed_data.get("issue_date")
        expiry_date_str = confirmed_data.get("expiry_date")

    from datetime import date as date_type
    issue_date = None
    expiry_date = None
    try:
        if issue_date_str:
            issue_date = date_type.fromisoformat(issue_date_str)
    except (ValueError, TypeError):
        pass
    try:
        if expiry_date_str:
            expiry_date = date_type.fromisoformat(expiry_date_str)
    except (ValueError, TypeError):
        pass

    # AI không auto-approve. Chỉ admin mới có thể chuyển certificate sang ACTIVE.
    cert_status = CertificateStatusEnum.PENDING

    cert = Certificate.objects.create(
        name=name,
        issued_by=issued_by,
        issue_date=issue_date or date_type.today(),
        expiration_date=expiry_date,
        owner=user,
        certificate_type=cert_type,
        status=cert_status,
    )

    # Tạo CertificateAttachment cho từng trang — đúng với model của app certificate
    query = AttachmentQuery()
    for uid_str in attachment_uids:
        att = query.get_instance_by_uid(uid=uid_str)
        if att:
            CertificateAttachment.objects.create(certificate=cert, attachment=att)

    return cert


def _schedule_s3_deletion(attachment, delay_days: int = 30) -> None:
    """
    Lên lịch xóa file S3 sau delay_days ngày.
    File vật lý chưa bị xóa — management command sẽ xóa sau.
    """
    from django.utils.timezone import now
    from datetime import timedelta
    from verification.models import ScheduledS3Deletion

    if not attachment or not getattr(settings, "USE_S3", False):
        return
    if attachment.is_file_deleted:
        return

    key = f"{attachment.directory}/{attachment.hashed_name}"
    ScheduledS3Deletion.objects.get_or_create(
        attachment_uid=attachment.uid,
        defaults={
            "s3_bucket": attachment.bucket,
            "s3_key": key,
            "delete_after": now() + timedelta(days=delay_days),
        },
    )
    logger.info("Scheduled S3 deletion for attachment %s in %d days", attachment.uid, delay_days)


def _delete_sensitive_images(session: ChefVerificationSession) -> None:
    """
    Sau khi ra quyết định:
    - VERIFIED / REJECTED: xóa CCCD và selfie khỏi S3 ngay lập tức.
    - PENDING_REVIEW: GIỮ NGUYÊN — admin cần xem để review.
      Sẽ xóa sau 30 ngày kể từ khi admin hoàn tất review chứng chỉ cuối.
    """
    if session.decision == "PENDING_REVIEW":
        # Không xóa gì hết — giữ CCCD + selfie để admin xem
        return

    from attachment.queries import Query as AttachmentQuery

    # Xóa tất cả trang CCCD
    for uid_str in list(session.cccd_attachment_uids or []):
        try:
            att = AttachmentQuery().get_instance_by_uid(uid=uid_str)
            if att:
                _delete_from_s3(att)
                logger.info("Deleted CCCD image %s from S3", uid_str)
        except Exception as exc:
            logger.error("S3 delete failed for CCCD %s: %s", uid_str, exc)

    # Xóa selfie
    if session.selfie_attachment_id:
        try:
            _delete_from_s3(session.selfie_attachment)
            logger.info("Deleted selfie from S3")
        except Exception as exc:
            logger.error("S3 delete failed for selfie: %s", exc)


def _finalize_verification(session: ChefVerificationSession) -> None:
    """
    Chạy sau khi decision được set. Thực hiện:
      1. Xóa ảnh CCCD khỏi S3 (privacy)
      2. Lưu identity an toàn (masked number + Argon2id hash + clean JSON)
      3. Xóa raw CCCD data khỏi session
      4. Tạo Certificate records cho ĐKKD và ATTP (nếu không REJECTED)
    """
    cccd_confirmed = session.cccd_confirmed or {}

    # ── 1. Hash + mask CCCD number ────────────────────────────────────────────
    raw_number = cccd_confirmed.get("cccd_number", "")
    if raw_number:
        session.cccd_number_masked = _mask_cccd_number(raw_number)
        session.cccd_number_hash = _cccd_hasher.hash(raw_number)

    # ── 2. Store safe identity (no CCCD number) ───────────────────────────────
    session.verified_identity = {
        "full_name": cccd_confirmed.get("full_name"),
        "date_of_birth": cccd_confirmed.get("date_of_birth"),
    }
    session.verified_at = now()

    # ── 3. Wipe raw CCCD data ──────────────────────────────────────────────────
    session.cccd_extracted = None
    session.cccd_confirmed = None

    # ── 4. Unlink attachment references trong DB ──────────────────────────────
    # VERIFIED/REJECTED: file đã bị xóa bởi _delete_sensitive_images() → clear references.
    # PENDING_REVIEW: file vẫn tồn tại (admin cần xem) → GIỮ references.
    if session.decision != "PENDING_REVIEW":
        session.cccd_attachment_uids = []
        session.selfie_attachment = None

    session.save(update_fields=[
        "cccd_number_masked", "cccd_number_hash",
        "verified_identity", "verified_at",
        "cccd_extracted", "cccd_confirmed",
        "cccd_attachment_uids",
        "selfie_attachment",
        "updated_at",
    ])

    # ── 5. Tạo Certificate records trong app certificate ──────────────────────
    # Chỉ tạo khi không bị REJECTED.
    # FK được lưu vào session để truy xuất sau (admin có thể dùng /certificates/ API).
    if session.decision != "REJECTED":
        fields_to_update = []

        if session.business_confirmed and session.business_attachment_uids \
                and not session.business_certificate_id:   # guard: chưa tạo
            try:
                biz_cert = _create_certificate_from_session(
                    user=session.user,
                    cert_type=CertificateTypeEnum.BUSINESS_LICENSE,
                    confirmed_data=session.business_confirmed,
                    attachment_uids=session.business_attachment_uids,
                    decision=session.decision,
                )
                session.business_certificate = biz_cert
                fields_to_update.append("business_certificate")
            except Exception as exc:
                logger.error("Failed to create Business Certificate: %s", exc)

        if session.food_safety_confirmed and session.food_safety_attachment_uids \
                and not session.food_safety_certificate_id:   # guard: chưa tạo
            try:
                fs_cert = _create_certificate_from_session(
                    user=session.user,
                    cert_type=CertificateTypeEnum.FOOD_SAFETY,
                    confirmed_data=session.food_safety_confirmed,
                    attachment_uids=session.food_safety_attachment_uids,
                    decision=session.decision,
                )
                session.food_safety_certificate = fs_cert
                fields_to_update.append("food_safety_certificate")
            except Exception as exc:
                logger.error("Failed to create Food Safety Certificate: %s", exc)

        if fields_to_update:
            session.save(update_fields=fields_to_update + ["updated_at"])
