from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ContentType = Literal["note", "post"]


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthMeResponse(BaseModel):
    user: str


class ContentItemSummary(BaseModel):
    id: str
    type: ContentType
    path: str
    slug: str
    title: str
    date: str | None = None
    draft: bool | None = None
    updated_at: str


class ContentListResponse(BaseModel):
    items: list[ContentItemSummary]
    page: int
    page_size: int
    total: int


class ContentDocument(BaseModel):
    id: str
    type: ContentType
    path: str
    frontmatter: dict[str, Any]
    body: str
    raw: str


class ContentCreateRequest(BaseModel):
    type: ContentType
    title: str
    link: str | None = None
    comment: str | None = None
    body: str | None = None
    categories: list[str] = Field(default_factory=list)
    date: str | None = None
    draft: bool = True


class ContentUpdateRequest(BaseModel):
    title: str | None = None
    link: str | None = None
    comment: str | None = None
    body: str | None = None
    categories: list[str] | None = None
    date: str | None = None
    draft: bool | None = None


class GitStatusItem(BaseModel):
    status: str
    path: str


class GitStatusResponse(BaseModel):
    changed: bool
    files: list[GitStatusItem]


class PublishRequest(BaseModel):
    message: str | None = None


class PublishResponse(BaseModel):
    commit_hash: str
    message: str
    files: list[GitStatusItem]
    output: str
