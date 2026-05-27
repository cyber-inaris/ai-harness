---
name: plan
description: Turn a goal into a concrete plan, checklist, or task breakdown without executing it.
---

# Plan

Use this skill when the user asks to plan, decompose, estimate, or organize work.

## Rules

- Produce a concrete plan with ordered steps.
- Do not execute the plan.
- Do not create Notion tasks unless the user explicitly asks to put the plan into Notion.
- Mark steps that need approval, secrets, spending, service restarts, or account access.
- If implementation should start immediately, ask the user to switch to execute mode.

## Notion Handoff

If the user asks to put the plan into Notion, create tasks with:

```bash
/opt/ai-harness/repo/scripts/agent-task notion-create-task --title "..." --body "..." --type infra --risk medium --agent planner
```

## Examples

```text
/plan как внедрить Notion task sync в LangGraph?
/plan разбей настройку реселлер-бенчмарков на задачи
```
