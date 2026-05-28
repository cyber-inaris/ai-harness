# Dataview Dashboards

All dashboards use the [Dataview](https://blacksmithgu.github.io/obsidian-dataview/) plugin.
They are seeded into the vault by `scripts/bootstrap-vaults.sh`.

> **Prerequisites**: Install the **Dataview** community plugin in Obsidian and enable
> `JavaScript Queries` and `Inline Queries` in its settings.

---

## 1. Task Dashboard (`10_tasks/Dashboard.md`)

### All Open Tasks — Table View

```dataview
TABLE priority, status, due, project AS "Project"
FROM "10_tasks"
WHERE type = "task" AND status != "done"
SORT priority DESC, due ASC
```

### Tasks by Project

```dataview
TABLE rows.file.link AS "Task", rows.status, rows.due
FROM "10_tasks"
WHERE type = "task" AND status != "done"
GROUP BY project
```

### Overdue Tasks

```dataview
LIST
FROM "10_tasks"
WHERE type = "task" AND status != "done" AND due < date(today)
SORT due ASC
```

### Completed This Week

```dataview
TABLE priority, project, file.mtime AS "Completed"
FROM "10_tasks"
WHERE type = "task" AND status = "done" AND file.mtime >= date(today) - dur(7 days)
SORT file.mtime DESC
```

### Task Checklist Tracker

```dataview
TASK
FROM "10_tasks"
WHERE !completed
GROUP BY file.link
```

---

## 2. Project Dashboard (`20_projects/Dashboard.md`)

### All Projects — Status View

```dataview
TABLE status, priority, owner, file.mtime AS "Last Updated"
FROM "20_projects"
WHERE type = "project"
SORT status ASC, priority DESC
```

### Active Projects with Open Tasks

```dataview
TABLE rows.file.link AS "Open Tasks", rows.status AS "Task Status"
FROM "10_tasks"
WHERE type = "task" AND status != "done" AND project
GROUP BY project
```

### Recently Updated Projects

```dataview
LIST
FROM "20_projects"
WHERE type = "project" AND status = "active"
SORT file.mtime DESC
LIMIT 10
```

---

## 3. Research Dashboard (`30_research/Dashboard.md`)

### All Research Notes

```dataview
TABLE status, tags, file.mtime AS "Last Updated"
FROM "30_research"
WHERE type = "research"
SORT file.mtime DESC
```

### Research by Status

```dataview
TABLE rows.file.link AS "Notes"
FROM "30_research"
WHERE type = "research"
GROUP BY status
```

### Recent Research (last 14 days)

```dataview
LIST
FROM "30_research"
WHERE type = "research" AND file.ctime >= date(today) - dur(14 days)
SORT file.ctime DESC
```

---

## 4. Knowledge Base Index (`40_knowledge/Dashboard.md`)

### All Knowledge Notes — by Tag

```dataview
TABLE tags, file.mtime AS "Last Modified"
FROM "40_knowledge"
WHERE type = "knowledge"
SORT tags ASC, file.mtime DESC
```

### Recently Added

```dataview
LIST
FROM "40_knowledge"
WHERE type = "knowledge"
SORT file.ctime DESC
LIMIT 20
```

### Runbooks (infra knowledge)

```dataview
TABLE status, file.mtime AS "Last Updated"
FROM "40_knowledge/infra"
WHERE subtype = "runbook"
SORT file.mtime DESC
```

---

## 5. Idea Pipeline Dashboard (`50_ideas/Dashboard.md`)

### Ideas by Stage

```dataview
TABLE status, priority, file.ctime AS "Created"
FROM "50_ideas"
WHERE type = "idea"
SORT status ASC, priority DESC
```

### Ready to Promote

```dataview
LIST
FROM "50_ideas"
WHERE type = "idea" AND status = "ready"
SORT priority DESC
```

---

## 6. Agent Activity Dashboard (`70_agents/Dashboard.md`)

### Agent Index

```dataview
TABLE status, file.mtime AS "Last Active"
FROM "70_agents"
WHERE type = "agent"
SORT file.mtime DESC
```

### Recent Agent Files

```dataview
LIST
FROM "vault-agents"
WHERE file.mtime >= date(today) - dur(1 days)
SORT file.mtime DESC
LIMIT 30
```

---

## 7. Combined Inbox View (`00_inbox/Dashboard.md`)

### Items Pending Review

```dataview
TABLE file.ctime AS "Arrived", type, status
FROM "00_inbox"
WHERE type != null
SORT file.ctime ASC
```

### Stale Inbox Items (> 48h)

```dataview
LIST
FROM "00_inbox"
WHERE file.ctime < date(today) - dur(2 days)
SORT file.ctime ASC
```

---

## YAML Frontmatter Reference

All notes in the vault should include this frontmatter for Dataview to index them:

```yaml
---
type: task | project | research | knowledge | idea | agent
status: open | active | in-progress | done | paused | blocked | draft | ready | promoted
priority: low | medium | high | critical
created: 2026-05-28
due: 2026-06-01           # tasks only
project: "[[Project Name]]"  # tasks only
assigned_to: human | task-agent | research-agent  # tasks only
owner: human | orchestration-agent  # projects only
subtype: runbook           # knowledge sub-types
tags: [tag1, tag2]
---
```
