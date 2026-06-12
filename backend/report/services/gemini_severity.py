"""
Gemini severity classifier cho Chef Report.

Nhận vào: category + description từ customer.
Trả về: severity (LOW/MEDIUM/HIGH/CRITICAL), food_safety_risk, keywords_detected, reason.

Chỉ có trách nhiệm phân loại — quyết định khóa do analysis.py thực hiện.
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger("django")

_SEVERITY_PROMPT = """\
Phân tích nội dung phản ánh về chất lượng thức ăn của khách hàng và phân loại mức độ nghiêm trọng.

Danh mục phản ánh: {category}
Mô tả của khách: {description}

Trả về JSON đúng cấu trúc sau, không kèm markdown:
{{
  "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "food_safety_risk": true | false,
  "keywords_detected": ["<từ khóa 1>", "<từ khóa 2>"],
  "confidence": "high" | "medium" | "low",
  "reason": "<giải thích ngắn dưới 2 câu>"
}}

Quy tắc phân loại:
- CRITICAL: Dị vật nguy hiểm (tóc, kim loại, kính, sâu), mốc nhìn thấy được, nghi ngờ ngộ độc thực phẩm.
- HIGH: Thức ăn hôi thối, hư thiu, ôi, tanh nặng — có nguy cơ gây hại cho sức khỏe nếu ăn.
- MEDIUM: Sạn/cát trong thức ăn, thức ăn tái/sống nhẹ, vệ sinh bao bì kém, mùi lạ nhẹ.
- LOW: Không ngon, ít đồ, sai món, thiếu gia vị, giao nhầm — không ảnh hưởng sức khỏe.

food_safety_risk = true khi severity là HIGH hoặc CRITICAL.
keywords_detected: liệt kê các từ/cụm từ liên quan đến an toàn thực phẩm tìm thấy trong mô tả.
"""


def analyze_report_severity(category: str, description: str) -> dict:
    """
    Gọi Gemini để phân loại mức độ nghiêm trọng của report.

    Returns dict với các keys:
      - severity: str (LOW/MEDIUM/HIGH/CRITICAL)
      - food_safety_risk: bool
      - keywords_detected: list[str]
      - confidence: str
      - reason: str

    Raises: Không raise — mọi lỗi đều được log và trả về fallback LOW.
    """
    import time
    try:
        from google import genai
        from google.genai import types
        from google.genai.errors import ClientError

        prompt = _SEVERITY_PROMPT.format(
            category=category,
            description=description,
        )

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=types.Content(
                        parts=[types.Part(text=prompt)],
                        role="user",
                    ),
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                result = json.loads(response.text)
                return {
                    "severity": result.get("severity", "LOW"),
                    "food_safety_risk": bool(result.get("food_safety_risk", False)),
                    "keywords_detected": result.get("keywords_detected", []),
                    "confidence": result.get("confidence", "low"),
                    "reason": result.get("reason", ""),
                }
            except ClientError as exc:
                is_429 = exc.args[0] == 429 or "429" in str(exc)
                is_daily = "PerDay" in str(exc) or "per_day" in str(exc)
                if is_429 and not is_daily and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise

    except Exception as exc:
        logger.warning("Gemini severity analysis failed, defaulting to LOW: %s", exc)
        return {
            "severity": "LOW",
            "food_safety_risk": False,
            "keywords_detected": [],
            "confidence": "low",
            "reason": "Không thể phân tích tự động.",
        }
