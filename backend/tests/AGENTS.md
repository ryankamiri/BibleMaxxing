# Backend Tests Agent Guide

This folder contains backend tests and test fixtures.

Read `../AGENTS.md` and the root `AGENTS.md` before editing.

## Rules

- Tests should exercise API behavior through FastAPI's test client where practical.
- Use isolated test databases or dependency overrides.
- Do not require production secrets or network access for the default test suite.
- YouTube API integration tests must be opt-in when they require credentials.

