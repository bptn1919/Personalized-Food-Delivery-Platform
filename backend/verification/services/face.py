"""
InsightFaceService — So sánh khuôn mặt giữa ảnh chân dung trên CCCD và ảnh selfie.

Thresholds (từ spec):
  >= 0.80  → PASS
  0.65–0.80 → REVIEW
  < 0.65   → FACE_MATCH_FAILED

InsightFace model 'buffalo_l' được download tự động lần đầu (~300 MB).
Dùng lazy singleton để tránh load model mỗi request.
"""

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger("django")

_face_app = None


def _get_app():
    global _face_app
    if _face_app is None:
        try:
            from insightface.app import FaceAnalysis
        except ImportError:
            logger.error(
                "insightface chưa được cài. Chạy: pip install insightface onnxruntime opencv-python"
            )
            raise
        _face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("InsightFace model 'buffalo_l' loaded.")
    return _face_app


def _largest_face_embedding(image_bytes: bytes, label: str = "") -> Optional[np.ndarray]:
    """Detect faces in image and return the embedding of the largest face."""
    import cv2

    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        logger.warning("[%s] cv2.imdecode returned None — invalid image bytes.", label)
        return None

    # Fix EXIF rotation — điện thoại chụp thường có metadata xoay ảnh
    # cv2 không đọc EXIF nên ảnh bị ngược/nằm ngang → InsightFace không nhận mặt
    try:
        from PIL import Image, ExifTags
        import io
        pil_img = Image.open(io.BytesIO(image_bytes))
        exif = pil_img._getexif()
        if exif:
            for tag, val in exif.items():
                if ExifTags.TAGS.get(tag) == "Orientation":
                    if val == 3:
                        img = cv2.rotate(img, cv2.ROTATE_180)
                    elif val == 6:
                        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    elif val == 8:
                        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                    break
    except Exception:
        pass  # Nếu không có EXIF thì bỏ qua

    h, w = img.shape[:2]
    logger.info("[%s] Image loaded: %dx%d", label, w, h)

    faces = _get_app().get(img)
    logger.info("[%s] InsightFace detected %d face(s).", label, len(faces) if faces else 0)

    if not faces:
        return None

    largest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    return largest.embedding


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compare_faces(cccd_image_bytes: bytes, selfie_image_bytes: bytes) -> Optional[float]:
    """
    Returns cosine similarity in [0.0, 1.0], or None if any face could not be detected.
    """
    try:
        emb_cccd   = _largest_face_embedding(cccd_image_bytes,   label="CCCD")
        emb_selfie = _largest_face_embedding(selfie_image_bytes, label="SELFIE")

        if emb_cccd is None:
            logger.warning("CCCD: không phát hiện khuôn mặt.")
            return None
        if emb_selfie is None:
            logger.warning("SELFIE: không phát hiện khuôn mặt.")
            return None

        score = _cosine_similarity(emb_cccd, emb_selfie)
        logger.info("Face similarity score: %.4f", score)
        return round(max(0.0, min(1.0, score)), 4)

    except Exception as exc:
        logger.error("InsightFace error: %s", exc, exc_info=True)
        return None
