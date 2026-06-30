# Infra Assets

This folder contains safe, env-based deployment helpers for the overnight
BibleMaxxing build.

## Files

- `deployment-plan.md`: target topology, preflight, deploy, verify, and rollback
  steps for `https://api.tailortom.org/biblemaxxing`.
- `docker-compose.biblemaxxing.example.yml`: separate BibleMaxxing API and
  Postgres services.
- `Caddyfile.biblemaxxing.example`: path route to insert above TailorTom's
  existing catch-all route.
- `biblemaxxing.env.example`: secret-free environment template.
- `deploy-tailortom.sh`: guarded preflight/sync/health helper. It requires
  `BIBLEMAXXING_CONFIRM_DEPLOY=1` before syncing files to the VPS and does not
  patch live Caddy automatically.

## Non-Negotiables

- Keep TailorTom's existing `api.tailortom.org` behavior working.
- Store real secrets only in `/opt/biblemaxxing/.env` or the deployment secret
  manager, never in git.
- Use official YouTube embed playback only. Do not serve downloaded media.
- Back up `/opt/tailortom/Caddyfile` before any live Caddy edit.
- Do not strip `/biblemaxxing` in Caddy; the FastAPI app owns that prefix.
