# Telegram Account Pool & Provisioning Engine (HPE)

This document covers the shared infrastructure, database state, and orchestrator architecture used to register accounts and harvest API keys across multiple AI platforms (e.g. FreeModel, Cursor, ChatGPT, Windsurf, Trae).

## Overview

The provisioning flow combines local resource pools (Telegram accounts managed via SSPanel, Proton Mail accounts, Mozilla Relay aliases, and Proxies) with an automated browser/API engine to register accounts and extract API keys.

The core execution engine is based on our fork of **any-auto-register**, located at [packages/any-auto-register](file:///Users/alex/Work/GitHub/ai-harness/packages/any-auto-register).

---

## 1. System Architecture (HPE)

The **Harness Provisioning Engine (HPE)** acts as the orchestrator. It receives high-level tasks (e.g. *"provision 3 accounts for Cursor"*) and coordinates resources and workers.

```text
  [ User / AI Agent (Hermes) / OmniRoute ]
                    │
                    ▼  (e.g. "provision_keys: freemodel, count: 2")
         ┌────────────────────────┐
         │    HPE Orchestrator    │
         └───────────┬────────────┘
                     │
    ┌────────────────┼────────────────┐
    ▼                ▼                ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│    Resource Pools    │  │  Execution Engine    │  │   Credential Vault   │
│                      │  │ (any-auto-register)  │  │                      │
│ - TG Pool (SSPanel)  │  │                      │  │ - SQLite Database    │
│ - Mail Pool (Proton) │  │ - platforms/         │  │ - Decrypted Storage  │
│ - Proxy Pool         │  │ - providers/mailbox  │  │ - Sync to OmniRoute  │
│ - Email Aliases      │  │ - providers/sms      │  │                      │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

### Shared Resource Pools
* **Telegram Pool:** Managed by SSPanel. Used to trigger bot `/start` commands.
* **Email Mailbox & Aliases:** Proton Mail (via web/IMAP reader) and Mozilla Relay (for generating disposable forwarders).
* **Proxies:** Applied to individual registration runs to prevent IP-based blacklisting.

---

## 2. Submodule Integration: any-auto-register

Our fork is integrated as a git submodule:
* **Upstream:** `https://github.com/lxf746/any-auto-register`
* **Our Fork:** `https://github.com/Alexcsharp17/any-auto-register`
* **Path:** `packages/any-auto-register`

To keep upstream merges clean, we structure our custom code within designated extension points:

### A. Platforms (`platforms/`)
Contains registration scripts for target AI services.
* **Path:** `packages/any-auto-register/platforms/`
* We add new platforms (e.g. `platforms/freemodel/`) by subclassing `BaseProvider` and implementing the site-specific Playwright/API actions.

### B. Custom Mailbox Providers (`providers/mailbox/`)
Handles retrieval of verification codes.
* **Path:** `packages/any-auto-register/providers/mailbox/`
* We implement our Proton Mail reader / Mozilla Relay automation here.

### C. Custom SMS/Telegram Providers (`providers/sms/`)
Binds verification flows to our SSPanel Telegram bot pool.
* **Path:** `packages/any-auto-register/providers/sms/`
* We map the verification requests to the SSPanel `bot-start` API.

---

## 3. Database Schema (State & History)

All registrations, actions, and recurring tasks (like daily `/checkin`) are tracked in SQLite.

* **Server Path:** `/var/lib/ai-harness/provider-bindings.sqlite`
* **Local Path:** `data/provider-bindings.sqlite`
* **Env Override:** `AI_HARNESS_BINDINGS_DB`

### Database Tables

```sql
-- 1. Accounts Pool Registry
CREATE TABLE IF NOT EXISTS telegram_accounts (
  telegram_id TEXT PRIMARY KEY,
  phone TEXT,
  status TEXT NOT NULL DEFAULT 'active', -- active, banned, warning
  last_used_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bot Bindings (1:1 and N:1 relations)
CREATE TABLE IF NOT EXISTS telegram_bot_bindings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id TEXT NOT NULL,
  provider TEXT NOT NULL,              -- freemodel, freeaisub, etc.
  bot_username TEXT NOT NULL,          -- @FreeModelDevBot, @freeaisub_bot
  binding_type TEXT NOT NULL,          -- provider-binding, referral-join
  status TEXT NOT NULL,                -- success, failed
  bound_account_ref TEXT,              -- email or provider account ID
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(telegram_id) REFERENCES telegram_accounts(telegram_id),
  UNIQUE(telegram_id, bot_username)
);

-- 3. Action History (Logs and Recurring Check-ins)
CREATE TABLE IF NOT EXISTS telegram_action_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id TEXT NOT NULL,
  bot_username TEXT NOT NULL,
  action_type TEXT NOT NULL,           -- checkin, start, send_message, click_button
  status TEXT NOT NULL,                -- success, failed, timeout
  payload TEXT,                        -- command text or bot response log
  executor TEXT NOT NULL,              -- cron-script, hermes-agent
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(telegram_id) REFERENCES telegram_accounts(telegram_id)
);
```

---

## 4. Runbooks & Helper Scripts

* **Database Migration & Registry Helper:** [provider-bindings](file:///Users/alex/Work/GitHub/ai-harness/scripts/provider-bindings) (wrapper for [provider_bindings.py](file:///Users/alex/Work/GitHub/ai-harness/scripts/provider_bindings.py))
* **FreeModel Binding Playbook:** [freemodel-account-binding.md](../playbooks/freemodel-account-binding.md)
* **Referral Bot Playbook:** [referral-bot-activation.md](../playbooks/referral-bot-activation.md)
* **Browser Service Setup:** [camofox-browser.md](camofox-browser.md)

