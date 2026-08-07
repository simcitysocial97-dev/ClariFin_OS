"""
Institution Repository Tests
=============================
Tests for InstitutionRepository methods.

Run: cd backend && ./venv/bin/python3 -m pytest tests/test_institution_repository.py -v
"""

import json

import pytest

from src.repositories.institution_repository import InstitutionRepository


def _create_institutions_table(db_path: str) -> None:
    """Create the institutions table for testing."""
    conn = __import__("sqlite3").connect(db_path)
    conn.execute("""
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
    conn.commit()
    conn.close()


@pytest.fixture
def db_path(temp_db: str) -> str:
    """Schema-initialized database with institutions table."""
    _create_institutions_table(temp_db)
    return temp_db


def test_institution_create_and_get(db_path: str) -> None:
    """Verify institution creation and retrieval."""
    repo = InstitutionRepository(db_path=db_path)

    inst_id = repo.create(
        institution_id="HDFC",
        name="HDFC Bank",
        institution_type="BANK",
        interest_rate_bps=350,
        supported_features_json=json.dumps(["UPI", "IMPS", "NEFT"]),
    )

    assert inst_id == "HDFC"

    inst = repo.get("HDFC")
    assert inst is not None
    assert inst["name"] == "HDFC Bank"
    assert inst["type"] == "BANK"
    assert inst["interest_rate_bps"] == 350


def test_institution_list(db_path: str) -> None:
    """Verify listing institutions."""
    repo = InstitutionRepository(db_path=db_path)

    repo.create("HDFC", "HDFC Bank", "BANK", 350)
    repo.create("ICICI", "ICICI Bank", "BANK", 340)
    repo.create("PAYTM", "Paytm Payments Bank", "WALLET", 400)

    insts = repo.list()
    assert len(insts) == 3

    names = {inst["name"] for inst in insts}
    assert "HDFC Bank" in names
    assert "ICICI Bank" in names
    assert "Paytm Payments Bank" in names


def test_institution_update(db_path: str) -> None:
    """Verify institution update."""
    repo = InstitutionRepository(db_path=db_path)

    repo.create("HDFC", "HDFC Bank", "BANK", 350)

    inst = repo.update("HDFC", interest_rate_bps=360)
    assert inst is not None
    assert inst["interest_rate_bps"] == 360

    inst = repo.update("HDFC", name="HDFC Bank Ltd")
    assert inst is not None
    assert inst["name"] == "HDFC Bank Ltd"


def test_institution_delete(db_path: str) -> None:
    """Verify institution deletion."""
    repo = InstitutionRepository(db_path=db_path)

    repo.create("HDFC", "HDFC Bank", "BANK", 350)

    inst = repo.get("HDFC")
    assert inst is not None

    result = repo.delete("HDFC")
    assert result is True

    inst = repo.get("HDFC")
    assert inst is None


def test_duplicate_institution_handling(db_path: str) -> None:
    """Verify duplicate institutions are ignored gracefully."""
    repo = InstitutionRepository(db_path=db_path)

    repo.create("HDFC", "HDFC Bank", "BANK", 350)

    repo.create("HDFC", "HDFC Bank Updated", "BANK", 400)

    inst = repo.get("HDFC")
    assert inst is not None
    assert inst["interest_rate_bps"] == 350, "Original rate preserved"

    insts = repo.list()
    assert len(insts) == 1


def test_institution_types(db_path: str) -> None:
    """Verify all institution types work."""
    repo = InstitutionRepository(db_path=db_path)

    repo.create("HDFC", "HDFC Bank", "BANK", 350)
    repo.create("PAYTM", "Paytm", "WALLET", 400)
    repo.create("ZERODHA", "Zerodha", "BROKER", None)
    repo.create("OTHER", "Other", "OTHER", None)

    insts = repo.list()
    types = {inst["type"] for inst in insts}

    assert "BANK" in types
    assert "WALLET" in types
    assert "BROKER" in types
    assert "OTHER" in types


def test_get_nonexistent_institution(db_path: str) -> None:
    """Verify get returns None for non-existent institution."""
    repo = InstitutionRepository(db_path=db_path)

    inst = repo.get("NONEXISTENT")
    assert inst is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
