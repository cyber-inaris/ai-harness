# Telegram Command Router

## Purpose

Hermes is operated from Telegram, so commands must be short enough to use from a phone.

Long prompts should live in playbooks. Telegram messages should only express intent.

```text
short Telegram command
  -> command router
    -> playbook
      -> Hermes / CrewAI / scripts
        -> verified artifact or status response
```

## Design Principles

1. Keep the top-level command vocabulary small.
2. Use two-level commands: command + subcommand.
3. Support natural-language aliases.
4. Use playbooks for long instructions.
5. Use buttons for approval and confirmation.
6. Ask a clarification question when intent is uncertain.
7. Verify artifacts before reporting completion.

## Command Shape

Preferred:

```text
/review team
/review security
/bench run lightningzeus claude-opus-4.6
/check vps
/check router
/status
```

Avoid too many one-off top-level commands:

```text
/review-team
/review-security
/review-benchmarks
/check-router
/check-vps
```

Top-level commands should describe broad modes:

```text
/ask
/plan
/execute
/review
/bench
/check
/notion
/status
/help
```

## Natural Language Aliases

Hermes should map short natural-language messages to command intents.

Examples:

| User message | Routed command |
|---|---|
| `командное ревью` | `/review team` |
| `проверь секреты` | `/review security` |
| `прогони бенч lightning opus` | `/bench run lightningzeus claude-opus-4.6` |
| `статус сервера` | `/check vps` |
| `проверь роутер` | `/check router` |

If confidence is low, Hermes must ask for clarification instead of guessing.

Example:

```text
Похоже, ты хочешь review. Выбери:
[team] [security] [benchmarks] [router]
```

## Playbook Runner

Each command maps to a playbook.

Example:

```text
/review team
  -> docs/playbooks/multi-perspective-review.md
  -> output docs/agents/ai-harness-agent-team-review.md
  -> verification artifact
```

The user should not need to type the playbook path from Telegram.

## Approval UX

Before risky tasks, Hermes should send a short confirmation with buttons.

Example:

```text
Run reseller benchmark?

Provider: lightningzeus
Model: claude-opus-4.6
Risk: medium
Budget: 20 requests / $2 max
Output: docs/benchmarks/lightningzeus-opus.md

[Run] [Dry run] [Cancel] [Details]
```

Risk policy:

| Risk | Telegram behavior |
|---|---|
| Low | Run directly unless user asked for approval |
| Medium | Ask if cost/account/router changes are involved |
| High | Always ask |
| Critical | Always ask and include recovery/rollback note |

## Response Format

For completed file-producing tasks:

```text
Done: <task title>

Top findings:
1. ...
2. ...
3. ...

Artifact:
<path>

Verification:
read-back: yes
git: modified <file>
```

For blocked tasks:

```text
Blocked: <task title>

Reason:
<missing secret/access/approval/context>

Next:
<one concrete action>
```

## Command Config

The command router should read:

```text
configs/telegram-commands.yaml
```

The config should define:

```text
command
subcommand
aliases
playbook
required args
risk
verification type
output path
approval behavior
```

## Implementation Notes

MVP can be simple:

```text
Hermes receives Telegram text.
Hermes calls scripts/agent-task mode-route --message "...".
Runtime matches command/alias from YAML.
Runtime returns a structured task.
Hermes asks approval if needed.
Hermes calls the matching playbook/script.
Hermes reports result.
```

Later:

```text
Telegram inline buttons
persistent task state
CrewAI task delegation
LangGraph state machine for high-risk workflows
task dashboard
```

## Safety Rules

1. Never expose raw secrets in Telegram.
2. Never execute high/critical risk tasks without explicit approval.
3. Do not guess if the command is ambiguous.
4. Do not require long prompts for common tasks.
5. Use playbooks instead of creating one-off skills.
6. Verify artifacts before saying a task is done.
