# Agent VPS Setup Runbook

## Purpose

This runbook describes how to configure the VPS so an AI agent such as Hermes can operate the harness.

It assumes the host has already followed:

- [Ubuntu Host Setup Runbook](../vps/ubuntu-setup.md)
- [ngrok + nginx Access Pattern](../networking/ngrok-nginx-auth.md)
- [Hermes Agent On VPS](hermes-agent.md)

The goal is to make the agent useful without losing control of accounts, secrets, routers, and the server itself.

## Target Layout

Use one stable filesystem layout:

```text
/opt/ai-harness/
  repo/                  # git checkout
  config/                # non-secret config
  secrets/               # local secrets, not committed
  docker/                # compose files and overrides
  logs/                  # service logs if not in journald/docker

/var/lib/ai-harness/
  benchmarks/            # benchmark results
  telemetry/             # real request observations
  scores/                # scoring outputs
  agent/                 # agent state if needed

/etc/ai-harness/
  env/                   # systemd env files
  nginx/                 # nginx snippets
```

Create directories:

```bash
sudo mkdir -p /opt/ai-harness/{repo,config,secrets,docker,logs}
sudo mkdir -p /var/lib/ai-harness/{benchmarks,telemetry,scores,agent}
sudo mkdir -p /etc/ai-harness/{env,nginx}
sudo chown -R ai:ai /opt/ai-harness /var/lib/ai-harness /etc/ai-harness
sudo chmod 700 /opt/ai-harness/secrets
```

## Agent User

Use a dedicated `ai` user for the harness.

MVP policy:

```text
ai user has sudo
ai user can use Docker
ai user owns /opt/ai-harness and /var/lib/ai-harness
root login over SSH is disabled
```

This is intentionally permissive for the first version. It lets Hermes help administer the VPS. Later, split permissions into separate users:

```text
ai-admin      # server administration
ai-agent      # Hermes runtime
ai-router     # router services
ai-worker     # benchmark/scoring workers
```

## Secrets Files

Create runtime secret files:

```bash
sudo -u ai touch /opt/ai-harness/secrets/providers.env
sudo -u ai touch /opt/ai-harness/secrets/accounts.env
sudo -u ai touch /opt/ai-harness/secrets/router.env
sudo -u ai touch /opt/ai-harness/secrets/hermes.env
sudo -u ai touch /opt/ai-harness/secrets/ngrok.env
sudo chmod 600 /opt/ai-harness/secrets/*.env
```

Recommended file responsibilities:

```text
providers.env  # LLM provider keys and reseller API keys
accounts.env   # account credentials only when unavoidable
router.env     # router API keys and internal auth
hermes.env     # Hermes provider/gateway settings
ngrok.env      # ngrok token and tunnel settings
```

Do not put secrets in:

```text
git
README files
benchmark result files
nginx logs
shell history
agent prompts
```

## Secret Classification

| Secret | Risk | Preferred handling |
|---|---|---|
| LLM API key | Medium | `providers.env`, revocable provider key |
| Reseller API key | Medium | `providers.env`, tagged by provider |
| Router bearer token | Medium | `router.env`, rotate if leaked |
| Telegram bot token | Medium | `hermes.env`, restrict allowed users |
| Notion integration token | Medium | `accounts.env`, scoped integration only |
| GitHub token | High | Prefer SSH key or fine-grained PAT |
| Browser cookies | High | Avoid if API exists; store separately with short TTL |
| Account login/password | High | Prefer password manager/vault; avoid plain env |
| VPS SSH private key | Critical | Do not give to agent unless absolutely required |

## Hermes Environment

Example `/opt/ai-harness/secrets/hermes.env`:

```env
HERMES_PROVIDER=openai-compatible
HERMES_BASE_URL=https://<ngrok-id>.ngrok-free.app/router/v1
HERMES_MODEL=trusted-admin-model
HERMES_API_KEY=replace-me

TELEGRAM_BOT_TOKEN=replace-me
TELEGRAM_ALLOWED_USER_IDS=123456789
```

If Hermes talks directly to a provider instead of the local router, set provider-specific values there.

Rule:

```text
Admin/high-risk Hermes tasks should use the trusted model, not an unverified reseller model.
```

## Account Access Policy

Give the agent accounts gradually.

Recommended first accounts:

1. Telegram bot for command/chat access.
2. Read/write access to this repo only.
3. Notion integration limited to operational docs.
4. Router API key for reading status and running tests.
5. Reseller API keys only after benchmark/scoring flows are ready.

Avoid giving the agent broad personal accounts at the start.

For each account, record metadata in non-secret config:

```yaml
accounts:
  - id: notion-ops
    type: notion
    secret_env: NOTION_TOKEN
    scope: "ai-harness docs database only"
    risk: medium
    owner: alex

  - id: github-ai-harness
    type: github
    auth: ssh-key
    scope: "cyber-inaris/ai-harness"
    risk: medium
    owner: cyber-inaris
```

## Agent Capabilities

Start with these allowed capabilities:

| Capability | Initial mode |
|---|---|
| Read docs/configs | Allowed |
| Write docs | Allowed |
| Run benchmark scripts | Allowed |
| Read service logs | Allowed |
| Restart harness services | Ask first |
| Edit nginx/router config | Ask first |
| Add reseller account | Ask first |
| Print or reveal secrets | Denied |
| Delete data/backups | Denied unless explicitly approved |

The agent should report what it changed and where.

## Systemd Services

Run long-lived pieces through systemd or Docker Compose.

Possible systemd units:

```text
hermes.service
ngrok-ai-harness.service
ai-harness-worker.service
```

Example service pattern:

```ini
[Unit]
Description=AI Harness Hermes Agent
After=network-online.target
Wants=network-online.target

[Service]
User=ai
WorkingDirectory=/opt/ai-harness/repo
EnvironmentFile=/opt/ai-harness/secrets/hermes.env
ExecStart=/usr/local/bin/hermes run
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Adjust `ExecStart` after confirming the real Hermes runtime command on the VPS.

## Docker Compose Role

Use Docker Compose for services that are not host administration:

```text
router
benchmark runner
telemetry database
score dashboard
optional web UI
```

Keep these on the host:

```text
ssh
nginx
ngrok
xrdp
cockpit
docker
hermes if the installer expects host-level operation
```

If Hermes supports Docker cleanly in the chosen setup, it can move to Compose later.

## First Boot Checklist

After the agent is installed:

```bash
whoami
pwd
hostname
systemctl status ssh --no-pager
systemctl status nginx --no-pager
ls -la /opt/ai-harness
ls -la /opt/ai-harness/secrets
```

Check Hermes:

```bash
which hermes
hermes --help
hermes config list
```

Check routing/auth:

```bash
curl -I http://127.0.0.1:8080/hermes/
curl -I http://127.0.0.1:8080/router/
```

Check ngrok URL from a local machine:

```bash
curl -I -u "$AI_HARNESS_USER:$AI_HARNESS_PASSWORD" \
  https://<ngrok-id>.ngrok-free.app/hermes/
```

## Agent Smoke Task

The first safe task for Hermes:

```text
Read /opt/ai-harness/repo/docs/overview.md.
Summarize the current harness purpose.
List which services are running.
Do not edit files.
Do not print secrets.
```

The second safe task:

```text
Create a benchmark run note in /var/lib/ai-harness/benchmarks/manual-smoke-<date>.md.
Include service status, model provider configured, and any missing setup steps.
Do not include API keys or tokens.
```

## Agent Operating Rules

Every agent operating this VPS should follow these rules:

1. Never print full secrets.
2. Never commit `.env`, cookies, tokens, or account exports.
3. Confirm before changing nginx, router policy, SSH, firewall, or secrets.
4. Confirm before adding a new provider/account.
5. Confirm before running high-cost benchmark suites.
6. Write benchmark outputs to `/var/lib/ai-harness/benchmarks`.
7. Write docs/runbooks to `/opt/ai-harness/repo/docs`.
8. Report exact commands when a setup step fails.
9. Prefer reversible changes.
10. Leave a short action summary after every admin task.

## Next Documents To Add

Useful follow-up docs:

```text
docs/accounts/secrets-storage.md
docs/agents/hermes-skills.md
docs/docker/docker-compose-layout.md
docs/routers/omni-router.md
docs/benchmarks/benchmark-runner.md
```
