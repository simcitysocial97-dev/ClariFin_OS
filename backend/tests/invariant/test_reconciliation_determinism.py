"""
Test Suite for Phase 2B: Reconciliation Determinism
====================================================

Tests for:
1. Same dataset → same reconciliation rows
2. Re-run engine → no duplicates
3. Confirmed rows remain unchanged
4. Ledger replay still produces identical balances

Run: python -m pytest tests/test_reconciliation_determinism.py -v
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
from engines.balance_engine import compute_account_balance
from engines.reconciliation_engine import find_potential_matches
from repositories.reconciliation_repository import ReconciliationRepository
from repositories.statement_repository import StatementRepository

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    db = FinanceDB(db_path=db_path)
    stmt_repo = StatementRepository(db_path)

    # Insert test statements for different accounts
    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")

    yield db, db_path

    # Cleanup - ensure connection is closed
    if db._conn:
        db._conn.close()
        db._conn = None
    os.unlink(db_path)


@pytest.fixture
def populated_db(temp_db):
    """Populate database with deterministic test transactions."""
    db, db_path = temp_db

    conn = sqlite3.connect(db_path)

    # Insert transactions for Account A (debits)
    # Note: debit/credit are GENERATED columns from amount_paise and type
    conn.execute("""
        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id)
        VALUES
            (1, '01/01/2025', '2025-01-01', 'Transfer to B', 100000, 'debit', 'Account_A'),
            (1, '05/01/2025', '2025-01-05', 'Transfer to B late', 200000, 'debit', 'Account_A'),
            (1, '10/01/2025', '2025-01-10', 'Different amount', 50000, 'debit', 'Account_A')
    """)

    # Insert transactions for Account B (credits)
    # Note: debit/credit are GENERATED columns from amount_paise and type
    conn.execute("""
        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id)
        VALUES
            (2, '01/01/2025', '2025-01-01', 'Transfer from A', 100000, 'credit', 'Account_B'),
            (2, '07/01/2025', '2025-01-07', 'Transfer from A late', 200000, 'credit', 'Account_B'),
            (2, '10/01/2025', '2025-01-10', 'Different amount', 75000, 'credit', 'Account_B')
    """)

    conn.commit()
    conn.close()

    return db, db_path


# ============================================================
# Test 1: Same Dataset → Same Reconciliation Rows
# ============================================================


def test_deterministic_matching(populated_db):
    """Test that same dataset produces same reconciliation matches."""
    db, db_path = populated_db

    # Run matching twice
    matches_1 = find_potential_matches(db_path)
    matches_2 = find_potential_matches(db_path)

    # Should produce identical results
    assert len(matches_1) == len(matches_2), "Match count should be identical"

    # Sort by deterministic key for comparison
    keys_1 = sorted([m["deterministic_key"] for m in matches_1])
    keys_2 = sorted([m["deterministic_key"] for m in matches_2])

    assert keys_1 == keys_2, "Match keys should be identical"

    # Verify confidence scores are identical
    for m1, m2 in zip(
        sorted(matches_1, key=lambda x: x["deterministic_key"]),
        sorted(matches_2, key=lambda x: x["deterministic_key"]),
        strict=False,
    ):
        assert (
            m1["match_confidence"] == m2["match_confidence"]
        ), f"Confidence should be identical for {m1['deterministic_key']}"


def test_deterministic_key_consistency(populated_db):
    """Test that deterministic keys are consistent across runs."""
    db, db_path = populated_db

    matches = find_potential_matches(db_path)

    for m in matches:
        # Verify key format: "min_id:max_id"
        parts = m["deterministic_key"].split(":")
        assert len(parts) == 2, "Key should have format 'min_id:max_id'"

        min_id = int(parts[0])
        max_id = int(parts[1])

        # Verify min < max
        assert min_id < max_id, "First ID should be smaller"

        # Verify key matches transaction IDs
        ids = [m["debit_txn_id"], m["credit_txn_id"]]
        assert min_id == min(ids), "Min ID should match"
        assert max_id == max(ids), "Max ID should match"


# ============================================================
# Test 2: Re-run Engine → No Duplicates
# ============================================================


def test_idempotent_insert(populated_db):
    """Test that INSERT OR IGNORE prevents duplicates."""
    db, db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    matches = find_potential_matches(db_path)
    assert len(matches) > 0, "Should find matches"

    # Insert first match
    m = matches[0]
    inserted_1 = rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount=m["amount"],
        date_diff_days=m["date_diff_days"],
        match_confidence=m["match_confidence"],
        match_type=m["match_type"],
    )
    assert inserted_1 is True, "First insert should succeed"

    # Try to insert same match again
    inserted_2 = rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount=m["amount"],
        date_diff_days=m["date_diff_days"],
        match_confidence=m["match_confidence"],
        match_type=m["match_type"],
    )
    assert inserted_2 is False, "Second insert should be ignored"

    # Verify only one row exists
    reconciliations = rec_repo.get_reconciliations()
    keys = [r["deterministic_key"] for r in reconciliations]
    assert keys.count(m["deterministic_key"]) == 1, "Should have exactly one row"


def test_mirrored_pair_prevention(populated_db):
    """Test that mirrored pairs (A,B) and (B,A) are prevented."""
    db, db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    matches = find_potential_matches(db_path)
    m = matches[0]

    # Insert with original order
    inserted_1 = rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount=m["amount"],
        date_diff_days=m["date_diff_days"],
        match_confidence=m["match_confidence"],
        match_type=m["match_type"],
    )
    assert inserted_1 is True

    # Try to insert with reversed order
    inserted_2 = rec_repo.insert_reconciliation(
        debit_txn_id=m["credit_txn_id"],  # Reversed
        credit_txn_id=m["debit_txn_id"],  # Reversed
        debit_account_id=m["credit_account_id"],
        credit_account_id=m["debit_account_id"],
        amount=m["amount"],
        date_diff_days=m["date_diff_days"],
        match_confidence=m["match_confidence"],
        match_type=m["match_type"],
    )
    assert inserted_2 is False, "Mirrored pair should be ignored"


# ============================================================
# Test 3: Confirmed Rows Remain Unchanged
# ============================================================


def test_confirmed_row_immutable(populated_db):
    """Test that confirmed rows cannot be modified."""
    db, db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    matches = find_potential_matches(db_path)
    m = matches[0]

    # Insert and confirm
    rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount=m["amount"],
        date_diff_days=m["date_diff_days"],
        match_confidence=m["match_confidence"],
        match_type=m["match_type"],
    )

    reconciliations = rec_repo.get_reconciliations()
    rec_id = reconciliations[0]["id"]

    # Confirm
    rec_repo.confirm_reconciliation(rec_id)

    # Get the confirmed row
    confirmed = rec_repo.get_reconciliations(status="confirmed")
    assert len(confirmed) == 1

    # Verify fields are unchanged
    assert confirmed[0]["deterministic_key"] == m["deterministic_key"]
    assert confirmed[0]["match_confidence"] == m["match_confidence"]
    assert confirmed[0]["amount_paise"] == int(m["amount"] * 100)


def test_confirm_does_not_modify_transactions(populated_db):
    """Test that confirming reconciliation does NOT modify transaction records."""
    db, db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    matches = find_potential_matches(db_path)
    m = matches[0]

    # Get transaction states before
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT debit, credit, amount_paise FROM transactions WHERE id = ?",
        (m["debit_txn_id"],),
    )
    txn_before = dict(cur.fetchone())
    conn.close()

    # Insert and confirm
    rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount=m["amount"],
        date_diff_days=m["date_diff_days"],
        match_confidence=m["match_confidence"],
        match_type=m["match_type"],
    )

    reconciliations = rec_repo.get_reconciliations()
    rec_repo.confirm_reconciliation(reconciliations[0]["id"])

    # Get transaction states after
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT debit, credit, amount_paise FROM transactions WHERE id = ?",
        (m["debit_txn_id"],),
    )
    txn_after = dict(cur.fetchone())
    conn.close()

    # Transactions should be unchanged
    assert txn_before == txn_after, "Confirm should NOT modify transaction records"


# ============================================================
# Test 4: Ledger Replay Produces Identical Balances
# ============================================================


def test_balance_unaffected_by_reconciliation(populated_db):
    """Test that balance computation is unaffected by reconciliation state."""
    db, db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    # Compute balance before reconciliation
    balance_before = compute_account_balance(db_path, "Account_A")

    # Create and confirm reconciliations
    matches = find_potential_matches(db_path)
    for m in matches:
        rec_repo.insert_reconciliation(
            debit_txn_id=m["debit_txn_id"],
            credit_txn_id=m["credit_txn_id"],
            debit_account_id=m["debit_account_id"],
            credit_account_id=m["credit_account_id"],
            amount=m["amount"],
            date_diff_days=m["date_diff_days"],
            match_confidence=m["match_confidence"],
            match_type=m["match_type"],
        )

    # Confirm all
    for r in rec_repo.get_reconciliations(status="pending"):
        rec_repo.confirm_reconciliation(r["id"])

    # Compute balance after reconciliation
    balance_after = compute_account_balance(db_path, "Account_A")

    # Balances should be identical
    assert (
        balance_before["balance_paise"] == balance_after["balance_paise"]
    ), "Balance should be unaffected by reconciliation"


def test_replay_determinism_maintained(populated_db):
    """Test that ledger replay determinism is maintained after reconciliation."""
    db, db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    # Get initial transaction order
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute("""
        SELECT id, date_iso, debit, credit
        FROM transactions
        WHERE account_id = 'Account_A'
        ORDER BY date_iso ASC, id ASC
    """)
    txns_before = [dict(row) for row in cur.fetchall()]
    conn.close()

    # Create and confirm reconciliations
    matches = find_potential_matches(db_path)
    for m in matches:
        rec_repo.insert_reconciliation(
            debit_txn_id=m["debit_txn_id"],
            credit_txn_id=m["credit_txn_id"],
            debit_account_id=m["debit_account_id"],
            credit_account_id=m["credit_account_id"],
            amount=m["amount"],
            date_diff_days=m["date_diff_days"],
            match_confidence=m["match_confidence"],
            match_type=m["match_type"],
        )

    for r in rec_repo.get_reconciliations(status="pending"):
        rec_repo.confirm_reconciliation(r["id"])

    # Get transaction order after
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute("""
        SELECT id, date_iso, debit, credit
        FROM transactions
        WHERE account_id = 'Account_A'
        ORDER BY date_iso ASC, id ASC
    """)
    txns_after = [dict(row) for row in cur.fetchall()]
    conn.close()

    # Transaction order should be identical
    assert len(txns_before) == len(txns_after)
    for t1, t2 in zip(txns_before, txns_after, strict=False):
        assert t1["id"] == t2["id"]
        assert t1["date_iso"] == t2["date_iso"]
        assert t1["debit"] == t2["debit"]
        assert t1["credit"] == t2["credit"]


# ============================================================
# Test 5: Confidence Calculation Determinism
# ============================================================


def test_confidence_deterministic(populated_db):
    """Test that confidence scores are deterministic."""
    db, db_path = populated_db

    # Run matching multiple times
    all_confidences = []
    for _ in range(3):
        matches = find_potential_matches(db_path)
        confidences = {m["deterministic_key"]: m["match_confidence"] for m in matches}
        all_confidences.append(confidences)

    # All runs should produce identical confidence scores
    for i in range(1, len(all_confidences)):
        assert (
            all_confidences[0] == all_confidences[i]
        ), f"Run {i} produced different confidence scores"


def test_confidence_bounds(populated_db):
    """Test that confidence scores are within bounds [0, 1]."""
    db, db_path = populated_db

    matches = find_potential_matches(db_path)

    for m in matches:
        assert (
            0.0 <= m["match_confidence"] <= 1.0
        ), f"Confidence {m['match_confidence']} out of bounds for {m['deterministic_key']}"

        # Verify rounding to 4 decimals
        rounded = round(m["match_confidence"], 4)
        assert (
            m["match_confidence"] == rounded
        ), "Confidence should be rounded to 4 decimals"


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
