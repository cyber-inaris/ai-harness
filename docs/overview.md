# Overview

`ai-harness` is a practical operations repository for AI-agent infrastructure.

It collects the runbooks, configs, benchmark suites, scripts, and operational policies needed to run:

- AI agents such as Hermes.
- Model routers such as OmniRouter or OpenAI-compatible router tools.
- Reseller/provider accounts.
- Benchmark and scoring workflows.
- VPS administration with optional GUI/admin access.

The first version is intentionally ops-first. Custom services can be added later under `packages/` when documentation, scripts, and existing tools are no longer enough.

## Primary Workflows

1. Set up a VPS.
2. Install admin access through Cockpit, SSH tunnels, and optional XFCE + xrdp.
3. Configure model routers and provider metadata.
4. Store real account secrets outside git.
5. Run benchmark suites against new resellers/models.
6. Score model usefulness, identity confidence, cost, reliability, speed, compatibility, and risk.
7. Use the scores to decide production, burst, sandbox, or avoid routing.

