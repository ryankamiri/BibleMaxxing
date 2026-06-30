# Docs Agent Guide

This folder owns product specs, architecture notes, App Store compliance notes, API docs, privacy/terms drafts, and research summaries.

Read the root `AGENTS.md` before changing anything here.

## Documentation Priorities

- Keep docs concise, implementation-useful, and current.
- Cite primary sources for App Store, YouTube, privacy, or legal/platform policy claims.
- Document final decisions and open questions separately.
- Prefer dated decision records for major architecture/product changes.

## Required Topics

Maintain docs for:

- App Store compliance path.
- YouTube API/embed-only content policy.
- Content moderation/report/block/account deletion.
- Recommendation algorithm and anti-addiction guardrails.
- Data model and API surface.
- Deployment plan for `https://api.tailortom.org/biblemaxxing`.
- Overnight QA checklist and verification evidence.

## Canonical Files

- `api-surface.md` is the shared backend/iOS/admin API contract.
- `youtube-embed-policy.md` is the source-of-truth for YouTube allowed and forbidden behavior.
- `app-store-compliance.md` tracks App Store and TestFlight readiness.
- `app-review-submission.md` is the App Store Connect handoff for public URLs,
  review notes, metadata wording, and demo account instructions.
- `app-store-connect-pre-submit.md` is the paste-ready App Store Connect package
  for metadata, privacy nutrition answers, age rating, screenshots, and
  signing/upload handoff.
- `app-store-friend-publishing.md` is the friend-publisher handoff for signing,
  App Store Connect ownership, public URL values, and compliance guardrails.
- `moderation-account-deletion.md` tracks moderation, reports, blocks, and account deletion behavior.
- `recommendation-ingestion-evals.md` tracks recommender/worker eval scorecards,
  gates, baseline comparison semantics, and run commands.
- `qa-checklist.md` tracks final CTO verification steps.
- `verification-log.md` records commands and live deployment evidence from completed checkpoints.

When production worker cadence, ingestion counts, admin state, or VPS health is
verified, update `verification-log.md` with UTC timestamps and counts.

## Privacy

- Do not include secrets, cookies, private keys, raw tokens, or private account data in docs.
- Draft privacy/terms text should be clearly marked as drafts unless reviewed.
