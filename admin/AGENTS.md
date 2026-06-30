# Admin Agent Guide

This folder owns admin-facing tools and interfaces for moderation, ingestion review, reports, creator/channel management, and operational visibility.

Read the root `AGENTS.md` before changing anything here.

## Admin Requirements

- Admins need to see ingested videos, source metadata, moderation status, reports, comments, users, creators/channels, and blocks.
- Admins need to hide/remove videos and comments.
- Admins need to review reported content quickly.
- Admins need to override topic/theology labels when automated classification is wrong.
- Keep audit metadata for admin actions.
- Keep `README.md` and `moderation-runbook.md` updated when admin endpoints, review queues, or moderation actions change.

## Policy

- YouTube content remains embedded and attributed.
- Do not add tools that download or rehost YouTube/Instagram videos.
- Future creator uploads must require rights confirmation before publishing.
