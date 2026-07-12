"""
Migration 004: Account Engine Persistence Schema
==================================================
Creates account_balance_history, institutions, and account_links tables.

Run: cd backend && ./venv/bin/python3 scripts/migration_004_account_engine.py
"""

import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "src" / "data" / "finance.db")


def run_migration(db_path: str | None = None) -> None:
    """Create account engine persistence tables if they don't exist."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Enable foreign keys for referential integrity
    cursor.execute("PRAGMA foreign_keys=ON")

    # ============================================================
    # account_balance_history - Balance snapshot history
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_balance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL REFERENCES accounts(id),
            balance_paise INTEGER NOT NULL,
            date_iso TEXT NOT NULL,
            source TEXT NOT NULL CHECK(
                source IN ('actual','projected','adjusted')
            ),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(account_id, date_iso)
        )
    """)

    # Indexes for account_balance_history
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_abh_account_id
        ON account_balance_history(account_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_abh_account_date
        ON account_balance_history(account_id, date_iso)
    """)

    # ============================================================
    # institutions - Reference table for bank/institution metadata
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS institutions (
            institution_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('BANK','WALLET','BROKER','OTHER')),
            interest_rate_bps INTEGER,
            supported_features_json TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ============================================================
    # account_links - Relationship table between accounts
    # ============================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_links (
            primary_account_id TEXT NOT NULL REFERENCES accounts(id),
            linked_account_id TEXT NOT NULL REFERENCES accounts(id),
            relationship_type TEXT NOT NULL CHECK(
                relationship_type IN ('TRANSFER','JOINT','GUARANTOR')
            ),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(primary_account_id, linked_account_id, relationship_type)
        )
    """)

    conn.commit()
    conn.close()
    print("[MIGRATION 004] Account engine persistence tables created successfully.")


if __name__ == "__main__":
    run_migration()
