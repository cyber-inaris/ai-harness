# AI Harness Ops-First Design

Date: 2026-05-26

## Purpose

`ai-harness` is an operations-first repository for setting up, running, and testing AI agents, routers, reseller accounts, and benchmark workflows.

The repository should not start as a custom router or full SaaS platform. It should be a practical harness: documentation, scripts, benchmark suites, example configs, Docker layouts, and runbooks that let AI agents and a human operator manage an AI infrastructure stack.

The long-term direction is hybrid:

1. Start as an ops/playbook repository with minimal code.
2. Use existing tools such as OmniRouter, Cockpit-style admin tools, Docker, SSH, and benchmark scripts.
3. Leave clean extension points for future packages if custom scoring workers, APIs, or UI become necessary.

## Goals

- Document how to provision a Linux VPS for AI-agent infrastructure.
- Provide repeatable setup for XFCE + xrdp, Cockpit, SSH tunnels, Docker, and firewall basics.
- Define where reseller accounts, API keys, pricing metadata, and quota rules live.
- Provide benchmark suites and scripts for testing new resellers/models.
- Preserve and evolve the existing AI reseller benchmark notes and scoring system.
- Help AI agents understand how to operate the stack without relying on tribal knowledge.
- Keep the first version simple enough to maintain without writing a full platform.

## Non-Goals

- Do not write a custom OmniRouter replacement in the first version.
- Do not expose admin tools publicly by default.
- Do not commit real API keys, reseller accounts, cookies, sessions, or credentials.
- Do not make one global score hide important tradeoffs. Keep quality, cost, reliability, speed, compatibility, and risk visible separately.
- Do not depend on a full desktop GUI when a web admin panel or CLI is enough.

## Repository Shape

```text
ai-harness/
  README.md

  docs/
    overview.md
    architecture.md

    design/
      2026-05-26-ai-harness-ops-first-design.md

    vps/
      ubuntu-setup.md
      xfce-xrdp.md
      cockpit.md
      ssh-tunnels.md
      firewall.md

    routers/
      omni-router.md
      cockpit-tools.md
      routing-strategy.md

    accounts/
      where-to-store-secrets.md
      reseller-account-lifecycle.md
      account-ban-handling.md
      pricing-models.md

    benchmarks/
      reseller-benchmark-notes.md
      reseller-scoring-system.md
      benchmark-protocol.md
      model-identity-tests.md
      coding-agent-tests.md

    docker/
      docker-compose-layout.md
      volumes-and-backups.md
      logs-and-telemetry.md

    agents/
      hermes-agent.md
      codex-agent-workflow.md
      task-routing.md

  configs/
    examples/
      providers.yaml
      pricing.yaml
      accounts.example.yaml
      router-policy.yaml
      docker-compose.yml
      env.example

  scripts/
    setup-vps.sh
    install-xfce-xrdp.sh
    install-cockpit.sh
    create-ssh-tunnel.sh
    check-provider-models.sh
    run-smoke-benchmark.sh
    run-reseller-benchmark.sh

  benchmarks/
    suites/
      smoke.json
      identity.json
      coding.json
      long-context.json
    results/
      .gitkeep

  secrets/
    README.md
    .gitignore

  ops/
    systemd/
    nginx/
    firewall/
    backups/

  packages/
    README.md
```

## Subsystems

### VPS Setup

The VPS documentation should describe a known-good Linux setup:

- Ubuntu Server 24.04 LTS as the default distribution.
- XFCE + xrdp for optional remote desktop access.
- Cockpit for web-based server administration.
- SSH tunnels as the default way to reach admin UIs.
- Docker and Docker Compose for routers, workers, and supporting tools.
- Basic firewall rules that keep admin services off the public internet.

The default stance is conservative: expose only SSH publicly, then reach Cockpit, router dashboards, and xrdp through SSH tunnels or a private VPN.

### Router Integration

`ai-harness` should document and configure existing routers rather than replacing them.

Initial router targets:

- OmniRouter or compatible model router.
- Cockpit-style tools if they are part of the chosen operational stack.
- OpenAI-compatible reseller endpoints.

Router docs should cover:

- How providers are registered.
- How models are named.
- How fallback routes work.
- How benchmark scores influence preferred routes.
- How to separate production routes from sandbox/testing routes.

### Account And Secret Management

Credentials must be separated from public config.

Public config can contain:

- Provider id.
- Base URL.
- Claimed models.
- Pricing model.
- Daily/monthly quotas.
- Routing tags.

Secrets must not be committed:

- API keys.
- Reseller account logins.
- Cookies.
- Session tokens.
- Payment or recovery data.

First version storage options:

- `.env` files ignored by git for local development.
- Encrypted files with `sops`/`age` for portable secrets.
- Server-local secret files under restricted permissions.

Future storage options:

- Vault.
- Infisical.
- Doppler.
- Cloud secret managers.

Account lifecycle docs should track:

- Active accounts.
- Quota state.
- Ban or suspension events.
- Failed keys.
- Replacement history.
- Real useful work completed before failure.

### Benchmarks

Benchmarks should be explicit suites, not ad hoc prompts hidden in scripts.

Initial suites:

- `smoke`: endpoint health, `/v1/models`, one simple completion.
- `identity`: weak model identity probes, behavior probes, claimed-model plausibility.
- `coding`: small code generation, bug fix, test writing, refactor explanation.
- `long-context`: context-window and recall checks.

Benchmark outputs should include:

- Provider and model requested.
- Status and error details.
- Latency.
- Token usage reported by API.
- Local token estimate where possible.
- Hidden overhead ratio.
- Output excerpts.
- Judge scores when a trusted judge is used.

### Reseller Scoring

The existing scoring concept should move into this repo.

Scores remain separate:

- Quality.
- Identity confidence.
- Cost efficiency.
- Reliability.
- Speed.
- API compatibility.
- Risk.

The system should normalize different reseller pricing models:

- Per-token billing.
- Requests per day.
- Account sales.
- Credits.
- Subscriptions.
- Unlimited/fair-use plans.

The practical output is not just "price per million tokens". It is:

- Effective cost per useful coding task.
- Effective tasks per day.
- Hidden overhead ratio.
- Ban-adjusted cost for account sellers.
- Retry and failure penalty.

### Trusted Judge

A trusted strong model can evaluate benchmark answers, especially coding outputs.

Judge scoring should be structured:

- Correctness.
- Instruction following.
- Code quality.
- Reasoning quality.
- Model plausibility.
- Safety behavior.

Judge scores are useful but not authoritative alone. They must be combined with objective telemetry: errors, latency, token usage, quota loss, bans, retries, and user acceptance.

### Production Telemetry

When real routing is added, every model call should be observable.

Useful fields:

- Provider id.
- Claimed model.
- Actual model reported by API, if available.
- Task type.
- Latency.
- TTFT and tokens/sec for streaming.
- Reported input/output tokens.
- Estimated local prompt tokens.
- Error status.
- Retry count.
- Billing units spent.
- Quota/bans/throttle events.
- User or judge feedback.

Scores should decay over time so fresh reseller behavior matters more than old benchmark results.

## First Milestone

Milestone 1 should create a useful repo without building a full platform.

Deliverables:

1. Top-level README explaining the purpose and workflow.
2. VPS setup docs for Ubuntu, XFCE + xrdp, Cockpit, SSH tunnels, firewall, and Docker.
3. Account/secrets policy docs.
4. Benchmark docs migrated from `ai-testing-toolkit`.
5. Benchmark suite JSON files for smoke, identity, coding, and long-context tests.
6. Basic scripts for provider model discovery and smoke benchmark runs.
7. Example configs for providers, pricing, accounts, and router policy.

## Migration From `ai-testing-toolkit`

Move these docs:

```text
ai-testing-toolkit/docs/benchmarks/reseller-benchmark-2026-05-26.md
  -> ai-harness/docs/benchmarks/reseller-benchmark-notes.md

ai-testing-toolkit/docs/benchmarks/reseller-scoring-system.md
  -> ai-harness/docs/benchmarks/reseller-scoring-system.md
```

Convert selected tests from:

```text
ai-testing-toolkit/api/tests/index.js
```

into:

```text
ai-harness/benchmarks/suites/smoke.json
ai-harness/benchmarks/suites/identity.json
ai-harness/benchmarks/suites/coding.json
ai-harness/benchmarks/suites/long-context.json
```

Do not move the old frontend/backend wholesale unless later needed. The new repo should start lighter and more operational.

## Open Decisions

- Which router will be the first supported target: OmniRouter, Cockpit tools, or another OpenAI-compatible router?
- Which trusted judge model will be used first?
- Should secrets start with server-local encrypted files or a real secret manager?
- Should benchmark results be stored as JSON files first or in SQLite from day one?
- Which VPS provider will be the reference deployment target?

## Acceptance Criteria

The repo is useful when a new operator or AI agent can:

1. Provision a VPS using the docs.
2. Install optional GUI/admin access without exposing it publicly.
3. Add a reseller account without committing secrets.
4. Configure a router to use that reseller.
5. Run smoke and coding benchmarks.
6. Read benchmark results and understand whether the reseller is usable, risky, or should be avoided.
7. Extend the setup without needing to reverse-engineer decisions from chat history.
