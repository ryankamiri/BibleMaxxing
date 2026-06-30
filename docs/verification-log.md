# BibleMaxxing Verification Log

Reviewed: 2026-06-30

## Local Verification

- Backend format/lint/tests:
  `cd backend && source .venv/bin/activate && ruff format . && ruff check . && pytest -q`
  passed with 3 tests.
- Alembic clean-database migration:
  `BIBLEMAXXING_DATABASE_URL=sqlite:////tmp/biblemaxxing-alembic-test.db alembic upgrade head`
  passed.
- iOS build:
  `xcodebuild -project ios/BibleMaxxing.xcodeproj -scheme BibleMaxxing -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build`
  passed.
- Local HTTP smoke:
  `BASE_URL=http://127.0.0.1:8765 ./scripts/smoke_api.sh`
  passed against a live `uvicorn` process.
- Compose config:
  `docker compose --env-file infra/biblemaxxing.env.example -f infra/docker-compose.biblemaxxing.example.yml config`
  passed with `TAILORTOM_CADDY_NETWORK=tailortom_tailortom`.

## VPS Deployment

- TailorTom preflight inspected Docker containers, ports, Caddyfile, compose
  config, and networks.
- Observed shared Caddy network: `tailortom_tailortom`.
- BibleMaxxing deployed under `/opt/biblemaxxing` with its own compose project,
  Postgres volume, and FastAPI container.
- Caddyfile was backed up before editing and reloaded after
  `docker exec tailortom-caddy caddy validate --config /etc/caddy/Caddyfile`
  passed.
- Caddy routes `/biblemaxxing` to `biblemaxxing-api:8000` and preserves the
  TailorTom fallback to `api:8000`.
- Docker DNS alias collision was fixed by naming the BibleMaxxing service
  `biblemaxxing-api`; TailorTom retains the generic `api` alias.

## Public Verification

- `https://api.tailortom.org/biblemaxxing/health` returns:
  `{"ok":true,"service":"biblemaxxing","env":"production"}`.
- `https://api.tailortom.org/health` returns:
  `{"status":"healthy"}`.
- `BASE_URL=https://api.tailortom.org ./scripts/smoke_api.sh` passed.
- Production sample inventory now has three approved BibleProject videos:
  - `p7XRPGzL6kk`: `Who is Jesus?`
  - `YMOB4hWKqfw`: `Jesus Feeds People in the Wilderness`
  - `jGKFWfpAfZY`: `Do not worry.`
- Old placeholder sample rows are hidden in production.
- Production active user count after smoke cleanup is `0`, so Ryan's first real
  signup should become admin.

## Remaining Manual Checks

- Run the app on Ryan's iPhone and log in/register against the hosted API.
- Configure Apple Developer credentials before real Sign in with Apple use.
- Add a real YouTube Data API key before scheduled live ingestion beyond the
  seed inventory.
