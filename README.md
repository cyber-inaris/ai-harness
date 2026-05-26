# AI Harness

Ops-first repository for setting up, running, and testing AI agents, routers, reseller accounts, and benchmark workflows.

This project is not starting as a custom router or full SaaS platform. It is a practical harness: documentation, scripts, benchmark suites, example configs, Docker layouts, and runbooks that let a human operator and AI agents manage an AI infrastructure stack.

## What This Repo Covers

- VPS setup for AI-agent infrastructure.
- Optional Linux GUI access with XFCE + xrdp.
- Cockpit and admin access through SSH tunnels.
- Docker layout for routers, workers, and supporting tools.
- Reseller/API account storage policy.
- Benchmark suites for model identity, coding quality, latency, and cost signals.
- Scoring methodology for reseller/model quality, reliability, pricing, and risk.
- Agent runbooks for Hermes, Codex, and future automation.

## Current Direction

The repository follows a hybrid strategy:

1. Start as an ops/playbook repo with minimal code.
2. Use existing tools such as OmniRouter, Cockpit-style admin tools, Docker, SSH, and benchmark scripts.
3. Leave extension points for custom scoring workers, APIs, or UI later.

Start with the design doc:

- [AI Harness Ops-First Design](docs/design/2026-05-26-ai-harness-ops-first-design.md)

## Repository Map

```text
docs/                 Human and agent runbooks
configs/examples/     Safe example configs, no secrets
scripts/              Setup and benchmark helper scripts
benchmarks/suites/    Benchmark suite definitions
benchmarks/results/   Local benchmark output, ignored by git
secrets/              Local/encrypted secrets only, ignored by git
ops/                  Systemd, nginx, firewall, backup templates
packages/             Future code packages if needed
```

## Safety Rules

- Do not commit real API keys, reseller accounts, cookies, sessions, or credentials.
- Keep admin tools private by default; prefer SSH tunnels or VPN.
- Treat reseller claims as untrusted until benchmarked.
- Store benchmark facts separately from subjective model-judge scores.
- Keep pricing, quota, ban, and reliability signals visible instead of hiding them behind one score.

## First Useful Workflow

1. Provision a VPS.
2. Install optional admin access: Cockpit, XFCE + xrdp, SSH tunnels.
3. Configure a router such as OmniRouter or another OpenAI-compatible router.
4. Add reseller/provider metadata in `configs/examples/providers.yaml`.
5. Store real secrets outside git.
6. Run smoke, identity, coding, and long-context benchmarks.
7. Use scoring docs to decide whether the model is production, burst, sandbox, or avoid.

