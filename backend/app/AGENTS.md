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
- Update this file when backend architecture changes.
