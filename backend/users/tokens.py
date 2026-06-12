"""
Token utilities for access (JWT) and refresh (opaque, Redis-backed) tokens.

Access token  — short-lived JWT (default 15 min), stateless, verified via signature.
Refresh token — long-lived opaque random string (default 30 days).
               Only its HMAC-SHA256 hash is stored in Redis with a matching TTL.
               Raw token is sent to the client once and never persisted.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import timedelta

import jwt
from django.conf import settings
from django.utils.timezone import now

from exceptions.auth import InvalidOrExpiredToken
from . import redis_tokens as rt

# ── defaults (overridable via Django settings) ────────────────────────────────

DEFAULT_ACCESS_EXPIRES_MINUTES  = 15
DEFAULT_REFRESH_EXPIRES_MINUTES = 60 * 24 * 30   # 30 days
DEFAULT_JWT_ALGORITHM           = "HS256"


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_jwt_secret() -> str:
    return getattr(settings, "AUTH_JWT_SECRET", None) or settings.SECRET_KEY


def _get_refresh_pepper() -> str:
    return getattr(settings, "AUTH_REFRESH_TOKEN_PEPPER", None) or settings.SECRET_KEY


def _get_jwt_algorithm() -> str:
    return getattr(settings, "AUTH_JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM)


def _get_access_exp_minutes() -> int:
    return int(getattr(settings, "AUTH_ACCESS_TOKEN_EXPIRES_IN", DEFAULT_ACCESS_EXPIRES_MINUTES))


def _get_refresh_exp_minutes() -> int:
    return int(getattr(settings, "AUTH_REFRESH_TOKEN_EXPIRES_IN", DEFAULT_REFRESH_EXPIRES_MINUTES))


def hash_refresh_token(raw_token: str) -> str:
    """
    HMAC-SHA256(pepper, raw_token)  →  64-char hex string.
    This is what gets stored in Redis — the raw token is never persisted.
    """
    pepper = _get_refresh_pepper().encode()
    return hmac.new(pepper, raw_token.encode(), hashlib.sha256).hexdigest()


# ── access token (JWT) ────────────────────────────────────────────────────────

def issue_access_token(user_id: int, expires_at=None) -> str:
    """Sign and return a short-lived JWT access token."""
    issued_at = now()
    exp_time  = expires_at or (issued_at + timedelta(minutes=_get_access_exp_minutes()))
    payload   = {
        "user_id": user_id,
        "typ":     "access",
        "iat":     int(issued_at.timestamp()),
        "exp":     int(exp_time.timestamp()),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=_get_jwt_algorithm())


def decode_access_token(token: str) -> dict:
    """Verify JWT signature and expiry; raise jwt.InvalidTokenError on failure."""
    payload = jwt.decode(token, _get_jwt_secret(), algorithms=[_get_jwt_algorithm()])
    if payload.get("typ") != "access":
        raise jwt.InvalidTokenError("invalid_token_type")
    return payload


# ── refresh token (opaque, Redis-backed) ─────────────────────────────────────

def issue_refresh_token(user_id: int) -> tuple[str, str]:
    """
    Generate a cryptographically random refresh token and store its hash in Redis.

    Returns:
        (raw_token, jti)  — raw_token is sent to the client; jti is the UUID handle.

    Storage:
        Redis key  rt:token:{HMAC-SHA256}  →  {"user_id": X, "jti": "..."}
        TTL        set to configured refresh lifetime in seconds
    """
    raw_token  = secrets.token_urlsafe(64)
    token_hash = hash_refresh_token(raw_token)
    jti        = str(uuid.uuid4())
    ttl        = _get_refresh_exp_minutes() * 60

    rt.store(token_hash=token_hash, user_id=user_id, jti=jti, ttl_seconds=ttl)
    return raw_token, jti


def issue_token_pair(user_id: int) -> tuple[str, str]:
    """Convenience: issue both access and refresh tokens."""
    access_token    = issue_access_token(user_id=user_id)
    refresh_token, _ = issue_refresh_token(user_id=user_id)
    return access_token, refresh_token


def get_refresh_payload(raw_token: str) -> dict:
    """
    Validate a refresh token by looking up its hash in Redis.

    Returns:
        dict with keys  user_id, jti, token_hash   (token_hash added for caller convenience)

    Raises:
        InvalidOrExpiredToken — if the token is unknown, expired, or already revoked.
    """
    token_hash = hash_refresh_token(raw_token)
    payload    = rt.load(token_hash)
    if payload is None:
        raise InvalidOrExpiredToken
    return {**payload, "token_hash": token_hash}


def rotate_refresh_token(raw_token: str) -> tuple[str, int]:
    """
    Token rotation — the old token is deleted from Redis IMMEDIATELY after the new
    one is stored.  Any replay of the old raw_token will find no Redis entry and
    will be rejected.

    Returns:
        (new_raw_token, user_id)
    """
    payload  = get_refresh_payload(raw_token)
    user_id  = int(payload["user_id"])
    old_hash = payload["token_hash"]

    # Issue new token first — if this fails, the old token remains valid (safe).
    new_raw, _ = issue_refresh_token(user_id=user_id)

    # Invalidate old token — atomic delete from Redis.
    rt.delete(token_hash=old_hash, user_id=user_id)

    return new_raw, user_id


def revoke_refresh_token(raw_token: str) -> None:
    """Immediately delete a single refresh token from Redis (logout)."""
    token_hash = hash_refresh_token(raw_token)
    payload    = rt.load(token_hash)
    if payload is not None:
        rt.delete(token_hash=token_hash, user_id=int(payload["user_id"]))


def revoke_all_refresh_tokens(user_id: int) -> int:
    """
    Delete every active refresh token for a user from Redis.
    Used on password change or 'logout from all devices'.
    Returns count of tokens deleted.
    """
    return rt.delete_all_for_user(user_id=user_id)
