# OmniRoute Provider Setup

Use this skill when the user asks Hermes to add, verify, or debug an AI reseller/provider in OmniRoute.

## Context

- OmniRoute local API: `http://127.0.0.1:20128/v1`
- OmniRoute dashboard: `https://omniroute.ss-promotion.com/`
- OmniRoute API key is stored outside git.
- Provider secrets must stay outside git and should not be printed.

## Workflow

1. Record provider metadata: name, base URL, API type, model list endpoint, pricing/quota notes.
2. Validate the provider directly with a tiny non-streaming request.
3. Add or update the OmniRoute provider connection.
4. Run the OmniRoute provider health test.
5. Sync/import models.
6. Verify `/v1/models`.
7. Test one non-streaming completion through OmniRoute.
8. Test streaming separately; do not assume it works.
9. Update `/opt/ai-harness/repo/docs/routers/omniroute.md`.

## Known Providers

FreeModel:

```text
base_url: https://api.freemodel.dev/v1
prefix: free-mod
default model: free-mod/gpt-5.5
chat completions through OmniRoute: works
responses through OmniRoute: retest before using
```

LightningZeus:

```text
base_url: https://lightningzeus.com/v1
prefix: lightningzeus
models: lightningzeus/claude-opus-4.6, lightningzeus/cursorlm
chat completions through OmniRoute with stream:false: works
streaming through OmniRoute: failed with STREAM_EARLY_EOF during verification
```

