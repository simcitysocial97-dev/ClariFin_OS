"""Migration 004 — import_runs table (M08).

Additive-only DDL for persisting post-upload pipeline summaries:

    id          INTEGER PRIMARY KEY AUTOINCREMENT
    statement_id   INTEGER  (nullable — CSV imports may not have one)
    started_at     TEXT DEFAULT (datetime('now'))
    completed_at   TEXT
    has_errors     INTEGER DEFAULT 0
    summary_json   TEXT NOT NULL
    created_at     TEXT DEFAULT (datetime('now'))
"""

from __future__ import annotations

import sqlite3

DESCRIPTION = "import runs tracking"

DDL = """
CREATE TABLE IF NOT EXISTS import_runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id  INTEGER,
    started_at    TEXT DEFAULT (datetime('now')),
    completed_at  TEXT,
    has_errors    INTEGER DEFAULT 0,
    summary_json  TEXT NOT NULL,
    created_at    TEXT DEFAULT (datetime('now'))
)
"""


def migrate(conn: sqlite3.Connection) -> None:
    conn.execute(DDL)
    conn.commit()
