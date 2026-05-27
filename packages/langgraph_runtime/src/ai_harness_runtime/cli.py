from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
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
COMMAND_ALIASES = {
    "/status": ("status", None),
    "status": ("status", None),
    "статус": ("status", None),
    "что сейчас работает": ("status", None),
    "/omni": ("omni", None),
    "omni": ("omni", None),
    "/omniroute": ("omni", None),
    "omniroute": ("omni", None),
    "проверь роутер": ("omni", None),
    "статус роутера": ("omni", None),
    "/hermes": ("hermes", None),
    "hermes": ("hermes", None),
    "проверь hermes": ("hermes", None),
    "статус hermes": ("hermes", None),
    "/deploy status": ("deploy", "status"),
    "deploy status": ("deploy", "status"),
    "статус деплоя": ("deploy", "status"),
}
COMMANDS = {
    "status": {
        "mode": "review",
        "risk": "low",
        "approval": "not_required",
        "description": "Read-only summary of host, services, docker, gateway, and repo state.",
    },
    "omni": {
        "mode": "review",
        "risk": "low",
        "approval": "not_required",
        "description": "Read-only OmniRoute health, container, route, and model availability check.",
    },
    "hermes": {
        "mode": "review",
        "risk": "low",
        "approval": "not_required",
        "description": "Read-only Hermes gateway/dashboard/config/tooling check.",
    },
    "deploy": {
        "mode": "review",
        "risk": "low",
        "approval": "not_required",
        "description": "Read-only deployment/git/nginx/systemd status.",
        "subcommands": {"status": "Read-only deployment status."},
    },
}


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


def normalize_message(message: str) -> str:
    return re.sub(r"\s+", " ", message.strip().lower())


def route_command(message: str) -> dict:
    text = normalize_message(message)
    parts = text.split()
    if text in COMMAND_ALIASES:
        command, subcommand = COMMAND_ALIASES[text]
    elif parts and parts[0] in {"/status", "status"}:
        command, subcommand = "status", None
    elif parts and parts[0] in {"/omni", "/omniroute", "omni", "omniroute"}:
        command, subcommand = "omni", None
    elif parts and parts[0] in {"/hermes", "hermes"}:
        command, subcommand = "hermes", None
    elif len(parts) >= 2 and parts[0] in {"/deploy", "deploy"} and parts[1] == "status":
        command, subcommand = "deploy", "status"
    elif text in {"проверь сервер", "статус сервера", "server status"}:
        command, subcommand = "status", None
    else:
        return {
            "matched": False,
            "message": message,
            "reason": "no preset command matched",
            "choices": ["/status", "/omni", "/hermes", "/deploy status"],
        }

    meta = COMMANDS[command]
    return {
        "matched": True,
        "command": command,
        "subcommand": subcommand,
        "mode": meta["mode"],
        "risk": meta["risk"],
        "approval": meta["approval"],
        "description": meta["description"],
        "verification": "commands",
        "read_only": True,
    }


def command_result(name: str, cmd: list[str], timeout: int = 20) -> dict:
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(DEFAULT_REPO),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        output = completed.stdout.strip()
        if has_secret_marker(output):
            output = "<redacted: output looked like it contained a secret>"
        return {"name": name, "exit_code": completed.returncode, "output": output[-4000:]}
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "").strip() if isinstance(exc.stdout, str) else ""
        return {"name": name, "exit_code": 124, "output": f"timed out after {timeout}s\n{output[-1000:]}"}


def run_read_only_checks(command: str, subcommand: str | None) -> dict:
    if command == "status":
        checks = [
            ("host", ["bash", "-lc", "hostname; date; uptime"]),
            (
                "services",
                [
                    "systemctl",
                    "is-active",
                    "ssh",
                    "tailscaled",
                    "nginx",
                    "cloudflared",
                    "docker",
                    "hermes-gateway",
                    "hermes-dashboard",
                ],
            ),
            ("docker", ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"]),
            ("gateway", ["curl", "-fsS", "http://127.0.0.1:8080/healthz"]),
            ("tasks", [str(DEFAULT_REPO / "scripts/agent-task"), "status", "--limit", "5"]),
            ("git", ["git", "status", "--short", "--branch"]),
        ]
    elif command == "omni":
        checks = [
            ("container", ["docker", "ps", "--filter", "name=ai-harness-omniroute", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"]),
            ("require-login", ["curl", "-fsS", "http://127.0.0.1:20128/api/settings/require-login"]),
            ("models", ["bash", "-lc", "curl -fsS http://127.0.0.1:20128/v1/models | jq -r '.data[0:12][]?.id'"]),
            ("public-route", ["bash", "-lc", "curl -sS -o /dev/null -w '%{http_code}\\n' -H 'Host: omniroute.ss-promotion.com' http://127.0.0.1:8080/login"]),
        ]
    elif command == "hermes":
        checks = [
            ("services", ["systemctl", "is-active", "hermes-gateway", "hermes-dashboard"]),
            ("gateway-status", ["/home/ai/.local/bin/hermes", "gateway", "status"]),
            ("tools-telegram", ["/home/ai/.local/bin/hermes", "tools", "list", "--platform", "telegram"]),
            ("mcp", ["/home/ai/.local/bin/hermes", "mcp", "list"]),
            ("dashboard", ["bash", "-lc", "curl -sS -o /dev/null -w '%{http_code}\\n' http://127.0.0.1:9119/"]),
        ]
    elif command == "deploy" and subcommand == "status":
        checks = [
            ("git", ["git", "status", "--short", "--branch"]),
            ("last-commit", ["git", "log", "--oneline", "-1"]),
            ("nginx", ["sudo", "nginx", "-t"]),
            ("services", ["systemctl", "is-active", "nginx", "cloudflared", "hermes-gateway", "hermes-dashboard"]),
            ("repo-remote", ["git", "remote", "-v"]),
        ]
    else:
        raise SystemExit(f"Unknown read-only command: {command} {subcommand or ''}".strip())

    results = [command_result(name, cmd) for name, cmd in checks]
    ok = all(item["exit_code"] == 0 for item in results)
    return {
        "command": command,
        "subcommand": subcommand,
        "read_only": True,
        "ok": ok,
        "results": results,
    }


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


def run_command_route(args: argparse.Namespace) -> int:
    print(json.dumps(route_command(args.message), ensure_ascii=False, indent=2))
    return 0


def run_command_run(args: argparse.Namespace) -> int:
    route = route_command(args.command if not args.subcommand else f"{args.command} {args.subcommand}")
    if not route.get("matched"):
        raise SystemExit(f"Unknown command preset: {args.command} {args.subcommand or ''}".strip())
    result = run_read_only_checks(route["command"], route.get("subcommand"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


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

    command_route = sub.add_parser("command-route", help="Map a Telegram-style message to a command preset")
    command_route.add_argument("--message", required=True)
    command_route.set_defaults(func=run_command_route)

    command_run = sub.add_parser("command-run", help="Run a read-only command preset")
    command_run.add_argument("command", choices=sorted(COMMANDS))
    command_run.add_argument("subcommand", nargs="?")
    command_run.set_defaults(func=run_command_run)

    notion_task = sub.add_parser("notion-create-task", help="Create a Notion task")
    add_notion_task_args(notion_task)
    notion_task.set_defaults(func=run_notion_create_task)

    brainstorm = sub.add_parser("brainstorm-start", help="Create a local brainstorming task record")
    brainstorm.add_argument("--topic", required=True)
    brainstorm.add_argument("--task-id")
    brainstorm.set_defaults(func=run_brainstorm_start)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
