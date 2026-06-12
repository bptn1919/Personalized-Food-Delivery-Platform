"""
RiskEngine + DecisionEngine — Tính Risk Score và ra quyết định cuối.

Nguyên tắc: AI chỉ có quyền gợi ý từ chối. Quyết định chấp thuận cuối cùng thuộc về ADMIN,
vì vậy backend chỉ trả về:
    - PENDING_REVIEW: không đủ lý do để reject, chuyển admin duyệt thủ công
    - REJECTED: AI phát hiện rủi ro cao, loại ngay

Risk Score thresholds:
    < 80       → PENDING_REVIEW
    >= 80      → REJECTED
"""

from datetime import date

# ── Risk weights ──────────────────────────────────────────────────────────────

_RISK_WEIGHTS: dict[str, int] = {
    "IMAGE_BLURRY_CCCD": 10,
    "IMAGE_BLURRY_BUSINESS": 10,
    "IMAGE_BLURRY_FOOD_SAFETY": 10,
    "POSSIBLE_EDITING": 30,
    "MISSING_SIGNATURE_BUSINESS": 10,
    "MISSING_RED_STAMP_BUSINESS": 10,
    "MISSING_SIGNATURE_FOOD_SAFETY": 10,
    "MISSING_RED_STAMP_FOOD_SAFETY": 10,
    "OWNER_NAME_MISMATCH": 50,
    "ADDRESS_MISMATCH": 30,
    "FOOD_SAFETY_CERT_EXPIRED": 100,
    "FACE_MATCH_REVIEW": 20,    # similarity 0.65–0.80
    "FACE_MATCH_FAILED": 70,    # similarity < 0.65
    "FACE_NOT_DETECTED": 50,    # InsightFace không phát hiện mặt
}

FACE_PASS_THRESHOLD = 0.80
FACE_REVIEW_THRESHOLD = 0.65


def collect_risk_flags(session) -> list[str]:
    """
    Collect all risk flags from the session's confirmed data, cross-validation errors,
    and face matching result. Called after selfie analysis is complete.
    """
    flags: list[str] = []

    # ── Image quality & editing ───────────────────────────────────────────────
    cccd = session.cccd_confirmed or {}
    if not cccd.get("image_clear", True):
        flags.append("IMAGE_BLURRY_CCCD")
    if cccd.get("possible_editing", False):
        flags.append("POSSIBLE_EDITING")

    business = session.business_confirmed or {}
    if not business.get("image_clear", True):
        flags.append("IMAGE_BLURRY_BUSINESS")
    if not business.get("has_signature", True):
        flags.append("MISSING_SIGNATURE_BUSINESS")
    if not business.get("has_red_stamp", True):
        flags.append("MISSING_RED_STAMP_BUSINESS")

    food_safety = session.food_safety_confirmed or {}
    if not food_safety.get("image_clear", True):
        flags.append("IMAGE_BLURRY_FOOD_SAFETY")
    if not food_safety.get("has_signature", True):
        flags.append("MISSING_SIGNATURE_FOOD_SAFETY")
    if not food_safety.get("has_red_stamp", True):
        flags.append("MISSING_RED_STAMP_FOOD_SAFETY")

    # ── Cross-validation results ──────────────────────────────────────────────
    for cv_err in session.cross_validation_errors:
        code = cv_err.get("code", "")
        if "OWNER_NAME_MISMATCH" in code:
            if "OWNER_NAME_MISMATCH" not in flags:
                flags.append("OWNER_NAME_MISMATCH")
        elif "ADDRESS_MISMATCH" in code:
            if "ADDRESS_MISMATCH" not in flags:
                flags.append("ADDRESS_MISMATCH")
        elif code == "FOOD_SAFETY_CERT_EXPIRED":
            flags.append("FOOD_SAFETY_CERT_EXPIRED")

    # ── Food safety expiry (double-check from confirmed data) ─────────────────
    expiry_str = food_safety.get("expiry_date")
    if expiry_str:
        try:
            if date.fromisoformat(expiry_str) < date.today():
                if "FOOD_SAFETY_CERT_EXPIRED" not in flags:
                    flags.append("FOOD_SAFETY_CERT_EXPIRED")
        except (ValueError, TypeError):
            pass

    # ── Face matching ─────────────────────────────────────────────────────────
    score = session.face_similarity_score
    if score is None:
        flags.append("FACE_NOT_DETECTED")
    elif score < FACE_REVIEW_THRESHOLD:
        flags.append("FACE_MATCH_FAILED")
    elif score < FACE_PASS_THRESHOLD:
        flags.append("FACE_MATCH_REVIEW")

    return flags


def calculate_risk_score(flags: list[str]) -> int:
    return sum(_RISK_WEIGHTS.get(f, 0) for f in flags)


def make_decision(risk_score: int) -> str:
    if risk_score >= 80:
        return "REJECTED"
    return "PENDING_REVIEW"
