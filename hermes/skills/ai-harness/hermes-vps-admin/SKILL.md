# Hermes VPS Admin

Use this skill when the user asks Hermes to administer its host, configure Telegram, manage systemd services, or inspect Hermes runtime.

## Context

- Hermes binary: `/home/ai/.local/bin/hermes`
- Hermes config: `/home/ai/.hermes/config.yaml`
- Hermes env: `/home/ai/.hermes/.env`
- Hermes persona: `/home/ai/.hermes/SOUL.md`
- Dashboard service: `hermes-dashboard.service`
- Telegram gateway service: `hermes-gateway.service`

## Safety

- Do not print Telegram bot tokens or LLM API keys.
- Ask before destructive operations such as deleting data directories, rotating credentials, or disabling access.
- Use `sudo` only when required.
- Prefer service-specific restarts over rebooting the host.

## Useful Commands

```bash
hermes status
hermes doctor
hermes config show
hermes gateway status
sudo systemctl status hermes-dashboard hermes-gateway --no-pager
sudo journalctl -u hermes-gateway -n 100 --no-pager
```

## Current Defaults

```text
provider: custom
base_url: http://127.0.0.1:20128/v1
default model: free-mod/gpt-5.5
telegram: enabled for the allowed user only
terminal backend: local
working directory: /opt/ai-harness/repo
```

