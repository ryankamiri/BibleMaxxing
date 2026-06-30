# BibleMaxxing TailorTom Deployment Plan

Reviewed: 2026-06-30

## Objective

Expose the FastAPI backend at:

- Public base URL: `https://api.tailortom.org/biblemaxxing`
- Versioned API: `https://api.tailortom.org/biblemaxxing/api/v1`
- Health check: `https://api.tailortom.org/biblemaxxing/health`

Do this without breaking the existing TailorTom API that already lives behind
`api.tailortom.org`.

## Current Assumptions

- SSH host: `tailortom`.
- Current Caddy config on VPS: `/opt/tailortom/Caddyfile`.
- Current TailorTom compose on VPS: `/opt/tailortom/docker-compose.yml`.
- Existing TailorTom Caddy currently proxies the default API traffic to
  `api:8000`.
- BibleMaxxing should run as separate containers and should not replace or
  rename the TailorTom `api` service.

## Safe Topology

Use a separate BibleMaxxing Docker Compose project:

- `biblemaxxing-api`: FastAPI app listening on container port `8000`.
- `youtube-worker`: background YouTube Data API metadata ingestion loop.
- `biblemaxxing-db`: Postgres for BibleMaxxing only.
- `biblemaxxing-data`: named volume for that Postgres instance.
- Shared Docker network with TailorTom Caddy for reverse proxy DNS.
- Worker-only outbound Docker network for YouTube Data API requests.

Preferred Caddy behavior:

1. Requests matching `/biblemaxxing` and `/biblemaxxing/*` are routed to
   `biblemaxxing-api:8000`.
2. Caddy does not strip `/biblemaxxing`.
3. FastAPI owns `/biblemaxxing/health` and `/biblemaxxing/api/v1/...` routes.
4. All other `api.tailortom.org` traffic continues to route to TailorTom's
   existing `api:8000`.

This means the backend route shape is identical inside the container and at the
public URL, except for scheme/host.

## Required VPS Preflight

Before changing anything on the VPS:

```bash
ssh tailortom 'hostname && docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"'
ssh tailortom 'ss -ltnp'
ssh tailortom 'sudo sed -n "1,220p" /opt/tailortom/Caddyfile'
ssh tailortom 'sudo sed -n "1,260p" /opt/tailortom/docker-compose.yml'
ssh tailortom 'docker network ls'
```

Record:

- The current Caddy container/service name.
- The Docker network Caddy uses.
- Whether Caddy runs in Docker or on the host.
- The exact fallback reverse proxy that serves TailorTom today.

## Deployment Steps

1. Create a remote app directory:

   ```bash
   ssh tailortom 'sudo mkdir -p /opt/biblemaxxing && sudo chown $USER:$USER /opt/biblemaxxing'
   ```

2. Copy the backend build context and safe examples:

   ```bash
   rsync -av --delete --exclude .venv --exclude __pycache__ backend/ tailortom:/opt/biblemaxxing/backend/
   rsync -av infra/docker-compose.biblemaxxing.example.yml tailortom:/opt/biblemaxxing/docker-compose.yml
   rsync -av infra/biblemaxxing.env.example tailortom:/opt/biblemaxxing/.env.example
   ```

3. On the VPS, create `/opt/biblemaxxing/.env` from `.env.example` and fill in
   real values. Do not commit the real file.

4. Build or publish the backend image. The checked-in compose file builds from
   `/opt/biblemaxxing/backend` by default. If using a registry, set
   `BIBLEMAXXING_API_IMAGE` in `/opt/biblemaxxing/.env`.

5. Start BibleMaxxing services:

   ```bash
   ssh tailortom 'cd /opt/biblemaxxing && docker compose up -d --remove-orphans'
   ssh tailortom 'cd /opt/biblemaxxing && docker compose ps'
   ssh tailortom 'curl -fsS http://127.0.0.1:8017/biblemaxxing/health'
   ```

   The `youtube-worker` service runs one ingestion cycle immediately, then
   sleeps for `BIBLEMAXXING_YOUTUBE_INGEST_INTERVAL_SECONDS` before the next
   cycle. It must be attached to `biblemaxxing-egress`; the private DB network
   is intentionally internal and cannot resolve/reach YouTube.

   A 7200-second cadence is free in dollars but not free in YouTube Data API
   quota. Keep `BIBLEMAXXING_YOUTUBE_INGEST_SEARCH_CALLS_PER_CYCLE` budgeted
   below the daily search-call limit; the default `6` calls every two hours is
   about `72` `search.list` calls per day and rotates both broad discovery and
   pastor/source queries over time.

6. Back up TailorTom Caddy before editing:

   ```bash
   ssh tailortom 'sudo cp /opt/tailortom/Caddyfile /opt/tailortom/Caddyfile.bak.$(date +%Y%m%d-%H%M%S)'
   ```

7. Add the BibleMaxxing route from `infra/Caddyfile.biblemaxxing.example` above
   the existing catch-all TailorTom route.

8. Validate and reload Caddy using the current TailorTom deployment method.
   If Caddy is a container, prefer its existing compose command. If Caddy is a
   host service, use `sudo caddy validate --config /opt/tailortom/Caddyfile`
   and `sudo systemctl reload caddy`.

9. Verify both products:

   ```bash
   curl -fsS https://api.tailortom.org/biblemaxxing/health
   curl -fsS https://api.tailortom.org/
   ```

## Rollback

If the public BibleMaxxing health check fails or TailorTom breaks:

1. Restore the Caddy backup created in step 6.
2. Reload Caddy.
3. Stop only the BibleMaxxing compose project:

   ```bash
   ssh tailortom 'cd /opt/biblemaxxing && docker compose down'
   ```

Do not stop or recreate TailorTom containers as part of the BibleMaxxing
rollback unless Ryan explicitly asks.

## Sources

- Caddy `handle`: https://caddyserver.com/docs/caddyfile/directives/handle
- Caddy `uri`: https://caddyserver.com/docs/caddyfile/directives/uri
- Caddy `reverse_proxy`: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy
- Docker Compose environment variables: https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/
