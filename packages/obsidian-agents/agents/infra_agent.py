"""
Infra Agent
===========

Monitors and documents infrastructure state for the ai-harness server.

Responsibilities:
  - Logs infrastructure events and changes to vault-agents/60_logs/
  - Creates and updates infra runbooks in vault-agents/40_knowledge/
  - Tracks service health and documents incidents
  - Generates infra status snapshots

Vault access scope:
  READ:  vault-agents/60_logs/infra-log.md
         vault-agents/40_knowledge/
         vault-personal/  (read-only, context)
  WRITE: vault-agents/60_logs/infra-log.md
         vault-agents/40_knowledge/  (runbooks)
         vault-agents/70_agents/     (own agent notes)

Usage:
    python agents/infra_agent.py log "Restarted obsidian-mcp.service after OOM"
    python agents/infra_agent.py snapshot
    python agents/infra_agent.py runbook "nginx gateway"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone

from google.antigravity import Agent, LocalAgentConfig, policy

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from common.mcp_config import get_mcp_server

AGENT_ID = "infra-agent"

SYSTEM_PROMPT = f"""
You are the **infra-agent** in the Obsidian AI Knowledge OS.

Your identity: agent_id = "{AGENT_ID}"

## Primary responsibilities
1. Log infrastructure events to vault-agents/60_logs/infra-log.md using append_file.
2. Create and maintain runbooks in vault-agents/40_knowledge/infra/<Component>.md
3. Generate infrastructure status snapshots summarising known service states.
4. Document incidents, changes, and outages in structured log entries.

## Infra log entry format (append to infra-log.md)
```markdown
## <ISO timestamp>
**Event**: <one-line description>
**Severity**: info | warning | critical
**Component**: <service or system>
**Action taken**: <what was done>
**Outcome**: <result>
**Related**: [[<runbook or project link>]]
```

## Runbook format (vault-agents/40_knowledge/infra/<Component>.md)
```markdown
---
type: knowledge
subtype: runbook
status: active
created: <ISO date>
tags: [infra, runbook, <component>]
---

# <Component> Runbook

## Overview
<What this component does>

## Start / Stop
```bash
sudo systemctl start|stop <service>
```

## Health Check
<How to verify it's working>

## Common Issues
### Issue 1
**Symptom**: ...
**Fix**: ...

## Change Log
### <timestamp>
<Change description>
```

## Rules
- Always pass agent="{AGENT_ID}" to every MCP tool call.
- Use append_file for log entries — never overwrite the infra log.
- Use write_file for runbooks (they are living documents).
- Keep log entries factual and timestamped.
- Never store credentials or tokens in the vault.
"""


def build_config() -> LocalAgentConfig:
    return LocalAgentConfig(
        model="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
        mcp_servers=[get_mcp_server()],
        safety_policies=[policy.confirm_run_command()],
    )


async def run(prompt: str) -> None:
    config = build_config()
    async with Agent(config) as agent:
        print(f"[{AGENT_ID}] Processing infra task…")
        async for chunk in await agent.chat(prompt):
            print(chunk, end="", flush=True)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Infra Agent")
    sub = parser.add_subparsers(dest="command")

    log_p = sub.add_parser("log", help="Log an infrastructure event")
    log_p.add_argument("event", help="Event description")
    log_p.add_argument("--severity", default="info", choices=["info", "warning", "critical"])
    log_p.add_argument("--component", default="unknown")

    sub.add_parser("snapshot", help="Generate an infra status snapshot")

    runbook_p = sub.add_parser("runbook", help="Create or update a component runbook")
    runbook_p.add_argument("component", help="Component name")

    args = parser.parse_args()
    now = datetime.now(timezone.utc).isoformat()

    if args.command == "log":
        prompt = (
            f"Log the following infrastructure event to vault-agents/60_logs/infra-log.md:\n"
            f"Timestamp: {now}\n"
            f"Event: {args.event}\n"
            f"Severity: {args.severity}\n"
            f"Component: {args.component}\n"
            "Use the standard infra log entry format."
        )
    elif args.command == "snapshot":
        prompt = (
            "Generate an infrastructure status snapshot. "
            "Read vault-agents/60_logs/infra-log.md for recent events, "
            "then write a snapshot note to vault-agents/70_agents/infra-snapshot.md "
            "summarising current known service states, recent incidents, and open issues."
        )
    elif args.command == "runbook":
        prompt = (
            f"Create or update a runbook for the '{args.component}' component "
            f"at vault-agents/40_knowledge/infra/{args.component}.md. "
            "Include: overview, start/stop commands, health check, and common issues sections."
        )
    else:
        parser.print_help()
        sys.exit(1)

    asyncio.run(run(prompt))


if __name__ == "__main__":
    main()
