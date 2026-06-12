import secrets
from datetime import timedelta

from django.db import models
from django.utils.timezone import now

from utils.enums import DocumentStepStatusEnum, VerificationSessionStatusEnum
from utils.types import User

_VERIFICATION_CODE_TTL_MINUTES = 10


class ChefVerificationSession(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name="chef_verification_session",
        db_index=True,
    )

    # ── CCCD (Căn cước công dân) ──────────────────────────────────────────────
    cccd_status = models.CharField(
        max_length=20,
        choices=DocumentStepStatusEnum.choices,
        default=DocumentStepStatusEnum.PENDING,
    )
    # Lưu list UUID strings — thường 1 ảnh (mặt trước), tối đa 2 (mặt trước + sau)
    # Ảnh đầu tiên được dùng cho face matching
    cccd_attachment_uids = models.JSONField(default=list)
    cccd_extracted = models.JSONField(null=True, blank=True)
    cccd_confirmed = models.JSONField(null=True, blank=True)

    # ── Giấy đăng ký kinh doanh (ĐKKD) ───────────────────────────────────────
    business_status = models.CharField(
        max_length=20,
        choices=DocumentStepStatusEnum.choices,
        default=DocumentStepStatusEnum.PENDING,
    )
    # Hỗ trợ nhiều trang: ["uid1", "uid2", ...]
    business_attachment_uids = models.JSONField(default=list)
    business_extracted = models.JSONField(null=True, blank=True)
    business_confirmed = models.JSONField(null=True, blank=True)

    # ── Giấy chứng nhận ATTP ──────────────────────────────────────────────────
    food_safety_status = models.CharField(
        max_length=20,
        choices=DocumentStepStatusEnum.choices,
        default=DocumentStepStatusEnum.PENDING,
    )
    food_safety_attachment_uids = models.JSONField(default=list)
    food_safety_extracted = models.JSONField(null=True, blank=True)
    food_safety_confirmed = models.JSONField(null=True, blank=True)

    # ── Liên kết Certificate records được tạo sau khi finalize ───────────────
    # FK về app certificate — lưu để session biết certificate nào nó đã tạo
    business_certificate = models.ForeignKey(
        "certificate.Certificate",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
    )
    food_safety_certificate = models.ForeignKey(
        "certificate.Certificate",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
    )

    # ── Cross-validation ──────────────────────────────────────────────────────
    cross_validation_passed = models.BooleanField(null=True)
    cross_validation_errors = models.JSONField(default=list)

    # ── Selfie ────────────────────────────────────────────────────────────────
    verification_code = models.CharField(max_length=20, null=True, blank=True)
    verification_code_expires_at = models.DateTimeField(null=True, blank=True)
    selfie_attachment = models.ForeignKey(
        "attachment.Attachment",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        to_field="uid",
        db_column="selfie_attachment_uid",
    )
    selfie_extracted = models.JSONField(null=True, blank=True)

    # ── Face matching ─────────────────────────────────────────────────────────
    face_similarity_score = models.FloatField(null=True, blank=True)

    # ── Risk & Decision ───────────────────────────────────────────────────────
    risk_flags = models.JSONField(default=list)
    risk_score = models.IntegerField(default=0)
    decision = models.CharField(max_length=20, null=True, blank=True)

    # ── Overall session status ────────────────────────────────────────────────
    status = models.CharField(
        max_length=25,
        choices=VerificationSessionStatusEnum.choices,
        default=VerificationSessionStatusEnum.IN_PROGRESS,
    )

    # ── Post-verification safe identity data ──────────────────────────────────
    # Stored after decision is made; raw CCCD data + attachment are wiped.
    # CCCD number is never stored in plaintext — only masked (display) + hash (uniqueness check).
    cccd_number_masked = models.CharField(max_length=20, null=True, blank=True)  # 079******789
    cccd_number_hash = models.TextField(null=True, blank=True)                   # Argon2id hash
    verified_identity = models.JSONField(null=True, blank=True)                  # {full_name, date_of_birth}
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def all_documents_confirmed(self) -> bool:
        return (
            self.cccd_status == DocumentStepStatusEnum.CONFIRMED
            and self.business_status == DocumentStepStatusEnum.CONFIRMED
            and self.food_safety_status == DocumentStepStatusEnum.CONFIRMED
        )

    def generate_verification_code(self) -> str:
        """Generate a new selfie verification code and persist it."""
        code = f"VERIFY-{secrets.randbelow(900000) + 100000}"
        self.verification_code = code
        self.verification_code_expires_at = now() + timedelta(minutes=_VERIFICATION_CODE_TTL_MINUTES)
        self.save(update_fields=["verification_code", "verification_code_expires_at", "updated_at"])
        return code

    def verification_code_is_valid(self) -> bool:
        return (
            bool(self.verification_code)
            and self.verification_code_expires_at is not None
            and now() <= self.verification_code_expires_at
        )

    class Meta:
        verbose_name = "Chef Verification Session"
        verbose_name_plural = "Chef Verification Sessions"


class ScheduledS3Deletion(models.Model):
    """
    Lên lịch xóa file S3 sau một thời điểm nhất định.
    Dùng cho CCCD + selfie của PENDING_REVIEW sessions: xóa sau 30 ngày
    kể từ khi admin hoàn tất review chứng chỉ cuối cùng.
    """
    attachment_uid = models.UUIDField(db_index=True)
    s3_bucket = models.CharField(max_length=255)
    s3_key = models.TextField()
    delete_after = models.DateTimeField(db_index=True)
    is_executed = models.BooleanField(default=False, db_index=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Scheduled S3 Deletion"
        verbose_name_plural = "Scheduled S3 Deletions"
        indexes = [
            models.Index(fields=["is_executed", "delete_after"]),
        ]
