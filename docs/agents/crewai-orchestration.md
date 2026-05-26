# CrewAI Orchestration

## Purpose

`ai-harness` will use CrewAI as the first multi-agent orchestration layer.

Hermes remains the user-facing agent in Telegram. CrewAI runs the specialist agent team behind Hermes.

The goal:

```text
Alex talks to Hermes in Telegram.
Hermes turns requests into structured tasks.
CrewAI manager delegates work to specialist agents.
Specialist agents use scripts, tools, docs, router APIs, and accounts.
Reviewer/judge checks the result.
Hermes reports progress and final results back to Telegram.
```

## High-Level Flow

```text
Telegram
  -> Hermes
    -> CrewAI Manager Agent
      -> ops-agent
      -> benchmark-agent
      -> pricing-agent
      -> router-agent
      -> docs-agent
      -> notion-agent
      -> github-agent
      -> reviewer-agent
    -> Hermes summary
  -> Telegram
```

Hermes is the front-controller. CrewAI is the internal team coordinator.

## Why CrewAI First

CrewAI is a good MVP choice because its mental model is simple:

```text
Agent = specialist role
Task = unit of work
Crew = team
Manager = controller
Hierarchical process = manager delegates and validates work
```

This matches the initial need:

```text
one main agent talks to the user
several worker agents perform specialist tasks
manager/reviewer checks output before reporting back
```

LangGraph can be added later if the system needs stricter state machines, long-running checkpoints, complex approval gates, or durable workflow recovery.

## Roles

### Hermes

Hermes receives messages from Telegram and acts as the human-facing controller.

Responsibilities:

```text
parse user intent
decide whether a request needs a CrewAI task
create task metadata
send the task to the CrewAI manager
ask for user approval when needed
summarize progress and final result
avoid exposing secrets in Telegram
```

Hermes should not directly perform every technical action. For non-trivial tasks, it should delegate to the CrewAI team.

### CrewAI Manager Agent

The CrewAI manager coordinates the internal agent team.

Responsibilities:

```text
break user goal into subtasks
choose the right specialist agents
set expected outputs
track task progress
request missing information
send work to reviewer-agent
return a concise result to Hermes
```

The manager should prefer narrow, bounded tasks and require artifacts for important operations.

### Specialist Agents

Initial specialist agents:

| Agent | Responsibility |
|---|---|
| `ops-agent` | VPS, nginx, ngrok, Docker, systemd, logs, health checks |
| `benchmark-agent` | Smoke tests, identity tests, coding tests, reseller benchmark runs |
| `pricing-agent` | Pricing models, quotas, credits, account bans, effective cost |
| `router-agent` | OmniRouter/cockpit tools configs, provider routing, model availability |
| `docs-agent` | Markdown docs, runbooks, benchmark reports |
| `notion-agent` | Notion documentation sync and decision capture |
| `github-agent` | Git status, commits, pushes, issues, PRs |
| `reviewer-agent` | Quality review, risk check, final validation |

Agents should have explicit allowed tools and write scopes. For example, `docs-agent` can edit docs, but should not change nginx or secrets.

## Task Object

Every delegated request should become a structured task.

Example:

```yaml
task_id: reseller-lightningzeus-opus-check
source: telegram
requested_by: alex
goal: "Check LightningZeus claude-opus-4.6 and update the reseller benchmark report"
risk_level: medium
status: planned
budget:
  max_requests: 20
  max_cost_usd: 2
agents:
  - benchmark-agent
  - pricing-agent
  - docs-agent
review_required: true
artifacts:
  expected:
    - benchmark-result.json
    - reseller-report.md
```

The task object gives Hermes and CrewAI a shared contract.

## Task Lifecycle

```text
requested
  -> clarified
  -> planned
  -> delegated
  -> running
  -> reviewing
  -> needs_user_approval
  -> completed
```

Failure states:

```text
blocked
failed
cancelled
needs_manual_action
```

Lifecycle rules:

| State | Meaning |
|---|---|
| `requested` | User asked Hermes for something |
| `clarified` | Hermes/CrewAI has enough detail to proceed |
| `planned` | Manager selected agents and expected outputs |
| `delegated` | Work assigned to specialist agents |
| `running` | Specialist agents are executing |
| `reviewing` | Reviewer checks correctness and risk |
| `needs_user_approval` | User must approve a risky/destructive/costly action |
| `completed` | Result accepted and summarized |
| `blocked` | Missing access, missing secret, unclear requirement, or external failure |
| `failed` | Task attempted but did not meet acceptance criteria |

## Risk Levels

Use risk levels to decide approval requirements.

| Risk | Examples | Approval |
|---|---|---|
| Low | Read docs, check status, summarize logs, draft report | No approval needed |
| Medium | Run benchmark, edit docs, update non-secret config | Approval optional or policy-based |
| High | Add provider account, change router policy, restart services, write to Notion | Ask first |
| Critical | Reveal secrets, delete data, change SSH/firewall/root access, spend significant money | Manual approval required |

Default policy:

```text
High and Critical tasks require explicit Telegram approval.
Critical tasks should include a rollback or recovery note.
```

## Artifacts

Agents should produce artifacts instead of only chat summaries.

Artifact examples:

| Artifact | Location |
|---|---|
| Benchmark JSON | `/var/lib/ai-harness/benchmarks/<run-id>.json` |
| Benchmark report | `/opt/ai-harness/repo/docs/benchmarks/<name>.md` |
| Router config diff | `/var/lib/ai-harness/router/<task-id>-diff.md` |
| Incident note | `/var/lib/ai-harness/telemetry/incidents/<date>.md` |
| Notion sync note | `/var/lib/ai-harness/agent/notion-sync/<task-id>.md` |

Each final Hermes response should include:

```text
task id
status
what changed
where artifacts were saved
risks or unresolved questions
next recommended action
```

## Tools And Boundaries

The CrewAI team should call tools through controlled interfaces:

```text
shell scripts in scripts/
benchmark suites in benchmarks/
router APIs
GitHub CLI or connector
Notion connector/integration
Docker/systemd commands
```

Avoid giving every agent every tool. Suggested boundaries:

| Agent | Allowed tools |
|---|---|
| `ops-agent` | shell, systemd, docker, logs, nginx config with approval |
| `benchmark-agent` | benchmark scripts, provider APIs, result writer |
| `pricing-agent` | pricing config, usage logs, reseller metadata |
| `router-agent` | router API/config, provider metadata, no raw secrets by default |
| `docs-agent` | repo docs, markdown reports |
| `notion-agent` | Notion API for approved pages/databases |
| `github-agent` | git, GitHub repo access |
| `reviewer-agent` | read task outputs, compare to acceptance criteria |

## Example Workflows

### Run Reseller Benchmark

```text
User:
  "Hermes, check LightningZeus claude-opus-4.6"

Hermes:
  creates task, sets budget, asks for approval if needed

CrewAI manager:
  delegates API/model checks to benchmark-agent
  delegates cost/quota interpretation to pricing-agent
  delegates report update to docs-agent
  asks reviewer-agent to validate the result

Hermes:
  sends Telegram summary with score, risks, and report path
```

### Add New Provider

```text
User:
  "Add FreeModel API key and test gpt-5.5"

Hermes:
  asks where the secret should be stored
  requests approval before writing secrets

CrewAI manager:
  router-agent adds provider metadata
  benchmark-agent runs smoke tests
  pricing-agent records pricing model
  docs-agent updates provider notes
  reviewer-agent checks no secret leaked

Hermes:
  reports status and whether model is safe for production routing
```

### Update VPS Routing

```text
User:
  "Expose benchmark dashboard through nginx"

Hermes:
  marks task high risk
  asks for confirmation

CrewAI manager:
  ops-agent proposes nginx change
  reviewer-agent checks exposure/auth policy
  ops-agent applies after approval
  ops-agent tests local and ngrok access

Hermes:
  reports URL and auth requirements
```

## Memory And Metrics

The system should track agent effectiveness over time.

Metrics:

| Metric | Meaning |
|---|---|
| `tasks_completed` | Completed tasks by agent |
| `tasks_failed` | Failed tasks by agent |
| `avg_latency` | Time from assignment to result |
| `approval_required_count` | How often the agent touches risky areas |
| `review_failures` | Results rejected by reviewer-agent |
| `user_rejects` | Results rejected by Alex |
| `cost_used` | API/tool cost for agent work |
| `artifact_quality` | Whether outputs were useful and complete |

These metrics should eventually feed an agent score:

```text
agent_effectiveness =
  completion_rate
  * review_pass_rate
  * user_acceptance_rate
  / cost_and_latency_penalty
```

## MVP Scope

First CrewAI integration should support only a few safe workflows:

1. Create task objects from Telegram/Hermes requests.
2. Run docs-only tasks through `docs-agent`.
3. Run benchmark tasks through `benchmark-agent`.
4. Run review through `reviewer-agent`.
5. Return a structured summary to Hermes.

Out of scope for first MVP:

```text
automatic secret entry
automatic router policy changes
automatic firewall/SSH changes
autonomous spending
browser-cookie management
full Notion workspace writes
```

## Later

Later improvements:

```text
persistent task database
Telegram buttons for approval
CrewAI flows for repeatable workflows
LangGraph for strict state machines
dashboard for agent/task metrics
automatic selection of best model per agent
integration with reseller scoring system
```

## Design Rule

CrewAI is the team engine. Hermes is the human interface.

Hermes should never lose the conversation with Alex, and CrewAI should never silently perform high-risk actions without a task record, artifacts, and approval policy.
