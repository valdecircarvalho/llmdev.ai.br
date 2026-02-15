from __future__ import annotations

import re
import threading
import unicodedata
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import HTTPException, status

from ..config import settings

CONTENT_LOCK = threading.Lock()
STANDARD_FIELDS = ["title", "date", "categories", "draft"]


def _slugify(value: str) -> str:
    ascii_text = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug or "untitled"


def _split_front_matter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---\n"):
        return {}, raw

    lines = raw.splitlines()
    closing_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            closing_idx = idx
            break

    if closing_idx is None:
        return {}, raw

    yaml_text = "\n".join(lines[1:closing_idx]).strip()
    body = "\n".join(lines[closing_idx + 1 :])
    parsed = yaml.safe_load(yaml_text) if yaml_text else {}
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid YAML front matter",
        )
    return parsed, body


def _ordered_front_matter(frontmatter: dict[str, Any]) -> OrderedDict[str, Any]:
    ordered: OrderedDict[str, Any] = OrderedDict()
    for field in STANDARD_FIELDS:
        if field in frontmatter:
            ordered[field] = frontmatter[field]
    for key, value in frontmatter.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _serialize(frontmatter: dict[str, Any], body: str) -> str:
    ordered = _ordered_front_matter(frontmatter)
    yaml_text = yaml.safe_dump(dict(ordered), sort_keys=False, allow_unicode=True).strip()
    clean_body = body.rstrip()
    if clean_body:
        return f"---\n{yaml_text}\n---\n\n{clean_body}\n"
    return f"---\n{yaml_text}\n---\n"


def _content_dir(content_type: str) -> Path:
    if content_type == "note":
        return settings.notes_dir
    if content_type == "post":
        return settings.posts_dir
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content type")


def _safe_resolve(item_id: str) -> tuple[str, Path]:
    item_path = Path(item_id)
    if item_path.is_absolute() or ".." in item_path.parts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content id")

    parts = item_path.as_posix().split("/", 1)
    if len(parts) != 2 or parts[0] not in {"note", "post"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content id")

    content_type, relative_part = parts
    root = _content_dir(content_type)
    file_path = (root / relative_part).resolve()
    if not str(file_path).startswith(str(root.resolve())):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content path")
    if file_path.suffix != ".md":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only markdown files are supported")

    return content_type, file_path


def _compose_body(comment: str | None, link: str | None) -> str:
    chunks: list[str] = []
    if comment and comment.strip():
        chunks.append(comment.strip())
    if link and link.strip():
        clean_link = link.strip()
        chunks.append(f"[{clean_link}]({clean_link})")
    return "\n\n".join(chunks)


def _to_item_id(content_type: str, root: Path, file_path: Path) -> str:
    relative = file_path.resolve().relative_to(root.resolve()).as_posix()
    return f"{content_type}/{relative}"


def get_content(item_id: str) -> dict[str, Any]:
    content_type, file_path = _safe_resolve(item_id)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    raw = file_path.read_text(encoding="utf-8")
    frontmatter, body = _split_front_matter(raw)

    return {
        "id": item_id,
        "type": content_type,
        "path": str(file_path),
        "frontmatter": frontmatter,
        "body": body,
        "raw": raw,
    }


def list_content(content_type: str | None, query: str, page: int, page_size: int) -> dict[str, Any]:
    candidates: list[tuple[str, Path, Path]] = []

    if content_type in {None, "note"}:
        candidates.append(("note", settings.notes_dir, settings.notes_dir))
    if content_type in {None, "post"}:
        candidates.append(("post", settings.posts_dir, settings.posts_dir))

    items: list[dict[str, Any]] = []
    query_lower = query.lower().strip()

    for kind, root, _ in candidates:
        if not root.exists():
            continue
        for file_path in sorted(root.rglob("*.md")):
            if file_path.name == "_index.md":
                continue
            raw = file_path.read_text(encoding="utf-8")
            frontmatter, _ = _split_front_matter(raw)
            title = str(frontmatter.get("title", file_path.stem))
            if query_lower and query_lower not in title.lower() and query_lower not in file_path.stem.lower():
                continue
            stat = file_path.stat()
            items.append(
                {
                    "id": _to_item_id(kind, root, file_path),
                    "type": kind,
                    "path": str(file_path),
                    "slug": file_path.stem,
                    "title": title,
                    "date": frontmatter.get("date"),
                    "draft": frontmatter.get("draft"),
                    "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )

    items.sort(key=lambda value: value["updated_at"], reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paged = items[start:end]

    return {
        "items": paged,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


def create_content(payload: dict[str, Any]) -> dict[str, Any]:
    content_type = payload["type"]
    target_dir = _content_dir(content_type)
    target_dir.mkdir(parents=True, exist_ok=True)

    title = payload["title"].strip()
    base_slug = _slugify(title)
    slug = base_slug
    suffix = 2

    while (target_dir / f"{slug}.md").exists():
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    file_path = target_dir / f"{slug}.md"
    categories = payload.get("categories") or []
    date_value = payload.get("date") or datetime.now(timezone.utc).date().isoformat()
    draft = bool(payload.get("draft", True))

    body = payload.get("body")
    if body is None:
        body = _compose_body(payload.get("comment"), payload.get("link"))

    frontmatter: dict[str, Any] = {
        "title": title,
        "date": date_value,
        "categories": categories,
        "draft": draft,
    }

    with CONTENT_LOCK:
        file_path.write_text(_serialize(frontmatter, body or ""), encoding="utf-8")

    item_id = _to_item_id(content_type, target_dir, file_path)
    return get_content(item_id)


def update_content(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    content_type, file_path = _safe_resolve(item_id)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    raw = file_path.read_text(encoding="utf-8")
    frontmatter, body = _split_front_matter(raw)

    if payload.get("title") is not None:
        frontmatter["title"] = payload["title"].strip()
    if payload.get("date") is not None:
        frontmatter["date"] = payload["date"]
    if payload.get("categories") is not None:
        frontmatter["categories"] = payload["categories"]
    if payload.get("draft") is not None:
        frontmatter["draft"] = payload["draft"]

    if payload.get("body") is not None:
        body = payload["body"]
    elif payload.get("comment") is not None or payload.get("link") is not None:
        body = _compose_body(payload.get("comment"), payload.get("link"))

    with CONTENT_LOCK:
        file_path.write_text(_serialize(frontmatter, body), encoding="utf-8")

    target_dir = _content_dir(content_type)
    return get_content(_to_item_id(content_type, target_dir, file_path))


def delete_content(item_id: str) -> None:
    _, file_path = _safe_resolve(item_id)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    with CONTENT_LOCK:
        file_path.unlink()
