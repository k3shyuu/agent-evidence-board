from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB = Path("work") / "board.db"


def utcnow() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def db_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path)
    return Path(os.environ.get("AEB_DB", DEFAULT_DB))


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    resolved = db_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(topic_id, key),
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS raw_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            source_id INTEGER,
            event_type TEXT NOT NULL DEFAULT 'url_capture',
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT '',
            dedupe_hash TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'new',
            captured_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE,
            FOREIGN KEY(source_id) REFERENCES sources(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS evidence_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_event_id INTEGER,
            topic_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            card_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_by TEXT NOT NULL DEFAULT 'agent',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(raw_event_id) REFERENCES raw_events(id) ON DELETE SET NULL,
            FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_card_id INTEGER,
            reviewer TEXT NOT NULL,
            verdict TEXT NOT NULL,
            confidence TEXT NOT NULL DEFAULT 'unknown',
            body TEXT NOT NULL DEFAULT '',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(evidence_card_id) REFERENCES evidence_cards(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS judge_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_card_id INTEGER,
            decision TEXT NOT NULL,
            blockers_json TEXT NOT NULL DEFAULT '[]',
            warnings_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY(evidence_card_id) REFERENCES evidence_cards(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_card_id INTEGER,
            channel TEXT NOT NULL,
            destination TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            published_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(evidence_card_id) REFERENCES evidence_cards(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_raw_events_status ON raw_events(status, captured_at);
        CREATE INDEX IF NOT EXISTS idx_cards_status ON evidence_cards(status, created_at);
        CREATE INDEX IF NOT EXISTS idx_publications_status ON publications(status, created_at);
        """
    )
    conn.commit()


def ensure_topic(conn: sqlite3.Connection, key: str, title: str | None = None) -> int:
    now = utcnow()
    title = title or key.replace("_", " ").title()
    conn.execute(
        """
        INSERT INTO topics(key, title, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET updated_at=excluded.updated_at
        """,
        (key, title, now, now),
    )
    conn.commit()
    return int(conn.execute("SELECT id FROM topics WHERE key=?", (key,)).fetchone()["id"])


def ensure_source(
    conn: sqlite3.Connection,
    topic_id: int,
    key: str,
    source_type: str,
    name: str,
    url: str,
    metadata: dict[str, Any] | None = None,
) -> int:
    now = utcnow()
    conn.execute(
        """
        INSERT INTO sources(topic_id, key, type, name, url, metadata_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(topic_id, key) DO UPDATE SET
            name=excluded.name,
            url=excluded.url,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (topic_id, key, source_type, name, url, json.dumps(metadata or {}, ensure_ascii=False), now, now),
    )
    conn.commit()
    return int(
        conn.execute("SELECT id FROM sources WHERE topic_id=? AND key=?", (topic_id, key)).fetchone()["id"]
    )


def stable_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8", errors="replace"))
        h.update(b"\0")
    return h.hexdigest()


def add_raw_event(
    conn: sqlite3.Connection,
    topic_id: int,
    source_id: int | None,
    title: str,
    body: str,
    url: str,
    metadata: dict[str, Any] | None = None,
) -> int:
    now = utcnow()
    dedupe_hash = stable_hash(url, body[:1000])
    conn.execute(
        """
        INSERT INTO raw_events(topic_id, source_id, title, body, url, dedupe_hash, captured_at, metadata_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(dedupe_hash) DO UPDATE SET
            body=excluded.body,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            topic_id,
            source_id,
            title,
            body,
            url,
            dedupe_hash,
            now,
            json.dumps(metadata or {}, ensure_ascii=False),
            now,
            now,
        ),
    )
    conn.commit()
    return int(conn.execute("SELECT id FROM raw_events WHERE dedupe_hash=?", (dedupe_hash,)).fetchone()["id"])


def add_evidence_card(
    conn: sqlite3.Connection,
    topic_id: int,
    title: str,
    card: dict[str, Any],
    raw_event_id: int | None = None,
    created_by: str = "agent",
) -> int:
    now = utcnow()
    cur = conn.execute(
        """
        INSERT INTO evidence_cards(raw_event_id, topic_id, title, card_json, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (raw_event_id, topic_id, title, json.dumps(card, ensure_ascii=False), created_by, now, now),
    )
    conn.commit()
    return int(cur.lastrowid)


def list_rows(conn: sqlite3.Connection, table: str, limit: int = 20) -> list[dict[str, Any]]:
    allowed = {"topics", "sources", "raw_events", "evidence_cards", "reviews", "judge_decisions", "publications"}
    if table not in allowed:
        raise ValueError(f"unsupported table: {table}")
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]
