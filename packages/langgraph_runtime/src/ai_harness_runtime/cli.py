from __future__ import annotations

import argparse
import json
import re
import sqlite3
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


DEFAULT_REPO = Path("/opt/ai-harness/repo")
DEFAULT_DATA = Path("/var/lib/ai-harness/agent")
DEFAULT_NOTION_ENV = Path("/opt/ai-harness/secrets/notion.env")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"fe_oa_[A-Za-z0-9]{16,}"),
    re.compile(r"\b[A-Za-z0-9_-]{20,}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
NOTION_TRIGGERS = [
    "add to board",
    "добавь в борду",
    "добавь на борду",
    "создай задачу",
    "запиши в notion",
    "поставь в backlog",
    "добавь в backlog",
]
BRAINSTORM_TRIGGERS = [
    "brainstorm",
    "брейншторм",
    "давай подумаем",
    "придумай архитектуру",
    "спроектируй",
    "design",
]
PLAN_TRIGGERS = ["plan", "план", "распиши", "разбей", "декомпоз"]
EXECUTE_TRIGGERS = ["запусти", "сделай", "установи", "почини", "deploy", "run", "test now"]
REVIEW_TRIGGERS = ["review", "проверь", "сравни", "оцени", "audit", "verify"]
NOTION_VERSION = "2022-06-28"


class TaskState(TypedDict, total=False):
    task_id: str
    topic: str
    target_path: str
    risk_level: str
    status: str
    report: str
    review: dict
    artifacts: list[str]


@dataclass(frozen=True)
class RuntimePaths:
    repo: Path
    data: Path

    @property
    def db(self) -> Path:
        return self.data / "tasks.sqlite"

    @property
    def task_root(self) -> Path:
        return self.data / "tasks"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "task"


def has_secret_marker(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        raise SystemExit(f"Missing env file: {path}")
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def notion_request(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        f"https://api.notion.com/v1/{path.lstrip('/')}",
        data=data,
        headers=notion_headers(token),
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"Notion API error {exc.code}: {body}") from exc


def notion_config(env_path: str) -> tuple[str, str]:
    env = load_env_file(Path(env_path))
    token = env.get("NOTION_API_TOKEN", "")
    database_id = env.get("NOTION_TASKS_DATABASE_ID", "")
    if not token:
        raise SystemExit("NOTION_API_TOKEN is missing")
    if not database_id:
        raise SystemExit("NOTION_TASKS_DATABASE_ID is missing")
    return token, database_id


def notion_database_schema(token: str, database_id: str) -> dict[str, str]:
    database = notion_request("GET", f"databases/{database_id}", token)
    return {name: prop.get("type", "") for name, prop in database.get("properties", {}).items()}


def notion_title_property(schema: dict[str, str]) -> str:
    for name, prop_type in schema.items():
        if prop_type == "title":
            return name
    raise SystemExit("Notion task database has no title property")


def maybe_set_property(properties: dict, schema: dict[str, str], name: str, value: object) -> None:
    prop_type = schema.get(name)
    if not prop_type:
        return
    if prop_type == "select" and value:
        properties[name] = {"select": {"name": str(value)}}
    elif prop_type == "status" and value:
        properties[name] = {"status": {"name": str(value)}}
    elif prop_type == "rich_text" and value:
        properties[name] = {"rich_text": [{"text": {"content": str(value)}}]}
    elif prop_type == "url" and value:
        properties[name] = {"url": str(value)}
    elif prop_type == "checkbox":
        properties[name] = {"checkbox": bool(value)}


def classify_mode(message: str) -> tuple[str, str]:
    text = message.lower()
    checks = [
        ("notion", NOTION_TRIGGERS, "user explicitly asked to add or write something to Notion/tasks"),
        ("brainstorm", BRAINSTORM_TRIGGERS, "user asked for brainstorming or design exploration"),
        ("review", REVIEW_TRIGGERS, "user asked to check, compare, review, or verify"),
        ("execute", EXECUTE_TRIGGERS, "user asked to run or change something now"),
        ("plan", PLAN_TRIGGERS, "user asked for a plan or decomposition"),
    ]
    for mode, triggers, reason in checks:
        if any(trigger in text for trigger in triggers):
            return mode, reason
    return "ask", "no action trigger detected"


def resolve_allowed_target(target: str, paths: RuntimePaths) -> Path:
    raw = Path(target).expanduser()
    if not raw.is_absolute():
        raw = paths.repo / raw
    resolved = raw.resolve()
    allowed_roots = [
        (paths.repo / "docs").resolve(),
        (paths.data / "tasks").resolve(),
        Path("/var/lib/ai-harness/benchmarks").resolve(),
    ]
    if not any(resolved == root or root in resolved.parents for root in allowed_roots):
        roots = ", ".join(str(root) for root in allowed_roots)
        raise SystemExit(f"Refusing target outside allowed roots: {resolved}. Allowed: {roots}")
    return resolved


def init_db(paths: RuntimePaths) -> None:
    paths.data.mkdir(parents=True, exist_ok=True)
    paths.task_root.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(paths.db) as con:
        con.executescript(
            """
            create table if not exists tasks (
              task_id text primary key,
              kind text not null,
              topic text not null,
              target_path text,
              risk_level text not null,
              status text not null,
              created_at text not null,
              updated_at text not null
            );
            create table if not exists artifacts (
              id integer primary key autoincrement,
              task_id text not null,
              path text not null,
              kind text not null,
              created_at text not null
            );
            create table if not exists events (
              id integer primary key autoincrement,
              task_id text not null,
              event text not null,
              payload_json text not null,
              created_at text not null
            );
            """
        )


def record_task(paths: RuntimePaths, state: TaskState, kind: str = "docs-smoke") -> None:
    now = utc_now()
    with sqlite3.connect(paths.db) as con:
        con.execute(
            """
            insert into tasks(task_id, kind, topic, target_path, risk_level, status, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(task_id) do update set
              status=excluded.status,
              target_path=excluded.target_path,
              updated_at=excluded.updated_at
            """,
            (
                state["task_id"],
                kind,
                state["topic"],
                state.get("target_path"),
                state.get("risk_level", "low"),
                state.get("status", "requested"),
                now,
                now,
            ),
        )


def record_event(paths: RuntimePaths, task_id: str, event: str, payload: dict) -> None:
    with sqlite3.connect(paths.db) as con:
        con.execute(
            "insert into events(task_id, event, payload_json, created_at) values (?, ?, ?, ?)",
            (task_id, event, json.dumps(payload, ensure_ascii=False), utc_now()),
        )


def record_artifact(paths: RuntimePaths, task_id: str, path: Path, kind: str) -> None:
    with sqlite3.connect(paths.db) as con:
        con.execute(
            "insert into artifacts(task_id, path, kind, created_at) values (?, ?, ?, ?)",
            (task_id, str(path), kind, utc_now()),
        )


def build_graph(paths: RuntimePaths):
    def plan(state: TaskState) -> TaskState:
        record_event(paths, state["task_id"], "planned", {"topic": state["topic"]})
        return {"status": "planned", "risk_level": "low"}

    def write_report(state: TaskState) -> TaskState:
        target = resolve_allowed_target(state["target_path"], paths)
        target.parent.mkdir(parents=True, exist_ok=True)
        body = f"""# {state["topic"]}

## Purpose

This is a LangGraph smoke-test artifact for the ai-harness agent runtime.

## What Ran

The local `docs-smoke` workflow planned a low-risk documentation task, wrote this markdown file, and sent it to the reviewer node.

## Output Path

```text
{target}
```

## Next Step

Use this runtime as the base for benchmark-provider and provider-review workflows.
"""
        if has_secret_marker(body):
            raise SystemExit("Refusing to write report that appears to contain a secret")
        target.write_text(body, encoding="utf-8")
        record_artifact(paths, state["task_id"], target, "markdown-report")
        record_event(paths, state["task_id"], "report_written", {"path": str(target)})
        return {"status": "report_written", "report": body, "artifacts": [str(target)]}

    def review(state: TaskState) -> TaskState:
        report = state.get("report", "")
        findings: list[str] = []
        if has_secret_marker(report):
            findings.append("report appears to contain a secret")
        for section in ["## Purpose", "## What Ran", "## Output Path", "## Next Step"]:
            if section not in report:
                findings.append(f"missing section: {section}")
        verdict = "pass" if not findings else "fail"
        review_result = {"verdict": verdict, "findings": findings}
        task_dir = paths.task_root / state["task_id"]
        task_dir.mkdir(parents=True, exist_ok=True)
        summary_path = task_dir / "summary.json"
        summary = {**state, "status": "completed" if verdict == "pass" else "failed", "review": review_result}
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        record_artifact(paths, state["task_id"], summary_path, "task-summary")
        record_event(paths, state["task_id"], "reviewed", review_result)
        return {"status": summary["status"], "review": review_result, "artifacts": state.get("artifacts", []) + [str(summary_path)]}

    graph = StateGraph(TaskState)
    graph.add_node("plan", plan)
    graph.add_node("write_report", write_report)
    graph.add_node("review", review)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "write_report")
    graph.add_edge("write_report", "review")
    graph.add_edge("review", END)
    return graph.compile()


def run_docs_smoke(args: argparse.Namespace) -> int:
    paths = RuntimePaths(repo=Path(args.repo), data=Path(args.data))
    init_db(paths)
    task_id = args.task_id or f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slugify(args.topic)}"
    target = resolve_allowed_target(args.target, paths)
    initial: TaskState = {
        "task_id": task_id,
        "topic": args.topic,
        "target_path": str(target),
        "risk_level": "low",
        "status": "requested",
        "artifacts": [],
    }
    record_task(paths, initial)
    result = build_graph(paths).invoke(initial)
    record_task(paths, {**initial, **result})
    print(json.dumps({**initial, **result}, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "completed" else 2


def show_status(args: argparse.Namespace) -> int:
    paths = RuntimePaths(repo=Path(args.repo), data=Path(args.data))
    init_db(paths)
    with sqlite3.connect(paths.db) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "select task_id, kind, topic, status, updated_at from tasks order by updated_at desc limit ?",
            (args.limit,),
        ).fetchall()
    print(json.dumps([dict(row) for row in rows], ensure_ascii=False, indent=2))
    return 0


def run_mode_route(args: argparse.Namespace) -> int:
    mode, reason = classify_mode(args.message)
    print(
        json.dumps(
            {
                "mode": mode,
                "reason": reason,
                "message": args.message,
                "recommended_next": {
                    "ask": "answer directly",
                    "notion": "create or update Notion state only",
                    "brainstorm": "start brainstorming and wait for design approval before implementation",
                    "plan": "produce a plan or task breakdown",
                    "execute": "start a bounded workflow after safety checks",
                    "review": "inspect evidence and report findings first",
                }[mode],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def run_notion_create_task(args: argparse.Namespace) -> int:
    if has_secret_marker(args.title) or has_secret_marker(args.body or ""):
        raise SystemExit("Refusing to create a Notion task that appears to contain a secret")
    token, database_id = notion_config(args.notion_env)
    schema = notion_database_schema(token, database_id)
    title_property = notion_title_property(schema)
    properties: dict = {
        title_property: {"title": [{"text": {"content": args.title}}]},
    }
    maybe_set_property(properties, schema, "Task Type", args.type)
    maybe_set_property(properties, schema, "Risk", args.risk)
    maybe_set_property(properties, schema, "Agent", args.agent)
    maybe_set_property(properties, schema, "Priority", args.priority)
    maybe_set_property(properties, schema, "Status", args.status)
    maybe_set_property(properties, schema, "LangGraph Task ID", args.langgraph_task_id)
    maybe_set_property(properties, schema, "Artifact", args.artifact)
    maybe_set_property(properties, schema, "Approval Required", args.approval_required)

    children = []
    if args.body:
        children.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": args.body}}]},
            }
        )
    payload = {"parent": {"database_id": database_id}, "properties": properties}
    if children:
        payload["children"] = children
    page = notion_request("POST", "pages", token, payload)
    print(
        json.dumps(
            {
                "created": True,
                "title": args.title,
                "page_id": page.get("id"),
                "url": page.get("url"),
                "database_id": database_id,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def run_brainstorm_start(args: argparse.Namespace) -> int:
    paths = RuntimePaths(repo=Path(args.repo), data=Path(args.data))
    init_db(paths)
    task_id = args.task_id or f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slugify(args.topic)}"
    state: TaskState = {
        "task_id": task_id,
        "topic": args.topic,
        "risk_level": "low",
        "status": "brainstorming",
        "artifacts": [],
    }
    record_task(paths, state, kind="brainstorm")
    record_event(
        paths,
        task_id,
        "brainstorm_started",
        {
            "topic": args.topic,
            "rules": [
                "explore context first",
                "ask one question at a time",
                "present approaches and design",
                "wait for approval before implementation",
                "write approved spec to docs/superpowers/specs",
            ],
        },
    )
    task_dir = paths.task_root / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    summary_path = task_dir / "brainstorm.json"
    summary = {
        "task_id": task_id,
        "topic": args.topic,
        "status": "brainstorming",
        "next_step": "ask one clarifying question or present approaches if enough context exists",
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    record_artifact(paths, task_id, summary_path, "brainstorm-summary")
    print(json.dumps({**summary, "summary_path": str(summary_path)}, ensure_ascii=False, indent=2))
    return 0


def add_notion_task_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--type", default="research")
    parser.add_argument("--risk", default="low")
    parser.add_argument("--agent", default="planner")
    parser.add_argument("--priority", default="Normal")
    parser.add_argument("--status")
    parser.add_argument("--langgraph-task-id", default="")
    parser.add_argument("--artifact", default="")
    parser.add_argument("--approval-required", action="store_true")
    parser.add_argument("--notion-env", default=str(DEFAULT_NOTION_ENV))


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Harness LangGraph task runtime")
    parser.add_argument("--repo", default=str(DEFAULT_REPO))
    parser.add_argument("--data", default=str(DEFAULT_DATA))
    sub = parser.add_subparsers(dest="command", required=True)

    smoke = sub.add_parser("docs-smoke", help="Run a low-risk documentation smoke workflow")
    smoke.add_argument("--topic", required=True)
    smoke.add_argument("--target", required=True)
    smoke.add_argument("--task-id")
    smoke.set_defaults(func=run_docs_smoke)

    status = sub.add_parser("status", help="Show recent task records")
    status.add_argument("--limit", type=int, default=10)
    status.set_defaults(func=show_status)

    route = sub.add_parser("mode-route", help="Classify a user message into a Hermes mode")
    route.add_argument("--message", required=True)
    route.set_defaults(func=run_mode_route)

    notion_task = sub.add_parser("notion-create-task", help="Create a Notion task")
    add_notion_task_args(notion_task)
    notion_task.set_defaults(func=run_notion_create_task)

    board = sub.add_parser("board-create", help=argparse.SUPPRESS)
    add_notion_task_args(board)
    board.set_defaults(func=run_notion_create_task)

    brainstorm = sub.add_parser("brainstorm-start", help="Create a local brainstorming task record")
    brainstorm.add_argument("--topic", required=True)
    brainstorm.add_argument("--task-id")
    brainstorm.set_defaults(func=run_brainstorm_start)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
