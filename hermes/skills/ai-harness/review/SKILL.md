---
name: review
description: Review, verify, compare, or audit results before giving a verdict.
---

# Review

Use this skill when the user asks to check, compare, review, audit, or judge something.

## Rules

- Findings first.
- Ground claims in concrete evidence: files, logs, command output, benchmark artifacts, Notion task fields, or API responses.
- Separate facts from assumptions.
- Do not change state unless the user asks for a fix after review.
- For benchmarks, report identity risk, quality, reliability, speed, cost signals, and compatibility.

## Examples

```text
/review проверь результат benchmark freemodel
/review сравни LightningZeus и FreeModel для вайбкодинга
```
