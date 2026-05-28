#!/usr/bin/env bash
# =============================================================================
# vault-sync.sh
#
# Bi-directional Git sync for the two Obsidian vaults.
#
# Source-of-truth strategy:
#   vault-personal  →  Mac is SoT.  Server pulls Mac changes then pushes back.
#   vault-agents    →  Server is SoT. Server commits and pushes; Mac only pulls.
#
# Conflict resolution:
#   vault-personal: timestamp-based — newer file wins.
#   vault-agents:   server always wins (agent data, not human-edited).
#
# Usage:
#   bash scripts/vault-sync.sh                   # sync both vaults
#   bash scripts/vault-sync.sh --vault personal  # sync only vault-personal
#   bash scripts/vault-sync.sh --vault agents    # sync only vault-agents
#   bash scripts/vault-sync.sh --dry-run
#
# Designed to be called by vault-sync.service (systemd).
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VAULT_ROOT="${OBSIDIAN_VAULT_ROOT:-/opt/vaults}"
VAULT_PERSONAL="${VAULT_ROOT}/vault-personal"
VAULT_AGENTS="${VAULT_ROOT}/vault-agents"
LOG_FILE="${VAULT_AGENTS}/60_logs/sync-log.md"

# Remote names (set these after adding git remotes)
PERSONAL_REMOTE="${VAULT_PERSONAL_REMOTE:-origin}"
AGENTS_REMOTE="${VAULT_AGENTS_REMOTE:-origin}"

DRY_RUN=false
SYNC_TARGET="both"  # personal | agents | both

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)         DRY_RUN=true; shift ;;
    --vault)           SYNC_TARGET="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ts()   { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
info() { echo "[$(ts)] [INFO]  $*"; }
warn() { echo "[$(ts)] [WARN]  $*"; }
err()  { echo "[$(ts)] [ERROR] $*" >&2; }

run() {
  if $DRY_RUN; then
    echo "[DRY] $*"
  else
    "$@"
  fi
}

append_sync_log() {
  local msg="$1"
  if ! $DRY_RUN && [[ -d "${VAULT_AGENTS}/60_logs" ]]; then
    printf '\n## %s\n%s\n' "$(ts)" "$msg" >> "$LOG_FILE"
  fi
}

has_remote() {
  local vault="$1" remote="$2"
  git -C "$vault" remote get-url "$remote" &>/dev/null
}

# ---------------------------------------------------------------------------
# vault-agents sync (Server is SoT)
# ---------------------------------------------------------------------------
sync_agents() {
  local vault="$VAULT_AGENTS"
  info "Syncing vault-agents (server SoT)…"

  if ! has_remote "$vault" "$AGENTS_REMOTE"; then
    warn "vault-agents has no remote '$AGENTS_REMOTE' — skipping push. Run git remote add first."
    return 0
  fi

  # Commit any uncommitted agent writes
  if [[ -n "$(git -C "$vault" status --porcelain)" ]]; then
    run git -C "$vault" add -A
    run git -C "$vault" commit -m "chore(agents): auto-sync $(ts)"
  fi

  # Push to remote (Mac will pull this)
  run git -C "$vault" push "$AGENTS_REMOTE" main

  info "vault-agents sync complete"
  append_sync_log "vault-agents synced to remote (server SoT push)."
}

# ---------------------------------------------------------------------------
# vault-personal sync (Mac is SoT)
# ---------------------------------------------------------------------------
sync_personal() {
  local vault="$VAULT_PERSONAL"
  info "Syncing vault-personal (mac SoT)…"

  if ! has_remote "$vault" "$PERSONAL_REMOTE"; then
    warn "vault-personal has no remote '$PERSONAL_REMOTE' — skipping. Run git remote add first."
    return 0
  fi

  # Commit any local server-side changes first (e.g. agent consolidation writes)
  if [[ -n "$(git -C "$vault" status --porcelain)" ]]; then
    run git -C "$vault" add -A
    run git -C "$vault" commit -m "chore(server): pre-sync commit $(ts)"
  fi

  # Fetch latest from Mac
  run git -C "$vault" fetch "$PERSONAL_REMOTE" main

  # Check for divergence
  local_rev=$(git -C "$vault" rev-parse HEAD)
  remote_rev=$(git -C "$vault" rev-parse "${PERSONAL_REMOTE}/main")

  if [[ "$local_rev" == "$remote_rev" ]]; then
    info "vault-personal already up to date"
    return 0
  fi

  # Attempt rebase (cleaner history)
  if run git -C "$vault" rebase "${PERSONAL_REMOTE}/main" 2>/dev/null; then
    info "vault-personal rebased onto mac changes"
    run git -C "$vault" push "$PERSONAL_REMOTE" main
    append_sync_log "vault-personal synced via rebase (mac SoT)."
    return 0
  fi

  # Rebase failed — abort and use timestamp merge strategy
  warn "Rebase conflict in vault-personal — falling back to timestamp merge"
  run git -C "$vault" rebase --abort 2>/dev/null || true

  # For each conflicting file: keep the version with the newer mtime
  run git -C "$vault" merge --no-commit --no-ff "${PERSONAL_REMOTE}/main" 2>/dev/null || true

  local conflicts
  conflicts=$(git -C "$vault" diff --name-only --diff-filter=U 2>/dev/null || true)
  if [[ -n "$conflicts" ]]; then
    while IFS= read -r file; do
      local_mtime remote_mtime
      local_mtime=$(stat -c %Y "${vault}/${file}" 2>/dev/null || echo 0)
      # Get remote version's commit time as proxy
      remote_mtime=$(git -C "$vault" log -1 --format="%ct" "${PERSONAL_REMOTE}/main" -- "$file" 2>/dev/null || echo 0)

      if (( remote_mtime > local_mtime )); then
        warn "Conflict in $file — keeping remote (mac) version (newer by timestamp)"
        run git -C "$vault" checkout "${PERSONAL_REMOTE}/main" -- "$file"
      else
        warn "Conflict in $file — keeping local (server) version (newer by timestamp)"
        run git -C "$vault" checkout --ours -- "$file"
      fi
      run git -C "$vault" add "$file"
    done <<< "$conflicts"
  fi

  run git -C "$vault" commit -m "chore: resolve sync conflicts via timestamp strategy $(ts)" || true
  run git -C "$vault" push "$PERSONAL_REMOTE" main
  append_sync_log "vault-personal merged with timestamp conflict resolution."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
info "=== vault-sync starting (target: $SYNC_TARGET) ==="

case "$SYNC_TARGET" in
  agents)   sync_agents ;;
  personal) sync_personal ;;
  both)     sync_agents; sync_personal ;;
  *) err "Unknown --vault target: $SYNC_TARGET (use: personal | agents | both)"; exit 1 ;;
esac

info "=== vault-sync complete ==="
