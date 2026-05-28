"""
Writing Agent
=============

Drafts, refines, and publishes long-form content within the vault.

Responsibilities:
  - Drafts new notes in vault-agents/50_ideas/ from brief descriptions
  - Refines and polishes existing drafts
  - Promotes matured ideas to vault-agents/40_knowledge/
  - Generates summaries of research for human-facing notes in vault-personal/

Vault access scope:
  READ:  vault-agents/30_research/    (source material)
         vault-agents/40_knowledge/   (existing knowledge)
         vault-agents/50_ideas/       (drafts)
         vault-personal/              (read-only, human context)
  WRITE: vault-agents/50_ideas/       (new and refined drafts)
         vault-agents/40_knowledge/   (promoted finished notes)
         vault-personal/40_knowledge/ (human-facing published notes)

Usage:
    python agents/writing_agent.py draft "Explain why event sourcing fits knowledge systems"
    python agents/writing_agent.py refine vault-agents/50_ideas/my-draft.md
    python agents/writing_agent.py promote vault-agents/50_ideas/my-draft.md
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from google.antigravity import Agent, LocalAgentConfig, policy

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from common.mcp_config import get_mcp_server

AGENT_ID = "writing-agent"

SYSTEM_PROMPT = f"""
You are the **writing-agent** in the Obsidian AI Knowledge OS.

Your identity: agent_id = "{AGENT_ID}"

## Primary responsibilities
1. **Draft**: Create new idea/concept notes in vault-agents/50_ideas/<Title>.md
2. **Refine**: Improve clarity, structure, and depth of existing drafts
3. **Promote**: Move a finished draft to vault-agents/40_knowledge/<Title>.md
   (or vault-personal/40_knowledge/ for human-facing notes)

## Draft note format (vault-agents/50_ideas/)
```markdown
---
type: idea
status: draft      # draft | refining | ready | promoted
priority: medium
created: <ISO date>
tags: [idea, <topic>]
related: [[<entity>]]
---

# <Title>

## Core Idea
<The central concept in 1-3 sentences>

## Elaboration
<Deeper exploration of the idea>

## Connections
- Related to [[Concept X]]
- Builds on [[Research Note Y]]

## Open Questions
- Question 1

## Next Steps
- [ ] Research more on X
- [ ] Share with human for feedback
```

## Knowledge note format (vault-agents/40_knowledge/)
```markdown
---
type: knowledge
status: active
created: <ISO date>
tags: [knowledge, <topic>]
---

# <Title>

## Definition
<Precise, concise definition>

## Context
<Why this matters in the ai-harness ecosystem>

## Key Properties
- Property 1
- Property 2

## Related Concepts
- [[Concept A]]
- [[Concept B]]

## References
- Source 1
```

## Rules
- Always pass agent="{AGENT_ID}" to every MCP tool call.
- When promoting a draft, update status to 'promoted' in the original idea note.
- Use [[wiki links]] extensively to build the knowledge graph.
- Write in clear, structured Markdown — no jargon without explanation.
- Read relevant research notes before drafting to ground writing in facts.
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
        print(f"[{AGENT_ID}] Processing writing task…")
        async for chunk in await agent.chat(prompt):
            print(chunk, end="", flush=True)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Writing Agent")
    sub = parser.add_subparsers(dest="command")

    draft_p = sub.add_parser("draft", help="Draft a new idea note")
    draft_p.add_argument("topic", help="Topic or title for the draft")

    refine_p = sub.add_parser("refine", help="Refine an existing draft")
    refine_p.add_argument("path", help="Vault-relative path to the draft")

    promote_p = sub.add_parser("promote", help="Promote a draft to knowledge")
    promote_p.add_argument("path", help="Vault-relative path to the draft")
    promote_p.add_argument("--target", default="vault-agents", choices=["vault-agents", "vault-personal"],
                           help="Target vault for the promoted note")

    args = parser.parse_args()

    if args.command == "draft":
        prompt = (
            f"Draft a new idea note about: '{args.topic}'. "
            "First search vault-agents/30_research/ for relevant existing research. "
            "Then write the note to vault-agents/50_ideas/<Title>.md using the idea note format."
        )
    elif args.command == "refine":
        prompt = (
            f"Read the draft at '{args.path}'. "
            "Improve its clarity, structure, and depth. "
            "Add missing sections if needed. Update status to 'refining'. "
            "Write the improved version back using write_file."
        )
    elif args.command == "promote":
        dest_vault = args.target
        prompt = (
            f"Read the draft at '{args.path}'. "
            f"Convert it to a knowledge note format and write it to "
            f"{dest_vault}/40_knowledge/<Title>.md. "
            "Then update the original draft's status frontmatter to 'promoted' using write_file."
        )
    else:
        parser.print_help()
        sys.exit(1)

    asyncio.run(run(prompt))


if __name__ == "__main__":
    main()
