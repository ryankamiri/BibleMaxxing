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
- If YouTube returns quota-exhausted errors, stop the current worker cycle early
  and sleep until the next interval instead of repeatedly hitting later queries.
- `services.classify_candidate` may use source-aware boosts for explicitly
  aligned pastor/channel names, but broad or ambiguous words should not become
  automatic approval signals.
- `services.ranking_score` should keep the trusted influencer boost bounded:
  trusted pastor/creator clips should rank prominently, but not bypass
  moderation, not-interested, blocks, or seen-history exclusions.
- `services.user_interest_profile` is the per-user recommendation feedback
  loop. It should use explicit signals first, keep watch-time capped, and never
  allow engagement to override theological safety or spiritual usefulness.
- `services.diversify_ranked_videos` is the exploration/diversity layer after
  relevance scoring. Keep creator/topic diversity as a first-class feed
  invariant so trusted creators can appear often without monopolizing the feed.
  It should cap repeated source/person keys such as `philip-anthony-mitchell`
  across repost channels, not only repeated `creator_id` rows.
- Small fresh feeds should be especially strict about source/person caps; one
  aligned preacher/source can appear, but should not crowd the first screen
  when safe alternatives exist.
- `evals.py` owns scorecards for recommendation quality, YouTube candidate
  quality, red-team ingestion fixtures, query-plan coverage, and baseline
  comparison. Update it when ranking or ingestion semantics change.
- Admin eval endpoints persist scorecard runs in `eval_runs` by default and
  expose `save=false` for dry-run checks. Keep the recent-runs endpoint
  admin-only.
- Positive feedback endpoints should validate that the target video exists
  before returning success, so the app never believes it trained the recommender
  on a missing video.
- Public legal/support pages under `/biblemaxxing/privacy`, `/terms`,
  `/community`, and `/support` must stay accessible without auth for App Store
  Connect and unauthenticated iOS links.
- `services.comment_policy_violation` rejects profanity, threats, slurs, and
  direct abuse before comments publish. Keep this targeted; do not move all
  comments to pending unless v1 moderation policy changes.
- `/biblemaxxing/player/{youtube_video_id}` serves a first-party HTML shell for
  the official YouTube iframe player so iOS gets a stable HTTPS origin/referrer.
  It must never proxy, download, cache, or rehost YouTube audiovisual content.
- The player shell may use official iframe commands to replay the current video
  when YouTube reports the ended state.
- Update this file when backend architecture changes.
