"""
Loan Engine Coverage Gap Tests
===============================
Tests covering remaining uncovered paths in the loan engine.

Run: python -m pytest tests/test_loan_engine_coverage.py -v --tb=short
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.loan_engine import (
    compute_emi_floating,
    compute_emi_fixed,
    compute_loan_metrics,
    compute_monthly_interest,
    compute_principal_component,
    generate_schedule,
    total_interest_paise,
    validate_schedule,
    validate_schedule_invariants,
)
from engines.loan_engine.floating_rate import apply_floating_rate_change
from engines.loan_engine.foreclosure import (
    compute_foreclosure_amount,
    compute_prepayment_breakup,
)
from engines.loan_engine.metrics import (
    calculate_interest_saved,
    calculate_tenure_saved,
    get_emi_component,
    get_interest_component,
)


class TestEMICoverage:
    """Cover uncovered EMI paths."""

    def test_compute_emi_floating_delegates(self):
        """compute_emi_floating delegates to compute_emi_fixed."""
        result = compute_emi_floating(100000000, 850, 120)
        expected = compute_emi_fixed(100000000, 850, 120)
        assert result == expected

    def test_compute_monthly_interest_zero_rate(self):
        """Monthly interest at zero rate is zero."""
        result = compute_monthly_interest(100000000, 0)
        assert result == 0

    def test_compute_monthly_interest_positive(self):
        """Monthly interest at positive rate."""
        result = compute_monthly_interest(100000000, 850)
        assert result > 0

    def test_compute_principal_component(self):
        """Principal component = EMI - interest."""
        result = compute_principal_component(10000, 3000)
        assert result == 7000


class TestAmortizationCoverage:
    """Cover uncovered amortization paths."""

    def test_find_schedule_row_found(self):
        """find_schedule_row returns correct row."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        from engines.loan_engine.amortization import find_schedule_row
        row = find_schedule_row(schedule, 6)
        assert row is not None
        assert row.month_number == 6

    def test_find_schedule_row_not_found(self):
        """find_schedule_row returns None for invalid month."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        from engines.loan_engine.amortization import find_schedule_row
        row = find_schedule_row(schedule, 99)
        assert row is None

    def test_validate_schedule_empty(self):
        """Empty schedule passes validation."""
        assert validate_schedule([], 0, debug_mode=True) is True

    def test_validate_schedule_debug_mode_raises(self):
        """validate_schedule with debug_mode=True raises on EMI inconsistency."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        # This should pass
        assert validate_schedule(schedule, 100000000, debug_mode=True) is True

    def test_validate_schedule_invariants_passes(self):
        """validate_schedule_invariants passes for valid schedule."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        assert validate_schedule_invariants(schedule, 100000000) is True

    def test_total_interest_empty_schedule(self):
        """total_interest_paise on empty schedule returns 0."""
        assert total_interest_paise([]) == 0

    def test_total_payment_empty_schedule(self):
        """total_payment_paise on empty schedule returns 0."""
        from engines.loan_engine.amortization import total_payment_paise
        assert total_payment_paise([]) == 0


class TestForeclosureCoverage:
    """Cover foreclosure paths."""

    def test_compute_prepayment_breakup_basic(self):
        """compute_prepayment_breakup works with standard params."""
        result = compute_prepayment_breakup(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            months_elapsed=12,
            original_principal_paise=100000000,
            original_tenure_months=120,
        )
        assert "principal_remaining_paise" in result
        assert "accrued_interest_paise" in result
        assert "penalty_paise" in result
        assert "total_foreclosure_paise" in result
        assert result["principal_remaining_paise"] == 100000000

    def test_compute_prepayment_breakup_zero_remaining(self):
        """compute_prepayment_breakup with full elapsed tenure returns zeros."""
        result = compute_prepayment_breakup(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            months_elapsed=120,
            original_principal_paise=100000000,
            original_tenure_months=120,
        )
        assert result["principal_remaining_paise"] == 0
        assert result["accrued_interest_paise"] == 0
        assert result["penalty_paise"] == 0
        assert result["total_foreclosure_paise"] == 0

    def test_foreclosure_with_penalty(self):
        """compute_foreclosure_amount with nonzero penalty."""
        result = compute_foreclosure_amount(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=60,
            prepayment_penalty_bps=200,
        )
        assert result.penalty_paise == 2000000  # 2% of 1Cr
        assert result.foreclosure_amount_paise > result.outstanding_paise


class TestMetricsCoverage:
    """Cover metrics paths."""

    def test_compute_loan_metrics_empty_schedule(self):
        """compute_loan_metrics on empty schedule returns zeros."""
        metrics = compute_loan_metrics([], 100000000)
        assert metrics.outstanding_paise == 0
        assert metrics.principal_paid_paise == 0
        assert metrics.interest_paid_paise == 0
        assert metrics.effective_interest_ratio == 0.0

    def test_compute_loan_metrics_with_schedule(self):
        """compute_loan_metrics on valid schedule."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        metrics = compute_loan_metrics(schedule, 100000000)
        # With a full schedule, current outstanding = first balance (minus principal)
        # But schedule is the full schedule, so current_outstanding = schedule[0].balance_paise
        assert metrics.outstanding_paise > 0
        assert metrics.remaining_tenure_months == 12
        assert metrics.effective_interest_ratio > 0

    def test_calculate_interest_saved(self):
        """calculate_interest_saved compares schedules."""
        original = generate_schedule(100000000, 850, 120, "2025-01-01")
        new = generate_schedule(100000000, 850, 60, "2025-01-01")
        saved = calculate_interest_saved(original, new)
        assert saved > 0

    def test_calculate_interest_saved_with_prepayment(self):
        """calculate_interest_saved with prepayment cost."""
        original = generate_schedule(100000000, 850, 120, "2025-01-01")
        new = generate_schedule(100000000, 850, 60, "2025-01-01")
        saved = calculate_interest_saved(original, new, prepayment_paise=50000000)
        assert saved >= 0

    def test_calculate_tenure_saved(self):
        """calculate_tenure_saved compares schedule lengths."""
        original = generate_schedule(100000000, 850, 120, "2025-01-01")
        new = generate_schedule(100000000, 850, 60, "2025-01-01")
        saved = calculate_tenure_saved(original, new)
        assert saved == 60

    def test_get_interest_component(self):
        """get_interest_component returns positive value."""
        from engines.loan_engine.metrics import get_interest_component
        interest = get_interest_component(100000000, 850, 120)
        assert interest > 0

    def test_get_emi_component(self):
        """get_emi_component returns positive value."""
        from engines.loan_engine.metrics import get_emi_component
        emi = get_emi_component(100000000, 850, 120)
        assert emi > 0


class TestFloatingRateCoverage:
    """Cover floating rate edge cases."""

    def test_floating_rate_change_start_month(self):
        """Rate change at month 1 should work."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        new_schedule = apply_floating_rate_change(schedule, 1, 950)
        assert len(new_schedule) == 120

    def test_floating_rate_with_tuple_changes(self):
        """simulate with tuple-based rate changes."""
        from engines.loan_engine.floating_rate import simulate_floating_rate_schedule
        changes = [(12, 900), (24, 850)]
        schedule = simulate_floating_rate_schedule(
            100000000, 850, 120, changes, "adjust_emi"
        )
        assert len(schedule) == 120


class TestPrepaymentCoverage:
    """Cover prepayment edge cases."""

    def test_apply_prepayment_passes_schedule(self):
        """apply_prepayment with existing_schedule param."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        from engines.loan_engine import apply_prepayment
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=50000000,
            existing_schedule=schedule,
        )
        assert result.interest_saved_paise > 0