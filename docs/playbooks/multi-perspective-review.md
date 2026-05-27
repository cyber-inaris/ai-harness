# Multi-Perspective Review Playbook

## Purpose

Use this playbook when a user asks for a review from several roles, reviewers, or perspectives.

This is a playbook, not a Hermes skill. The generic `review` skill defines how to review. This file defines one reusable review pattern.

## Pattern

One lead reviewer coordinates the review.

```text
Lead reviewer
  -> defines scope
  -> assigns perspectives
  -> gathers evidence
  -> consolidates findings
  -> prioritizes backlog
  -> writes/verifies artifact if requested
```

Do not create a new skill for each review type. Create or update a playbook/template if the pattern is reusable.

## Inputs

Required:

```text
scope
reviewer perspectives
expected output
artifact path if a file is requested
```

Optional:

```text
priority scale
owner roles
evidence checklist
areas out of scope
```

## Default Perspectives For ai-harness

| Perspective | Focus |
|---|---|
| Ops engineer | VPS, nginx, tunnels, systemd, Docker, runtime setup |
| Agent architect | Hermes, CrewAI/LangGraph, task routing, skills, agent boundaries |
| Security reviewer | Secrets, accounts, API keys, cookies, auth, public exposure |
| QA reviewer | Smoke tests, benchmark checks, verification gaps, regression risks |
| Judge | Consolidation, priority order, final backlog |

## Evidence Collection

The lead reviewer should inspect current files before writing conclusions.

Suggested file areas:

```text
docs/vps/
docs/networking/
docs/operations/
docs/agents/
docs/accounts/
docs/benchmarks/
hermes/
scripts/
packages/
secrets/README.md
```

Suggested commands:

```bash
git status --short
find docs scripts packages hermes secrets -maxdepth 4 -type f | sort
```

Use current evidence. Avoid relying on memory or old chat context when files are available.

## Output Table

Default backlog table:

| priority | area | issue | evidence | recommendation | owner role |
|---|---|---|---|---|---|

Priority scale:

```text
P0 = blocks safe operation
P1 = should fix before real accounts or public exposure
P2 = important hardening or reliability improvement
P3 = cleanup or future improvement
```

## Artifact Verification

If the review writes a file, the lead reviewer must verify delivery before saying it is complete.

Required checks:

```bash
test -f <artifact-path>
sed -n '1,80p' <artifact-path>
git status --short
```

Final response must include:

```text
absolute artifact path
whether the file was read back
git status summary
top 3 findings
```

## Example Prompt

```text
/review Use docs/playbooks/multi-perspective-review.md.

Review current ai-harness repo with these perspectives:
- Ops engineer checks VPS/nginx/cloudflare/hermes setup docs.
- Agent architect checks LangGraph runtime docs.
- Security reviewer checks secrets/accounts/API key handling.
- QA reviewer checks missing smoke tests.
- Judge consolidates a prioritized backlog.

Write:
docs/agents/ai-harness-agent-team-review.md

Use table columns:
priority, area, issue, evidence, recommendation, owner role.
Verify the artifact before reporting completion.
```
