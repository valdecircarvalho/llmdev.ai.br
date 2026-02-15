from __future__ import annotations

import os
import subprocess
import threading
from datetime import datetime, timezone

from fastapi import HTTPException, status

from ..config import settings

GIT_LOCK = threading.Lock()


def _run_git(args: list[str], check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        return subprocess.run(
            ["git", *args],
            cwd=settings.blog_root,
            capture_output=True,
            text=True,
            check=check,
            env=run_env,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Git is not installed in the API container",
        ) from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or "Git command failed").strip()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc


def _git_auth_env() -> tuple[dict[str, str], str]:
    remote_url = settings.git_remote_url.strip()
    token = settings.git_token.strip()
    if not remote_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CMS_GIT_REMOTE_URL must be configured for PAT publish",
        )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CMS_GIT_TOKEN must be configured for PAT publish",
        )

    askpass_path = "/app/app/scripts/git_askpass.sh"
    env = {
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": askpass_path,
        "GIT_USERNAME": "x-access-token",
        "CMS_GIT_TOKEN": token,
    }
    return env, remote_url


def get_status() -> list[dict[str, str]]:
    command = _run_git(["status", "--porcelain", "content"], check=True)
    lines = [line for line in command.stdout.splitlines() if line.strip()]
    files: list[dict[str, str]] = []
    for line in lines:
        state = line[:2].strip() or "??"
        path = line[3:].strip()
        files.append({"status": state, "path": path})
    return files


def publish(message: str | None) -> dict[str, str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    commit_message = message or f"content: publish updates {timestamp}"

    with GIT_LOCK:
        files = get_status()
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No changes in content/ to publish",
            )

        _run_git(["add", "content/"], check=True)

        commit_result = _run_git(["commit", "-m", commit_message], check=False)
        if commit_result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=commit_result.stderr.strip() or "Commit failed",
            )

        if settings.git_token or settings.git_remote_url:
            auth_env, remote_target = _git_auth_env()
            push_result = _run_git(["push", remote_target, settings.git_branch], check=False, env=auth_env)
        else:
            push_result = _run_git(["push", settings.git_remote, settings.git_branch], check=False)
        if push_result.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=push_result.stderr.strip() or "Push failed",
            )

        head_result = _run_git(["rev-parse", "HEAD"], check=True)

    output = "\n".join(
        value for value in [commit_result.stdout.strip(), push_result.stdout.strip(), push_result.stderr.strip()] if value
    )

    return {
        "commit_hash": head_result.stdout.strip(),
        "message": commit_message,
        "output": output,
    }
