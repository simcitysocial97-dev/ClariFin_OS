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
        assert result == date(2025, 2, 1)

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
        with pytest.raises(ValueError):
            compute_emi_conversion(0, 2400, 12)

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
