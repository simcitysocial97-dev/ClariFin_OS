"""
Account Balance Repository Tests
=================================
Tests for AccountBalanceRepository methods.

Run: cd backend && ./venv/bin/python3 -m pytest tests/test_account_balance_repository.py -v
"""

import sqlite3

import pytest

from src.repositories.account_balance_repository import AccountBalanceRepository


def _create_account_balance_history_table(db_path: str) -> None:
    """Create the account_balance_history table for testing."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS account_balance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(id),
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


@pytest.fixture
def db_path(temp_db: str) -> str:
    """Schema-initialized database with account_balance_history table."""
    _create_account_balance_history_table(temp_db)
    return temp_db


def test_insert_balance_snapshot(db_path: str) -> None:
    """Verify insert_balance_snapshot creates record correctly."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO accounts (id, name, bank, account_type, balance_paise)
        VALUES (1, 'Test Account', 'TestBank', 'savings', 100000)
        """)
    conn.commit()
    conn.close()

    repo = AccountBalanceRepository(db_path=db_path)

    snapshot_id = repo.insert_balance_snapshot(
        account_id=1,
        balance_paise=150000,
        date_iso="2026-07-01",
        source="actual",
    )

    assert snapshot_id > 0, "Should return valid snapshot ID"

    snapshot = repo.get_balance_on_date(1, "2026-07-01")
    assert snapshot is not None
    assert snapshot["balance_paise"] == 150000
    assert snapshot["source"] == "actual"


def test_get_balance_history(db_path: str) -> None:
    """Verify get_balance_history returns ordered history."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test', 'Bank', 'savings', 100000)"
    )
    conn.commit()
    conn.close()

    repo = AccountBalanceRepository(db_path=db_path)

    repo.insert_balance_snapshot(1, 100000, "2026-01-01", "actual")
    repo.insert_balance_snapshot(1, 110000, "2026-02-01", "actual")
    repo.insert_balance_snapshot(1, 120000, "2026-03-01", "actual")

    history = repo.get_balance_history(1)
    assert len(history) == 3, "Should have 3 snapshots"

    assert history[0]["date_iso"] == "2026-03-01"
    assert history[1]["date_iso"] == "2026-02-01"
    assert history[2]["date_iso"] == "2026-01-01"


def test_get_latest_balance(db_path: str) -> None:
    """Verify get_latest_balance returns most recent snapshot."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test', 'Bank', 'savings', 100000)"
    )
    conn.commit()
    conn.close()

    repo = AccountBalanceRepository(db_path=db_path)

    repo.insert_balance_snapshot(1, 100000, "2026-01-01")
    repo.insert_balance_snapshot(1, 150000, "2026-02-01")
    repo.insert_balance_snapshot(1, 200000, "2026-03-01")

    latest = repo.get_latest_balance(1)
    assert latest is not None
    assert latest["balance_paise"] == 200000
    assert latest["date_iso"] == "2026-03-01"


def test_get_balance_on_date(db_path: str) -> None:
    """Verify get_balance_on_date returns exact date lookup."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test', 'Bank', 'savings', 100000)"
    )
    conn.commit()
    conn.close()

    repo = AccountBalanceRepository(db_path=db_path)

    repo.insert_balance_snapshot(1, 100000, "2026-01-15")
    repo.insert_balance_snapshot(1, 150000, "2026-02-15")

    balance = repo.get_balance_on_date(1, "2026-01-15")
    assert balance is not None
    assert balance["balance_paise"] == 100000

    balance = repo.get_balance_on_date(1, "2026-03-15")
    assert balance is None


def test_duplicate_snapshot_protection(db_path: str) -> None:
    """Verify duplicate date snapshots are ignored."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test', 'Bank', 'savings', 100000)"
    )
    conn.commit()
    conn.close()

    repo = AccountBalanceRepository(db_path=db_path)

    id1 = repo.insert_balance_snapshot(1, 100000, "2026-01-01")
    assert id1 > 0

    id2 = repo.insert_balance_snapshot(1, 150000, "2026-01-01")
    assert id2 == 0, "Duplicate should return 0"

    history = repo.get_balance_history(1)
    assert len(history) == 1
    assert history[0]["balance_paise"] == 100000, "Original balance preserved"


def test_delete_snapshot(db_path: str) -> None:
    """Verify delete_snapshot removes record."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test', 'Bank', 'savings', 100000)"
    )
    conn.commit()
    conn.close()

    repo = AccountBalanceRepository(db_path=db_path)

    snapshot_id = repo.insert_balance_snapshot(1, 100000, "2026-01-01")
    assert repo.get_balance_on_date(1, "2026-01-01") is not None

    result = repo.delete_snapshot(snapshot_id)
    assert result is True

    assert repo.get_balance_on_date(1, "2026-01-01") is None


def test_different_sources(db_path: str) -> None:
    """Verify all source types work (actual, projected, adjusted)."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test', 'Bank', 'savings', 100000)"
    )
    conn.commit()
    conn.close()

    repo = AccountBalanceRepository(db_path=db_path)

    repo.insert_balance_snapshot(1, 100000, "2026-01-01", "actual")
    repo.insert_balance_snapshot(1, 110000, "2026-02-01", "projected")
    repo.insert_balance_snapshot(1, 120000, "2026-03-01", "adjusted")

    history = repo.get_balance_history(1)
    assert len(history) == 3

    sources = {h["source"] for h in history}
    assert "actual" in sources
    assert "projected" in sources
    assert "adjusted" in sources


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
