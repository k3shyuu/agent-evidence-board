from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .board import add_evidence_card, add_raw_event, connect, ensure_source, ensure_topic, export_rows, list_rows
from .capture import capture_url
from .gate import gate_file, load_json, validate_card


def emit(value: Any) -> None:
    sys.stdout.write(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def cmd_init_db(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    conn.close()
    emit({"ok": True, "db": str(Path(args.db or "work/board.db"))})
    return 0


def cmd_ingest_url(args: argparse.Namespace) -> int:
    result = capture_url(args.url, timeout_sec=args.timeout_sec)
    conn = connect(args.db)
    try:
        topic_id = ensure_topic(conn, args.topic)
        source_id = ensure_source(
            conn,
            topic_id,
            key=args.source_key or result.capture_method,
            source_type="x" if "x.com/" in args.url or "twitter.com/" in args.url else "web",
            name=args.source_name or result.capture_method,
            url=args.url,
            metadata={"capture_method": result.capture_method},
        )
        event_id = add_raw_event(
            conn,
            topic_id,
            source_id,
            title=result.title,
            body=result.text,
            url=args.url,
            metadata=result.to_dict(),
        )
    finally:
        conn.close()
    emit({"ok": result.access_status == "full", "raw_event_id": event_id, "capture": result.to_dict()})
    return 0 if result.access_status == "full" else 2


def cmd_validate_card(args: argparse.Namespace) -> int:
    result = validate_card(load_json(args.path))
    emit(result)
    return 0 if result["ok"] else 1


def cmd_gate_card(args: argparse.Namespace) -> int:
    result = gate_file(args.path, allow_warnings=args.allow_warnings, max_x_age_days=args.max_x_age_days)
    emit(result)
    return 0 if result["ok"] else 1


def cmd_demo(args: argparse.Namespace) -> int:
    card_path = Path(__file__).resolve().parents[2] / "examples" / "sample_intelligence_card.json"
    card = load_json(card_path)
    gate = gate_file(card_path, allow_warnings=True)
    conn = connect(args.db)
    try:
        topic_id = ensure_topic(conn, "ai_agents_web3_infra", "AI agents / Web3 infra")
        raw_id = add_raw_event(
            conn,
            topic_id,
            None,
            title="Demo raw event",
            body="A demo event used to show the board flow.",
            url="https://example.com/demo",
            metadata={"demo": True},
        )
        card_id = add_evidence_card(conn, topic_id, card["title"], card, raw_event_id=raw_id, created_by="demo")
    finally:
        conn.close()
    emit({"ok": True, "raw_event_id": raw_id, "evidence_card_id": card_id, "gate": gate})
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    try:
        emit(list_rows(conn, args.table, limit=args.limit))
    finally:
        conn.close()
    return 0


def cmd_export_jsonl(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    try:
        rows = export_rows(conn, args.table, limit=args.limit)
    finally:
        conn.close()

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    emit({"ok": True, "table": args.table, "count": len(rows), "out": str(output)})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aeb", description="Agent Evidence Board CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init-db", help="Create or migrate the SQLite board.")
    p.add_argument("--db", default=None, help="SQLite database path. Defaults to AEB_DB or work/board.db.")
    p.set_defaults(func=cmd_init_db)

    p = sub.add_parser("ingest-url", help="Capture a public URL into raw_events.")
    p.add_argument("url")
    p.add_argument("--db", default=None, help="SQLite database path. Defaults to AEB_DB or work/board.db.")
    p.add_argument("--topic", default="general")
    p.add_argument("--source-key", default="")
    p.add_argument("--source-name", default="")
    p.add_argument("--timeout-sec", type=int, default=15)
    p.set_defaults(func=cmd_ingest_url)

    p = sub.add_parser("validate-card", help="Validate an evidence card JSON file.")
    p.add_argument("path")
    p.add_argument("--db", default=None, help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_validate_card)

    p = sub.add_parser("gate-card", help="Run publication gate on an evidence card JSON file.")
    p.add_argument("path")
    p.add_argument("--db", default=None, help=argparse.SUPPRESS)
    p.add_argument("--allow-warnings", action="store_true")
    p.add_argument("--max-x-age-days", type=int, default=7)
    p.set_defaults(func=cmd_gate_card)

    p = sub.add_parser("demo", help="Insert a demo event and card.")
    p.add_argument("--db", default=None, help="SQLite database path. Defaults to AEB_DB or work/board.db.")
    p.set_defaults(func=cmd_demo)

    p = sub.add_parser("list", help="List recent rows from a board table.")
    p.add_argument("table")
    p.add_argument("--db", default=None, help="SQLite database path. Defaults to AEB_DB or work/board.db.")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("export-jsonl", help="Export a board table as JSONL.")
    p.add_argument("table")
    p.add_argument("--out", required=True, help="Output JSONL path.")
    p.add_argument("--db", default=None, help="SQLite database path. Defaults to AEB_DB or work/board.db.")
    p.add_argument("--limit", type=int, default=None)
    p.set_defaults(func=cmd_export_jsonl)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
