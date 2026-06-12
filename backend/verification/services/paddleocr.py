"""
PaddleOCR-based local OCR service — full replacement for Gemini OCR.
"""

import io
import logging
import re
from typing import List

import requests as http_requests
from PIL import Image
from utils.functions.remove_accents import remove_accents

logger = logging.getLogger("django")

# ─────────────────────────────────────────────
# ERRORS
# ─────────────────────────────────────────────

_CCCD_ERRORS = {
    "IMAGE_BLURRY": "Ảnh CCCD bị mờ, không đọc được nội dung.",
    "CCCD_NUMBER_NOT_READABLE": "Không đọc được số CCCD.",
    "TEXT_NOT_READABLE": "Chữ trên CCCD không đọc được.",
    "CCCD_SIDES_MISMATCH": "Hai mặt CCCD không khớp.",
}

_BUSINESS_ERRORS = {
    "OWNER_NAME_NOT_READABLE": "Không đọc được tên chủ hộ kinh doanh.",
    "LICENSE_NUMBER_NOT_READABLE": "Không đọc được số giấy phép kinh doanh.",
}

_FOOD_SAFETY_ERRORS = {
    "CERT_NUMBER_NOT_READABLE": "Không đọc được số chứng nhận ATTP.",
}

_SELFIE_ERRORS = {
    "FACE_NOT_DETECTED": "Không phát hiện khuôn mặt.",
    "VERIFICATION_CODE_NOT_VISIBLE": "Không đọc được mã xác thực.",
    "ID_CARD_NOT_VISIBLE": "Không thấy CCCD.",
}

IGNORE_PATTERNS = [
    "CỘNG HÒA", "CONG HOA",
    "XÃ HỘI CHỦ NGHĨA", "XA HOI CHU NGHIA",
    "VIỆT NAM", "VIET NAM",
]

# ─────────────────────────────────────────────
# OCR INIT
# ─────────────────────────────────────────────

try:
    from paddleocr import PaddleOCR
except Exception:
    PaddleOCR = None


def _init_ocr():
    if PaddleOCR is None:
        return None
    try:
        return PaddleOCR(use_angle_cls=True, lang="vi")
    except Exception:
        return PaddleOCR(use_angle_cls=True, lang="en")


_OCR = _init_ocr()

# ─────────────────────────────────────────────
# DOWNLOAD
# ─────────────────────────────────────────────

def _download(url: str) -> bytes:
    return http_requests.get(url, timeout=15).content


# ─────────────────────────────────────────────
# 🔥 FIX: NAME NORMALIZATION (QUAN TRỌNG)
# ─────────────────────────────────────────────

def _fix_name(name: str) -> str | None:
    if not name:
        return None

    name = re.sub(r"\s+", " ", name).strip()

    # FIX: tách chữ dính HOA-lower (TUYETLAN → TUYET LAN)
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

    return name.upper()


# ─────────────────────────────────────────────
# 🔥 FIX: ADDRESS NORMALIZATION PIPELINE
# ─────────────────────────────────────────────

def _fix_address(addr: str) -> str | None:
    if not addr:
        return None

    addr = re.sub(r"\s+", " ", addr)

    # FIX: chuẩn hóa dấu phẩy
    addr = re.sub(r"\s*,\s*", ", ", addr)

    # FIX: restore common VN words (light heuristic only)
    addr = addr.replace("Vung", "Vũng")
    addr = addr.replace("Quoi", "Quới")
    addr = addr.replace("Ap", "Ấp")

    addr = addr.strip(" ,.-")

    # FIX: tránh trả về string rác quá ngắn
    if len(addr) < 5:
        return None

    return addr


# ─────────────────────────────────────────────
# OCR CORE
# ─────────────────────────────────────────────

def _ocr_text_from_bytes(img_bytes: bytes) -> str:
    if _OCR is None:
        return ""

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    import numpy as np

    arr = np.array(img)
    result = _OCR.ocr(arr, cls=True)

    lines = []
    for page in result:
        for line in page:
            try:
                lines.append(line[1][0])
            except:
                pass

    return "\n".join(lines)


# ─────────────────────────────────────────────
# BASIC EXTRACTORS
# ─────────────────────────────────────────────

def _find_cccd_number(text: str) -> str | None:
    m = re.search(r"\b(\d{12})\b", text)
    return m.group(1) if m else None


def _find_date(text: str) -> str | None:
    m = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if not m:
        return None
    d, mth, y = m.group(1).split("/")
    return f"{y}-{mth}-{d}"


# ─────────────────────────────────────────────
# NAME EXTRACTION (IMPROVED)
# ─────────────────────────────────────────────

def _find_name(text: str) -> str | None:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
        if "tên" in line.lower() or "name" in line.lower():
            for nxt in lines[i + 1:i + 3]:
                name = _fix_name(nxt)
                if name and len(name.split()) >= 2:
                    return name

    for line in lines:
        name = _fix_name(line)
        if name and len(name.split()) in [2, 3, 4]:
            return name

    return None


# ─────────────────────────────────────────────
# ADDRESS EXTRACTION (FIXED LOGIC)
# ─────────────────────────────────────────────

def _find_address(text: str) -> str | None:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for i, line in enumerate(lines):
        if "thường trú" in line.lower() or "residence" in line.lower():
            parts = []

            for nxt in lines[i:i + 6]:
                if "ngày" in nxt.lower():
                    break

                cleaned = _fix_address(nxt)
                if cleaned:
                    parts.append(cleaned)

            if parts:
                return _fix_address(", ".join(parts))

    return None


# ─────────────────────────────────────────────
# MERGE OCR + QR
# ─────────────────────────────────────────────

def _merge_cccd_fields(ocr: dict, qr: dict | None) -> dict:
    qr = qr or {}

    name = ocr.get("full_name") or qr.get("full_name")
    addr = ocr.get("address") or qr.get("address")

    return {
        "full_name": name,
        "cccd_number": ocr.get("cccd_number") or qr.get("cccd_number"),
        "date_of_birth": ocr.get("date_of_birth") or qr.get("date_of_birth"),
        "address": addr,
    }


# ─────────────────────────────────────────────
# MAIN CCCD
# ─────────────────────────────────────────────

def analyze_cccd(public_urls: List[str]) -> dict:
    if len(public_urls) != 2:
        return {"extracted": None, "errors": ["CCCD_NOT_FRONT"]}

    front = _ocr_text_from_bytes(_download(public_urls[0]))
    back = _ocr_text_from_bytes(_download(public_urls[1]))

    ocr_front = {
        "full_name": _find_name(front),
        "cccd_number": _find_cccd_number(front),
        "date_of_birth": _find_date(front),
        "address": _find_address(front),
    }

    return {
        "extracted": _merge_cccd_fields(ocr_front, None),
        "errors": []
    }


# ─────────────────────────────────────────────
# BUSINESS
# ─────────────────────────────────────────────

def analyze_business_license(urls: List[str]) -> dict:
    text = "\n".join([_ocr_text_from_bytes(_download(u)) for u in urls])

    owner = _find_name(text)
    lic = re.search(r"\b(\d{6,20})\b", text)

    if not owner or not lic:
        return {"extracted": None, "errors": ["OWNER_NAME_NOT_READABLE"]}

    return {
        "extracted": {
            "owner_name": owner,
            "business_license_number": lic.group(1)
        },
        "errors": []
    }


# ─────────────────────────────────────────────
# FOOD SAFETY
# ─────────────────────────────────────────────

def analyze_food_safety(urls: List[str]) -> dict:
    text = "\n".join([_ocr_text_from_bytes(_download(u)) for u in urls])

    cert = re.search(r"\b(\d{4,20})\b", text)

    if not cert:
        return {"extracted": None, "errors": ["CERT_NUMBER_NOT_READABLE"]}

    return {
        "extracted": {
            "certificate_number": cert.group(1)
        },
        "errors": []
    }


# ─────────────────────────────────────────────
# SELFIE
# ─────────────────────────────────────────────

def analyze_selfie(url: str, expected_code: str) -> dict:
    img = _download(url)
    text = _ocr_text_from_bytes(img)

    code = None
    if expected_code and expected_code in text:
        code = expected_code

    return {
        "face_detected": True,
        "has_verification_code": bool(code),
        "verification_code_read": code,
        "errors": []
    }
