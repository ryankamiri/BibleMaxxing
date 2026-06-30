# BibleMaxxing Admin Plan

This folder defines the minimum admin surface for overnight moderation and
operations. The first shippable admin surface can be endpoint/script based; a
static or backend-rendered dashboard can follow once the API is stable.

## Minimum Overnight Capability

Admins need to:

- list open reports
- inspect reported videos, comments, users, and creators/channels
- hide or approve videos
- hide, remove, or approve comments
- block or unblock creators/channels
- suspend or reinstate users
- override topic/theology/safety labels
- resolve reports with notes
- view audit history for admin actions

## Static Admin Dashboard Plan

A simple v0 admin dashboard can be one protected page served by the backend or
opened locally by the CTO agent. It should call the admin API described in
`../docs/api-surface.md`.

Suggested views:

- Reports queue
- Pending videos
- Pending comments
- Creator/channel lookup
- User lookup
- Audit log

Do not include secrets in static files. Admin auth should use the normal backend
session/JWT flow with an admin role.

## API Dependencies

Required endpoints:

- `GET /api/v1/admin/reports?status=open&type=`
- `POST /api/v1/admin/reports/{report_id}/resolve`
- `GET /api/v1/admin/videos?status=pending`
- `PATCH /api/v1/admin/videos/{video_id}/moderation`
- `GET /api/v1/admin/comments?status=pending`
- `PATCH /api/v1/admin/comments/{comment_id}/moderation`
- `GET /api/v1/admin/users?query=`
- `PATCH /api/v1/admin/users/{user_id}`
- `GET /api/v1/admin/creators?query=`
- `PATCH /api/v1/admin/creators/{creator_id}`
- `GET /api/v1/admin/audit-log`

## Data Columns For Review Tables

Reports:

- report ID
- report type
- reason
- target type and ID
- target preview
- reporter username or ID
- status
- created at
- assigned/reviewed by
- resolution note

Videos:

- video ID
- YouTube video ID
- title
- channel
- source URL
- embeddable/availability status
- topic labels
- theology/safety labels
- moderation status
- report count
- last reviewed at

Comments:

- comment ID
- video title/source
- author
- body preview
- status
- report count
- created at
- last reviewed at

## Safety Rules

- YouTube videos remain embedded and attributed.
- Admin tools must not download or rehost YouTube/Instagram media.
- Every moderation write must create an audit log entry.
- Hiding/removing content should be reversible where practical.
- Admin scripts should default to read-only unless a `--write` or explicit
  action flag is provided.
