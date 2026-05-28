#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB = Path(os.environ.get("AI_HARNESS_BINDINGS_DB", "data/provider-bindings.sqlite"))
DEFAULT_EXCLUDE_STATUSES = ("success", "pending", "failed", "send_failed")
VALID_STATUSES = {"pending", "success", "failed", "expired", "send_failed", "unknown"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.executescript(
            """
            create table if not exists provider_telegram_bindings (
              id integer primary key autoincrement,
              provider text not null,
              provider_account_ref text,
              telegram_id text not null,
              start_code text not null,
              start_link text not null,
              status text not null,
              bot_response_status text,
              bot_response_text text,
              ss_panel_response_json text,
              error text,
              executor text,
              run_id text,
              created_at text not null default current_timestamp,
              updated_at text not null default current_timestamp,
              activated_at text
            );

            create table if not exists telegram_accounts (
              telegram_id text primary key,
              phone text,
              status text not null default 'active',
              last_used_at text,
              created_at text not null default current_timestamp
            );

            create table if not exists telegram_action_history (
              id integer primary key autoincrement,
              telegram_id text not null,
              bot_username text not null,
              action_type text not null,
              status text not null,
              payload text,
              executor text,
              created_at text not null default current_timestamp,
              foreign key(telegram_id) references telegram_accounts(telegram_id)
            );

            create unique index if not exists provider_telegram_success_once
            on provider_telegram_bindings(provider, telegram_id)
            where status = 'success';

            create index if not exists provider_telegram_bindings_provider_status_idx
            on provider_telegram_bindings(provider, status);
            """
        )


def _lower_text(value: Any) -> str:
    return str(value or "").lower()


def _message_results_text(result: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in result.get("messageResults") or []:
        if isinstance(item, dict):
            parts.extend(str(item.get(key) or "") for key in ("error", "botResponseText", "botResponseError"))
    return " ".join(parts)


def classify_sspanel_result(result: dict[str, Any]) -> str:
    bot_response_status = _lower_text(result.get("botResponseStatus"))
    bot_response_text = _lower_text(result.get("botResponseText"))
    error_text = " ".join(
        [
            _lower_text(result.get("error")),
            _lower_text(result.get("message")),
            _message_results_text(result).lower(),
        ]
    )

    if "senddirectmessage returned false" in error_text:
        return "send_failed"
    if "this binding link has expired" in bot_response_text:
        return "expired"
    if "already bound to a different account" in bot_response_text:
        return "failed"
    if bot_response_status == "success" or "account bound successfully" in bot_response_text:
        return "success"
    if bot_response_status == "failed":
        return "failed"
    return "unknown"


def first_result_from_sspanel_response(response: dict[str, Any]) -> dict[str, Any]:
    results = response.get("results")
    if isinstance(results, list) and results and isinstance(results[0], dict):
        return results[0]
    return response


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    provider = str(record.get("provider") or "").strip().lower()
    telegram_id = str(record.get("telegram_id") or record.get("telegramId") or "").strip()
    start_code = str(record.get("start_code") or record.get("code") or "").strip()
    start_link = str(record.get("start_link") or "").strip()
    if not provider:
        raise ValueError("provider is required")
    if not telegram_id:
        raise ValueError("telegram_id is required")
    if not start_code:
        raise ValueError("start_code is required")
    if not start_link:
        raise ValueError("start_link is required")

    status = str(record.get("status") or "").strip().lower()
    if not status:
        status = classify_sspanel_result(record)
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")

    now = utc_now()
    activated_at = record.get("activated_at")
    if status == "success" and not activated_at:
        activated_at = now

    return {
        "provider": provider,
        "provider_account_ref": record.get("provider_account_ref"),
        "telegram_id": telegram_id,
        "start_code": start_code,
        "start_link": start_link,
        "status": status,
        "bot_response_status": record.get("bot_response_status") or record.get("botResponseStatus"),
        "bot_response_text": record.get("bot_response_text") or record.get("botResponseText"),
        "ss_panel_response_json": record.get("ss_panel_response_json"),
        "error": record.get("error"),
        "executor": record.get("executor") or os.environ.get("AI_HARNESS_EXECUTOR", "manual"),
        "run_id": record.get("run_id"),
        "created_at": record.get("created_at") or now,
        "updated_at": now,
        "activated_at": activated_at,
    }


def record_binding(db_path: Path, record: dict[str, Any]) -> int:
    init_db(db_path)
    row = normalize_record(record)
    with sqlite3.connect(db_path) as con:
        cursor = con.execute(
            """
            insert into provider_telegram_bindings(
              provider, provider_account_ref, telegram_id, start_code, start_link,
              status, bot_response_status, bot_response_text, ss_panel_response_json,
              error, executor, run_id, created_at, updated_at, activated_at
            )
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["provider"],
                row["provider_account_ref"],
                row["telegram_id"],
                row["start_code"],
                row["start_link"],
                row["status"],
                row["bot_response_status"],
                row["bot_response_text"],
                row["ss_panel_response_json"],
                row["error"],
                row["executor"],
                row["run_id"],
                row["created_at"],
                row["updated_at"],
                row["activated_at"],
            ),
        )
        return int(cursor.lastrowid)


def exclude_telegram_ids(
    db_path: Path,
    provider: str,
    statuses: tuple[str, ...] = DEFAULT_EXCLUDE_STATUSES,
) -> list[str]:
    init_db(db_path)
    normalized_provider = provider.strip().lower()
    placeholders = ",".join("?" for _ in statuses)
    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            f"""
            select distinct telegram_id
            from provider_telegram_bindings
            where provider = ?
              and status in ({placeholders})
            order by telegram_id
            """,
            (normalized_provider, *statuses),
        ).fetchall()
    return [str(row[0]) for row in rows]


def list_bindings(db_path: Path, provider: str | None, limit: int) -> list[dict[str, Any]]:
    init_db(db_path)
    query = """
        select id, provider, provider_account_ref, telegram_id, start_code, start_link,
               status, bot_response_status, bot_response_text, error, executor, run_id,
               created_at, updated_at, activated_at
        from provider_telegram_bindings
    """
    params: list[Any] = []
    if provider:
        query += " where provider = ?"
        params.append(provider.strip().lower())
    query += " order by id desc limit ?"
    params.append(limit)
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def load_json_arg(value: str | None, file_path: str | None) -> dict[str, Any] | None:
    if value and file_path:
        raise ValueError("use either --ss-panel-response-json or --ss-panel-response-json-file, not both")
    if file_path:
        value = Path(file_path).read_text(encoding="utf-8")
    if not value:
        return None
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("SSPanel response JSON must be an object")
    return parsed


def run_init(args: argparse.Namespace) -> int:
    init_db(Path(args.db))
    print(json.dumps({"ok": True, "db": str(Path(args.db))}, ensure_ascii=False, indent=2))
    return 0


def run_exclude(args: argparse.Namespace) -> int:
    statuses = tuple(status.strip() for status in args.statuses.split(",") if status.strip())
    ids = exclude_telegram_ids(Path(args.db), args.provider, statuses=statuses)
    if args.format == "lines":
        print("\n".join(ids))
    else:
        print(json.dumps(ids, ensure_ascii=False, indent=2))
    return 0


def run_record(args: argparse.Namespace) -> int:
    response = load_json_arg(args.ss_panel_response_json, args.ss_panel_response_json_file)
    response_result = first_result_from_sspanel_response(response) if response else {}
    record = {
        **response_result,
        "provider": args.provider,
        "provider_account_ref": args.provider_account_ref,
        "telegram_id": args.telegram_id or response_result.get("telegramId"),
        "start_code": args.start_code or response_result.get("code"),
        "start_link": args.start_link,
        "status": args.status or classify_sspanel_result(response_result),
        "bot_response_status": args.bot_response_status or response_result.get("botResponseStatus"),
        "bot_response_text": args.bot_response_text or response_result.get("botResponseText"),
        "ss_panel_response_json": json.dumps(response, ensure_ascii=False) if response else args.ss_panel_response_raw,
        "error": args.error or response_result.get("error"),
        "executor": args.executor,
        "run_id": args.run_id,
    }
    row_id = record_binding(Path(args.db), record)
    print(json.dumps({"ok": True, "id": row_id, "status": normalize_record(record)["status"]}, ensure_ascii=False, indent=2))
    return 0


def run_list(args: argparse.Namespace) -> int:
    rows = list_bindings(Path(args.db), args.provider, args.limit)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def record_action(
    db_path: Path,
    telegram_id: str,
    bot_username: str,
    action_type: str,
    status: str,
    payload: str | None,
    executor: str | None,
) -> int:
    init_db(db_path)
    now = utc_now()
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            insert into telegram_accounts(telegram_id, last_used_at)
            values (?, ?)
            on conflict(telegram_id) do update set last_used_at = excluded.last_used_at
            """,
            (telegram_id, now)
        )
        cursor = con.execute(
            """
            insert into telegram_action_history(telegram_id, bot_username, action_type, status, payload, executor, created_at)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (telegram_id, bot_username, action_type, status, payload, executor or "manual", now)
        )
        return int(cursor.lastrowid)


def run_record_action(args: argparse.Namespace) -> int:
    row_id = record_action(
        Path(args.db),
        args.telegram_id,
        args.bot_username,
        args.action_type,
        args.status,
        args.payload,
        args.executor,
    )
    print(json.dumps({"ok": True, "action_id": row_id}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Track provider Telegram binding state for ai-harness")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite DB path; defaults to AI_HARNESS_BINDINGS_DB or data/provider-bindings.sqlite")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create or migrate the provider bindings DB")
    init.set_defaults(func=run_init)

    exclude = sub.add_parser("exclude", help="Print Telegram ids to pass to SSPanel excludeTelegramIds")
    exclude.add_argument("--provider", required=True)
    exclude.add_argument("--statuses", default=",".join(DEFAULT_EXCLUDE_STATUSES))
    exclude.add_argument("--format", choices=("json", "lines"), default="json")
    exclude.set_defaults(func=run_exclude)

    record = sub.add_parser("record", help="Record one provider Telegram binding attempt")
    record.add_argument("--provider", required=True)
    record.add_argument("--provider-account-ref")
    record.add_argument("--telegram-id")
    record.add_argument("--start-code")
    record.add_argument("--start-link", required=True)
    record.add_argument("--status", choices=sorted(VALID_STATUSES))
    record.add_argument("--bot-response-status")
    record.add_argument("--bot-response-text")
    record.add_argument("--ss-panel-response-json")
    record.add_argument("--ss-panel-response-json-file")
    record.add_argument("--ss-panel-response-raw")
    record.add_argument("--error")
    record.add_argument("--executor", default=os.environ.get("AI_HARNESS_EXECUTOR", "manual"))
    record.add_argument("--run-id")
    record.set_defaults(func=run_record)

    list_cmd = sub.add_parser("list", help="List recent binding attempts")
    list_cmd.add_argument("--provider")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.set_defaults(func=run_list)

    record_action_cmd = sub.add_parser("record-action", help="Record one Telegram account action")
    record_action_cmd.add_argument("--telegram-id", required=True)
    record_action_cmd.add_argument("--bot-username", required=True)
    record_action_cmd.add_argument("--action-type", required=True)
    record_action_cmd.add_argument("--status", required=True)
    record_action_cmd.add_argument("--payload")
    record_action_cmd.add_argument("--executor")
    record_action_cmd.set_defaults(func=run_record_action)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
