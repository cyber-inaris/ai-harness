"""
Obsidian MCP Server
===================

Production-ready FastMCP server exposing structured vault operations over SSE.

Design principles:
  - All paths are sandboxed to /opt/vaults/vault-personal and /opt/vaults/vault-agents
  - File writes use POSIX advisory locking (fcntl.flock) for safe concurrency
  - Every operation is written to the append-only audit log
  - The server exposes exactly six tools:
      read_file, write_file, append_file, create_file, list_dir, search

Run:
    python server.py                     # SSE on 127.0.0.1:3000
    OBSIDIAN_MCP_PORT=3001 python server.py
"""

from __future__ import annotations

import asyncio
import fcntl
import fnmatch
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

import config as cfg

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("obsidian-mcp")

# ---------------------------------------------------------------------------
# MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="obsidian-mcp",
    instructions=(
        "You have structured, sandboxed access to two Obsidian vaults:\n"
        "  • vault-personal — human workspace (read/write)\n"
        "  • vault-agents   — agent workspace (read/write, agent primary)\n\n"
        "All paths must be relative to a vault root, e.g. "
        "'vault-personal/10_tasks/my-task.md'.\n"
        "Use append_file for logs. Use write_file only to replace whole notes.\n"
        "Never traverse outside the vault roots."
    ),
)

# ---------------------------------------------------------------------------
# Path sandboxing helpers
# ---------------------------------------------------------------------------


def _resolve_vault_path(relative_path: str) -> Path:
    """
    Resolve *relative_path* against the allowed vault roots.

    Accepts paths of the form:
        vault-personal/10_tasks/foo.md
        vault-agents/70_agents/bar.md
        /opt/vaults/vault-personal/10_tasks/foo.md  (absolute, validated)

    Raises ValueError if the resolved path is outside all allowed roots.
    """
    raw = Path(relative_path)

    # If absolute, validate directly
    if raw.is_absolute():
        resolved = raw.resolve()
    else:
        # Try to match the first component against a vault root directory name
        parts = raw.parts
        matched_root: Path | None = None
        for root in cfg.ALLOWED_ROOTS:
            if parts and parts[0] == root.name:
                matched_root = root
                inner = Path(*parts[1:]) if len(parts) > 1 else Path(".")
                resolved = (root / inner).resolve()
                break
        if matched_root is None:
            # Fall back: try resolving relative to each root (legacy behaviour)
            # Use the first root that contains the resolved path
            for root in cfg.ALLOWED_ROOTS:
                candidate = (root / raw).resolve()
                try:
                    candidate.relative_to(root)
                    resolved = candidate
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(
                    f"Path '{relative_path}' could not be resolved inside any allowed vault. "
                    f"Prefix with 'vault-personal/' or 'vault-agents/'."
                )

    # Final sandbox check
    for root in cfg.ALLOWED_ROOTS:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue

    raise ValueError(
        f"Access denied: '{resolved}' is outside the allowed vault roots "
        f"({', '.join(str(r) for r in cfg.ALLOWED_ROOTS)})."
    )


def _ensure_parents(path: Path) -> None:
    """Create parent directories if they do not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------

_audit_lock = asyncio.Lock()


async def _audit(tool: str, path: str, agent: str = "unknown", extra: dict | None = None) -> None:
    """Append a structured JSON line to the audit log."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "path": path,
        "agent": agent,
        **(extra or {}),
    }
    line = json.dumps(entry, ensure_ascii=False) + "\n"

    async with _audit_lock:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _write_audit_line, line)


def _write_audit_line(line: str) -> None:
    """Synchronous audit write with POSIX lock."""
    _ensure_parents(cfg.AUDIT_LOG_PATH)
    with open(cfg.AUDIT_LOG_PATH, "a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(line)
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# File I/O helpers (blocking, run in executor)
# ---------------------------------------------------------------------------


def _sync_read(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_SH)
        try:
            return fh.read()
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _sync_write(path: Path, content: str) -> None:
    _ensure_parents(path)
    with open(path, "w", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(content)
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _sync_append(path: Path, content: str) -> None:
    _ensure_parents(path)
    with open(path, "a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(content)
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _sync_create(path: Path, content: str) -> None:
    _ensure_parents(path)
    # x-mode raises FileExistsError if the file already exists
    with open(path, "x", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(content)
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


@mcp.tool()
async def read_file(path: str, agent: str = "unknown") -> dict[str, Any]:
    """
    Read the full contents of a vault file.

    Args:
        path:  Vault-relative path, e.g. 'vault-personal/10_tasks/foo.md'
        agent: Identifier of the calling agent (for audit log)

    Returns:
        {"path": str, "content": str, "size_bytes": int}
    """
    resolved = _resolve_vault_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not resolved.is_file():
        raise IsADirectoryError(f"Path is a directory, not a file: {path}")

    loop = asyncio.get_event_loop()
    content = await loop.run_in_executor(None, _sync_read, resolved)
    await _audit("read_file", str(resolved), agent)
    return {"path": str(resolved), "content": content, "size_bytes": len(content.encode())}


@mcp.tool()
async def write_file(path: str, content: str, agent: str = "unknown") -> dict[str, Any]:
    """
    Overwrite (or create) a vault file with new content.
    Use this to replace the full content of a note.
    For appending log entries, use append_file instead.

    Args:
        path:    Vault-relative path
        content: Full Markdown content (including YAML frontmatter if applicable)
        agent:   Identifier of the calling agent

    Returns:
        {"path": str, "size_bytes": int, "action": "written"}
    """
    resolved = _resolve_vault_path(path)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_write, resolved, content)
    await _audit("write_file", str(resolved), agent, {"size_bytes": len(content.encode())})
    return {"path": str(resolved), "size_bytes": len(content.encode()), "action": "written"}


@mcp.tool()
async def append_file(path: str, content: str, agent: str = "unknown") -> dict[str, Any]:
    """
    Append content to an existing vault file (creates it if it doesn't exist).
    Designed for event-sourcing log entries:

        ## 2026-05-28T16:00:00Z
        Research step completed. Found 3 sources on topic X.

    Args:
        path:    Vault-relative path
        content: Markdown content to append (newline-separated)
        agent:   Identifier of the calling agent

    Returns:
        {"path": str, "appended_bytes": int, "action": "appended"}
    """
    resolved = _resolve_vault_path(path)
    # Ensure content ends with newline
    if not content.endswith("\n"):
        content += "\n"
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _sync_append, resolved, content)
    await _audit("append_file", str(resolved), agent, {"appended_bytes": len(content.encode())})
    return {"path": str(resolved), "appended_bytes": len(content.encode()), "action": "appended"}


@mcp.tool()
async def create_file(path: str, content: str, agent: str = "unknown") -> dict[str, Any]:
    """
    Create a new vault file. Fails if the file already exists.
    Use write_file if you want upsert behaviour.

    Args:
        path:    Vault-relative path for the new file
        content: Initial Markdown content (YAML frontmatter recommended)
        agent:   Identifier of the calling agent

    Returns:
        {"path": str, "size_bytes": int, "action": "created"}
    """
    resolved = _resolve_vault_path(path)
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, _sync_create, resolved, content)
    except FileExistsError:
        raise FileExistsError(
            f"File already exists: {path}. Use write_file to overwrite."
        )
    await _audit("create_file", str(resolved), agent, {"size_bytes": len(content.encode())})
    return {"path": str(resolved), "size_bytes": len(content.encode()), "action": "created"}


@mcp.tool()
async def list_dir(path: str, agent: str = "unknown") -> dict[str, Any]:
    """
    List the contents of a vault directory.

    Args:
        path:  Vault-relative directory path, e.g. 'vault-agents/30_research'
        agent: Identifier of the calling agent

    Returns:
        {"path": str, "entries": [{"name": str, "type": "file"|"dir", "size_bytes": int|None}]}
    """
    resolved = _resolve_vault_path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Path is a file, not a directory: {path}")

    entries = []
    for child in sorted(resolved.iterdir()):
        entry: dict[str, Any] = {
            "name": child.name,
            "type": "dir" if child.is_dir() else "file",
        }
        if child.is_file():
            entry["size_bytes"] = child.stat().st_size
        entries.append(entry)

    await _audit("list_dir", str(resolved), agent, {"entry_count": len(entries)})
    return {"path": str(resolved), "entries": entries}


@mcp.tool()
async def search(
    query: str,
    vault: str = "both",
    agent: str = "unknown",
    glob: str = "*.md",
    case_sensitive: bool = False,
) -> dict[str, Any]:
    """
    Full-text search across vault files.

    Args:
        query:          Text or regex pattern to search for
        vault:          Which vault to search: 'vault-personal', 'vault-agents', or 'both'
        agent:          Identifier of the calling agent
        glob:           File glob pattern (default '*.md')
        case_sensitive: Whether to match case-sensitively (default False)

    Returns:
        {"query": str, "matches": [{"path": str, "line": int, "snippet": str}], "total": int}
    """
    # Select search roots
    vault_map = {
        "vault-personal": [cfg.VAULT_PERSONAL],
        "vault-agents": [cfg.VAULT_AGENTS],
        "both": list(cfg.ALLOWED_ROOTS),
    }
    if vault not in vault_map:
        raise ValueError(f"vault must be one of: {', '.join(vault_map)}")
    roots = vault_map[vault]

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags)
    except re.error as exc:
        # Treat as literal string if invalid regex
        pattern = re.compile(re.escape(query), flags)

    matches: list[dict[str, Any]] = []
    loop = asyncio.get_event_loop()

    def _search_files() -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        for root in roots:
            for filepath in root.rglob(glob):
                if not filepath.is_file():
                    continue
                if filepath.stat().st_size > cfg.SEARCH_MAX_FILE_BYTES:
                    continue
                try:
                    text = filepath.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for lineno, line in enumerate(text.splitlines(), start=1):
                    if pattern.search(line):
                        found.append(
                            {
                                "path": str(filepath),
                                "line": lineno,
                                "snippet": line.strip()[:200],
                            }
                        )
                        if len(found) >= cfg.SEARCH_MAX_RESULTS:
                            return found
        return found

    matches = await loop.run_in_executor(None, _search_files)
    await _audit(
        "search",
        f"query={query!r} vault={vault}",
        agent,
        {"result_count": len(matches)},
    )
    return {"query": query, "vault": vault, "matches": matches, "total": len(matches)}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    log.info("Starting Obsidian MCP server on %s:%d", cfg.MCP_HOST, cfg.MCP_PORT)
    log.info("Vault personal : %s", cfg.VAULT_PERSONAL)
    log.info("Vault agents   : %s", cfg.VAULT_AGENTS)
    log.info("Audit log      : %s", cfg.AUDIT_LOG_PATH)

    # FastMCP exposes a Starlette ASGI app via .sse_app()
    uvicorn.run(
        mcp.sse_app(),
        host=cfg.MCP_HOST,
        port=cfg.MCP_PORT,
        log_level="info",
        access_log=True,
    )
