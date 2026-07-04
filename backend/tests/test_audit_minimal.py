"""
Minimal Audit Tests
===================

Phase 2C: Essential audit tests for ledger integrity.

Tests:
1. Ledger integrity passes on clean DB
2. Hash verification works correctly
3. Update attempt on transactions raises exception (trigger working)
4. Re-running audit returns same result

Run: python -m pytest tests/test_audit_minimal.py -v
"""

import os
import sys
import sqlite3
import tempfile
import hashlib
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB
from engines.ledger_audit_engine import (
    validate_ledger_integrity,
    verify_hash_signatures,
    run_full_audit,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    db = FinanceDB(db_path=db_path)
    
    yield db, db_path
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def populated_db(temp_db):
    """Populate database with test transactions."""
    db, db_path = temp_db
    
    # Insert a statement
    stmt_id = db.insert_statement("TestBank", "test.pdf", "01/01/2025", "31/01/2025")
    
    # Insert transactions
    db.insert_transactions(stmt_id, [
        {"date": "01/01/2025", "description": "Test debit", "amount": 100.0, "type": "debit"},
        {"date": "02/01/2025", "description": "Test credit", "amount": 50.0, "type": "credit"},
    ])
    
    return db, db_path


# ============================================================
# Test 1: Ledger integrity passes on clean DB
# ============================================================

def test_integrity_passes_on_clean_db(populated_db):
    """Test that ledger integrity passes on a clean database."""
    db, db_path = populated_db
    
    result = validate_ledger_integrity(db)
    
    assert result["status"] == "PASS", f"Expected PASS, got {result}"
    assert result["violation_count"] == 0
    assert len(result["violations"]) == 0


def test_hash_verification_passes_on_clean_db(populated_db):
    """Test that hash verification passes on a clean database."""
    db, db_path = populated_db
    
    result = verify_hash_signatures(db)
    
    assert result["status"] == "PASS", f"Expected PASS, got {result}"
    assert result["tampered_count"] == 0
    assert len(result["tampered_transactions"]) == 0


def test_full_audit_passes_on_clean_db(populated_db):
    """Test that full audit passes on a clean database."""
    db, db_path = populated_db
    
    result = run_full_audit(db)
    
    assert result["overall_status"] == "PASS"
    assert result["ledger_integrity"]["status"] == "PASS"
    assert result["hash_verification"]["status"] == "PASS"


# ============================================================
# Test 2: Immutability triggers work correctly
# ============================================================

def test_update_prevented_by_trigger(populated_db):
    """Test that UPDATE on transactions is prevented by trigger.
    
    This confirms the immutability trigger is working correctly.
    """
    db, db_path = populated_db
    
    # Get a transaction
    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT id FROM transactions LIMIT 1")
    row = cur.fetchone()
    txn_id = row[0]
    
    # Attempt to update - should raise exception
    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        conn.execute(
            "UPDATE transactions SET amount = 999.99 WHERE id = ?",
            (txn_id,)
        )
        conn.commit()
    
    assert "immutable" in str(exc_info.value).lower()
    conn.close()


def test_delete_prevented_by_trigger(populated_db):
    """Test that DELETE on transactions is prevented by trigger.
    
    This confirms the immutability trigger is working correctly.
    """
    db, db_path = populated_db
    
    # Get a transaction
    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT id FROM transactions LIMIT 1")
    row = cur.fetchone()
    txn_id = row[0]
    
    # Attempt to delete - should raise exception
    with pytest.raises(sqlite3.IntegrityError) as exc_info:
        conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
        conn.commit()
    
    assert "immutable" in str(exc_info.value).lower()
    conn.close()


# ============================================================
# Test 3: Tampering detection (via direct DB manipulation without triggers)
# ============================================================

def test_tampered_hash_detected_via_recompute():
    """Test that hash verification can detect tampering.
    
    Since triggers prevent UPDATE, we test by:
    1. Creating a new database with FinanceDB
    2. Inserting data using FinanceDB methods
    3. Temporarily disabling the immutability trigger
    4. Manually modifying hash
    5. Verifying detection
    """
    # Create an in-memory database using FinanceDB
    db = FinanceDB(':memory:')
    
    # Insert a statement
    stmt_id = db.insert_statement("TestBank", "test.pdf", "01/01/2025", "31/01/2025")
    
    # Insert transactions - this will compute proper hashes
    db.insert_transactions(stmt_id, [
        {"date": "01/01/2025", "description": "Test debit", "amount": 100.0, "type": "debit"},
    ])
    
    # Verify hash passes before tampering
    result_before = verify_hash_signatures(db)
    assert result_before["status"] == "PASS"
    
    # Now tamper with the hash by temporarily disabling the trigger
    # We need to use the raw connection to drop and recreate the trigger
    with db.transaction() as conn:
        # Drop the immutability trigger temporarily
        conn.execute("DROP TRIGGER IF EXISTS prevent_transaction_update")
        
        # Tamper with the hash
        conn.execute("UPDATE transactions SET hash_signature = 'tampered_hash'")
        
        # Recreate the trigger
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_transaction_update
            BEFORE UPDATE ON transactions
            BEGIN
                SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.');
            END
        """)
    
    # Verify detection
    result_after = verify_hash_signatures(db)
    
    assert result_after["status"] == "FAIL"
    assert result_after["tampered_count"] >= 1
    
    db.close()


# ============================================================
# Test 4: Re-running audit returns same result
# ============================================================

def test_audit_deterministic(populated_db):
    """Test that running audit multiple times returns same result."""
    db, db_path = populated_db
    
    # Run audit 3 times
    results = [run_full_audit(db) for _ in range(3)]
    
    # All results should be identical
    for i in range(1, len(results)):
        assert results[i]["overall_status"] == results[0]["overall_status"]
        assert results[i]["ledger_integrity"]["violation_count"] == results[0]["ledger_integrity"]["violation_count"]
        assert results[i]["hash_verification"]["tampered_count"] == results[0]["hash_verification"]["tampered_count"]


def test_audit_idempotent_on_clean_db(populated_db):
    """Test that audit consistently returns PASS on clean database."""
    db, db_path = populated_db
    
    # Run audit multiple times
    results = [run_full_audit(db) for _ in range(3)]
    
    # All should pass
    for result in results:
        assert result["overall_status"] == "PASS"
        assert result["ledger_integrity"]["status"] == "PASS"
        assert result["hash_verification"]["status"] == "PASS"


# ============================================================
# Test 5: Integrity validation checks
# ============================================================

def test_integrity_detects_null_account_id():
    """Test that integrity check detects NULL account_id."""
    # Create an in-memory database using FinanceDB
    db = FinanceDB(':memory:')
    
    # Insert a statement
    stmt_id = db.insert_statement("TestBank", "test.pdf", "01/01/2025", "31/01/2025")
    
    # Insert a transaction with valid data first
    db.insert_transactions(stmt_id, [
        {"date": "01/01/2025", "description": "Test transaction", "amount": 100.0, "type": "debit"},
    ])
    
    # Now tamper with account_id by temporarily disabling the trigger
    with db.transaction() as conn:
        # Drop the immutability trigger temporarily
        conn.execute("DROP TRIGGER IF EXISTS prevent_transaction_update")
        
        # Set account_id to NULL
        conn.execute("UPDATE transactions SET account_id = NULL")
        
        # Recreate the trigger
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_transaction_update
            BEFORE UPDATE ON transactions
            BEGIN
                SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.');
            END
        """)
    
    result = validate_ledger_integrity(db)
    
    assert result["status"] == "FAIL"
    assert any(v["type"] == "NULL_ACCOUNT_ID" for v in result["violations"])
    
    db.close()


def test_integrity_detects_duplicate_hash():
    """Test that integrity check detects duplicate hash_signature."""
    # Create an in-memory database using FinanceDB
    db = FinanceDB(':memory:')
    
    # Insert a statement
    stmt_id = db.insert_statement("TestBank", "test.pdf", "01/01/2025", "31/01/2025")
    
    # Insert two transactions with different data (will have different hashes)
    db.insert_transactions(stmt_id, [
        {"date": "01/01/2025", "description": "Test transaction 1", "amount": 100.0, "type": "debit"},
        {"date": "02/01/2025", "description": "Test transaction 2", "amount": 200.0, "type": "debit"},
    ])
    
    # Now make them have the same hash by temporarily disabling the trigger
    # and dropping the unique index on hash_signature
    with db.transaction() as conn:
        # Drop the immutability trigger temporarily
        conn.execute("DROP TRIGGER IF EXISTS prevent_transaction_update")
        
        # Drop the unique index on hash_signature temporarily
        conn.execute("DROP INDEX IF EXISTS idx_transaction_hash")
        
        # Set both to have the same hash
        conn.execute("UPDATE transactions SET hash_signature = 'duplicate_hash'")
        
        # Note: We don't recreate the unique index here because it would fail
        # with duplicate values. The trigger is sufficient for the test.
        
        # Recreate the trigger
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_transaction_update
            BEFORE UPDATE ON transactions
            BEGIN
                SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.');
            END
        """)
    
    # Validate before recreating the unique index (can't recreate with duplicates)
    result = validate_ledger_integrity(db)
    
    assert result["status"] == "FAIL"
    assert any(v["type"] == "DUPLICATE_HASH" for v in result["violations"])
    
    db.close()


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
