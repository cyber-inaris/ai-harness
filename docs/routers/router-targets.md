# Router Targets

`ai-harness` is router-neutral. It owns install scripts, Docker Compose files, nginx routes, health checks, benchmark hooks, and docs around router tools.

## Supported Targets

| Target | Status | Purpose |
|---|---|---|
| OmniRoute | First supported target | OpenAI-compatible gateway with dashboard, provider routing, fallback, and coding-agent integrations |
| Cockpit tools | Planned experiment | Alternative UI/control plane to evaluate after OmniRoute is stable |

## Common Contract

Every router target should provide:

```text
install script
Docker Compose or systemd runtime
localhost-only bind
nginx route
health check
OpenAI-compatible base URL if available
secrets/env example
backup notes
benchmark integration notes
```

## Current Routing Policy

For the MVP:

```text
OmniRoute UI/API:
  local:  http://127.0.0.1:20128
  API:    http://127.0.0.1:20128/v1
  public API: https://apps.ss-promotion.com/v1
  public UI:  https://omniroute.ss-promotion.com/

Generic router path:
  public: https://apps.ss-promotion.com/router/
```

If a router dashboard requires root-level assets or WebSocket paths that conflict with Hermes, prefer a dedicated hostname:

```text
omniroute.ss-promotion.com -> Cloudflare Tunnel -> http://localhost:8080 -> nginx -> http://localhost:20128
cockpit.ss-promotion.com   -> cockpit service
```

OmniRoute already needs the dedicated-hostname pattern because its Web UI uses root paths such as `/_next`, `/login`, `/dashboard`, and `/api/*`.
