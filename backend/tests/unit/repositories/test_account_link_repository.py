"""
Account Link Repository Tests
=============================
Tests for AccountLinkRepository methods.

Run: cd backend && ./venv/bin/python3 -m pytest tests/test_account_link_repository.py -v
"""

import sqlite3

import pytest

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


@pytest.fixture
def db_path(temp_db: str) -> str:
    """Schema-initialized database with account_links table."""
    _create_account_links_table(temp_db)
    return temp_db


def test_link_accounts(db_path: str) -> None:
    """Verify link_accounts creates relationship."""
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

    assert repo.relationship_exists(1, 2, "TRANSFER")


def test_unlink_accounts(db_path: str) -> None:
    """Verify unlink_accounts removes relationship."""
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
    assert repo.relationship_exists(1, 2)

    result = repo.unlink_accounts(1, 2)
    assert result is True

    assert not repo.relationship_exists(1, 2)


def test_duplicate_prevention(db_path: str) -> None:
    """Verify duplicate relationships are prevented."""
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

    result1 = repo.link_accounts(1, 2, "TRANSFER")
    assert result1 is True

    result2 = repo.link_accounts(1, 2, "TRANSFER")
    assert result2 is False


def test_get_linked_accounts(db_path: str) -> None:
    """Verify get_linked_accounts retrieves relationships."""
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

    repo.link_accounts(1, 2, "TRANSFER")
    repo.link_accounts(1, 3, "JOINT")

    links = repo.get_linked_accounts(1)
    assert len(links) == 2

    link_types = {link["relationship_type"] for link in links}
    assert "TRANSFER" in link_types
    assert "JOINT" in link_types


def test_relationship_exists_with_type(db_path: str) -> None:
    """Verify relationship_exists checks specific type."""
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

    assert repo.relationship_exists(1, 2, "TRANSFER")
    assert not repo.relationship_exists(1, 2, "JOINT")

    assert repo.relationship_exists(1, 2)


def test_all_relationship_types(db_path: str) -> None:
    """Verify all relationship types work (TRANSFER, JOINT, GUARANTOR)."""
    conn = sqlite3.connect(db_path)
    for i in range(1, 5):
        conn.execute(
            f"INSERT INTO accounts (id, name, bank, account_type, balance_paise) VALUES ({i}, 'Test{i}', 'Bank', 'savings', 100000)"
        )
    conn.commit()
    conn.close()

    repo = AccountLinkRepository(db_path=db_path)

    repo.link_accounts(1, 2, "TRANSFER")
    repo.link_accounts(1, 3, "JOINT")
    repo.link_accounts(1, 4, "GUARANTOR")

    links = repo.get_linked_accounts(1)
    link_types = {link["relationship_type"] for link in links}

    assert "TRANSFER" in link_types
    assert "JOINT" in link_types
    assert "GUARANTOR" in link_types


def test_unlink_nonexistent(db_path: str) -> None:
    """Verify unlink returns False for non-existent link."""
    repo = AccountLinkRepository(db_path=db_path)

    result = repo.unlink_accounts(999, 888)
    assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
