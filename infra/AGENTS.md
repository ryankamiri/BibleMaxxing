# Infra Agent Guide

This folder owns deployment, Docker, Caddy, VPS notes, environment examples, and operational scripts.

Read the root `AGENTS.md` before changing anything here.

## Target Host

- SSH host: `tailortom`.
- Hostname observed: `tailortom-small`.
- Public IP observed: `167.71.165.199`.
- Current public API domain: `api.tailortom.org`.
- DNS is Vercel-managed.
- Existing Caddy config lives at `/opt/tailortom/Caddyfile` on the VPS.
- Existing TailorTom Docker compose lives at `/opt/tailortom/docker-compose.yml`.

## Deployment Rule

Do not break TailorTom.

The safest BibleMaxxing deployment path is:

- Keep TailorTom's existing `api.tailortom.org { reverse_proxy api:8000 }` behavior working.
- Add a path route for BibleMaxxing under `https://api.tailortom.org/biblemaxxing`.
- Prefer separate BibleMaxxing containers/services and a separate database/schema where practical.
- Keep the YouTube metadata worker attached to a non-internal egress network;
  the private DB network is intentionally unable to reach public APIs.

## Ops Practices

- Before changing VPS routing, inspect `docker ps`, `ss -ltnp`, and the current Caddyfile.
- Back up Caddyfile/compose files before editing on the VPS.
- Use Docker health checks.
- Use env files for secrets and never commit real env values.
- Keep deployment commands repeatable and documented.
- Keep `deployment-plan.md`, `docker-compose.biblemaxxing.example.yml`, `Caddyfile.biblemaxxing.example`, and `biblemaxxing.env.example` in sync with the live deployment shape.
- Helper scripts must be guarded, explicit, and safe for a shared TailorTom VPS; do not auto-patch live Caddy unless Ryan asks.
