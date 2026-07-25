"""
Test Suite: Migration 006 — Household columns backfill correctness
===================================================================
Verifies that the household migration correctly adds owner_id and
household_id columns and backfills defaults on existing rows.

Run: python -m pytest tests/test_migration_household.py -v
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scripts.migration_006_household import run_migration


@pytest.fixture
def db_with_existing_accounts():
    """Create a temp DB with accounts table (pre-migration schema)."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    # Create accounts table WITHOUT household columns (pre-migration)
    conn.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bank TEXT NOT NULL,
            account_type TEXT DEFAULT 'savings',
            account_number_last4 TEXT,
            balance_paise INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Insert test accounts
    test_accounts = [
        ("Savings A", "Bank1", "savings", "1234", 100000),
        ("Current B", "Bank2", "current", "5678", 200000),
        ("Credit C", "Bank3", "credit_card", "9012", -50000),
    ]
    conn.executemany(
        """
        INSERT INTO accounts (name, bank, account_type, account_number_last4, balance_paise)
        VALUES (?, ?, ?, ?, ?)
        """,
        test_accounts,
    )

    conn.commit()
    conn.close()

    yield db_path

    os.unlink(db_path)


# ============================================================
# Tests
# ============================================================


def test_household_columns_added(db_with_existing_accounts):
    """Verify that migration adds owner_id and household_id columns."""
    db_path = db_with_existing_accounts
    run_migration(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.execute("PRAGMA table_info(accounts)")
    columns = {row[1] for row in cur.fetchall()}

    assert "owner_id" in columns, "owner_id column should exist after migration"
    assert "household_id" in columns, "household_id column should exist after migration"

    conn.close()


def test_household_defaults_backfilled(db_with_existing_accounts):
    """Verify that existing rows get default owner_id and household_id."""
    db_path = db_with_existing_accounts
    run_migration(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT id, owner_id, household_id FROM accounts ORDER BY id"
    ).fetchall()

    assert len(rows) == 3, "Should have 3 accounts"

    for row in rows:
        assert row["owner_id"] == "self", (
            f"Account {row['id']}: expected owner_id='self', got '{row['owner_id']}'"
        )
        assert row["household_id"] == "primary", (
            f"Account {row['id']}: expected household_id='primary', got '{row['household_id']}'"
        )

    conn.close()


def test_migration_idempotent(db_with_existing_accounts):
    """Verify that running the migration twice causes no errors."""
    db_path = db_with_existing_accounts

    # Run migration twice
    run_migration(db_path)
    run_migration(db_path)  # Second run should be a no-op

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Values should still be correct
    row = conn.execute(
        "SELECT owner_id, household_id FROM accounts WHERE id = 1"
    ).fetchone()
    assert row["owner_id"] == "self"
    assert row["household_id"] == "primary"

    conn.close()


def test_new_accounts_get_defaults(db_with_existing_accounts):
    """Verify that new accounts inserted after migration get defaults."""
    db_path = db_with_existing_accounts
    run_migration(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO accounts (name, bank, account_type, account_number_last4, balance_paise)
        VALUES ('New Account', 'Bank4', 'savings', '0000', 50000)
        """)
    conn.commit()

    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT owner_id, household_id FROM accounts WHERE name = 'New Account'"
    ).fetchone()
    assert row["owner_id"] == "self", "New account should get default owner_id"
    assert row["household_id"] == "primary", (
        "New account should get default household_id"
    )

    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
