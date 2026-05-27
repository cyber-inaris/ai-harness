# Hermes Modes And Skills

## Purpose

Hermes should behave like a small operational controller, not like a single prompt that always does everything.

Every user message should be routed into one of a few modes. The mode decides whether Hermes answers directly, creates a Notion task, starts a LangGraph workflow, asks for approval, or enters a structured skill such as brainstorming.

## Modes

| Mode | Use When | Default Action |
|---|---|---|
| `ask` | The user asks a question or wants advice | Answer directly; do not write Notion; do not run tools unless needed |
| `notion` | The user says to add/write/put something in Notion, the board, backlog, or task list | Create or update Notion state; do not execute it |
| `brainstorm` | The user wants to design, invent, choose architecture, or explicitly invokes brainstorming | Run the brainstorming skill; do not implement before design approval |
| `plan` | The user asks for a plan, breakdown, checklist, or task decomposition | Produce a plan; optionally create Notion tasks if asked |
| `execute` | The user asks to run, install, test, fix, deploy, or do the work now | Start a bounded LangGraph workflow or use shell after safety checks |
| `review` | The user asks to check, review, verify, compare, judge, or audit | Inspect evidence and report findings first |

If the route is ambiguous, Hermes should ask:

```text
Do you want me to answer, add this to Notion, brainstorm it, plan it, or execute it now?
```

## Triggers

Board triggers:

```text
add to board
создай задачу
добавь в борду
запиши в Notion
поставь в backlog
запланируй как задачу
```

Brainstorm triggers:

```text
brainstorm
брейншторм
придумай архитектуру
давай подумаем
спроектируй
```

Execute triggers:

```text
запусти
сделай
установи
почини
протестируй сейчас
deploy
run
```

Review triggers:

```text
проверь
review
compare
сравни
оцени результат
```

## Stable Commands

Hermes should call stable wrapper commands, not Python modules directly:

```bash
/opt/ai-harness/repo/scripts/agent-task mode-route --message "..."
/opt/ai-harness/repo/scripts/agent-task notion-create-task --title "..." --body "..."
/opt/ai-harness/repo/scripts/agent-task brainstorm-start --topic "..."
```

## Board Mode

Board mode creates a Notion task only.

Example user request:

```text
добавь в борду: протестировать нового реселера https://tcdmx.com/usage
```

Expected task:

```text
Project name: Test reseller tcdmx.com
Task Type: provider
Risk: medium
Agent: benchmark
Priority: Normal
Approval Required: true
```

The task body should include the original user request and known missing inputs.

## Brainstorm Mode

Brainstorm mode is a hard gate before creative or architectural work.

Hermes must:

1. inspect project context first;
2. ask one question at a time;
3. propose 2-3 approaches;
4. present a design;
5. wait for user approval;
6. write the approved spec to `docs/superpowers/specs/`;
7. self-review the spec;
8. ask the user to review it before implementation planning.

Hermes must not implement, edit files, deploy, or change services during brainstorming unless the user explicitly exits brainstorming mode.

## Execution Boundary

High and critical tasks require explicit approval before changing:

```text
secrets
SSH/firewall
billing/account state
router policy
nginx/systemd services
provider credentials
paid benchmark runs
```

Low-risk tasks can run directly. Medium-risk tasks can run if they only read APIs, update docs, or create local artifacts.

## State Split

Use Notion for high-level task state.

Use LangGraph SQLite and `/var/lib/ai-harness` for execution state:

```text
Notion:
  task title, status, risk, agent, artifact link

LangGraph:
  task events, workflow state, reviewer verdicts

/var/lib/ai-harness:
  generated reports, benchmark JSON, task summaries
```
