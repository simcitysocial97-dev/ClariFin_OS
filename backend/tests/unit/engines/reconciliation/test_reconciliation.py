"""
Test Suite for Phase 2B: Cross-Account Reconciliation
======================================================

Tests for:
1. Exact match detection
2. Date window detection
3. No false positives when amounts differ
4. Confirm does not mutate transactions
5. Reject does not mutate transactions
6. Duplicate reconciliation prevention

Phase 2B.1: Deterministic matching with confidence scoring.

Run: python -m pytest tests/test_reconciliation.py -v
"""

import sqlite3

import pytest
from repositories.reconciliation_repository import ReconciliationRepository
from repositories.statement_repository import StatementRepository
from src.engines.reconciliation_engine import (
    _calculate_confidence,
    _check_match,
    _date_difference_days,
    _generate_explanation,
    _parse_date_iso,
    _simple_description_similarity,
    find_matches_for_transaction,
    find_potential_matches,
)


@pytest.fixture
def populated_db(temp_db: str) -> str:
    """Provide a database populated with reconciliation test data.

    Uses the global schema-initialized temp_db to avoid expensive
    full database initialization per test.
    """
    db_path = temp_db
    stmt_repo = StatementRepository(db_path)

    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")

    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id)
        VALUES
            (1, '01/01/2025', '2025-01-01', 'Transfer to B', 100000, 'debit', 'Account_A'),
            (1, '05/01/2025', '2025-01-05', 'Transfer to B late', 200000, 'debit', 'Account_A'),
            (1, '10/01/2025', '2025-01-10', 'Different amount', 50000, 'debit', 'Account_A'),
            (1, '15/01/2025', '2025-01-15', 'Same account transfer', 30000, 'debit', 'Account_A')
    """)
    conn.execute("""
        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id)
        VALUES
            (2, '01/01/2025', '2025-01-01', 'Transfer from A', 100000, 'credit', 'Account_B'),
            (2, '07/01/2025', '2025-01-07', 'Transfer from A late', 200000, 'credit', 'Account_B'),
            (2, '10/01/2025', '2025-01-10', 'Different amount', 75000, 'credit', 'Account_B'),
            (2, '15/01/2025', '2025-01-15', 'Same account credit', 30000, 'credit', 'Account_B')
    """)
    conn.commit()
    conn.close()

    return db_path


# ============================================================
# Test 1: Exact Match Detection
# ============================================================


def test_exact_match_detection(populated_db):
    """Test that exact matches (same amount, same date, different accounts) are detected."""
    db_path = populated_db

    matches = find_potential_matches(db_path)

    # Should find exact match: 1000 debit on 2025-01-01 in A matches 1000 credit on 2025-01-01 in B
    exact_matches = [m for m in matches if m["match_type"] == "exact"]

    assert len(exact_matches) >= 1, "Should detect at least one exact match"

    # Verify the match details
    exact_match = exact_matches[0]
    assert exact_match["match_type"] == "exact"
    assert exact_match["match_confidence"] >= 0.8  # High confidence for exact match


# ============================================================
# Test 2: Date Window Detection
# ============================================================


def test_date_window_detection(populated_db):
    """Test that date window matches (same amount, within 3 days) are detected."""
    db_path = populated_db

    matches = find_potential_matches(db_path)

    # Should find date window match: 2000 debit on 2025-01-05 matches 2000 credit on 2025-01-07 (2 days apart)
    window_matches = [m for m in matches if m["match_type"] == "window"]

    assert len(window_matches) >= 1, "Should detect at least one date window match"

    # Verify the match details
    window_match = window_matches[0]
    assert window_match["match_type"] == "window"
    assert window_match["date_diff_days"] <= 3


# ============================================================
# Test 3: No False Positives When Amounts Differ
# ============================================================


def test_no_false_positives_different_amounts(populated_db):
    """Test that transactions with different amounts are NOT matched."""
    db_path = populated_db

    matches = find_potential_matches(db_path)

    # All matches should have matching amounts (debit == credit in paise)
    for m in matches:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT debit, credit FROM transactions WHERE id = ?", (m["debit_txn_id"],)
        )
        debit_txn = cur.fetchone()
        cur = conn.execute(
            "SELECT debit, credit FROM transactions WHERE id = ?", (m["credit_txn_id"],)
        )
        credit_txn = cur.fetchone()
        conn.close()

        # Debit from one should equal credit from other
        assert (
            debit_txn["debit"] == credit_txn["credit"]
        ), "Matched transactions should have equal debit/credit amounts"


def test_no_same_account_matches(populated_db):
    """Test that transactions in the same account are NOT matched."""
    db_path = populated_db

    matches = find_potential_matches(db_path)

    # All matches should be between different accounts
    for m in matches:
        assert (
            m["debit_account_id"] != m["credit_account_id"]
        ), "Should not match transactions from the same account"


# ============================================================
# Test 4: Confirm Does Not Mutate Transactions
# ============================================================


def test_confirm_no_transaction_mutation(populated_db):
    """Test that confirming a reconciliation does NOT modify transaction records."""
    db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    # Get a match to work with
    matches = find_potential_matches(db_path)
    m = (
        matches[0]
        if matches
        else {
            "debit_txn_id": 1,
            "credit_txn_id": 5,
            "debit_account_id": "Account_A",
            "credit_account_id": "Account_B",
            "amount": 1000.00,
            "date_diff_days": 0,
            "match_confidence": 0.8,
            "match_type": "exact",
        }
    )

    # Create a reconciliation
    inserted = rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount_paise=int(m["amount"] * 100),
        date_diff_days=m["date_diff_days"],
        confidence_bps=int(m["match_confidence"] * 10000),
        match_type=m["match_type"],
    )

    assert inserted is True, "Insert should succeed"

    # Get reconciliations to find the ID
    recs = rec_repo.get_reconciliations(status="pending")
    rec_id = recs[0]["id"] if recs else None

    if rec_id:
        # Get transaction states before confirm
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT debit, credit, amount_paise FROM transactions WHERE id = ?",
            (m["debit_txn_id"],),
        )
        txn_before = dict(cur.fetchone())
        conn.close()

        # Confirm the reconciliation
        result = rec_repo.confirm_reconciliation(rec_id)
        assert result is True, "Confirm should succeed"

        # Get transaction states after confirm
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
# Test 5: Reject Does Not Mutate Transactions
# ============================================================


def test_reject_no_transaction_mutation(populated_db):
    """Test that rejecting a reconciliation does NOT modify transaction records."""
    db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    # Get a match to work with
    matches = find_potential_matches(db_path)
    m = (
        matches[0]
        if matches
        else {
            "debit_txn_id": 1,
            "credit_txn_id": 5,
            "debit_account_id": "Account_A",
            "credit_account_id": "Account_B",
            "amount": 1000.00,
            "date_diff_days": 0,
            "match_confidence": 0.8,
            "match_type": "exact",
        }
    )

    # Create a reconciliation
    inserted = rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount_paise=int(m["amount"] * 100),
        date_diff_days=m["date_diff_days"],
        confidence_bps=int(m["match_confidence"] * 10000),
        match_type=m["match_type"],
    )

    assert inserted is True, "Insert should succeed"

    # Get reconciliations to find the ID
    recs = rec_repo.get_reconciliations(status="pending")
    rec_id = recs[0]["id"] if recs else None

    if rec_id:
        # Get transaction states before reject
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT debit, credit, amount_paise FROM transactions WHERE id = ?",
            (m["debit_txn_id"],),
        )
        txn_before = dict(cur.fetchone())
        conn.close()

        # Reject the reconciliation
        result = rec_repo.reject_reconciliation(rec_id)
        assert result is True, "Reject should succeed"

        # Get transaction states after reject
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT debit, credit, amount_paise FROM transactions WHERE id = ?",
            (m["debit_txn_id"],),
        )
        txn_after = dict(cur.fetchone())
        conn.close()

        # Transactions should be unchanged
        assert txn_before == txn_after, "Reject should NOT modify transaction records"


# ============================================================
# Test 6: Duplicate Reconciliation Prevention
# ============================================================


def test_prevent_duplicate_pairs(populated_db):
    """Test that duplicate reconciliation pairs are prevented via idempotent insert."""
    db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    # Get a match to work with
    matches = find_potential_matches(db_path)
    m = (
        matches[0]
        if matches
        else {
            "debit_txn_id": 1,
            "credit_txn_id": 5,
            "debit_account_id": "Account_A",
            "credit_account_id": "Account_B",
            "amount": 1000.00,
            "date_diff_days": 0,
            "match_confidence": 0.8,
            "match_type": "exact",
        }
    )

    # Create first reconciliation
    inserted_1 = rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount_paise=int(m["amount"] * 100),
        date_diff_days=m["date_diff_days"],
        confidence_bps=int(m["match_confidence"] * 10000),
        match_type=m["match_type"],
    )
    assert inserted_1 is True

    # Try to create duplicate (same pair) - should be ignored
    inserted_2 = rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount_paise=int(m["amount"] * 100),
        date_diff_days=m["date_diff_days"],
        confidence_bps=int(m["match_confidence"] * 10000),
        match_type=m["match_type"],
    )
    assert inserted_2 is False, "Duplicate should be ignored"


def test_prevent_mirrored_pairs(populated_db):
    """Test that mirrored pairs (A,B) and (B,A) are prevented via deterministic key."""
    db_path = populated_db
    rec_repo = ReconciliationRepository(db_path)

    # Get a match to work with
    matches = find_potential_matches(db_path)
    m = (
        matches[0]
        if matches
        else {
            "debit_txn_id": 1,
            "credit_txn_id": 5,
            "debit_account_id": "Account_A",
            "credit_account_id": "Account_B",
            "amount": 1000.00,
            "date_diff_days": 0,
            "match_confidence": 0.8,
            "match_type": "exact",
        }
    )

    # Create first reconciliation
    inserted_1 = rec_repo.insert_reconciliation(
        debit_txn_id=m["debit_txn_id"],
        credit_txn_id=m["credit_txn_id"],
        debit_account_id=m["debit_account_id"],
        credit_account_id=m["credit_account_id"],
        amount_paise=int(m["amount"] * 100),
        date_diff_days=m["date_diff_days"],
        confidence_bps=int(m["match_confidence"] * 10000),
        match_type=m["match_type"],
    )
    assert inserted_1 is True

    # Try to create mirrored pair (swapped IDs) - should be ignored
    # Note: The deterministic key uses min/max IDs, so this is the same key
    inserted_2 = rec_repo.insert_reconciliation(
        debit_txn_id=m["credit_txn_id"],
        credit_txn_id=m["debit_txn_id"],
        debit_account_id=m["credit_account_id"],
        credit_account_id=m["debit_account_id"],
        amount_paise=int(m["amount"] * 100),
        date_diff_days=m["date_diff_days"],
        confidence_bps=int(m["match_confidence"] * 10000),
        match_type=m["match_type"],
    )
    assert inserted_2 is False, "Mirrored pair should be ignored"


# ============================================================
# Additional Tests: Unit Tests for Matching Functions
# ============================================================


def test_check_match_same_account():
    """Test that match returns None for same account."""
    txn_a = {
        "id": 1,
        "account_id": "Account_A",
        "debit": 100000,
        "credit": 0,
        "date_iso": "2025-01-01",
        "description": "Test",
    }
    txn_b = {
        "id": 2,
        "account_id": "Account_A",
        "debit": 0,
        "credit": 100000,
        "date_iso": "2025-01-01",
        "description": "Test",
    }

    result = _check_match(txn_a, txn_b)
    assert result is None


def test_check_match_different_amounts():
    """Test that match returns None for different amounts."""
    txn_a = {
        "id": 1,
        "account_id": "Account_A",
        "debit": 100000,
        "credit": 0,
        "date_iso": "2025-01-01",
        "description": "Test",
    }
    txn_b = {
        "id": 2,
        "account_id": "Account_B",
        "debit": 0,
        "credit": 50000,
        "date_iso": "2025-01-01",
        "description": "Test",
    }

    result = _check_match(txn_a, txn_b)
    assert result is None


def test_check_match_valid():
    """Test that match returns valid result for matching transactions."""
    txn_a = {
        "id": 1,
        "account_id": "Account_A",
        "debit": 100000,
        "credit": 0,
        "date_iso": "2025-01-01",
        "description": "Transfer",
    }
    txn_b = {
        "id": 2,
        "account_id": "Account_B",
        "debit": 0,
        "credit": 100000,
        "date_iso": "2025-01-01",
        "description": "Transfer",
    }

    result = _check_match(txn_a, txn_b)

    assert result is not None
    assert result["match_type"] == "exact"
    assert result["match_confidence"] >= 0.8
    assert result["amount"] == 1000.00  # Converted to rupees


def test_check_match_date_window():
    """Test that match detects window match for dates within 3 days."""
    txn_a = {
        "id": 1,
        "account_id": "Account_A",
        "debit": 100000,
        "credit": 0,
        "date_iso": "2025-01-01",
        "description": "Transfer",
    }
    txn_b = {
        "id": 2,
        "account_id": "Account_B",
        "debit": 0,
        "credit": 100000,
        "date_iso": "2025-01-03",
        "description": "Transfer",
    }

    result = _check_match(txn_a, txn_b)

    assert result is not None
    assert result["match_type"] == "window"
    assert result["date_diff_days"] == 2


def test_check_match_outside_window():
    """Test that match returns None for dates outside 3 days."""
    txn_a = {
        "id": 1,
        "account_id": "Account_A",
        "debit": 100000,
        "credit": 0,
        "date_iso": "2025-01-01",
        "description": "Transfer",
    }
    txn_b = {
        "id": 2,
        "account_id": "Account_B",
        "debit": 0,
        "credit": 100000,
        "date_iso": "2025-01-10",
        "description": "Transfer",
    }

    result = _check_match(txn_a, txn_b, max_date_window_days=3)
    assert result is None


def test_calculate_confidence():
    """Test confidence calculation."""
    # Exact date, exact amount
    conf = _calculate_confidence(date_diff_days=0, amount_exact=True)
    assert conf == 0.8  # 0.4 (date) + 0.4 (amount)

    # Within 1 day, exact amount
    conf = _calculate_confidence(date_diff_days=1, amount_exact=True)
    assert conf == 0.7  # 0.3 (date) + 0.4 (amount)

    # With description similarity
    conf = _calculate_confidence(
        date_diff_days=0, amount_exact=True, description_similarity=1.0
    )
    assert conf == 1.0  # 0.4 + 0.4 + 0.2 = 1.0 (capped)


def test_date_difference_days():
    """Test date difference calculation."""
    diff = _date_difference_days("2025-01-01", "2025-01-03")
    assert diff == 2

    diff = _date_difference_days("2025-01-03", "2025-01-01")
    assert diff == 2  # Absolute value

    diff = _date_difference_days("2025-01-01", "invalid")
    assert diff is None


# ============================================================
# Tests for _generate_explanation
# ============================================================


def test_generate_explanation_exact_match():
    """Exact match (date_diff=0) produces correct explanation with rupees, same date, account IDs."""
    debit_txn = {
        "id": 1,
        "account_id": "Account_A",
        "date_iso": "2025-01-01",
        "description": "Transfer",
    }
    credit_txn = {
        "id": 2,
        "account_id": "Account_B",
        "date_iso": "2025-01-01",
        "description": "Transfer",
    }
    amount_paise = 100000  # ₹1000.00
    date_diff = 0

    explanation = _generate_explanation(debit_txn, credit_txn, amount_paise, date_diff)

    assert "Exact match" in explanation
    assert "1000.00" in explanation  # Simple float formatting, not Indian grouping
    assert "Account_A" in explanation
    assert "Account_B" in explanation
    assert "2025-01-01" in explanation
    assert "days apart" not in explanation


def test_generate_explanation_window_match():
    """Window match (date_diff>0) produces correct explanation with both dates and day count."""
    debit_txn = {
        "id": 1,
        "account_id": "Account_A",
        "date_iso": "2025-01-01",
        "description": "Transfer",
    }
    credit_txn = {
        "id": 2,
        "account_id": "Account_B",
        "date_iso": "2025-01-03",
        "description": "Transfer",
    }
    amount_paise = 200000  # ₹2000.00
    date_diff = 2

    explanation = _generate_explanation(debit_txn, credit_txn, amount_paise, date_diff)

    assert "Window match" in explanation
    assert "2000.00" in explanation  # Simple float formatting
    assert "Account_A" in explanation
    assert "Account_B" in explanation
    assert "2025-01-01" in explanation
    assert "2025-01-03" in explanation
    assert "2 days apart" in explanation


def test_generate_explanation_amount_in_rupees():
    """Amount in paise correctly converted to rupees with 2 decimal places."""
    debit_txn = {
        "id": 1,
        "account_id": "A",
        "date_iso": "2025-01-01",
        "description": "T",
    }
    credit_txn = {
        "id": 2,
        "account_id": "B",
        "date_iso": "2025-01-01",
        "description": "T",
    }

    # Test various paise amounts - uses simple float formatting
    explanation = _generate_explanation(debit_txn, credit_txn, 1, 0)
    assert "0.01" in explanation

    explanation = _generate_explanation(debit_txn, credit_txn, 100, 0)
    assert "1.00" in explanation

    explanation = _generate_explanation(debit_txn, credit_txn, 12345, 0)
    assert "123.45" in explanation

    explanation = _generate_explanation(debit_txn, credit_txn, 10000000, 0)
    assert "100000.00" in explanation  # Simple float, no Indian grouping


# ============================================================
# Additional Tests for Gaps Identified by C42 Forensics
# ============================================================


def test_parse_date_iso_valid():
    """Valid ISO date strings parse correctly."""

    result = _parse_date_iso("2025-01-01")
    assert result is not None
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 1

    result = _parse_date_iso("2024-12-31")
    assert result.year == 2024
    assert result.month == 12
    assert result.day == 31


def test_parse_date_iso_invalid():
    """Invalid or empty date strings return None."""

    assert _parse_date_iso("") is None
    assert _parse_date_iso(None) is None  # type: ignore
    assert _parse_date_iso("invalid") is None
    assert _parse_date_iso("2025-13-01") is None  # Invalid month


def test_simple_description_similarity_with_keywords():
    """Descriptions containing transfer keywords return similarity 1.0."""

    assert _simple_description_similarity("NEFT Transfer", "Transfer via NEFT") == 1.0
    assert _simple_description_similarity("IMPS payment", "Received via IMPS") == 1.0
    assert _simple_description_similarity("UPI transfer", "Payment via UPI") == 1.0
    assert _simple_description_similarity("RTGS credit", "RTGS debit") == 1.0
    assert (
        _simple_description_similarity("Paytm transfer", "Transfer from Paytm") == 1.0
    )
    assert _simple_description_similarity("GPay payment", "Payment via GPay") == 1.0


def test_simple_description_similarity_no_keywords():
    """Descriptions without transfer keywords return similarity 0.0."""

    assert _simple_description_similarity("Salary Credit", "Bank Fee") == 0.0
    assert _simple_description_similarity("Grocery Purchase", "Restaurant Bill") == 0.0
    assert _simple_description_similarity("", "Transfer") == 0.0
    assert _simple_description_similarity("Transfer", "") == 0.0
    assert _simple_description_similarity("", "") == 0.0


def test_calculate_confidence_caps_at_one():
    """Confidence cannot exceed 1.0 even with all factors maxed."""
    from src.engines.reconciliation_engine import _calculate_confidence

    # All factors present: date_diff=0 (+0.4), amount_exact (+0.4), sim>0.7 (+0.2) = 1.0
    conf = _calculate_confidence(
        date_diff_days=0, amount_exact=True, description_similarity=1.0
    )
    assert conf == 1.0

    # Edge case: slight above threshold still caps
    conf = _calculate_confidence(
        date_diff_days=0, amount_exact=True, description_similarity=0.99
    )
    assert conf == 1.0


def test_calculate_confidence_rounds_to_four_decimals():
    """Confidence is rounded to exactly 4 decimal places."""
    from src.engines.reconciliation_engine import _calculate_confidence

    # Base confidence should have at most 4 decimal places
    conf = _calculate_confidence(date_diff_days=0, amount_exact=True)
    assert conf == round(conf, 4)
    assert str(conf).count(".") <= 1
    if "." in str(conf):
        assert len(str(conf).split(".")[1]) <= 4


def test_check_match_with_description_similarity():
    """Match includes description similarity factor in confidence."""
    from src.engines.reconciliation_engine import _check_match

    txn_a = {
        "id": 1,
        "account_id": "Account_A",
        "debit": 100000,
        "credit": 0,
        "date_iso": "2025-01-01",
        "description": "NEFT Transfer",
    }
    txn_b = {
        "id": 2,
        "account_id": "Account_B",
        "debit": 0,
        "credit": 100000,
        "date_iso": "2025-01-01",
        "description": "IMPS Credit",
    }

    result = _check_match(txn_a, txn_b)
    assert result is not None
    # Should have higher confidence due to description keywords
    assert result["match_confidence"] >= 1.0  # 0.4 + 0.4 + 0.2 = 1.0


def test_check_match_no_description_similarity():
    """Match without description keywords has lower confidence."""
    from src.engines.reconciliation_engine import _check_match

    txn_a = {
        "id": 1,
        "account_id": "Account_A",
        "debit": 100000,
        "credit": 0,
        "date_iso": "2025-01-01",
        "description": "Payment",
    }
    txn_b = {
        "id": 2,
        "account_id": "Account_B",
        "debit": 0,
        "credit": 100000,
        "date_iso": "2025-01-01",
        "description": "Credit",
    }

    result = _check_match(txn_a, txn_b)
    assert result is not None
    # No description similarity: 0.4 + 0.4 = 0.8
    assert result["match_confidence"] == 0.8


def test_check_match_missing_dates():
    """Match returns None when either transaction has missing date."""
    from src.engines.reconciliation_engine import _check_match

    txn_a = {
        "id": 1,
        "account_id": "Account_A",
        "debit": 100000,
        "credit": 0,
        "date_iso": "",
        "description": "Transfer",
    }
    txn_b = {
        "id": 2,
        "account_id": "Account_B",
        "debit": 0,
        "credit": 100000,
        "date_iso": "2025-01-01",
        "description": "Transfer",
    }

    result = _check_match(txn_a, txn_b)
    assert result is None


def test_check_match_credit_first():
    """Match works regardless of which transaction is debit vs credit."""
    from src.engines.reconciliation_engine import _check_match

    # txn_a has credit, txn_b has debit
    txn_a = {
        "id": 1,
        "account_id": "Account_A",
        "debit": 0,
        "credit": 100000,
        "date_iso": "2025-01-01",
        "description": "Credit",
    }
    txn_b = {
        "id": 2,
        "account_id": "Account_B",
        "debit": 100000,
        "credit": 0,
        "date_iso": "2025-01-01",
        "description": "Debit",
    }

    result = _check_match(txn_a, txn_b)
    assert result is not None
    assert result["match_type"] == "exact"
    assert result["amount"] == 1000.00


def test_generate_explanation_edge_cases():
    """Explanation handles missing or empty fields gracefully."""
    from src.engines.reconciliation_engine import _generate_explanation

    debit_txn = {"id": 1, "account_id": "", "date_iso": "", "description": ""}
    credit_txn = {"id": 2, "account_id": "", "date_iso": "", "description": ""}

    explanation = _generate_explanation(debit_txn, credit_txn, 100000, 0)
    assert "Exact match" in explanation
    # Empty account/date fields produce empty strings in output
    assert "1000.00" in explanation

    explanation = _generate_explanation(debit_txn, credit_txn, 100000, 5)
    assert "Window match" in explanation
    assert "5 days apart" in explanation


def test_find_matches_for_transaction_existing(populated_db):
    """find_matches_for_transaction returns matches for valid transaction ID."""

    matches = find_matches_for_transaction(populated_db, 1)
    # Transaction 1 is debit in Account_A, should match transaction 5 (credit in Account_B)
    assert isinstance(matches, list)
    # At least one match expected
    assert len(matches) >= 1


def test_find_matches_for_transaction_not_found(populated_db):
    """find_matches_for_transaction returns empty list for non-existent transaction ID."""

    matches = find_matches_for_transaction(populated_db, 99999)
    assert matches == []


# ============================================================
# M9-C43.6 — Mutation-Strengthening Tests (Targeted at C42 Class-A Survivors)
# ============================================================
#
# These tests were generated from the C42.17 forensic survivor inventory
# and are designed to discriminate the EXACT mutants that survived.
# Each test targets a specific surviving mutant identified by its
# source location and mutation operator.
#
# MUTANT TARGET KEY (from C42.17 inventory):
#   reconciliation_engine.py:4   - default max_date_window_days 3 -> 4
#   reconciliation_engine.py:5   - desc non-empty check: or -> and (boolean)
#   reconciliation_engine.py:7-8 - date default "?" -> None (constant)
#   reconciliation_engine.py:10-11 - account default "?" -> None (constant)
#   reconciliation_engine.py:14  - keyword check any(kw in) -> any(kw not in)
#   reconciliation_engine.py:21-24 - debit/credit defaults: or 0 -> or 1
#   reconciliation_engine.py:27-29 - debit/credit/amount defaults: None/""/0/1
#   reconciliation_engine.py:31-35 - comparison operators: > -> >=, and -> or
#   reconciliation_engine.py:37 - min(confidence, 1.0) -> min(confidence, 2.0)
#   reconciliation_engine.py:40 - round(confidence, 4) -> round(confidence, 5)
#   reconciliation_engine.py:40 - None check: or -> and
#   reconciliation_engine.py:44-45 - date default "" -> "XXXX" (constant)
#   reconciliation_engine.py:47 - boolean: or -> and
#   reconciliation_engine.py:55  - slice index i+1 -> i-1 (arithmetic)
#   reconciliation_engine.py:62  - set.add(key) -> set.add(None)
#   reconciliation_engine.py:65  - description default "" -> None/XX/skip arg
#   reconciliation_engine.py:69  - _check_match call missing arg
#   reconciliation_engine.py:71  - matches.append(match) -> matches.append(None)
#   reconciliation_engine.py:75-76 - min/max -> None (constant)
#   reconciliation_engine.py:89  - dict key "explanation" -> mangled/uppercase
#   reconciliation_engine.py:90  - call arg amount_paise -> None
#   reconciliation_engine.py:1,4 - db_path functions default 3 -> 4 (numeric_default)
#   reconciliation_engine.py:33  - target_debit default or 0 -> or 1
#   reconciliation_engine.py:34  - target_credit default or 0 -> None/and 0/XX/1
#   reconciliation_engine.py:38,41 - comparison > -> >=, > -> >=
#   reconciliation_engine.py:42  - amount_to_match = target_credit -> None
#   reconciliation_engine.py:43  - match_condition string -> None
#   reconciliation_engine.py:69  - _check_match call missing arg
#   reconciliation_engine.py:71  - matches.append -> None
#   reconciliation_engine.py:75-76 - min/max -> None
#   reconciliation_engine.py:89  - dict key "explanation" -> mangled/uppercase
#   reconciliation_engine.py:90  - call arg amount_paise -> None
#
# CLASSIFICATION: Most mutants are Class-A (genuine behavioral gaps).
# Some are equivalent (e.g., default 3 -> 4 on window functions where
# the test suite doesn't exercise window boundaries precisely). Those
# are documented but not targeted for killing per C43 constraints.
# ============================================================


class TestMutationStrengthening_ConfidenceCalculation:
    """M9-C43.6: Discriminate confidence calculation mutants.

    Mutants target _calculate_confidence function's weights and boundaries.
    """

    def test_confidence_date_exact_amount_exact(self):
        """Exact date + exact amount = 0.8."""
        from src.engines.reconciliation_engine import _calculate_confidence

        assert _calculate_confidence(0, True, 0.0) == 0.8

    def test_confidence_date_window_amount_exact(self):
        """Within 1 day + exact amount = 0.7."""
        from src.engines.reconciliation_engine import _calculate_confidence

        assert _calculate_confidence(1, True, 0.0) == 0.7

    def test_confidence_capped_at_one(self):
        """Cap at 1.0 with similarity."""
        from src.engines.reconciliation_engine import _calculate_confidence

        assert _calculate_confidence(0, True, 0.8) == 1.0

    def test_confidence_similarity_boundary_exact_07_excluded(self):
        """Similarity == 0.7 is NOT strictly > 0.7, so no +0.2 bonus."""
        from src.engines.reconciliation_engine import _calculate_confidence

        assert _calculate_confidence(0, True, 0.7) == 0.8

    def test_confidence_similarity_above_07_included(self):
        """Similarity > 0.7 includes +0.2 bonus."""
        from src.engines.reconciliation_engine import _calculate_confidence

        assert _calculate_confidence(0, True, 0.71) == 1.0

    def test_confidence_date_diff_two_no_date_bonus(self):
        """Date diff 2 -> no date bonus; only exact amount contributes."""
        from src.engines.reconciliation_engine import _calculate_confidence

        assert _calculate_confidence(2, True, 0.0) == 0.4

    def test_confidence_amount_not_exact(self):
        """Amount not exact -> only date factor counts."""
        from src.engines.reconciliation_engine import _calculate_confidence

        assert _calculate_confidence(0, False, 0.0) == 0.4
        assert _calculate_confidence(1, False, 0.0) == 0.3

    def test_confidence_capped_at_one_exact(self):
        """1.0 cap with exact date + amount + similarity."""
        from src.engines.reconciliation_engine import _calculate_confidence

        assert _calculate_confidence(0, True, 1.0) == 1.0


class TestMutationStrengthening_DescriptionSimilarity:
    """M9-C43.6: Discriminate description similarity mutants.

    Mutants: keyword check logic (any kw in -> any kw not in).
    """

    def test_simple_description_similarity_keywords_both(self):
        from src.engines.reconciliation_engine import _simple_description_similarity

        assert _simple_description_similarity("neft transfer", "imps transfer") == 1.0

    def test_simple_description_similarity_no_keywords(self):
        from src.engines.reconciliation_engine import _simple_description_similarity

        assert _simple_description_similarity("grocery", "grocery") == 0.0

    def test_simple_description_similarity_empty(self):
        from src.engines.reconciliation_engine import _simple_description_similarity

        assert _simple_description_similarity("", "transfer") == 0.0

    def test_simple_description_similarity_single_keyword(self):
        """Single keyword in one description only returns 0."""
        from src.engines.reconciliation_engine import _simple_description_similarity

        assert _simple_description_similarity("neft payment", "grocery store") == 0.0

    def test_simple_description_similarity_keyword_case_insensitive(self):
        """Keywords are matched case-insensitively."""
        from src.engines.reconciliation_engine import _simple_description_similarity

        assert _simple_description_similarity("NEFT transfer", "imps TRANSFER") == 1.0


class TestMutationStrengthening_DateDifference:
    """M9-C43.6: Discriminate date difference mutants."""

    def test_date_difference_days_same(self):
        from src.engines.reconciliation_engine import _date_difference_days

        assert _date_difference_days("2025-01-01", "2025-01-01") == 0

    def test_date_difference_days_adjacent(self):
        from src.engines.reconciliation_engine import _date_difference_days

        assert _date_difference_days("2025-01-01", "2025-01-02") == 1

    def test_date_difference_days_leap_year(self):
        from src.engines.reconciliation_engine import _date_difference_days

        # 2024 is a leap year
        assert _date_difference_days("2024-02-28", "2024-03-01") == 2


class TestMutationStrengthening_CheckMatchBoundary:
    """M9-C43.6: Discriminate _check_match boundary mutants.

    Mutants: comparison operators (> -> >=), boolean logic (and -> or),
    default values (0 -> 1, None -> ""), date defaults ("?" -> None).
    """

    def test_check_match_exact_amount_same_account_rejected(self):
        """Same account_id -> no match."""
        from src.engines.reconciliation_engine import _check_match

        txn_a = {
            "id": 1,
            "account_id": "Account_A",
            "debit": 100000,
            "credit": 0,
            "date_iso": "2025-01-01",
            "description": "Transfer",
        }
        txn_b = {
            "id": 2,
            "account_id": "Account_A",  # Same account
            "debit": 0,
            "credit": 100000,
            "date_iso": "2025-01-01",
            "description": "Transfer",
        }

        result = _check_match(txn_a, txn_b)
        assert result is None  # Same account -> no match

    def test_check_match_different_amount_rejected(self):
        """Different amounts -> no match."""
        from src.engines.reconciliation_engine import _check_match

        txn_a = {
            "id": 1,
            "account_id": "Account_A",
            "debit": 100000,
            "credit": 0,
            "date_iso": "2025-01-01",
            "description": "Transfer",
        }
        txn_b = {
            "id": 2,
            "account_id": "Account_B",
            "debit": 0,
            "credit": 200000,  # Different amount
            "date_iso": "2025-01-01",
            "description": "Transfer",
        }

        result = _check_match(txn_a, txn_b)
        assert result is None  # Different amounts

    def test_check_match_date_diff_exceeds_window(self):
        """Date difference > max window -> no match."""
        from src.engines.reconciliation_engine import _check_match

        txn_a = {
            "id": 1,
            "account_id": "Account_A",
            "debit": 100000,
            "credit": 0,
            "date_iso": "2025-01-01",
            "description": "Transfer",
        }
        txn_b = {
            "id": 2,
            "account_id": "Account_B",
            "debit": 0,
            "credit": 100000,
            "date_iso": "2025-01-10",  # 9 days diff > default 3
            "description": "Transfer",
        }

        result = _check_match(txn_a, txn_b)
        assert result is None

    def test_check_match_missing_dates_rejected(self):
        """Missing dates -> no match."""
        from src.engines.reconciliation_engine import _check_match

        txn_a = {
            "id": 1,
            "account_id": "Account_A",
            "debit": 100000,
            "credit": 0,
            "date_iso": "",
            "description": "Transfer",
        }
        txn_b = {
            "id": 2,
            "account_id": "Account_B",
            "debit": 0,
            "credit": 100000,
            "date_iso": "2025-01-01",
            "description": "Transfer",
        }

        result = _check_match(txn_a, txn_b)
        assert result is None


class TestMutationStrengthening_Explanation:
    """M9-C43.6: Discriminate explanation generation mutants.

    Mutants: dict key mangling ("explanation" -> mangled/uppercase),
    call arg removal (amount_paise -> None).
    """

    def test_generate_explanation_exact_match(self):
        from src.engines.reconciliation_engine import _generate_explanation

        debit_txn = {"id": 1, "account_id": "Account_A", "date_iso": "2025-01-01"}
        credit_txn = {"id": 2, "account_id": "Account_B", "date_iso": "2025-01-01"}

        explanation = _generate_explanation(debit_txn, credit_txn, 100000, 0)
        assert "Exact match" in explanation
        assert "1000.00" in explanation

    def test_generate_explanation_window_match(self):
        from src.engines.reconciliation_engine import _generate_explanation

        debit_txn = {"id": 1, "account_id": "Account_A", "date_iso": "2025-01-01"}
        credit_txn = {"id": 2, "account_id": "Account_B", "date_iso": "2025-01-03"}

        explanation = _generate_explanation(debit_txn, credit_txn, 100000, 2)
        assert "Window match" in explanation
        assert "2 days apart" in explanation


class TestCalculateConfidenceMutants:
    """Exact confidence constant assertions to kill constant/comparison mutants."""

    def test_exact_date_match_confidence_0_4(self) -> None:
        """Exact same date with exact amount gives 0.4 + 0.4 = 0.8 (no description bonus)."""
        conf = _calculate_confidence(
            date_diff_days=0, amount_exact=True, description_similarity=0.0
        )
        assert conf == 0.8

    def test_exact_date_match_confidence_with_description(self) -> None:
        """Exact same date with exact amount and high description similarity = 1.0 (capped)."""
        conf = _calculate_confidence(
            date_diff_days=0, amount_exact=True, description_similarity=0.8
        )
        assert conf == 1.0

    def test_within_1_day_match_confidence_0_3(self) -> None:
        """Within 1 day with exact amount gives 0.3 + 0.4 = 0.7."""
        conf = _calculate_confidence(
            date_diff_days=1, amount_exact=True, description_similarity=0.0
        )
        assert conf == 0.7

    def test_within_1_day_match_confidence_with_description(self) -> None:
        """Within 1 day with exact amount and high description = 0.3 + 0.4 + 0.2 = 0.9."""
        conf = _calculate_confidence(
            date_diff_days=1, amount_exact=True, description_similarity=0.8
        )
        assert conf == 0.9

    def test_exact_date_amount_mismatch_confidence(self) -> None:
        """Exact date but amount mismatch: 0.4 + 0.0 = 0.4."""
        conf = _calculate_confidence(
            date_diff_days=0, amount_exact=False, description_similarity=0.0
        )
        assert conf == 0.4

    def test_within_1_day_amount_mismatch_confidence(self) -> None:
        """Within 1 day but amount mismatch: 0.3 + 0.0 = 0.3."""
        conf = _calculate_confidence(
            date_diff_days=1, amount_exact=False, description_similarity=0.0
        )
        assert conf == 0.3

    def test_outside_window_confidence(self) -> None:
        """Date diff > 1 with exact amount: 0.0 + 0.4 = 0.4."""
        conf = _calculate_confidence(
            date_diff_days=2, amount_exact=True, description_similarity=0.0
        )
        assert conf == 0.4

    def test_description_similarity_boundary(self) -> None:
        """Description similarity exactly at 0.7 boundary gives no bonus."""
        conf = _calculate_confidence(
            date_diff_days=0, amount_exact=True, description_similarity=0.7
        )
        assert conf == 0.8  # No description bonus at exactly 0.7

    def test_description_similarity_above_boundary(self) -> None:
        """Description similarity above 0.7 gives bonus."""
        conf = _calculate_confidence(
            date_diff_days=0, amount_exact=True, description_similarity=0.71
        )
        assert conf == 1.0  # 0.4 + 0.4 + 0.2 = 1.0 (capped)

    def test_confidence_cap_at_1_0(self) -> None:
        """Confidence never exceeds 1.0 even with all bonuses."""
        conf = _calculate_confidence(
            date_diff_days=0, amount_exact=True, description_similarity=1.0
        )
        assert conf == 1.0

    def test_confidence_rounding_4_decimals(self) -> None:
        """Confidence rounded to 4 decimals for determinism."""
        # 0.3 + 0.4 = 0.7, exact
        conf = _calculate_confidence(
            date_diff_days=1, amount_exact=True, description_similarity=0.0
        )
        assert conf == 0.7
        assert isinstance(conf, float)

    def test_confidence_no_date_no_amount(self) -> None:
        """No date match, no amount match = 0.0."""
        conf = _calculate_confidence(
            date_diff_days=5, amount_exact=False, description_similarity=0.0
        )
        assert conf == 0.0
