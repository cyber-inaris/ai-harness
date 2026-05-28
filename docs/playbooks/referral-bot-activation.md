# Referral Bot Activation Playbook

Generic playbook for registering owned Telegram accounts under a referral or
reward bot campaign. Applies to any bot that follows the pattern:

```text
/start <referral_code>  →  bot confirms registration  →  account counted as referral
```

Known bots using this pattern:

| Provider key | Bot username | Campaign code source |
|---|---|---|
| `freeaisub` | `@freeaisub_bot` | `My Link` button in the bot |

Related doc:

```text
TG pool & SSPanel: docs/operations/telegram-account-pool.md
```

## Activation Type

```text
type: referral-join
link: https://t.me/<BotUsername>?start=<referral_code>
N:1   many Telegram accounts → one campaign referral code
```

The referral code is fixed and belongs to the campaign owner's account. It does
not expire between runs. All TG accounts join under the same code.

## How to Get the Referral Link

For `@freeaisub_bot`:

```text
1. Open @freeaisub_bot.
2. Send the "🔗 My Link" button.
3. The bot replies with: https://t.me/freeaisub_bot?start=<code>
4. That code is stable; reuse it for all subsequent registrations.
```

Example observed link:

```text
https://t.me/freeaisub_bot?start=e2f59b99d1
```

## Step 1 — Build Exclude List

Even for referral bots, track which TG accounts have already been used to avoid
sending duplicate joins:

```bash
AI_HARNESS_BINDINGS_DB=/var/lib/ai-harness/provider-bindings.sqlite \
  ./scripts/provider-bindings exclude --provider freeaisub
```

## Step 2 — Call SSPanel

```bash
source /opt/ai-harness/secrets/sspanel.env

EXCLUDE_IDS=$(
  AI_HARNESS_BINDINGS_DB=/var/lib/ai-harness/provider-bindings.sqlite \
    ./scripts/provider-bindings exclude --provider freeaisub
)

REFERRAL_LINK="https://t.me/freeaisub_bot?start=e2f59b99d1"
BATCH_SIZE=5   # how many TG accounts to register in this run

curl -s -X POST "${SSPANEL_BASE_URL}/api/v2/telegram/bot-start/test" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SSPANEL_ADMIN_TOKEN}" \
  --data "{
    \"botLink\": \"${REFERRAL_LINK}\",
    \"limit\": ${BATCH_SIZE},
    \"excludeTelegramIds\": ${EXCLUDE_IDS},
    \"messages\": [],
    \"botResponseWaitMs\": 3000,
    \"dryRun\": false
  }" | tee /tmp/sspanel-response-freeaisub-$(date +%s).json
```

Adjust `limit` based on how many new registrations are needed in this batch.

## Step 3 — Record Each Result

For each result in the SSPanel response `results[]` array:

```bash
./scripts/provider-bindings record \
  --provider freeaisub \
  --provider-account-ref "<campaign owner account or referral code>" \
  --start-link "${REFERRAL_LINK}" \
  --executor hermes-server \
  --ss-panel-response-json-file /tmp/sspanel-response-freeaisub-<timestamp>.json
```

For batch runs with multiple results, record each result individually or write
a wrapper script that iterates over `results[]`.

## Step 4 — Verify Bot Response

Expected success response from `@freeaisub_bot` after `/start <code>`:

```text
👤 Profile

ID: <telegram_id>
Referrals: 0
Claimed Rewards: 0
Status: ✅ OK
```

If the bot responds with an "already registered" or error message, classify
accordingly:

| Bot response | Status to record |
|---|---|
| `✅ OK` / profile shown | `success` |
| Already registered / duplicate | `failed` |
| No response / timeout | `unknown` |
| sendDirectMessage returned false | `send_failed` |

## Step 5 — Check Campaign Progress

To see how many TG accounts have been registered:

```bash
AI_HARNESS_BINDINGS_DB=/var/lib/ai-harness/provider-bindings.sqlite \
  ./scripts/provider-bindings list --provider freeaisub --limit 20
```

To check referral count, open the bot manually and press `📊 Progress`.

## Adding a New Referral Bot

To onboard another bot that follows the same referral pattern:

1. Get the referral link from the bot.
2. Choose a short `provider` key (e.g., `newbot`).
3. Use that key consistently in `--provider` flags and `excludeTelegramIds` calls.
4. Add a row to the Known bots table above.
5. Add the provider to `docs/accounts/providers.md`.

No code changes to `provider_bindings.py` are needed.

## Notes

- Referral codes are not secrets, but do not commit bot message logs that may
  contain Telegram account details.
- For high-volume runs (>10 accounts per batch), increase `botResponseWaitMs`
  or split into multiple SSPanel calls.
- Check `@freeaisub_bot` rewards thresholds before running large batches:
  the next reward tier dictates how many registrations are worth targeting.
