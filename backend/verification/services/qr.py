"""
QR Scanner cho mặt sau CCCD Việt Nam (căn cước công dân gắn chip, từ 2021).

Dữ liệu QR theo format pipe-delimited:
  {cccd_number}|{old_cmnd}|{full_name}|{dob_ddMMyyyy}|{gender}|{address}|{issue_date_ddMMyyyy}

Ưu tiên:
  1. OpenCV QRCodeDetector (đã có trong project, không cần dep mới)
  2. pyzbar fallback (cần libzbar0, tốt hơn cho ảnh nghiêng / độ phân giải thấp)
"""

import logging
from datetime import date

import numpy as np

logger = logging.getLogger("django")

_MIN_QR_FIELDS = 5


def scan_cccd_qr(image_bytes: bytes) -> dict | None:
    """
    Quét và parse QR code trên mặt sau CCCD.
    Returns: dict với các trường đã parse, hoặc None nếu không tìm thấy QR.
    """
    import cv2

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    raw_value = _try_opencv(img)
    if not raw_value:
        raw_value = _try_pyzbar(img)
    if not raw_value:
        return None

    try:
        return _parse_cccd_qr(raw_value)
    except Exception as exc:
        logger.warning("QR parse failed: %s | raw=%r", exc, raw_value[:100])
        return {"raw": raw_value}


# ── Decoders ──────────────────────────────────────────────────────────────────

def _try_opencv(img) -> str | None:
    import cv2
    try:
        detector = cv2.QRCodeDetector()
        value, _, _ = detector.detectAndDecode(img)
        return value.strip() if value else None
    except Exception:
        return None


def _try_pyzbar(img) -> str | None:
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
        results = pyzbar_decode(img)
        for r in results:
            if r.type == "QRCODE":
                return r.data.decode("utf-8", errors="replace").strip()
    except ImportError:
        pass
    except Exception as exc:
        logger.debug("pyzbar decode error: %s", exc)
    return None


# ── Parser ────────────────────────────────────────────────────────────────────

def _parse_cccd_qr(raw: str) -> dict:
    """
    Parse CCCD QR pipe-delimited data.
    Format: cccd_number|old_cmnd|full_name|dob_ddMMyyyy|gender|address|issue_date_ddMMyyyy
    """
    parts = [p.strip() for p in raw.split("|")]

    def get(idx: int) -> str | None:
        return parts[idx] if idx < len(parts) and parts[idx] else None

    dob = _parse_date_ddmmyyyy(get(3))

    return {
        "cccd_number": get(0),
        "old_cmnd": get(1),
        "full_name": get(2),
        "date_of_birth": dob.isoformat() if dob else None,
        "gender": get(4),
        "address": get(5),
        "raw": raw,
    }


def _parse_date_ddmmyyyy(value: str | None) -> date | None:
    if not value or len(value) != 8:
        return None
    try:
        return date(int(value[4:8]), int(value[2:4]), int(value[0:2]))
    except (ValueError, TypeError):
        return None
