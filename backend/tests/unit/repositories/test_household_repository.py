"""
Test Suite: Account Repository — Household Methods
====================================================
Tests for get_household_accounts, get_accounts_by_owner, and is_same_household
on AccountRepository.

Run: python -m pytest tests/test_household_repository.py -v
"""

import sqlite3

import pytest

from repositories.account_repository import AccountRepository


@pytest.fixture
def multi_owner_db(temp_db: str) -> str:
    """Create a temp DB with accounts spanning multiple owners/households."""
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

    test_accounts = [
        ("Savings A", "Bank1", "savings", "1234", 100000, 1, "self", "primary"),
        ("Current B", "Bank2", "current", "5678", 200000, 1, "self", "primary"),
        ("Spouse Savings", "Bank1", "savings", "4321", 150000, 1, "spouse", "primary"),
        (
            "Spouse Credit",
            "Bank3",
            "credit_card",
            "8765",
            -25000,
            1,
            "spouse",
            "primary",
        ),
        ("Vacation Account", "Bank4", "savings", "9999", 50000, 1, "self", "vacation"),
        ("Closed Account", "Bank5", "savings", "0000", 0, 0, "self", "primary"),
    ]
    conn.executemany(
        """
        INSERT INTO accounts
            (name, bank, account_type, account_number_last4, balance_paise,
             is_active, owner_id, household_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        test_accounts,
    )

    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def repo(multi_owner_db: str):
    """Create an AccountRepository connected to the temp DB."""
    return AccountRepository(multi_owner_db)


def test_get_household_accounts_primary(repo):
    """Test getting all active accounts in the primary household."""
    accounts = repo.get_household_accounts("primary")

    names = {a["name"] for a in accounts}
    assert "Savings A" in names
    assert "Current B" in names
    assert "Spouse Savings" in names
    assert "Spouse Credit" in names
    assert "Vacation Account" not in names, "Vacation is not in primary household"
    assert "Closed Account" not in names, "Closed account is inactive"

    assert len(accounts) == 4


def test_get_household_accounts_vacation(repo):
    """Test getting all active accounts in the vacation household."""
    accounts = repo.get_household_accounts("vacation")
    assert len(accounts) == 1
    assert accounts[0]["name"] == "Vacation Account"


def test_get_household_accounts_nonexistent(repo):
    """Test getting accounts for a household that doesn't exist."""
    accounts = repo.get_household_accounts("nonexistent")
    assert accounts == [], "Should return empty list for non-existent household"


def test_get_accounts_by_owner_self_primary(repo):
    """Test getting self-owned accounts in the primary household."""
    accounts = repo.get_accounts_by_owner("self", "primary")

    names = {a["name"] for a in accounts}
    assert "Savings A" in names
    assert "Current B" in names
    assert "Spouse Savings" not in names, "Spouse accounts should not appear"
    assert len(accounts) == 2


def test_get_accounts_by_owner_spouse_primary(repo):
    """Test getting spouse-owned accounts in the primary household."""
    accounts = repo.get_accounts_by_owner("spouse", "primary")

    names = {a["name"] for a in accounts}
    assert "Spouse Savings" in names
    assert "Spouse Credit" in names
    assert "Savings A" not in names, "Self accounts should not appear"
    assert len(accounts) == 2


def test_get_accounts_by_owner_default_household(repo):
    """Test get_accounts_by_owner uses 'primary' as default household."""
    accounts = repo.get_accounts_by_owner("self")
    names = {a["name"] for a in accounts}
    assert "Savings A" in names
    assert "Current B" in names
    assert "Vacation Account" not in names, "Default household should be 'primary'"
    assert len(accounts) == 2


def test_get_accounts_by_owner_vacation(repo):
    """Test getting self-owned accounts in the vacation household."""
    accounts = repo.get_accounts_by_owner("self", "vacation")
    assert len(accounts) == 1
    assert accounts[0]["name"] == "Vacation Account"


def test_accounts_by_owner_no_match(repo):
    """Test getting accounts for an owner with no accounts."""
    accounts = repo.get_accounts_by_owner("nonexistent_owner")
    assert accounts == [], "Should return empty list for non-existent owner"


def test_is_same_household_true(repo):
    """Test that two accounts in the same household return True."""
    assert repo.is_same_household(1, 2) is True


def test_is_same_household_false(repo):
    """Test that two accounts in different households return False."""
    assert repo.is_same_household(1, 5) is False


def test_is_same_household_nonexistent(repo):
    """Test that is_same_household returns False if either account doesn't exist."""
    assert repo.is_same_household(1, 99999) is False
    assert repo.is_same_household(99999, 1) is False
    assert repo.is_same_household(99999, 88888) is False


def test_is_same_household_spouse(repo):
    """Test that spouse and self accounts in same household return True."""
    assert repo.is_same_household(1, 3) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
