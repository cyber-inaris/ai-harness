# Router Targets And OmniRoute Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OmniRoute as the first supported router target while keeping `ai-harness` neutral enough to add Cockpit later.

**Architecture:** `ai-harness` owns deployment, nginx routing, docs, health checks, and secrets layout. OmniRoute runs as a Docker Compose service bound to localhost, and nginx exposes it through the existing Cloudflare web gateway.

**Tech Stack:** Docker Compose, nginx, Bash scripts, Markdown runbooks, Cloudflare Tunnel web ingress.

---

### Task 1: Router Target Documentation

**Files:**
- Create: `docs/routers/router-targets.md`
- Create: `docs/routers/omniroute.md`
- Modify: `docs/routers/README.md`

- [x] Add a router target overview that defines OmniRoute as the first supported target and Cockpit as a future target.
- [x] Add an OmniRoute runbook with ports, filesystem layout, install/update commands, and verification commands.
- [x] Link the new docs from `docs/routers/README.md`.

### Task 2: OmniRoute Runtime Files

**Files:**
- Create: `docker/omniroute.compose.yml`
- Create: `configs/examples/omniroute.env.example`
- Create: `scripts/install-omniroute.sh`

- [x] Add a Compose service using `diegosouzapw/omniroute:latest`.
- [x] Bind the router to `127.0.0.1:20128`.
- [x] Persist router data under `/var/lib/ai-harness/router/omniroute`.
- [x] Add an idempotent install script that copies compose/env files to `/opt/ai-harness/docker`, starts the service, and verifies local HTTP.

### Task 3: nginx Gateway Integration

**Files:**
- Modify: `ops/nginx/ai-harness.conf`
- Modify: `ops/nginx/README.md`
- Modify: `docs/operations/current-host-status.md`

- [x] Add `/omniroute/` and `/router/` proxy routes to `127.0.0.1:20128`.
- [x] Preserve `/hermes/` routing and existing Hermes root asset/API compatibility routes.
- [x] Document the chosen route and the future Cockpit slot.

### Task 4: Server Deployment And Verification

**Commands:**

```bash
rsync -az --delete --exclude '.git/' --exclude '.superpowers/' --exclude 'benchmarks/results/*' --exclude 'secrets/*' ./ ai-harness-ts:/opt/ai-harness/repo/
ssh ai-harness-ts 'sudo /opt/ai-harness/repo/scripts/install-omniroute.sh'
curl -sS https://apps.ss-promotion.com/omniroute/ | head
```

- [x] Sync the repo to `/opt/ai-harness/repo`.
- [x] Run the installer on the host.
- [x] Verify the container is running.
- [x] Verify nginx config.
- [ ] Verify the public Cloudflare route returns OmniRoute content. Blocked because the host went offline after install: Tailscale reports `dima-a35s` offline and Cloudflare returns `530 The origin has been unregistered from Argo Tunnel`.

### Task 5: Commit

**Commands:**

```bash
git diff --check
git status --short
git add docs/routers docker configs/examples scripts ops/nginx docs/operations docs/superpowers/plans
git commit -m "Add OmniRoute router target"
```

- [x] Commit all repo changes after successful local/server install verification, with public Cloudflare verification pending host connectivity.
