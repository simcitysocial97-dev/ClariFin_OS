"""
Tests for Reconciliation Stats Endpoint (PRD Acceptance Criteria)
================================================================

Tests for:
1. Known fixture (10 transactions, 6 matched+confirmed, 1 rejected) produces
   hand-verified coverage_ratio, accuracy_score, and health_score matching the PRD formula
2. Zero-transaction edge case returns 0.0 health_score, not a crash

Run: python -m pytest tests/test_reconciliation_stats.py -v
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB
from repositories.reconciliation_repository import ReconciliationRepository

# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Use FinanceDB to initialize schema
    db = FinanceDB(db_path=db_path)
    conn = sqlite3.connect(db_path)

    # Create reconciliations table (FinanceDB doesn't create it)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reconciliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debit_txn_id INTEGER NOT NULL,
            credit_txn_id INTEGER NOT NULL,
            debit_account_id TEXT NOT NULL,
            credit_account_id TEXT NOT NULL,
            amount_paise INTEGER NOT NULL,
            date_diff_days INTEGER DEFAULT 0,
            match_confidence REAL DEFAULT 0.0,
            match_type TEXT DEFAULT 'exact',
            status TEXT DEFAULT 'pending',
            deterministic_key TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            confirmed_at TEXT
        )
    """)

    conn.commit()
    conn.close()

    yield db, db_path

    if db._conn:
        db._conn.close()
        db._conn = None
    os.unlink(db_path)


@pytest.fixture
def populated_stats_db(temp_db):
    """Populate database with known test data for stats verification.

    Creates:
    - 10 total transactions
    - 3 confirmed reconciliations (matches 6 transaction IDs)
    - 1 rejected reconciliation (matches 2 more transaction IDs)
    - Remaining 2 transactions unmatched

    So: 6 matched, 4 unmatched (total 10)
    """
    db, db_path = temp_db
    conn = sqlite3.connect(db_path)

    # Insert 10 transactions (ids 1-10)
    # 6 debits and 4 credits to get 6 distinct matched IDs in confirmed reconciliations
    for i in range(1, 7):
        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, sequence_num)
            VALUES (1, '01/01/2025', '2025-01-01', ?, ?, 'debit', 'Account_A', ?)
        """, (f'Debit {i}', 10000 * i, i))

    for i in range(7, 11):
        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, sequence_num)
            VALUES (1, '01/01/2025', '2025-01-01', ?, ?, 'credit', 'Account_B', ?)
        """, (f'Credit {i}', 10000 * i, i))

    conn.commit()

    # Insert 3 confirmed reconciliations (matching 6 transaction IDs: 1-3 and 7-9)
    confirmed_pairs = [
        (1, 7, 'Account_A', 'Account_B'),
        (2, 8, 'Account_A', 'Account_B'),
        (3, 9, 'Account_A', 'Account_B'),
    ]

    for debit_id, credit_id, debit_acc, credit_acc in confirmed_pairs:
        min_id = min(debit_id, credit_id)
        max_id = max(debit_id, credit_id)
        deterministic_key = f"{min_id}:{max_id}"
        conn.execute("""
            INSERT INTO reconciliations (
                debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
                amount_paise, date_diff_days, match_confidence, match_type, status, deterministic_key
            ) VALUES (?, ?, ?, ?, 100000, 0, 1.0, 'exact', 'confirmed', ?)
        """, (debit_id, credit_id, debit_acc, credit_acc, deterministic_key))

    # Insert 1 rejected reconciliation (matching ids 4, 10)
    conn.execute("""
        INSERT INTO reconciliations (
            debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
            amount_paise, date_diff_days, match_confidence, match_type, status, deterministic_key
        ) VALUES (4, 10, 'Account_A', 'Account_B', 100000, 0, 0.8, 'window', 'rejected', '4:10')
    """)

    conn.commit()
    conn.close()

    yield db, db_path


# ============================================================
# Test 1: Known Fixture - Stats Calculation Verification
# ============================================================

def test_reconciliation_stats_known_fixture(populated_stats_db):
    """Test stats with PRD-specified fixture: 10 transactions, 6 matched in confirmed, 1 rejected."""
    db, db_path = populated_stats_db
    repo = ReconciliationRepository(db_path)
    stats = repo.get_reconciliation_stats()

    # Verify PRD-specified counts
    assert stats["total_transactions"] == 10
    assert stats["matched_transactions"] == 6  # 3 pairs = 6 distinct IDs in confirmed reconciliations
    assert stats["confirmed_count"] == 3
    assert stats["rejected_count"] == 1

    # Calculate expected values using PRD formula
    expected_coverage_ratio = 6 / 10  # 6 matched / 10 total
    expected_accuracy_score = 3 / (3 + 1)  # 3 confirmed / 4 total decisions = 0.75
    expected_health_score = round((expected_coverage_ratio * 0.6 + expected_accuracy_score * 0.4) * 100, 2)

    # Hand-verified: (0.6 * 0.6 + 0.75 * 0.4) * 100 = 70.0
    assert stats["coverage_ratio"] == pytest.approx(expected_coverage_ratio, rel=1e-3)
    assert stats["accuracy_score"] == pytest.approx(expected_accuracy_score, rel=1e-3)
    assert stats["health_score"] == pytest.approx(expected_health_score, rel=1e-2)


# ============================================================
# Test 2: Zero-Transaction Edge Case
# ============================================================

def test_reconciliation_stats_zero_transactions(temp_db):
    """Test that zero transactions returns 0.0 health_score without crash."""
    db, db_path = temp_db
    repo = ReconciliationRepository(db_path)

    # Database has no transactions or reconciliations
    stats = repo.get_reconciliation_stats()

    assert stats["total_transactions"] == 0
    assert stats["matched_transactions"] == 0
    assert stats["confirmed_count"] == 0
    assert stats["rejected_count"] == 0
    assert stats["coverage_ratio"] == 0.0
    assert stats["accuracy_score"] == 0.0
    assert stats["health_score"] == 0.0


# ============================================================
# Test 3: Zero Matched Transactions (No Reconciliations)
# ============================================================

@pytest.fixture
def transactions_no_reconciliations(temp_db):
    """Database with transactions but no reconciliations."""
    db, db_path = temp_db
    conn = sqlite3.connect(db_path)

    # Insert 10 transactions but no reconciliations
    for i in range(1, 11):
        tx_type = 'debit' if i <= 5 else 'credit'
        amount = 10000 * i
        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, sequence_num)
            VALUES (1, '01/01/2025', '2025-01-01', ?, ?, ?, 'Account_A', ?)
        """, (f'Transaction {i}', amount, tx_type, i))

    conn.commit()
    conn.close()
    yield db, db_path


def test_reconciliation_stats_no_matched(transactions_no_reconciliations):
    """Test stats when no reconciliations exist."""
    db, db_path = transactions_no_reconciliations
    repo = ReconciliationRepository(db_path)
    stats = repo.get_reconciliation_stats()

    assert stats["total_transactions"] == 10
    assert stats["matched_transactions"] == 0
    assert stats["confirmed_count"] == 0
    assert stats["rejected_count"] == 0
    assert stats["coverage_ratio"] == 0.0
    assert stats["accuracy_score"] == 0.0
    assert stats["health_score"] == 0.0


# ============================================================
# Test 4: All Confirmed (Perfect Record)
# ============================================================

@pytest.fixture
def all_confirmed_db(temp_db):
    """Database with all confirmed reconciliations."""
    db, db_path = temp_db
    conn = sqlite3.connect(db_path)

    # Insert 4 transactions (2 pairs)
    conn.execute("""
        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, sequence_num)
        VALUES (1, '01/01/2025', '2025-01-01', 'Debit 1', 100000, 'debit', 'Account_A', 1),
               (1, '01/01/2025', '2025-01-01', 'Credit 1', 100000, 'credit', 'Account_B', 2),
               (1, '01/01/2025', '2025-01-01', 'Debit 2', 200000, 'debit', 'Account_A', 3),
               (1, '01/01/2025', '2025-01-01', 'Credit 2', 200000, 'credit', 'Account_B', 4)
    """)

    # Insert 2 confirmed reconciliations
    conn.execute("""
        INSERT INTO reconciliations (
            debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
            amount_paise, date_diff_days, match_confidence, match_type, status, deterministic_key
        ) VALUES (1, 2, 'Account_A', 'Account_B', 100000, 0, 1.0, 'exact', 'confirmed', '1:2'),
               (3, 4, 'Account_A', 'Account_B', 200000, 0, 1.0, 'exact', 'confirmed', '3:4')
    """)

    conn.commit()
    conn.close()
    yield db, db_path


def test_reconciliation_stats_all_confirmed(all_confirmed_db):
    """Test stats when all reconciliations are confirmed (no rejections)."""
    db, db_path = all_confirmed_db
    repo = ReconciliationRepository(db_path)
    stats = repo.get_reconciliation_stats()

    assert stats["total_transactions"] == 4
    assert stats["matched_transactions"] == 4  # 2 pairs = 4 distinct matched IDs
    assert stats["confirmed_count"] == 2
    assert stats["rejected_count"] == 0

    # accuracy_score should be 1.0 when no rejections and has confirms
    assert stats["accuracy_score"] == 1.0
    assert stats["coverage_ratio"] == 1.0  # All matched
    assert stats["health_score"] == 100.0  # (1.0 * 0.6 + 1.0 * 0.4) * 100


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
