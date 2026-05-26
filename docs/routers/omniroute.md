# OmniRoute Router Target

## Purpose

OmniRoute is the first router target for `ai-harness`.

It gives the harness a local OpenAI-compatible endpoint for coding agents and later benchmarks:

```text
http://127.0.0.1:20128/v1
```

Public dashboard/API routing goes through the existing Cloudflare/nginx gateway:

```text
https://apps.ss-promotion.com/v1/
https://omniroute.ss-promotion.com/
```

## Upstream References

- GitHub: https://github.com/diegosouzapw/OmniRoute
- Docker image: https://hub.docker.com/r/diegosouzapw/omniroute

The upstream Docker image is:

```text
diegosouzapw/omniroute:latest
```

Upstream docs describe the local API endpoint as:

```text
http://localhost:20128/v1
```

## Host Layout

Runtime files:

```text
/opt/ai-harness/docker/omniroute.compose.yml
/opt/ai-harness/secrets/omniroute.env
/var/lib/ai-harness/router/omniroute
```

Repo templates:

```text
docker/omniroute.compose.yml
configs/examples/omniroute.env.example
scripts/install-omniroute.sh
ops/nginx/ai-harness.conf
```

## Install

From the server:

```bash
sudo /opt/ai-harness/repo/scripts/install-omniroute.sh
```

The script:

```text
creates runtime directories
copies compose/env templates
starts the Docker Compose service
updates nginx from repo template
verifies local HTTP
```

## Verify

Container:

```bash
docker ps --filter name=omniroute
docker compose -f /opt/ai-harness/docker/omniroute.compose.yml ps
```

Local HTTP:

```bash
curl -I http://127.0.0.1:20128/
curl -I http://127.0.0.1:20128/v1/models
```

Gateway:

```bash
curl -I -H 'Host: omniroute.ss-promotion.com' http://127.0.0.1:8080/
curl -I https://omniroute.ss-promotion.com/
curl -I https://omniroute.ss-promotion.com/dashboard
curl -I https://omniroute.ss-promotion.com/_next/static/chunks/webpack-63849d10ecdf4bd8.js
```

OpenAI-compatible API:

```bash
curl http://127.0.0.1:20128/v1/models \
  -H "Authorization: Bearer ${OMNIROUTE_API_KEY:-sk_omniroute}"
```

The API may return an auth or setup error until providers/API keys are configured. That is acceptable for the first install; the service must still respond.

## First Login

If the login endpoint returns this response:

```json
{"error":"No password configured. Complete onboarding first.","needsSetup":true}
```

set the initial dashboard password through OmniRoute's setup endpoint from the server:

```bash
curl -X POST http://127.0.0.1:20128/api/settings/require-login \
  -H "Content-Type: application/json" \
  --data '{"requireLogin":true,"password":"CHANGEME"}'
```

Then log in at:

```text
https://omniroute.ss-promotion.com/
```

Change the temporary password immediately in the OmniRoute settings.

## Web UI Hostname Routing

OmniRoute's Web UI is a Next.js app and uses root-level paths:

```text
/_next/*
/login
/dashboard
/api/*
```

Path routing under `apps.ss-promotion.com/omniroute/` was tested and rejected because the UI redirects to root-level `/dashboard` and `/home` after login. On the shared hostname those paths belong to Hermes, so the user can be pushed into the wrong app.

Use a dedicated UI hostname:

```text
omniroute.ss-promotion.com -> Cloudflare Tunnel -> HTTP localhost:8080 -> nginx -> http://127.0.0.1:20128
```

Keep the OpenAI-compatible API on the shared apps hostname:

```text
https://apps.ss-promotion.com/v1/
```

The legacy shared path redirects to the dedicated hostname:

```text
https://apps.ss-promotion.com/omniroute/... -> https://omniroute.ss-promotion.com/...
```

In Cloudflare Tunnel, add the public hostname:

```text
Subdomain: omniroute
Domain: ss-promotion.com
Path: empty
Type: HTTP
URL: localhost:8080
```

## Secrets

Do not commit real OmniRoute keys or provider credentials.

Use:

```text
/opt/ai-harness/secrets/omniroute.env
```

Non-secret provider metadata belongs in:

```text
/opt/ai-harness/config/
configs/examples/
```

## Future Benchmark Hook

Benchmarks should target OmniRoute through:

```text
base_url: http://127.0.0.1:20128/v1
api_key_env: OMNIROUTE_API_KEY
```

This lets the same benchmark runner compare:

```text
direct reseller API
OmniRoute route
future Cockpit route
```
