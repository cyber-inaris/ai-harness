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
curl -I http://127.0.0.1:8080/omniroute/
curl -I https://apps.ss-promotion.com/omniroute/
curl -I -H 'Host: omniroute.ss-promotion.com' http://127.0.0.1:8080/
```

OpenAI-compatible API:

```bash
curl http://127.0.0.1:20128/v1/models \
  -H "Authorization: Bearer ${OMNIROUTE_API_KEY:-sk_omniroute}"
```

The API may return an auth or setup error until providers/API keys are configured. That is acceptable for the first install; the service must still respond.

## Web UI Hostname

OmniRoute's Web UI is a Next.js app and uses root-level paths:

```text
/_next/*
/login
/dashboard
/api/*
```

These conflict with Hermes dashboard paths on `apps.ss-promotion.com`, especially `/api/*`. For this reason the working UI target is:

```text
omniroute.ss-promotion.com
```

Cloudflare Tunnel should route that hostname to the same local nginx origin:

```text
omniroute.ss-promotion.com -> HTTP localhost:8080
```

nginx then selects the `server_name omniroute.ss-promotion.com` block and proxies `/` to `127.0.0.1:20128`.

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
