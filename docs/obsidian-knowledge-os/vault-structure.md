# Vault Structure

Full directory layout for both vaults. Created by `scripts/bootstrap-vaults.sh`.

## /opt/vaults/vault-personal

```
vault-personal/
├── .obsidian/
│   ├── app.json                        # Obsidian settings (wiki links, attachments)
│   ├── community-plugins.json          # ["dataview"]
│   └── plugins/dataview/data.json      # Dataview plugin config
│
├── 00_inbox/
│   ├── README.md                       # Inbox rules (48h retention)
│   └── Dashboard.md                    # Dataview: pending + stale items
│
├── 10_tasks/
│   ├── Dashboard.md                    # Dataview: open tasks, overdue, completed
│   └── YYYY-MM-DD-<task-name>.md       # Individual task notes
│
├── 20_projects/
│   ├── Dashboard.md                    # Dataview: all projects by status
│   └── <Project Name>.md              # Project entity notes
│
├── 30_research/
│   ├── Dashboard.md                    # Dataview: research notes list
│   └── <Topic>.md                     # Research briefs (human-written)
│
├── 40_knowledge/
│   ├── README.md                       # Knowledge base rules
│   ├── infra/                          # (optional: human infra knowledge)
│   └── <Concept Name>.md              # Promoted knowledge notes
│
├── 50_ideas/
│   └── <Idea Title>.md                # Human drafts and ideas
│
├── 60_logs/
│   └── README.md                       # Log rules
│
├── 70_agents/
│   └── README.md                       # Agent area (read-only for humans here)
│
└── 90_archive/
    ├── projects/                       # Archived project notes
    ├── tasks/                          # Archived task notes
    └── research/                       # Archived research notes
```

---

## /opt/vaults/vault-agents

```
vault-agents/
├── .obsidian/
│   ├── app.json
│   ├── community-plugins.json          # ["dataview"]
│   └── plugins/dataview/data.json
│
├── 00_inbox/
│   └── (agent staging — rarely used)
│
├── 10_tasks/
│   ├── Dashboard.md                    # Dataview: agent task queue
│   └── YYYY-MM-DD-<task-name>.md       # Agent-created tasks
│
├── 20_projects/
│   ├── Dashboard.md                    # Dataview: active projects
│   └── <Project Name>.md              # Full project entity notes
│
├── 30_research/
│   ├── Dashboard.md
│   └── <Topic>.md                     # Agent research findings
│
├── 40_knowledge/
│   ├── <Concept Name>.md              # Agent-promoted knowledge
│   └── infra/
│       └── <Component>.md             # Infrastructure runbooks (infra-agent)
│
├── 50_ideas/
│   └── <Draft Title>.md               # Writing-agent drafts
│
├── 60_logs/
│   ├── README.md
│   ├── infra-log.md                   # Infrastructure events (infra-agent)
│   ├── research-log.md                # Research progress (research-agent)
│   ├── orchestration-log.md           # Agent decisions (orchestration-agent)
│   └── sync-log.md                    # Git sync events (vault-sync.sh)
│
├── 70_agents/
│   ├── Dashboard.md                    # Dataview: agent activity
│   ├── agent-index.md                  # Agent registry + last-active timestamps
│   └── audit.log                       # MCP server audit log (JSON lines)
│
└── 90_archive/
    ├── projects/
    ├── tasks/
    └── research/
```

---

## Naming Conventions

| Type | Pattern | Example |
|---|---|---|
| Task notes | `YYYY-MM-DD-kebab-title.md` | `2026-05-28-review-mcp-docs.md` |
| Project notes | `Title Case.md` | `AI Router Benchmarking Suite.md` |
| Research notes | `Topic Name.md` | `MCP Protocol Adoption.md` |
| Knowledge notes | `Concept Name.md` | `Model Context Protocol.md` |
| Idea notes | `Draft Title.md` | `Event Sourcing for Knowledge.md` |
| Infra runbooks | `Component Name.md` | `nginx.md`, `obsidian-mcp.md` |

## YAML Frontmatter Schema

```yaml
---
# Required for all structured notes
type: task | project | research | knowledge | idea | agent

# Status (type-specific values)
status:
  task:       open | in-progress | done | blocked
  project:    active | paused | done | cancelled
  research:   active | done
  knowledge:  active | deprecated
  idea:       draft | refining | ready | promoted

# Shared optional fields
priority: low | medium | high | critical
created: 2026-05-28                        # ISO date
tags: [tag1, tag2]

# Task-specific
due: 2026-06-01
project: "[[Project Name]]"
assigned_to: human | task-agent | research-agent

# Project-specific
owner: human | orchestration-agent
completed: null | 2026-06-15

# Knowledge-specific
subtype: runbook | concept | reference

# Research-specific
related: ["[[Entity A]]", "[[Entity B]]"]
---
```
