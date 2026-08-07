"""
Minimal Audit Tests
====================

Phase 2C: Essential audit tests for ledger integrity.

Tests:
1. Ledger integrity passes on clean DB
2. Hash verification works correctly
3. Update attempt on transactions raises exception (trigger working)
4. Re-running audit returns same result

Run: python -m pytest tests/test_audit_minimal.py -v
"""

import hashlib
import os
import sqlite3
import tempfile

import pytest

from repositories.statement_repository import StatementRepository
from repositories.transaction_repository import TransactionRepository
from src.engines.ledger_audit_engine import (
    run_full_audit,
    validate_ledger_integrity,
    verify_hash_signatures,
)


@pytest.fixture
def populated_db(temp_db: str) -> str:
    """Provide a database populated with test transactions."""
    stmt_repo = StatementRepository(temp_db)
    txn_repo = TransactionRepository(temp_db)

    stmt_id = stmt_repo.insert_statement(
        "TestBank", "test.pdf", "01/01/2025", "31/01/2025"
    )

    txn_repo.insert_transactions(
        stmt_id,
        [
            {
                "date": "01/01/2025",
                "description": "Test debit",
                "amount_paise": 10000,
                "type": "debit",
            },
            {
                "date": "02/01/2025",
                "description": "Test credit",
                "amount_paise": 5000,
                "type": "credit",
            },
        ],
    )

    return temp_db


def test_integrity_passes_on_clean_db(populated_db):
    """Test that ledger integrity passes on a clean database."""
    db_path = populated_db

    result = validate_ledger_integrity(db_path)

    assert result["status"] == "PASS", f"Expected PASS, got {result}"
    assert result["violation_count"] == 0
    assert len(result["violations"]) == 0


def test_hash_verification_passes_on_clean_db(populated_db):
    """Test that hash verification passes on a clean database."""
    db_path = populated_db

    result = verify_hash_signatures(db_path)

    assert result["status"] == "PASS", f"Expected PASS, got {result}"
    assert result["tampered_count"] == 0
    assert len(result["tampered_transactions"]) == 0


def test_full_audit_passes_on_clean_db(populated_db):
    """Test that full audit passes on a clean database."""
    db_path = populated_db

    result = run_full_audit(db_path)

    assert result["overall_status"] == "PASS"
    assert result["ledger_integrity"]["status"] == "PASS"
    assert result["hash_verification"]["status"] == "PASS"


def test_update_prevented_by_trigger(populated_db):
    """Test that UPDATE on transactions is prevented by trigger."""
    db_path = populated_db

    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT id FROM transactions LIMIT 1")
    row = cur.fetchone()
    txn_id = row[0]

    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        conn.execute(
            "UPDATE transactions SET amount_paise = 99999 WHERE id = ?", (txn_id,)
        )
        conn.commit()

    assert "immutable" in str(exc_info.value).lower()
    conn.close()


def test_delete_prevented_by_trigger(populated_db):
    """Test that DELETE on transactions is prevented by trigger."""
    db_path = populated_db

    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT id FROM transactions LIMIT 1")
    row = cur.fetchone()
    txn_id = row[0]

    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
        conn.commit()

    assert "immutable" in str(exc_info.value).lower()
    conn.close()


def test_tampered_hash_detected_via_recompute(populated_db):
    """Test that hash verification can detect tampering.

    Since triggers prevent UPDATE, we test by:
    1. Creating a new database without triggers
    2. Inserting data
    3. Manually modifying hash
    4. Verifying detection
    """
    import tempfile

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        conn = sqlite3.connect(db_path)

        conn.execute("""
            CREATE TABLE statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank TEXT NOT NULL,
                file_name TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                statement_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                date_iso TEXT,
                description TEXT,
                amount REAL NOT NULL,
                type TEXT,
                category TEXT,
                debit INTEGER DEFAULT 0,
                credit INTEGER DEFAULT 0,
                account_id TEXT,
                hash_signature TEXT
            )
        """)

        hash_input = "TestBank|2025-01-01|Test debit|10000|0"
        valid_hash = hashlib.sha256(hash_input.encode()).hexdigest().lower()

        conn.execute(
            """
            INSERT INTO transactions (statement_id, date, date_iso, description, amount, type,
                                      debit, credit, account_id, hash_signature)
            VALUES (1, '01/01/2025', '2025-01-01', 'Test debit', 100.0, 'debit',
                    10000, 0, 'TestBank', ?)
        """,
            (valid_hash,),
        )

        conn.commit()

        result_before = verify_hash_signatures(db_path)
        assert result_before["status"] == "PASS"

        conn.execute("UPDATE transactions SET hash_signature = 'tampered_hash'")
        conn.commit()
        conn.close()

        result_after = verify_hash_signatures(db_path)

        assert result_after["status"] == "FAIL"
        assert result_after["tampered_count"] >= 1
    finally:
        os.unlink(db_path)


def test_audit_deterministic(populated_db):
    """Test that running audit multiple times returns same result."""
    db_path = populated_db

    results = [run_full_audit(db_path) for _ in range(3)]

    for i in range(1, len(results)):
        assert results[i]["overall_status"] == results[0]["overall_status"]
        assert (
            results[i]["ledger_integrity"]["violation_count"]
            == results[0]["ledger_integrity"]["violation_count"]
        )
        assert (
            results[i]["hash_verification"]["tampered_count"]
            == results[0]["hash_verification"]["tampered_count"]
        )


def test_audit_idempotent_on_clean_db(populated_db):
    """Test that audit consistently returns PASS on clean database."""
    db_path = populated_db

    results = [run_full_audit(db_path) for _ in range(3)]

    for result in results:
        assert result["overall_status"] == "PASS"
        assert result["ledger_integrity"]["status"] == "PASS"
        assert result["hash_verification"]["status"] == "PASS"


def test_integrity_detects_null_account_id():
    """Test that integrity check detects NULL account_id."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        conn = sqlite3.connect(db_path)

        conn.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                date_iso TEXT,
                description TEXT,
                amount REAL,
                type TEXT,
                debit INTEGER DEFAULT 0,
                credit INTEGER DEFAULT 0,
                account_id TEXT,
                hash_signature TEXT
            )
        """)

        conn.execute("""
            INSERT INTO transactions (date_iso, description, amount, debit, credit, account_id, hash_signature)
            VALUES ('2025-01-01', 'Test', 100, 10000, 0, NULL, 'somehash')
        """)
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(db_path)

        assert result["status"] == "FAIL"
        assert any(v["type"] == "NULL_ACCOUNT_ID" for v in result["violations"])
    finally:
        os.unlink(db_path)


def test_integrity_detects_duplicate_hash():
    """Test that integrity check detects duplicate hash_signature."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        conn = sqlite3.connect(db_path)

        conn.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                date_iso TEXT,
                description TEXT,
                amount REAL,
                type TEXT,
                debit INTEGER DEFAULT 0,
                credit INTEGER DEFAULT 0,
                account_id TEXT,
                hash_signature TEXT
            )
        """)

        conn.execute("""
            INSERT INTO transactions (date_iso, description, amount, debit, credit, account_id, hash_signature)
            VALUES ('2025-01-01', 'Test1', 100, 10000, 0, 1, 'duplicate_hash')
        """)
        conn.execute("""
            INSERT INTO transactions (date_iso, description, amount, debit, credit, account_id, hash_signature)
            VALUES ('2025-01-02', 'Test2', 200, 20000, 0, 1, 'duplicate_hash')
        """)
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(db_path)

        assert result["status"] == "FAIL"
        assert any(v["type"] == "DUPLICATE_HASH" for v in result["violations"])
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
