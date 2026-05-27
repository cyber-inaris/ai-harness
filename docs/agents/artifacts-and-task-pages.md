# Artifacts And Task Pages

## Purpose

Hermes should not only answer in Telegram. For long-running agent work, it should produce readable artifacts and links.

Target UX:

```text
Hermes runs a task.
Hermes writes task logs and artifacts under /var/lib/ai-harness/tasks/<task_id>/.
nginx exposes a read-only authenticated artifact URL.
Telegram response includes links to the task page, report, logs, and diffs.
```

This makes agent work inspectable from a phone without SSH.

## Directory Layout

Each task gets its own directory:

```text
/var/lib/ai-harness/tasks/
  <task_id>/
    status.json
    events.jsonl
    summary.md
    index.html                 # optional generated task page
    artifacts/
      report.md
      result.json
      diff.patch
      screenshots/
```

Example:

```text
/var/lib/ai-harness/tasks/review-20260527-001/
  status.json
  events.jsonl
  summary.md
  artifacts/
    ai-harness-agent-team-review.md
    git-status.txt
```

## Public URL Shape

nginx exposes task artifacts under the existing ngrok/nginx access pattern:

```text
https://<ngrok-id>.ngrok-free.app/artifacts/tasks/<task_id>/
```

Examples:

```text
https://<ngrok-id>.ngrok-free.app/artifacts/tasks/review-20260527-001/
https://<ngrok-id>.ngrok-free.app/artifacts/tasks/review-20260527-001/summary.md
https://<ngrok-id>.ngrok-free.app/artifacts/tasks/review-20260527-001/events.jsonl
https://<ngrok-id>.ngrok-free.app/artifacts/tasks/review-20260527-001/artifacts/ai-harness-agent-team-review.md
```

The `/artifacts/` route must require nginx Basic Auth.

## Telegram Response Format

For file-producing tasks, Hermes should answer like this:

```text
Done: Team review
Task: review-20260527-001

Top findings:
1. ...
2. ...
3. ...

Open:
https://<ngrok-id>.ngrok-free.app/artifacts/tasks/review-20260527-001/

Report:
https://<ngrok-id>.ngrok-free.app/artifacts/tasks/review-20260527-001/artifacts/ai-harness-agent-team-review.md

Logs:
https://<ngrok-id>.ngrok-free.app/artifacts/tasks/review-20260527-001/events.jsonl

Verification:
read-back: yes
git: modified docs/agents/ai-harness-agent-team-review.md
```

## Task Status JSON

Example `status.json`:

```json
{
  "task_id": "review-20260527-001",
  "title": "AI Harness team review",
  "status": "completed",
  "risk": "low",
  "created_at": "2026-05-27T09:30:00Z",
  "updated_at": "2026-05-27T09:42:00Z",
  "requested_by": "alex",
  "source": "telegram",
  "mode": "review",
  "playbook": "docs/playbooks/multi-perspective-review.md",
  "repo_artifact": "docs/agents/ai-harness-agent-team-review.md",
  "artifacts": [
    "summary.md",
    "events.jsonl",
    "artifacts/ai-harness-agent-team-review.md"
  ],
  "verification": {
    "file_exists": true,
    "read_back": true,
    "git_status_checked": true
  }
}
```

## Event Log

Use JSONL so logs are streamable and easy to parse.

Example `events.jsonl`:

```jsonl
{"ts":"2026-05-27T09:30:01Z","level":"info","event":"task.created","message":"Team review requested"}
{"ts":"2026-05-27T09:30:05Z","level":"info","event":"evidence.read","path":"docs/agents/langgraph-runtime.md"}
{"ts":"2026-05-27T09:34:10Z","level":"info","event":"artifact.write","path":"docs/agents/ai-harness-agent-team-review.md"}
{"ts":"2026-05-27T09:34:12Z","level":"info","event":"artifact.verify","read_back":true}
{"ts":"2026-05-27T09:34:14Z","level":"info","event":"task.completed"}
```

## Artifact Safety Rules

Never expose these paths:

```text
/opt/ai-harness/secrets/
/etc/ai-harness/
*.env
*.key
*.pem
*.p12
*.sqlite
*.db
*cookie*
*token*
*secret*
```

The public artifact route should only serve:

```text
/var/lib/ai-harness/tasks/
```

Do not expose the full git repo through nginx. Copy or render selected reports into the task artifact directory.

## MVP Implementation

MVP can use nginx `autoindex` for browsing task directories.

Config examples:

```text
configs/examples/nginx/artifacts.conf          # snippet for an existing server block
configs/examples/nginx/artifacts-server.conf   # standalone syntax-testable example
```

Later, replace autoindex with generated `index.html` task pages:

```text
task title
status
timeline
artifacts
top findings
git diff summary
approval state
```

## Agent Contract

For every task with artifacts, Hermes should:

1. Create `/var/lib/ai-harness/tasks/<task_id>/`.
2. Write `status.json`.
3. Append progress to `events.jsonl`.
4. Write human-readable `summary.md`.
5. Copy final user-facing files into `artifacts/`.
6. Verify repo artifact and copied artifact.
7. Return artifact URLs in Telegram.

## Verification Commands

On VPS:

```bash
TASK_ID=review-20260527-001

test -d "/var/lib/ai-harness/tasks/${TASK_ID}"
test -f "/var/lib/ai-harness/tasks/${TASK_ID}/status.json"
test -f "/var/lib/ai-harness/tasks/${TASK_ID}/events.jsonl"
find "/var/lib/ai-harness/tasks/${TASK_ID}" -maxdepth 3 -type f -print
```

From outside through ngrok:

```bash
curl -I -u "$AI_HARNESS_USER:$AI_HARNESS_PASSWORD" \
  "https://<ngrok-id>.ngrok-free.app/artifacts/tasks/${TASK_ID}/"
```
