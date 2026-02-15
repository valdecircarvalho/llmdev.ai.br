from __future__ import annotations

import os
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        self.blog_root = Path(os.getenv("CMS_BLOG_ROOT", "/workspace/blog")).resolve()
        self.db_path = Path(os.getenv("CMS_DB_PATH", "/data/app.db"))
        self.admin_user = os.getenv("CMS_ADMIN_USER", "admin")
        self.admin_password_hash = os.getenv("CMS_ADMIN_PASSWORD_HASH", "")
        self.jwt_secret = os.getenv("CMS_JWT_SECRET", "change-me")
        self.jwt_expire_hours = int(os.getenv("CMS_JWT_EXPIRE_HOURS", "8"))
        self.allowed_origin = os.getenv("CMS_ALLOWED_ORIGIN", "http://localhost:8080")
        self.git_branch = os.getenv("CMS_GIT_BRANCH", "main")
        self.git_remote = os.getenv("CMS_GIT_REMOTE", "origin")
        self.git_remote_url = os.getenv("CMS_GIT_REMOTE_URL", "")
        self.git_token = os.getenv("CMS_GIT_TOKEN", "")
        self.secure_cookie = os.getenv("CMS_SECURE_COOKIE", "true").lower() == "true"

    @property
    def notes_dir(self) -> Path:
        return self.blog_root / "content" / "notes"

    @property
    def posts_dir(self) -> Path:
        return self.blog_root / "content" / "posts"


settings = Settings()
