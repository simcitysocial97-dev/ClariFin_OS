"""
Test Suite for Validation Engine
==================================

Tests for:
1. Delta == 0 for balanced statement
2. Delta non-zero for mismatch
3. Edge cases (0 transactions, negative values, empty lists)
4. is_statement_balanced with and without tolerance
5. compute_statement_summary correctness

Run: python -m pytest tests/test_validation_engine.py -v
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.validation_engine import (
    compute_statement_delta_paise,
    is_statement_balanced,
    compute_statement_summary,
)


# ============================================================
# Test 1: Balanced Statement (Delta == 0)
# ============================================================

def test_balanced_statement_perfect_match():
    """Test that a perfectly balanced statement returns delta = 0."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=100000,   # ₹1000.00
        closing_balance_paise=50000,    # ₹500.00
        credits_paise=[200000],          # ₹2000.00 in
        debits_paise=[250000],           # ₹2500.00 out
    )
    # Expected: 1000 + 2000 - 2500 = 500, delta = 500 - 500 = 0
    assert delta == 0


def test_balanced_statement_multiple_transactions():
    """Test balanced statement with multiple credits and debits."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=50000,    # ₹500.00
        closing_balance_paise=75000,    # ₹750.00
        credits_paise=[100000, 50000],   # ₹1000 + ₹500 = ₹1500 in
        debits_paise=[75000, 50000],     # ₹750 + ₹500 = ₹1250 out
    )
    # Expected: 500 + 1500 - 1250 = 750, delta = 750 - 750 = 0
    assert delta == 0


def test_balanced_statement_only_credits():
    """Test statement with only credits (no debits)."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=0,
        closing_balance_paise=50000,    # ₹500.00
        credits_paise=[30000, 20000],    # ₹300 + ₹200 = ₹500 in
        debits_paise=[],                 # No debits
    )
    # Expected: 0 + 500 - 0 = 500, delta = 500 - 500 = 0
    assert delta == 0


def test_balanced_statement_only_debits():
    """Test statement with only debits (no credits)."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=100000,   # ₹1000.00
        closing_balance_paise=40000,    # ₹400.00
        credits_paise=[],                # No credits
        debits_paise=[30000, 30000],     # ₹300 + ₹300 = ₹600 out
    )
    # Expected: 1000 - 600 = 400, delta = 400 - 400 = 0
    assert delta == 0


# ============================================================
# Test 2: Mismatch Statement (Delta Non-Zero)
# ============================================================

def test_mismatch_positive_delta():
    """Test positive delta (expected closing > actual closing - missing money)."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=100000,   # ₹1000.00
        closing_balance_paise=40000,    # ₹400.00 (less than expected)
        credits_paise=[200000],          # ₹2000.00 in
        debits_paise=[250000],           # ₹2500.00 out
    )
    # Expected: 1000 + 2000 - 2500 = 500
    # Actual closing: 400
    # Delta: 500 - 400 = 100 (positive means missing money)
    assert delta == 10000  # ₹100.00


def test_mismatch_negative_delta():
    """Test negative delta (expected closing < actual closing - extra money)."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=100000,   # ₹1000.00
        closing_balance_paise=60000,    # ₹600.00 (more than expected)
        credits_paise=[200000],          # ₹2000.00 in
        debits_paise=[250000],           # ₹2500.00 out
    )
    # Expected: 1000 + 2000 - 2500 = 500
    # Actual closing: 600
    # Delta: 500 - 600 = -100 (negative means extra money)
    assert delta == -10000  # -₹100.00


def test_mismatch_large_discrepancy():
    """Test large discrepancy amount."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=1000000,   # ₹10000.00
        closing_balance_paise=0,          # ₹0 (completely off)
        credits_paise=[500000],           # ₹5000.00 in
        debits_paise=[200000],            # ₹2000.00 out
    )
    # Expected: 10000 + 5000 - 2000 = 13000
    # Actual closing: 0
    # Delta: 13000 - 0 = 13000
    assert delta == 1300000  # ₹13000.00


# ============================================================
# Test 3: Edge Cases
# ============================================================

def test_zero_transactions():
    """Test with no transactions (empty credits and debits)."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=50000,    # ₹500.00
        closing_balance_paise=50000,    # ₹500.00
        credits_paise=[],                # No credits
        debits_paise=[],                 # No debits
    )
    # Expected: 500 + 0 - 0 = 500, delta = 500 - 500 = 0
    assert delta == 0


def test_zero_opening_balance():
    """Test with zero opening balance."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=0,
        closing_balance_paise=25000,    # ₹250.00
        credits_paise=[50000],           # ₹500.00 in
        debits_paise=[25000],            # ₹250.00 out
    )
    # Expected: 0 + 500 - 250 = 250, delta = 250 - 250 = 0
    assert delta == 0


def test_zero_closing_balance():
    """Test with zero closing balance (account emptied)."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=100000,   # ₹1000.00
        closing_balance_paise=0,          # ₹0
        credits_paise=[],                  # No credits
        debits_paise=[100000],            # ₹1000.00 out (emptied)
    )
    # Expected: 1000 + 0 - 1000 = 0, delta = 0 - 0 = 0
    assert delta == 0


def test_empty_lists_vs_zero():
    """Test that empty lists are handled same as no transactions."""
    delta_empty = compute_statement_delta_paise(
        opening_balance_paise=50000,
        closing_balance_paise=50000,
        credits_paise=[],
        debits_paise=[],
    )
    # Should also work without passing the lists (defaults would be needed in signature)
    # But with explicit empty lists:
    assert delta_empty == 0


def test_large_transaction_count():
    """Test with many transactions."""
    credits = [1000] * 1000  # 1000 transactions of ₹10 each = ₹10000
    debits = [1000] * 1000   # 1000 transactions of ₹10 each = ₹10000

    delta = compute_statement_delta_paise(
        opening_balance_paise=50000,    # ₹500.00
        closing_balance_paise=50000,    # ₹500.00 (same opening/closing)
        credits_paise=credits,
        debits_paise=debits,
    )
    # Expected: 500 + 10000 - 10000 = 500, delta = 500 - 500 = 0
    assert delta == 0


def test_single_credit():
    """Test with a single credit transaction."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=0,
        closing_balance_paise=50000,    # ₹500.00
        credits_paise=[50000],           # ₹500.00 in
        debits_paise=[],                 # No debits
    )
    assert delta == 0


def test_single_debit():
    """Test with a single debit transaction."""
    delta = compute_statement_delta_paise(
        opening_balance_paise=100000,   # ₹1000.00
        closing_balance_paise=50000,    # ₹500.00
        credits_paise=[],                # No credits
        debits_paise=[50000],            # ₹500.00 out
    )
    # Expected: 1000 - 500 = 500, delta = 500 - 500 = 0
    assert delta == 0


# ============================================================
# Test 4: is_statement_balanced with Tolerance
# ============================================================

def test_is_balanced_exact():
    """Test is_statement_balanced with exact match."""
    result = is_statement_balanced(
        opening_balance_paise=100000,
        closing_balance_paise=50000,
        credits_paise=[200000],
        debits_paise=[250000],
    )
    assert result is True


def test_is_balanced_with_tolerance():
    """Test is_statement_balanced within tolerance."""
    # ₹1.00 discrepancy
    result = is_statement_balanced(
        opening_balance_paise=100000,
        closing_balance_paise=50100,    # ₹1.00 more than expected
        credits_paise=[200000],
        debits_paise=[250000],
        tolerance_paise=100,             # Allow ₹1.00 tolerance
    )
    assert result is True


def test_is_balanced_outside_tolerance():
    """Test is_statement_balanced outside tolerance."""
    # ₹10.00 discrepancy
    result = is_statement_balanced(
        opening_balance_paise=100000,
        closing_balance_paise=60000,    # ₹10.00 more than expected
        credits_paise=[200000],
        debits_paise=[250000],
        tolerance_paise=500,             # Only allow ₹5.00 tolerance
    )
    assert result is False


def test_is_balanced_zero_tolerance():
    """Test is_statement_balanced with zero tolerance (exact match required)."""
    # Slight discrepancy
    result = is_statement_balanced(
        opening_balance_paise=100000,
        closing_balance_paise=50100,    # ₹1.00 off
        credits_paise=[200000],
        debits_paise=[250000],
        tolerance_paise=0,               # No tolerance
    )
    assert result is False


# ============================================================
# Test 5: compute_statement_summary
# ============================================================

def test_summary_balanced():
    """Test summary for balanced statement."""
    summary = compute_statement_summary(
        opening_balance_paise=100000,
        closing_balance_paise=50000,
        credits_paise=[200000],
        debits_paise=[250000],
    )

    assert summary["opening_balance_paise"] == 100000
    assert summary["closing_balance_paise"] == 50000
    assert summary["total_credits_paise"] == 200000
    assert summary["total_debits_paise"] == 250000
    assert summary["transaction_count"] == 2
    assert summary["expected_closing_paise"] == 50000
    assert summary["delta_paise"] == 0
    assert summary["is_balanced"] is True


def test_summary_unbalanced():
    """Test summary for unbalanced statement."""
    summary = compute_statement_summary(
        opening_balance_paise=100000,
        closing_balance_paise=60000,    # Wrong closing
        credits_paise=[200000],
        debits_paise=[250000],
    )

    assert summary["opening_balance_paise"] == 100000
    assert summary["closing_balance_paise"] == 60000
    assert summary["total_credits_paise"] == 200000
    assert summary["total_debits_paise"] == 250000
    assert summary["transaction_count"] == 2
    assert summary["expected_closing_paise"] == 50000
    assert summary["delta_paise"] == -10000  # -₹100.00
    assert summary["is_balanced"] is False


def test_summary_empty():
    """Test summary with no transactions."""
    summary = compute_statement_summary(
        opening_balance_paise=50000,
        closing_balance_paise=50000,
        credits_paise=[],
        debits_paise=[],
    )

    assert summary["opening_balance_paise"] == 50000
    assert summary["closing_balance_paise"] == 50000
    assert summary["total_credits_paise"] == 0
    assert summary["total_debits_paise"] == 0
    assert summary["transaction_count"] == 0
    assert summary["expected_closing_paise"] == 50000
    assert summary["delta_paise"] == 0
    assert summary["is_balanced"] is True


def test_summary_multiple_transactions():
    """Test summary with multiple credits and debits."""
    summary = compute_statement_summary(
        opening_balance_paise=0,
        closing_balance_paise=0,
        credits_paise=[10000, 20000, 30000],  # ₹100 + ₹200 + ₹300 = ₹600
        debits_paise=[15000, 15000, 30000],   # ₹150 + ₹150 + ₹300 = ₹600
    )

    assert summary["total_credits_paise"] == 60000
    assert summary["total_debits_paise"] == 60000
    assert summary["transaction_count"] == 6
    assert summary["expected_closing_paise"] == 0
    assert summary["is_balanced"] is True


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
