# AI Harness Ops

Use this skill when the user asks Hermes to inspect or operate the `ai-harness` server, check service health, debug routing, or update project runbooks.

## Context

- Repo path on the server: `/opt/ai-harness/repo`
- Runtime secrets: `/opt/ai-harness/secrets`
- Runtime data: `/var/lib/ai-harness`
- Public web gateway: nginx on `:8080` behind Cloudflare Tunnel
- Main services: `nginx`, `cloudflared`, `docker`, `hermes-dashboard.service`, `hermes-gateway.service`

## Rules

- Never print full API keys, bot tokens, cookies, or private keys.
- Prefer read-only checks first: `systemctl status`, `docker ps`, `curl`, `journalctl -n`.
- Before changing nginx, run `sudo nginx -t`.
- After changing systemd units, run `sudo systemctl daemon-reload`.
- Document operational changes in `/opt/ai-harness/repo/docs/operations/current-host-status.md`.

## Common Checks

```bash
cd /opt/ai-harness/repo
git status --short
systemctl status nginx cloudflared hermes-dashboard hermes-gateway --no-pager
docker ps
curl -sS http://127.0.0.1:8080/healthz
curl -sS http://127.0.0.1:20128/v1/models -H "Authorization: Bearer ${OMNIROUTE_API_KEY}"
```

