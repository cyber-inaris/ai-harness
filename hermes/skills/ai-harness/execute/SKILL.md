---
name: execute
description: Execute a bounded operational task through shell, LangGraph, or existing ai-harness scripts after safety checks.
---

# Execute

Use this skill when the user explicitly asks to run, install, fix, test, deploy, or change something now.

## Rules

1. Inspect current state before changing it.
2. Use stable repo scripts before ad hoc commands.
3. For high or critical risk, ask for explicit approval before changing anything.
4. Never print secrets.
5. Report exact commands and verification results.

## Risk Gate

Ask for approval before changing:

```text
secrets
SSH/firewall
nginx/systemd
router policy
provider credentials
billing/account state
paid benchmark runs
```

## Useful Commands

```bash
/opt/ai-harness/repo/scripts/agent-task mode-route --message "..."
/opt/ai-harness/repo/scripts/agent-task status
```

## Examples

```text
/execute проверь сервисы Hermes и перезапусти если надо
/execute запусти smoke benchmark для нового провайдера
```
