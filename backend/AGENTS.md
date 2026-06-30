# Backend Agent Guide

This folder owns the Python API, data model, ingestion workers, recommendation engine, auth, moderation, and admin APIs.

Read the root `AGENTS.md` before changing anything here.

## Stack

- FastAPI.
- SQLAlchemy 2.0 ORM.
- Alembic migrations.
- Pydantic schemas.
- Postgres.
- Prefer `async` only where the stack is consistently async. Do not mix patterns casually.

## API Shape

- Production path should live under `/biblemaxxing`.
- Health endpoint required.
- Keep routes versionable, for example `/biblemaxxing/api/v1/...`.
- Design for deployment behind Caddy at `https://api.tailortom.org/biblemaxxing`.

## Data Domains

Model at least:

- users
- auth credentials / sessions
- onboarding preferences
- creators/channels
- videos
- video sources
- topics/tags
- feed impressions
- watch events
- likes
- saves
- not-interested signals
- follows
- comments
- moderation reports
- blocks
- reflection cards/events
- admin review state

## Content Ingestion

- V1 ingestion is YouTube metadata only.
- Use official YouTube APIs.
- Store metadata, thumbnails, IDs, source URLs, duration, tags, descriptions, channel data, and ranking/moderation fields.
- The `youtube-worker` runs broad Christian Shorts queries plus a rotating
  pastor/sermon-clip query lane. Keep the pastor list Protestant-first and
  aligned with Ryan's belief profile; current named examples include Philip
  Anthony Mitchell / 2819 Church, Bryce Crawford, and Cliffe Knechtle / Give Me
  An Answer.
- Aligned pastor/creator sources are trusted influencers. Tag their videos with
  `trusted-influencer` and use a bounded ranking boost so they appear often
  without overriding user safety controls or feedback.
- Do not download, cache, store, transcode, or serve YouTube audiovisual content.
- Keep the player iframe passive (`pointer-events: none`) and disable YouTube
  embed controls (`controls: 0`) so mobile feed taps do not surface native
  YouTube chrome over the BibleMaxxing controls.
- Filter for embeddable, public, available, Christian/Protestant-first, theologically safe videos.
- Default-publish only videos that pass automated filters. Keep moderation status editable.
- Skip non-embeddable or unavailable videos.

## Auth And Privacy

- Store username, email, and password hash.
- Do not collect phone numbers.
- Support declared birthday/13+ posture.
- Support account deletion.
- Build Sign in with Apple compatibility points, even if the Apple Developer account is not ready.
- Never log plaintext passwords, tokens, or secrets.

## Recommendations

Do not optimize for pure engagement.

Use:

- theological safety
- spiritual usefulness
- aligned pastor/source signals
- trusted influencer ranking boosts
- onboarding topics
- follows
- likes
- saves
- not-interested
- skips
- completion
- watch time
- rewatch
- freshness
- creator diversity
- reflection-card timing
- Shorts-like / vertical-frame fit as a preference signal

Watch time is a bounded signal, not the master objective.

Do not hard-ban landscape videos solely for format. Prefer Shorts-like,
screen-filling videos in ranking, but allow safe and spiritually useful
landscape videos to remain eligible.

Newly generated feeds should not show already-seen videos. Exclude videos with
prior impressions, watch events, likes, saves, or not-interested rows for that
user before ranking the candidate pool.

## Moderation

- Comments are part of v1 and must be reportable.
- Videos and creators must be reportable/blockable.
- Admins need a way to review reports and hide/remove content.
- Keep audit fields for moderation actions.
