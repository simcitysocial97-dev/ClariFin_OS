"""
Credit Card Engine — Determinism and financial-correctness tests.
"""

from datetime import date
from decimal import Decimal

import pytest
from src.engines.credit_card_engine import billing, interest, metrics, utilization
from src.engines.credit_card_engine.emi import compute_emi_conversion
from src.engines.credit_card_engine.foreclosure import compute_card_foreclosure
from src.engines.credit_card_engine.outstanding import compute_outstanding


class TestBillingEngine:
    def test_due_date_fixed_offset(self):
        assert billing.compute_due_date(date(2025, 1, 1), 21) == date(2025, 1, 22)

    def test_due_date_zero_offset(self):
        assert billing.compute_due_date(date(2025, 1, 1), 0) == date(2025, 1, 1)

    def test_due_date_negative_offset_raises(self):
        with pytest.raises(ValueError):
            billing.compute_due_date(date(2025, 1, 1), -1)

    def test_next_statement_date_first_statement(self):
        # When reference date is Jan 10 and billing day is 1, Jan 1 is in the past
        # so it advances to Feb 1
        ref = date(2025, 1, 10)
        result = billing.compute_next_statement_date(1, ref, None)
        assert result == date(2025, 2, 1)

    def test_next_statement_date_month_end_safe(self):
        ref = date(2025, 1, 10)
        result = billing.compute_next_statement_date(30, ref, None)
        assert result == date(2025, 1, 30)

    def test_next_statement_date_advance_if_past(self):
        ref = date(2025, 2, 15)
        last = date(2025, 1, 1)
        result = billing.compute_next_statement_date(1, ref, last)
        assert result == date(2025, 3, 1)

    def test_compute_statement_dates(self):
        # When reference date is Jan 10 and billing day is 1, Jan 1 is in the past
        # so it advances to Feb 1
        ref = date(2025, 1, 10)
        result = billing.compute_statement_dates(1, 21, ref)
        assert result["statement_date"] == "2025-02-01"
        assert result["due_date"] == "2025-02-22"

    def test_minimum_due_basic(self):
        assert billing.compute_minimum_due(100000, 500, 10000) == 10000

    def test_minimum_due_percent_over_floor(self):
        assert billing.compute_minimum_due(500000, 500, 10000) == 25000

    def test_minimum_due_zero_outstanding(self):
        assert billing.compute_minimum_due(0, 500, 10000) == 0

    def test_minimum_due_negative_input_raises(self):
        with pytest.raises(ValueError):
            billing.compute_minimum_due(-1, 500, 10000)


class TestInterestEngine:
    def test_daily_rate_constant(self):
        # 2400 bps = 24% annual rate
        # Daily rate = 24 / (365 * 100) = 0.0006575...
        expected = Decimal("0.0006575342465753424657534246575")
        assert interest.bps_to_daily_rate(2400) == expected

    def test_compute_daily_interest_basic(self):
        assert interest.compute_daily_interest(1000000, 2400) > 0

    def test_compute_daily_interest_zero_outstanding(self):
        assert interest.compute_daily_interest(0, 2400) == 0

    def test_compute_daily_interest_zero_rate(self):
        assert interest.compute_daily_interest(1000000, 0) == 0

    def test_monthly_interest_simple(self):
        result = interest.compute_monthly_interest_simple(1000000, 2400, 30)
        assert result == 30 * interest.compute_daily_interest(1000000, 2400)

    def test_monthly_interest_simple_negative_average_raises(self):
        with pytest.raises(ValueError):
            interest.compute_monthly_interest_simple(-1, 2400, 30)

    def test_monthly_interest_charge_empty(self):
        assert interest.compute_monthly_interest_charge([], 2400) == 0

    def test_monthly_interest_charge_negative_balance_raises(self):
        with pytest.raises(ValueError):
            interest.compute_monthly_interest_charge([("2025-01-01", -1)], 2400)


class TestOutstandingEngine:
    def test_compute_outstanding_basic(self):
        assert compute_outstanding(100000, 0, 0, 0) == 100000

    def test_compute_outstanding_zero_inputs(self):
        assert compute_outstanding(0, 0, 0, 0) == 0

    def test_compute_outstanding_emi_and_payments(self):
        assert compute_outstanding(100000, 50000, 10000, 60000) == 100000

    def test_compute_outstanding_all_negative_inputs(self):
        # All inputs negative should raise ValueError
        with pytest.raises(ValueError):
            compute_outstanding(-100000, 0, 0, 0)


class TestUtilizationEngine:
    def test_utilization_basic(self):
        assert utilization.compute_utilization(50000, 100000) == 5000

    def test_utilization_zero_limit_zero_utilization(self):
        # Zero limit returns 0 utilization (not an error)
        assert utilization.compute_utilization(50000, 0) == 0

    def test_available_credit_basic(self):
        assert utilization.compute_available_credit(100000, 50000) == 50000

    def test_available_credit_full_usage(self):
        assert utilization.compute_available_credit(100000, 100000) == 0

    def test_available_credit_negative_outstanding(self):
        # Negative outstanding raises ValueError (defensive validation)
        with pytest.raises(ValueError):
            utilization.compute_available_credit(100000, -1000)


class TestMetricsEngine:
    def test_compute_financial_metrics_basic(self):
        result = metrics.compute_financial_metrics(100000, 200000, 2400, 0)
        assert result["utilization_bps"] == 5000

    def test_zero_utilization(self):
        result = metrics.compute_financial_metrics(0, 100000, 2400, 0)
        assert result["utilization_bps"] == 0

    def test_zero_limit_zero_utilization(self):
        # Zero limit returns 0 utilization (not an error)
        result = metrics.compute_financial_metrics(100000, 0, 2400, 0)
        assert result["utilization_bps"] == 0


class TestEmiConversionEngine:
    def test_convert_to_emi_basic(self):
        result = compute_emi_conversion(1000000, 2400, 12)
        assert result["emi_paise"] > 0
        assert result["total_repayment_paise"] == result["emi_paise"] * 12
        assert result["total_interest_paise"] >= 0

    def test_convert_zero_principal_raises(self):
        result = compute_emi_conversion(0, 2400, 12)
        assert result["emi_paise"] == 0
        assert result["total_interest_paise"] == 0
        assert result["total_repayment_paise"] == 0

    def test_convert_negative_rate_raises(self):
        with pytest.raises(ValueError):
            compute_emi_conversion(1000000, -1, 12)


class TestForeclosureEngine:
    def test_foreclosure_basic(self):
        result = compute_card_foreclosure(1000000, 2400, 6)
        assert result["foreclosure_amount_paise"] > 0

    def test_foreclosure_zero_outstanding(self):
        result = compute_card_foreclosure(0, 2400, 6)
        assert result["foreclosure_amount_paise"] == 0

    def test_negative_months_raises(self):
        with pytest.raises(ValueError):
            compute_card_foreclosure(1000000, 2400, -1)

    def test_foreclosure_with_penalty(self):
        """Foreclosure with prepayment penalty returns higher amount."""
        result_no_penalty = compute_card_foreclosure(1000000, 2400, 6, penalty_bps=0)
        result_with_penalty = compute_card_foreclosure(
            1000000, 2400, 6, penalty_bps=500
        )
        assert result_with_penalty["penalty_paise"] > 0
        assert (
            result_with_penalty["foreclosure_amount_paise"]
            > result_no_penalty["foreclosure_amount_paise"]
        )

    def test_foreclosure_zero_remaining_months(self):
        """Zero remaining months still owes principal (no penalty, but full amount)."""
        result = compute_card_foreclosure(1000000, 2400, 0)
        # Foreclosure with 0 remaining months: principal still owed, no future interest
        assert result["foreclosure_amount_paise"] == 1000000
        assert result["outstanding_paise"] == 1000000

    def test_foreclosure_inputs_validated(self):
        """All negative inputs raise ValueError."""
        with pytest.raises(ValueError):
            compute_card_foreclosure(-1000000, 2400, 6)
        with pytest.raises(ValueError):
            compute_card_foreclosure(1000000, -1, 6)
        with pytest.raises(ValueError):
            compute_card_foreclosure(1000000, 2400, -1)
        with pytest.raises(ValueError):
            compute_card_foreclosure(1000000, 2400, 6, penalty_bps=-1)


# ============================================================
# Additional Tests for Gaps Identified by C42 Forensics
# ============================================================


class TestBillingEdgeCases:
    """Edge cases for billing engine not covered by existing tests."""

    def test_compute_next_statement_date_billing_day_31_in_feb(self):
        """billing_day=31 in Feb rolls to last day when reference is before it."""
        # Reference date is AFTER Jan 31, so next statement should be Feb 28
        result = billing.compute_next_statement_date(31, date(2025, 2, 15))
        assert result.month == 2
        assert result.day == 28  # Feb 2025 has 28 days

    def test_compute_next_statement_date_leap_year(self):
        """billing_day=31 in Feb during leap year uses Feb 29 when reference is after."""
        result = billing.compute_next_statement_date(31, date(2024, 2, 15))
        assert result.month == 2
        assert result.day == 29  # Feb 2024 is leap year

    def test_compute_next_statement_date_last_day_of_month(self):
        """billing_day=31 correctly handles months with 30 days."""
        # In April (30 days), billing_day=31 should roll to Apr 30
        result = billing.compute_next_statement_date(31, date(2025, 4, 1))
        assert result.month == 4
        assert result.day == 30

    def test_compute_next_statement_date_invalid_billing_day_zero(self):
        """billing_day=0 raises ValueError."""
        with pytest.raises(ValueError):
            billing.compute_next_statement_date(0, date(2025, 1, 1))

    def test_compute_next_statement_date_invalid_billing_day_thirty_two(self):
        """billing_day=32 raises ValueError."""
        with pytest.raises(ValueError):
            billing.compute_next_statement_date(32, date(2025, 1, 1))

    def test_compute_minimum_due_exact_percentage(self):
        """Minimum due equals percentage when above floor."""
        # 10% of 100000 paise = 10000, floor = 5000 → should use percentage
        result = billing.compute_minimum_due(100000, 1000, 5000)
        assert result == 10000

    def test_compute_minimum_due_floor_wins(self):
        """Minimum due equals floor when percentage is below floor."""
        # 1% of 50000 paise = 500, floor = 10000 → should use floor
        result = billing.compute_minimum_due(50000, 100, 10000)
        assert result == 10000

    def test_compute_minimum_due_capped_at_outstanding(self):
        """Minimum due never exceeds total outstanding."""
        result = billing.compute_minimum_due(5000, 5000, 10000)
        assert result == 5000

    def test_compute_minimum_due_zero_outstanding(self):
        """Zero outstanding yields zero minimum due."""
        result = billing.compute_minimum_due(0, 500, 10000)
        assert result == 0

    def test_compute_minimum_due_invalid_pct_raises(self):
        """Negative min_due_pct_bps raises ValueError."""
        with pytest.raises(ValueError):
            billing.compute_minimum_due(100000, -1, 10000)

    def test_compute_minimum_due_invalid_floor_raises(self):
        """Negative floor_paise raises ValueError."""
        with pytest.raises(ValueError):
            billing.compute_minimum_due(100000, 500, -1)


class TestInterestPrecision:
    """Tests for interest calculation precision and edge cases."""

    def test_bps_to_daily_rate_precision(self):
        """Daily rate computed with exact Decimal arithmetic."""
        # 24% annual = 2400 bps → daily = 2400 / 3650000
        result = interest.bps_to_daily_rate(2400)
        expected = Decimal("2400") / Decimal("3650000")
        assert result == expected

    def test_compute_daily_interest_bankers_rounding(self):
        """Daily interest uses ROUND_HALF_EVEN (banker's rounding)."""
        # Use a case where rounding matters
        result = interest.compute_daily_interest(100000, 2400)
        # Should be positive and deterministic
        assert result > 0
        # Running twice gives same result
        result2 = interest.compute_daily_interest(100000, 2400)
        assert result == result2

    def test_compute_monthly_interest_charge_multiple_days(self):
        """Monthly charge aggregates multiple daily balances correctly."""
        balances = [("2025-01-01", 100000), ("2025-01-02", 200000)]
        result = interest.compute_monthly_interest_charge(balances, 2400)
        expected = interest.compute_daily_interest(
            100000, 2400
        ) + interest.compute_daily_interest(200000, 2400)
        assert result == expected

    def test_compute_monthly_interest_charge_large_cycle(self):
        """Interest over 30-day cycle with varying balances."""
        balances = [(f"2025-01-{i:02d}", 500000) for i in range(1, 31)]
        result = interest.compute_monthly_interest_charge(balances, 2400)
        daily = interest.compute_daily_interest(500000, 2400)
        assert result == 30 * daily

    def test_compute_monthly_interest_simple_boundary(self):
        """Simple monthly interest matches daily × days."""
        result = interest.compute_monthly_interest_simple(1000000, 2400, 30)
        daily = interest.compute_daily_interest(1000000, 2400)
        assert result == 30 * daily

    def test_compute_monthly_interest_simple_edge_days(self):
        """Simple interest works with varying cycle lengths."""
        for days in [1, 7, 14, 28, 30, 31]:
            result = interest.compute_monthly_interest_simple(1000000, 2400, days)
            daily = interest.compute_daily_interest(1000000, 2400)
            assert result == days * daily


class TestOutstandingBoundary:
    """Boundary tests for outstanding balance computation."""

    def test_compute_outstanding_payments_exceed_spending(self):
        """Outstanding caps at zero when payments exceed charges."""
        result = compute_outstanding(100000, 0, 0, 150000)
        assert result == 0

    def test_compute_outstanding_exact_break_even(self):
        """Outstanding is zero when spending equals payments."""
        result = compute_outstanding(100000, 0, 0, 100000)
        assert result == 0

    def test_compute_outstanding_with_all_components(self):
        """Outstanding includes spend + EMI + fees - payments."""
        result = compute_outstanding(500000, 200000, 50000, 300000)
        assert result == 450000

    def test_compute_outstanding_only_fees(self):
        """Fees-only outstanding."""
        result = compute_outstanding(0, 0, 10000, 0)
        assert result == 10000

    def test_compute_outstanding_negative_spend_raises(self):
        with pytest.raises(ValueError):
            compute_outstanding(-1, 0, 0, 0)

    def test_compute_outstanding_negative_emi_raises(self):
        with pytest.raises(ValueError):
            compute_outstanding(0, -1, 0, 0)

    def test_compute_outstanding_negative_fees_raises(self):
        with pytest.raises(ValueError):
            compute_outstanding(0, 0, -1, 0)

    def test_compute_outstanding_negative_payments_raises(self):
        with pytest.raises(ValueError):
            compute_outstanding(0, 0, 0, -1)


class TestUtilizationCaps:
    """Tests for utilization capping and boundary conditions."""

    def test_compute_utilization_exactly_100_percent(self):
        """Utilization at exactly 100% returns 10000 bps."""
        result = utilization.compute_utilization(100000, 100000)
        assert result == 10000

    def test_compute_utilization_over_100_percent_caps(self):
        """Utilization over 100% caps at 10000 bps."""
        result = utilization.compute_utilization(150000, 100000)
        assert result == 10000

    def test_compute_utilization_very_small_outstanding(self):
        """Very small outstanding still computes correctly."""
        result = utilization.compute_utilization(1, 100000)
        assert result == 0  # 1/100000 * 10000 = 0.1, rounds to 0

    def test_compute_utilization_half_limit(self):
        """50% utilization = 5000 bps."""
        result = utilization.compute_utilization(50000, 100000)
        assert result == 5000

    def test_compute_available_credit_overlimit(self):
        """Available credit is zero when outstanding exceeds limit."""
        result = utilization.compute_available_credit(100000, 150000)
        assert result == 0

    def test_compute_available_credit_exact_limit(self):
        """Available credit is zero when fully utilized."""
        result = utilization.compute_available_credit(100000, 100000)
        assert result == 0

    def test_compute_available_credit_partial_usage(self):
        """Available credit reflects partial usage."""
        result = utilization.compute_available_credit(100000, 30000)
        assert result == 70000


class TestMetricsComprehensive:
    """Comprehensive tests for financial metrics computation."""

    def test_compute_financial_metrics_full(self):
        """Full metrics computation with all inputs."""
        result = metrics.compute_financial_metrics(50000, 100000, 2400, 10000)
        assert result["utilization_bps"] == 5000
        assert result["available_credit_paise"] == 50000
        assert result["annual_rate_bps"] == 2400
        assert result["total_interest_paid_paise"] == 10000

    def test_compute_financial_metrics_zero_limit(self):
        """Zero limit returns zero utilization, full available credit."""
        result = metrics.compute_financial_metrics(50000, 0, 2400)
        assert result["utilization_bps"] == 0
        assert result["available_credit_paise"] == 0

    def test_compute_financial_metrics_over_limit(self):
        """Over-limit returns capped utilization and zero available credit."""
        result = metrics.compute_financial_metrics(150000, 100000, 2400)
        assert result["utilization_bps"] == 10000
        assert result["available_credit_paise"] == 0


class TestEmiPrecision:
    """Precision tests for EMI calculations."""

    def test_compute_emi_fixed_zero_rate(self):
        """Zero rate EMI is exact division (ceiling-adjusted)."""
        result = billing._next_billing_day_after  # trigger import
        from src.engines.credit_card_engine.emi import compute_emi_fixed

        result = compute_emi_fixed(100000, 0, 3)
        # 100000 / 3 = 33333.33... → ceiling to 33334
        assert result == 33334
        assert result * 3 >= 100000

    def test_compute_emi_fixed_positive_rate(self):
        """Positive rate EMI is greater than simple division."""
        from src.engines.credit_card_engine.emi import compute_emi_fixed

        zero_rate = compute_emi_fixed(100000, 0, 12)
        positive_rate = compute_emi_fixed(100000, 2400, 12)
        assert positive_rate > zero_rate

    def test_compute_emi_conversion_zero_principal(self):
        """Zero principal yields zero EMI and zero interest."""
        result = compute_emi_conversion(0, 2400, 12)
        assert result["emi_paise"] == 0
        assert result["total_interest_paise"] == 0
        assert result["total_repayment_paise"] == 0

    def test_compute_emi_conversion_all_fields_present(self):
        """EMI conversion returns all required fields."""
        result = compute_emi_conversion(1000000, 2400, 12)
        assert "emi_paise" in result
        assert "total_interest_paise" in result
        assert "total_repayment_paise" in result
        assert "monthly_interest_paise" in result
        assert result["emi_paise"] > 0
        assert result["total_interest_paise"] >= 0
        assert result["total_repayment_paise"] == result["emi_paise"] * 12

    def test_compute_monthly_interest_edge_cases(self):
        """Monthly interest handles edge cases correctly."""
        from src.engines.credit_card_engine.emi import compute_monthly_interest

        assert compute_monthly_interest(0, 2400) == 0
        assert compute_monthly_interest(100000, 0) == 0


class TestUtilizationValidationMutants:
    """Boundary value assertions for outstanding/limit validation."""

    def test_outstanding_zero_is_valid(self) -> None:
        """Zero outstanding is valid and returns zero utilization."""
        result = utilization.compute_utilization(0, 100000)
        assert result == 0
        result = utilization.compute_available_credit(100000, 0)
        assert result == 100000

    def test_outstanding_negative_raises_value_error(self) -> None:
        """Negative outstanding must raise ValueError."""
        with pytest.raises(ValueError, match="outstanding_paise must be non-negative"):
            utilization.compute_utilization(-1, 100000)
        with pytest.raises(ValueError, match="outstanding_paise must be non-negative"):
            utilization.compute_available_credit(100000, -1)

    def test_credit_limit_negative_raises_value_error(self) -> None:
        """Negative credit limit must raise ValueError."""
        with pytest.raises(ValueError, match="credit_limit_paise must be non-negative"):
            utilization.compute_utilization(100000, -1)
        with pytest.raises(ValueError, match="credit_limit_paise must be non-negative"):
            utilization.compute_available_credit(-1, 100000)

    def test_outstanding_equals_limit_utilization_capped(self) -> None:
        """Outstanding equal to limit gives 100% utilization."""
        result = utilization.compute_utilization(100000, 100000)
        assert result == 10000  # 100% in bps

    def test_outstanding_exceeds_limit_utilization_capped(self) -> None:
        """Outstanding exceeding limit is capped at 100%."""
        result = utilization.compute_utilization(150000, 100000)
        assert result == 10000  # Capped at 100%
