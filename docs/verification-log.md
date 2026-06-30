# BibleMaxxing Verification Log

Reviewed: 2026-06-30

## Local Verification

- Backend format/lint/tests:
  `cd backend && source .venv/bin/activate && ruff format . && ruff check . && pytest -q`
  passed with 5 tests.
- Alembic clean-database migration:
  `BIBLEMAXXING_DATABASE_URL=sqlite:////tmp/biblemaxxing-alembic-test.db alembic upgrade head`
  passed.
- iOS build:
  `xcodebuild -project ios/BibleMaxxing.xcodeproj -scheme BibleMaxxing -destination 'generic/platform=iOS Simulator' CODE_SIGNING_ALLOWED=NO build`
  passed.
- Physical iPhone build/install:
  `xcodebuild -project ios/BibleMaxxing.xcodeproj -scheme BibleMaxxing -destination 'id=00008150-001678E1368B401C' -allowProvisioningUpdates build`
  passed, then `xcrun devicectl device install app ...` and
  `xcrun devicectl device process launch ... com.ryanamiri.biblemaxxing`
  installed and launched the app on Ryan's iPhone.
- Local HTTP smoke:
  `BASE_URL=http://127.0.0.1:8765 ./scripts/smoke_api.sh`
  passed against a live `uvicorn` process.
- Compose config:
  `docker compose --env-file infra/biblemaxxing.env.example -f infra/docker-compose.biblemaxxing.example.yml config`
  passed with `TAILORTOM_CADDY_NETWORK=tailortom_tailortom` and a
  worker-only `biblemaxxing-egress` network for outbound YouTube Data API
  requests.

## VPS Deployment

- TailorTom preflight inspected Docker containers, ports, Caddyfile, compose
  config, and networks.
- Observed shared Caddy network: `tailortom_tailortom`.
- BibleMaxxing deployed under `/opt/biblemaxxing` with its own compose project,
  Postgres volume, and FastAPI container.
- YouTube Data API v3 is enabled in the Google Cloud `TailorTom` project.
- The production YouTube Data API key is stored only in `/opt/biblemaxxing/.env`,
  restricted to YouTube Data API v3 and the VPS IP. A previously exposed
  generated key was rotated and the previous key was deleted in Google Cloud.
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
- `https://api.tailortom.org/biblemaxxing/player/M7lc1UVf-VE?autoplay=1`
  returns `200 OK` through Caddy with `cache-control: no-store`,
  `referrer-policy: strict-origin-when-cross-origin`, the official
  `https://www.youtube.com/iframe_api` script, `origin:
  window.location.origin`, `widget_referrer: window.location.href`, and
  `onPlayerError` fallback handling.
- `https://api.tailortom.org/health` returns:
  `{"status":"healthy"}`.
- `BASE_URL=https://api.tailortom.org/biblemaxxing ./scripts/smoke_api.sh`
  passed.
- `youtube-worker` completed a live metadata ingestion cycle at
  `2026-06-30 11:49:47 UTC`, creating 211 records and skipping 39 duplicates or
  filtered candidates. Its default interval was later reduced from 21600
  seconds to 7200 seconds for more frequent development ingestion.
- After the 7200-second interval change, the production worker was restarted and
  completed another cycle at `2026-06-30 13:23:00 UTC`, creating 36 records and
  skipping 214 duplicates or filtered candidates. The next sleep interval logged
  as 7200 seconds.
- After deploying the hosted player shell, the production worker restarted again
  and completed a cycle at `2026-06-30 13:28:58 UTC`, creating 8 records and
  skipping 242 duplicates or filtered candidates. The next sleep interval logged
  as 7200 seconds.
- The production user `ryanamiri05@gmail.com` was idempotently promoted to admin
  again, then the production worker was force-recreated and completed an
  immediate cycle at `2026-06-30 13:53:57 UTC`, creating 15 records and
  skipping 235 duplicates or filtered candidates. The next sleep interval logged
  as 7200 seconds.
- Production video inventory after live ingestion:
  - approved: `273`
  - hidden: `3`
  - total: `276`
  - distinct approved creators: `176`
- Production sample inventory still includes the three approved BibleProject
  seed videos:
  - `p7XRPGzL6kk`: `Who is Jesus?`
  - `YMOB4hWKqfw`: `Jesus Feeds People in the Wilderness`
  - `jGKFWfpAfZY`: `Do not worry.`
- Old placeholder sample rows are hidden in production.
- Production user `ryanamiri05@gmail.com` exists and has `is_admin = true`.

## Remaining Manual Checks

- Verify YouTube playback manually on Ryan's iPhone after the installed player
  shell fix.
- Configure Apple Developer credentials before real Sign in with Apple use.
- Review/curate the newly ingested approved feed in the admin workflow as the
  theological safety bar tightens.
