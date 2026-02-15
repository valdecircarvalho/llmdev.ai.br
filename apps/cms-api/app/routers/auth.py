from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from ..config import settings
from ..database import get_connection
from ..dependencies import AuthSession, require_auth
from ..schemas import AuthMeResponse, LoginRequest, TokenResponse
from ..security import create_access_token, hash_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

LOGIN_WINDOW_SECONDS = 10 * 60
LOGIN_MAX_ATTEMPTS = 5
LOGIN_ATTEMPTS: dict[str, list[float]] = {}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _register_audit(action: str, target_path: str | None, details: dict[str, str], user: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs (ts, user, action, target_path, details_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                _now_utc().isoformat(),
                user,
                action,
                target_path,
                json.dumps(details),
            ),
        )


def _allow_login(ip: str) -> bool:
    now_ts = _now_utc().timestamp()
    previous = LOGIN_ATTEMPTS.get(ip, [])
    valid_attempts = [value for value in previous if now_ts - value <= LOGIN_WINDOW_SECONDS]
    LOGIN_ATTEMPTS[ip] = valid_attempts
    return len(valid_attempts) < LOGIN_MAX_ATTEMPTS


def _register_failed_login(ip: str) -> None:
    LOGIN_ATTEMPTS.setdefault(ip, []).append(_now_utc().timestamp())


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, response: Response) -> TokenResponse:
    if not settings.admin_password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CMS_ADMIN_PASSWORD_HASH is not configured",
        )

    ip = request.client.host if request.client else "unknown"
    if not _allow_login(ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts")

    try:
        is_valid = verify_password(payload.password, settings.admin_password_hash)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if not is_valid:
        _register_failed_login(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, expires_at = create_access_token(settings.admin_user)
    token_hash = hash_token(token)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (id, created_at, expires_at, revoked_at, token_hash)
            VALUES (?, ?, ?, NULL, ?)
            """,
            (str(uuid.uuid4()), _now_utc().isoformat(), expires_at.isoformat(), token_hash),
        )

    response.set_cookie(
        key="cms_token",
        value=token,
        httponly=True,
        secure=settings.secure_cookie,
        samesite="lax",
        max_age=int(timedelta(hours=settings.jwt_expire_hours).total_seconds()),
        path="/",
    )

    _register_audit("auth.login", None, {"ip": ip}, settings.admin_user)
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(response: Response, session: AuthSession = Depends(require_auth)) -> dict[str, str]:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET revoked_at = ?
            WHERE token_hash = ?
            """,
            (_now_utc().isoformat(), session.token_hash),
        )

    response.delete_cookie("cms_token", path="/")
    _register_audit("auth.logout", None, {}, session.user)
    return {"status": "ok"}


@router.get("/me", response_model=AuthMeResponse)
def me(session: AuthSession = Depends(require_auth)) -> AuthMeResponse:
    return AuthMeResponse(user=session.user)
