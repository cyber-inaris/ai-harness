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

## Artifact Delivery

When execution creates or updates a file, the file is not complete until it has been verified.

Required checks:

```text
file exists at the intended absolute path
file was read back after writing
expected heading/table/section is present
git status was checked
final response includes absolute path and git state
```

If the user asked to commit or push, verify after the git operation:

```text
commit hash or push target
clean or expected git status
```

Never answer "done" for a file-producing task based only on `write_file` or editor success.

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
