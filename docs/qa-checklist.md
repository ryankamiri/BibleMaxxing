# Overnight QA Checklist

Reviewed: 2026-06-30

Use this as the CTO final verification checklist. Mark blockers with exact
commands, output snippets, and the next required action.

## Repo Hygiene

```bash
git status --short
rg -n "SECRET|PRIVATE KEY|BEGIN RSA|BEGIN OPENSSH|YOUTUBE_API_KEY=.*[A-Za-z0-9_-]{20}|JWT_SECRET|PASSWORD=" .
rg -n "yt-dlp|youtube-dl|ffmpeg|mp4|m3u8|AVAssetDownload|download.*youtube" .
```

Pass criteria:

- No committed secrets.
- No YouTube audiovisual download/rehost path.
- No unintended backend/iOS/admin/infra conflicts.

## Backend Local

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
curl -fsS http://127.0.0.1:8000/biblemaxxing/health
```

Pass criteria:

- FastAPI starts.
- DB migrations run.
- Health returns JSON with `ok=true`.

## API Behavior

Exercise at least:

- register
- login
- onboarding
- feed
- impression/watch event
- like/unlike
- save/unsave
- not interested
- comment create/list/report
- video report
- user/creator block
- account deletion
- admin report list/resolve

Preferred smoke script shape:

```bash
BASE_URL=http://127.0.0.1:8000 ./scripts/smoke_api.sh
BASE_URL=https://api.tailortom.org/biblemaxxing ./scripts/smoke_api.sh
```

## YouTube Ingestion

```bash
python scripts/fetch_youtube_candidates.py "Christian shorts prayer" --max-results 10 > /tmp/biblemaxxing-candidates.json
cd backend && BIBLEMAXXING_YOUTUBE_API_KEY=... python -m app.youtube_worker --once --query "Christian prayer shorts" --max-results 10
curl -fsS -X POST "$BASE_URL/api/v1/admin/ingest/candidates" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/biblemaxxing-candidates.json
curl -fsS "$BASE_URL/api/v1/admin/videos?moderation_status=pending" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Pass criteria:

- Real YouTube metadata is stored when credentials are present.
- `youtube-worker` is running in production compose and logs completed cycles.
- Fixture/sample path is available when credentials are absent.
- Stored records include `youtube_video_id`, source URL, embed URL, channel,
  thumbnails, duration, embeddable/availability status, and moderation status.
- Non-embeddable/private/deleted/age-restricted items are excluded from feed.

## iOS Local

```bash
cd ios
xcodebuild -list
xcodebuild -scheme BibleMaxxing -destination 'platform=iOS Simulator,name=iPhone 17' build
```

Manual checks:

- Login is required before feed.
- Onboarding is required before first feed.
- Feed is vertical and dark mode.
- First playback requires Tap to Start with sound.
- Subsequent swipes cue/play.
- Double tap likes.
- Save/bookmark works.
- Comments, reports, blocks, and not-interested are reachable.
- Account deletion exists in settings.
- Reflection/Scripture card appears after the configured trigger.

## Deployment

```bash
infra/deploy-tailortom.sh preflight
BIBLEMAXXING_CONFIRM_DEPLOY=1 infra/deploy-tailortom.sh sync
ssh tailortom 'cd /opt/biblemaxxing && docker compose up -d --remove-orphans'
curl -fsS https://api.tailortom.org/biblemaxxing/health
curl -fsS https://api.tailortom.org/
```

Pass criteria:

- BibleMaxxing health is reachable at the public URL.
- TailorTom's existing API still responds.
- Caddy config was backed up before changes.
- Caddy routes `/biblemaxxing` without stripping it and preserves TailorTom fallback.

## Admin And Moderation

Pass criteria:

- Admin can list open reports.
- Admin can hide a video.
- Admin can hide/remove a comment.
- Admin can resolve a report with a note.
- Admin can view audit log entries.
- User reports are easy to reach from the iOS app.

## App Store Readiness Snapshot

Pass criteria:

- No phone number collection.
- Sign in with Apple path exists if any third-party login exists.
- Account deletion works in app.
- Report/block flows exist for UGC.
- Privacy/terms drafts exist before external TestFlight.
- YouTube videos are embedded and attributed, not rehosted.
