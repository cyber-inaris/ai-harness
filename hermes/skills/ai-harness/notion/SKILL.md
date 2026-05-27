# Notion

Use this skill when the user asks Hermes to add, update, plan, inspect, or sync Notion tasks and project records.

## Context

Notion env:

```text
/opt/ai-harness/secrets/notion.env
```

Current task database:

```text
AI Benchmarks
36db5aee9b288037be25f9620837ad3b
```

## Commands

Classify a user message:

```bash
/opt/ai-harness/repo/scripts/agent-task mode-route --message "..."
```

Create a Notion task:

```bash
/opt/ai-harness/repo/scripts/agent-task notion-create-task \
  --title "Test reseller tcdmx.com" \
  --body "Source URL: https://tcdmx.com/usage" \
  --type provider \
  --risk medium \
  --agent benchmark \
  --priority Normal \
  --approval-required
```

`board-create` exists only as a backwards-compatible hidden alias. Prefer `notion-create-task` in new instructions.

## Rules

- Notion mode creates or updates task/project state only.
- Do not run benchmarks or shell commands just because a task was added to Notion.
- Do not write secrets into Notion.
- Put raw logs and benchmark JSON in `/var/lib/ai-harness`, then link final artifacts from Notion.
