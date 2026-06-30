# BibleMaxxing Agent Guide

BibleMaxxing is a personal-first iOS app intended to replace compulsive short-video scrolling with a Christian short-video feed. The motto is: "Don't brainrot. BibleMax."

The product goal is to help Ryan become more like Christ at work and in life by replacing compulsive scrolling with explicitly Christian short-form content, reflection, Scripture, and a feed algorithm that resists addictive loops.

For the overnight build contract, read `goal.md` after this file. It contains the copy-paste `/goal` prompt and the verification checklist for the CTO agent.

## Required Agent Workflow

- Before working in any folder, read the root `AGENTS.md` and every `AGENTS.md` on the path to the files you will touch.
- If you create a new folder, add an `AGENTS.md` to it before or with the first code in that folder.
- When code behavior, architecture, deployment, data models, or product rules change, update the relevant `AGENTS.md` files in the same change.
- Keep `AGENTS.md` files operational and current. Do not turn them into stale essays.
- Prefer `rg` and `rg --files` for repo exploration.
- Do not commit secrets, cookies, tokens, private keys, production env files, or user credentials.
- Do not run destructive commands against the TailorTom VPS or local machine unless Ryan explicitly asks.
- Preserve existing user work. If a file has changes you did not make, work with them rather than reverting them.

## GitHub And CTO Operating Mode

- GitHub repo: `https://github.com/ryankamiri/BibleMaxxing`.
- Local remote: `origin git@github.com:ryankamiri/BibleMaxxing.git`.
- The CTO agent may create commits and push to `origin` when that helps checkpoint meaningful working progress, share diffs, or preserve deployable states.
- Commit only coherent milestones. Do not commit secrets, local env files, generated junk, or broken half-edits unless the commit message clearly marks a WIP checkpoint that Ryan requested.
- Prefer small, reviewable commits with clear messages.
- Before pushing, inspect `git status --short` and avoid bundling unrelated user changes.
- The Xcode `project.pbxproj` is versioned and should not be gitignored. Ryan's
  Apple development team ID may be committed for this personal sideloaded
  prototype so agents can rebuild/install on his phone without reconfiguring
  signing. Never commit certificates, provisioning profiles, or xcuserdata.
- If a long-running `/goal` is active, keep a short progress trail through commits, docs, or a progress log so resumed agents can understand what was verified.
- Use subagents aggressively for parallel research, implementation, QA, and deployment work, but the CTO agent owns final integration, verification, and product judgment.
- Subagents must read all relevant `AGENTS.md` files before touching their assigned area and must update those files when their changes alter architecture or behavior.

## Current Stack Decisions

- iOS app: native SwiftUI.
- Design: dark mode only, polished vertical short-video feed inspired by Reels but not a clone.
- Backend: Python FastAPI.
- Database: Postgres.
- ORM: SQLAlchemy 2.0 with Alembic migrations and Pydantic schemas. Do not switch to SQLModel unless Ryan explicitly reverses this decision.
- Recommendation data: start with Postgres tables and local/simple embeddings where practical; keep the schema compatible with `pgvector` later.
- Deployment target: TailorTom VPS at `ssh tailortom`, reachable through `https://api.tailortom.org/biblemaxxing`.
- Deployment shape: add a separate BibleMaxxing backend route/container. Do not disrupt the existing TailorTom API currently routed at `api.tailortom.org`.

## Content Source Policy

The v1 content source is YouTube Shorts-style videos via official YouTube APIs and embedded playback.

Allowed:

- Use YouTube Data API to discover and store video metadata.
- Include a rotating pastor/sermon-clip ingestion lane in addition to broad
  Christian Shorts discovery. Prioritize sources aligned with Ryan's profile,
  including Philip Anthony Mitchell / 2819 Church, Bryce Crawford, Cliffe
  Knechtle / Give Me An Answer, Tim Mackie / BibleProject, Gavin Ortlund, John
  Piper, Tim Keller, David Platt, and Matt Chandler.
- Treat those aligned pastor/creator sources as trusted influencers in the
  recommender. Their videos should show up often through a bounded ranking
  boost, while still respecting theological safety, reports, blocks, seen
  history, and not-interested signals.
- Store `youtube_video_id`, title, description, channel, thumbnails, duration, tags, topic scores, embeddings, ranking features, moderation status, and source URLs.
- Play YouTube videos through the official embedded player in the app.
- Prefetch metadata, thumbnails, feed candidates, ranking results, and next-player shells.
- Cue the next video player so swiping feels fast.
- Skip unavailable, age-restricted, private, deleted, or non-embeddable videos.
- Show source/attribution in a subtle but accessible way.

Forbidden:

- Do not download, cache, store, rehost, convert, or serve YouTube audiovisual content as MP4s.
- Do not offer save-to-camera-roll or offline playback for YouTube-sourced videos.
- Do not scrape Instagram, use Instagram cookies/tokens, automate Instagram scrolling, download Instagram Reels, or hide Instagram as a source.
- Do not disguise third-party content as BibleMaxxing-owned content.

Future creator uploads are allowed as an architecture consideration only. When implemented, require creator rights confirmation, moderation, reporting, blocking, takedown handling, and clear attribution.

## Product Requirements

- Login before feed.
- Build Sign in with Apple code paths as App-Store-ready, even if full use requires an Apple Developer account later.
- Email/password auth is required. Username and email are required. Phone is not collected.
- Passwords must be securely hashed.
- Birthday or declared age gate should support a 13+ posture.
- Account deletion must be available in app.
- User profiles are public for now.
- Users can follow creators and topics.
- Onboarding is required before the first feed. It should collect topic preferences such as prayer, anxiety, discipline, apologetics, workplace holiness, Bible study, worship, testimony, and Christian living.
- Feed UX: Tap to Start with sound, subsequent native paging swipes auto-play,
  tapping the video surface pauses/resumes, double tap likes, the current video
  repeats when it ends, and YouTube embed chrome stays hidden behind
  BibleMaxxing's own controls.
- The app should maintain a previous/current/next player window where feasible.
- Prefer vertical or Shorts-like videos that fill the reel frame, but do not
  ban landscape videos when the content is spiritually useful and safe.
- Double tap hearts/likes a video.
- Saves are in-app bookmarks for YouTube videos.
- No share feature in v1.
- Comments are in v1 and require moderation.
- Users can report videos/comments and block users/creators.
- Users can mark videos as not interested.
- Reflection/Scripture cards should appear after about 10 minutes and when binge-like behavior is detected.

## Recommendation Priorities

The feed must not optimize for watch time alone.

Priority order:

1. Spiritual usefulness and Christ-centeredness.
2. Theological safety.
3. Trusted influencer/source boosts for aligned pastors and creators.
4. Entertainment and freshness.
5. Creator diversity.
6. Watch-time, completion, rewatch, likes, saves, skips, and not-interested signals.

Watch time and rewatch are positive signals, but they must be bounded by theological safety, source quality, diversity, freshness, and anti-addiction rules.

Already-seen feed videos should not be recycled into newly generated feeds. Treat
prior impressions, watch events, likes, saves, and not-interested signals as
seen-history exclusions before ranking candidates.

Video format is a preference signal, not a hard exclusion. Boost Shorts-like,
screen-filling candidates when metadata suggests it, while keeping landscape
videos eligible if they score well on spiritual usefulness and safety.

## Theology And Content Fit

The app should be explicitly Christian and Protestant-first. Catholic and Orthodox videos are not categorically banned, but rank lower unless they are clearly Bible-centered, Christ-centered, and compatible with the app's guardrails.

Personalization should follow Ryan's belief profile from `/Users/ramiri/dev/projects/Codex-Env/christian-beliefs-profile.md`:

- Biblical-theological / narrativist instincts.
- BibleProject, Tim Mackie, N. T. Wright, Gavin Ortlund, and broadly Reformed influences.
- Christ-centered, kingdom/new-creation emphasis.
- Broadly Calvinist soteriology, but not cage-stage or Calvinism-centered.
- Complementarian leadership instincts.
- Amillennial / new-creation eschatology.
- Spirit-open but orderly.
- Serious about Scripture, warm pastoral tone, practical holiness, and workplace discipleship.

Exclude or downrank:

- Mormon, Jehovah's Witness, Oneness Pentecostal, and Seventh-Day Adventist teaching.
- Non-Christian spirituality.
- Prosperity gospel.
- Christian nationalism.
- Rapture-chart / premillennial Israel-politics-heavy content.
- Doctrinal vagueness around whether same-sex marriage is sin.
- Harsh, cruel, or mocking treatment of gay/trans people.
- Political outrage bait.
- Low-effort engagement bait that is not spiritually useful.
- Content that is mainly controversy, debates, or end-times speculation.
- Heretical, pornographic, hateful, violent, or exploitative material.

## App Store Track

Build in a way that can later become App Store compliant:

- Use permitted third-party APIs and embeds only.
- Keep rights/attribution/source metadata.
- Include content filtering, report flows, block flows, timely moderation surfaces, and contact information.
- Include account deletion.
- Keep privacy policy and terms drafts in `docs/` when created.
- Do not require unnecessary personal data.
- Do not copy Instagram branding or exact UI details. A vertical swipe feed is acceptable; cloning Instagram is not.

## Overnight Success Criteria

By 8 AM, the ideal outcome is:

- A SwiftUI app that can run on Ryan's iPhone 17 or simulator.
- A reachable backend at `https://api.tailortom.org/biblemaxxing`.
- Postgres-backed auth and feed data.
- YouTube-based video feed with real videos already ingested.
- Onboarding, login, vertical feed, tap-to-start playback, swiping, likes, saves, comments, reports, blocks, not-interested, and reflection cards.
- A basic recommendation loop using watch events and explicit signals.
- Admin moderation surfaces or at least admin endpoints/scripts.
- Folder-level `AGENTS.md` files kept current.
