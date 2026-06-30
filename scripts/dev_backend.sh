#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"
ENV_FILE="$BACKEND_DIR/.env"

usage() {
  cat <<'USAGE'
Usage:
  scripts/dev_backend.sh setup   Create/update local backend venv and .env
  scripts/dev_backend.sh run     Run FastAPI locally on 127.0.0.1:8000
  scripts/dev_backend.sh smoke   Run API smoke test against local backend

The local backend uses SQLite by default and never needs production secrets.
USAGE
}

ensure_venv() {
  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    python3 -m venv "$VENV_DIR"
  fi
  "$VENV_DIR/bin/python" -m pip install -U pip >/dev/null
  "$VENV_DIR/bin/python" -m pip install -e "$BACKEND_DIR[dev]"
}

ensure_env() {
  if [[ -f "$ENV_FILE" ]]; then
    return
  fi
  cat >"$ENV_FILE" <<'ENV'
BIBLEMAXXING_ENV=development
BIBLEMAXXING_DATABASE_URL=sqlite:///./biblemaxxing-dev.db
BIBLEMAXXING_SECRET_KEY=dev-local-change-me
BIBLEMAXXING_ACCESS_TOKEN_MINUTES=43200
BIBLEMAXXING_YOUTUBE_API_KEY=
BIBLEMAXXING_AUTO_CREATE_TABLES=true
BIBLEMAXXING_CORS_ORIGINS=*
ENV
  echo "Created $ENV_FILE"
}

case "${1:-}" in
  setup)
    ensure_venv
    ensure_env
    echo "Local backend is ready."
    ;;
  run)
    ensure_venv
    ensure_env
    cd "$BACKEND_DIR"
    exec "$VENV_DIR/bin/uvicorn" app.main:app --reload --host 127.0.0.1 --port 8000
    ;;
  smoke)
    BASE_URL="${BASE_URL:-http://127.0.0.1:8000}" "$ROOT_DIR/scripts/smoke_api.sh"
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
