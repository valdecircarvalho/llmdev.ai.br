from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Cookie, Depends, Header, HTTPException, status

from .database import get_connection
from .security import decode_access_token, hash_token


@dataclass
class AuthSession:
    user: str
    token_hash: str


def _extract_bearer_token(auth_header: str | None) -> str | None:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def get_current_session(
    authorization: str | None = Header(default=None),
    cms_token: str | None = Cookie(default=None),
) -> AuthSession:
    token = _extract_bearer_token(authorization) or cms_token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

    try:
        payload = decode_access_token(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc

    token_hash = hash_token(token)
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, expires_at, revoked_at
            FROM sessions
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found")

    if row["revoked_at"] is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    return AuthSession(user=subject, token_hash=token_hash)


def get_db_connection() -> sqlite3.Connection:
    with get_connection() as conn:
        yield conn


def require_auth(session: AuthSession = Depends(get_current_session)) -> AuthSession:
    return session
