"""
Task Agent
==========

Manages task lifecycle in the Obsidian vault:
  - Creating structured task notes
  - Updating task status ([ ] → [/] → [x])
  - Generating daily task summaries
  - Surfacing overdue or high-priority tasks

Vault access scope:
  READ:  vault-personal/10_tasks/   (human tasks — read to avoid duplication)
         vault-agents/10_tasks/     (agent task queue)
         vault-personal/20_projects/ (project context)
  WRITE: vault-agents/10_tasks/     (new task notes)
         vault-agents/60_logs/      (task activity log)

Usage:
    python agents/task_agent.py create "Write architecture doc" --priority high --project "AI Harness"
    python agents/task_agent.py summary
    python agents/task_agent.py overdue
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone

from google.antigravity import Agent, LocalAgentConfig, policy

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from common.mcp_config import get_mcp_server

AGENT_ID = "task-agent"

SYSTEM_PROMPT = f"""
You are the **task-agent** in the Obsidian AI Knowledge OS.

Your identity: agent_id = "{AGENT_ID}"

## Primary responsibilities
1. Create structured task notes in vault-agents/10_tasks/<Task Name>.md
2. Update task status fields in existing task notes
3. Generate daily summaries listing open, in-progress, and recently completed tasks
4. Identify overdue tasks based on `due:` frontmatter fields

## Task note format
```markdown
---
type: task
status: open        # open | in-progress | done | blocked
priority: medium    # low | medium | high | critical
project: "[[Project Name]]"
due: YYYY-MM-DD
created: <ISO datetime>
assigned_to: task-agent
tags: [task]
---

# <Task Name>

## Description
<What needs to be done and why>

## Checklist
- [ ] Sub-task 1
- [ ] Sub-task 2

## Log
### <timestamp>
Task created by task-agent.
```

## Rules
- Always pass agent="{AGENT_ID}" to every MCP tool call.
- Task filenames use the format: <YYYY-MM-DD>-<kebab-task-name>.md
- When updating status, use write_file to replace the full note.
- Always append a log entry when status changes.
- Use [[Project Name]] links to reference projects.
- If a similar task already exists in vault-personal/10_tasks/, mention it in your response.
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
        print(f"[{AGENT_ID}] Processing task request…")
        async for chunk in await agent.chat(prompt):
            print(chunk, end="", flush=True)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Task Agent")
    sub = parser.add_subparsers(dest="command")

    create_p = sub.add_parser("create", help="Create a new task")
    create_p.add_argument("title", help="Task title")
    create_p.add_argument("--priority", default="medium", choices=["low", "medium", "high", "critical"])
    create_p.add_argument("--project", default=None, help="Project name")
    create_p.add_argument("--due", default=None, help="Due date YYYY-MM-DD")

    sub.add_parser("summary", help="Generate a task summary")
    sub.add_parser("overdue", help="List overdue tasks")

    args = parser.parse_args()

    if args.command == "create":
        parts = [f"Create a task note titled '{args.title}'"]
        parts.append(f"Priority: {args.priority}")
        if args.project:
            parts.append(f"Project: {args.project}")
        if args.due:
            parts.append(f"Due: {args.due}")
        prompt = ". ".join(parts) + "."
    elif args.command == "summary":
        prompt = (
            "List all open and in-progress tasks from vault-agents/10_tasks/ and "
            "vault-personal/10_tasks/. Group by priority. Format as a markdown summary."
        )
    elif args.command == "overdue":
        today = datetime.now(timezone.utc).date().isoformat()
        prompt = (
            f"Today is {today}. Find all tasks in vault-agents/10_tasks/ and "
            "vault-personal/10_tasks/ with a `due:` field earlier than today "
            "and status not 'done'. List them with their priority and project."
        )
    else:
        parser.print_help()
        sys.exit(1)

    asyncio.run(run(prompt))


if __name__ == "__main__":
    main()
