"""
Statement Reconciliation Invariant Tests
=========================================
Guarantee: computed_closing == reported_closing

These tests validate that statement reconciliation remains correct,
ensuring that computed closing balances match reported closing balances
within acceptable tolerance, and that delta calculations are accurate.
"""

import pytest
from decimal import Decimal
from typing import List, Dict, Optional

from src.utils.money import to_paise, from_paise, validate_paise, add_paise, subtract_paise


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def empty_statement() -> Dict:
    """Empty statement with zero balances."""
    return {
        "opening_balance_paise": to_paise(Decimal("0.00")),
        "closing_balance_paise": to_paise(Decimal("0.00")),
        "transactions": [],
    }


@pytest.fixture
def balanced_statement() -> Dict:
    """Statement where computed closing == reported closing (delta = 0)."""
    return {
        "opening_balance_paise": to_paise(Decimal("1000.00")),
        "closing_balance_reported": to_paise(Decimal("1400.00")),
        "transactions": [
            {"amount_paise": to_paise(Decimal("200.00")), "type": "credit", "date": "2025-01-01"},
            {"amount_paise": to_paise(Decimal("300.00")), "type": "debit", "date": "2025-01-02"},
            {"amount_paise": to_paise(Decimal("500.00")), "type": "credit", "date": "2025-01-03"},
        ],
    }


@pytest.fixture
def unbalanced_statement() -> Dict:
    """Statement with mismatch (delta != 0)."""
    return {
        "opening_balance_paise": to_paise(Decimal("1000.00")),
        "closing_balance_reported": to_paise(Decimal("2000.00")),
        "transactions": [
            {"amount_paise": to_paise(Decimal("100.00")), "type": "credit", "date": "2025-01-01"},
        ],
    }


@pytest.fixture
def extreme_statement() -> Dict:
    """Statement with extreme values."""
    return {
        "opening_balance_paise": to_paise(Decimal("0.01")),
        "closing_balance_reported": to_paise(Decimal("10000000.00")),
        "transactions": [
            {"amount_paise": to_paise(Decimal("9999999.99")), "type": "credit", "date": "2025-01-01"},
        ],
    }


@pytest.fixture
def negative_balance_statement() -> Dict:
    """Statement with negative closing balance (overdraft)."""
    return {
        "opening_balance_paise": to_paise(Decimal("500.00")),
        "closing_balance_reported": to_paise(Decimal("-200.00")),
        "transactions": [
            {"amount_paise": to_paise(Decimal("100.00")), "type": "credit", "date": "2025-01-01"},
            {"amount_paise": to_paise(Decimal("800.00")), "type": "debit", "date": "2025-01-02"},
        ],
    }


# ============================================================
# Core Invariant: computed_closing == reported_closing
# ============================================================

def compute_closing_balance(
    opening_balance_paise: int,
    transactions: List[Dict]
) -> int:
    """
    Compute closing balance from opening balance + transactions.
    
    Formula:
        closing = opening + Σ(credits) - Σ(debits)
    
    All amounts in paise (int).
    """
    current = opening_balance_paise
    
    for txn in transactions:
        if txn["type"] == "credit":
            current = add_paise(current, txn["amount_paise"])
        else:
            current = subtract_paise(current, txn["amount_paise"])
    
    return current


def compute_delta(
    computed_closing_paise: int,
    reported_closing_paise: int
) -> int:
    """
    Compute reconciliation delta.
    
    Formula:
        delta = computed - reported
    
    Returns 0 if balanced, nonzero if mismatch.
    """
    return subtract_paise(computed_closing_paise, reported_closing_paise)


class TestStatementReconciliationInvariant:
    """Validate statement reconciliation invariants."""

    def test_empty_statement(self, empty_statement):
        """Empty statement: delta = 0."""
        computed = compute_closing_balance(
            empty_statement["opening_balance_paise"],
            empty_statement["transactions"]
        )
        delta = compute_delta(computed, empty_statement["closing_balance_paise"])
        assert delta == 0

    def test_balanced_statement(self, balanced_statement):
        """Balanced statement: computed == reported."""
        computed = compute_closing_balance(
            balanced_statement["opening_balance_paise"],
            balanced_statement["transactions"]
        )
        reported = balanced_statement["closing_balance_reported"]
        
        assert computed == reported
        assert compute_delta(computed, reported) == 0

    def test_unbalanced_statement(self, unbalanced_statement):
        """Unbalanced statement: delta != 0."""
        computed = compute_closing_balance(
            unbalanced_statement["opening_balance_paise"],
            unbalanced_statement["transactions"]
        )
        reported = unbalanced_statement["closing_balance_reported"]
        
        assert computed != reported
        assert compute_delta(computed, reported) != 0

    def test_extreme_values(self, extreme_statement):
        """Extreme values reconcile correctly."""
        computed = compute_closing_balance(
            extreme_statement["opening_balance_paise"],
            extreme_statement["transactions"]
        )
        reported = extreme_statement["closing_balance_reported"]
        
        assert computed == reported
        assert compute_delta(computed, reported) == 0

    def test_negative_balance(self, negative_balance_statement):
        """Negative closing balance handled correctly."""
        computed = compute_closing_balance(
            negative_balance_statement["opening_balance_paise"],
            negative_balance_statement["transactions"]
        )
        reported = negative_balance_statement["closing_balance_reported"]
        
        assert computed == reported
        assert computed < 0  # Overdraft

    def test_delta_sign_convention(self, balanced_statement):
        """Delta sign convention: positive = understated, negative = overstated."""
        # Modify to create understated closing (computed > reported)
        opening = balanced_statement["opening_balance_paise"]
        txns = balanced_statement["transactions"]
        computed = compute_closing_balance(opening, txns)
        reported = computed - to_paise(Decimal("100.00"))  # Reported is 100 less
        
        delta = compute_delta(computed, reported)
        assert delta > 0  # Positive delta = computed > reported = understated

    def test_single_transaction_reconciliation(self):
        """Single transaction reconciliation."""
        opening = to_paise(Decimal("1000.00"))
        txns = [{"amount_paise": to_paise(Decimal("500.00")), "type": "debit", "date": "2025-01-01"}]
        reported = to_paise(Decimal("500.00"))
        
        computed = compute_closing_balance(opening, txns)
        assert computed == reported
        assert compute_delta(computed, reported) == 0


# ============================================================
# Float Regression Detection
# ============================================================

class TestNoFloatLeakage:
    """Ensure no float values appear in reconciliation."""

    def test_computed_closing_is_int(self, balanced_statement):
        """Computed closing balance must be int."""
        computed = compute_closing_balance(
            balanced_statement["opening_balance_paise"],
            balanced_statement["transactions"]
        )
        assert isinstance(computed, int)

    def test_delta_is_int(self, balanced_statement):
        """Delta must be int."""
        computed = compute_closing_balance(
            balanced_statement["opening_balance_paise"],
            balanced_statement["transactions"]
        )
        reported = balanced_statement["closing_balance_reported"]
        delta = compute_delta(computed, reported)
        assert isinstance(delta, int)

    def test_all_transaction_amounts_are_int(self, balanced_statement):
        """All transaction amounts must be int."""
        for txn in balanced_statement["transactions"]:
            assert isinstance(txn["amount_paise"], int)


# ============================================================
# Determinism Tests
# ============================================================

class TestDeterminism:
    """Reconciliation must be deterministic."""

    def test_same_transactions_same_result(self, balanced_statement):
        """Same statement → same computed closing."""
        c1 = compute_closing_balance(
            balanced_statement["opening_balance_paise"],
            balanced_statement["transactions"]
        )
        c2 = compute_closing_balance(
            balanced_statement["opening_balance_paise"],
            balanced_statement["transactions"]
        )
        assert c1 == c2

    def test_transaction_order_matters(self):
        """Order affects intermediate balances but not final."""
        txns_a = [
            {"amount_paise": 10000, "type": "credit", "date": "2025-01-01"},
            {"amount_paise": 3000, "type": "debit", "date": "2025-01-02"},
        ]
        txns_b = list(reversed(txns_a))
        
        c_a = compute_closing_balance(0, txns_a)
        c_b = compute_closing_balance(0, txns_b)
        
        # Final balance same regardless of order
        assert c_a == c_b


# ============================================================
# Stress Test: Large statement
# ============================================================

class TestStress:
    """Reconciliation under load."""

    def test_one_hundred_transactions(self):
        """100 transactions reconcile correctly."""
        opening = to_paise(Decimal("50000.00"))
        txns = []
        expected_closing = opening
        
        for i in range(100):
            is_credit = i % 2 == 0
            amount = to_paise(Decimal(str(100 + i)))
            txns.append({
                "amount_paise": amount,
                "type": "credit" if is_credit else "debit",
                "date": "2025-01-01",
            })
            if is_credit:
                expected_closing = add_paise(expected_closing, amount)
            else:
                expected_closing = subtract_paise(expected_closing, amount)
        
        computed = compute_closing_balance(opening, txns)
        assert computed == expected_closing
        assert isinstance(computed, int)

    def test_micro_transactions(self):
        """Many tiny transactions (₹0.01 each)."""
        opening = to_paise(Decimal("100.00"))
        txns = [
            {"amount_paise": to_paise(Decimal("0.01")), "type": "debit", "date": "2025-01-01"}
            for _ in range(50)
        ]
        expected = subtract_paise(opening, to_paise(Decimal("0.50")))
        
        computed = compute_closing_balance(opening, txns)
        assert computed == expected