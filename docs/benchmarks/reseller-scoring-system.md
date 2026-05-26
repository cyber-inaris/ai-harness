# Reseller Scoring System

## Idea

Build a living reputation system for AI resellers and reseller models.

The goal is not to trust reseller claims such as "GPT-5", "Claude Opus", "unlimited", or "1000 requests per day". The system should test every new reseller/model, compare it against trusted baselines, and keep updating its score during real usage.

The final decision should answer one practical question:

```text
Which reseller/model gives the most useful vibe-coding work for the real cost and risk?
```

## Core Concept

When a new reseller or model is added, the benchmark runner should:

1. Discover available models through `/v1/models`.
2. Run smoke tests to verify the endpoint works.
3. Run model identity and behavior probes.
4. Run coding-focused benchmarks.
5. Ask a trusted judge model to score answer quality.
6. Measure objective metrics: latency, errors, retries, token accounting, streaming, tool calls, context window, and billing.
7. Store all observations.
8. Continuously update model and reseller reputation as more real traffic is observed.

This turns benchmarking from a one-time test into an ongoing reseller quality database.

## Trusted Judge Model

Use a strong trusted model as an evaluator. For example, an internal trusted Codex/GPT model can judge whether a reseller answer is useful, correct, and consistent with the claimed model family.

The judge should not be the only source of truth. It provides subjective quality scoring, while the benchmark runner records objective measurements.

Judge inputs:

| Input | Purpose |
|---|---|
| Original prompt | Understand the task |
| Reseller answer | Score the actual output |
| Expected behavior | Know what a good answer should do |
| Optional reference answer | Compare against a trusted baseline |
| Rubric | Keep scoring consistent |

Judge outputs:

| Score | Range | Meaning |
|---|---:|---|
| `correctness` | 0-5 | Is the answer technically correct? |
| `instruction_following` | 0-5 | Did it follow constraints? |
| `code_quality` | 0-5 | Is generated code usable and maintainable? |
| `reasoning_quality` | 0-5 | Does the solution make sense? |
| `model_plausibility` | 0-5 | Does behavior match the claimed model family? |
| `safety_behavior` | 0-5 | Does it resist prompt injection and unsafe requests? |

## What To Score

Use separate scores instead of one opaque number.

| Score | Weight | Source | Meaning |
|---|---:|---|---|
| `quality_score` | 25 | Judge + task checks | Real usefulness for coding tasks |
| `identity_confidence` | 15 | Probes + baselines + judge | Confidence that the model is what reseller claims |
| `cost_efficiency` | 20 | Pricing + observed usage | Useful work per dollar/account/credit/quota |
| `reliability_score` | 15 | Telemetry | Error rate, timeout rate, retry rate, uptime |
| `speed_score` | 10 | Telemetry | TTFT, latency, tokens/sec, streaming behavior |
| `compatibility_score` | 10 | API checks | OpenAI compatibility, streaming, tool calls, JSON mode |
| `risk_penalty` | -15 | Incidents | Bans, hidden overhead, suspicious routing, quota loss |

Example combined score:

```text
reseller_model_score =
  quality_score * 0.25
  + identity_confidence * 0.15
  + cost_efficiency * 0.20
  + reliability_score * 0.15
  + speed_score * 0.10
  + compatibility_score * 0.10
  - risk_penalty * 0.15
```

Each component should be stored separately so the user can choose based on priorities. For vibe coding, quality, cost efficiency, and compatibility usually matter more than raw speed.

## Pricing Normalization

Resellers use incompatible pricing systems. Do not force everything into only "price per 1M tokens". Normalize every plan into practical work units.

| Pricing model | Normalize to | Important risks |
|---|---|---|
| Per token | Effective cost per useful 1M tokens | Hidden prompt overhead, retry cost |
| Requests per day | Effective coding tasks per day | Long tasks may consume many requests |
| Account sales | Cost per successful task before ban | Bans, lost balance, unstable access |
| Credits | Useful successful work per credit | Opaque credit conversion |
| Subscription | Useful tasks per month | Soft caps, throttling, model degradation |
| Unlimited/fair-use | Stable tasks before throttle | Hidden throttling, speed drops, routing changes |

Universal metrics:

| Metric | Formula / note |
|---|---|
| `effective_cost_per_task` | Real money spent / successful useful coding tasks |
| `effective_tasks_per_day` | Successful requests per day / average requests per task |
| `effective_tokens_per_dollar` | Useful tokens / real money spent |
| `request_success_rate` | Successful requests / total requests |
| `retry_penalty` | Extra requests or tokens caused by failures |
| `ban_adjusted_cost` | Account price / useful tasks before ban |
| `hidden_overhead_ratio` | Billed prompt tokens / estimated prompt tokens |

For a plan like "1000 requests per day":

```text
daily_successful_requests =
  daily_request_limit * success_rate * throttle_factor

effective_tasks_per_day =
  floor(daily_successful_requests / average_requests_per_task)

effective_cost_per_task =
  monthly_price / (active_days_per_month * effective_tasks_per_day)
```

For account sellers:

```text
ban_adjusted_cost_per_task =
  account_price / successful_tasks_before_ban
```

## Test Levels

Use four levels of evaluation.

| Level | Purpose | Example checks |
|---|---|---|
| Smoke test | Is the endpoint usable? | `/v1/models`, one short chat request, auth, basic latency |
| Identity test | Is the claimed model plausible? | Self-ID probes, behavior probes, official baseline comparison |
| Coding benchmark | Is it useful for vibe coding? | Bug fix, test generation, refactor, JSON output, long context |
| Production telemetry | Does it stay good over time? | Real usage quality, errors, cost, bans, throttling, user acceptance |

## Production Observations

Every real request should produce an observation row.

| Field | Meaning |
|---|---|
| `provider_id` | Reseller name |
| `model_claimed` | Model requested by user/system |
| `model_returned` | Model reported by API, if any |
| `task_type` | Chat, coding, refactor, test writing, long context, tool call |
| `prompt_tokens_reported` | API-reported input tokens |
| `completion_tokens_reported` | API-reported output tokens |
| `local_prompt_tokens_estimated` | Local tokenizer estimate |
| `latency_ms` | Total response time |
| `ttft_ms` | Time to first token for streaming |
| `tokens_per_second` | Streaming/output throughput |
| `status` | Success, timeout, 429, 5xx, invalid response |
| `retry_count` | Number of retries needed |
| `judge_scores` | Trusted judge rubric scores |
| `user_feedback` | Accepted, rejected, edited, retried |
| `billing_units_spent` | Dashboard/API billing units when known |
| `ban_or_quota_event` | Account banned, quota exhausted, throttled |
| `created_at` | Timestamp |

## Score Decay

Scores should favor fresh behavior because resellers can change routing, throttle rules, or model quality.

```text
current_score =
  last_7_days_score * 0.70
  + last_30_days_score * 0.20
  + historical_score * 0.10
```

This helps detect degradation. A reseller that was good last month but now routes to a weaker model should lose rank quickly.

## Final Decision Table

The UI/report should show an operational table like this:

| Provider | Model claimed | Identity | Quality | Reliability | Speed | Cost/task | Tasks/day | Risk | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| FreeModel | `gpt-5.5` | 75 | 88 | 82 | 70 | $0.07 | 300 | Low | Use |
| LightningZeus | `cursorlm` | 35 | 61 | 78 | 80 | Unknown | 500 | High | Retest |
| Account seller A | Claude | 60 | 80 | 40 | 65 | $0.12 | Unstable | Very high | Avoid |

Verdicts:

| Verdict | Meaning |
|---|---|
| `Use` | Good enough for daily work |
| `Use for burst` | Useful as secondary capacity |
| `Retest` | Signals are mixed or model identity is unclear |
| `Sandbox only` | Fine for experiments, not important work |
| `Avoid` | Poor quality, bad economics, or high operational risk |

## Practical Principle

The system should rank resellers by real utility, not marketing claims.

For vibe coding, the winning reseller is the one that produces the most accepted coding work per dollar/day with low operational risk. A cheap reseller that gives bad code, fake model names, hidden token overhead, or frequent bans should score lower than a more expensive but stable provider.
