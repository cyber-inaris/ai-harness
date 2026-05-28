# Workflow Walkthroughs

Four end-to-end workflows demonstrating how humans and agents collaborate through the vault.

---

## 1. Task Creation Flow

**Actors:** Human (Mac), task-agent
**Vaults touched:** `vault-personal/10_tasks/`, `vault-agents/10_tasks/`

### Human-initiated (in Obsidian on Mac)

Create a file in `vault-personal/10_tasks/`:

```markdown
---
type: task
status: open
priority: high
project: "[[AI Harness Docs]]"
due: 2026-05-30
created: 2026-05-28T14:00:00Z
tags: [task, docs]
---

# Review MCP documentation

## Description
Review and update the MCP server docs to reflect the SSE transport.

## Checklist
- [ ] Read current docs
- [ ] Identify outdated sections
- [ ] Write updates

## Log
### 2026-05-28T14:00:00Z
Task created by human.
```

Git sync (Mac LaunchAgent) pushes this to the server within 5 minutes.

### Agent-initiated (CLI on server)

```bash
python agents/task_agent.py create \
  "Benchmark OmniRouter latency on free-mod/gpt-5.5" \
  --priority high \
  --project "AI Router Benchmarking" \
  --due 2026-06-01
```

The task-agent:
1. `search(vault="vault-agents", query="AI Router Benchmarking")` — checks existing tasks
2. `create_file("vault-agents/10_tasks/2026-05-28-benchmark-omnirouter.md", content)` — creates the task
3. `append_file("vault-agents/60_logs/orchestration-log.md", log_entry)` — logs it

---

## 2. Research Flow

**Actors:** Human (writes brief), research-agent (conducts research)
**Vaults touched:** `vault-personal/30_research/` → `vault-agents/30_research/`, `vault-agents/40_knowledge/`

### Step 1: Human writes a research brief (Mac Obsidian)

```markdown
# vault-personal/30_research/mcp-adoption-brief.md

---
type: research
status: active
priority: high
created: 2026-05-28
tags: [research, mcp, brief]
---

# Research Brief: MCP Protocol Adoption

## Question
What is the current state of MCP adoption in the AI agent ecosystem as of 2026?

## Scope
- Frameworks: LangChain, CrewAI, AutoGen, smolagents
- Companies: Anthropic, OpenAI, Google DeepMind

## Deliverable
Structured research note with sources and entity notes for each major implementation.
```

### Step 2: Run research agent on server

```bash
python agents/research_agent.py --brief vault-personal/30_research/mcp-adoption-brief.md
```

MCP calls made by the agent:
1. `read_file("vault-personal/30_research/mcp-adoption-brief.md")` — reads brief
2. `search(query="MCP", vault="vault-agents")` — checks existing research
3. (web_search tool calls for actual research)
4. `create_file("vault-agents/30_research/MCP Protocol Adoption.md", full_note)`
5. `create_file("vault-agents/40_knowledge/Model Context Protocol.md", entity_note)`
6. `append_file("vault-agents/60_logs/research-log.md", log_entry)`

### Step 3: Consolidate for human review

```bash
python agents/orchestration_agent.py --consolidate
```

Writes `vault-personal/00_inbox/MCP-Adoption-Research-Update.md`.
Human reviews in Obsidian, then files it into `40_knowledge/` or `90_archive/`.

---

## 3. Agent Memory Flow

**Actors:** Any agent, orchestration-agent
**Vaults touched:** `vault-agents/70_agents/`, `vault-agents/60_logs/`

### Agent writes activity to memory

After completing any significant task, agents update the audit trail:

```bash
python agents/infra_agent.py log \
  "obsidian-mcp restarted after memory pressure" \
  --severity warning \
  --component obsidian-mcp
```

MCP calls:
1. `append_file("vault-agents/60_logs/infra-log.md", structured_entry)`
2. `read_file("vault-agents/70_agents/agent-index.md")`
3. `write_file("vault-agents/70_agents/agent-index.md", updated_with_last_active)`

### Orchestration rebuilds the index weekly

```bash
python agents/orchestration_agent.py --index
```

The orchestration-agent scans all `60_logs/` files for timestamps, then rewrites `70_agents/agent-index.md` with current `last_active` and `current_task` fields.

### Human views agent activity in Obsidian

The Dataview dashboard at `vault-agents/70_agents/Dashboard.md` shows:

```dataview
TABLE status, file.mtime AS "Last Active"
FROM "70_agents"
WHERE type = "agent"
SORT file.mtime DESC
```

The MCP audit log (`70_agents/audit.log`) provides full forensic trail:
```bash
tail -f /opt/vaults/vault-agents/70_agents/audit.log | jq .
```

---

## 4. Project Lifecycle Flow

**Actors:** Human, orchestration-agent, research-agent, task-agent, writing-agent

```
Human intent
    │
    ▼
orchestration-agent (creates project note, decomposes tasks)
    │
    ├──→ research-agent (gathers context)
    ├──→ task-agent (creates execution tasks)
    └──→ writing-agent (documents findings)
    │
    ▼
orchestration-agent (consolidates → vault-personal/00_inbox/)
    │
    ▼
Human reviews in Obsidian → archives or promotes
```

### Phase 1: Initiation

```bash
python agents/orchestration_agent.py \
  "Start project: AI Router Benchmarking Suite. Goal: evaluate 5 routers on latency, quality, cost."
```

Creates: `vault-agents/20_projects/AI Router Benchmarking Suite.md`

### Phase 2: Task Decomposition

The project note is populated with a task checklist and agent assignments:

```markdown
## Tasks
- [ ] Research router landscape — research-agent
- [ ] Set up benchmark harness — task-agent
- [ ] Run latency tests — task-agent
- [ ] Document methodology — writing-agent
```

### Phase 3: Parallel Execution

Each agent runs independently on its assigned work:

```bash
python agents/research_agent.py "Research AI router landscape — OmniRouter, LiteLLM, Helicone"
python agents/task_agent.py create "Set up benchmark harness" --project "AI Router Benchmarking Suite"
python agents/writing_agent.py draft "Benchmark scoring methodology for AI routers"
```

Each agent appends to the project note's `## Log` section as work progresses.

### Phase 4: Consolidation

```bash
python agents/orchestration_agent.py --project-status "AI Router Benchmarking Suite"
python agents/orchestration_agent.py --consolidate
```

Writes final summary to `vault-personal/00_inbox/AI-Router-Benchmarking-Complete.md`.
Updates project status to `done`.

### Phase 5: Human Archive

Human reviews the inbox note in Obsidian:
- Promotes key findings to `vault-personal/40_knowledge/`
- Archives the project note to `vault-personal/90_archive/projects/`
- Moves agent project note to `vault-agents/90_archive/`
