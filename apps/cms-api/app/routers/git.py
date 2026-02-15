from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ..database import get_connection
from ..dependencies import AuthSession, require_auth
from ..schemas import GitStatusItem, GitStatusResponse, PublishRequest, PublishResponse
from ..services.git_ops import get_status, publish

router = APIRouter(prefix="/git", tags=["git"])


def _register_audit(user: str, action: str, details: dict[str, str]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs (ts, user, action, target_path, details_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (datetime.now(timezone.utc).isoformat(), user, action, None, json.dumps(details)),
        )


def _register_publish_run(status_value: str, commit_hash: str | None, output: str | None, error: str | None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO publish_runs (ts, status, commit_hash, output, error)
            VALUES (?, ?, ?, ?, ?)
            """,
            (datetime.now(timezone.utc).isoformat(), status_value, commit_hash, output, error),
        )


@router.get("/status", response_model=GitStatusResponse)
def git_status(session: AuthSession = Depends(require_auth)) -> GitStatusResponse:
    _ = session
    files = [GitStatusItem(**item) for item in get_status()]
    return GitStatusResponse(changed=bool(files), files=files)


@router.post("/publish", response_model=PublishResponse)
def git_publish(payload: PublishRequest, session: AuthSession = Depends(require_auth)) -> PublishResponse:
    files = [GitStatusItem(**item) for item in get_status()]
    try:
        result = publish(payload.message)
    except HTTPException as exc:
        _register_publish_run("error", None, None, str(exc.detail))
        raise

    _register_publish_run("success", result["commit_hash"], result["output"], None)
    _register_audit(
        session.user,
        "git.publish",
        {
            "commit_hash": result["commit_hash"],
            "file_count": str(len(files)),
        },
    )

    return PublishResponse(
        commit_hash=result["commit_hash"],
        message=result["message"],
        files=files,
        output=result["output"],
    )
