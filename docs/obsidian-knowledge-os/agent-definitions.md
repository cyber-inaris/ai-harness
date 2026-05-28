# Agent Definitions

Each agent operates exclusively via MCP, connecting to the shared `obsidian-mcp` SSE service at `127.0.0.1:3000`.

---

## Connection Pattern

```python
from common.mcp_config import get_mcp_server
from google.antigravity import Agent, LocalAgentConfig

config = LocalAgentConfig(
    model="gemini-2.0-flash",
    mcp_servers=[get_mcp_server()],  # → http://127.0.0.1:3000/sse
    ...
)
```

All agents pass `agent="<agent-id>"` to every MCP tool call. This populates the audit log.

---

## research-agent

**File**: `packages/obsidian-agents/agents/research_agent.py`

| Property | Value |
|---|---|
| Identity | `research-agent` |
| Model | `gemini-2.0-flash` |
| Built-in tools | `web_search` |
| Primary write vault | `vault-agents/30_research/` |

**Responsibilities:**
- Reads research briefs from `vault-personal/30_research/`
- Conducts web research and writes structured findings
- Creates entity notes for new concepts in `vault-agents/40_knowledge/`
- Appends progress to `vault-agents/60_logs/research-log.md`

**Read access:**
- `vault-personal/30_research/` (briefs)
- `vault-agents/30_research/`, `vault-agents/40_knowledge/`

**Write access:**
- `vault-agents/30_research/` (new findings)
- `vault-agents/40_knowledge/` (entity notes)
- `vault-agents/60_logs/research-log.md`

**Usage examples:**
```bash
# Direct prompt
python agents/research_agent.py "Research MCP protocol adoption in 2026"

# From a brief file
python agents/research_agent.py --brief vault-personal/30_research/llm-routing-brief.md
```

---

## task-agent

**File**: `packages/obsidian-agents/agents/task_agent.py`

| Property | Value |
|---|---|
| Identity | `task-agent` |
| Model | `gemini-2.0-flash` |
| Primary write vault | `vault-agents/10_tasks/` |

**Responsibilities:**
- Creates structured task notes with YAML frontmatter
- Updates task status (open → in-progress → done)
- Generates daily task summaries
- Surfaces overdue tasks

**Usage examples:**
```bash
python agents/task_agent.py create "Write nginx runbook" --priority high --project "Infra"
python agents/task_agent.py summary
python agents/task_agent.py overdue
```

---

## infra-agent

**File**: `packages/obsidian-agents/agents/infra_agent.py`

| Property | Value |
|---|---|
| Identity | `infra-agent` |
| Model | `gemini-2.0-flash` |
| Primary write vault | `vault-agents/60_logs/`, `vault-agents/40_knowledge/infra/` |

**Responsibilities:**
- Logs infrastructure events (service restarts, config changes, incidents)
- Maintains runbooks in `vault-agents/40_knowledge/infra/`
- Generates infra status snapshots

**Usage examples:**
```bash
python agents/infra_agent.py log "obsidian-mcp OOM kill, restarted" --severity warning --component obsidian-mcp
python agents/infra_agent.py snapshot
python agents/infra_agent.py runbook "nginx"
```

---

## writing-agent

**File**: `packages/obsidian-agents/agents/writing_agent.py`

| Property | Value |
|---|---|
| Identity | `writing-agent` |
| Model | `gemini-2.0-flash` |
| Primary write vault | `vault-agents/50_ideas/`, `vault-agents/40_knowledge/` |

**Responsibilities:**
- Drafts new idea notes from brief descriptions
- Refines and polishes drafts
- Promotes mature ideas to knowledge notes
- Can write human-facing notes to `vault-personal/40_knowledge/`

**Note lifecycle:**
```
50_ideas/<title>.md (status: draft)
        ↓  writing-agent refine
50_ideas/<title>.md (status: ready)
        ↓  writing-agent promote
40_knowledge/<title>.md (type: knowledge)
```

**Usage examples:**
```bash
python agents/writing_agent.py draft "Why event sourcing fits knowledge systems"
python agents/writing_agent.py refine vault-agents/50_ideas/event-sourcing.md
python agents/writing_agent.py promote vault-agents/50_ideas/event-sourcing.md --target vault-personal
```

---

## orchestration-agent

**File**: `packages/obsidian-agents/agents/orchestration_agent.py`

| Property | Value |
|---|---|
| Identity | `orchestration-agent` |
| Model | `gemini-2.0-flash` |
| Primary write vault | `vault-agents/20_projects/`, `vault-personal/00_inbox/` |

**Responsibilities:**
- Decomposes high-level goals into sub-tasks
- Creates and maintains project notes
- Runs periodic consolidation (agent → human vault)
- Maintains the agent index in `vault-agents/70_agents/`

**Unique privilege:** Can write to `vault-personal/00_inbox/` and `vault-personal/20_projects/` for human-review summaries.

**Usage examples:**
```bash
# Start a new project
python agents/orchestration_agent.py "Start project: AI Router Benchmarking suite"

# Weekly consolidation
python agents/orchestration_agent.py --consolidate

# Check a project
python agents/orchestration_agent.py --project-status "AI Router Benchmarking"

# Rebuild agent index
python agents/orchestration_agent.py --index
```

---

## Agent Access Matrix

| Agent | vault-personal read | vault-personal write | vault-agents read | vault-agents write |
|---|---|---|---|---|
| research-agent | `30_research/` | — | all | `30_research/`, `40_knowledge/`, `60_logs/` |
| task-agent | `10_tasks/` | — | `10_tasks/`, `20_projects/` | `10_tasks/`, `60_logs/` |
| infra-agent | full | — | full | `40_knowledge/infra/`, `60_logs/`, `70_agents/` |
| writing-agent | full | `40_knowledge/` | full | `50_ideas/`, `40_knowledge/`, `60_logs/` |
| orchestration-agent | full | `00_inbox/`, `20_projects/` | full | `20_projects/`, `60_logs/`, `70_agents/` |

> Note: MCP sandbox is at the vault level, not folder level. These are **policy conventions**
> enforced by each agent's system prompt, not OS-level ACLs.
