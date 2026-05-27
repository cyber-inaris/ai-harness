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

Public hostnames:

```text
https://apps.ss-promotion.com
https://hermes.ss-promotion.com
https://omniroute.ss-promotion.com
https://benchmark.ss-promotion.com
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
https://hermes.ss-promotion.com/
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
hermes.ss-promotion.com    -> HTTP localhost:8080
omniroute.ss-promotion.com -> HTTP localhost:8080
benchmark.ss-promotion.com -> HTTP localhost:8080
```

OmniRoute uses root-level Next.js paths such as `/_next`, `/login`, `/dashboard`, `/home`, and `/api/*`. It should own `/` on `omniroute.ss-promotion.com`; path routing under `apps.ss-promotion.com/omniroute/` is only a redirect fallback.

Benchmark hostname currently routes to `127.0.0.1:5000`. It returns `502` until a benchmark UI/API service is started on that port.

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

## Laptop Power Policy

Last verified: 2026-05-27

The current host is a laptop on Wi-Fi. Screen blanking settings are not enough
for an always-on agent server: GNOME can still suspend the machine on battery,
and suspend drops Wi-Fi, Tailscale, SSH, Cloudflare Tunnel, and running agents.

Current policy:

```text
systemd sleep/suspend/hibernate targets: masked
logind lid switch: ignore
GNOME AC idle action: nothing
GNOME battery idle action: nothing
GNOME lid close action: nothing
NetworkManager Wi-Fi power save: disabled by override
```

Apply or re-apply the policy:

```bash
sudo /opt/ai-harness/repo/scripts/disable-laptop-sleep.sh
```

For GNOME settings, the script defaults to `GUI_USER=dima`. Override it when the
desktop session belongs to a different user:

```bash
sudo GUI_USER=alice /opt/ai-harness/repo/scripts/disable-laptop-sleep.sh
```

Verification commands:

```bash
systemctl status sleep.target suspend.target hibernate.target hybrid-sleep.target --no-pager
sudo -u dima DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
  gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type
grep -R "wifi.powersave" /etc/NetworkManager/conf.d
```

## OmniRoute Provider State

Last verified: 2026-05-27

FreeModel is configured as an OpenAI-compatible provider in OmniRoute:

```text
provider: FreeModel
prefix: free-mod
base_url: https://api.freemodel.dev/v1
connection: TestKey
status: active
```

Imported OmniRoute model ids:

```text
free-mod/gpt-5.5
free-mod/gpt-5.4
free-mod/gpt-5.4-mini
free-mod/gpt-5.3-codex
```

Verified path:

```text
Hermes -> http://127.0.0.1:20128/v1 -> OmniRoute -> FreeModel
```

Hermes model config:

```text
provider: custom
base_url: http://127.0.0.1:20128/v1
model.default: free-mod/gpt-5.5
```

LightningZeus is also configured in OmniRoute:

```text
provider: LightningZeus
prefix: lightningzeus
base_url: https://lightningzeus.com/v1
connection: TestKey
status: active
```

Imported LightningZeus model ids:

```text
lightningzeus/claude-opus-4-6
lightningzeus/claude-opus-4.6
lightningzeus/cursorlm
```

Use `stream: false` for LightningZeus through OmniRoute. Streaming requests returned `STREAM_EARLY_EOF` during verification.

## Hermes Runtime State

Last verified: 2026-05-27

Hermes is configured as the Telegram-facing operational agent for this host:

```text
dashboard service: hermes-dashboard.service
gateway service: hermes-gateway.service
telegram: configured for the allowed user only
personality: technical
terminal cwd: /opt/ai-harness/repo
streaming.enabled: false
browser tools: enabled
git checkout: /opt/ai-harness/repo
```

Project-specific Hermes files:

```text
repo persona: hermes/SOUL.md
runtime persona: /home/ai/.hermes/SOUL.md
repo skills: hermes/skills/ai-harness/
runtime skills: /home/ai/.hermes/skills/ai-harness/
```

Enabled local project skills:

```text
ai-harness-ops
omniroute-provider-setup
reseller-benchmark
hermes-vps-admin
```

Telegram secrets are stored only in:

```text
/home/ai/.hermes/.env
```

Do not print or commit the Telegram bot token.

GitHub SSH key for the server has been generated at:

```text
/home/ai/.ssh/github_cyber_inaris
/home/ai/.ssh/github_cyber_inaris.pub
```

Push/pull remains pending until the public key is added to GitHub.
