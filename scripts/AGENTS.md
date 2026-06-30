# Scripts Agent Guide

This folder owns local helper scripts, ingestion scripts, admin scripts, one-off maintenance utilities, and developer automation.

Read the root `AGENTS.md` before changing anything here.

## Script Rules

- Scripts must be idempotent where practical.
- Add `--dry-run` for destructive or bulk-changing scripts.
- Print useful progress and final summaries.
- Never print secrets.
- Never scrape Instagram or download/rehost YouTube audiovisual content.
- YouTube scripts may fetch/store metadata and thumbnails only as allowed by platform policy.
- Prefer environment variables for configuration.
- Include usage comments or `--help` for non-trivial scripts.

## Safety

- For VPS-affecting scripts, default to inspect/report mode.
- For database scripts, require explicit env/config and avoid hardcoded production credentials.

## Current Scripts

- `fetch_youtube_candidates.py` fetches YouTube Data API metadata candidates only.
- `smoke_api.sh` walks the deployed or local API with throwaway test accounts.
- `dev_backend.sh` sets up/runs a local SQLite FastAPI dev backend.
- `build_ios_simulator.sh` builds the SwiftUI app for the iPhone 17 simulator.
- Long-running production ingestion lives in `backend/app/youtube_worker.py`.
