# Camofox Browser Automation

Camofox Browser is the preferred browser path for account-registration flows
that need to interact with provider dashboards or Proton Web Mail when IMAP is
not available.

Source:

```text
https://github.com/jo-inc/camofox-browser
```

The project wraps Camoufox, a Firefox fork with fingerprint spoofing implemented
below the JavaScript layer. The server exposes an agent-oriented browser API with
compact accessibility snapshots, stable element refs, cookies, proxy support,
screenshots, OpenAPI docs, and Docker deployment.

## Target Use Cases

- Read Proton verification emails through Proton Web for free Proton accounts.
- Register owned accounts on provider dashboards.
- Preserve authenticated sessions with cookies/session storage.
- Run browser flows behind proxy profiles when a provider is sensitive to
  ordinary headless Playwright/Chromium.

## Local Service Shape

Default upstream start command:

```bash
npx @askjo/camofox-browser
```

Default local port:

```text
127.0.0.1:9377
```

API docs:

```text
http://127.0.0.1:9377/docs
http://127.0.0.1:9377/openapi.json
```

Keep the service bound to localhost. Do not expose it through nginx,
Cloudflare Tunnel, or public Docker ports unless access control is explicitly
designed first.

## Proton Web Verification Flow

Use this instead of Proton Bridge when the Proton account is on a free plan.

```text
1. Start Camofox Browser on the host.
2. Create or reuse a dedicated browser session for the Proton mailbox.
3. Navigate to https://mail.proton.me/u/0/inbox.
4. Complete the first login interactively through the browser/VNC path.
5. Persist cookies/session storage for reuse.
6. Trigger a verification email to the relay address.
7. Search Proton Web for a stable provider subject hint.
8. Open the newest matching email.
9. Extract the code from the rendered message text.
```

Expected verification result:

```text
source: proton-web
found: true
code: <verification code>
subject: <provider email subject>
```

## FreeModel Code Retrieval Flow

Use this exact flow for FreeModel owned-account registration when verification
emails are delivered through Mozilla Relay aliases into Proton Mail.

Known test aliases:

```text
wgsr7b2t7@mozmail.com
l081p64su@mozmail.com
```

Observed working result:

```text
alias: wgsr7b2t7@mozmail.com
sender: hello@freemodel.dev [via Relay]
subject: Your FreeModel code: 908056
code: 908056
```

Steps:

```text
1. Confirm Camofox Browser is running:
   curl http://127.0.0.1:9377/health

2. Open FreeModel:
   POST /tabs
   userId=ai-harness
   sessionKey=freemodel-test
   url=https://freemodel.dev/dashboard/keys

3. In the FreeModel email form, enter the Relay alias.

4. Click "Send verification code".

5. Confirm the FreeModel page says:
   We sent a 6-digit code to <alias>

6. Open Proton Web in a separate Camofox tab:
   userId=ai-harness
   sessionKey=proton-mail
   url=https://mail.proton.me/u/0/inbox

7. If Proton is logged out, load credentials from:
   /opt/ai-harness/secrets/proton-mail.env

8. In Proton inbox, look for:
   sender: hello@freemodel.dev [via Relay]
   subject prefix: Your FreeModel code:

9. Extract the 6-digit code from the subject or rendered message.

10. Return to the FreeModel tab and enter the code into the six code inputs.
```

Do not use Proton Bridge for this mailbox unless the Proton account is upgraded
to a paid plan.

## FreeModel Telegram Verification Flow

After the email code is accepted, FreeModel redirects to the dashboard.

Observed successful login:

```text
alias: wgsr7b2t7@mozmail.com
latest email code used: 224119
dashboard URL: https://freemodel.dev/dashboard
```

Steps:

```text
1. Wait until the FreeModel page shows:
   You're in. Redirecting to your dashboard…

2. Wait for:
   https://freemodel.dev/dashboard

3. In the Account verification section, click:
   Bind Telegram

4. Extract the "Open in Telegram →" link.

5. Send that link to ss-panel or the Telegram-account automation service.
```

Observed Telegram verification link format:

```text
https://t.me/FreeModelDevBot?start=<token>
```

Observed current link:

```text
https://t.me/FreeModelDevBot?start=iBHwRVAyZV3K
```

The page then shows:

```text
Waiting for Telegram…
```

At that point, the remaining action is external to the browser session: open the
link from an owned Telegram account and tap/start the bot.

## FreeModel Telegram Binding State

`ai-harness` is the source of truth for FreeModel Telegram binding history. The
browser flow creates the FreeModel account and extracts the Telegram start link;
the Telegram executor only sends `/start <token>` from an owned Telegram account.

Current executor:

```text
codex-mac -> local SSPanel API
```

Future executor:

```text
hermes-server -> SSPanel API or a dedicated Telegram executor service
```

Both executors must use the same state database:

```text
local default: data/provider-bindings.sqlite
server path:   /var/lib/ai-harness/provider-bindings.sqlite
env override:  AI_HARNESS_BINDINGS_DB
```

Schema managed by `./scripts/provider-bindings init`:

```sql
create table if not exists provider_telegram_bindings (
  id integer primary key autoincrement,
  provider text not null,
  provider_account_ref text,
  telegram_id text not null,
  start_code text not null,
  start_link text not null,
  status text not null,
  bot_response_status text,
  bot_response_text text,
  ss_panel_response_json text,
  error text,
  executor text,
  run_id text,
  created_at text not null default current_timestamp,
  updated_at text not null default current_timestamp,
  activated_at text
);
```

The DB also has a partial unique index that allows only one `success` row per
`provider + telegram_id`, so a consumed Telegram account cannot silently become
available again for the same provider.

Initialize or inspect the database:

```bash
./scripts/provider-bindings init
./scripts/provider-bindings list --provider freemodel
```

Before sending a new FreeModel Telegram link, build the SSPanel
`excludeTelegramIds` list from prior attempts:

```bash
./scripts/provider-bindings exclude --provider freemodel
```

The default exclude policy returns Telegram ids with these statuses:

```text
success, pending, failed, send_failed
```

This prevents reuse of already-bound accounts, in-progress accounts, accounts
FreeModel rejected as already bound elsewhere, and technically bad sessions.
`expired` and `unknown` are not excluded by default because they may reflect a
bad start link or unclear provider response rather than a consumed Telegram
account.

SSPanel request shape:

```bash
curl -X POST "${SSPANEL_BASE_URL:-http://localhost:3000}/api/v2/telegram/bot-start/test" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SSPANEL_ADMIN_TOKEN}" \
  --data '{
    "botLink": "https://t.me/FreeModelDevBot?start=<token>",
    "limit": 1,
    "excludeTelegramIds": ["<ids from provider-bindings exclude>"],
    "messages": [],
    "botResponseWaitMs": 3000,
    "dryRun": false
  }'
```

For local Codex/Mac execution, `SSPANEL_ADMIN_TOKEN` can be obtained from:

```bash
curl -X POST "${SSPANEL_BASE_URL:-http://localhost:3000}/api/v2/auth/login" \
  -H "Content-Type: application/json" \
  --data '{"email":"admin@sspanel.com","password":"admin123"}'
```

Do not hard-code these credentials in repo files. Hermes/server runs should use
`/opt/ai-harness/secrets/*` or another private env file.

After SSPanel responds, record the first result:

```bash
./scripts/provider-bindings record \
  --provider freemodel \
  --provider-account-ref "<relay alias or provider account id>" \
  --start-link "https://t.me/FreeModelDevBot?start=<token>" \
  --executor codex-mac \
  --ss-panel-response-json-file /path/to/sspanel-response.json
```

The recorder classifies common SSPanel/bot outcomes:

```text
Account bound successfully                       -> success
This binding link has expired                    -> expired
already bound to a different account             -> failed
sendDirectMessage returned false                 -> send_failed
anything else                                    -> unknown
```

When status is `expired`, return to the browser flow and request a fresh
FreeModel Telegram link. When status is `success`, the FreeModel account's
Telegram binding is complete.

## Runtime Notes

- Store browser cookies/session data under `/var/lib/ai-harness/browser` or a
  similarly private runtime directory.
- Store Camofox API keys and proxy credentials under `/opt/ai-harness/secrets`.
- Keep screenshots and traces out of git because rendered mail can contain
  credentials, links, and one-time codes.
- Prefer one browser session per owned mailbox or provider identity.
- Standard Playwright remains useful for local UI tests; use Camofox for
  production-like account-registration browsing.

## Current Decision

Proton Bridge is not the default path for `ss.magic.admin@proton.me` because the
server-side Bridge login returned:

```text
Please upgrade to a paid plan to use this client
```

Until that account is upgraded, use Proton Web through browser automation.
