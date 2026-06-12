import secrets
from datetime import timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from utils.enums import OtpPurposeEnum

OTP_MAX_ATTEMPTS = 3

# Argon2id with moderate cost — makes offline enumeration of 10k OTP values slow.
_otp_hasher = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1, hash_len=32, salt_len=16)


def _otp_expiry_minutes(purpose: str) -> int:
    mapping: dict = getattr(settings, "OTP_EXPIRY_MINUTES", {})
    return mapping.get(purpose, getattr(settings, "RESET_PASSWORD_EXPIRES_IN_MINUTES", 15))

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  
    
    objects = UserManager()

    @property
    def is_onboarded(self) -> bool:
        try:
            return bool(self.customer_profile.is_onboarded)
        except ObjectDoesNotExist:
            return False

class AuthenticateToken(models.Model):
    """
    DB backup for Redis-backed refresh tokens.
    Primary store: Redis (fast). This table is the persistent fallback.

    token_hash = HMAC-SHA256(pepper, raw_token) — raw token không bao giờ lưu ở đây.
    """
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authenticate_tokens",
        db_index=True,
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    jti = models.UUIDField(unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_valid(self) -> bool:
        return self.revoked_at is None and self.expires_at > now()

    class Meta:
        indexes = [
            models.Index(fields=["user", "revoked_at"]),
        ]



class UserOTP(models.Model):
    user = models.ForeignKey(
       to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        to_field="id",
        db_column="user_id",
        related_name="reset_password_fk_user",
        db_constraint=True,
        null=False,
        blank=False,
    )
    # Argon2id hash of the plaintext OTP — salt is embedded in the hash string.
    otp_hash = models.TextField(null=False, blank=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    otp_verified = models.BooleanField(default=False)
    reset_session_token = models.CharField(
        max_length=255, unique=True, db_index=True
    )
    purpose = models.CharField(
        max_length=16, choices=OtpPurposeEnum.choices, null=False, blank=False
    )
    target_email = models.EmailField(max_length=254, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    def is_expired(self) -> bool:
        return now() > self.created_at + timedelta(minutes=_otp_expiry_minutes(self.purpose))

    def verify(self, otp: str) -> bool:
        """Verify OTP. Increments attempts on failure; raises ValueError when locked out."""
        if self.attempts >= OTP_MAX_ATTEMPTS:
            raise ValueError("max_attempts_exceeded")
        try:
            _otp_hasher.verify(self.otp_hash, otp)
            return True
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            self.attempts += 1
            self.save(update_fields=["attempts", "updated_at"])
            return False
