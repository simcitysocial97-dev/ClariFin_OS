"""
Account Link Repository Tests
=============================
Tests for AccountLinkRepository methods.

Run: cd backend && ./venv/bin/python3 -m pytest tests/test_account_link_repository.py -v
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB
from src.repositories.account_link_repository import AccountLinkRepository


def _create_account_links_table(db_path: str) -> None:
    """Create the account_links table for testing."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
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
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC002', 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        result = repo.link_accounts("ACC001", "ACC002", "TRANSFER")
        assert result is True

        # Verify link exists
        assert repo.relationship_exists("ACC001", "ACC002", "TRANSFER")

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
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC002', 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        # Create link
        repo.link_accounts("ACC001", "ACC002", "TRANSFER")
        assert repo.relationship_exists("ACC001", "ACC002")

        # Remove link
        result = repo.unlink_accounts("ACC001", "ACC002")
        assert result is True

        assert not repo.relationship_exists("ACC001", "ACC002")

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
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC002', 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        # First link should succeed
        result1 = repo.link_accounts("ACC001", "ACC002", "TRANSFER")
        assert result1 is True

        # Duplicate should fail
        result2 = repo.link_accounts("ACC001", "ACC002", "TRANSFER")
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
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC002', 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC003', 'Test3', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        # Create multiple links
        repo.link_accounts("ACC001", "ACC002", "TRANSFER")
        repo.link_accounts("ACC001", "ACC003", "JOINT")

        links = repo.get_linked_accounts("ACC001")
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
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC001', 'Test1', 'Bank', 'savings', 100000)"
        )
        conn.execute(
            "INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC002', 'Test2', 'Bank', 'savings', 100000)"
        )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        repo.link_accounts("ACC001", "ACC002", "TRANSFER")

        # Check with type
        assert repo.relationship_exists("ACC001", "ACC002", "TRANSFER")
        assert not repo.relationship_exists("ACC001", "ACC002", "JOINT")

        # Check without type (any relationship)
        assert repo.relationship_exists("ACC001", "ACC002")

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
                f"INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ('ACC{i:03d}', 'Test{i}', 'Bank', 'savings', 100000)"
            )
        conn.commit()
        conn.close()

        repo = AccountLinkRepository(db_path=db_path)

        # Create links with different types
        repo.link_accounts("ACC001", "ACC002", "TRANSFER")
        repo.link_accounts("ACC001", "ACC003", "JOINT")
        repo.link_accounts("ACC001", "ACC004", "GUARANTOR")

        links = repo.get_linked_accounts("ACC001")
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

        result = repo.unlink_accounts("NONEXISTENT1", "NONEXISTENT2")
        assert result is False

    finally:
        os.unlink(db_path)


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
