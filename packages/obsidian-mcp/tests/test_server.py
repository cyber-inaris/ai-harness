"""
Tests for the Obsidian MCP server.

Uses pytest with a temporary vault root so tests are fully isolated
from /opt/vaults on the real server.

Run:
    cd packages/obsidian-mcp
    pip install -r requirements.txt pytest pytest-asyncio
    pytest tests/ -v
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Patch config before importing server
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="session")
def _temp_vaults(tmp_path_factory):
    """Create isolated vault roots for the test session."""
    root = tmp_path_factory.mktemp("vaults")
    personal = root / "vault-personal"
    agents = root / "vault-agents"
    personal.mkdir()
    agents.mkdir()
    # Create required sub-directories so audit log path resolves
    (agents / "70_agents").mkdir(parents=True)

    # Patch environment before config is imported
    os.environ["OBSIDIAN_VAULT_ROOT"] = str(root)
    os.environ["OBSIDIAN_VAULT_PERSONAL"] = str(personal)
    os.environ["OBSIDIAN_VAULT_AGENTS"] = str(agents)
    os.environ["OBSIDIAN_AUDIT_LOG"] = str(agents / "70_agents" / "audit.log")

    # Reload config with patched env
    if "config" in sys.modules:
        import importlib
        import config as cfg_mod
        importlib.reload(cfg_mod)

    yield {"root": root, "personal": personal, "agents": agents}


# Import after env patch
import config as cfg  # noqa: E402
import server  # noqa: E402  (imports mcp and tool functions)

from server import (  # noqa: E402
    append_file,
    create_file,
    list_dir,
    read_file,
    search,
    write_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vp(rel: str) -> str:
    """Vault-personal relative path."""
    return f"vault-personal/{rel}"


def _va(rel: str) -> str:
    """Vault-agents relative path."""
    return f"vault-agents/{rel}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_and_read_file():
    result = await create_file(_vp("10_tasks/test-task.md"), "# Test Task\n", agent="pytest")
    assert result["action"] == "created"
    assert result["size_bytes"] > 0

    read = await read_file(_vp("10_tasks/test-task.md"), agent="pytest")
    assert "# Test Task" in read["content"]


@pytest.mark.asyncio
async def test_write_file_overwrites():
    path = _vp("40_knowledge/concept.md")
    await create_file(path, "original content\n", agent="pytest")
    await write_file(path, "replaced content\n", agent="pytest")
    read = await read_file(path, agent="pytest")
    assert read["content"] == "replaced content\n"


@pytest.mark.asyncio
async def test_append_file():
    path = _va("60_logs/events.md")
    await create_file(path, "# Events\n", agent="pytest")
    await append_file(path, "\n## 2026-01-01T00:00:00Z\nFirst event.\n", agent="pytest")
    read = await read_file(path, agent="pytest")
    assert "First event" in read["content"]


@pytest.mark.asyncio
async def test_create_file_fails_if_exists():
    path = _vp("50_ideas/idea.md")
    await create_file(path, "first\n", agent="pytest")
    with pytest.raises(FileExistsError):
        await create_file(path, "second\n", agent="pytest")


@pytest.mark.asyncio
async def test_list_dir():
    # Create a file so the dir has content
    await create_file(_vp("30_research/paper.md"), "# Paper\n", agent="pytest")
    result = await list_dir(_vp("30_research"), agent="pytest")
    names = [e["name"] for e in result["entries"]]
    assert "paper.md" in names


@pytest.mark.asyncio
async def test_search_finds_match():
    await create_file(_vp("40_knowledge/python.md"), "Python is a great language.\n", agent="pytest")
    result = await search("great language", vault="vault-personal", agent="pytest")
    assert result["total"] >= 1
    assert any("python.md" in m["path"] for m in result["matches"])


@pytest.mark.asyncio
async def test_sandbox_blocks_escape():
    with pytest.raises(ValueError, match="outside the allowed vault roots|could not be resolved"):
        await read_file("/etc/passwd", agent="pytest")


@pytest.mark.asyncio
async def test_sandbox_blocks_traversal():
    with pytest.raises(ValueError):
        await read_file("vault-personal/../../etc/passwd", agent="pytest")


@pytest.mark.asyncio
async def test_audit_log_written():
    audit_path = cfg.AUDIT_LOG_PATH
    before = audit_path.read_text() if audit_path.exists() else ""
    await read_file(_vp("10_tasks/test-task.md"), agent="audit-test")
    after = audit_path.read_text()
    assert "audit-test" in after
    assert len(after) > len(before)
