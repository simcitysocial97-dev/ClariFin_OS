"""
Migration 003: Credit Card Engine Schema
========================================
Creates credit_cards and credit_card_statements tables.

Run: cd backend && ./venv/bin/python3 scripts/migration_003_credit_card_engine.py
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "src" / "data" / "finance.db")


def run_migration(db_path: str | None = None) -> None:
    """Create credit card engine tables if they don't exist."""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # credit_cards table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_cards (
            id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(id),
            name TEXT NOT NULL,
            bank TEXT NOT NULL,
            card_last4 TEXT,
            credit_limit_paise INTEGER NOT NULL,
            annual_fee_paise INTEGER DEFAULT 0,
            interest_rate_bps INTEGER NOT NULL,
            billing_day INTEGER,
            due_day_offset INTEGER DEFAULT 21,
            is_active INTEGER NOT NULL DEFAULT 1,
            notes TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # credit_card_statements table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_card_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id TEXT NOT NULL REFERENCES credit_cards(id),
            statement_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            total_outstanding_paise INTEGER NOT NULL,
            minimum_due_paise INTEGER NOT NULL,
            payment_date TEXT,
            payment_amount_paise INTEGER,
            interest_charged_paise INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(card_id, statement_date)
        )
    """)

    conn.commit()
    conn.close()
    print("[MIGRATION 003] Credit card engine tables created successfully.")


if __name__ == "__main__":
    run_migration()
