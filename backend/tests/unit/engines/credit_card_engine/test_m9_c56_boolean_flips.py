"""Targeted tests for credit_card_engine boolean-operator mutation gaps.

These tests target genuine behavioral mutations where changing `or` to `and`
(or vice versa) changes the output when one parameter is zero and another is
positive.
"""

from __future__ import annotations

from datetime import date

import pytest
from src.engines.credit_card_engine.billing import _next_billing_day_after
from src.engines.credit_card_engine.emi import compute_monthly_interest
from src.engines.credit_card_engine.interest import (
    compute_daily_interest,
    compute_monthly_interest_simple,
)


class TestMonthlyInterestBooleanFlip:
    """Tests for compute_monthly_interest boolean operator mutations.

    The mutation `outstanding_paise <= 0 or annual_rate_bps <= 0` ->
    `outstanding_paise <= 0 and annual_rate_bps <= 0` survives because
    existing tests always have both parameters positive or both zero.
    """

    def test_zero_outstanding_positive_rate_returns_zero(self):
        """Zero balance with positive rate should return zero interest."""
        result = compute_monthly_interest(0, 2400)
        assert result == 0

    def test_positive_outstanding_zero_rate_returns_zero(self):
        """Positive balance with zero rate should return zero interest."""
        result = compute_monthly_interest(100000, 0)
        assert result == 0

    def test_both_positive_calculates_interest(self):
        """Both positive → interest is calculated."""
        result = compute_monthly_interest(100000, 2400)
        assert result > 0

    def test_both_zero_returns_zero(self):
        """Both zero → zero interest."""
        result = compute_monthly_interest(0, 0)
        assert result == 0

    def test_negative_balance_returns_zero(self):
        """Negative balance returns zero (not an error - per current behavior)."""
        result = compute_monthly_interest(-1000, 2400)
        assert result == 0

    def test_negative_rate_returns_zero(self):
        """Negative rate returns zero (not an error - per current behavior)."""
        result = compute_monthly_interest(100000, -100)
        assert result == 0


class TestDailyInterestBooleanFlip:
    """Tests for compute_daily_interest boolean operator mutations."""

    def test_zero_outstanding_positive_rate(self):
        """Zero balance with positive rate returns zero."""
        result = compute_daily_interest(0, 2400)
        assert result == 0

    def test_positive_outstanding_zero_rate(self):
        """Positive balance with zero rate returns zero."""
        result = compute_daily_interest(100000, 0)
        assert result == 0

    def test_both_positive_calculates(self):
        """Both positive → non-zero interest."""
        result = compute_daily_interest(100000, 2400)
        assert result > 0

    def test_interest_scales_with_rate(self):
        """Interest scales proportionally with rate."""
        r1 = compute_daily_interest(100000, 1200)
        r2 = compute_daily_interest(100000, 2400)
        assert r2 == 2 * r1


class TestMonthlyInterestSimpleBooleanFlip:
    """Tests for compute_monthly_interest_simple boolean operator mutations."""

    def test_zero_balance_positive_days(self):
        """Zero balance with positive days returns zero."""
        result = compute_monthly_interest_simple(0, 2400, 30)
        assert result == 0

    def test_positive_balance_zero_days_raises(self):
        """Zero days must raise ValueError."""
        with pytest.raises(ValueError):
            compute_monthly_interest_simple(100000, 2400, 0)

    def test_positive_balance_positive_days_calculates(self):
        """Both positive → non-zero interest."""
        result = compute_monthly_interest_simple(100000, 2400, 30)
        assert result > 0

    def test_interest_scales_with_days(self):
        """Interest scales with days in cycle."""
        d15 = compute_monthly_interest_simple(100000, 2400, 15)
        d30 = compute_monthly_interest_simple(100000, 2400, 30)
        assert d30 == 2 * d15


class TestNextBillingDayBoundary:
    """Tests for _next_billing_day_after boundary conditions."""

    def test_candidate_equal_to_start_advances(self):
        """When candidate date equals start_date, must advance one month.

        The condition `candidate > start_date` must be strict.
        Mutation to `>=` would not advance when they're equal.
        """
        # billing_day=10, start_date=June 10 → candidate=June 10
        # June 10 == June 10, so MUST advance to July 10
        result = _next_billing_day_after(date(2025, 6, 10), 10)
        assert result == date(2025, 7, 10)

    def test_candidate_after_start_returns_candidate(self):
        """When candidate is after start_date, return candidate directly."""
        # billing_day=15, start_date=June 10 → candidate=June 15
        # June 15 > June 10, so return June 15
        result = _next_billing_day_after(date(2025, 6, 10), 15)
        assert result == date(2025, 6, 15)
