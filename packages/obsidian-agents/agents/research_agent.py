"""
Research Agent
==============

Autonomous agent that conducts research tasks and writes structured
findings into the Obsidian vault via MCP.

Responsibilities:
  - Reads research briefs from vault-personal/30_research/
  - Uses web search (built-in) to gather information
  - Writes structured research notes to vault-agents/30_research/
  - Appends progress logs to vault-agents/60_logs/research-log.md
  - Creates entity notes for new concepts in vault-agents/40_knowledge/

Vault access scope:
  READ:  vault-personal/30_research/     (briefs)
         vault-agents/30_research/       (existing research)
         vault-agents/40_knowledge/      (existing knowledge)
  WRITE: vault-agents/30_research/       (new findings)
         vault-agents/40_knowledge/      (new entity notes)
         vault-agents/60_logs/           (activity log)

Usage:
    python agents/research_agent.py "Research the state of MCP protocol adoption in 2026"
    python agents/research_agent.py --brief vault-personal/30_research/my-brief.md
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone

from google.antigravity import Agent, LocalAgentConfig, policy

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from common.mcp_config import get_mcp_server

AGENT_ID = "research-agent"

SYSTEM_PROMPT = f"""
You are the **research-agent** in the Obsidian AI Knowledge OS.

Your identity: agent_id = "{AGENT_ID}"

## Primary responsibilities
1. Read research briefs from vault-personal/30_research/ or as given in the user prompt.
2. Conduct thorough research using your web search capability.
3. Write a structured research note to vault-agents/30_research/<Topic>.md with:
   - YAML frontmatter (type: research, status: active/done, created, tags)
   - ## Summary section
   - ## Sources section (with [[wiki links]] for entities found)
   - ## Key Findings section
   - ## Open Questions section
4. Create entity notes in vault-agents/40_knowledge/<Entity>.md for any
   significant new concepts, companies, or tools you discover.
5. Append a progress log entry to vault-agents/60_logs/research-log.md
   in the format:
   ```
   ## <ISO timestamp>
   Completed research on <topic>. Key findings: <brief summary>.
   ```

## Rules
- Always pass agent="{AGENT_ID}" to every MCP tool call.
- Never write to vault-personal/ (read-only for you, except 30_research briefs).
- Never access files outside /opt/vaults/.
- If a research note already exists, use write_file to update it, not create_file.
- Use [[Entity Name]] Obsidian wiki links when referencing concepts.

## Output format for research notes
```markdown
---
type: research
status: active
priority: medium
created: <ISO date>
tags: [research, <topic-tag>]
related: [[<entity1>]], [[<entity2>]]
---

# <Topic>

## Summary
<2-3 sentence overview>

## Key Findings
- Finding 1
- Finding 2

## Sources
- [Source Title](URL) — <one-line description>

## Open Questions
- Question 1

## Log
### <timestamp>
Research initiated by research-agent.
```
"""


def build_config() -> LocalAgentConfig:
    return LocalAgentConfig(
        model="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
        mcp_servers=[get_mcp_server()],
        tools=["web_search"],
        safety_policies=[
            policy.confirm_run_command(),   # block shell; allow all MCP tools
        ],
    )


async def run(prompt: str) -> None:
    config = build_config()
    async with Agent(config) as agent:
        print(f"[{AGENT_ID}] Starting research task…")
        async for chunk in await agent.chat(prompt):
            print(chunk, end="", flush=True)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Agent")
    parser.add_argument("prompt", nargs="?", help="Research task description")
    parser.add_argument("--brief", help="Path to a research brief note in the vault")
    args = parser.parse_args()

    if args.brief:
        prompt = (
            f"Read the research brief at '{args.brief}' and conduct the research described."
        )
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        sys.exit(1)

    asyncio.run(run(prompt))


if __name__ == "__main__":
    main()
