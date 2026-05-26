# nginx

Reverse proxy templates and notes. Admin services should be private by default and reached through SSH tunnels, Tailscale, or app-level auth unless explicitly hardened.

## Files

- `ai-harness.conf` - MVP gateway config for local nginx.

## MVP Routing

The host exposes one nginx gateway on ports `80` and `8080`.

```text
/healthz      -> nginx health check
/hermes/      -> 127.0.0.1:9119
/router/      -> 127.0.0.1:20128
/omniroute/   -> 127.0.0.1:20128
/v1/          -> 127.0.0.1:20128/v1
/benchmarks/  -> 127.0.0.1:5000
/cockpit/     -> 127.0.0.1:9090
/webhooks/    -> 127.0.0.1:7000
```

Cloudflare Tunnel or ngrok should point at `http://localhost:8080`.

## Hermes Dashboard Caveat

Hermes dashboard currently emits absolute root paths (`/assets/...`, `/api/...`, etc.). The MVP config proxies those root paths to Hermes so the dashboard works under:

```text
https://apps.ss-promotion.com/hermes/
```

If this conflicts with other applications, move Hermes to a dedicated hostname and proxy `/` there.

## Router Target

The first router target is OmniRoute on `127.0.0.1:20128`.

Use:

```text
/omniroute/ for dashboard access
/router/    as the generic current router path
/v1/        as the OpenAI-compatible API path
```

OmniRoute currently runs under the shared web hostname:

```text
https://apps.ss-promotion.com/omniroute/ -> nginx :8080 -> 127.0.0.1:20128
```

The OmniRoute dashboard uses root paths like `/_next`, `/login`, `/dashboard`, and `/api/*`, so nginx rewrites those paths under `/omniroute/`. This keeps Cloudflare simple: one HTTP hostname points to nginx, and nginx owns the internal service map.

The config also keeps a narrow set of root compatibility routes for browser-managed OmniRoute assets and first-login setup:

```text
/_next/*
/manifest.webmanifest
/favicon.svg
/icon-*
/apple-touch-icon.png
/home
/api/settings/require-login
```

Avoid broad root `/api/*` proxying to OmniRoute because Hermes currently owns several root dashboard API paths on the same hostname.

For future routers, add a new nginx path block instead of a new Cloudflare Tunnel hostname unless the upstream UI cannot be made path-safe:

```text
/router-name/ -> router dashboard
/router-name/v1/ or /v1-router-name/ -> router API if needed
/v1/ -> currently selected default OpenAI-compatible API
```
