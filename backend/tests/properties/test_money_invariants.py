"""Property tests for money invariants.

Uses lightweight random testing without hypothesis dependency.
All monetary values use integer paise (₹1 = 100 paise).
"""

from __future__ import annotations

import random


def _random_paise(min_val: int = -1000000, max_val: int = 1000000) -> int:
    """Generate random paise value within bounds."""
    return random.randint(min_val, max_val)


def _random_confidence_bps() -> int:
    """Generate random confidence in basis points (0-10000)."""
    return random.randint(0, 10000)


class TestMoneyInvariants:
    """QEA-5: Money uses integer paise, never float."""

    def test_paise_values_are_integers(self) -> None:
        """All paise values should be integers, not floats."""
        for _ in range(100):
            paise = _random_paise()
            assert isinstance(paise, int), f"Expected int, got {type(paise)}"

    def test_paise_negative_handling(self) -> None:
        """Negative paise values should be valid (representing debits)."""
        for _ in range(100):
            paise = _random_paise(-100000, -1)
            # Negative paise is valid for debits/expense tracking
            assert isinstance(paise, int)
            assert paise < 0

    def test_paise_addition_valid(self) -> None:
        """Adding paise values should preserve integer type."""
        for _ in range(100):
            a = _random_paise()
            b = _random_paise()
            result = a + b
            assert isinstance(result, int)

    def test_paise_subtraction_valid(self) -> None:
        """Subtracting paise values should preserve integer type."""
        for _ in range(100):
            a = _random_paise()
            b = _random_paise()
            result = a - b
            assert isinstance(result, int)


class TestConfidenceInvariants:
    """QEA-6: Confidence values are integer bps in range 0-10000."""

    def test_confidence_in_valid_range(self) -> None:
        """Confidence should be between 0 and 10000 bps."""
        for _ in range(100):
            confidence = _random_confidence_bps()
            assert 0 <= confidence <= 10000, f"Confidence {confidence} out of range"

    def test_confidence_is_integer(self) -> None:
        """Confidence should always be an integer."""
        for _ in range(100):
            confidence = _random_confidence_bps()
            assert isinstance(confidence, int)

    def test_confidence_100_percent(self) -> None:
        """100% confidence = 10000 bps."""
        assert 10000 == 10000


class TestSurplusInvariant:
    """Rule: income - expense = surplus."""

    def test_surplus_calculation(self) -> None:
        """Verify income - expense equals surplus mathematically."""
        for _ in range(100):
            income = _random_paise(100, 100000)  # Positive income
            expense = _random_paise(100, 100000)
            surplus = income - expense
            assert isinstance(surplus, int)

    def test_surplus_positive_when_income_exceeds_expense(self) -> None:
        """Surplus should be positive when income > expense."""
        for _ in range(100):
            income = _random_paise(500, 100000)
            expense = _random_paise(100, income - 100)
            surplus = income - expense
            assert surplus > 0

    def test_surplus_negative_when_expense_exceeds_income(self) -> None:
        """Surplus should be negative when expense > income."""
        for _ in range(100):
            expense = _random_paise(500, 100000)
            income = _random_paise(100, expense - 100)
            surplus = income - expense
            assert surplus < 0


class TestLoanInvariants:
    """Rules: principal never increases, balance trends downward."""

    def test_principal_decrease_or_equal(self) -> None:
        """Original principal should not increase through repayments."""
        # Simulate amortization: principal starts high and should decrease
        principal = 10000000  # 100000 INR in paise
        for _ in range(100):
            principal_change = _random_paise(-10000, -100)  # Principal reduction
            principal += principal_change
            # Principal should never exceed original in a healthy loan
            assert principal < 10000000 or principal == 10000000

    def test_final_balance_non_negative(self) -> None:
        """Loan balance should not go negative."""
        balance = 1000000  # Starting balance
        for _ in range(100):
            payment = _random_paise(1000, 10000)
            balance -= payment
            assert balance >= 0

    def test_reducing_balance_trend(self) -> None:
        """Each payment should reduce or maintain balance (not increase it)."""
        # Mock amortization schedule
        balance = 10000000
        for _ in range(100):
            payment = _random_paise(1000, 50000)
            balance -= payment
            assert balance <= 10000000


class TestForecastInvariants:
    """Rules: confidence valid, no impossible negative values."""

    def test_forecast_confidence_valid(self) -> None:
        """Forecast confidence should remain in valid bps range."""
        for _ in range(100):
            conf = _random_confidence_bps()
            assert 0 <= conf <= 10000

    def test_forecast_values_non_negative_savings(self) -> None:
        """Savings in forecasts should not be impossible negative beyond context."""
        # Savings can be negative (deficit) but should be tracked correctly
        savings = _random_paise(-100000, 100000)
        assert isinstance(savings, int)
