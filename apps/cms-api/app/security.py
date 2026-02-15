from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from .config import settings

def verify_password(plain_password: str, password_hash: str) -> bool:
    encoded_password = plain_password.encode("utf-8")
    encoded_hash = password_hash.encode("utf-8")
    try:
        return bcrypt.checkpw(encoded_password, encoded_hash)
    except ValueError as exc:
        raise ValueError("CMS_ADMIN_PASSWORD_HASH must be a valid bcrypt hash") from exc


def create_access_token(subject: str) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.jwt_expire_hours)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
