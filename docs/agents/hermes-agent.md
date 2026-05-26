# Hermes Agent On VPS

## Purpose

Hermes is planned as the always-on personal AI agent layer for this harness. It can live on a VPS, connect to messaging gateways, use tools, learn reusable skills, and operate against configured LLM providers.

This repository should not blindly copy the full Hermes setup. It should keep a maintained runbook for installing Hermes, deciding how much server access to give it, connecting personal accounts, and validating LLM providers with benchmarks.

## References

Primary references:

| Resource | Link | Use |
|---|---|---|
| Habr VPS guide | https://habr.com/ru/articles/1032656/ | Practical Russian walkthrough: VPS, Hermes, provider selection, Telegram gateway, skills, security tradeoffs |
| Official installation docs | https://hermes-agent.nousresearch.com/docs/getting-started/installation | Current install command and supported platforms |
| Official GitHub repo | https://github.com/NousResearch/hermes-agent | Source, issues, latest project state |
| Official product page | https://nousresearch.com/hermes-agent/ | High-level feature overview |

Do not freeze install commands from blog posts. Before installing on a real VPS, check the official installation docs or GitHub README because Hermes changes quickly.

## VPS Baseline

Recommended baseline for experiments:

```text
OS: Ubuntu Server 24.04 LTS
CPU: 1-2 vCPU minimum
RAM: 2 GB minimum, 4 GB preferred
Disk: 20 GB minimum, 40+ GB preferred
Network: stable EU location, good outbound connectivity
Access: SSH key auth
Optional UI: XFCE + xrdp, Cockpit over SSH tunnel
```

Hermes itself is not expected to be the heaviest process. Browser automation, transcription, Docker workloads, and benchmarks can consume much more RAM/CPU.

## Install Flow

High-level flow:

1. Prepare VPS and SSH access.
2. Install base packages and firewall.
3. Install optional GUI/admin tools.
4. Install Hermes from the official installer.
5. Run `hermes setup`.
6. Configure LLM provider and model.
7. Configure at least one gateway, usually Telegram or CLI.
8. Decide whether Hermes terminal access is host-level or Docker-restricted.
9. Add project-specific skills and account access only after the base setup is stable.

Official Linux/macOS/WSL installer from the Hermes docs:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

After install, run:

```bash
hermes setup
```

Expected setup choices:

```text
quick setup
LLM provider
API key
model name
messaging gateway
systemd service for gateway if needed
```

## Provider Strategy

Hermes consumes tokens aggressively because tool calls and long conversations resend context. The provider strategy should be connected to this repo's benchmark/scoring system.

Recommended provider categories:

| Category | Use |
|---|---|
| Trusted strong model | Important admin tasks, account changes, high-risk actions |
| Cheap daily model | Routine chat and low-risk automation |
| Reseller models | Extra quota, fallback, experiments |
| Free/limited models | Smoke tests and non-critical tasks only |

Before giving a new model to Hermes for real work, run reseller benchmarks:

```text
smoke test
identity test
coding/task quality test
latency and streaming test
quota/pricing normalization
```

## Account And Secret Access

Hermes may need access to accounts such as Notion, GitHub, Telegram, reseller APIs, VPS SSH, and router/admin panels. Treat these as production secrets.

Recommended rule:

```text
Hermes can use secrets needed for its tasks, but secrets should be scoped, revocable, and stored outside git.
```

Never commit real secrets to this repository.

Suggested layout on VPS:

```text
/opt/ai-harness/
  config/
    providers.yaml
    router-policy.yaml
    pricing.yaml

  secrets/
    README.md
    accounts.env              # local only, chmod 600, not committed
    accounts.sops.yaml        # optional encrypted secrets

  data/
    benchmarks/
    telemetry/
    scores/
```

Minimum secret rules:

| Secret type | Recommended handling |
|---|---|
| LLM API keys | Store in local env/vault, not git |
| Notion token | Use a dedicated integration with limited workspace/database access |
| GitHub token | Prefer SSH deploy keys or fine-grained PATs with minimal scopes |
| Telegram bot token | Restrict bot access by allowed user IDs |
| Reseller accounts | Track provider, quota, risk, ban status separately from the secret |
| VPS root access | Avoid giving root permanently when a narrower user can work |

## Full Access vs Restricted Access

For this project, there are two valid modes.

### Full VPS Access

Hermes can administer the server, install software, edit configs, restart services, and debug infrastructure.

Use this mode when:

```text
the VPS is disposable or well backed up
you want the agent to operate as sysadmin
the model is trusted
you accept prompt-injection and tool-risk exposure
```

Required safeguards:

```text
daily backups or snapshots
SSH key auth
firewall enabled
separate non-root service user where possible
logs for agent actions
manual review for secrets and destructive operations
```

### Docker-Restricted Terminal

Hermes terminal actions are contained in Docker. This reduces host risk but prevents direct server administration.

Use this mode when:

```text
the server stores important accounts or production data
the model/provider is untrusted
the agent is exposed to external content
you are testing unknown skills or tools
```

The Habr guide notes Hermes can switch terminal backend to Docker:

```bash
hermes config set terminal.backend docker
```

Before relying on this, verify current Hermes docs and test what files/network/services the Docker backend can access.

## Notion And External Accounts

If Hermes gets a Notion account/integration:

1. Create a dedicated Notion integration for Hermes.
2. Share only the needed pages/databases with that integration.
3. Store the token outside git.
4. Add a runbook describing what Hermes is allowed to write.
5. Log changes or ask Hermes to summarize what it changed.
6. Prefer "draft first, approve later" for important docs.

Recommended policy:

```text
Hermes may read operational docs and write benchmark notes.
Hermes should not get broad workspace owner permissions by default.
```

The same pattern applies to GitHub, email, cloud panels, VPS providers, and reseller dashboards.

## Skills And Project Concerns

Hermes supports reusable skills. This repo should eventually hold project-specific skill docs for:

```text
VPS health checks
provider benchmark runs
reseller account rotation
pricing/quota interpretation
router config updates
Notion documentation updates
incident reports
backup verification
```

Planned location:

```text
docs/agents/hermes-skills.md
skills/hermes/
```

Keep skills explicit and narrow. A skill that can touch accounts, billing, or server config should include preflight checks and expected outputs.

## Open Questions

These decisions should be made before production use:

1. Will Hermes run as a root-capable admin agent or a restricted service user?
2. Will the first VPS be disposable/test-only or hold real accounts?
3. Which accounts will Hermes get first: Notion, GitHub, Telegram, router admin, reseller dashboards?
4. Should account changes require manual approval?
5. Where will encrypted secrets live: local env files, SOPS, Vault, Infisical, Doppler, or another store?
6. Which model is trusted enough for high-risk admin tasks?
