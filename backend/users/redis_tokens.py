"""
Hybrid refresh-token store: Redis (primary) + PostgreSQL (fallback).

Tại sao hybrid?
  - Redis: lookup O(1), TTL tự xóa  → fast path (99% requests)
  - DB:    persistent, survives Redis restart → fallback khi Redis down/restart

Cách hoạt động:
  store()  → ghi cả Redis lẫn DB
  load()   → đọc Redis trước; nếu miss thì đọc DB rồi tự restore Redis
  delete() → xóa Redis + đánh revoked_at trong DB (audit trail giữ lại)

Key layout (Redis DB 1):
  rt:token:{HMAC-SHA256}  →  JSON {"user_id": int, "jti": str}   TTL = lifetime
  rt:user:{user_id}       →  SET  of token_hashes (dùng cho revoke-all)
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta

import redis
from django.conf import settings
from django.utils.timezone import now

logger = logging.getLogger("django")

_client: redis.Redis | None = None
_RT_PREFIX = "rt:token"
_USER_IDX  = "rt:user"


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        url = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/1")
        _client = redis.Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _client


# ── helpers ───────────────────────────────────────────────────────────────────

def _redis_key(token_hash: str) -> str:
    return f"{_RT_PREFIX}:{token_hash}"

def _user_key(user_id: int) -> str:
    return f"{_USER_IDX}:{user_id}"

def _to_payload(user_id: int, jti: str) -> str:
    return json.dumps({"user_id": user_id, "jti": jti})

def _from_payload(raw: str) -> dict:
    return json.loads(raw)


# ── public API ────────────────────────────────────────────────────────────────

def store(*, token_hash: str, user_id: int, jti: str, ttl_seconds: int) -> None:
    """
    Lưu refresh token vào Redis VÀ DB.
    Nếu DB ghi lỗi → log warning, không raise (Redis vẫn là primary).
    """
    payload = _to_payload(user_id, jti)

    # ── 1. Redis (primary) ────────────────────────────────────────────────────
    try:
        r = _get_client()
        r.setex(_redis_key(token_hash), ttl_seconds, payload)
        r.sadd(_user_key(user_id), token_hash)
    except redis.RedisError as exc:
        logger.error("Redis store failed: %s", exc)
        raise   # Redis write failure IS fatal — can't issue token without primary store

    # ── 2. DB (backup) ────────────────────────────────────────────────────────
    try:
        from users.models import AuthenticateToken
        import uuid as _uuid
        AuthenticateToken.objects.create(
            user_id=user_id,
            token_hash=token_hash,
            jti=_uuid.UUID(jti),
            expires_at=now() + timedelta(seconds=ttl_seconds),
        )
    except Exception as exc:
        # DB backup failure is non-fatal — Redis already has the token.
        logger.warning("DB backup for refresh token failed (non-fatal): %s", exc)


def load(token_hash: str) -> dict | None:
    """
    Trả về {"user_id": int, "jti": str} nếu token hợp lệ, None nếu không.

    Fast path:   Redis hit  → trả về ngay
    Fallback:    Redis miss → check DB → nếu valid thì restore Redis rồi trả về
    """
    # ── 1. Redis (fast path) ──────────────────────────────────────────────────
    try:
        raw = _get_client().get(_redis_key(token_hash))
        if raw is not None:
            return _from_payload(raw)
    except redis.RedisError as exc:
        logger.warning("Redis load failed, falling back to DB: %s", exc)

    # ── 2. DB fallback ────────────────────────────────────────────────────────
    try:
        from users.models import AuthenticateToken
        record = AuthenticateToken.objects.get(token_hash=token_hash)
        if not record.is_valid:
            return None

        # Restore token to Redis so subsequent requests hit fast path again
        ttl = int((record.expires_at - now()).total_seconds())
        if ttl > 0:
            try:
                r = _get_client()
                payload = _to_payload(record.user_id, str(record.jti))
                r.setex(_redis_key(token_hash), ttl, payload)
                r.sadd(_user_key(record.user_id), token_hash)
                logger.info("Restored refresh token to Redis from DB (jti=%s)", record.jti)
            except redis.RedisError:
                pass  # Restore is best-effort

        return {"user_id": record.user_id, "jti": str(record.jti)}

    except Exception:
        return None


def delete(*, token_hash: str, user_id: int) -> None:
    """Revoke một token: xóa Redis + đánh dấu revoked trong DB."""
    # ── Redis ─────────────────────────────────────────────────────────────────
    try:
        r = _get_client()
        r.delete(_redis_key(token_hash))
        r.srem(_user_key(user_id), token_hash)
    except redis.RedisError as exc:
        logger.warning("Redis delete failed: %s", exc)

    # ── DB (set revoked_at, giữ record cho audit trail) ───────────────────────
    try:
        from users.models import AuthenticateToken
        AuthenticateToken.objects.filter(
            token_hash=token_hash, revoked_at__isnull=True
        ).update(revoked_at=now())
    except Exception as exc:
        logger.warning("DB revoke failed: %s", exc)


def delete_all_for_user(user_id: int) -> int:
    """Revoke tất cả token của 1 user (logout all devices / đổi password)."""
    count = 0

    # ── Redis ─────────────────────────────────────────────────────────────────
    try:
        r = _get_client()
        hashes: set[str] = r.smembers(_user_key(user_id))
        count = len(hashes)
        if hashes:
            r.delete(*[_redis_key(h) for h in hashes])
            r.delete(_user_key(user_id))
    except redis.RedisError as exc:
        logger.warning("Redis delete_all failed: %s", exc)

    # ── DB ────────────────────────────────────────────────────────────────────
    try:
        from users.models import AuthenticateToken
        db_count = AuthenticateToken.objects.filter(
            user_id=user_id, revoked_at__isnull=True
        ).update(revoked_at=now())
        count = max(count, db_count)
    except Exception as exc:
        logger.warning("DB revoke_all failed: %s", exc)

    return count
