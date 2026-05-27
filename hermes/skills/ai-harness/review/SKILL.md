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
- Do not change state unless the user asks for a fix or explicitly requests a written review artifact.
- For benchmarks, report identity risk, quality, reliability, speed, cost signals, and compatibility.

## Written Artifacts

If the user asks for a review report to be written to a file, the task is both review and artifact delivery.

Required workflow:

```text
1. inspect evidence from the relevant files/logs/commands;
2. write the review report to the requested path;
3. verify the file exists using the absolute path;
4. read the file back and confirm the expected table/sections are present;
5. run git status;
6. report findings plus artifact path and git state.
```

## Multi-Perspective Reviews

If a review needs multiple perspectives, use a lead-reviewer pattern:

1. Define review scope.
2. Define reviewer perspectives.
3. Assign evidence areas to each perspective.
4. Gather findings per perspective.
5. Consolidate duplicates and conflicts.
6. Prioritize final findings.
7. Produce the requested artifact.

Use project playbooks/templates when available instead of creating new skills for each review type.

The output must distinguish:

```text
evidence-backed findings
assumptions
recommended backlog items
```

## Examples

```text
/review проверь результат benchmark freemodel
/review сравни LightningZeus и FreeModel для вайбкодинга
```
