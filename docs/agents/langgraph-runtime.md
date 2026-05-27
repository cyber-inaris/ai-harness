# LangGraph Agent Runtime

## Decision

`ai-harness` uses LangGraph as the primary runtime for AI-agent workflows.

Hermes remains the Telegram-facing control plane. LangGraph is the local task runtime for workflows, approval gates, reviewer/judge steps, retries, and task records.

CrewAI is not the foundation anymore. It can still be used later as an optional worker backend from a LangGraph node.

## Why LangGraph

The target system needs:

```text
task state
interrupt/resume for user approval
reviewer and judge routing
workflow branching
retries
clear task records
selected artifacts
```

LangGraph fits this better than a role-only agent crew.

## Runtime Shape

```text
Telegram
  -> Hermes
    -> scripts/agent-task
      -> LangGraph workflow
        -> planner node
        -> worker nodes
        -> reviewer/judge nodes
        -> approval interrupt nodes
        -> artifact writer
      -> SQLite task/event records
      -> selected files in docs/ or /var/lib/ai-harness
    -> Telegram summary
```

## Storage Policy

Do not write a markdown file for every agent action.

Use this split:

```text
Task metadata: SQLite
Events/tool summaries: SQLite
Important artifacts: files
Raw noisy logs: journal/tool logs with retention
```

Allowed artifact examples:

```text
benchmark report
provider test JSON
config diff
incident note
final task summary
```

The first runtime stores task records in:

```text
/var/lib/ai-harness/agent/tasks.sqlite
```

and task artifacts in:

```text
/var/lib/ai-harness/agent/tasks/<task-id>/
```

## First Workflow

The first runnable workflow is intentionally safe:

```text
docs-smoke
```

It:

1. creates a low-risk task record;
2. writes one markdown report to an allowed path;
3. reviews the report for required sections and obvious secret markers;
4. writes a task summary JSON;
5. returns a compact JSON result.

It does not:

```text
edit secrets
call provider APIs
change router policy
restart services
commit or push
write outside allowed roots
```

## Install

Host package prerequisites:

```bash
sudo apt install -y python3-venv sqlite3
```

From the server:

```bash
cd /opt/ai-harness/repo
sudo ./scripts/install-langgraph-runtime.sh
```

Verify:

```bash
./scripts/agent-task status
./scripts/agent-task mode-route --message "добавь в борду: протестировать tcdmx.com"
./scripts/agent-task brainstorm-start --topic "Agent modes"
./scripts/agent-task docs-smoke \
  --topic "LangGraph smoke test" \
  --target /opt/ai-harness/repo/docs/agents/langgraph-smoke-result.md
```

## Hermes Integration

Hermes should call the stable wrapper:

```bash
/opt/ai-harness/repo/scripts/agent-task docs-smoke \
  --topic "..." \
  --target /opt/ai-harness/repo/docs/agents/<file>.md
```

Hermes should not call internal Python modules directly.

Mode and board commands:

```bash
/opt/ai-harness/repo/scripts/agent-task mode-route --message "..."
/opt/ai-harness/repo/scripts/agent-task board-create --title "..." --body "..."
/opt/ai-harness/repo/scripts/agent-task brainstorm-start --topic "..."
```

## Next Workflows

Implement in this order:

1. `benchmark-provider`: run a small provider/model benchmark through OmniRoute.
2. `provider-review`: compare benchmark result, identity risk, token overhead, and streaming compatibility.
3. `router-provider-check`: read-only OmniRoute provider health and model sync check.
4. `approval-gate`: pause for Telegram approval before high-risk changes.

## Current Boundary

Low-risk tasks can run automatically.

Medium tasks can run if they only read APIs or write docs.

High and critical tasks must stop for explicit approval before changing services, router policy, secrets, firewall, SSH, billing, or account state.
