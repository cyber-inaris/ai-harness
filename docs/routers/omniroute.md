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
https://apps.ss-promotion.com/omniroute/
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
curl -I http://127.0.0.1:8080/omniroute/
curl -I https://apps.ss-promotion.com/omniroute/
```

OpenAI-compatible API:

```bash
curl http://127.0.0.1:20128/v1/models \
  -H "Authorization: Bearer ${OMNIROUTE_API_KEY:-sk_omniroute}"
```

The API may return an auth or setup error until providers/API keys are configured. That is acceptable for the first install; the service must still respond.

## Web UI Path Routing

OmniRoute's Web UI is a Next.js app and uses root-level paths:

```text
/_next/*
/login
/dashboard
/api/*
```

The MVP exposes only one public HTTP hostname:

```text
apps.ss-promotion.com -> Cloudflare Tunnel -> HTTP localhost:8080 -> nginx
```

nginx then maps OmniRoute under:

```text
https://apps.ss-promotion.com/omniroute/
```

The nginx config rewrites OmniRoute's root-level Next.js asset, dashboard, login, and API paths so they stay under `/omniroute/`.

This is more fragile than a dedicated hostname because it depends on upstream HTML/JavaScript path shapes. If OmniRoute changes its frontend output and the dashboard breaks, first update `ops/nginx/ai-harness.conf`; only add a dedicated hostname if path rewriting becomes too expensive to maintain.

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
