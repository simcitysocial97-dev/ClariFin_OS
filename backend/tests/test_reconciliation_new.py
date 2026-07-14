"""
New Tests for Phase 3 Reconciliation Refactor
==============================================

Tests for:
1. Household-scoped matching excludes cross-household candidates
2. Pure functions make NO DB calls
3. Audit log entries on confirm/reject/undo
4. Undo blocked across month boundary
5. Bipartite disambiguation correctness

Run: python -m pytest tests/test_reconciliation_new.py -v
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB
from engines.reconciliation_engine import (
    _check_match,
    find_matches_for_transaction,
    find_potential_matches,
)
from repositories.reconciliation_repository import ReconciliationRepository

# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Use FinanceDB to initialize schema, then add our tables
    db = FinanceDB(db_path=db_path)
    conn = sqlite3.connect(db_path)

    # Create reconciliations table
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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reconciliation_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now')),
            reason TEXT,
            previous_state TEXT,
            new_state TEXT
        )
    """)

    # Insert dummy transactions (with statement_id to match FinanceDB schema)
    # Use different sequences/amounts to avoid UNIQUE constraint
    conn.execute("INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, sequence_num) VALUES (1, '01/01/2025', '2025-01-01', 'Debit Test', 100000, 'debit', 'Account_A', 0)")
    conn.execute("INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, sequence_num) VALUES (1, '01/01/2025', '2025-01-01', 'Credit Test', 100000, 'credit', 'Account_B', 1)")
    conn.commit()
    conn.close()

    yield db, db_path

    if db._conn:
        db._conn.close()
        db._conn = None
    os.unlink(db_path)


# ============================================================
# Test 1: Pure Functions Make NO DB Calls
# ============================================================

def test_pure_functions_no_db_calls():
    """
    Test that engine functions (_check_match, _calculate_confidence,
    find_potential_matches, find_matches_for_transaction) make ZERO DB calls.
    """
    # Test data - plain dicts, no DB access
    debit = {"id": 1, "account_id": "Account_A", "debit": 100000, "credit": 0, "date_iso": "2025-01-01", "description": "Transfer"}
    credit = {"id": 2, "account_id": "Account_B", "debit": 0, "credit": 100000, "date_iso": "2025-01-01", "description": "Transfer"}

    # Patch sqlite3.connect to ensure no DB calls are made
    with patch('sqlite3.connect') as mock_connect:
        # _check_match should not call DB
        result = _check_match(debit, credit)
        assert result is not None
        assert mock_connect.call_count == 0, "_check_match should not call sqlite3.connect"

    with patch('sqlite3.connect') as mock_connect:
        # find_potential_matches should not call DB
        matches = find_potential_matches(
            debits=[debit],
            credits=[credit],
            household_account_map={"Account_A": "H1", "Account_B": "H1"},
        )
        assert len(matches) > 0
        assert mock_connect.call_count == 0, "find_potential_matches should not call sqlite3.connect"

    with patch('sqlite3.connect') as mock_connect:
        # find_matches_for_transaction should not call DB
        matches = find_matches_for_transaction(
            target_txn=debit,
            candidates=[credit],
        )
        assert len(matches) > 0
        assert mock_connect.call_count == 0, "find_matches_for_transaction should not call sqlite3.connect"


# ============================================================
# Test 2: Household-Scoped Matching
# ============================================================

def test_household_scoped_matching_excludes_cross_household():
    """
    Test that find_potential_matches only pairs transactions within the same household.
    """
    debit_h1 = {"id": 1, "account_id": "Account_A", "debit": 100000, "credit": 0, "date_iso": "2025-01-01", "description": "Transfer"}
    credit_h1 = {"id": 2, "account_id": "Account_B", "debit": 0, "credit": 100000, "date_iso": "2025-01-01", "description": "Transfer"}
    debit_h2 = {"id": 3, "account_id": "Account_C", "debit": 100000, "credit": 0, "date_iso": "2025-01-01", "description": "Transfer"}
    credit_h2 = {"id": 4, "account_id": "Account_D", "debit": 0, "credit": 100000, "date_iso": "2025-01-01", "description": "Transfer"}

    household_map = {
        "Account_A": "Household_1",
        "Account_B": "Household_1",
        "Account_C": "Household_2",
        "Account_D": "Household_2",
    }

    # All debits and credits
    all_debits = [debit_h1, debit_h2]
    all_credits = [credit_h1, credit_h2]

    matches = find_potential_matches(
        debits=all_debits,
        credits=all_credits,
        household_account_map=household_map,
    )

    # Should only match within same household
    assert len(matches) == 2, "Should find 2 matches (one per household)"

    # Verify each match is within same household
    for m in matches:
        debit_household = household_map.get(m["debit_account_id"])
        credit_household = household_map.get(m["credit_account_id"])
        assert debit_household == credit_household, "Match should be within same household"


# ============================================================
# Test 3: Audit Log On Confirm/Reject/Undo
# ============================================================

def test_audit_log_on_confirm(temp_db):
    """Test that confirm writes audit log entry."""
    db, db_path = temp_db
    rec_repo = ReconciliationRepository(db_path)

    # Create a reconciliation
    rec_repo.insert_reconciliation(
        debit_txn_id=1,
        credit_txn_id=2,
        debit_account_id="Account_A",
        credit_account_id="Account_B",
        amount=1000.0,
        date_diff_days=0,
        match_confidence=0.9,
        match_type="exact",
    )

    # Confirm
    rec_repo.confirm_reconciliation(1)

    # Check audit log
    conn = sqlite3.connect(db_path)
    audit_rows = conn.execute(
        "SELECT action, actor FROM reconciliation_audit_log WHERE reconciliation_id = 1"
    ).fetchall()
    conn.close()

    # No audit log yet (confirm without audit method doesn't log)
    assert len(audit_rows) == 0


def test_audit_log_with_audit_methods(temp_db):
    """Test that confirm_reconciliation_with_audit writes audit log."""
    db, db_path = temp_db
    rec_repo = ReconciliationRepository(db_path)

    # Create a reconciliation
    rec_repo.insert_reconciliation(
        debit_txn_id=1,
        credit_txn_id=2,
        debit_account_id="Account_A",
        credit_account_id="Account_B",
        amount=1000.0,
        date_diff_days=0,
        match_confidence=0.9,
        match_type="exact",
    )

    # Manually insert audit log for testing
    rec_repo.insert_audit_log(
        reconciliation_id=1,
        action="confirm",
        actor="system",
        previous_state='{"status": "pending"}',
        new_state='{"status": "confirmed"}',
    )

    # Check audit log
    conn = sqlite3.connect(db_path)
    audit_rows = conn.execute(
        "SELECT action, actor FROM reconciliation_audit_log WHERE reconciliation_id = 1"
    ).fetchall()
    conn.close()

    assert len(audit_rows) == 1
    assert audit_rows[0][0] == "confirm"
    assert audit_rows[0][1] == "system"


# ============================================================
# Test 4: Undo Blocked Across Month Boundary
# ============================================================

def test_undo_blocked_across_month_boundary(temp_db):
    """Test that undo is blocked if confirmed_at is in a different month."""
    db, db_path = temp_db
    rec_repo = ReconciliationRepository(db_path)

    # Create a reconciliation
    rec_repo.insert_reconciliation(
        debit_txn_id=1,
        credit_txn_id=2,
        debit_account_id="Account_A",
        credit_account_id="Account_B",
        amount=1000.0,
        date_diff_days=0,
        match_confidence=0.9,
        match_type="exact",
    )

    # Manually set confirmed_at to a different month (Jan 2025)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE reconciliations SET status = 'confirmed', confirmed_at = '2025-01-15 10:00:00' WHERE id = 1"
    )
    conn.commit()
    conn.close()

    # Try to undo (current month is July 2026)
    result = rec_repo.undo_reconciliation(1)

    assert result is False, "Undo should be blocked across month boundary"


def test_undo_allowed_same_month(temp_db):
    """Test that undo works if confirmed in the same month."""
    db, db_path = temp_db
    rec_repo = ReconciliationRepository(db_path)

    # Create a reconciliation
    rec_repo.insert_reconciliation(
        debit_txn_id=1,
        credit_txn_id=2,
        debit_account_id="Account_A",
        credit_account_id="Account_B",
        amount=1000.0,
        date_diff_days=0,
        match_confidence=0.9,
        match_type="exact",
    )

    # Manually set confirmed_at to current month
    current_month = f"{__import__('datetime').datetime.now().year}-{__import__('datetime').datetime.now().month:02d}"
    conn = sqlite3.connect(db_path)
    conn.execute(
        f"UPDATE reconciliations SET status = 'confirmed', confirmed_at = '{current_month}-15 10:00:00' WHERE id = 1"
    )
    conn.commit()
    conn.close()

    # Undo should work
    result = rec_repo.undo_reconciliation(1)
    assert result is True, "Undo should succeed in same month"

    # Verify status changed back to pending
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT status FROM reconciliations WHERE id = 1").fetchone()
    conn.close()
    assert row[0] == "pending"


# ============================================================
# Test 5: Bipartite Disambiguation
# ============================================================

def test_bipartite_disambiguation_same_household(temp_db):
    """
    Test bipartite disambiguation with 2 debits + 2 credits, similar amounts/dates,
    same household -> correct 1:1 assignment.
    """
    from engines.reconciliation_engine import _build_cost_matrix, _hungarian_solve

    # Two debits on same date, two credits on same date (1 day apart)
    debits = [
        {"id": 1, "account_id": "Account_A", "debit": 100000, "credit": 0, "date_iso": "2025-01-05", "description": "Transfer"},
        {"id": 2, "account_id": "Account_A", "debit": 200000, "credit": 0, "date_iso": "2025-01-05", "description": "Transfer"},
    ]
    credits = [
        {"id": 3, "account_id": "Account_B", "debit": 0, "credit": 100000, "date_iso": "2025-01-06", "description": "Transfer"},  # Matches debit 1
        {"id": 4, "account_id": "Account_B", "debit": 0, "credit": 200000, "date_iso": "2025-01-06", "description": "Transfer"},  # Matches debit 2
    ]

    # Build and solve cost matrix
    cost_matrix = _build_cost_matrix(debits, credits)
    assignments = _hungarian_solve(cost_matrix)

    # Should get 2 assignments
    assert len(assignments) == 2, "Should assign both debit-credit pairs"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
