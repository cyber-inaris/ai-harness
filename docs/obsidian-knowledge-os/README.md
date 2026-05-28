# Obsidian AI Knowledge OS

A production-ready AI-native knowledge system that uses Obsidian as the filesystem-native memory layer for both humans and autonomous agents.

## System Overview

```text
Obsidian (Mac) ←──── Git sync ────→ /opt/vaults/ (Server)
                                           │
                                    FastMCP SSE :3000
                                           │
                     ┌─────────────────────┼──────────────────────┐
                     │                     │                      │
               research-agent        task-agent           orchestration-agent
               infra-agent           writing-agent
```

| Layer | Technology | Role |
|---|---|---|
| Knowledge store | Two Obsidian vaults | Human + agent memory |
| Execution bridge | FastMCP SSE server | Safe, sandboxed vault I/O |
| AI agents | Google Antigravity SDK | 5 specialist agents |
| Query engine | Dataview plugin | Virtual database over markdown |
| Sync | Git (SSH/Tailscale) | Bi-directional Mac ↔ Server |
| Process mgmt | Systemd | Services + 5-min sync timer |

## Quick Start

### 1. Bootstrap vaults on the server

```bash
# On the server, as root or with sudo
sudo bash /opt/ai-harness/repo/scripts/bootstrap-vaults.sh
```

This creates `/opt/vaults/vault-personal` and `/opt/vaults/vault-agents` with the full folder structure, template files, and Git repos.

### 2. Install MCP server

```bash
# Create virtualenv and install deps
python3 -m venv /opt/ai-harness/venv/obsidian-mcp
source /opt/ai-harness/venv/obsidian-mcp/bin/activate
pip install -r /opt/ai-harness/repo/packages/obsidian-mcp/requirements.txt

# Install and start the systemd service
sudo cp /opt/ai-harness/repo/ops/systemd/obsidian-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now obsidian-mcp

# Verify
sudo systemctl status obsidian-mcp
curl -s http://127.0.0.1:3000/  # should return MCP server info
```

### 3. Install vault sync timer

```bash
sudo cp /opt/ai-harness/repo/ops/systemd/vault-sync.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vault-sync.timer

# Verify
systemctl list-timers vault-sync.timer
```

### 4. Set up Mac client

See [git-sync-setup.md](git-sync-setup.md) for the full Mac setup including SSH keys and Obsidian vault connection.

### 5. Install agent dependencies

```bash
python3 -m venv /opt/ai-harness/venv/obsidian-agents
source /opt/ai-harness/venv/obsidian-agents/bin/activate
pip install -r /opt/ai-harness/repo/packages/obsidian-agents/requirements.txt
export GEMINI_API_KEY=your-key-here
```

### 6. Run your first agent

```bash
cd /opt/ai-harness/repo/packages/obsidian-agents
python agents/research_agent.py "Research the current state of Model Context Protocol (MCP) adoption"
```

## Key Concepts

### Vault Roles

| Vault | Source of Truth | Primary Editor |
|---|---|---|
| `vault-personal` | Mac (human) | Human via Obsidian |
| `vault-agents` | Server | Agents via MCP |

### Folder Structure

```
/opt/vaults/<vault>/
├── 00_inbox/       ← Ingestion staging (< 48h retention)
├── 10_tasks/       ← Task notes + Dataview dashboard
├── 20_projects/    ← Project entity notes
├── 30_research/    ← Research notes and briefs
├── 40_knowledge/   ← Refined knowledge + runbooks
├── 50_ideas/       ← Drafts and idea notes
├── 60_logs/        ← Append-only event logs
├── 70_agents/      ← Agent memory, index, audit log
└── 90_archive/     ← Cold storage
```

### MCP Tool Contracts

| Tool | Description |
|---|---|
| `read_file(path, agent)` | Read a vault file |
| `write_file(path, content, agent)` | Replace a file (upsert) |
| `append_file(path, content, agent)` | Append to a file (log pattern) |
| `create_file(path, content, agent)` | Create new file (fails if exists) |
| `list_dir(path, agent)` | List directory contents |
| `search(query, vault, agent)` | Full-text search across vault |

All tools require the `agent` parameter (agent identity) for audit logging.

## Documentation Index

| Document | Description |
|---|---|
| [vault-structure.md](vault-structure.md) | Full vault folder tree and naming conventions |
| [git-sync-setup.md](git-sync-setup.md) | Mac client setup and SSH git remotes |
| [dataview-dashboards.md](dataview-dashboards.md) | All Dataview query examples |
| [agent-definitions.md](agent-definitions.md) | Per-agent roles, scope, and examples |
| [logging-strategy.md](logging-strategy.md) | Event sourcing approach and log formats |
| [workflows.md](workflows.md) | End-to-end workflow walkthroughs |
