# Hermes Runtime Setup

Last verified: 2026-05-27

Hermes is installed on the host and configured as the Telegram-facing operational agent for `ai-harness`.

## Runtime

```text
user: ai
binary: /home/ai/.local/bin/hermes
config: /home/ai/.hermes/config.yaml
env: /home/ai/.hermes/.env
persona: /home/ai/.hermes/SOUL.md
working directory: /opt/ai-harness/repo
personality: technical
streaming.enabled: false
browser tools: enabled
```

## Services

```text
hermes-dashboard.service: dashboard on 127.0.0.1:9119
hermes-gateway.service: Telegram gateway
```

Check:

```bash
sudo systemctl status hermes-dashboard hermes-gateway --no-pager
hermes status
hermes gateway status
hermes skills list | grep ai-harness
```

## Model

Hermes uses OmniRoute as an OpenAI-compatible endpoint:

```text
provider: custom
base_url: http://127.0.0.1:20128/v1
model.default: free-mod/gpt-5.5
```

## Telegram

Telegram is configured through `/home/ai/.hermes/.env`:

```text
TELEGRAM_BOT_TOKEN=<secret>
TELEGRAM_ALLOWED_USERS=<allowed user ids>
TELEGRAM_HOME_CHANNEL=<home chat id>
```

Do not commit or print the token.

## Project Skills

Project-specific skills are stored in the repo under:

```text
hermes/skills/ai-harness/
```

They are mirrored to:

```text
/home/ai/.hermes/skills/ai-harness/
```

Current skills:

```text
ai-harness-ops
ask
brainstorm
execute
hermes-vps-admin
notion
omniroute-provider-setup
plan
reseller-benchmark
review
```

## Browser Tools

Playwright Chromium is installed for Hermes:

```text
/home/ai/.cache/ms-playwright/
```

`hermes doctor` should show:

```text
Playwright Chromium: ok
browser: available
```

## Git Access

The server copy at `/opt/ai-harness/repo` is a real git checkout.

Local git operations are available:

```bash
cd /opt/ai-harness/repo
git status --short
git log -1 --oneline
```

GitHub SSH alias is configured for the `ai` user:

```text
Host github-cyber-inaris
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_cyber_inaris
  IdentitiesOnly yes
```

The public key must be added to GitHub before push/pull works:

```bash
cat /home/ai/.ssh/github_cyber_inaris.pub
ssh -T github-cyber-inaris
```
