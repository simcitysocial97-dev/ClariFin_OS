"""
Account Balance Repository Tests
=================================
Tests for AccountBalanceRepository methods.

Run: cd backend && ./venv/bin/python3 -m pytest tests/test_account_balance_repository.py -v
"""

import os
import sqlite3
import tempfile

import pytest

from db import FinanceDB
from src.repositories.account_balance_repository import AccountBalanceRepository


def _create_account_balance_history_table(db_path: str) -> None:
    """Create the account_balance_history table for testing."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS account_balance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL REFERENCES accounts(id),
            balance_paise INTEGER NOT NULL,
            date_iso TEXT NOT NULL,
            source TEXT NOT NULL CHECK(source IN ('actual','projected','adjusted')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(account_id, date_iso)
        )
        """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_abh_account_id ON account_balance_history(account_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_abh_account_date ON account_balance_history(account_id, date_iso)"
    )
    conn.commit()
    conn.close()


# ============================================================
# Test: Balance Snapshot Operations
# ============================================================


def test_insert_balance_snapshot():
    """Verify insert_balance_snapshot creates record correctly."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_balance_history_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO accounts (id, name, bank, account_type, balance_paise)
            VALUES ('ACC001', 'Test Account', 'TestBank', 'savings', 100000)
            """)
        conn.commit()
        conn.close()

        repo = AccountBalanceRepository(db_path=db_path)

        # Insert snapshot
        snapshot_id = repo.insert_balance_snapshot(
            account_id="ACC001",
            balance_paise=150000,
            date_iso="2026-07-01",
            source="actual",
        )

        assert snapshot_id > 0, "Should return valid snapshot ID"

        # Verify data
        snapshot = repo.get_balance_on_date("ACC001", "2026-07-01")
        assert snapshot is not None
        assert snapshot["balance_paise"] == 150000
        assert snapshot["source"] == "actual"

    finally:
        os.unlink(db_path)


def test_get_balance_history():
    """Verify get_balance_history returns ordered history."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_balance_history_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountBalanceRepository(db_path=db_path)

        # Insert multiple snapshots
        repo.insert_balance_snapshot("ACC001", 100000, "2026-01-01", "actual")
        repo.insert_balance_snapshot("ACC001", 110000, "2026-02-01", "actual")
        repo.insert_balance_snapshot("ACC001", 120000, "2026-03-01", "actual")

        history = repo.get_balance_history("ACC001")
        assert len(history) == 3, "Should have 3 snapshots"

        # Most recent first
        assert history[0]["date_iso"] == "2026-03-01"
        assert history[1]["date_iso"] == "2026-02-01"
        assert history[2]["date_iso"] == "2026-01-01"

    finally:
        os.unlink(db_path)


def test_get_latest_balance():
    """Verify get_latest_balance returns most recent snapshot."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_balance_history_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountBalanceRepository(db_path=db_path)

        # Insert snapshots
        repo.insert_balance_snapshot("ACC001", 100000, "2026-01-01")
        repo.insert_balance_snapshot("ACC001", 150000, "2026-02-01")
        repo.insert_balance_snapshot("ACC001", 200000, "2026-03-01")

        latest = repo.get_latest_balance("ACC001")
        assert latest is not None
        assert latest["balance_paise"] == 200000
        assert latest["date_iso"] == "2026-03-01"

    finally:
        os.unlink(db_path)


def test_get_balance_on_date():
    """Verify get_balance_on_date returns exact date lookup."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_balance_history_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountBalanceRepository(db_path=db_path)

        # Insert snapshots for different dates
        repo.insert_balance_snapshot("ACC001", 100000, "2026-01-15")
        repo.insert_balance_snapshot("ACC001", 150000, "2026-02-15")

        # Get specific date
        balance = repo.get_balance_on_date("ACC001", "2026-01-15")
        assert balance is not None
        assert balance["balance_paise"] == 100000

        # Non-existent date
        balance = repo.get_balance_on_date("ACC001", "2026-03-15")
        assert balance is None

    finally:
        os.unlink(db_path)


def test_duplicate_snapshot_protection():
    """Verify duplicate date snapshots are ignored."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_balance_history_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountBalanceRepository(db_path=db_path)

        # Insert first snapshot
        id1 = repo.insert_balance_snapshot("ACC001", 100000, "2026-01-01")
        assert id1 > 0

        # Try duplicate - should return 0
        id2 = repo.insert_balance_snapshot("ACC001", 150000, "2026-01-01")
        assert id2 == 0, "Duplicate should return 0"

        # Verify original data preserved
        history = repo.get_balance_history("ACC001")
        assert len(history) == 1
        assert history[0]["balance_paise"] == 100000, "Original balance preserved"

    finally:
        os.unlink(db_path)


def test_delete_snapshot():
    """Verify delete_snapshot removes record."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_balance_history_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountBalanceRepository(db_path=db_path)

        snapshot_id = repo.insert_balance_snapshot("ACC001", 100000, "2026-01-01")
        assert repo.get_balance_on_date("ACC001", "2026-01-01") is not None

        result = repo.delete_snapshot(snapshot_id)
        assert result is True

        assert repo.get_balance_on_date("ACC001", "2026-01-01") is None

    finally:
        os.unlink(db_path)


def test_different_sources():
    """Verify all source types work (actual, projected, adjusted)."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_balance_history_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountBalanceRepository(db_path=db_path)

        # Insert with different sources
        repo.insert_balance_snapshot("ACC001", 100000, "2026-01-01", "actual")
        repo.insert_balance_snapshot("ACC001", 110000, "2026-02-01", "projected")
        repo.insert_balance_snapshot("ACC001", 120000, "2026-03-01", "adjusted")

        history = repo.get_balance_history("ACC001")
        assert len(history) == 3

        sources = {h["source"] for h in history}
        assert "actual" in sources
        assert "projected" in sources
        assert "adjusted" in sources

    finally:
        os.unlink(db_path)


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
