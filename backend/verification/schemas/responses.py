from typing import Optional
from ninja import Schema


# ── Extracted data schemas (returned to chef for review) ─────────────────────

class CCCDExtractedSchema(Schema):
    full_name: Optional[str] = None
    cccd_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None


class BusinessExtractedSchema(Schema):
    owner_name: Optional[str] = None
    business_name: Optional[str] = None
    business_license_number: Optional[str] = None
    address: Optional[str] = None
    issue_date: Optional[str] = None


class FoodSafetyExtractedSchema(Schema):
    owner_name: Optional[str] = None
    facility_name: Optional[str] = None
    certificate_number: Optional[str] = None
    address: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None


# ── Analyze responses (Giai đoạn 1) ──────────────────────────────────────────

class AnalyzeCCCDResponse(Schema):
    session_id: int
    extracted: CCCDExtractedSchema


class AnalyzeBusinessResponse(Schema):
    session_id: int
    extracted: BusinessExtractedSchema


class AnalyzeFoodSafetyResponse(Schema):
    session_id: int
    extracted: FoodSafetyExtractedSchema


# ── Confirm response (Giai đoạn 2) ───────────────────────────────────────────

class ConfirmResponse(Schema):
    status: str   # "CONFIRMED"


# ── Cross validation response (Giai đoạn 3) ──────────────────────────────────

class CrossValidationResponse(Schema):
    passed: bool
    next_step: Optional[str] = None   # "SELFIE" when passed


# ── Selfie responses ──────────────────────────────────────────────────────────

class VerificationCodeResponse(Schema):
    verification_code: str
    expires_at: str   # ISO 8601


class VerificationDecisionResponse(Schema):
    decision: str              # PENDING_REVIEW | REJECTED
    risk_score: int
    risk_flags: list[str]
    face_similarity_score: Optional[float] = None
    status: str                # COMPLETED


# ── Status response ───────────────────────────────────────────────────────────

class VerifiedIdentitySchema(Schema):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None


class SessionStatusResponse(Schema):
    status: str
    cccd_status: str
    business_status: str
    food_safety_status: str
    cross_validation_passed: Optional[bool] = None
    decision: Optional[str] = None
    risk_score: int
    risk_flags: list[str] = []
    face_similarity_score: Optional[float] = None
    # Post-verification safe identity fields
    cccd_number_masked: Optional[str] = None
    verified_identity: Optional[VerifiedIdentitySchema] = None
    verified_at: Optional[str] = None
    # Admin review: URL selfie (chỉ có khi PENDING_REVIEW, xóa sau khi admin duyệt)
    selfie_url: Optional[str] = None
