#!/usr/bin/env python3
"""
migrate_docs.py — Migrate ai-harness repo docs into vault-personal Obsidian vault.

Reads source docs from /opt/ai-harness/repo/docs/,
adds YAML frontmatter, converts relative links to [[wiki links]],
and writes to /opt/vaults/vault-personal/.

Usage:
    python3 migrate_docs.py              # full migration
    python3 migrate_docs.py --dry-run    # print plan, no writes
    python3 migrate_docs.py --list       # list source→dest mapping
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_DOCS = Path("/opt/ai-harness/repo/docs")
VAULT = Path("/opt/vaults/vault-personal")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ---------------------------------------------------------------------------
# Source → destination mapping
# Each entry: (source_relative, dest_relative, type, tags, extra_frontmatter)
# ---------------------------------------------------------------------------

MIGRATION_MAP: list[tuple[str, str, str, list[str], dict]] = [
    # Overview / Architecture
    ("overview.md",
     "40_knowledge/AI Harness Overview.md",
     "knowledge", ["ai-harness", "overview"],
     {"status": "active"}),

    ("architecture.md",
     "40_knowledge/AI Harness Architecture.md",
     "knowledge", ["ai-harness", "architecture"],
     {"status": "active"}),

    ("design/2026-05-26-ai-harness-ops-first-design.md",
     "40_knowledge/AI Harness Design.md",
     "knowledge", ["ai-harness", "design"],
     {"status": "active"}),

    # Agents
    ("agents/hermes-agent.md",
     "40_knowledge/agents/Hermes Agent.md",
     "knowledge", ["agent", "hermes"],
     {"status": "active", "entity": "[[Hermes]]"}),

    ("agents/hermes-current-setup.md",
     "40_knowledge/agents/Hermes Current Setup.md",
     "knowledge", ["agent", "hermes", "setup"],
     {"status": "active"}),

    ("agents/hermes-modes-and-skills.md",
     "40_knowledge/agents/Hermes Modes and Skills.md",
     "knowledge", ["agent", "hermes", "skills"],
     {"status": "active"}),

    ("agents/hermes-runtime-setup.md",
     "40_knowledge/agents/Hermes Runtime Setup.md",
     "knowledge", ["agent", "hermes", "runtime"],
     {"status": "active"}),

    ("agents/langgraph-runtime.md",
     "40_knowledge/agents/LangGraph Runtime.md",
     "knowledge", ["agent", "langgraph", "runtime"],
     {"status": "active", "entity": "[[LangGraph]]"}),

    ("agents/crewai-mvp-setup.md",
     "40_knowledge/agents/CrewAI MVP Setup.md",
     "knowledge", ["agent", "crewai", "setup"],
     {"status": "active"}),

    ("agents/crewai-orchestration.md",
     "40_knowledge/agents/CrewAI Orchestration.md",
     "knowledge", ["agent", "crewai", "orchestration"],
     {"status": "active"}),

    ("agents/agent-vps-setup.md",
     "40_knowledge/infra/Agent VPS Setup.md",
     "knowledge", ["infra", "vps", "agent"],
     {"status": "active"}),

    ("agents/artifacts-and-task-pages.md",
     "40_knowledge/agents/Artifacts and Task Pages.md",
     "knowledge", ["agent", "artifacts"],
     {"status": "active"}),

    ("agents/notion-task-board.md",
     "40_knowledge/agents/Notion Task Board.md",
     "knowledge", ["agent", "notion", "tasks"],
     {"status": "active"}),

    ("agents/telegram-command-router.md",
     "40_knowledge/agents/Telegram Command Router.md",
     "knowledge", ["agent", "telegram", "routing"],
     {"status": "active", "entity": "[[Telegram Command Router]]"}),

    # Routers
    ("routers/omniroute.md",
     "40_knowledge/routers/OmniRoute.md",
     "knowledge", ["router", "omniroute"],
     {"status": "active", "entity": "[[OmniRoute]]"}),

    ("routers/router-targets.md",
     "40_knowledge/routers/Router Targets.md",
     "knowledge", ["router", "targets"],
     {"status": "active"}),

    # Benchmarks
    ("benchmarks/reseller-benchmark-notes.md",
     "30_research/Reseller Benchmark Notes.md",
     "research", ["benchmarks", "resellers", "research"],
     {"status": "active"}),

    ("benchmarks/reseller-scoring-system.md",
     "40_knowledge/Reseller Scoring System.md",
     "knowledge", ["benchmarks", "scoring", "resellers"],
     {"status": "active"}),

    # Networking
    ("networking/tailscale-cloudflare-access.md",
     "40_knowledge/infra/Tailscale Cloudflare Access.md",
     "knowledge", ["infra", "networking", "tailscale", "cloudflare"],
     {"status": "active", "entity": "[[Tailscale]]"}),

    ("networking/ngrok-nginx-auth.md",
     "40_knowledge/infra/Ngrok Nginx Auth.md",
     "knowledge", ["infra", "networking", "ngrok", "nginx"],
     {"status": "active"}),

    # VPS / Operations
    ("vps/ubuntu-setup.md",
     "40_knowledge/infra/Ubuntu Host Setup.md",
     "knowledge", ["infra", "vps", "ubuntu", "setup"],
     {"status": "active", "subtype": "runbook"}),

    ("operations/current-host-status.md",
     "60_logs/host-status.md",
     "knowledge", ["infra", "status", "log"],
     {"status": "active"}),

    ("operations/server-monitoring.md/server-monitoring.md",
     "40_knowledge/infra/Server Monitoring.md",
     "knowledge", ["infra", "monitoring"],
     {"status": "active"}),

    ("operations/bitwarden-mcp.md",
     "40_knowledge/infra/Bitwarden MCP.md",
     "knowledge", ["infra", "bitwarden", "mcp"],
     {"status": "active"}),

    ("operations/camofox-browser.md",
     "40_knowledge/infra/Camofox Browser.md",
     "knowledge", ["infra", "browser", "automation"],
     {"status": "active", "entity": "[[Camofox]]"}),

    # Playbooks
    ("playbooks/multi-perspective-review.md",
     "40_knowledge/playbooks/Multi-Perspective Review.md",
     "knowledge", ["playbook", "review", "process"],
     {"status": "active"}),

    # Projects / Plans
    ("superpowers/plans/2026-05-26-router-targets-omniroute.md",
     "20_projects/Router Targets OmniRoute.md",
     "project", ["project", "router", "omniroute"],
     {"status": "active", "owner": "human"}),

    # Obsidian OS self-docs
    ("obsidian-knowledge-os/README.md",
     "40_knowledge/obsidian-os/Obsidian Knowledge OS.md",
     "knowledge", ["obsidian-os", "system"],
     {"status": "active"}),

    ("obsidian-knowledge-os/agent-definitions.md",
     "40_knowledge/obsidian-os/Agent Definitions.md",
     "knowledge", ["obsidian-os", "agents"],
     {"status": "active"}),

    ("obsidian-knowledge-os/dataview-dashboards.md",
     "40_knowledge/obsidian-os/Dataview Dashboards.md",
     "knowledge", ["obsidian-os", "dataview"],
     {"status": "active"}),

    ("obsidian-knowledge-os/git-sync-setup.md",
     "40_knowledge/obsidian-os/Git Sync Setup.md",
     "knowledge", ["obsidian-os", "git", "sync"],
     {"status": "active"}),

    ("obsidian-knowledge-os/logging-strategy.md",
     "40_knowledge/obsidian-os/Logging Strategy.md",
     "knowledge", ["obsidian-os", "logging"],
     {"status": "active"}),

    ("obsidian-knowledge-os/vault-structure.md",
     "40_knowledge/obsidian-os/Vault Structure.md",
     "knowledge", ["obsidian-os", "structure"],
     {"status": "active"}),

    ("obsidian-knowledge-os/workflows.md",
     "40_knowledge/obsidian-os/Workflows.md",
     "knowledge", ["obsidian-os", "workflows"],
     {"status": "active"}),
]

# ---------------------------------------------------------------------------
# Entity notes — created fresh (not migrated from a single source)
# ---------------------------------------------------------------------------

ENTITY_NOTES: list[tuple[str, str]] = [
    ("40_knowledge/Hermes.md", """---
type: knowledge
status: active
created: {date}
tags: [entity, agent, hermes]
---

# Hermes

Hermes is the primary AI agent in the [[AI Harness]] stack.
It is Telegram-facing and serves as the human-operator interface for server management.

## Key Facts
- Runtime: host-level (not Docker)
- Interface: [[Telegram Command Router]]
- Model: via [[OmniRoute]] (`free-mod/gpt-5.5`)
- Config: `/home/ai/.hermes/config.yaml`
- Services: `hermes-dashboard.service`, `hermes-gateway.service`

## Related Notes
- [[Hermes Agent]]
- [[Hermes Runtime Setup]]
- [[Hermes Modes and Skills]]
- [[Hermes Current Setup]]
- [[Telegram Command Router]]
"""),

    ("40_knowledge/OmniRoute.md", """---
type: knowledge
status: active
created: {date}
tags: [entity, router, omniroute]
---

# OmniRoute

OmniRoute is an OpenAI-compatible AI router used as the model serving layer.

## Key Facts
- Endpoint: `http://127.0.0.1:20128/v1`
- Compatible with OpenAI SDK
- Serves multiple models under unified API

## Related Notes
- [[OmniRoute]] (config)
- [[Router Targets]]
- [[Reseller Scoring System]]
"""),

    ("40_knowledge/Tailscale.md", """---
type: knowledge
status: active
created: {date}
tags: [entity, infra, networking, tailscale]
---

# Tailscale

Tailscale is the private VPN used for secure admin access to the server.

## Key Facts
- Server Tailscale IP: `100.105.206.54`
- SSH alias: `ai-harness-ts`
- Used for: SSH access, RDP/XFCE access
- NOT used for: public web traffic (that goes via Cloudflare Tunnel)

## Access Pattern
```
Mac → Tailscale → ai@100.105.206.54
```

## Related Notes
- [[Tailscale Cloudflare Access]]
- [[Ubuntu Host Setup]]
"""),

    ("40_knowledge/LangGraph.md", """---
type: knowledge
status: active
created: {date}
tags: [entity, agent, langgraph]
---

# LangGraph

LangGraph is the agent orchestration framework used for multi-step task automation.

## Key Facts
- Virtualenv: `/opt/ai-harness/venvs/langgraph-runtime`
- State stored in SQLite

## Related Notes
- [[LangGraph Runtime]]
- [[CrewAI MVP Setup]]
- [[CrewAI Orchestration]]
"""),

    ("40_knowledge/AI Harness.md", """---
type: knowledge
status: active
created: {date}
tags: [entity, ai-harness, system]
---

# AI Harness

AI Harness is the ops-first repository for setting up, running, and testing AI agents,
routers, reseller accounts, and benchmark workflows on a Linux server.

## System Components
- [[Hermes]] — primary AI agent (Telegram-facing)
- [[OmniRoute]] — AI router / model serving
- [[LangGraph]] — agent orchestration runtime
- [[Tailscale]] — secure admin network
- [[Obsidian Knowledge OS]] — knowledge + memory layer

## Repo
- GitHub: `cyber-inaris/ai-harness`
- Server path: `/opt/ai-harness/repo`

## Related Notes
- [[AI Harness Overview]]
- [[AI Harness Architecture]]
- [[AI Harness Design]]
"""),
]

# ---------------------------------------------------------------------------
# Link conversion table: filename → entity name (for wiki link conversion)
# ---------------------------------------------------------------------------

LINK_MAP: dict[str, str] = {
    "hermes-agent.md": "Hermes Agent",
    "hermes-current-setup.md": "Hermes Current Setup",
    "hermes-modes-and-skills.md": "Hermes Modes and Skills",
    "hermes-runtime-setup.md": "Hermes Runtime Setup",
    "langgraph-runtime.md": "LangGraph Runtime",
    "crewai-mvp-setup.md": "CrewAI MVP Setup",
    "crewai-orchestration.md": "CrewAI Orchestration",
    "agent-vps-setup.md": "Agent VPS Setup",
    "artifacts-and-task-pages.md": "Artifacts and Task Pages",
    "notion-task-board.md": "Notion Task Board",
    "telegram-command-router.md": "Telegram Command Router",
    "omniroute.md": "OmniRoute",
    "router-targets.md": "Router Targets",
    "reseller-benchmark-notes.md": "Reseller Benchmark Notes",
    "reseller-scoring-system.md": "Reseller Scoring System",
    "tailscale-cloudflare-access.md": "Tailscale Cloudflare Access",
    "ngrok-nginx-auth.md": "Ngrok Nginx Auth",
    "ubuntu-setup.md": "Ubuntu Host Setup",
    "current-host-status.md": "host-status",
    "server-monitoring.md": "Server Monitoring",
    "bitwarden-mcp.md": "Bitwarden MCP",
    "camofox-browser.md": "Camofox Browser",
    "multi-perspective-review.md": "Multi-Perspective Review",
    "overview.md": "AI Harness Overview",
    "architecture.md": "AI Harness Architecture",
}

# ---------------------------------------------------------------------------
# Transformation helpers
# ---------------------------------------------------------------------------


def build_frontmatter(
    note_type: str,
    tags: list[str],
    source: str,
    extra: dict,
) -> str:
    lines = ["---"]
    lines.append(f"type: {note_type}")
    for k, v in extra.items():
        lines.append(f"{k}: {v}")
    lines.append(f"created: {NOW}")
    lines.append(f"source: repo/docs/{source}")
    tags_str = "[" + ", ".join(tags) + "]"
    lines.append(f"tags: {tags_str}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def convert_links(content: str) -> str:
    """Convert markdown relative links to Obsidian [[wiki links]] where known."""

    def replace_link(m: re.Match) -> str:
        text = m.group(1)
        href = m.group(2)
        # Extract filename from path
        filename = Path(href).name
        # Remove fragment
        filename = filename.split("#")[0]
        if filename in LINK_MAP:
            entity = LINK_MAP[filename]
            if text == entity or text.lower() == entity.lower():
                return f"[[{entity}]]"
            return f"[[{entity}|{text}]]"
        return m.group(0)  # Leave unchanged if not in map

    # Convert [text](relative-path.md) style links
    content = re.sub(r"\[([^\]]+)\]\(([^)]+\.md[^)]*)\)", replace_link, content)
    return content


def strip_existing_frontmatter(content: str) -> str:
    """Remove existing YAML frontmatter if present."""
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            return content[end + 5:].lstrip("\n")
    return content


def transform_doc(
    source_path: Path,
    note_type: str,
    tags: list[str],
    extra: dict,
) -> str:
    """Read source, strip old frontmatter, add new frontmatter, convert links."""
    raw = source_path.read_text(encoding="utf-8")
    body = strip_existing_frontmatter(raw)
    frontmatter = build_frontmatter(note_type, tags, source_path.relative_to(REPO_DOCS).as_posix(), extra)
    body = convert_links(body)
    return frontmatter + body


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        print(f"{'SOURCE':<55} {'DEST'}")
        print("-" * 100)
        for src, dst, *_ in MIGRATION_MAP:
            print(f"{src:<55} {dst}")
        print(f"\nTotal: {len(MIGRATION_MAP)} docs + {len(ENTITY_NOTES)} entity notes")
        return

    errors: list[str] = []
    written: list[str] = []
    skipped: list[str] = []

    # --- Migrate docs ---
    for src_rel, dst_rel, note_type, tags, extra in MIGRATION_MAP:
        src_path = REPO_DOCS / src_rel
        dst_path = VAULT / dst_rel

        if not src_path.exists():
            print(f"  [SKIP] Source not found: {src_rel}")
            skipped.append(src_rel)
            continue

        try:
            content = transform_doc(src_path, note_type, tags, extra)
        except Exception as e:
            print(f"  [ERR]  Transform failed for {src_rel}: {e}")
            errors.append(src_rel)
            continue

        if args.dry_run:
            print(f"  [DRY]  {src_rel} → {dst_rel}")
            continue

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.write_text(content, encoding="utf-8")
        print(f"  [OK]   {src_rel} → {dst_rel}")
        written.append(dst_rel)

    # --- Create entity notes ---
    for dst_rel, content_template in ENTITY_NOTES:
        dst_path = VAULT / dst_rel
        content = content_template.format(date=NOW)

        if dst_path.exists():
            print(f"  [SKIP] Entity note already exists: {dst_rel}")
            skipped.append(dst_rel)
            continue

        if args.dry_run:
            print(f"  [DRY]  Entity note → {dst_rel}")
            continue

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.write_text(content, encoding="utf-8")
        print(f"  [OK]   Entity note → {dst_rel}")
        written.append(dst_rel)

    if args.dry_run:
        print(f"\n[DRY RUN] Would write {len(MIGRATION_MAP)} docs + {len(ENTITY_NOTES)} entity notes")
        return

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"Migration complete:")
    print(f"  Written : {len(written)}")
    print(f"  Skipped : {len(skipped)}")
    print(f"  Errors  : {len(errors)}")
    if errors:
        print(f"  Error files: {errors}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
