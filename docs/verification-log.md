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

## Eval System Deployment

- At `2026-06-30 17:08:58 UTC`, after deploying backend recommendation and
  ingestion eval scorecards, both health routes returned healthy:
  - `https://api.tailortom.org/biblemaxxing/health`:
    `{"ok":true,"service":"biblemaxxing","env":"production"}`
  - `https://api.tailortom.org/health`: `{"status":"healthy"}`
- Local verification after the eval changes:
  - `backend/.venv/bin/python -m ruff check backend scripts/run_evals.py`
    passed.
  - `backend/.venv/bin/python -m pytest backend/tests` passed with
    `21 passed, 4 warnings`.
  - `scripts/run_evals.py --limit 12`, followed by a saved-baseline comparison,
    reported `baselining` for recommendation, ingest query plan, and ingest
    red-team scorecards.
- Production eval sample for `ryanamiri05@gmail.com` after the final deploy:
  - recommendation status: `healthy`
  - recommendation score: `91.54`
  - feed count: `30`
  - creator coverage: `1.0`
  - max creator share: `0.0333`
  - max aligned source share: `0.1`
  - consecutive source repeats: `0`
  - average theology score: `0.8287`
- Production ingestion eval sample:
  - query plan status: `healthy`, score `100.0`
  - query count: `12`
  - broad query count: `10`
  - pastor query count: `2`
  - duplicate query count: `0`
  - red-team status: `baseline`, score `72.16`
  - red-flag auto-approved count: `0`
- The production YouTube worker is currently quota-limited by YouTube Search
  Queries for the day. After the quota-aware worker patch, the restarted worker
  logged one query-plan eval, encountered one `429` quota error, stopped the
  current cycle early, and slept for `7200` seconds instead of continuing to
  hit later queries.
- At `2026-06-30 17:44:20 UTC`, after tightening source/person diversity and
  deploying eval-history persistence, production migration state was
  `0002_eval_runs`; `eval_runs` contained the worker query-plan scorecard:
  status `healthy`, score `100.0`, `4` broad queries, `2` pastor/source
  queries, and estimated `72.0` YouTube search calls per day.
- Production inventory at the same checkpoint had `395` videos, `392`
  approved/embeddable videos, and `249` creators with approved embeddable
  videos. Top approved creators included BibleProject `36`, Those Few `14`,
  2819 Church `9`, David Diga Hernandez `8`, Hailey Julia `7`, Gathering
  Worship `6`, and JoeChristianGuy `6`.
- A production feed probe for `ryanamiri05@gmail.com` with `limit=12` returned
  exactly one `philip-anthony-mitchell` source item, no repeated creators,
  max creator share `0.0833`, max aligned source share `0.0833`, recommendation
  eval status `healthy`, and score `91.66`.
- The latest iOS app, including the admin page, was built for Ryan's connected
  iPhone 17 Pro Max (`0E6487E2-0018-5DF6-9541-F0099E1FEBAE`), installed, and
  launched with bundle id `com.ryanamiri.biblemaxxing`.

## Remaining Manual Checks

- Verify YouTube playback manually on Ryan's iPhone after the installed player
  shell fix.
- Configure Apple Developer credentials before real Sign in with Apple use.
- Review/curate the newly ingested approved feed in the admin workflow as the
  theological safety bar tightens.

## App Store Pre-Submit Package

- At `2026-06-30 21:22:24 UTC`, production health returned
  `{"ok":true,"service":"biblemaxxing","env":"production"}` after the account
  deletion privacy patch was deployed to the VPS.
- Production inventory at the same checkpoint:
  - total videos: `396`
  - approved videos: `393`
  - open reports: `0`
  - active users: `6`
  - comments: `17`
- A live disposable deletion probe created
  `appstore-deletecheck-*.example.com`, called `DELETE /api/v1/me`, then
  confirmed:
  - deleted row had `deleted_at` set
  - email was anonymized to the `deleted.biblemaxxing.local` namespace
  - username was anonymized to `deleted-{user_id_without_dashes}`
  - birthday was cleared
  - admin flag was false
  - active sessions count was `0`
  - reused token returned HTTP `401`
- Local pre-submit verification passed:
  - `backend/.venv/bin/python -m ruff check backend scripts/run_evals.py`
  - `backend/.venv/bin/python -m pytest backend/tests -q`
  - `xcodebuild -project ios/BibleMaxxing.xcodeproj -scheme BibleMaxxing
    -configuration Debug -destination
    'id=52478642-5FE7-4182-B023-5BD6EE03C88A' -derivedDataPath
    /tmp/BibleMaxxingSubmitDerived CODE_SIGNING_ALLOWED=NO build`
- Generated iPhone 17 App Store screenshot candidates live in
  `docs/app-store-assets/screenshots/`:
  - `iphone17-auth-login.png`
  - `iphone17-feed-tap-to-start.png`
  - `iphone17-comments-empty.png`
  - `iphone17-settings-legal.png`
- The current build hides the visible Sign in with Apple button until the
  backend Apple credential exchange is configured, preventing a review-visible
  501 flow while preserving the future code path.
