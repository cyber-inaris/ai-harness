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

Cloudflare should expose one shared HTTP hostname for generic apps and API traffic:

```text
apps.ss-promotion.com -> Cloudflare Tunnel -> http://localhost:8080 -> nginx
```

Some web dashboards need their own hostname because they assume root-level paths. OmniRoute is one of them: its Next.js UI navigates to `/_next`, `/login`, `/dashboard`, `/home`, and `/api/*`. Path-mounting it under `/omniroute/` conflicts with Hermes and breaks after login.

For OmniRoute, add a second Cloudflare public hostname that still points to the same local nginx origin:

```text
omniroute.ss-promotion.com -> Cloudflare Tunnel -> http://localhost:8080 -> nginx
```

## Adding More Routers

Default to nginx path routes behind `apps.ss-promotion.com` for APIs and simple dashboards. Use a dedicated hostname only when the upstream UI requires root paths or cannot be made path-safe.

Recommended pattern:

```text
/omniroute/       -> OmniRoute dashboard
/router-cockpit/  -> Cockpit-style router dashboard, if added
/router-name/     -> another router dashboard

/v1/              -> default active OpenAI-compatible router
/v1-omniroute/    -> direct OmniRoute API, if parallel testing needs it
/v1-router-name/  -> direct API for another router, if needed
```

Use `/v1/` as the stable endpoint for agents. Switch its upstream when the chosen default router changes. Keep router-specific API paths only for testing, fallback, and benchmarks.

Hostname rule:

```text
Simple service or API: apps.ss-promotion.com/path/
Root-assuming dashboard: service.ss-promotion.com/
```
