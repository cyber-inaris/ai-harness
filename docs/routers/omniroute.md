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

## FreeModel Provider

Verified on 2026-05-27:

```text
Provider name: FreeModel
Provider type: OpenAI compatible
Base URL: https://api.freemodel.dev/v1
Dashboard prefix: free-mod
OmniRoute model ids:
  free-mod/gpt-5.5
  free-mod/gpt-5.4
  free-mod/gpt-5.4-mini
  free-mod/gpt-5.3-codex
```

Direct FreeModel `/v1/models` returned these upstream models:

```text
gpt-5.5
gpt-5.4
gpt-5.4-mini
gpt-5.3-codex
```

After adding the provider connection in the OmniRoute dashboard, sync models from the server:

```bash
OMNIROUTE_API_KEY="$(sudo awk -F= '/^OMNIROUTE_API_KEY=/ {print $2}' /opt/ai-harness/secrets/omniroute.env)"

curl -X POST \
  -H "Authorization: Bearer ${OMNIROUTE_API_KEY}" \
  "http://127.0.0.1:20128/api/providers/<connection-id>/sync-models?mode=import"
```

Then verify:

```bash
curl http://127.0.0.1:20128/v1/models \
  -H "Authorization: Bearer ${OMNIROUTE_API_KEY}"

curl http://127.0.0.1:20128/v1/chat/completions \
  -H "Authorization: Bearer ${OMNIROUTE_API_KEY}" \
  -H "Content-Type: application/json" \
  --data '{"model":"free-mod/gpt-5.5","messages":[{"role":"user","content":"Return exactly ok"}],"max_tokens":8}'
```

Use the OpenAI Chat Completions path for agents:

```text
base_url: http://127.0.0.1:20128/v1
model: free-mod/gpt-5.5
```

The direct FreeModel Responses API can work, but OmniRoute's `/v1/responses` path returned `STREAM_EARLY_EOF` during this verification. Keep Hermes and coding agents on `/v1/chat/completions` unless this is retested.

## LightningZeus Provider

Verified on 2026-05-27:

```text
Provider name: LightningZeus
Provider type: OpenAI compatible
Base URL: https://lightningzeus.com/v1
Dashboard prefix: lightningzeus
OmniRoute model ids:
  lightningzeus/claude-opus-4-6
  lightningzeus/claude-opus-4.6
  lightningzeus/cursorlm
```

The local `ai-testing-toolkit` key is stored as:

```text
/Users/alex/Work/GitHub/ai-testing-toolkit/api/.env
LIGHTNINGZEUS_API_KEY
```

Do not copy the key into git. OmniRoute stores the provider connection in its own runtime database after adding it through the API or dashboard.

Direct LightningZeus `/v1/chat/completions` works with both streaming and non-streaming requests. Through OmniRoute, non-streaming requests work:

```bash
curl http://127.0.0.1:20128/v1/chat/completions \
  -H "Authorization: Bearer ${OMNIROUTE_API_KEY}" \
  -H "Content-Type: application/json" \
  --data '{"model":"lightningzeus/claude-opus-4.6","messages":[{"role":"user","content":"Return exactly ok"}],"max_tokens":8,"stream":false}'
```

OmniRoute streaming requests to LightningZeus returned `STREAM_EARLY_EOF` during verification. For agents and benchmarks, set `stream: false` when using LightningZeus through OmniRoute until this is retested or fixed upstream.

Prior local benchmark notes:

```text
claude-opus-4.6 passed 5/5 smoke tests, but reported high token usage.
cursorlm passed 3/5 smoke tests and had weaker model identity signals.
```

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
