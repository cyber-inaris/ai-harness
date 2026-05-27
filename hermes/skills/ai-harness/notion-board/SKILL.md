# Notion Board

Use this skill when the user asks Hermes to add, update, plan, or inspect board tasks.

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

Create a board task:

```bash
/opt/ai-harness/repo/scripts/agent-task board-create \
  --title "Test reseller tcdmx.com" \
  --body "Source URL: https://tcdmx.com/usage" \
  --type provider \
  --risk medium \
  --agent benchmark \
  --priority Normal \
  --approval-required
```

## Rules

- Board mode creates or updates task state only.
- Do not run benchmarks or shell commands just because a task was added to Notion.
- Do not write secrets into Notion.
- Put raw logs and benchmark JSON in `/var/lib/ai-harness`, then link final artifacts from Notion.
