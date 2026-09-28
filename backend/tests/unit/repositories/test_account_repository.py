"""
Test Suite: AccountRepository — Core CRUD and Queries
======================================================
Tests for get_all_accounts, get_account_by_id, get_active_accounts, list_accounts,
deactivate_account, get_accounts_by_type on AccountRepository.

These exercise the previously-untested core CRUD methods per M46.6 baseline
(36% coverage in account_repository).
"""

from __future__ import annotations

import sqlite3

import pytest
from src.repositories.account_repository import AccountRepository


@pytest.fixture
def populated_accounts_db(temp_db: str) -> str:
    """Populate a temp DB with a small set of accounts across types/banks."""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bank TEXT NOT NULL,
            account_type TEXT DEFAULT 'savings',
            account_number_last4 TEXT,
            balance_paise INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            notes TEXT,
            owner_id TEXT DEFAULT 'self',
            household_id TEXT DEFAULT 'primary',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
        """)
    rows = [
        ("Savings A", "Bank1", "savings", "1234", 100000, 1),
        ("Current B", "Bank2", "current", "5678", 200000, 1),
        ("Credit C", "Bank3", "credit_card", "4321", -25000, 1),
        ("Inactive D", "Bank1", "savings", "9999", 50000, 0),
    ]
    for r in rows:
        conn.execute(
            "INSERT INTO accounts (name, bank, account_type, account_number_last4, "
            "balance_paise, is_active) VALUES (?, ?, ?, ?, ?, ?)",
            r,
        )
    conn.commit()
    conn.close()
    return temp_db


class TestAccountRepository:
    def test_get_all_accounts_excludes_inactive(
        self, populated_accounts_db: str
    ) -> None:
        """get_all_accounts must only return active accounts."""
        repo = AccountRepository(db_path=populated_accounts_db)
        result = repo.get_all_accounts()
        assert len(result) == 3  # 3 active, 1 inactive
        for account in result:
            assert account.get("is_active") == 1

    def test_get_all_accounts_returns_required_fields(
        self, populated_accounts_db: str
    ) -> None:
        """Each account must have id, name, bank, account_type, balance_paise."""
        repo = AccountRepository(db_path=populated_accounts_db)
        result = repo.get_all_accounts()
        required = {"id", "name", "bank", "account_type", "balance_paise"}
        for account in result:
            assert required.issubset(account.keys())

    def test_get_account_by_id_returns_correct_account(
        self, populated_accounts_db: str
    ) -> None:
        """get_account_by_id(1) must return Savings A."""
        repo = AccountRepository(db_path=populated_accounts_db)
        result = repo.get_account_by_id(1)
        assert result is not None
        assert result["name"] == "Savings A"
        assert result["bank"] == "Bank1"

    def test_get_account_by_id_nonexistent_returns_none(
        self, populated_accounts_db: str
    ) -> None:
        """get_account_by_id(99999) must return None (not raise)."""
        repo = AccountRepository(db_path=populated_accounts_db)
        result = repo.get_account_by_id(99999)
        assert result is None

    def test_get_accounts_by_type_filters_correctly(
        self, populated_accounts_db: str
    ) -> None:
        """get_accounts_by_type('savings') must include only savings accounts."""
        repo = AccountRepository(db_path=populated_accounts_db)
        result = repo.get_accounts_by_type("savings")
        # 2 savings rows in fixture: Savings A (active), Inactive D (inactive)
        # If the method filters on type only, we get 2; if on type+active, we get 1.
        # Either is acceptable; what MUST hold is all returned rows have type=savings.
        for account in result:
            assert account.get("account_type") == "savings"
        assert len(result) >= 1

    def test_deactivate_account_marks_inactive(
        self, populated_accounts_db: str
    ) -> None:
        """deactivate_account(1) must set is_active=0 and return True."""
        repo = AccountRepository(db_path=populated_accounts_db)
        ok = repo.deactivate_account(1)
        assert ok is True
        # Now the account must not appear in get_all_accounts
        result = repo.get_all_accounts()
        assert all(a["id"] != 1 for a in result)

    def test_deactivate_nonexistent_account_returns_false(
        self, populated_accounts_db: str
    ) -> None:
        """deactivate_account(99999) must return False (not raise)."""
        repo = AccountRepository(db_path=populated_accounts_db)
        result = repo.deactivate_account(99999)
        assert result is False

    def test_list_accounts_returns_all(self, populated_accounts_db: str) -> None:
        """list_accounts returns active accounts (excludes inactive by default)."""
        repo = AccountRepository(db_path=populated_accounts_db)
        result = repo.list_accounts()
        assert len(result) == 3  # 3 active, 1 inactive excluded

    def test_get_accounts_by_institution(self, populated_accounts_db: str) -> None:
        """get_accounts_by_institution('Bank1') must return only Bank1 accounts."""
        repo = AccountRepository(db_path=populated_accounts_db)
        result = repo.get_accounts_by_institution("Bank1")
        for account in result:
            assert account.get("bank") == "Bank1"
        assert len(result) >= 1
