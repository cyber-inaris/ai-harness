# AI Harness — Map of Content

> Master index of all knowledge in this vault. Start here.

---

## 🏗️ System Architecture

- [[AI Harness]] — what the system is
- [[AI Harness Overview]] — high-level overview
- [[AI Harness Architecture]] — technical architecture
- [[AI Harness Design]] — ops-first design decisions

---

## 🤖 Agents

### Hermes (Primary Agent)
- [[Hermes]] — entity note
- [[Hermes Agent]] — full agent spec
- [[Hermes Runtime Setup]] — current runtime config
- [[Hermes Current Setup]] — live state
- [[Hermes Modes and Skills]] — capabilities

### Other Agent Runtimes
- [[LangGraph]] — entity note
- [[LangGraph Runtime]] — setup guide
- [[CrewAI MVP Setup]] — CrewAI install
- [[CrewAI Orchestration]] — multi-agent patterns

### Agent Infrastructure
- [[Telegram Command Router]] — Hermes Telegram interface
- [[Artifacts and Task Pages]] — task output patterns
- [[Notion Task Board]] — task tracking integration
- [[Agent VPS Setup]] — VPS-level agent config

---

## 🔀 Routers

- [[OmniRoute]] — entity note
- [[OmniRoute]] — full router config
- [[Router Targets]] — model/provider targets

---

## 📊 Benchmarks & Scoring

- [[Reseller Benchmark Notes]] — raw benchmark data (research)
- [[Reseller Scoring System]] — scoring methodology

---

## 🌐 Infrastructure

### Networking
- [[Tailscale]] — entity note
- [[Tailscale Cloudflare Access]] — access setup
- [[Ngrok Nginx Auth]] — public ingress config

### Server Operations
- [[Ubuntu Host Setup]] — server setup runbook
- [[Server Monitoring]] — monitoring setup
- [[Bitwarden MCP]] — secrets via MCP
- [[Camofox Browser]] — browser automation
- [[Agent VPS Setup]] — agent VPS config

---

## 🧠 Obsidian Knowledge OS

- [[Obsidian Knowledge OS]] — system overview
- [[Vault Structure]] — folder layout + YAML schema
- [[Agent Definitions]] — 5 agents reference
- [[Dataview Dashboards]] — query examples
- [[Git Sync Setup]] — Mac ↔ Server sync
- [[Logging Strategy]] — event sourcing
- [[Workflows]] — end-to-end workflows

---

## 📋 Playbooks

- [[Multi-Perspective Review]] — review process

---

## 📁 Projects

```dataview
TABLE status, priority, owner, file.mtime AS "Updated"
FROM "20_projects"
WHERE type = "project"
SORT file.mtime DESC
```

---

## 📝 Recent Knowledge

```dataview
LIST
FROM "40_knowledge"
WHERE type = "knowledge"
SORT file.mtime DESC
LIMIT 15
```
