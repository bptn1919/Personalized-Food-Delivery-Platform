"""
Local rule-based severity classifier for ChefReport.

This replaces the previous Gemini-based analyzer. It classifies severity
based on the user-selected category and keyword matching in the description.
Returns the same dict shape previously expected by the system.
"""
import logging
import re
from typing import List

logger = logging.getLogger("django")


def _keywords_in_text(text: str, kws: List[str]) -> List[str]:
    found = []
    for kw in kws:
        if re.search(r"\b" + re.escape(kw) + r"\b", text, flags=re.I):
            found.append(kw)
    return found


def analyze_report_severity(category: str, description: str) -> dict:
    """
    Simple deterministic classifier:
      - Uses the explicit `category` chosen by the customer as the primary signal.
      - Augments with keyword lookup in `description` to raise severity for
        dangerous tokens (e.g. glass, metal, mốc, ngộ độc, đau bụng).

    Returns a dict with keys: severity, food_safety_risk, keywords_detected, confidence, reason
    """
    text = (description or "").strip()

    critical_kw = ["kính", "kim loại", "kimloại", "dao", "kim", "mốc", "ngộ độc", "đau bụng", "ngộ độc thực phẩm", "dị vật"]
    foreign_kw = ["tóc", "côn trùng", "dị vật", "xương", "mảnh", "vật thể lạ"]

    keywords = _keywords_in_text(text, critical_kw + foreign_kw)

    # Default outputs
    severity = "LOW"
    food_safety_risk = False
    confidence = "medium"
    reason = "Phân loại dựa trên category do customer chọn."

    cat = (category or "").upper()
    if cat == "FOREIGN_OBJECT":
        severity = "CRITICAL"
        food_safety_risk = True
        confidence = "high"
        reason = "Phát hiện dị vật/khuyến cáo nguy hiểm theo category."
    elif cat == "FOOD_SAFETY":
        severity = "CRITICAL"
        food_safety_risk = True
        confidence = "high"
        reason = "Khách nghi ngờ ngộ độc thực phẩm."
    elif cat == "EXPIRED_INGREDIENT":
        severity = "HIGH"
        food_safety_risk = True
        confidence = "high"
        reason = "Nghi sử dụng nguyên liệu quá hạn."
    elif cat == "FOOD_QUALITY":
        # elevate if severe keywords present
        if any(k in keywords for k in critical_kw):
            severity = "HIGH"
            food_safety_risk = True
            confidence = "high"
            reason = "Từ khóa nguy hiểm được tìm thấy trong mô tả."
        else:
            severity = "MEDIUM"
            food_safety_risk = True
            confidence = "medium"
            reason = "Phản ánh chất lượng/thức ăn."
    elif cat == "HYGIENE":
        severity = "MEDIUM"
        food_safety_risk = True
        confidence = "medium"
        reason = "Vấn đề vệ sinh/độ sạch."
    elif cat == "MISLEADING_INFORMATION":
        severity = "MEDIUM"
        food_safety_risk = False
        confidence = "medium"
        reason = "Thông tin mô tả sai sự thật."
    elif cat == "PACKAGING_ISSUE":
        severity = "MEDIUM"
        food_safety_risk = True
        confidence = "medium"
        reason = "Vấn đề bao bì có thể ảnh hưởng an toàn."
    elif cat == "OTHER":
        severity = "LOW"
        food_safety_risk = False
        confidence = "low"
        reason = "Khác — không xác định."
    else:
        # unknown category — fallback conservative
        severity = "LOW"
        food_safety_risk = False
        confidence = "low"
        reason = "Category không rõ — mặc định LOW."

    # If critical keywords found in any category, bump severity to at least HIGH
    if keywords and severity in ("LOW", "MEDIUM"):
        severity = "HIGH"
        food_safety_risk = True
        confidence = "high"
        reason = "Từ khóa nghiêm trọng xuất hiện trong mô tả."

    return {
        "severity": severity,
        "food_safety_risk": bool(food_safety_risk),
        "keywords_detected": keywords,
        "confidence": confidence,
        "reason": reason,
    }
