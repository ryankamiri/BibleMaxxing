# Alembic Versions Agent Guide

This folder contains Alembic revision files.

Read `../../AGENTS.md` and the root `AGENTS.md` before editing.

## Rules

- Name revisions clearly.
- Keep schema changes in sync with SQLAlchemy models.
- The initial revision creates tables from current SQLAlchemy metadata. New
  additive table migrations should tolerate the table already existing so fresh
  databases and already-migrated databases both upgrade cleanly.
- Do not include secrets or environment-specific values.
