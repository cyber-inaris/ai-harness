# Reseller Benchmark

Use this skill when the user asks Hermes to test an AI reseller, compare model quality, verify model identity, or estimate practical value for vibe coding.

## Goal

Estimate whether a reseller is useful for coding-agent work, not just whether the API returns text.

## Minimum Test Set

Run the same prompts against each provider/model:

```text
1. Direct prompt-injection refusal
2. Obfuscated prompt-injection refusal
3. Small reasoning/math task
4. Code generation task
5. Citation or honesty check
```

## Metrics

Capture:

```text
provider
model requested
model returned
base_url
endpoint type
streaming support
latency
errors
prompt tokens
completion tokens
total tokens
reasoning tokens if reported
reported hidden/cached tokens
qualitative pass/fail
identity concerns
quota/pricing model
```

## Scoring

Prefer providers that are:

```text
stable
honest about model identity
low hidden token overhead
fast enough for interactive coding
compatible with OmniRoute/Hermes
clear about quota or pricing
```

Flag providers that:

```text
claim one model but self-identify as another
inflate token usage by large hidden context
fail basic prompt-injection checks
break streaming for agent workflows
have unclear ban/account replacement policy
```

Write results to `/opt/ai-harness/repo/docs/benchmarks/`.

