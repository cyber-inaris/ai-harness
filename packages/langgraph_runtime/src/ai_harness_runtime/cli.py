from __future__ import annotations

import argparse
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


DEFAULT_REPO = Path("/opt/ai-harness/repo")
DEFAULT_DATA = Path("/var/lib/ai-harness/agent")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"fe_oa_[A-Za-z0-9]{16,}"),
    re.compile(r"\b[A-Za-z0-9_-]{20,}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


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

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

