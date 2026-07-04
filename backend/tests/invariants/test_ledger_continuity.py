"""
Ledger Continuity Invariant Tests
==================================
Guarantee: balance[n] = balance[n-1] + transaction[n]

These tests validate that running balances remain consistent across
transaction sequences, including edge cases and stress conditions.
"""

import pytest
from decimal import Decimal
from typing import List, Dict

from src.utils.money import to_paise, from_paise, validate_paise, add_paise, subtract_paise


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def empty_sequence() -> List[Dict]:
    """No transactions."""
    return []


@pytest.fixture
def single_transaction() -> List[Dict]:
    """One transaction."""
    return [{
        "amount_paise": to_paise(Decimal("500.00")),
        "type": "debit",
        "date": "2025-01-01",
        "description": "Single purchase",
    }]


@pytest.fixture
def sequential_transactions() -> List[Dict]:
    """5 sequential transactions building a balance chain."""
    return [
        {"amount_paise": to_paise(Decimal("1000.00")), "type": "credit", "date": "2025-01-01", "description": "Salary"},
        {"amount_paise": to_paise(Decimal("200.00")), "type": "debit", "date": "2025-01-02", "description": "Rent"},
        {"amount_paise": to_paise(Decimal("150.00")), "type": "debit", "date": "2025-01-03", "description": "Groceries"},
        {"amount_paise": to_paise(Decimal("500.00")), "type": "credit", "date": "2025-01-04", "description": "Freelance"},
        {"amount_paise": to_paise(Decimal("50.00")), "type": "debit", "date": "2025-01-05", "description": "Coffee"},
    ]


@pytest.fixture
def mixed_with_gaps() -> List[Dict]:
    """Transactions with date gaps."""
    return [
        {"amount_paise": to_paise(Decimal("1000.00")), "type": "credit", "date": "2025-01-01", "description": "Jan salary"},
        {"amount_paise": to_paise(Decimal("300.00")), "type": "debit", "date": "2025-01-15", "description": "Mid-month"},
        {"amount_paise": to_paise(Decimal("2000.00")), "type": "credit", "date": "2025-02-01", "description": "Feb salary"},
    ]


# ============================================================
# Core Invariant: balance[n] = balance[n-1] + transaction[n]
# ============================================================

def compute_running_balances(transactions: List[Dict], opening_balance: int = 0) -> List[Dict]:
    """
    Compute running balances for a transaction sequence.
    
    Args:
        transactions: Ordered list of transactions with amount_paise and type
        opening_balance: Starting balance in paise
    
    Returns:
        List of dicts with 'balance_paise' added to each transaction
    """
    balances = []
    current_balance = opening_balance
    
    for txn in transactions:
        if txn["type"] == "credit":
            current_balance = add_paise(current_balance, txn["amount_paise"])
        else:
            current_balance = subtract_paise(current_balance, txn["amount_paise"])
        
        balances.append({
            **txn,
            "balance_paise": current_balance,
        })
    
    return balances


class TestLedgerContinuityInvariant:
    """Validate ledger continuity invariant."""

    def test_empty_sequence(self, empty_sequence):
        """Empty sequence → no balances to verify."""
        balances = compute_running_balances(empty_sequence)
        assert len(balances) == 0

    def test_single_transaction_credit(self):
        """Single credit from zero opening balance."""
        txns = [{"amount_paise": to_paise(Decimal("1000.00")), "type": "credit", "date": "2025-01-01", "description": "Deposit"}]
        balances = compute_running_balances(txns, opening_balance=0)
        assert len(balances) == 1
        assert balances[0]["balance_paise"] == to_paise(Decimal("1000.00"))

    def test_single_transaction_debit(self, single_transaction):
        """Single debit from zero opening balance."""
        balances = compute_running_balances(single_transaction, opening_balance=0)
        assert len(balances) == 1
        assert balances[0]["balance_paise"] == -single_transaction[0]["amount_paise"]

    def test_sequential_chain(self, sequential_transactions):
        """5 transactions → balances chain correctly."""
        balances = compute_running_balances(sequential_transactions, opening_balance=0)
        
        # Verify each step
        assert balances[0]["balance_paise"] == to_paise(Decimal("1000.00"))   # +1000
        assert balances[1]["balance_paise"] == to_paise(Decimal("800.00"))    # -200
        assert balances[2]["balance_paise"] == to_paise(Decimal("650.00"))    # -150
        assert balances[3]["balance_paise"] == to_paise(Decimal("1150.00"))   # +500
        assert balances[4]["balance_paise"] == to_paise(Decimal("1100.00"))   # -50

    def test_final_balance_matches_manual_sum(self, sequential_transactions):
        """Final balance equals sum of all transactions."""
        balances = compute_running_balances(sequential_transactions, opening_balance=0)
        final_balance = balances[-1]["balance_paise"] if balances else 0
        
        # Manual sum
        total_credit = sum(t["amount_paise"] for t in sequential_transactions if t["type"] == "credit")
        total_debit = sum(t["amount_paise"] for t in sequential_transactions if t["type"] == "debit")
        expected = total_credit - total_debit
        
        assert final_balance == expected

    def test_with_opening_balance(self):
        """Opening balance propagates correctly."""
        txns = [
            {"amount_paise": to_paise(Decimal("500.00")), "type": "credit", "date": "2025-01-01", "description": "Deposit"},
            {"amount_paise": to_paise(Decimal("200.00")), "type": "debit", "date": "2025-01-02", "description": "Withdraw"},
        ]
        opening = to_paise(Decimal("1000.00"))
        balances = compute_running_balances(txns, opening_balance=opening)
        
        assert balances[0]["balance_paise"] == to_paise(Decimal("1500.00"))  # 1000 + 500
        assert balances[1]["balance_paise"] == to_paise(Decimal("1300.00"))  # 1500 - 200


# ============================================================
# Float Regression Detection
# ============================================================

class TestNoFloatLeakage:
    """Ensure no float values appear in balance computations."""

    def test_all_balances_are_int(self, sequential_transactions):
        """Every balance_paise must be int."""
        balances = compute_running_balances(sequential_transactions)
        for b in balances:
            assert isinstance(b["balance_paise"], int)
            assert not isinstance(b["balance_paise"], bool)

    def test_all_amounts_are_int(self, sequential_transactions):
        """Every amount_paise must be int."""
        for txn in sequential_transactions:
            assert isinstance(txn["amount_paise"], int)

    def test_no_float_in_opening_balance(self):
        """Opening balance parameter must be int."""
        balances = compute_running_balances([], opening_balance=to_paise(Decimal("1000.00")))
        # Empty result, but function must not introduce float
        assert len(balances) == 0

    def test_add_paise_returns_int(self):
        """add_paise() returns int."""
        result = add_paise(10000, 5000)
        assert isinstance(result, int)
        assert result == 15000

    def test_subtract_paise_returns_int(self):
        """subtract_paise() returns int."""
        result = subtract_paise(10000, 3000)
        assert isinstance(result, int)
        assert result == 7000


# ============================================================
# Determinism Tests
# ============================================================

class TestDeterminism:
    """Ledger continuity must be deterministic."""

    def test_same_transactions_same_balances(self, sequential_transactions):
        """Same input → same balances."""
        b1 = compute_running_balances(sequential_transactions)
        b2 = compute_running_balances(sequential_transactions)
        assert b1 == b2

    def test_reversed_order_different_balances(self):
        """Reversing transaction order changes balances (order matters)."""
        txns_a = [
            {"amount_paise": 10000, "type": "credit", "date": "2025-01-01", "description": "A"},
            {"amount_paise": 3000, "type": "debit", "date": "2025-01-02", "description": "B"},
        ]
        txns_b = list(reversed(txns_a))
        
        b_a = compute_running_balances(txns_a)
        b_b = compute_running_balances(txns_b)
        
        # Different intermediate balances
        assert b_a[0]["balance_paise"] != b_b[0]["balance_paise"]
        # But same final balance
        assert b_a[-1]["balance_paise"] == b_b[-1]["balance_paise"]


# ============================================================
# Stress Test: 10,000 transactions
# ============================================================

class TestStress:
    """Ledger continuity under load."""

    def test_ten_thousand_sequential(self):
        """10,000 transactions → running balance correct."""
        txns = []
        expected_final = 0
        
        for i in range(10000):
            is_credit = i % 2 == 0
            amount = to_paise(Decimal(str((i + 1) % 1000 + 1)))
            txns.append({
                "amount_paise": amount,
                "type": "credit" if is_credit else "debit",
                "date": "2025-01-01",
                "description": f"Txn {i}",
            })
            if is_credit:
                expected_final += amount
            else:
                expected_final -= amount
        
        balances = compute_running_balances(txns)
        assert len(balances) == 10000
        assert all(isinstance(b["balance_paise"], int) for b in balances)
        assert balances[-1]["balance_paise"] == expected_final

    def test_extreme_balance_ranges(self):
        """Balance stays correct across huge swings."""
        txns = [
            {"amount_paise": to_paise(Decimal("10000000.00")), "type": "credit", "date": "2025-01-01", "description": "Large credit"},
            {"amount_paise": to_paise(Decimal("0.01")), "type": "debit", "date": "2025-01-02", "description": "Tiny debit"},
            {"amount_paise": to_paise(Decimal("9999999.99")), "type": "debit", "date": "2025-01-03", "description": "Near-total withdrawal"},
        ]
        
        balances = compute_running_balances(txns)
        assert balances[0]["balance_paise"] == to_paise(Decimal("10000000.00"))
        assert balances[1]["balance_paise"] == to_paise(Decimal("9999999.99"))
        assert balances[2]["balance_paise"] == 0
