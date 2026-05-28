# Provider Registry

Registry of all external providers and bots that use owned Telegram accounts.

Update this file when adding a new provider or bot campaign.

## Activation Types

```text
provider-binding  — one Telegram account binds one provider API account (1:1)
                    Token is unique per provider account, expires if unused.
referral-join     — many Telegram accounts join under one referral code (N:1)
                    Code is stable; no expiry between runs.
```

## Provider Table

| Provider key | Bot / Service | Activation type | Playbook |
|---|---|---|---|
| `freemodel` | @FreeModelDevBot | provider-binding | [freemodel-account-binding.md](../playbooks/freemodel-account-binding.md) |
| `freeaisub` | @freeaisub_bot (智联 free ai) | referral-join | [referral-bot-activation.md](../playbooks/referral-bot-activation.md) |

## FreeModel

```text
type:         provider-binding
bot:          @FreeModelDevBot
link format:  https://t.me/FreeModelDevBot?start=<token>
token scope:  one per FreeModel API account, unique, expires
registration: email verification via Mozilla Relay + Proton Web
API base:     https://api.freemodel.dev/v1
OmniRoute:    prefix=free-mod, status=active
```

Known registration aliases:

```text
wgsr7b2t7@mozmail.com
l081p64su@mozmail.com
```

## freeaisub (智联 free ai)

```text
type:          referral-join
bot:           @freeaisub_bot
link format:   https://t.me/freeaisub_bot?start=<referral_code>
referral code: e2f59b99d1  (owner's stable code — update if rotated)
registration:  just /start; no email or browser needed
```

Reward tiers observed 2026-05-28:

```text
3 refs   → ChatGPT Plus
5 refs   → Gemini Advanced
11 refs  → Super Grok
25 refs  → Cursor Pro
50 refs  → Claude 5x
75 refs  → Cursor Ultra
100 refs → Claude 20 Max
```

## Shared Infrastructure

- SSPanel bot pool: `/opt/ai-harness/secrets/sspanel.env`
- Binding history DB: `/var/lib/ai-harness/provider-bindings.sqlite`
- Pool helper: `./scripts/provider-bindings`
- Browser automation: `docs/operations/camofox-browser.md`
- Account pool management: `docs/operations/telegram-account-pool.md`
