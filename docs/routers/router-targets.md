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
  public UI:  https://apps.ss-promotion.com/omniroute/

Generic router path:
  public: https://apps.ss-promotion.com/router/
```

Cloudflare should expose one HTTP hostname for the MVP:

```text
apps.ss-promotion.com -> Cloudflare Tunnel -> http://localhost:8080 -> nginx
```

nginx owns service routing behind that single hostname. OmniRoute is a Next.js app that expects root paths such as `/_next`, `/login`, `/dashboard`, and `/api/*`, so the nginx config rewrites those paths under `/omniroute/`.

Dedicated hostnames remain a fallback if an upstream UI update breaks path rewriting, but they are not part of the MVP routing policy.

## Adding More Routers

Do not add a Cloudflare Tunnel hostname for every router during the MVP. Add nginx path routes behind the existing `apps.ss-promotion.com` gateway.

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
