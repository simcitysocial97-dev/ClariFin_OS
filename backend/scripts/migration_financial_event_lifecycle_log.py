"""Migration to create financial_event_lifecycle_log table.

This table logs all lifecycle state transitions (open → partially_settled → settled)
for financial events, providing auditability for "why is this event's state what it is today".

Run: python scripts/migration_financial_event_lifecycle_log.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"


def migrate(db_path: str | None = None) -> None:
    """Create the financial_event_lifecycle_log table."""
    conn = sqlite3.connect(db_path or DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS financial_event_lifecycle_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL REFERENCES financial_events(id),
                previous_lifecycle_state TEXT,
                new_lifecycle_state TEXT NOT NULL,
                previous_outstanding_paise INTEGER,
                new_outstanding_paise INTEGER,
                caused_by_event_id INTEGER,
                actor TEXT NOT NULL DEFAULT 'system',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        print("Created financial_event_lifecycle_log table")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
