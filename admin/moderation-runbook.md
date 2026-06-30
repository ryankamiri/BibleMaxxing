# Moderation Runbook

Reviewed: 2026-06-30

## Queue Order

Review in this order:

1. Safety-critical reports: sexual content, violence/self-harm, hateful content,
   harassment/cruelty, spam/scam.
2. Theological/content-fit reports: unsafe theology, not Christian, political
   outrage bait, copyright/source concern.
3. Pending comments.
4. Pending ingested videos.
5. Topic/theology label overrides.

## Video Report Workflow

1. Open the report and inspect:
   - source URL
   - title/description/channel
   - thumbnail
   - embeddable/availability status
   - current topic/theology labels
   - prior reports/actions
2. If the video is unavailable, private, deleted, age-restricted, or
   non-embeddable, set `source_unavailable`, `age_restricted`, or
   `non_embeddable` and remove it from feed eligibility.
3. If the video violates BibleMaxxing guardrails, set `rejected` or `hidden`.
4. If it is safe but mislabeled, update topic/theology/safety labels.
5. Resolve the report with a concise note.

## Comment Report Workflow

1. Inspect the full comment, surrounding thread context, and report reason.
2. Hide immediately for harassment, cruelty, sexual content, violent content,
   hate, doxxing, spam/scam, or graphic material.
3. For borderline comments, use `pending` while reviewing.
4. If the comment is acceptable, keep or restore it and dismiss the report.
5. Resolve the report with the action and note.

## User Or Creator Blocks

Creator/channel block:

- Use for repeated unsafe theology, low-quality engagement bait, source
  problems, or creator-level mismatch.
- Exclude the creator from feeds immediately.
- Preserve source metadata and audit history.

User suspension:

- Use for repeated abusive comments, spam, evasion, or harmful behavior.
- Revoke sessions if supported.
- Keep audit metadata.

## Label Override Guidance

Use labels to improve ranking without over-removing:

- `christ_centered_high`
- `bible_centered_high`
- `pastoral_warm`
- `workplace_holiness`
- `discipleship`
- `apologetics`
- `worship`
- `testimony`
- `controversy_bait`
- `political_outrage`
- `prosperity_gospel`
- `unsafe_theology`
- `non_christian`

Safety labels should outweigh watch-time and engagement in ranking.

## Response Time Targets

For the personal prototype:

- Safety-critical reports: same day when possible.
- Ordinary reports: within 48 hours when possible.
- Pending ingestion review: before content enters the approved feed.

## Audit Note Examples

```text
Hidden: report confirmed harassment toward another user.
Rejected: prosperity-gospel teaching, not aligned with feed guardrails.
Approved: Bible-centered testimony; report dismissed after review.
Relabeled: moved from apologetics to workplace_holiness; content is practical discipleship.
```
