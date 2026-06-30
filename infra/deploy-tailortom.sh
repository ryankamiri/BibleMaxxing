#!/usr/bin/env bash
set -euo pipefail

REMOTE_HOST="${REMOTE_HOST:-tailortom}"
REMOTE_APP_DIR="${REMOTE_APP_DIR:-/opt/biblemaxxing}"
REMOTE_TAILORTOM_DIR="${REMOTE_TAILORTOM_DIR:-/opt/tailortom}"

usage() {
  cat <<'USAGE'
Usage:
  infra/deploy-tailortom.sh preflight
  infra/deploy-tailortom.sh sync
  infra/deploy-tailortom.sh health

Environment:
  REMOTE_HOST=tailortom
  REMOTE_APP_DIR=/opt/biblemaxxing
  REMOTE_TAILORTOM_DIR=/opt/tailortom
  BIBLEMAXXING_CONFIRM_DEPLOY=1   required for sync

This helper does not edit the TailorTom Caddyfile automatically. It prepares
BibleMaxxing compose assets and prints the Caddy snippet path so the CTO agent
can patch and validate the live Caddy config deliberately.
USAGE
}

require_confirm() {
  if [[ "${BIBLEMAXXING_CONFIRM_DEPLOY:-}" != "1" ]]; then
    echo "Refusing to change remote state without BIBLEMAXXING_CONFIRM_DEPLOY=1." >&2
    exit 2
  fi
}

preflight() {
  ssh "$REMOTE_HOST" 'hostname'
  ssh "$REMOTE_HOST" 'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"'
  ssh "$REMOTE_HOST" 'ss -ltnp'
  ssh "$REMOTE_HOST" "sudo sed -n '1,220p' ${REMOTE_TAILORTOM_DIR}/Caddyfile"
  ssh "$REMOTE_HOST" "sudo sed -n '1,260p' ${REMOTE_TAILORTOM_DIR}/docker-compose.yml"
  ssh "$REMOTE_HOST" 'docker network ls'
}

sync_assets() {
  require_confirm
  ssh "$REMOTE_HOST" "sudo mkdir -p '$REMOTE_APP_DIR' && sudo chown \$USER:\$USER '$REMOTE_APP_DIR'"
  rsync -av --delete \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.ruff_cache' \
    --exclude '*.egg-info' \
    backend/ "$REMOTE_HOST:$REMOTE_APP_DIR/backend/"
  rsync -av infra/docker-compose.biblemaxxing.example.yml "$REMOTE_HOST:$REMOTE_APP_DIR/docker-compose.yml"
  rsync -av infra/biblemaxxing.env.example "$REMOTE_HOST:$REMOTE_APP_DIR/.env.example"
  rsync -av infra/Caddyfile.biblemaxxing.example "$REMOTE_HOST:$REMOTE_APP_DIR/Caddyfile.biblemaxxing.example"
  ssh "$REMOTE_HOST" "test -f '$REMOTE_APP_DIR/.env' || cp '$REMOTE_APP_DIR/.env.example' '$REMOTE_APP_DIR/.env'"
  ssh "$REMOTE_HOST" "sudo cp '${REMOTE_TAILORTOM_DIR}/Caddyfile' '${REMOTE_TAILORTOM_DIR}/Caddyfile.bak.$(date +%Y%m%d-%H%M%S)'"
  echo "Assets synced. Fill $REMOTE_APP_DIR/.env on $REMOTE_HOST, then run docker compose from that directory."
  echo "Add $REMOTE_APP_DIR/Caddyfile.biblemaxxing.example inside ${REMOTE_TAILORTOM_DIR}/Caddyfile before the TailorTom fallback route."
}

health() {
  ssh "$REMOTE_HOST" "curl -fsS http://127.0.0.1:\${BIBLEMAXXING_HOST_PORT:-8017}/biblemaxxing/health || true"
  curl -fsS https://api.tailortom.org/biblemaxxing/health
}

case "${1:-}" in
  preflight)
    preflight
    ;;
  sync)
    sync_assets
    ;;
  health)
    health
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
