"""
Account Link Repository Tests
=============================
Tests for AccountLinkRepository methods.

Run: cd backend && ./venv/bin/python3 -m pytest tests/test_account_link_repository.py -v
"""

import os
import sqlite3
import tempfile

import pytest

from db import FinanceDB
from src.repositories.account_link_repository import AccountLinkRepository


def _create_account_links_table(db_path: str) -> None:
    """Create the account_links table for testing."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS account_links (
            primary_account_id INTEGER NOT NULL REFERENCES accounts(id),
            linked_account_id INTEGER NOT NULL REFERENCES accounts(id),
            relationship_type TEXT NOT NULL CHECK(
                relationship_type IN ('TRANSFER','JOINT','GUARANTOR')
            ),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(primary_account_id, linked_account_id, relationship_type)
        )
        """)
    conn.commit()
    conn.close()


# ============================================================
# Test: Account Link Operations
# ============================================================


def test_link_accounts():
    """Verify link_accounts creates relationship."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_links_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (2, 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        result = repo.link_accounts(1, 2, "TRANSFER")
        assert result is True

        # Verify link exists
        assert repo.relationship_exists(1, 2, "TRANSFER")

    finally:
        os.unlink(db_path)


def test_unlink_accounts():
    """Verify unlink_accounts removes relationship."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_links_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (2, 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        # Create link
        repo.link_accounts(1, 2, "TRANSFER")
        assert repo.relationship_exists(1, 2)

        # Remove link
        result = repo.unlink_accounts(1, 2)
        assert result is True

        assert not repo.relationship_exists(1, 2)

    finally:
        os.unlink(db_path)


def test_duplicate_prevention():
    """Verify duplicate relationships are prevented."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_links_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (2, 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        # First link should succeed
        result1 = repo.link_accounts(1, 2, "TRANSFER")
        assert result1 is True

        # Duplicate should fail
        result2 = repo.link_accounts(1, 2, "TRANSFER")
        assert result2 is False

    finally:
        os.unlink(db_path)


def test_get_linked_accounts():
    """Verify get_linked_accounts retrieves relationships."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_links_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (2, 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (3, 'Test3', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        # Create multiple links
        repo.link_accounts(1, 2, "TRANSFER")
        repo.link_accounts(1, 3, "JOINT")

        links = repo.get_linked_accounts(1)
        assert len(links) == 2

        link_types = {link["relationship_type"] for link in links}
        assert "TRANSFER" in link_types
        assert "JOINT" in link_types

    finally:
        os.unlink(db_path)


def test_relationship_exists_with_type():
    """Verify relationship_exists checks specific type."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_links_table(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (1, 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES (2, 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        repo.link_accounts(1, 2, "TRANSFER")

        # Check with type
        assert repo.relationship_exists(1, 2, "TRANSFER")
        assert not repo.relationship_exists(1, 2, "JOINT")

        # Check without type (any relationship)
        assert repo.relationship_exists(1, 2)

    finally:
        os.unlink(db_path)


def test_all_relationship_types():
    """Verify all relationship types work (TRANSFER, JOINT, GUARANTOR)."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_links_table(db_path)

        conn = sqlite3.connect(db_path)
        for i in range(1, 5):
            conn.execute(
                f"INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ({i}, 'Test{i}', 'Bank', 'savings', 100000)"
            )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        # Create links with different types using integer IDs
        repo.link_accounts(1, 2, "TRANSFER")
        repo.link_accounts(1, 3, "JOINT")
        repo.link_accounts(1, 4, "GUARANTOR")

        links = repo.get_linked_accounts(1)
        link_types = {link["relationship_type"] for link in links}

        assert "TRANSFER" in link_types
        assert "JOINT" in link_types
        assert "GUARANTOR" in link_types

    finally:
        os.unlink(db_path)


def test_unlink_nonexistent():
    """Verify unlink returns False for non-existent link."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_account_links_table(db_path)

        repo = AccountLinkRepository(db_path=db_path)

        result = repo.unlink_accounts(999, 888)
        assert result is False

    finally:
        os.unlink(db_path)


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
