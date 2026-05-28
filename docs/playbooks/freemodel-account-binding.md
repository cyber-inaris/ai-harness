# FreeModel Account Binding Playbook

Playbook for creating new FreeModel accounts and binding them to owned Telegram
accounts via SSPanel.

Prerequisites:

```text
- Camofox Browser running on the host: curl http://127.0.0.1:9377/health
- /opt/ai-harness/secrets/sspanel.env populated
- /opt/ai-harness/secrets/proton-mail.env populated
- ./scripts/provider-bindings init has been run
```

Related docs:

```text
Browser automation: docs/operations/camofox-browser.md
TG pool & SSPanel:  docs/operations/telegram-account-pool.md
```

## Activation Type

```text
type: provider-binding
bot:  @FreeModelDevBot
link: https://t.me/FreeModelDevBot?start=<token>
1:1   one Telegram account per FreeModel API account
```

The start token is unique per FreeModel account and expires after the page is
closed. Expired tokens require a fresh browser flow.

## Step 1 — Build Exclude List

```bash
AI_HARNESS_BINDINGS_DB=/var/lib/ai-harness/provider-bindings.sqlite \
  ./scripts/provider-bindings exclude --provider freemodel
```

Save the JSON array. It becomes `excludeTelegramIds` in the SSPanel request.

## Step 2 — Browser Flow: Create / Login FreeModel Account

Use Camofox Browser to open FreeModel and complete email verification.

Known Mozilla Relay aliases for FreeModel registration:

```text
wgsr7b2t7@mozmail.com
l081p64su@mozmail.com
```

Full browser steps are in:

```text
docs/operations/camofox-browser.md → FreeModel Code Retrieval Flow
```

Summary:

```text
1. POST /tabs  userId=ai-harness  sessionKey=freemodel-<alias>
   url=https://freemodel.dev/dashboard/keys
2. Enter Relay alias in the email form.
3. Click "Send verification code".
4. Open Proton Web in a second tab (sessionKey=proton-mail).
5. Load credentials from /opt/ai-harness/secrets/proton-mail.env if needed.
6. Find email: sender=hello@freemodel.dev  subject="Your FreeModel code: ..."
7. Extract the 6-digit code.
8. Enter code in FreeModel tab.
9. Wait for "You're in. Redirecting to your dashboard…"
```

## Step 3 — Extract Telegram Start Link

On the FreeModel dashboard:

```text
1. Go to the Account verification section.
2. Click "Bind Telegram".
3. Copy the "Open in Telegram →" link.
```

Expected format:

```text
https://t.me/FreeModelDevBot?start=<token>
```

The page then shows "Waiting for Telegram…". Do not close the tab yet.

## Step 4 — Call SSPanel

```bash
source /opt/ai-harness/secrets/sspanel.env

EXCLUDE_IDS=$(
  AI_HARNESS_BINDINGS_DB=/var/lib/ai-harness/provider-bindings.sqlite \
    ./scripts/provider-bindings exclude --provider freemodel
)

curl -s -X POST "${SSPANEL_BASE_URL}/api/v2/telegram/bot-start/test" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SSPANEL_ADMIN_TOKEN}" \
  --data "{
    \"botLink\": \"https://t.me/FreeModelDevBot?start=<token>\",
    \"limit\": 1,
    \"excludeTelegramIds\": ${EXCLUDE_IDS},
    \"messages\": [],
    \"botResponseWaitMs\": 3000,
    \"dryRun\": false
  }" | tee /tmp/sspanel-response-freemodel-$(date +%s).json
```

If `SSPANEL_ADMIN_TOKEN` is not set and only email+password are in the env file:

```bash
SSPANEL_ADMIN_TOKEN=$(
  curl -s -X POST "${SSPANEL_BASE_URL}/api/v2/auth/login" \
    -H "Content-Type: application/json" \
    --data "{\"email\":\"${SSPANEL_ADMIN_EMAIL}\",\"password\":\"${SSPANEL_ADMIN_PASSWORD}\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])"
)
```

## Step 5 — Record Result

```bash
./scripts/provider-bindings record \
  --provider freemodel \
  --provider-account-ref "<relay alias, e.g. wgsr7b2t7@mozmail.com>" \
  --start-link "https://t.me/FreeModelDevBot?start=<token>" \
  --executor hermes-server \
  --ss-panel-response-json-file /tmp/sspanel-response-freemodel-<timestamp>.json
```

## Step 6 — Handle Outcomes

| botResponseText / status | Action |
|---|---|
| `Account bound successfully` or `botResponseStatus=success` | ✅ Done. Record is `success`. |
| `This binding link has expired` | Return to Step 3, click "Bind Telegram" again for a fresh token. |
| `already bound to a different account` | Record is `failed`. Run Step 1 again (updated exclude), retry SSPanel with same link and a new TG account. |
| `sendDirectMessage returned false` | Record is `send_failed`. Retry SSPanel — SSPanel will pick a different TG account. |
| No `botResponseText` / timeout | Record as `unknown`. Investigate SSPanel logs. |

## Step 7 — Verify and Report

After 2 successful bindings, run:

```bash
AI_HARNESS_BINDINGS_DB=/var/lib/ai-harness/provider-bindings.sqlite \
  ./scripts/provider-bindings list --provider freemodel --limit 10
```

Expected summary output per bound account:

```text
provider_account_ref: <relay alias>
telegram_id:         <TG account id>
start_code:          <token>
status:              success
db:                  /var/lib/ai-harness/provider-bindings.sqlite
```

## Notes

- Do not commit cookies, screenshots, email codes, or raw tokens to git.
- Store Camofox session data under `/var/lib/ai-harness/browser`.
- Store secrets under `/opt/ai-harness/secrets` with mode `600`.
- Keep the FreeModel dashboard tab open until SSPanel confirms binding.
- Each Mozilla Relay alias can register exactly one FreeModel account.
