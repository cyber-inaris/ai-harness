"""
Orchestration Agent
===================

The meta-agent that coordinates all other agents and manages project lifecycle.

Responsibilities:
  - Breaks high-level goals into sub-tasks and routes them to specialist agents
  - Manages the /20_projects/ layer: creates, updates, and closes project notes
  - Runs periodic consolidation from vault-agents to vault-personal
  - Maintains the agent memory index in vault-agents/70_agents/
  - Acts as the entry point for complex multi-step workflows

Vault access scope:
  READ:  all vault directories (full read)
  WRITE: vault-agents/20_projects/    (project notes)
         vault-agents/70_agents/      (agent memory + index)
         vault-personal/20_projects/  (consolidated project summaries)
         vault-agents/60_logs/        (orchestration log)
         vault-personal/00_inbox/     (consolidated summaries for human review)

Usage:
    python agents/orchestration_agent.py "Start a new project: AI Router Benchmarking"
    python agents/orchestration_agent.py --consolidate
    python agents/orchestration_agent.py --project-status "AI Router Benchmarking"
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.antigravity import Agent, LocalAgentConfig, policy

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from common.mcp_config import get_mcp_server

AGENT_ID = "orchestration-agent"
AGENTS_DIR = Path(__file__).parent

SYSTEM_PROMPT = f"""
You are the **orchestration-agent** in the Obsidian AI Knowledge OS.

Your identity: agent_id = "{AGENT_ID}"

You are the highest-level agent. You plan, delegate, and consolidate.

## Primary responsibilities

### 1. Project Management
Create and maintain project notes in vault-agents/20_projects/<Project Name>.md

Project note format:
```markdown
---
type: project
status: active     # active | paused | done | cancelled
priority: medium
created: <ISO date>
completed: null
tags: [project, <domain>]
owner: human | orchestration-agent
---

# <Project Name>

## Goal
<What success looks like>

## Tasks
- [ ] [[task/task-name]] — assigned to task-agent
- [ ] [[task/task-name-2]] — assigned to research-agent

## Agent Activity Log
### <timestamp>
Project created. Delegated initial research to research-agent.

## Notes
<Any context or constraints>
```

### 2. Periodic Consolidation
When asked to consolidate:
1. Read vault-agents/20_projects/ for active projects with recent activity
2. Read vault-agents/30_research/ for completed research
3. Write human-readable summaries to vault-personal/00_inbox/ for human review
4. Append a consolidation log entry to vault-agents/60_logs/orchestration-log.md

### 3. Agent Memory Index
Maintain vault-agents/70_agents/agent-index.md:
```markdown
---
type: agent
status: active
created: <date>
---
# Agent Index

## research-agent
Last active: <date>
Current task: <or none>

## task-agent
...
```

### 4. Workflow routing
When given a high-level goal, decompose it:
1. Identify what type of work is needed (research / tasks / writing / infra)
2. Create a project note documenting the plan
3. List the specific sub-tasks with clear agent assignments
4. Log the plan in the orchestration log

## Rules
- Always pass agent="{AGENT_ID}" to every MCP tool call.
- You have full read access to both vaults.
- Write to vault-personal/ ONLY for human-review summaries in 00_inbox/ or 20_projects/.
- Always keep the project note updated — it is the single source of truth for a project.
- Log every significant decision to vault-agents/60_logs/orchestration-log.md.
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
        print(f"[{AGENT_ID}] Starting orchestration task…")
        async for chunk in await agent.chat(prompt):
            print(chunk, end="", flush=True)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestration Agent")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("prompt", nargs="?", help="High-level goal or command")
    group.add_argument("--consolidate", action="store_true",
                       help="Run consolidation from vault-agents to vault-personal")
    group.add_argument("--project-status", metavar="PROJECT",
                       help="Report status of a specific project")
    group.add_argument("--index", action="store_true",
                       help="Rebuild the agent index")

    args = parser.parse_args()

    if args.consolidate:
        prompt = (
            "Run the periodic consolidation process: "
            "1) Read all active projects from vault-agents/20_projects/. "
            "2) For each project with activity in the last 7 days, write a human-friendly "
            "summary to vault-personal/00_inbox/<Project Name>-update.md. "
            "3) Append a consolidation entry to vault-agents/60_logs/orchestration-log.md."
        )
    elif args.project_status:
        prompt = (
            f"Report the current status of the project '{args.project_status}'. "
            "Read its note from vault-agents/20_projects/ and any related task notes. "
            "Summarise: goal, open tasks, completed tasks, recent activity, blockers."
        )
    elif args.index:
        prompt = (
            "Rebuild the agent index at vault-agents/70_agents/agent-index.md. "
            "For each agent (research-agent, task-agent, infra-agent, writing-agent, "
            "orchestration-agent), check their log entries in vault-agents/60_logs/ "
            "and note the last activity timestamp and current task."
        )
    else:
        prompt = args.prompt

    asyncio.run(run(prompt))


if __name__ == "__main__":
    main()
