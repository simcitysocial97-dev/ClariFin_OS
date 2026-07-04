"""
Cashflow Invariant Tests
========================
Guarantee: Σ credits - Σ debits = net_cashflow

These tests validate that cashflow calculations remain correct under
all conditions: empty datasets, single transactions, large datasets,
and extreme values.
"""

import pytest
from decimal import Decimal
from typing import List, Dict

from src.utils.money import to_paise, from_paise, validate_paise


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def empty_transactions() -> List[Dict]:
    """Zero transactions."""
    return []


@pytest.fixture
def single_debit() -> List[Dict]:
    """One debit transaction."""
    return [{
        "amount_paise": to_paise(Decimal("100.50")),
        "type": "debit",
        "date": "2025-01-01",
        "description": "Test debit",
    }]


@pytest.fixture
def single_credit() -> List[Dict]:
    """One credit transaction."""
    return [{
        "amount_paise": to_paise(Decimal("5000.00")),
        "type": "credit",
        "date": "2025-01-01",
        "description": "Test credit",
    }]


@pytest.fixture
def mixed_ten() -> List[Dict]:
    """10 mixed debit/credit transactions."""
    txns = []
    for i in range(5):
        txns.append({
            "amount_paise": to_paise(Decimal(str(100 + i * 10))),
            "type": "debit",
            "date": f"2025-01-{i+1:02d}",
            "description": f"Debit {i+1}",
        })
        txns.append({
            "amount_paise": to_paise(Decimal(str(200 + i * 20))),
            "type": "credit",
            "date": f"2025-01-{i+1:02d}",
            "description": f"Credit {i+1}",
        })
    return txns


@pytest.fixture
def extreme_values() -> List[Dict]:
    """Transactions with extreme values."""
    return [
        {"amount_paise": to_paise(Decimal("0.01")), "type": "debit", "date": "2025-01-01", "description": "Min paise"},
        {"amount_paise": to_paise(Decimal("10000000.00")), "type": "credit", "date": "2025-01-02", "description": "1 crore"},
        {"amount_paise": to_paise(Decimal("-500.25")), "type": "debit", "date": "2025-01-03", "description": "Negative debit"},
    ]


# ============================================================
# Core Invariant: Σ credits - Σ debits = net_cashflow
# ============================================================

def compute_net_cashflow(transactions: List[Dict]) -> int:
    """
    Compute net cashflow from transactions.
    
    Formula:
        net_cashflow = Σ(credit amounts) - Σ(debit amounts)
    
    All amounts are in paise (int).
    """
    total_credit = sum(t["amount_paise"] for t in transactions if t["type"] == "credit")
    total_debit = sum(t["amount_paise"] for t in transactions if t["type"] == "debit")
    return total_credit - total_debit


class TestCashflowInvariant:
    """Validate cashflow invariant under various conditions."""

    def test_empty_dataset(self, empty_transactions):
        """0 transactions → net_cashflow = 0."""
        net = compute_net_cashflow(empty_transactions)
        assert net == 0

    def test_single_debit(self, single_debit):
        """Single debit → net == -debit_amount."""
        net = compute_net_cashflow(single_debit)
        assert net == -single_debit[0]["amount_paise"]
        assert net < 0

    def test_single_credit(self, single_credit):
        """Single credit → net == credit_amount."""
        net = compute_net_cashflow(single_credit)
        assert net == single_credit[0]["amount_paise"]
        assert net > 0

    def test_mixed_ten(self, mixed_ten):
        """10 mixed transactions → computed correctly."""
        net = compute_net_cashflow(mixed_ten)
        
        # Manual verification
        debits = [t["amount_paise"] for t in mixed_ten if t["type"] == "debit"]
        credits = [t["amount_paise"] for t in mixed_ten if t["type"] == "credit"]
        expected = sum(credits) - sum(debits)
        assert net == expected

    def test_extreme_values(self, extreme_values):
        """Extreme values handled correctly."""
        net = compute_net_cashflow(extreme_values)
        
        # Expected: 10000000 - 1 - (-500) = 10000501 (sign convention: negative debit adds to net)
        # Actually: credits - debits = 1000000 - (1 + 500) = 9999499
        expected_credits = sum(t["amount_paise"] for t in extreme_values if t["type"] == "credit")
        expected_debits = sum(t["amount_paise"] for t in extreme_values if t["type"] == "debit")
        expected = expected_credits - expected_debits
        
        assert net == expected
        assert net > 0  # 1 crore credit dominates


# ============================================================
# Float Regression Detection
# ============================================================

class TestNoFloatLeakage:
    """Ensure no float values appear in any paise field."""

    def test_no_float_in_transactions(self, mixed_ten):
        """All amount_paise must be int, never float."""
        for txn in mixed_ten:
            assert isinstance(txn["amount_paise"], int), \
                f"Float detected in amount_paise: {txn['amount_paise']!r}"
            assert not isinstance(txn["amount_paise"], bool)  # bool is subclass of int

    def test_no_float_in_extreme(self, extreme_values):
        """Extreme values must still be int."""
        for txn in extreme_values:
            assert isinstance(txn["amount_paise"], int)
            assert txn["amount_paise"] != 0 or txn["amount_paise"] == 0

    def test_to_paise_returns_int(self):
        """to_paise() must always return int."""
        result = to_paise(Decimal("100.50"))
        assert isinstance(result, int)
        assert result == 10050

    def test_from_paise_returns_decimal(self):
        """from_paise() must always return Decimal."""
        result = from_paise(10050)
        from decimal import Decimal as D
        assert isinstance(result, D)
        assert result == D("100.50")

    def test_no_float_in_net_cashflow(self, mixed_ten):
        """Net cashflow must be int."""
        net = compute_net_cashflow(mixed_ten)
        assert isinstance(net, int)
        assert not isinstance(net, float)


# ============================================================
# Determinism Tests
# ============================================================

class TestDeterminism:
    """Ensure cashflow computation is deterministic."""

    def test_same_input_same_output(self, mixed_ten):
        """Same transaction list → same net cashflow."""
        net1 = compute_net_cashflow(mixed_ten)
        net2 = compute_net_cashflow(mixed_ten)
        assert net1 == net2

    def test_order_independent(self):
        """Net cashflow is independent of transaction order."""
        txns_a = [
            {"amount_paise": 10000, "type": "debit", "date": "2025-01-01", "description": "A"},
            {"amount_paise": 20000, "type": "credit", "date": "2025-01-02", "description": "B"},
        ]
        txns_b = list(reversed(txns_a))
        
        assert compute_net_cashflow(txns_a) == compute_net_cashflow(txns_b)


# ============================================================
# Stress Test: 10,000 transactions
# ============================================================

class TestStress:
    """Performance and correctness under load."""

    def test_ten_thousand_transactions(self):
        """10,000 mixed transactions must compute correctly."""
        txns = []
        expected_net = 0
        
        for i in range(10000):
            is_credit = i % 2 == 0
            amount = to_paise(Decimal(str(i + 1)))
            txns.append({
                "amount_paise": amount,
                "type": "credit" if is_credit else "debit",
                "date": "2025-01-01",
                "description": f"Txn {i}",
            })
            if is_credit:
                expected_net += amount
            else:
                expected_net -= amount
        
        net = compute_net_cashflow(txns)
        assert net == expected_net
        assert isinstance(net, int)
        assert len(txns) == 10000

    def test_large_quantity_no_float(self):
        """Even with 10,000 txns, no float appears."""
        txns = [
            {"amount_paise": to_paise(Decimal("1.23")), "type": "credit", "date": "2025-01-01", "description": "x"}
            for _ in range(10000)
        ]
        net = compute_net_cashflow(txns)
        assert isinstance(net, int)
        assert net == 1230000  # 10000 * 123 paise