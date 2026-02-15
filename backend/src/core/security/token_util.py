import hashlib
import secrets
import time
from typing import Any

import jwt
from jwt import InvalidTokenError

from src.core.config.settings import Settings
from src.core.utils.compat import generate_uuid


def _now() -> int:
    """Get current Unix timestamp."""
    return int(time.time())


def create_access_token(user_id: str, role: str, device_id: str | None = None) -> tuple[str, int]:
    secret = Settings.JWT_SECRET
    if not secret:
        raise RuntimeError("DEVICE_JWT_SECRET must be set")

    # Access tokens are short-lived (1 hour)
    ttl_minutes = Settings.ACCESS_TOKEN_TTL_MIN
    algo = Settings.JWT_ALGO

    iat = _now()
    exp = iat + (ttl_minutes * 60)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "device_id": device_id,
        "iat": iat,
        "exp": exp,
        "jti": generate_uuid(),
        "type": "access",
        "iss": "travel-planner",
    }
    token = jwt.encode(payload, secret, algorithm=algo)
    return token, exp


def decode_access_token(token: str) -> dict[str, Any] | None:
    if not token:
        return None

    secret = Settings.JWT_SECRET
    if not secret:
        return None
    algo = Settings.JWT_ALGO

    try:
        payload = jwt.decode(token, secret, algorithms=[algo], options={"require": ["sub", "exp", "iat", "type"]})

        if payload.get("type") != "access":
            return None

        return payload

    except jwt.ExpiredSignatureError:
        return None
    except InvalidTokenError as e:
        return None


def create_refresh_token(user_id: str, device_id: str, parent_token_hash: str | None = None) -> tuple[str, str, int]:

    secret = Settings.JWT_SECRET
    if not secret:
        raise RuntimeError("DEVICE_JWT_SECRET must be set")

    # Refresh tokens are long-lived (30 days)
    ttl_days = Settings.REFRESH_TOKEN_TTL_DAYS
    algo = Settings.JWT_ALGO

    iat = _now()
    exp = iat + (ttl_days * 86400)  # 86400 seconds = 1 day

    # Generate unique token ID for tracking
    token_id = secrets.token_hex(8)  # 16 char hex string for identification

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "device_id": device_id,
        "token_id": token_id,
        "iat": iat,
        "exp": exp,
        "type": "refresh",
        "iss": "travel-planner",
    }

    if parent_token_hash:
        payload["par"] = parent_token_hash[:16]

    token = jwt.encode(payload, secret, algorithm=algo)

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return token, token_hash, exp


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    if not token:
        return None

    secret = Settings.JWT_SECRET
    if not secret:
        return None
    algo = Settings.JWT_ALGO

    try:
        payload = jwt.decode(token, secret, algorithms=[algo], options={"require": ["sub", "exp", "iat", "type"]})
        # Verify token type
        if payload.get("type") != "refresh":
            return None
        return payload

    except jwt.ExpiredSignatureError:
        return None
    except InvalidTokenError as e:
        return None


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
