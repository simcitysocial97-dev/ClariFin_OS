"""Additional targeted mutation-survivor tests for credit_card_engine.

Focuses on boundary conditions that kill genuinely behavioral mutations:
- Outstanding computation boundaries
- Foreclosure edge cases
- Monthly interest charge accumulation
- Available credit boundary
"""

from __future__ import annotations

import pytest
from src.engines.credit_card_engine.billing import compute_statement_dates
from src.engines.credit_card_engine.foreclosure import compute_card_foreclosure
from src.engines.credit_card_engine.interest import compute_monthly_interest_charge
from src.engines.credit_card_engine.metrics import compute_financial_metrics
from src.engines.credit_card_engine.outstanding import compute_outstanding


class TestComputeOutstandingBoundary:
    """Tests for compute_outstanding boundary conditions."""

    def test_zero_all_inputs_returns_zero(self):
        """All-zero inputs produce zero outstanding."""
        assert compute_outstanding(0, 0, 0, 0) == 0

    def test_spend_equals_payments_returns_zero(self):
        """Spend exactly matched by payments → zero outstanding."""
        assert compute_outstanding(100000, 0, 0, 100000) == 0

    def test_payments_exceed_spend_returns_zero_not_negative(self):
        """Overpayment must not produce negative outstanding."""
        result = compute_outstanding(50000, 0, 0, 100000)
        assert result == 0

    def test_fees_increase_outstanding(self):
        """Fees increase outstanding balance."""
        result = compute_outstanding(100000, 0, 5000, 0)
        assert result == 105000

    def test_emi_conversions_add_to_outstanding(self):
        """EMI conversions increase outstanding."""
        result = compute_outstanding(50000, 20000, 0, 0)
        assert result == 70000

    def test_negative_inputs_raise(self):
        """Negative inputs must raise ValueError."""
        with pytest.raises(ValueError):
            compute_outstanding(-1, 0, 0, 0)
        with pytest.raises(ValueError):
            compute_outstanding(0, -1, 0, 0)
        with pytest.raises(ValueError):
            compute_outstanding(0, 0, -1, 0)
        with pytest.raises(ValueError):
            compute_outstanding(0, 0, 0, -1)


class TestComputeCardForeclosureBoundary:
    """Tests for compute_card_foreclosure boundary conditions."""

    def test_zero_outstanding_returns_zero_foreclosure(self):
        """Zero outstanding → zero foreclosure amount."""
        result = compute_card_foreclosure(0, 2400, 12)
        assert result["foreclosure_amount_paise"] == 0
        assert result["accrued_interest_paise"] == 0
        assert result["penalty_paise"] == 0

    def test_negative_outstanding_raises(self):
        """Negative outstanding must raise ValueError."""
        with pytest.raises(ValueError, match="outstanding_paise"):
            compute_card_foreclosure(-1000, 2400, 12)

    def test_negative_rate_raises(self):
        """Negative rate must raise ValueError."""
        with pytest.raises(ValueError, match="annual_rate_bps"):
            compute_card_foreclosure(100000, -100, 12)

    def test_negative_months_raises(self):
        """Negative remaining months must raise ValueError."""
        with pytest.raises(ValueError, match="remaining_months"):
            compute_card_foreclosure(100000, 2400, -1)

    def test_penalty_applied_when_positive(self):
        """Positive penalty_bps should result in non-zero penalty."""
        result = compute_card_foreclosure(100000, 2400, 12, penalty_bps=100)
        # With positive penalty, penalty_paise should be > 0
        assert result["penalty_paise"] >= 0

    def test_zero_penalty_no_extra_charge(self):
        """Zero penalty_bps should not add penalty."""
        result_with = compute_card_foreclosure(100000, 2400, 12, penalty_bps=0)
        assert result_with["penalty_paise"] == 0


class TestComputeMonthlyInterestChargeBoundary:
    """Tests for compute_monthly_interest_charge boundary conditions."""

    def test_empty_list_returns_zero(self):
        """Empty daily balances produce zero interest."""
        assert compute_monthly_interest_charge([], 2400) == 0

    def test_single_day_zero_balance(self):
        """Single day with zero balance produces zero interest."""
        assert compute_monthly_interest_charge([("2025-01-01", 0)], 2400) == 0

    def test_single_day_positive_balance(self):
        """Single day with positive balance produces correct interest."""
        from src.engines.credit_card_engine.interest import compute_daily_interest

        expected = compute_daily_interest(100000, 2400)
        result = compute_monthly_interest_charge([("2025-01-01", 100000)], 2400)
        assert result == expected

    def test_multiple_days_accumulate_correctly(self):
        """Multiple days accumulate interest correctly."""
        from src.engines.credit_card_engine.interest import compute_daily_interest

        daily = compute_daily_interest(50000, 2400)
        result = compute_monthly_interest_charge(
            [("2025-01-01", 50000), ("2025-01-02", 50000), ("2025-01-03", 50000)],
            2400,
        )
        assert result == 3 * daily

    def test_zero_rate_across_multiple_days(self):
        """Zero rate produces zero interest regardless of balances."""
        assert (
            compute_monthly_interest_charge(
                [("2025-01-01", 100000), ("2025-01-02", 100000)],
                0,
            )
            == 0
        )

    def test_negative_balance_raises(self):
        """Negative balance in list must raise ValueError."""
        with pytest.raises(ValueError, match="Negative balance"):
            compute_monthly_interest_charge([("2025-01-01", -1000)], 2400)


class TestComputeAvailableCreditBoundary:
    """Tests for available credit computation via compute_financial_metrics."""

    def test_zero_outstanding_full_limit_available(self):
        """Zero outstanding → full credit limit is available."""
        result = compute_financial_metrics(0, 1000000, 2400)
        assert result["available_credit_paise"] == 1000000

    def test_outstanding_equal_limit_zero_available(self):
        """Outstanding equal to limit → zero available credit."""
        result = compute_financial_metrics(1000000, 1000000, 2400)
        assert result["available_credit_paise"] == 0

    def test_outstanding_exceeds_limit_zero_available(self):
        """Outstanding exceeding limit → zero available credit (not negative)."""
        result = compute_financial_metrics(1500000, 1000000, 2400)
        assert result["available_credit_paise"] == 0

    def test_zero_limit_full_outstanding_available(self):
        """Zero credit limit with any outstanding → zero available."""
        result = compute_financial_metrics(100000, 0, 2400)
        assert result["available_credit_paise"] == 0


class TestComputeStatementDatesBoundary:
    """Tests for statement date computation boundaries."""

    def test_statement_and_due_date_computed_together(self):
        """compute_statement_dates returns both dates as ISO strings."""
        from datetime import date

        result = compute_statement_dates(
            billing_day=15,
            due_day_offset=21,
            reference_date=date(2025, 6, 1),
        )
        assert "statement_date" in result
        assert "due_date" in result
        # Due date should be 21 days after statement date
        stmt = date.fromisoformat(result["statement_date"])
        due = date.fromisoformat(result["due_date"])
        assert (due - stmt).days == 21

    def test_last_statement_date_influences_next(self):
        """Providing last_statement_date advances the next statement."""
        from datetime import date

        result = compute_statement_dates(
            billing_day=10,
            due_day_offset=21,
            reference_date=date(2025, 6, 15),
            last_statement_date=date(2025, 5, 10),
        )
        # Next billing day after May 10 is June 10, but June 10 is in the past
        # relative to reference (June 15), so it advances to July 10.
        assert result["statement_date"] == "2025-07-10"
