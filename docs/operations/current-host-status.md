# Current Host Status

Last verified: 2026-05-26

## Access

Primary SSH access:

```bash
ssh ai-harness-ts
```

Resolved path:

```text
Mac -> Tailscale -> ai@100.105.206.54
```

The `ai` user has:

```text
groups: ai, sudo, users, docker
sudo: passwordless sudo verified
```

## Services

Verified active:

```text
ssh
nginx
docker
xrdp
tailscaled
cloudflared
hermes-dashboard
```

Listening ports:

```text
22    SSH
80    nginx
8080  nginx, intended Cloudflare/ngrok origin
3389  xrdp
9119  Hermes dashboard on 127.0.0.1 only
20128 OmniRoute on 127.0.0.1 only
```

## Web Gateway

Public hostname:

```text
https://apps.ss-promotion.com
```

Current checks:

```bash
curl https://apps.ss-promotion.com/healthz
# ai-harness ok

curl https://apps.ss-promotion.com/
# ai-harness gateway
```

Cloudflare points web traffic to:

```text
http://localhost:8080
```

nginx routes are defined in:

```text
/etc/nginx/sites-available/ai-harness
/opt/ai-harness/repo/ops/nginx/ai-harness.conf
```

Hermes dashboard route:

```text
https://apps.ss-promotion.com/hermes/
  -> Cloudflare Tunnel
  -> nginx :8080
  -> http://127.0.0.1:9119/
```

The dashboard also uses root-level `/assets/*` and `/api/*` paths, so nginx currently proxies those root paths to Hermes as well. Move Hermes to a dedicated hostname if that becomes a conflict.

OmniRoute route:

```text
https://omniroute.ss-promotion.com/
  -> Cloudflare Tunnel
  -> nginx :8080
  -> http://127.0.0.1:20128/

https://apps.ss-promotion.com/v1/
  -> Cloudflare Tunnel
  -> nginx :8080
  -> http://127.0.0.1:20128/v1/
```

Cloudflare needs these web hostnames pointing to the same origin:

```text
apps.ss-promotion.com      -> HTTP localhost:8080
omniroute.ss-promotion.com -> HTTP localhost:8080
```

OmniRoute uses root-level Next.js paths such as `/_next`, `/login`, `/dashboard`, `/home`, and `/api/*`. It should own `/` on `omniroute.ss-promotion.com`; path routing under `apps.ss-promotion.com/omniroute/` is only a redirect fallback.

## Host Layout

Runtime directories:

```text
/opt/ai-harness/repo
/opt/ai-harness/config
/opt/ai-harness/docker
/opt/ai-harness/logs
/opt/ai-harness/secrets
/var/lib/ai-harness/benchmarks
/var/lib/ai-harness/telemetry
/var/lib/ai-harness/scores
/var/lib/ai-harness/router
/var/lib/ai-harness/agent
/etc/ai-harness/env
/etc/ai-harness/nginx
```

Secret env files:

```text
/opt/ai-harness/secrets/accounts.env
/opt/ai-harness/secrets/cloudflare.env
/opt/ai-harness/secrets/hermes.env
/opt/ai-harness/secrets/ngrok.env
/opt/ai-harness/secrets/providers.env
/opt/ai-harness/secrets/router.env
```

`/opt/ai-harness/secrets` is `700`; env files are `600`.

## Deployment Command

From the repository root on the host:

```bash
sudo /opt/ai-harness/repo/scripts/deploy-host.sh
```

The script is idempotent for the MVP setup: packages, directories, secret file placeholders, nginx config, and service restarts.

## Known Decisions

- Use Tailscale for SSH/admin instead of Cloudflare SSH.
- Use Cloudflare Tunnel for public web ingress.
- Use nginx as the single local gateway.
- Keep real secrets out of git and under `/opt/ai-harness/secrets`.
- Keep Docker service images disabled/placeholders until router/benchmark images are final.
- Run Hermes dashboard as a host-level systemd service for now.
- Run OmniRoute as the first Docker Compose router target.
