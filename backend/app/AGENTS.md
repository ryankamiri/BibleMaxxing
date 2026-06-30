# Backend App Agent Guide

This folder contains the FastAPI application code: configuration, database setup, models, schemas, services, routes, and app startup.

Read `../AGENTS.md` and the root `AGENTS.md` before editing.

## Rules

- Keep the API mounted under `/biblemaxxing`.
- Keep route responses compatible with the SwiftUI client.
- Use SQLAlchemy 2.0 patterns.
- Do not add YouTube video downloading, caching, transcoding, or rehosting.
- Do not log secrets, passwords, tokens, or raw credentials.
- `youtube.py` and `youtube_worker.py` may fetch/store YouTube metadata only.
- The Docker `youtube-worker` service runs `python -m app.youtube_worker`.
- `youtube_worker.py` should keep the pastor/sermon-clip lane rotating through
  configured source queries instead of replacing the broad discovery queries.
- `services.classify_candidate` may use source-aware boosts for explicitly
  aligned pastor/channel names, but broad or ambiguous words should not become
  automatic approval signals.
- `services.ranking_score` should keep the trusted influencer boost bounded:
  trusted pastor/creator clips should rank prominently, but not bypass
  moderation, not-interested, blocks, or seen-history exclusions.
- `/biblemaxxing/player/{youtube_video_id}` serves a first-party HTML shell for
  the official YouTube iframe player so iOS gets a stable HTTPS origin/referrer.
  It must never proxy, download, cache, or rehost YouTube audiovisual content.
- The player shell may use official iframe commands to replay the current video
  when YouTube reports the ended state.
- Update this file when backend architecture changes.
