# BibleMaxxing Overnight Goal

Copy/paste this into Codex as the `/goal` prompt when starting the overnight build.

```text
/goal Build BibleMaxxing end to end as a working personal iOS prototype by 8 AM, verified by a runnable SwiftUI app and a reachable backend at https://api.tailortom.org/biblemaxxing. Read every AGENTS.md file first and keep AGENTS.md files updated whenever code changes alter architecture, behavior, deployment, or product constraints. Use the GitHub repo https://github.com/ryankamiri/BibleMaxxing with origin git@github.com:ryankamiri/BibleMaxxing.git; commit and push coherent CTO checkpoints when they preserve meaningful progress or help review diffs.

Act as CTO and orchestrator, not just an implementer. Fan work out to subagents where useful across iOS, backend, ingestion, recommendation, moderation/admin, infra/deployment, and QA. Each subagent must read the root AGENTS.md plus any folder-level AGENTS.md files before touching code, and must report back with files changed, verification done, and remaining risks. The CTO agent owns final integration, conflict resolution, quality bar, and evidence-based completion.

Product outcome: BibleMaxxing is a dark-mode native iOS app that replaces doom scrolling with an explicitly Christian short-video feed. The motto is "Don't brainrot. BibleMax." The app should help Ryan become more like Christ in work and life through Bible-centered videos, intentional reflection, and a feed algorithm that resists addictive loops.

Core stack:
- iOS: SwiftUI, dark mode only, optimized for modern iPhones including Ryan's iPhone 17.
- Backend: Python FastAPI.
- Database: Postgres.
- ORM: SQLAlchemy 2.0 plus Alembic migrations and Pydantic schemas.
- Deployment: TailorTom VPS via ssh tailortom, exposed under https://api.tailortom.org/biblemaxxing without disrupting TailorTom.
- Content source: YouTube Data API metadata plus official embedded YouTube playback only.

Hard content constraints:
- Do not scrape Instagram, use Instagram cookies/tokens, automate Instagram, download Instagram Reels, or hide third-party sources.
- Do not download, cache, store, convert, rehost, or serve YouTube audiovisual content or MP4s.
- Do not implement offline playback or save-to-camera-roll for YouTube-sourced videos.
- Allowed prefetching is metadata, thumbnails, feed candidates, ranking results, and next-player setup/cueing where permitted.
- Store YouTube video IDs, metadata, thumbnails, channel/creator info, source URLs, tags/topics, moderation status, embeddings/ranking features, and watch/recommendation signals.
- Skip unavailable, private, deleted, age-restricted, or non-embeddable videos.
- Keep source attribution available in the app.

Required app features:
- Login before feed for the personal prototype.
- Email/password auth with secure password hashing.
- Username and email required. Do not collect phone numbers.
- Birthday or declared-age gate for a 13+ posture.
- Sign in with Apple code path prepared, even if full Apple Developer setup is not ready.
- In-app account deletion.
- Onboarding before first feed with topic preferences such as prayer, anxiety, discipline, apologetics, workplace holiness, Bible study, worship, testimony, Christian living, Scripture, theology, and gospel encouragement.
- Vertical full-screen feed.
- Tap to Start with sound, then subsequent swipes auto-play.
- Previous/current/next player strategy where feasible.
- Double tap to like.
- In-app saves/bookmarks.
- Not interested.
- Follow creators and topics.
- Search people/creators and topics.
- Comments in v1, with moderation/reporting.
- Report video/comment.
- Block user/creator.
- Admin moderation surface or endpoints/scripts for reviewing videos, comments, reports, users, creators, and blocks.
- Reflection/Scripture cards after about 10 minutes and when binge-like behavior is detected.

Recommendation requirements:
- Do not optimize for watch time alone.
- Rank by spiritual usefulness and Christ-centeredness first, theological safety second, entertainment/freshness third, creator diversity fourth, and watch-time/rewatch/like/save/skip/not-interested signals fifth.
- Use onboarding topics, follows, likes, saves, watch events, skips, not-interested, freshness, creator diversity, and moderation quality.
- Bounded watch time and rewatch are positive signals, but must not override theological safety, diversity, or anti-addiction guardrails.

Theology/content fit:
- Explicitly Christian and Protestant-first.
- Catholic and Orthodox videos may appear only when clearly Bible-centered, Christ-centered, and compatible with guardrails; rank lower by default.
- Use Ryan's belief profile at /Users/ramiri/dev/projects/Codex-Env/christian-beliefs-profile.md for personalization.
- Prefer biblical-theological/narrativist, Christ-centered, kingdom/new-creation, broadly Reformed, complementarian, amillennial, Spirit-open but orderly, Scripture-serious content.
- Exclude or downrank Mormon, Jehovah's Witness, Oneness Pentecostal, Seventh-Day Adventist, prosperity gospel, Christian nationalism, rapture-chart/Israel-politics-heavy content, non-Christian spirituality, doctrinally vague sexuality teaching, harsh cruelty toward gay/trans people, political outrage bait, controversy bait, and low-effort engagement bait.

Backend/data requirements:
- Provide versioned API routes under /biblemaxxing/api/v1 where practical.
- Include health endpoint.
- Model users, auth credentials/sessions, onboarding preferences, creators/channels, videos, video sources, topics/tags, feed impressions, watch events, likes, saves, not-interested signals, follows, comments, reports, blocks, reflection events/cards, admin review state, and moderation audit fields.
- Provide ingestion worker/script that discovers Christian YouTube Shorts-style candidates, stores metadata, filters/moderates, and keeps enough feed inventory ready.
- Prefer local/simple embeddings if feasible; keep schema compatible with pgvector or stronger embeddings later.
- Provide seed/admin account setup that does not expose secrets.

Infrastructure requirements:
- Inspect the TailorTom VPS before editing deployment files.
- Back up any VPS Caddy/compose config before changing it.
- Deploy BibleMaxxing without breaking TailorTom's current api.tailortom.org behavior.
- Prefer a separate Docker compose/project or isolated services.
- Use env vars for secrets and commit only .env.example.
- Expose the backend at https://api.tailortom.org/biblemaxxing.

Verification surface:
- iOS app builds locally with xcodebuild or documented Xcode instructions if CLI build is blocked.
- Backend starts locally and health endpoint passes.
- Database migrations run.
- Ingestion can populate real YouTube metadata, or if API credentials are unavailable, the blocker is documented and a safe sample fixture path is implemented.
- API endpoints for auth, onboarding, feed, watch events, likes, saves, comments, reports, blocks, account deletion, and admin moderation are exercised by tests, scripts, or documented curl checks.
- Deployed backend health endpoint is reachable at https://api.tailortom.org/biblemaxxing/health or the implemented equivalent.
- No committed secrets.
- git status is clean or only contains intentionally documented work.

Iteration policy:
- Work in checkpoints: docs/contracts, backend schema/API, YouTube ingestion, recommendation loop, iOS app shell/feed/player, auth/onboarding, moderation/comments/admin, deployment, QA polish.
- After each checkpoint, run the most relevant verification command and record what passed, what failed, and the next best step.
- Commit and push coherent checkpoints to origin when useful.
- Keep changes scoped and prefer working vertical slices over isolated unfinished layers.
- If blocked, try at least three reasonable approaches when safe. If still blocked, stop with the blocker, attempted paths, evidence gathered, and the exact user input or external change needed.

Stopping condition:
- Mark the goal complete only when the app can be run as a personal dev build with a working feed experience backed by the hosted API, or when all feasible implementation work is done and any remaining blocker is external, explicit, and documented with evidence.
```

## Why This Goal Is Shaped This Way

OpenAI's Codex goal guidance says a strong goal should define the outcome, verification surface, constraints, boundaries, iteration policy, and blocked stop condition. This file is intentionally written as an operating contract rather than a loose backlog.

Primary references:

- https://developers.openai.com/codex/use-cases/follow-goals
- https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex

