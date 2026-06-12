"""
GeminiVisionService — OCR và phân tích ảnh giấy tờ.

Gemini chỉ chịu trách nhiệm:
  - OCR & trích xuất thông tin cấu trúc
  - Kiểm tra chất lượng ảnh (mờ, bị cắt, có con dấu, chữ ký...)
  - Đọc mã xác thực trong ảnh selfie

Mọi quyết định nghiệp vụ (cross-check, risk score, final decision)
đều do Backend thực hiện — xem engine.py và verification.py.
"""

import json
import logging

import requests as http_requests
from django.conf import settings

logger = logging.getLogger("django")

# ── Bảng thông báo lỗi theo ngôn ngữ tiếng Việt ─────────────────────────────

_CCCD_ERRORS = {
    "IMAGE_BLURRY": "Ảnh CCCD bị mờ, không đọc được nội dung.",
    "CCCD_NUMBER_NOT_READABLE": "Không đọc được số CCCD.",
    "PORTRAIT_MISSING": "Không tìm thấy ảnh chân dung trên CCCD.",
    "TEXT_NOT_READABLE": "Chữ trên CCCD không đọc được.",
    "WRONG_DOCUMENT_TYPE": "Đây không phải là CCCD Việt Nam.",
    "CCCD_NOT_FRONT": "Ảnh đầu tiên không phải mặt trước CCCD. Vui lòng tải đúng thứ tự: mặt trước trước, mặt sau sau.",
    "CCCD_NOT_BACK": "Ảnh thứ hai không phải mặt sau CCCD. Vui lòng tải đúng thứ tự: mặt trước trước, mặt sau sau.",
    "CCCD_SIDES_MISMATCH": "Mặt trước và mặt sau không thuộc cùng một CCCD (số CCCD không khớp). Vui lòng kiểm tra và tải lại.",
}

_BUSINESS_ERRORS = {
    "IMAGE_BLURRY": "Ảnh giấy phép kinh doanh bị mờ.",
    "OWNER_NAME_NOT_READABLE": "Không đọc được tên chủ hộ kinh doanh.",
    "LICENSE_NUMBER_NOT_READABLE": "Không đọc được số giấy phép kinh doanh.",
    "CONTENT_CROPPED": "Giấy tờ bị cắt mất nội dung quan trọng.",
    "WRONG_DOCUMENT_TYPE": "Đây không phải là giấy đăng ký kinh doanh.",
}

_FOOD_SAFETY_ERRORS = {
    "IMAGE_BLURRY": "Ảnh chứng nhận ATTP quá mờ.",
    "CERT_NUMBER_NOT_READABLE": "Không đọc được số chứng nhận ATTP.",
    "EXPIRY_DATE_NOT_READABLE": "Không đọc được ngày hết hạn.",
    "WRONG_DOCUMENT_TYPE": "Đây không phải là giấy chứng nhận an toàn thực phẩm.",
}

_SELFIE_ERRORS = {
    "FACE_NOT_DETECTED": "Không phát hiện khuôn mặt trong ảnh.",
    "ID_CARD_NOT_VISIBLE": "Không nhìn thấy CCCD trong ảnh selfie.",
    "VERIFICATION_CODE_NOT_VISIBLE": "Không thấy tờ giấy có mã xác thực trong ảnh.",
    "IMAGE_BLURRY": "Ảnh selfie bị mờ.",
}

# ── Prompts ───────────────────────────────────────────────────────────────────

_CCCD_PAIR_PROMPT = """
Bạn nhận được đúng 2 ảnh theo thứ tự: ảnh 1 = mặt TRƯỚC CCCD, ảnh 2 = mặt SAU CCCD.
Hãy phân tích và xác nhận từng mặt, sau đó kiểm tra 2 mặt có thuộc cùng một CCCD không.

Trả về JSON đúng cấu trúc sau, không kèm markdown:
{
  "front": {
    "is_front_side": true,
    "full_name": "<họ tên đầy đủ hoặc null>",
    "cccd_number": "<12 chữ số hoặc null>",
    "date_of_birth": "<YYYY-MM-DD hoặc null>",
    "address": "<địa chỉ thường trú hoặc null>",
    "has_portrait": true,
    "image_clear": true,
    "text_readable": true,
    "possible_editing": false
  },
  "back": {
    "is_back_side": true,
    "cccd_number_on_back": "<12 chữ số đọc từ mặt sau hoặc null>",
    "has_qr": true,
    "image_clear": true
  },
  "same_document": true,
  "document_errors": []
}

Quy tắc xác định mặt trước/sau:
- Mặt TRƯỚC: có ảnh chân dung, họ tên, số CCCD, ngày sinh, địa chỉ thường trú, quốc huy
- Mặt SAU: có chip điện tử, mã QR, vân tay điện tử, không có ảnh chân dung

same_document = false nếu:
- Số CCCD đọc được từ mặt trước và mặt sau KHÁC nhau (cả 2 đọc được mà khác)

Chỉ thêm mã lỗi vào document_errors khi thực sự gặp phải:
"IMAGE_BLURRY" | "CCCD_NUMBER_NOT_READABLE" | "PORTRAIT_MISSING" | "TEXT_NOT_READABLE" |
"WRONG_DOCUMENT_TYPE" | "CCCD_NOT_FRONT" | "CCCD_NOT_BACK" | "CCCD_SIDES_MISMATCH"
"""

_BUSINESS_PROMPT = """
Phân tích ảnh Giấy đăng ký hộ kinh doanh / Giấy phép kinh doanh Việt Nam.
Trả về JSON đúng cấu trúc sau, không kèm markdown:
{
  "owner_name": "<tên chủ hộ kinh doanh hoặc null>",
  "business_name": "<tên hộ/cơ sở kinh doanh hoặc null>",
  "business_license_number": "<số giấy phép hoặc null>",
  "address": "<địa chỉ kinh doanh hoặc null>",
  "issue_date": "<YYYY-MM-DD hoặc null>",
  "has_signature": true,
  "has_red_stamp": true,
  "document_errors": []
}
Chỉ thêm mã lỗi vào document_errors khi thực sự gặp phải:
"IMAGE_BLURRY" | "OWNER_NAME_NOT_READABLE" | "LICENSE_NUMBER_NOT_READABLE" | "CONTENT_CROPPED" | "WRONG_DOCUMENT_TYPE"
"""

_FOOD_SAFETY_PROMPT = """
Phân tích ảnh Giấy chứng nhận An toàn vệ sinh thực phẩm Việt Nam.
Trả về JSON đúng cấu trúc sau, không kèm markdown:
{
  "owner_name": "<tên chủ cơ sở hoặc null>",
  "facility_name": "<tên cơ sở kinh doanh hoặc null>",
  "certificate_number": "<số chứng nhận hoặc null>",
  "address": "<địa chỉ cơ sở hoặc null>",
  "issue_date": "<YYYY-MM-DD hoặc null>",
  "expiry_date": "<YYYY-MM-DD hoặc null>",
  "has_signature": true,
  "has_red_stamp": true,
  "document_errors": []
}
Chỉ thêm mã lỗi vào document_errors khi thực sự gặp phải:
"IMAGE_BLURRY" | "CERT_NUMBER_NOT_READABLE" | "EXPIRY_DATE_NOT_READABLE" | "WRONG_DOCUMENT_TYPE"
"""


def _selfie_prompt(expected_code: str) -> str:
    return f"""
Phân tích ảnh selfie này. Người chụp đang cầm CCCD và một tờ giấy có mã xác thực.
Mã xác thực cần đọc: {expected_code}
Trả về JSON đúng cấu trúc sau, không kèm markdown:
{{
  "face_detected": true,
  "has_id_card": true,
  "has_verification_code": true,
  "verification_code_read": "<mã đọc được hoặc null>",
  "document_errors": []
}}
Chỉ thêm mã lỗi vào document_errors khi thực sự gặp phải:
"FACE_NOT_DETECTED" | "ID_CARD_NOT_VISIBLE" | "VERIFICATION_CODE_NOT_VISIBLE" | "IMAGE_BLURRY"
"""

# ── Helpers ───────────────────────────────────────────────────────────────────


def _download(url: str) -> tuple[bytes, str]:
    resp = http_requests.get(url, timeout=15)
    resp.raise_for_status()
    mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    return resp.content, mime


_GEMINI_MODEL = "gemini-2.5-flash-lite"


def _call_gemini(images: list[tuple[bytes, str]], prompt: str) -> dict:
    """
    images: list of (image_bytes, mime_type) — hỗ trợ multi-page document.
    Tất cả ảnh được gửi trong 1 prompt để Gemini đọc toàn bộ nội dung.
    """
    import time
    from google import genai
    from google.genai import types
    from google.genai.errors import ClientError

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    image_parts = [
        types.Part(inline_data=types.Blob(mime_type=mime, data=data))
        for data, mime in images
    ]

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=_GEMINI_MODEL,
                contents=types.Content(
                    parts=image_parts + [types.Part(text=prompt)],
                    role="user",
                ),
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            return json.loads(response.text)
        except ClientError as exc:
            is_429 = exc.args[0] == 429 or "429" in str(exc)
            is_daily = "PerDay" in str(exc) or "per_day" in str(exc)
            if is_429 and not is_daily and attempt < 2:
                # Chỉ retry khi là per-minute rate limit, không retry daily quota
                time.sleep(2 ** attempt)
                continue
            raise


def _build_errors(codes: list[str], table: dict[str, str]) -> list[dict]:
    return [{"code": c, "message": table.get(c, c)} for c in codes]


def _download_all(public_urls: list[str]) -> list[tuple[bytes, str]]:
    return [_download(url) for url in public_urls]

# ── Public API ────────────────────────────────────────────────────────────────


def analyze_cccd(public_urls: list[str]) -> dict:
    """
    Yêu cầu đúng 2 URL: [mặt trước, mặt sau].
    Gemini validate cặp: đúng mặt trước/sau, cùng 1 CCCD.

    Returns:
        {"extracted": {...}, "errors": []}  on success
        {"extracted": None,  "errors": [...]} on document error
    """
    if len(public_urls) != 2:
        return {"extracted": None, "errors": _build_errors(["CCCD_NOT_FRONT"], _CCCD_ERRORS)}

    images = _download_all(public_urls)
    result = _call_gemini(images, _CCCD_PAIR_PROMPT)

    # Errors reported by Gemini
    gemini_errors = _build_errors(result.get("document_errors", []), _CCCD_ERRORS)

    front = result.get("front") or {}
    back = result.get("back") or {}

    # Hard-fail: wrong sides
    extra = []
    if not front.get("is_front_side", True):
        extra.append("CCCD_NOT_FRONT")
    if not back.get("is_back_side", True):
        extra.append("CCCD_NOT_BACK")
    if not result.get("same_document", True):
        extra.append("CCCD_SIDES_MISMATCH")

    # Mandatory front-side fields
    if not front.get("cccd_number"):
        extra.append("CCCD_NUMBER_NOT_READABLE")
    if not front.get("full_name"):
        extra.append("TEXT_NOT_READABLE")

    extra_errors = _build_errors(extra, _CCCD_ERRORS)
    all_errors = gemini_errors + [e for e in extra_errors if e["code"] not in {x["code"] for x in gemini_errors}]
    if all_errors:
        return {"extracted": None, "errors": all_errors}

    return {
        "extracted": {
            "full_name": front.get("full_name"),
            "cccd_number": front.get("cccd_number"),
            "date_of_birth": front.get("date_of_birth"),
            "address": front.get("address"),
            "image_clear": front.get("image_clear", True),
            "possible_editing": front.get("possible_editing", False),
            "back_has_qr": back.get("has_qr", False),
        },
        "errors": [],
    }


def analyze_business_license(public_urls: list[str]) -> dict:
    images = _download_all(public_urls)
    result = _call_gemini(images, _BUSINESS_PROMPT)

    gemini_errors = _build_errors(result.get("document_errors", []), _BUSINESS_ERRORS)

    extra = []
    if not result.get("owner_name"):
        extra.append("OWNER_NAME_NOT_READABLE")
    if not result.get("business_license_number"):
        extra.append("LICENSE_NUMBER_NOT_READABLE")
    extra_errors = _build_errors(extra, _BUSINESS_ERRORS)

    all_errors = gemini_errors + [e for e in extra_errors if e not in gemini_errors]
    if all_errors:
        return {"extracted": None, "errors": all_errors}

    return {
        "extracted": {
            "owner_name": result.get("owner_name"),
            "business_name": result.get("business_name"),
            "business_license_number": result.get("business_license_number"),
            "address": result.get("address"),
            "issue_date": result.get("issue_date"),
            "has_signature": result.get("has_signature", False),
            "has_red_stamp": result.get("has_red_stamp", False),
        },
        "errors": [],
    }


def analyze_food_safety(public_urls: list[str]) -> dict:
    images = _download_all(public_urls)
    result = _call_gemini(images, _FOOD_SAFETY_PROMPT)

    gemini_errors = _build_errors(result.get("document_errors", []), _FOOD_SAFETY_ERRORS)

    extra = []
    if not result.get("certificate_number"):
        extra.append("CERT_NUMBER_NOT_READABLE")
    if not result.get("expiry_date"):
        extra.append("EXPIRY_DATE_NOT_READABLE")
    extra_errors = _build_errors(extra, _FOOD_SAFETY_ERRORS)

    all_errors = gemini_errors + [e for e in extra_errors if e not in gemini_errors]
    if all_errors:
        return {"extracted": None, "errors": all_errors}

    return {
        "extracted": {
            "owner_name": result.get("owner_name"),
            "facility_name": result.get("facility_name"),
            "certificate_number": result.get("certificate_number"),
            "address": result.get("address"),
            "issue_date": result.get("issue_date"),
            "expiry_date": result.get("expiry_date"),
            "has_signature": result.get("has_signature", False),
            "has_red_stamp": result.get("has_red_stamp", False),
        },
        "errors": [],
    }


def analyze_selfie(public_url: str, expected_code: str) -> dict:
    """
    Returns the full Gemini result dict including face_detected, verification_code_read, errors.
    Code matching is verified by the caller (verification.py), not here.
    """
    images = _download_all([public_url])
    result = _call_gemini(images, _selfie_prompt(expected_code))
    errors = _build_errors(result.get("document_errors", []), _SELFIE_ERRORS)
    return {
        "face_detected": result.get("face_detected", False),
        "has_id_card": result.get("has_id_card", False),
        "has_verification_code": result.get("has_verification_code", False),
        "verification_code_read": result.get("verification_code_read"),
        "errors": errors,
    }


def verify_same_address(address_a: str, address_b: str) -> bool:
    """
    Dùng Gemini để phân tích ngữ nghĩa xem 2 địa chỉ có cùng một nơi không.
    Xử lý các trường hợp word-overlap không handle được:
      - Địa chỉ đầy đủ vs viết tắt
      - Mô tả khác nhau cho cùng địa điểm (nhà riêng / địa điểm sản xuất)

    Trả về True nếu Gemini cho là cùng địa chỉ, False nếu khác.
    Trả về True khi không chắc (tránh false positive → đẩy về PENDING_REVIEW qua risk score).
    """
    prompt = f"""So sánh 2 địa chỉ sau đây và xác định chúng có cùng một địa điểm thực tế không.

Địa chỉ A: {address_a}
Địa chỉ B: {address_b}

Trả về JSON:
{{"same_location": true/false, "confidence": "high"/"medium"/"low", "reason": "<giải thích ngắn>"}}

Các trường hợp cần coi là CÙNG địa chỉ:
- Một địa chỉ đầy đủ hơn địa chỉ kia (VD: "123 Nguyễn Huệ" và "123 Nguyễn Huệ, P. Bến Nghé, Q.1")
- Mô tả khác nhau cho cùng nơi (VD: "Nhà riêng" và "Địa điểm sản xuất tại nhà")
- Cách viết khác nhau (VD: "Quận 1" và "Q.1")

Chỉ trả về false khi rõ ràng là 2 địa điểm khác nhau (số nhà khác, đường khác, quận/tỉnh khác)."""

    try:
        # Không cần ảnh — gọi Gemini text-only
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=types.Content(
                parts=[types.Part(text=prompt)],
                role="user",
            ),
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        result = json.loads(response.text)
        same = result.get("same_location", True)
        confidence = result.get("confidence", "low")
        logger.info(
            "Address comparison: same=%s confidence=%s | '%s' vs '%s'",
            same, confidence, address_a[:50], address_b[:50],
        )
        # Nếu không chắc (low confidence) → coi là khớp để tránh false positive
        if confidence == "low":
            return True
        return bool(same)
    except Exception as exc:
        logger.warning("Address Gemini comparison failed, defaulting to match: %s", exc)
        return True  # Fail-safe: không phạt nếu không gọi được Gemini
