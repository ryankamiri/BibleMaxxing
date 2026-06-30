# Moderation, Reports, Blocks, And Account Deletion

Reviewed: 2026-06-30

## Moderation Goals

BibleMaxxing should feel explicitly Christian, pastorally warm, and resistant to
rage bait. Moderation should protect users, honor source creators, and keep the
feed aligned with the product's theology/content guardrails.

## Moderation Objects

Moderate these object types:

- videos
- creators/channels
- comments
- users
- reports
- topic/theology labels
- reflection prompts/cards

## Core Statuses

Video statuses:

- `pending`
- `approved`
- `rejected`
- `hidden`
- `source_unavailable`
- `non_embeddable`
- `age_restricted`

Comment statuses:

- `visible`
- `pending`
- `hidden`
- `deleted_by_user`
- `removed_by_admin`

Report statuses:

- `open`
- `triaged`
- `actioned`
- `dismissed`
- `needs_followup`

## Report Reasons

Use consistent report reasons across videos and comments:

- not Christian
- unsafe theology
- harassment or cruelty
- sexual content
- violence or self-harm
- hateful content
- political outrage bait
- spam or scam
- source unavailable
- copyright/source concern
- other

## Moderator Actions

Every admin action should store:

- admin user ID
- target type and target ID
- previous status
- new status
- action reason
- free-text note
- timestamp

Allowed actions:

- approve video/comment
- reject video
- hide video/comment
- restore video/comment
- block creator/channel
- unblock creator/channel
- suspend user
- reinstate user
- override topic labels
- override theology/safety labels
- resolve report

## Comments

Comments are in v1 and require moderation support.

Minimum behavior:

- New comments from trusted users can be visible immediately if automated checks
  pass.
- Comments with profanity, slurs, threats, or direct abuse are rejected before
  posting.
- Comments with other risky terms or reports should move to `pending` or
  `hidden`.
- Reported comments remain visible or hidden based on severity; high-risk
  reports should hide pending review.
- Comment deletion should be soft-delete or tombstone-backed so reports and
  audit logs remain understandable.

## Blocks

User block:

- The blocked user's comments are hidden from the blocking user.
- The blocked user should not be able to interact with the blocking user's
  profile or comments where practical.

Creator/channel block:

- Videos from the blocked creator are excluded from that user's feed.
- Creator block is stronger than topic preference or watch history.

## Account Deletion

Account deletion must be available in app.

Recommended data behavior:

- Revoke active sessions immediately.
- Delete or anonymize email, username, password hash, Apple identifiers, and
  profile fields.
- Remove personal follows, likes, saves, not-interested signals, onboarding
  preferences, and watch events unless needed only in aggregated/anonymized form.
- Keep moderation audit records, report records, and security logs when needed
  to preserve safety, fraud prevention, or legal integrity.
- Public comments can be deleted, anonymized, or tombstoned based on final
  product policy; expose the choice clearly.

API contract:

- `DELETE /api/v1/me` starts deletion.
- Return whether deletion is immediate or scheduled.
- Prevent login after deletion starts unless an undo window is intentionally
  implemented.

## Personal Prototype Shortcut

For the overnight build, admin endpoints/scripts are acceptable before a polished
admin web UI as long as they can:

- list open reports
- inspect reported videos/comments/users/creators
- hide/remove content
- resolve reports with notes
- view action audit history
