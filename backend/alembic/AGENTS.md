# Alembic Agent Guide

This folder contains database migration configuration and migration scripts.

Read `../AGENTS.md` and the root `AGENTS.md` before editing.

## Rules

- Keep migrations compatible with Postgres.
- Avoid destructive migrations without a clear rollback or explicit user approval.
- Do not put credentials in migration files.

