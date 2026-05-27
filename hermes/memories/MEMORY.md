# AI Harness Operational Memory

- The main repository is `/opt/ai-harness/repo`.
- The service user is `ai`; it has passwordless sudo for the MVP host.
- Primary SSH/admin access is through Tailscale using the `ai-harness-ts` client alias.
- Public web ingress goes through Cloudflare Tunnel to local nginx on `localhost:8080`.
- OmniRoute is the model router at `http://127.0.0.1:20128`; the public UI is `https://omniroute.ss-promotion.com/`.
- Hermes dashboard is served locally at `http://127.0.0.1:9119`; public UI is `https://hermes.ss-promotion.com/`.
- Hermes Telegram gateway runs as `hermes-gateway.service`.
- Hermes dashboard runs as `hermes-dashboard.service`.
- Current Hermes default model route is `Hermes -> OmniRoute -> free-mod/gpt-5.5`.
- FreeModel and LightningZeus providers are configured in OmniRoute; do not assume claimed model identity without benchmark evidence.
- LightningZeus through OmniRoute should use `stream:false` until streaming is retested.
- Do not print or store raw API keys, Telegram tokens, cookies, OAuth tokens, private keys, or router passwords in repo files or chat responses.
- Before changing infrastructure, inspect current state first with service status, logs, and local health checks.
- For long-running or multi-agent tasks, prefer writing artifacts under `/var/lib/ai-harness/agent/tasks` and summarizing the path back to Telegram.
- For repo changes, update docs/runbooks when operational behavior changes.
