"""
Institution Repository Tests
=============================
Tests for InstitutionRepository methods.

Run: cd backend && ./venv/bin/python3 -m pytest tests/test_institution_repository.py -v
"""

import json
import os
import tempfile

import pytest


from db import FinanceDB
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


# ============================================================
# Test: Institution CRUD Operations
# ============================================================


def test_institution_create_and_get():
    """Verify institution creation and retrieval."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_institutions_table(db_path)
        repo = InstitutionRepository(db_path=db_path)

        # Create institution
        inst_id = repo.create(
            institution_id="HDFC",
            name="HDFC Bank",
            institution_type="BANK",
            interest_rate_bps=350,  # 3.5%
            supported_features_json=json.dumps(["UPI", "IMPS", "NEFT"]),
        )

        assert inst_id == "HDFC"

        # Get institution
        inst = repo.get("HDFC")
        assert inst is not None
        assert inst["name"] == "HDFC Bank"
        assert inst["type"] == "BANK"
        assert inst["interest_rate_bps"] == 350

    finally:
        os.unlink(db_path)


def test_institution_list():
    """Verify listing institutions."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_institutions_table(db_path)
        repo = InstitutionRepository(db_path=db_path)

        # Create multiple institutions
        repo.create("HDFC", "HDFC Bank", "BANK", 350)
        repo.create("ICICI", "ICICI Bank", "BANK", 340)
        repo.create("PAYTM", "Paytm Payments Bank", "WALLET", 400)

        insts = repo.list()
        assert len(insts) == 3

        names = {inst["name"] for inst in insts}
        assert "HDFC Bank" in names
        assert "ICICI Bank" in names
        assert "Paytm Payments Bank" in names

    finally:
        os.unlink(db_path)


def test_institution_update():
    """Verify institution update."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_institutions_table(db_path)
        repo = InstitutionRepository(db_path=db_path)

        repo.create("HDFC", "HDFC Bank", "BANK", 350)

        # Update interest rate
        inst = repo.update("HDFC", interest_rate_bps=360)
        assert inst is not None
        assert inst["interest_rate_bps"] == 360

        # Update name
        inst = repo.update("HDFC", name="HDFC Bank Ltd")
        assert inst is not None
        assert inst["name"] == "HDFC Bank Ltd"

    finally:
        os.unlink(db_path)


def test_institution_delete():
    """Verify institution deletion."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_institutions_table(db_path)
        repo = InstitutionRepository(db_path=db_path)

        repo.create("HDFC", "HDFC Bank", "BANK", 350)

        inst = repo.get("HDFC")
        assert inst is not None

        result = repo.delete("HDFC")
        assert result is True

        inst = repo.get("HDFC")
        assert inst is None

    finally:
        os.unlink(db_path)


def test_duplicate_institution_handling():
    """Verify duplicate institutions are ignored gracefully."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_institutions_table(db_path)
        repo = InstitutionRepository(db_path=db_path)

        # Create institution
        repo.create("HDFC", "HDFC Bank", "BANK", 350)

        # Try to create duplicate - should be ignored
        repo.create("HDFC", "HDFC Bank Updated", "BANK", 400)

        # Verify original preserved
        inst = repo.get("HDFC")
        assert inst is not None
        assert inst["interest_rate_bps"] == 350, "Original rate preserved"

        # Verify only one record
        insts = repo.list()
        assert len(insts) == 1

    finally:
        os.unlink(db_path)


def test_institution_types():
    """Verify all institution types work."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_institutions_table(db_path)
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

    finally:
        os.unlink(db_path)


def test_get_nonexistent_institution():
    """Verify get returns None for non-existent institution."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        _create_institutions_table(db_path)
        repo = InstitutionRepository(db_path=db_path)

        inst = repo.get("NONEXISTENT")
        assert inst is None

    finally:
        os.unlink(db_path)


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])