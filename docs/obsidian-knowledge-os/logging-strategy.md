# Logging Strategy

The system uses an **event sourcing** approach: logs are append-only Markdown files that record every significant event chronologically.

---

## Core Principle

> **Logs are immutable history.** Never edit or delete past log entries.
> Use `append_file` (never `write_file`) when adding log entries.

---

## Log Files

| File | Owner | Purpose |
|---|---|---|
| `vault-agents/70_agents/audit.log` | MCP server | All MCP tool calls (JSON) |
| `vault-agents/60_logs/infra-log.md` | infra-agent | Infrastructure events |
| `vault-agents/60_logs/research-log.md` | research-agent | Research progress |
| `vault-agents/60_logs/orchestration-log.md` | orchestration-agent | Planning decisions |
| `vault-agents/60_logs/sync-log.md` | vault-sync.sh | Git sync events |
| `<entity>/Log` section | Any agent | Per-note event history |

---

## Audit Log Format (JSON Lines)

The MCP server writes one JSON object per line to `70_agents/audit.log`:

```json
{"ts":"2026-05-28T14:00:00Z","tool":"write_file","path":"/opt/vaults/vault-agents/30_research/MCP.md","agent":"research-agent","size_bytes":2048}
{"ts":"2026-05-28T14:00:01Z","tool":"append_file","path":"/opt/vaults/vault-agents/60_logs/research-log.md","agent":"research-agent","appended_bytes":256}
{"ts":"2026-05-28T14:00:02Z","tool":"search","path":"query='MCP' vault=both","agent":"orchestration-agent","result_count":12}
```

Fields:
- `ts` — ISO 8601 UTC timestamp
- `tool` — MCP tool name
- `path` — resolved absolute path (or query string for search)
- `agent` — calling agent ID
- Additional tool-specific fields (`size_bytes`, `appended_bytes`, `result_count`)

**Querying the audit log:**
```bash
# All writes by research-agent today
grep '"agent":"research-agent"' /opt/vaults/vault-agents/70_agents/audit.log | grep '"tool":"write_file"'

# All operations in the last hour
grep "$(date -u +%Y-%m-%dT%H)" /opt/vaults/vault-agents/70_agents/audit.log
```

---

## Domain Log Format (Markdown)

Domain logs (`infra-log.md`, `research-log.md`, `orchestration-log.md`) use human-readable Markdown:

```markdown
## 2026-05-28T14:00:00Z
**Event**: obsidian-mcp restarted after OOM kill
**Severity**: warning
**Component**: obsidian-mcp
**Action taken**: Restarted via systemctl; increased MemoryMax to 512M in unit file
**Outcome**: Service running. No data loss.
**Related**: [[infra/obsidian-mcp Runbook]]
```

Agents always use `append_file` with this format. The `##` heading creates a navigable section in Obsidian.

---

## Per-Entity Log Sections

Each entity note (project, research, task) includes an embedded `## Log` section:

```markdown
## Log

### 2026-05-28T14:00:00Z
Task created by task-agent. Priority: high. Assigned to: writing-agent.

### 2026-05-28T16:00:00Z
Status changed: open → in-progress. Work started.

### 2026-05-29T10:00:00Z
Status changed: in-progress → done. PR merged.
```

This gives a per-entity timeline visible in Obsidian without leaving the note.

---

## Log Rotation

Logs are append-only and do not rotate automatically — they grow indefinitely as Markdown files.

**Recommended practice:**
- After 90 days, move old entries from domain logs to `90_archive/logs/<year>/`
- The audit log (`audit.log`) is plain text — rotate with `logrotate` on the server:

```ini
# /etc/logrotate.d/obsidian-audit
/opt/vaults/vault-agents/70_agents/audit.log {
    monthly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

---

## Event Types to Log

| Event | Log target | Severity |
|---|---|---|
| Service start/stop | `infra-log.md` | info |
| OOM/crash | `infra-log.md` | critical |
| Config change | `infra-log.md` | info |
| Agent task started | Per-entity log section | — |
| Agent task completed | Per-entity log section + domain log | — |
| Research milestone | `research-log.md` | info |
| Consolidation run | `orchestration-log.md` | info |
| Conflict resolution | `sync-log.md` | warning |
| Sandbox violation attempt | `audit.log` | critical (auto-logged by MCP) |
