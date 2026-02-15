from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..database import get_connection
from ..dependencies import AuthSession, require_auth
from ..schemas import (
    ContentCreateRequest,
    ContentDocument,
    ContentListResponse,
    ContentType,
    ContentUpdateRequest,
)
from ..services.markdown import create_content, delete_content, get_content, list_content, update_content

router = APIRouter(prefix="/content", tags=["content"])


def _register_audit(user: str, action: str, target_path: str | None, details: dict[str, str] | None = None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs (ts, user, action, target_path, details_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                user,
                action,
                target_path,
                json.dumps(details or {}),
            ),
        )


@router.get("", response_model=ContentListResponse)
def get_content_list(
    session: AuthSession = Depends(require_auth),
    type: ContentType | None = Query(default=None),
    query: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ContentListResponse:
    _ = session
    result = list_content(type, query, page, page_size)
    return ContentListResponse(**result)


@router.get("/{item_id:path}", response_model=ContentDocument)
def get_content_by_id(item_id: str, session: AuthSession = Depends(require_auth)) -> ContentDocument:
    _ = session
    document = get_content(item_id)
    return ContentDocument(**document)


@router.post("", response_model=ContentDocument, status_code=status.HTTP_201_CREATED)
def create_content_endpoint(payload: ContentCreateRequest, session: AuthSession = Depends(require_auth)) -> ContentDocument:
    if not payload.title.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Title is required")

    created = create_content(payload.model_dump())
    _register_audit(session.user, "content.create", created["path"], {"id": created["id"], "type": created["type"]})
    return ContentDocument(**created)


@router.put("/{item_id:path}", response_model=ContentDocument)
def update_content_endpoint(
    item_id: str,
    payload: ContentUpdateRequest,
    session: AuthSession = Depends(require_auth),
) -> ContentDocument:
    updated = update_content(item_id, payload.model_dump())
    _register_audit(session.user, "content.update", updated["path"], {"id": updated["id"]})
    return ContentDocument(**updated)


@router.delete("/{item_id:path}")
def delete_content_endpoint(item_id: str, session: AuthSession = Depends(require_auth)) -> dict[str, str]:
    current = get_content(item_id)
    delete_content(item_id)
    _register_audit(session.user, "content.delete", current["path"], {"id": current["id"]})
    return {"status": "deleted"}
