# Hermes Current Setup

Last verified: 2026-05-26

## Installed State

Hermes is installed for the `ai` user:

```text
Command: /home/ai/.local/bin/hermes
Code:    /home/ai/.hermes/hermes-agent
Config:  /home/ai/.hermes/config.yaml
Env:     /home/ai/.hermes/.env
Skills:  /home/ai/.hermes/skills
```

Installed version reported by package install:

```text
hermes-agent 0.14.0
```

The installer was run with:

```bash
--skip-browser
```

So Playwright Chromium is not installed yet. Browser tools can be enabled later:

```bash
cd /home/ai/.hermes/hermes-agent
npx playwright install chromium
sudo npx playwright install-deps chromium
```

## Dashboard

Dashboard systemd service:

```text
/etc/systemd/system/hermes-dashboard.service
/opt/ai-harness/repo/ops/systemd/hermes-dashboard.service
```

Commands:

```bash
sudo systemctl status hermes-dashboard --no-pager
sudo systemctl restart hermes-dashboard
sudo journalctl -u hermes-dashboard -f
```

Local dashboard:

```text
http://127.0.0.1:9119
```

Public route through nginx/Cloudflare:

```text
https://apps.ss-promotion.com/hermes/
```

nginx proxies `/hermes/` to:

```text
http://127.0.0.1:9119/
```

Important: the Hermes dashboard currently emits absolute root URLs such as `/assets/...` and `/api/...`. The nginx config therefore reserves these root paths for Hermes dashboard compatibility:

```text
/assets/
/favicon.ico
/api/
/chat
/config
/analytics
/sessions
/tools
/cron
/plugins
/profiles
/logs
/model
/gateway
/skills
/dashboard
/pty
```

If these collide with future apps, move Hermes to a dedicated hostname such as `hermes.ss-promotion.com`.

Cloudflare may cache early 404 responses for hashed dashboard assets. The current nginx config rewrites the dashboard HTML to append a cache-busting query string to the initial JS/CSS asset URLs. If Hermes dashboard updates and the asset filenames change, update `ops/nginx/ai-harness.conf` or purge Cloudflare cache.

## Current Hermes Status

Expected before interactive setup:

```text
API keys: not configured
Telegram: not configured
Gateway service: stopped
Playwright Chromium: not installed
Dashboard: running
```

These are not installation failures. They are the next configuration steps.

## Required Interactive Setup

Run as `ai`:

```bash
sudo -iu ai
hermes setup
```

Configure at minimum:

```text
LLM provider or OAuth provider
default model
Telegram or another messaging gateway, if needed
```

After setup:

```bash
hermes status
hermes doctor
hermes gateway setup
hermes gateway install
hermes gateway start
```

## Notes

- Do not paste provider keys into git-tracked files.
- Prefer Hermes' own `~/.hermes/.env` for Hermes runtime keys.
- Mirror non-secret provider metadata into `/opt/ai-harness/config`.
- Keep benchmark/scoring decisions in this repository, not only inside Hermes sessions.
