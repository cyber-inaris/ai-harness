# nginx

Reverse proxy templates and notes. Admin services should be private by default and reached through SSH tunnels, Tailscale, or app-level auth unless explicitly hardened.

## Files

- `ai-harness.conf` - MVP gateway config for local nginx.

## MVP Routing

The host exposes one nginx gateway on ports `80` and `8080`.

```text
apps.ss-promotion.com/healthz       -> nginx health check
apps.ss-promotion.com/hermes/       -> 127.0.0.1:9119
apps.ss-promotion.com/router/       -> 127.0.0.1:20128
apps.ss-promotion.com/omniroute/    -> redirect to omniroute.ss-promotion.com
apps.ss-promotion.com/v1/           -> 127.0.0.1:20128/v1
apps.ss-promotion.com/benchmarks/   -> 127.0.0.1:5000
apps.ss-promotion.com/cockpit/      -> 127.0.0.1:9090
apps.ss-promotion.com/webhooks/     -> 127.0.0.1:7000

hermes.ss-promotion.com/            -> 127.0.0.1:9119
omniroute.ss-promotion.com/         -> 127.0.0.1:20128
benchmark.ss-promotion.com/         -> 127.0.0.1:5000
benchmarks.ss-promotion.com/        -> 127.0.0.1:5000
```

Cloudflare Tunnel or ngrok should point HTTP hostnames at `http://localhost:8080`.

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
/omniroute/ redirects to the dedicated dashboard hostname
/router/    as the generic current router path
/v1/        as the OpenAI-compatible API path
```

OmniRoute UI uses a dedicated hostname:

```text
https://omniroute.ss-promotion.com/ -> nginx :8080 -> 127.0.0.1:20128
```

Reason: the OmniRoute dashboard uses root paths like `/_next`, `/login`, `/dashboard`, `/home`, and `/api/*`. When path-mounted under `apps.ss-promotion.com/omniroute/`, post-login navigation can land on Hermes routes. The dedicated hostname lets OmniRoute own `/`.

Cloudflare Tunnel should have both public hostnames pointing to the same local origin:

```text
apps.ss-promotion.com      -> HTTP localhost:8080
hermes.ss-promotion.com    -> HTTP localhost:8080
omniroute.ss-promotion.com -> HTTP localhost:8080
benchmark.ss-promotion.com -> HTTP localhost:8080
```

For future routers, add a new nginx path block when the UI is path-safe. Use a dedicated hostname when the upstream app assumes root paths:

```text
/router-name/ -> router dashboard
/router-name/v1/ or /v1-router-name/ -> router API if needed
/v1/ -> currently selected default OpenAI-compatible API
```
