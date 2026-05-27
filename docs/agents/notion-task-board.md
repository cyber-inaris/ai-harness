# Notion Task Board

## Purpose

Notion is the human-facing board for `ai-harness` projects and tasks.

Hermes and future planners should use Notion for task selection and high-level status. LangGraph remains the execution runtime and stores detailed events, logs, and artifacts outside Notion.

## Current Board

```text
name: AI Benchmarks
url:  https://www.notion.so/36db5aee9b288037be25f9620837ad3b
id:   36db5aee9b288037be25f9620837ad3b
```

The server stores the Notion runtime config in:

```text
/opt/ai-harness/secrets/notion.env
```

Required variables:

```text
NOTION_API_TOKEN
NOTION_TASKS_DATABASE_ID
NOTION_PROJECTS_DATABASE_ID
```

`NOTION_PROJECTS_DATABASE_ID` is optional for now.

## Board Properties

The current database title property is:

```text
Project name
```

Agent workflow properties added for `ai-harness`:

| Property | Type | Purpose |
|---|---|---|
| `Task Type` | select | `infra`, `benchmark`, `provider`, `router`, `docs`, `research` |
| `Risk` | select | `low`, `medium`, `high`, `critical` |
| `Agent` | select | `planner`, `ops`, `benchmark`, `coder`, `reviewer`, `judge` |
| `LangGraph Task ID` | rich text | Link Notion task to local runtime task |
| `Artifact` | url | Link final report, benchmark output, PR, or dashboard |
| `Approval Required` | checkbox | Marks tasks that need explicit human approval |

Existing useful properties:

| Property | Type |
|---|---|
| `Status` | status |
| `Priority` | select |
| `Assignee` | people |
| `Start date` | date |
| `End date` | date |
| `Team` | multi-select |

## Status Policy

Use Notion for project-level state only:

```text
Inbox / Not started
Ready
Planned
Running
Review
Needs Approval
Blocked
Done
```

If the Notion status options differ, keep the closest existing values and document the mapping before automating writes.

## Runtime Boundary

Do not write noisy execution logs to Notion.

Use this split:

```text
Notion:
  task title
  status
  owner/agent
  risk
  priority
  short result
  artifact links

LangGraph SQLite:
  task events
  tool summaries
  retry history
  runtime status

/var/lib/ai-harness:
  benchmark JSON
  task summaries
  generated reports
  raw artifacts
```

## Starter Tasks

Initial tasks created in Notion:

```text
Connect Notion board to Hermes planner
Implement Notion task sync in LangGraph runtime
Run first provider benchmark from Notion task
Document Notion task board workflow
```

## Access Setup

The server token belongs to the Notion integration:

```text
Hermes connection
```

To give the integration access to a page or database:

1. Open the target Notion page/database as a full page.
2. Open the page menu.
3. Add `Hermes connection` under Connections.
4. Verify from the server:

```bash
python3 - <<'PY'
import json
import urllib.request
from pathlib import Path

env = dict(
    line.split("=", 1)
    for line in Path("/opt/ai-harness/secrets/notion.env").read_text().splitlines()
    if "=" in line
)
token = env["NOTION_API_TOKEN"]
db = env["NOTION_TASKS_DATABASE_ID"]
headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
}
req = urllib.request.Request(f"https://api.notion.com/v1/databases/{db}", headers=headers)
with urllib.request.urlopen(req, timeout=20) as resp:
    data = json.load(resp)
print(data["object"], data["id"])
PY
```

Never commit `notion.env` or Notion tokens.

## Next Integration Step

Add a LangGraph command that:

1. lists Notion tasks in a ready/planned state;
2. claims one task by writing `LangGraph Task ID`;
3. runs the selected workflow;
4. updates status and artifact link;
5. asks for approval before high or critical work.
