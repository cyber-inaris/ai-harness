"""
Configuration for the Obsidian MCP server.

All settings can be overridden via environment variables.
Vault paths default to /opt/vaults/ — system-level, not repo-specific.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Vault roots
# ---------------------------------------------------------------------------

_DEFAULT_VAULT_ROOT = "/opt/vaults"

VAULT_ROOT = Path(os.environ.get("OBSIDIAN_VAULT_ROOT", _DEFAULT_VAULT_ROOT)).resolve()

VAULT_PERSONAL = Path(
    os.environ.get("OBSIDIAN_VAULT_PERSONAL", str(VAULT_ROOT / "vault-personal"))
).resolve()

VAULT_AGENTS = Path(
    os.environ.get("OBSIDIAN_VAULT_AGENTS", str(VAULT_ROOT / "vault-agents"))
).resolve()

# Allowed sandbox roots — any file operation must resolve inside one of these
ALLOWED_ROOTS: tuple[Path, ...] = (VAULT_PERSONAL, VAULT_AGENTS)

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

MCP_HOST = os.environ.get("OBSIDIAN_MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.environ.get("OBSIDIAN_MCP_PORT", "3000"))

# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

AUDIT_LOG_PATH = Path(
    os.environ.get(
        "OBSIDIAN_AUDIT_LOG",
        str(VAULT_AGENTS / "70_agents" / "audit.log"),
    )
).resolve()

# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

# Maximum number of files returned by the search tool
SEARCH_MAX_RESULTS = int(os.environ.get("OBSIDIAN_SEARCH_MAX_RESULTS", "50"))

# Maximum content bytes read per file during search (avoids huge files)
SEARCH_MAX_FILE_BYTES = int(os.environ.get("OBSIDIAN_SEARCH_MAX_FILE_BYTES", str(512 * 1024)))
