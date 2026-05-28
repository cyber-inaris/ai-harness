#!/usr/bin/env bash
# =============================================================================
# bootstrap-vaults.sh
#
# Idempotent setup script for the Obsidian AI Knowledge OS vault structure.
# Creates both vaults at /opt/vaults/, seeds all directories and template files,
# initialises Git repos, and installs the Dataview plugin config.
#
# Usage:
#   sudo bash scripts/bootstrap-vaults.sh
#   sudo bash scripts/bootstrap-vaults.sh --dry-run   # print actions, no writes
#   sudo bash scripts/bootstrap-vaults.sh --vault-root /custom/path
#
# Idempotent: safe to re-run. Existing files are never overwritten.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
VAULT_ROOT="${OBSIDIAN_VAULT_ROOT:-/opt/vaults}"
VAULT_PERSONAL="${VAULT_ROOT}/vault-personal"
VAULT_AGENTS="${VAULT_ROOT}/vault-agents"
VAULT_USER="${SUDO_USER:-ai}"
DRY_RUN=false

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)       DRY_RUN=true; shift ;;
    --vault-root)    VAULT_ROOT="$2"; VAULT_PERSONAL="${VAULT_ROOT}/vault-personal"; VAULT_AGENTS="${VAULT_ROOT}/vault-agents"; shift 2 ;;
    --user)          VAULT_USER="$2"; shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()  { echo "  [INFO]  $*"; }
mkdir_p() { $DRY_RUN && echo "  [DRY]   mkdir -p $1" || mkdir -p "$1"; }
touch_if_missing() {
  local path="$1"
  if [[ -e "$path" ]]; then
    echo "  [SKIP]  $path already exists"
    return
  fi
  if $DRY_RUN; then
    echo "  [DRY]   create $path"
  else
    mkdir -p "$(dirname "$path")"
    cat > "$path"
  fi
}
git_init_if_needed() {
  local dir="$1"
  if [[ -d "${dir}/.git" ]]; then
    info "Git already initialised in $dir"
  else
    if $DRY_RUN; then
      echo "  [DRY]   git init $dir"
    else
      git -C "$dir" init -b main
      git -C "$dir" config user.name "obsidian-mcp"
      git -C "$dir" config user.email "obsidian-mcp@localhost"
    fi
    info "Git initialised: $dir"
  fi
}
chown_vault() {
  local dir="$1"
  if $DRY_RUN; then
    echo "  [DRY]   chown -R ${VAULT_USER}:${VAULT_USER} $dir"
  else
    chown -R "${VAULT_USER}:${VAULT_USER}" "$dir"
  fi
}

# ---------------------------------------------------------------------------
# Vault directory structure
# ---------------------------------------------------------------------------
DIRS=(
  "00_inbox"
  "10_tasks"
  "20_projects"
  "30_research"
  "40_knowledge"
  "40_knowledge/infra"
  "50_ideas"
  "60_logs"
  "70_agents"
  "90_archive"
)

echo ""
echo "======================================================="
echo " Obsidian AI Knowledge OS — Vault Bootstrap"
echo "======================================================="
echo " Vault root : $VAULT_ROOT"
echo " vault-personal : $VAULT_PERSONAL"
echo " vault-agents   : $VAULT_AGENTS"
echo " Owner      : $VAULT_USER"
$DRY_RUN && echo " Mode       : DRY RUN (no changes written)"
echo "======================================================="
echo ""

# ---------------------------------------------------------------------------
# Create vault root
# ---------------------------------------------------------------------------
info "Creating vault root directory"
mkdir_p "$VAULT_ROOT"

# ---------------------------------------------------------------------------
# vault-personal
# ---------------------------------------------------------------------------
info "Setting up vault-personal"
for d in "${DIRS[@]}"; do
  mkdir_p "${VAULT_PERSONAL}/${d}"
done

# Obsidian plugin config for Dataview (seeded, not overwritten)
OBSIDIAN_CFG_P="${VAULT_PERSONAL}/.obsidian"
mkdir_p "${OBSIDIAN_CFG_P}/plugins/dataview"

touch_if_missing "${OBSIDIAN_CFG_P}/app.json" << 'EOF'
{
  "useMarkdownLinks": false,
  "newLinkFormat": "shortest",
  "attachmentFolderPath": "90_archive/attachments"
}
EOF

touch_if_missing "${OBSIDIAN_CFG_P}/plugins/dataview/data.json" << 'EOF'
{
  "renderNullAs": "-",
  "taskCompletionTracking": true,
  "taskCompletionUseEmojiShorthand": false,
  "tableIdColumnName": "File",
  "tableGroupColumnName": "Group",
  "maxRecursiveRenderDepth": 4,
  "defaultDateFormat": "YYYY-MM-DD",
  "defaultDateTimeFormat": "YYYY-MM-DD HH:mm",
  "refreshInterval": 2500,
  "enableInlineDataview": true,
  "enableDataviewJs": true,
  "enableInlineDataviewJs": true
}
EOF

touch_if_missing "${OBSIDIAN_CFG_P}/community-plugins.json" << 'EOF'
["dataview"]
EOF

# Seed template files for vault-personal
touch_if_missing "${VAULT_PERSONAL}/00_inbox/README.md" << 'EOF'
# Inbox

Staging area for new notes, tasks, and ideas before they are processed.
Files here should be moved to the appropriate section once reviewed.

> **Rule**: Nothing stays in Inbox for more than 48 hours.
EOF

touch_if_missing "${VAULT_PERSONAL}/10_tasks/Dashboard.md" << 'DASHBOARD'
# Task Dashboard

```dataview
TABLE priority, status, due, project
FROM "10_tasks"
WHERE type = "task" AND status != "done"
SORT priority DESC, due ASC
```

## Overdue Tasks
```dataview
LIST
FROM "10_tasks"
WHERE type = "task" AND status != "done" AND due < date(today)
SORT due ASC
```
DASHBOARD

touch_if_missing "${VAULT_PERSONAL}/20_projects/Dashboard.md" << 'DASHBOARD'
# Project Dashboard

```dataview
TABLE status, priority, file.mtime AS "Last Modified"
FROM "20_projects"
WHERE type = "project"
SORT status ASC, priority DESC
```
DASHBOARD

touch_if_missing "${VAULT_PERSONAL}/30_research/Dashboard.md" << 'DASHBOARD'
# Research Dashboard

```dataview
LIST
FROM "30_research"
WHERE type = "research"
SORT file.mtime DESC
```
DASHBOARD

touch_if_missing "${VAULT_PERSONAL}/40_knowledge/README.md" << 'EOF'
# Knowledge Base

Refined, stable knowledge notes. Each note represents a well-understood concept,
tool, or system component.

Use [[wiki links]] to connect concepts.
EOF

touch_if_missing "${VAULT_PERSONAL}/60_logs/README.md" << 'EOF'
# Logs

Append-only event logs. Do not delete or edit past entries.

Log files:
- `infra-log.md` — Infrastructure events
- `research-log.md` — Research progress
- `orchestration-log.md` — Agent orchestration decisions
EOF

touch_if_missing "${VAULT_PERSONAL}/70_agents/README.md" << 'EOF'
# Agents

Agent entity notes and the agent index.
EOF

# ---------------------------------------------------------------------------
# vault-agents
# ---------------------------------------------------------------------------
info "Setting up vault-agents"
for d in "${DIRS[@]}"; do
  mkdir_p "${VAULT_AGENTS}/${d}"
done

# Obsidian plugin config (same as personal)
OBSIDIAN_CFG_A="${VAULT_AGENTS}/.obsidian"
mkdir_p "${OBSIDIAN_CFG_A}/plugins/dataview"

touch_if_missing "${OBSIDIAN_CFG_A}/app.json" << 'EOF'
{
  "useMarkdownLinks": false,
  "newLinkFormat": "shortest",
  "attachmentFolderPath": "90_archive/attachments"
}
EOF

touch_if_missing "${OBSIDIAN_CFG_A}/plugins/dataview/data.json" << 'EOF'
{
  "renderNullAs": "-",
  "taskCompletionTracking": true,
  "enableInlineDataview": true,
  "enableDataviewJs": true,
  "enableInlineDataviewJs": true,
  "refreshInterval": 2500
}
EOF

touch_if_missing "${OBSIDIAN_CFG_A}/community-plugins.json" << 'EOF'
["dataview"]
EOF

# Seed agent-specific files
touch_if_missing "${VAULT_AGENTS}/70_agents/agent-index.md" << 'EOF'
---
type: agent
status: active
created: 2026-01-01T00:00:00Z
tags: [agents, index]
---

# Agent Index

## research-agent
- **Role**: Conducts structured research from briefs
- **Primary vault**: vault-agents/30_research/
- **Last active**: —
- **Current task**: none

## task-agent
- **Role**: Manages task lifecycle
- **Primary vault**: vault-agents/10_tasks/
- **Last active**: —
- **Current task**: none

## infra-agent
- **Role**: Logs infra events and maintains runbooks
- **Primary vault**: vault-agents/40_knowledge/infra/
- **Last active**: —
- **Current task**: none

## writing-agent
- **Role**: Drafts and refines knowledge notes
- **Primary vault**: vault-agents/50_ideas/
- **Last active**: —
- **Current task**: none

## orchestration-agent
- **Role**: Coordinates agents and manages projects
- **Primary vault**: vault-agents/20_projects/
- **Last active**: —
- **Current task**: none
EOF

touch_if_missing "${VAULT_AGENTS}/70_agents/audit.log" << 'EOF'
EOF

touch_if_missing "${VAULT_AGENTS}/60_logs/infra-log.md" << 'EOF'
# Infrastructure Log

Append-only. Do not edit past entries.

---

## BOOT
System initialised by bootstrap-vaults.sh.
EOF

touch_if_missing "${VAULT_AGENTS}/60_logs/research-log.md" << 'EOF'
# Research Log

Append-only. Do not edit past entries.

---
EOF

touch_if_missing "${VAULT_AGENTS}/60_logs/orchestration-log.md" << 'EOF'
# Orchestration Log

Append-only. Do not edit past entries.

---
EOF

touch_if_missing "${VAULT_AGENTS}/10_tasks/Dashboard.md" << 'DASHBOARD'
# Agent Task Dashboard

```dataview
TABLE priority, status, due, assigned_to
FROM "10_tasks"
WHERE type = "task" AND status != "done"
SORT priority DESC, due ASC
```
DASHBOARD

touch_if_missing "${VAULT_AGENTS}/20_projects/Dashboard.md" << 'DASHBOARD'
# Agent Project Dashboard

```dataview
TABLE status, priority, owner, file.mtime AS "Last Updated"
FROM "20_projects"
WHERE type = "project"
SORT status ASC, priority DESC
```
DASHBOARD

touch_if_missing "${VAULT_AGENTS}/70_agents/Dashboard.md" << 'DASHBOARD'
# Agent Activity Dashboard

## Recent Audit Log Entries
> Read vault-agents/70_agents/audit.log for raw entries.

```dataview
TABLE file.mtime AS "Last Modified", status
FROM "70_agents"
WHERE type = "agent"
SORT file.mtime DESC
```
DASHBOARD

# ---------------------------------------------------------------------------
# Initialise Git repos
# ---------------------------------------------------------------------------
info "Initialising Git repositories"
git_init_if_needed "$VAULT_PERSONAL"
git_init_if_needed "$VAULT_AGENTS"

# Initial commit if clean
if ! $DRY_RUN; then
  for vault in "$VAULT_PERSONAL" "$VAULT_AGENTS"; do
    if [[ -z "$(git -C "$vault" log --oneline 2>/dev/null | head -1)" ]]; then
      git -C "$vault" add -A
      git -C "$vault" commit -m "chore: bootstrap vault structure" || true
    fi
  done
fi

# ---------------------------------------------------------------------------
# Fix ownership
# ---------------------------------------------------------------------------
info "Setting ownership to ${VAULT_USER}"
chown_vault "$VAULT_ROOT"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "======================================================="
echo " Bootstrap complete!"
echo "======================================================="
echo " vault-personal : ${VAULT_PERSONAL}"
echo " vault-agents   : ${VAULT_AGENTS}"
echo ""
echo " Next steps:"
echo "   1. Install pip deps:  cd packages/obsidian-mcp && pip install -r requirements.txt"
echo "   2. Start MCP server:  sudo systemctl enable --now obsidian-mcp"
echo "   3. Set up Git remote: see docs/obsidian-knowledge-os/git-sync-setup.md"
echo "   4. Open Obsidian on Mac and add vault-personal as a vault"
echo "   5. Install Dataview community plugin on first Obsidian launch"
echo "======================================================="
