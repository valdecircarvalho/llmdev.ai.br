#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./deploy.sh [options]

Options:
  -m, --message <msg>  Commit message (default: "chore(content): publish update")
      --no-build       Skip Hugo build validation
      --dry-run        Print actions without executing them
  -h, --help           Show this help
EOF
}

log() {
  printf '[deploy] %s\n' "$*"
}

run() {
  if [[ "$DRY_RUN" == "true" ]]; then
    printf '[dry-run] %s\n' "$*"
  else
    eval "$@"
  fi
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Error: required command not found: %s\n' "$1" >&2
    exit 1
  }
}

COMMIT_MESSAGE="chore(content): publish update"
RUN_BUILD="true"
DRY_RUN="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--message)
      [[ $# -lt 2 ]] && { echo "Error: missing value for $1" >&2; exit 1; }
      COMMIT_MESSAGE="$2"
      shift 2
      ;;
    --no-build)
      RUN_BUILD="false"
      shift
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

require_cmd git
require_cmd hugo

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "Error: run this script from inside a git repository." >&2
  exit 1
}

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [[ "$RUN_BUILD" == "true" ]]; then
  log "Running Hugo build validation..."
  run "hugo -s . --config ./hugo.toml --gc --minify"
fi

log "Staging changes..."
run "git add -A"

if git diff --cached --quiet; then
  log "No staged changes detected. Nothing to deploy."
  exit 0
fi

log "Creating commit..."
run "git commit -m \"$COMMIT_MESSAGE\""

if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  log "Pushing to upstream branch..."
  run "git push"
else
  log "Pushing and setting upstream to origin/$CURRENT_BRANCH..."
  run "git push -u origin \"$CURRENT_BRANCH\""
fi

log "Done. Changes pushed from branch '$CURRENT_BRANCH'."
