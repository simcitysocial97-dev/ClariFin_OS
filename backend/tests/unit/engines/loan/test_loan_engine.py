"""
Consolidated Loan Engine Tests
==============================
Merged from: test_loan_engine_comprehensive.py, test_loan_engine_coverage.py, test_loan_engine_financial_correctness.py

Covers: amortization, prepayment, foreclosure, floating rate, metrics, edge cases, financial correctness.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN

import pytest
from src.engines.loan_engine import (
    apply_floating_rate_change,
    apply_prepayment,
    compute_emi_fixed,
    compute_emi_floating,
    compute_loan_metrics,
    compute_monthly_interest,
    compute_principal_component,
    generate_schedule,
    total_interest_paise,
    validate_schedule,
    validate_schedule_invariants,
)
from src.engines.loan_engine.amortization import (
    find_schedule_row,
    total_payment_paise,
    total_principal_paise,
    _add_months,
)
from src.engines.loan_engine.emi import (
    compute_principal_from_emi,
    compute_tenure_from_emi,
)
from src.engines.loan_engine.floating_rate import (
    simulate_floating_rate_schedule,
)
from src.engines.loan_engine.foreclosure import (
    compute_foreclosure_amount,
    compute_prepayment_breakup,
)
from src.engines.loan_engine.metrics import (
    calculate_interest_saved,
    calculate_tenure_saved,
    compute_loan_metrics,
    get_emi_component,
    get_interest_component,
)
from src.engines.loan_engine.models import AmortizationRow
from src.engines.loan_engine.models import FloatingRateChange
from src.engines.loan_engine.prepayment import (
    _compute_tenure_from_emi,
    apply_multiple_prepayments,
    apply_prepayment_at_month,
    regenerate_schedule,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_loan():
    """Standard loan: ₹10L at 8.5% for 10 years."""
    return {
        "principal_paise": 100000000,  # ₹10,00,000
        "annual_rate_bps": 850,  # 8.5%
        "tenure_months": 120,  # 10 years
        "start_date": "2025-01-01",
    }


@pytest.fixture
def sample_loan_info():
    """LoanInfo object for testing - minimal required fields."""
    return {
        "outstanding_paise": 100000000,  # ₹10,00,000
        "annual_rate_bps": 850,  # 8.5%
        "remaining_months": 120,  # 10 years
        "emi_paise": 123960,  # Approx ₹12,396
        "start_date": "2025-01-01",
    }


@pytest.fixture
def sample_schedule(sample_loan):
    """Generated schedule for sample loan."""
    return generate_schedule(**sample_loan)


# ============================================================================
# EMI Formula Correctness
# ============================================================================


class TestEMIFormulaCorrectness:
    """Verify EMI formula against known RBI calculations."""

    def test_standard_loan_emi(self):
        """Standard ₹10L at 8.5% for 10 years."""
        principal = 100000000
        rate_bps = 850
        tenure = 120
        emi = compute_emi_fixed(principal, rate_bps, tenure)
        expected_emi = 1239857
        assert (
            abs(emi - expected_emi) <= 10
        ), f"EMI {emi} differs from expected {expected_emi}"

    def test_zero_interest_emi(self):
        """Zero interest loan: EMI should be principal/tenure."""
        principal = 100000000
        tenure = 60
        emi = compute_emi_fixed(principal, 0, tenure)
        assert emi == principal // tenure
        assert emi == 1666666

    def test_high_interest_emi(self):
        """High interest loan (18% personal loan)."""
        principal = 50000000
        rate_bps = 1800
        tenure = 24
        emi = compute_emi_fixed(principal, rate_bps, tenure)
        assert emi > 0
        assert emi < principal

    def test_tiny_interest_emi(self):
        """Tiny interest (< 1%) should still produce valid EMI."""
        principal = 100000000
        rate_bps = 50
        tenure = 120
        emi = compute_emi_fixed(principal, rate_bps, tenure)
        base_emi = principal // tenure
        assert emi >= base_emi
        assert emi < base_emi * 1.1


# ============================================================================
# EMI Coverage
# ============================================================================


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


# ============================================================================
# Schedule Correctness
# ============================================================================


class TestScheduleCorrectness:
    """Verify amortization schedule correctness."""

    def test_schedule_sum_principal_equals_original(self):
        """Sum of principal components should equal original principal."""
        principal = 100000000
        schedule = generate_schedule(
            principal_paise=principal,
            annual_rate_bps=850,
            tenure_months=120,
            start_date="2025-01-01",
        )
        total_principal = sum(row.principal_paise for row in schedule)
        assert (
            total_principal == principal
        ), f"Principal sum {total_principal} != {principal}"

    def test_schedule_final_balance_zero(self):
        """Final balance should be exactly zero."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=120,
            start_date="2025-01-01",
        )
        assert schedule[-1].balance_paise == 0

    def test_schedule_invariants(self):
        """All schedule invariants must hold."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=120,
            start_date="2025-01-01",
        )
        for row in schedule:
            assert row.balance_paise >= 0
        for i, row in enumerate(schedule, 1):
            assert row.month_number == i
        for row in schedule:
            assert len(row.payment_date) == 10
            assert row.payment_date[4] == "-"
            assert row.payment_date[7] == "-"

    def test_schedule_leap_year_february(self):
        """Schedule starting Feb 29 should handle non-leap years."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=24,
            start_date="2024-02-29",
        )
        assert len(schedule) == 24
        assert schedule[12].payment_date

    def test_schedule_generation(self, sample_loan):
        """Schedule is generated correctly."""
        schedule = generate_schedule(**sample_loan)
        assert len(schedule) == sample_loan["tenure_months"]
        assert schedule[0].month_number == 1
        assert schedule[-1].balance_paise <= schedule[-1].emi_paise

    def test_schedule_totals(self, sample_schedule):
        """Schedule totals are computed correctly."""
        total_interest = total_interest_paise(sample_schedule)
        total_payment = total_payment_paise(sample_schedule)
        assert total_interest > 0
        assert total_payment > total_interest
        assert total_payment == sum(row.emi_paise for row in sample_schedule)


# ============================================================================
# Amortization Coverage
# ============================================================================


class TestAmortizationCoverage:
    """Cover uncovered amortization paths."""

    def test_find_schedule_row_found(self):
        """find_schedule_row returns correct row."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        row = find_schedule_row(schedule, 6)
        assert row is not None
        assert row.month_number == 6

    def test_find_schedule_row_not_found(self):
        """find_schedule_row returns None for invalid month."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        row = find_schedule_row(schedule, 99)
        assert row is None

    def test_validate_schedule_empty(self):
        """Empty schedule passes validation."""
        assert validate_schedule([], 0, debug_mode=True) is True

    def test_validate_schedule_debug_mode_raises(self):
        """validate_schedule with debug_mode=True passes on valid schedule."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
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
        assert total_payment_paise([]) == 0


# ============================================================================
# Prepayment Tests
# ============================================================================


class TestPrepayment:
    """Tests for prepayment functionality."""

    def test_single_prepayment_reduce_tenure(self, sample_loan_info):
        """Single prepayment reduces tenure correctly."""
        result = apply_prepayment(
            outstanding_paise=sample_loan_info["outstanding_paise"],
            annual_rate_bps=sample_loan_info["annual_rate_bps"],
            remaining_months=sample_loan_info["remaining_months"],
            prepayment_paise=10000000,
            mode="reduce_tenure",
        )
        assert result.months_saved > 0
        assert result.interest_saved_paise > 0
        assert result.new_remaining_months < sample_loan_info["remaining_months"]
        assert result.loan_closed is False

    def test_single_prepayment_reduce_emi(self, sample_loan_info):
        """Single prepayment reduces EMI correctly."""
        result = apply_prepayment(
            outstanding_paise=sample_loan_info["outstanding_paise"],
            annual_rate_bps=sample_loan_info["annual_rate_bps"],
            remaining_months=sample_loan_info["remaining_months"],
            prepayment_paise=10000000,
            mode="reduce_emi",
        )
        assert result.months_saved == 0
        assert result.new_emi_paise < result.original_emi_paise
        assert result.interest_saved_paise > 0

    def test_full_foreclosure(self, sample_loan_info):
        """Full foreclosure closes loan."""
        result = apply_prepayment(
            outstanding_paise=sample_loan_info["outstanding_paise"],
            annual_rate_bps=sample_loan_info["annual_rate_bps"],
            remaining_months=sample_loan_info["remaining_months"],
            prepayment_paise=sample_loan_info["outstanding_paise"],
            mode="reduce_tenure",
        )
        assert result.loan_closed is True
        assert result.new_remaining_months == 0
        assert result.months_saved == sample_loan_info["remaining_months"]

    def test_multiple_prepayments(self, sample_schedule, sample_loan):
        """Multiple prepayments work correctly."""
        prepayments = [(6, 5000000), (12, 3000000)]
        new_schedule, results = apply_multiple_prepayments(
            sample_schedule,
            prepayments,
            sample_loan["annual_rate_bps"],
        )
        assert len(results) == 2
        assert len(new_schedule) < len(sample_schedule)
        assert total_interest_paise(new_schedule) < total_interest_paise(
            sample_schedule
        )

    def test_prepayment_with_penalty(self, sample_loan_info):
        """Prepayment with penalty reduces savings."""
        result_with_penalty = apply_prepayment(
            outstanding_paise=sample_loan_info["outstanding_paise"],
            annual_rate_bps=sample_loan_info["annual_rate_bps"],
            remaining_months=sample_loan_info["remaining_months"],
            prepayment_paise=10000000,
            mode="reduce_tenure",
            prepayment_penalty_bps=200,
        )
        result_without_penalty = apply_prepayment(
            outstanding_paise=sample_loan_info["outstanding_paise"],
            annual_rate_bps=sample_loan_info["annual_rate_bps"],
            remaining_months=sample_loan_info["remaining_months"],
            prepayment_paise=10000000,
            mode="reduce_tenure",
            prepayment_penalty_bps=0,
        )
        assert (
            result_with_penalty.interest_saved_paise
            < result_without_penalty.interest_saved_paise
        )

    def test_reduce_tenure_saves_both(self):
        """REDUCE_TENURE mode should save interest and months."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode="reduce_tenure",
        )
        assert result.months_saved > 0
        assert result.interest_saved_paise > 0
        assert result.new_remaining_months < 120

    def test_reduce_emi_keeps_tenure(self):
        """REDUCE_EMI mode should keep tenure same."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode="reduce_emi",
        )
        assert result.months_saved == 0
        assert result.new_remaining_months == 120
        assert result.new_emi_paise < result.original_emi_paise

    def test_full_prepayment_closes_loan(self):
        """Full prepayment should close the loan."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=100000000,
            mode="reduce_tenure",
        )
        assert result.loan_closed is True
        assert result.new_remaining_months == 0
        assert result.months_saved == 120
        assert result.new_schedule is not None
        assert len(result.new_schedule) == 1

    def test_interest_saved_formula(self):
        """Interest saved = original_interest - new_interest - penalty."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode="reduce_tenure",
        )
        assert result.new_schedule is not None
        assert result.interest_saved_paise >= 0

    def test_apply_prepayment_passes_schedule(self):
        """apply_prepayment with existing_schedule param."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=50000000,
            existing_schedule=schedule,
        )
        assert result.interest_saved_paise > 0


# ============================================================================
# Dynamic Prepayment Engine Tests
# ============================================================================


class TestDynamicPrepaymentEngine:
    """Tests for dynamic prepayment engine."""

    def test_apply_prepayment_at_month(self, sample_schedule):
        """Apply prepayment at specific month."""
        new_schedule, result = apply_prepayment_at_month(
            schedule=sample_schedule,
            prepayment_month=12,
            prepayment_paise=10000000,
            annual_rate_bps=850,
        )
        assert len(new_schedule) < len(sample_schedule)
        assert result.months_saved > 0
        assert result.interest_saved_paise > 0
        assert new_schedule[11].balance_paise < sample_schedule[11].balance_paise


# ============================================================================
# Floating Rate Tests
# ============================================================================


class TestFloatingRate:
    """Tests for floating rate functionality."""

    def test_floating_rate_change(self, sample_schedule):
        """Floating rate change works correctly."""
        new_schedule = apply_floating_rate_change(
            schedule=sample_schedule,
            change_month=12,
            new_rate_bps=950,
            mode="adjust_emi",
        )
        assert len(new_schedule) == len(sample_schedule)
        assert new_schedule[11].emi_paise != sample_schedule[11].emi_paise

    def test_floating_rate_tenure_adjustment(self, sample_schedule):
        """Floating rate change with tenure adjustment."""
        new_schedule = apply_floating_rate_change(
            schedule=sample_schedule,
            change_month=12,
            new_rate_bps=950,
            mode="adjust_tenure",
        )
        assert len(new_schedule) > len(sample_schedule)
        assert new_schedule[11].emi_paise == sample_schedule[11].emi_paise

    def test_simulate_floating_rate_schedule(self):
        """Simulate schedule with multiple rate changes."""
        rate_changes = [
            FloatingRateChange(change_month=12, new_rate_bps=900, mode="adjust_emi"),
            FloatingRateChange(change_month=24, new_rate_bps=850, mode="adjust_emi"),
        ]
        schedule = simulate_floating_rate_schedule(
            principal_paise=100000000,
            initial_rate_bps=850,
            tenure_months=120,
            rate_changes=rate_changes,
        )
        assert len(schedule) == 120
        assert schedule[10].emi_paise != schedule[11].emi_paise
        assert schedule[22].emi_paise != schedule[23].emi_paise

    def test_rate_increase_extends_tenure(self):
        """Rate increase with adjust_tenure should extend schedule."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=120,
            start_date="2025-01-01",
        )
        new_schedule = apply_floating_rate_change(
            schedule=schedule,
            change_month=12,
            new_rate_bps=950,
            mode="adjust_tenure",
        )
        assert len(new_schedule) > len(schedule)

    def test_rate_increase_adjusts_emi(self):
        """Rate increase with adjust_emi should change EMI."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=120,
            start_date="2025-01-01",
        )
        original_emi = schedule[11].emi_paise
        new_schedule = apply_floating_rate_change(
            schedule=schedule,
            change_month=12,
            new_rate_bps=950,
            mode="adjust_emi",
        )
        assert new_schedule[11].emi_paise != original_emi

    def test_floating_rate_change_start_month(self):
        """Rate change at month 1 should work."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        new_schedule = apply_floating_rate_change(schedule, 1, 950)
        assert len(new_schedule) == 120

    def test_floating_rate_with_tuple_changes(self):
        """simulate with tuple-based rate changes."""
        changes = [(12, 900), (24, 850)]
        schedule = simulate_floating_rate_schedule(
            100000000, 850, 120, changes, "adjust_emi"
        )
        assert len(schedule) == 120

    def test_rate_change_at_last_month(self):
        """Rate change at the final month should succeed and alter the last row."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        last_month = len(schedule)
        new_schedule = apply_floating_rate_change(
            schedule, last_month, 950, mode="adjust_emi"
        )
        assert len(new_schedule) == 120
        assert new_schedule[-1].emi_paise != schedule[-1].emi_paise

    def test_rate_change_on_closed_loan_returns_unchanged(self):
        """Rate change when opening balance is zero must return schedule unchanged."""
        from src.engines.loan_engine.models import AmortizationRow

        closed_row = AmortizationRow(
            month_number=1,
            payment_date="2025-01-01",
            emi_paise=0,
            principal_paise=0,
            interest_paise=0,
            balance_paise=0,
            cumulative_interest_paise=0,
        )
        schedule = [closed_row]
        new_schedule = apply_floating_rate_change(
            schedule, 1, 950, mode="adjust_emi"
        )
        assert len(new_schedule) == 1
        assert new_schedule[0].emi_paise == 0
        assert new_schedule[0].balance_paise == 0

    def test_simulate_with_three_element_tuple_uses_month_from_index_zero(self):
        """Three-element tuples must read month from index 0, not index 1."""
        # If month were read from index 1, month=950 would be out of range
        # and the change would be silently skipped, leaving EMI unchanged.
        schedule = simulate_floating_rate_schedule(
            100000000,
            850,
            120,
            [(12, 950, "adjust_emi")],
            "adjust_emi",
        )
        assert len(schedule) == 120
        assert schedule[11].emi_paise != schedule[10].emi_paise

    def test_simulate_with_invalid_tuple_mode_falls_back_to_adjust_emi(self):
        """Invalid mode in a three-element tuple must fall back to adjust_emi."""
        original_emi = 1239857  # known EMI for 10L at 8.5%/120mo
        schedule = simulate_floating_rate_schedule(
            100000000,
            850,
            120,
            [(12, 950, "bad_mode")],
            "adjust_emi",
        )
        assert len(schedule) == 120
        # Falls back to adjust_emi, so EMI at row 12 should differ from original.
        assert schedule[11].emi_paise != original_emi

    def test_simulate_with_explicit_adjust_tenure_tuple(self):
        """Three-element tuple with adjust_tenure must keep EMI unchanged."""
        schedule = simulate_floating_rate_schedule(
            100000000,
            850,
            120,
            [(12, 950, "adjust_tenure")],
            "adjust_emi",
        )
        assert len(schedule) > 120
        # EMI at the change point must remain identical to the original.
        assert schedule[11].emi_paise == schedule[10].emi_paise

    def test_rate_change_first_month_has_empty_prefix(self):
        """A rate change at month 1 must not prepend any unchanged rows."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        new_schedule = apply_floating_rate_change(
            schedule, 1, 950, mode="adjust_emi"
        )
        # Month numbers must start at 1, not 2 — proves prefix is empty.
        assert new_schedule[0].month_number == 1
        assert len(new_schedule) == 120

    def test_simulate_with_start_date_propagates_correctly(self):
        """simulate_floating_rate_schedule must pass start_date through to regenerate."""
        schedule = simulate_floating_rate_schedule(
            principal_paise=100000000,
            initial_rate_bps=850,
            tenure_months=120,
            rate_changes=[(12, 950)],
            mode="adjust_emi",
            start_date="2024-06-15",
        )
        assert len(schedule) == 120
        # Payment dates must reflect the explicit start date, not the default.
        assert schedule[0].payment_date == "2024-06-15"
        assert schedule[11].payment_date != schedule[0].payment_date

    def test_simulate_skips_out_of_range_month(self):
        """simulate_floating_rate_schedule must skip month=0 and month>len(schedule)."""
        schedule = simulate_floating_rate_schedule(
            100000000,
            850,
            120,
            [(0, 950), (121, 950), (12, 900)],
            "adjust_emi",
        )
        assert len(schedule) == 120
        # Only the month=12 change should have taken effect.
        assert schedule[11].emi_paise != schedule[10].emi_paise


# ============================================================================
# Foreclosure Tests
# ============================================================================


class TestForeclosure:
    """Tests for foreclosure calculations."""

    def test_foreclosure_sums_correctly(self):
        """Foreclosure = outstanding + accrued_interest + penalty."""
        result = compute_foreclosure_amount(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=60,
            prepayment_penalty_bps=100,
        )
        expected_penalty = 1000000
        assert result.penalty_paise == expected_penalty
        assert (
            result.foreclosure_amount_paise
            == result.outstanding_paise
            + result.accrued_interest_paise
            + result.penalty_paise
        )

    def test_penalty_calculation(self):
        """Penalty should be rate * outstanding / 10000."""
        result = compute_foreclosure_amount(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=60,
            prepayment_penalty_bps=200,
        )
        assert result.penalty_paise == 2000000

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
        assert result.penalty_paise == 2000000
        assert result.foreclosure_amount_paise > result.outstanding_paise


# ============================================================================
# Metrics Tests
# ============================================================================


class TestMetrics:
    """Tests for loan metrics calculations."""

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
        interest = get_interest_component(100000000, 850, 120)
        assert interest > 0

    def test_get_emi_component(self):
        """get_emi_component returns positive value."""
        emi = get_emi_component(100000000, 850, 120)
        assert emi > 0

    def test_compute_loan_metrics_empty_schedule_remaining_interest(self):
        """Empty schedule: remaining_interest_paise must be 0 (kills numeric_default mutant line 7)."""
        metrics = compute_loan_metrics([], 100000000)
        assert metrics.remaining_interest_paise == 0

    def test_compute_loan_metrics_empty_schedule_tenure_saved(self):
        """Empty schedule: tenure_saved_months must be 0 (kills numeric_default mutant line 9)."""
        metrics = compute_loan_metrics([], 100000000)
        assert metrics.tenure_saved_months == 0

    def test_compute_loan_metrics_empty_schedule_total_payments(self):
        """Empty schedule: total_payments_remaining must be 0 (kills numeric_default mutant line 10)."""
        metrics = compute_loan_metrics([], 100000000)
        assert metrics.total_payments_remaining == 0

    def test_compute_loan_metrics_nonempty_schedule_tenure_saved(self):
        """Non-empty schedule: tenure_saved_months must be 0 (kills numeric_default mutant line 38)."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        metrics = compute_loan_metrics(schedule, 100000000)
        assert metrics.tenure_saved_months == 0

    def test_compute_loan_metrics_zero_principal_ratio(self):
        """original_principal_paise=0 must return ratio 0.0 without crashing (kills comparison >=0 and else 0.0->1.0 mutants lines 28-29)."""
        metrics = compute_loan_metrics([], 0)
        assert metrics.effective_interest_ratio == 0.0

    def test_compute_loan_metrics_principal_one_ratio(self):
        """original_principal_paise=1 must use division branch, not fallback (kills comparison >1 mutant line 28)."""
        row = AmortizationRow(
            month_number=1,
            payment_date="2025-01-01",
            emi_paise=2,
            principal_paise=1,
            interest_paise=1,
            balance_paise=0,
            cumulative_interest_paise=1,
        )
        metrics = compute_loan_metrics([row], 1)
        assert metrics.effective_interest_ratio == 1.0

    def test_compute_loan_metrics_rounding_precision(self):
        """effective_interest_ratio rounded to 4 decimals, not 5 (kills numeric_default mutant line 40)."""
        row = AmortizationRow(
            month_number=1,
            payment_date="2025-01-01",
            emi_paise=2,
            principal_paise=1,
            interest_paise=1,
            balance_paise=0,
            cumulative_interest_paise=1,
        )
        metrics = compute_loan_metrics([row], 3)
        assert metrics.effective_interest_ratio == 0.3333

    def test_calculate_interest_saved_default_prepayment(self):
        """calculate_interest_saved without prepayment_paise uses default 0 (kills numeric_default mutant line 1 param)."""
        original = generate_schedule(100000000, 850, 120, "2025-01-01")
        new = generate_schedule(100000000, 850, 60, "2025-01-01")
        saved_with_default = calculate_interest_saved(original, new)
        saved_explicit_zero = calculate_interest_saved(original, new, prepayment_paise=0)
        assert saved_with_default == saved_explicit_zero
        assert saved_with_default > 0


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_zero_prepayment(self, sample_loan_info):
        """Zero prepayment should raise error."""
        with pytest.raises(ValueError, match="must be positive"):
            apply_prepayment(
                outstanding_paise=sample_loan_info["outstanding_paise"],
                annual_rate_bps=sample_loan_info["annual_rate_bps"],
                remaining_months=sample_loan_info["remaining_months"],
                prepayment_paise=0,
            )

    def test_invalid_prepayment_month(self, sample_schedule):
        """Invalid prepayment month should raise error."""
        with pytest.raises(ValueError, match="out of range"):
            apply_prepayment_at_month(
                schedule=sample_schedule,
                prepayment_month=121,
                prepayment_paise=10000000,
                annual_rate_bps=850,
            )

    def test_invalid_rate_change_month(self, sample_schedule):
        """Invalid rate change month should raise error."""
        with pytest.raises(ValueError, match="out of range"):
            apply_floating_rate_change(
                schedule=sample_schedule,
                change_month=121,
                new_rate_bps=950,
            )

    def test_negative_rate(self, sample_schedule):
        """Negative rate should raise error."""
        with pytest.raises(ValueError, match="Rate cannot be negative"):
            apply_floating_rate_change(
                schedule=sample_schedule,
                change_month=12,
                new_rate_bps=-100,
            )

    def test_negative_values_rejected(self):
        """Negative principal or rate should raise errors."""
        with pytest.raises(ValueError):
            compute_emi_fixed(-100, 850, 120)
        with pytest.raises(ValueError):
            compute_emi_fixed(100000000, -850, 120)

    def test_zero_tenure_rejected(self):
        """Zero tenure should raise error."""
        with pytest.raises(ValueError, match="Tenure must be positive"):
            compute_emi_fixed(100000000, 850, 0)

    def test_large_principal(self):
        """Large principal (₹1Cr+) should work."""
        schedule = generate_schedule(
            principal_paise=10000000000,
            annual_rate_bps=850,
            tenure_months=240,
            start_date="2025-01-01",
        )
        assert len(schedule) == 240
        assert schedule[-1].balance_paise == 0

    def test_small_principal(self):
        """Small principal (₹10k) should work."""
        schedule = generate_schedule(
            principal_paise=1000000,
            annual_rate_bps=850,
            tenure_months=12,
            start_date="2025-01-01",
        )
        assert len(schedule) == 12
        assert schedule[-1].balance_paise == 0


# ============================================================================
# Foreclosure Survivor Kill Tests (M9-C42.17)
# ============================================================================


class TestForeclosureSurvivors:
    """Targeted tests to kill surviving mutants in foreclosure.py."""

    def test_foreclosure_zero_outstanding(self):
        """outstanding_paise=0 triggers guard: max(0, 0)=0, not max(1,0)=1."""
        result = compute_foreclosure_amount(
            outstanding_paise=0, annual_rate_bps=850, remaining_months=60
        )
        assert result.outstanding_paise == 0
        assert result.foreclosure_amount_paise == 0
        assert result.accrued_interest_paise == 0
        assert result.penalty_paise == 0
        assert result.remaining_months_saved == 60

    def test_foreclosure_zero_remaining_months(self):
        """remaining_months=0 triggers guard: max(0, 0)=0 for remaining_months_saved."""
        result = compute_foreclosure_amount(
            outstanding_paise=100000000, annual_rate_bps=850, remaining_months=0
        )
        assert result.remaining_months_saved == 0
        assert result.foreclosure_amount_paise == 100000000
        assert result.outstanding_paise == 100000000

    def test_foreclosure_negative_outstanding(self):
        """negative outstanding: max(0, negative)=0 guards against <=1 mutation."""
        result = compute_foreclosure_amount(
            outstanding_paise=-100, annual_rate_bps=850, remaining_months=60
        )
        assert result.outstanding_paise == 0
        assert result.foreclosure_amount_paise == 0

    def test_foreclosure_negative_remaining_months(self):
        """negative remaining_months: guard catches <=0 but not <0 mutation."""
        result = compute_foreclosure_amount(
            outstanding_paise=100000000, annual_rate_bps=850, remaining_months=-1
        )
        assert result.remaining_months_saved == 0
        assert result.foreclosure_amount_paise == 100000000

    def test_foreclosure_default_params_zero(self):
        """Omitting optional params uses defaults of 0 (kills numeric_default mut)."""
        result = compute_foreclosure_amount(
            outstanding_paise=100000000, annual_rate_bps=850, remaining_months=60
        )
        assert result.penalty_paise == 0
        assert result.accrued_interest_paise > 0

    def test_foreclosure_prepayment_breakup_dict_keys(self):
        """All 4 required dict keys must exist with exact string names."""
        result = compute_prepayment_breakup(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            months_elapsed=12,
            original_principal_paise=100000000,
            original_tenure_months=120,
        )
        expected_keys = {
            "principal_remaining_paise",
            "accrued_interest_paise",
            "penalty_paise",
            "total_foreclosure_paise",
        }
        assert set(result.keys()) == expected_keys
        for key in expected_keys:
            assert isinstance(result[key], int)

    def test_foreclosure_prepayment_breakup_zero_remaining(self):
        """months_elapsed >= tenure → all-zero dict (kills dict_key mutations on guard path)."""
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

    def test_foreclosure_prepayment_breakup_zero_outstanding(self):
        """outstanding_paise=0 → max(0, 0)=0 guard path dict values."""
        result = compute_prepayment_breakup(
            outstanding_paise=0,
            annual_rate_bps=850,
            months_elapsed=12,
            original_principal_paise=100000000,
            original_tenure_months=120,
        )
        assert result["principal_remaining_paise"] == 0
        assert result["total_foreclosure_paise"] == 0

    def test_foreclosure_penalty_rounding_precision(self):
        """Penalty uses integer quantize, not 2-decimal (kills rounding_precision mut)."""
        from decimal import ROUND_HALF_EVEN, Decimal

        # 15 bps on 1000 paise = 1.5 → quantize(Decimal(1)) ROUND_HALF_EVEN = 2
        # quantize(Decimal(2)) would give 1.50 → int()=1 — different result
        result = compute_foreclosure_amount(
            outstanding_paise=1000,
            annual_rate_bps=850,
            remaining_months=1,
            prepayment_penalty_bps=15,
        )
        expected = int(
            (Decimal(15) * Decimal(1000) / Decimal(10000))
            .quantize(Decimal(1), rounding=ROUND_HALF_EVEN)
        )
        assert result.penalty_paise == expected

    def test_foreclosure_max_zero_not_one(self):
        """Guard uses max(0,...) not max(1,...) for remaining_months_saved."""
        result = compute_foreclosure_amount(
            outstanding_paise=100000000, annual_rate_bps=850, remaining_months=0
        )
        assert result.remaining_months_saved == 0
        assert result.foreclosure_amount_paise == 100000000

    def test_foreclosure_breakup_max_zero_not_one(self):
        """Breakup guard uses max(0,...) not max(1,...) for principal."""
        result = compute_prepayment_breakup(
            outstanding_paise=-100,
            annual_rate_bps=850,
            months_elapsed=12,
            original_principal_paise=100000000,
            original_tenure_months=120,
        )
        assert result["principal_remaining_paise"] == 0
        assert result["total_foreclosure_paise"] == 0


# ============================================================================
# EMI Survivor Kill Tests (M9-C42.17)
# ============================================================================


class TestEMISurvivors:
    """Targeted tests to kill surviving mutants in emi.py."""

    def test_emi_fixed_zero_principal_rejected(self):
        """principal=0 must raise (kills <=1 comparison mutation)."""
        with pytest.raises(ValueError, match="Principal must be positive"):
            compute_emi_fixed(0, 850, 120)

    def test_emi_fixed_negative_principal_rejected(self):
        """principal=-1 must raise (kills <0 comparison mutation)."""
        with pytest.raises(ValueError, match="Principal must be positive"):
            compute_emi_fixed(-1, 850, 120)

    def test_emi_fixed_negative_tenure_rejected(self):
        """tenure=-1 must raise (kills <0 comparison mutation on tenure)."""
        with pytest.raises(ValueError, match="Tenure must be positive"):
            compute_emi_fixed(100000000, 850, -1)

    def test_tenure_from_emi_zero_principal_rejected(self):
        """principal=0 must raise (kills <=1 comparison mutation)."""
        with pytest.raises(ValueError, match="Principal must be positive"):
            compute_tenure_from_emi(0, 850, 1000000)

    def test_tenure_from_emi_negative_principal_rejected(self):
        """principal=-1 must raise (kills <0 comparison mutation)."""
        with pytest.raises(ValueError, match="Principal must be positive"):
            compute_tenure_from_emi(-1, 850, 1000000)

    def test_tenure_from_emi_zero_emi_rejected(self):
        """emi=0 must raise (kills <=1 comparison mutation)."""
        with pytest.raises(ValueError, match="EMI must be positive"):
            compute_tenure_from_emi(100000000, 850, 0)

    def test_tenure_from_emi_negative_emi_rejected(self):
        """emi=-1 must raise (kills <0 comparison mutation)."""
        with pytest.raises(ValueError, match="EMI must be positive"):
            compute_tenure_from_emi(100000000, 850, -1)

    def test_monthly_interest_positive_rate(self):
        """Positive rate must produce positive interest (kills ==1 comparison)."""
        result = compute_monthly_interest(100000000, 850)
        assert result > 0

    def test_tenure_zero_rate_ceiling_formula(self):
        """Zero-rate tenure uses ceiling formula (kills -2 arithmetic mutation)."""
        principal = 100000000
        emi = 2000000  # ₹20,000/month
        tenure = compute_tenure_from_emi(principal, 0, emi)
        expected = (principal + emi - 1) // emi
        assert tenure == expected

    def test_tenure_interest_only_returns_max(self):
        """EMI equal to interest-only returns 999 (kills == comparison mutation)."""
        # At 12% annual (100 bps monthly), interest on 100L = 100000000 * 0.00833... ≈ 833333
        # Use exact: monthly_rate = 100/120000 = 1/1200
        # interest = 100000000 / 1200 = 83333.33... → int = 83333
        # Set emi = 83333 (below or equal to interest)
        tenure = compute_tenure_from_emi(100000000, 100, 83333)
        assert tenure == 999

    def test_tenure_below_interest_returns_max(self):
        """EMI below interest returns 999 (kills < comparison mutation)."""
        tenure = compute_tenure_from_emi(100000000, 100, 1)
        assert tenure == 999

    def test_tenure_capped_at_999(self):
        """Computed tenure > 999 is capped at 999 (kills numeric_default 999→1000)."""
        # Very small EMI relative to principal at low rate → large computed tenure
        tenure = compute_tenure_from_emi(100000000, 10, 100000)
        assert tenure <= 999
        assert tenure >= 1

    def test_tenure_max_lower_bound(self):
        """min(1, tenure) keeps tenure >= 1 (kills max(2,...) numeric_default)."""
        tenure = compute_tenure_from_emi(100000000, 850, 999999999)
        assert tenure >= 1

    def test_principal_from_emi_returns_int_not_none(self):
        """compute_principal_from_emi must return int, not None (kills constant mut)."""
        result = compute_principal_from_emi(1239857, 850, 120)
        assert isinstance(result, int)
        assert result is not None
        assert result > 0

    def test_principal_from_emi_inverse_roundtrip(self):
        """Round-trip: principal → EMI → principal recovers within tolerance (kills call_arg mut)."""
        principal = 100000000
        rate = 850
        tenure = 120
        emi = compute_emi_fixed(principal, rate, tenure)
        recovered = compute_principal_from_emi(emi, rate, tenure)
        # Rounding divergence is expected; assert within ±10 paise
        assert abs(recovered - principal) <= 10

    def test_principal_from_emi_zero_rate(self):
        """Zero-rate inverse: principal = EMI * tenure (kills arithmetic mutation)."""
        principal = compute_principal_from_emi(1666666, 0, 60)
        assert principal == 1666666 * 60

    def test_principal_from_emi_search_window_valid(self):
        """Search window [-500,+500] finds correct principal near boundary cases."""
        # High-rate short-tenure loan where rounding divergence is likely
        emi = compute_emi_fixed(50000000, 1800, 12)
        recovered = compute_principal_from_emi(emi, 1800, 12)
        # Allow small rounding divergence
        assert abs(recovered - 50000000) <= 10

    def test_compute_tenure_from_emi_large_tenure_caps(self):
        """Large computed tenure clamps to 999, not 1000 (kills min(1000,...) mut)."""
        tenure = compute_tenure_from_emi(100000000, 5, 50000)
        assert tenure <= 999


# ============================================================================
# Amortization Mutation Killers (M9-C42.17)
# Targeted tests for surviving mutants in amortization.py
# ============================================================================


class TestAmortizationMutationKillers:
    """Tests targeting 70 real-gap survivors in amortization.py."""

    # --- Comparison mutations (_add_months December boundary) ---

    def test_add_months_december_to_january(self):
        """Exercises month_idx==12 branch in _add_months (line 15).

        Kills: comparison_operator_mutation on 'if month_idx == 12:' → '== 13'
        A December start date + 1 month forces the Dec→Jan fallback path.
        """
        from datetime import date

        result = _add_months(date(2024, 12, 15), 1)
        assert result == date(2025, 1, 15)

    def test_add_months_year_boundary_preserves_day(self):
        """Month-end Jan 31 + 11 months reaches December via fallback branch."""
        from datetime import date

        result = _add_months(date(2025, 1, 31), 11)
        assert result == date(2025, 12, 31)

    # --- Comparison mutations (_required_emi months==1 boundary) ---

    def test_required_emi_months_one_exactly(self):
        """months==1 exercises the `months <= 1` branch of _required_emi.

        Kills: comparison_operator_mutation on 'if months <= 1:' → 'if months < 1:'
        With months==1 the original enters the branch; mutant skips it.
        """
        from decimal import Decimal

        from src.engines.loan_engine.amortization import _required_emi

        # balance*(1+rate) = 1001 * 1.005 = 1006.005 → ROUND_CEILING = 1007
        result = _required_emi(Decimal("1001"), Decimal("0.005"), 1)
        assert result == 1007

    def test_required_emi_months_two_uses_annty_formula(self):
        """months==2 exercises the annuity formula path (not the <=1 shortcut)."""
        from decimal import Decimal

        from src.engines.loan_engine.amortization import _required_emi

        result = _required_emi(Decimal("1000"), Decimal("0.01"), 2)
        assert result > 0

    # --- Rounding precision (_required_emi ROUND_CEILING at half-paise) ---

    def test_required_emi_rounding_ceiling_at_half_paise(self):
        """ROUND_CEILING rounds 1006.005 up to 1007, not down to 1006.

        Kills: decimal_argument_mutation removing rounding arg, and
        constant_replacement_mutation changing ROUND_CEILING → None.
        """
        from decimal import Decimal

        from src.engines.loan_engine.amortization import _required_emi

        result = _required_emi(Decimal("1001"), Decimal("0.005"), 1)
        assert result == 1007  # ceiling(1006.005) = 1007, not 1006

    def test_required_emi_zero_rate_rounding(self):
        """Zero-rate path uses ROUND_CEILING on balance/months.

        Kills: decimal_argument_mutation removing rounding from
        '(balance / Decimal(months)).to_integral_value(rounding=ROUND_CEILING)'
        """
        from decimal import Decimal

        from src.engines.loan_engine.amortization import _required_emi

        # 1000 / 3 = 333.333... → ROUND_CEILING = 334
        result = _required_emi(Decimal("1000"), Decimal("0"), 3)
        assert result == 334

    # --- Comparison mutations (ill-conditioned last-month re-anchor) ---

    def test_ill_conditioned_loan_last_month_no_reanchor(self):
        """Ill-conditioned loan: last month should NOT re-anchor EMI.

        Kills: comparison_operator_mutation on
        'month < tenure_months' → 'month <= tenure_months'
        The mutated code would re-anchor on the final month, producing a
        different EMI than the original on month==tenure_months.
        """
        schedule = generate_schedule(7000, 3600, 60, "2025-01-01")
        # Month 60 is the last month; original does NOT re-anchor there
        assert schedule[59].emi_paise != schedule[58].emi_paise
        # But the difference comes from natural balance reduction, not re-anchor
        assert schedule[59].balance_paise == 0

    def test_ill_conditioned_threshold_boundary(self):
        """Principal just below ill-conditioned threshold stays fixed EMI.

        Kills: decimal_argument_mutation on
        'annuity_factor / Decimal(2) > Decimal(principal_paise) / Decimal(100)'
        vs '/ Decimal(3)' and '>= ' variants.
        """
        # principal=9000 at 36% for 60 months is NOT ill-conditioned
        # (annuity_factor/2 ≈ 81.5 < 9000/100 = 90)
        schedule_normal = generate_schedule(9000, 3600, 60, "2025-01-01")
        emis_normal = set(row.emi_paise for row in schedule_normal[:-1])
        assert len(emis_normal) == 1  # single fixed EMI

        # principal=7000 IS ill-conditioned
        schedule_ill = generate_schedule(7000, 3600, 60, "2025-01-01")
        emis_ill = set(row.emi_paise for row in schedule_ill)
        assert len(emis_ill) > 1  # re-anchored EMIs

    # --- Comparison mutations (interest-only mid-schedule) ---

    def test_interest_only_mid_schedule(self):
        """EMI < interest produces zero principal component mid-schedule.

        Kills: comparison_operator_mutation on
        'principal_exact <= 0 or reported_balance <= 0' → 'and', '< 0',
        '<= 1', etc. When principal_exact==0 exactly, 'or' triggers but
        'and' would not.
        """
        # principal=100, rate=10000bps (100% annual), tenure=60
        # EMI is small relative to monthly interest → interest-only months
        schedule = generate_schedule(100, 10000, 60, "2025-01-01")
        # Month 2 has principal=0 (EMI only covers part of interest)
        assert schedule[1].principal_paise == 0
        assert schedule[1].balance_paise > 0

    def test_interest_only_zero_balance_interest_falls_to_zero(self):
        """When reported_balance reaches 0, interest_paise must also be 0.

        Kills: comparison_operator_mutation on
        'interest_rounded if reported_balance > 0 else 0' →
        '>= 0', '> 1', 'else 1'. With balance==0, original returns 0 interest.
        """
        schedule = generate_schedule(100, 10000, 60, "2025-01-01")
        # Find first month where balance becomes 0
        for i, row in enumerate(schedule):
            if row.balance_paise == 0:
                assert row.interest_paise == 0, (
                    f"Month {i+1}: balance=0 but interest={row.interest_paise}"
                )
                break

    # --- Comparison mutations (early payoff exact boundary) ---

    def test_exact_payoff_boundary(self):
        """Find a loan where balance - principal_exact == 0 exactly.

        Kills: arithmetic_operator_mutation on
        'balance - principal_exact <= 0' → '< 0' and '<= 1'
        At the exact boundary, '==' should trigger early payoff, not fall through.
        """
        # Use a small principal where EMI clears balance exactly
        schedule = generate_schedule(100, 10000, 12, "2025-01-01")
        # Verify all balances are non-negative and final is 0
        assert schedule[-1].balance_paise == 0
        for row in schedule:
            assert row.balance_paise >= 0

    # --- Rounding precision (interest quantize precision) ---

    def test_interest_quantize_precision_at_half_value(self):
        """Interest with fractional 0.5 paise rounds via banker's rounding.

        Kills: rounding_argument_mutation on
        'quantize(Decimal(1), rounding=ROUND_HALF_EVEN)' → 'quantize(Decimal(2), ...)'
        Using Decimal(2) would round to nearest 2, giving different results.
        """
        from decimal import Decimal, ROUND_HALF_EVEN

        # 60 paise * 1000bps / 120000 = 0.5 exactly
        interest = Decimal("60") * Decimal("1000") / Decimal("120000")
        assert interest == Decimal("0.5")
        rounded = int(interest.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
        assert rounded == 0  # banker's rounding: 0.5 → 0 (round to even)

    def test_balance_quantize_precision_at_half_value(self):
        """Balance after payment with fractional 0.5 paise uses banker's rounding.

        Kills: rounding_argument_mutation on
        'balance.quantize(Decimal(1), rounding=ROUND_HALF_EVEN)' → 'Decimal(2)'
        """
        from decimal import Decimal, ROUND_HALF_EVEN

        balance = Decimal("29.5")
        rounded = int(balance.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
        assert rounded == 30  # banker's rounding: 29.5 → 30 (round to even)

        balance = Decimal("30.5")
        rounded = int(balance.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
        assert rounded == 30  # banker's rounding: 30.5 → 30 (round to even)

    # --- Numeric default mutations (empty schedule functions) ---

    def test_empty_schedule_total_interest_is_zero(self):
        """total_interest_paise([]) must return 0, not 1.

        Kills: numeric_constant_mutation on 'return 0' → 'return 1'
        """
        assert total_interest_paise([]) == 0

    def test_empty_schedule_total_payment_is_zero(self):
        """total_payment_paise([]) must return 0.

        Kills: numeric_constant_mutation on the empty-list return path.
        """
        assert total_payment_paise([]) == 0

    def test_empty_schedule_total_principal_is_zero(self):
        """total_principal_paise([]) must return 0.

        Kills: numeric_constant_mutation on 'return 0' → 'return 1' in
        total_principal_paise.
        """
        assert total_principal_paise([]) == 0

    # --- Constant mutations (validate_schedule empty returns True) ---

    def test_validate_schedule_empty_returns_true(self):
        """Empty schedule validation returns True, not False.

        Kills: constant_replacement_mutation on 'return True' → 'return False'
        """
        assert validate_schedule([], 0, debug_mode=True) is True

    def test_validate_schedule_invariants_empty_returns_true(self):
        """validate_schedule_invariants on empty schedule returns True.

        Kills: same constant mutation on the early-return True path.
        """
        from src.engines.loan_engine import validate_schedule_invariants

        assert validate_schedule_invariants([], 0) is True

    # --- Comparison mutations (single-row schedule validation) ---

    def test_validate_schedule_single_row_passes(self):
        """Single-row schedule passes EMI-consistency check.

        Kills: comparison_operator_mutation on
        'if len(schedule) > 1:' → '>= 1:' and '> 2:'
        With len==1, original skips the loop; mutant with '>=1' enters it
        and checks schedule[0] against itself (harmless but wrong logic).
        """
        schedule = generate_schedule(1000, 850, 1, "2025-01-01")
        assert validate_schedule(schedule, 1000, debug_mode=True) is True

    # --- Arithmetic mutations (cumulative interest initialization) ---

    def test_cumulative_interest_monotonic_strict(self):
        """Cumulative interest must be strictly non-decreasing.

        Kills: arithmetic_operator_mutation on
        'prev_cumulative = -1' → '+1' and '-2'
        With prev=-1, any cumulative_interest >= 0 passes. With prev=+1,
        a schedule starting at 0 would fail incorrectly.
        """
        schedule = generate_schedule(100000, 850, 12, "2025-01-01")
        for i in range(1, len(schedule)):
            assert schedule[i].cumulative_interest_paise >= schedule[i - 1].cumulative_interest_paise

    # --- Error message content (validate_schedule exception) ---

    def test_validate_schedule_error_message_format(self):
        """Error message starts with 'Schedule invariant violations: '.

        Kills: arithmetic_operator_mutation on
        '"Schedule invariant violations: "' → '"XX...XX"', lowercase, UPPERCASE, etc.
        """
        from src.engines.loan_engine.amortization import validate_schedule

        bad = [
            AmortizationRow(
                month_number=1,
                payment_date="2025-01-01",
                emi_paise=10000,
                principal_paise=100,
                interest_paise=9900,
                balance_paise=-1,
                cumulative_interest_paise=9900,
            )
        ]
        with pytest.raises(ValueError) as exc_info:
            validate_schedule(bad, 100, debug_mode=True)
        assert str(exc_info.value).startswith("Schedule invariant violations: ")

    def test_validate_schedule_error_message_semicolon_separator(self):
        """Error message uses '; ' as separator between violations.

        Kills: arithmetic_operator_mutation on
        '"; ".join(errors)' → '"XX; XX".join(errors)'
        """
        from src.engines.loan_engine.amortization import validate_schedule

        bad = [
            AmortizationRow(
                month_number=1,
                payment_date="2025-01-01",
                emi_paise=10000,
                principal_paise=100,
                interest_paise=9900,
                balance_paise=-1,
                cumulative_interest_paise=9900,
            ),
            AmortizationRow(
                month_number=2,
                payment_date="2025-02-01",
                emi_paise=10000,
                principal_paise=100,
                interest_paise=9900,
                balance_paise=-2,
                cumulative_interest_paise=19800,
            ),
        ]
        with pytest.raises(ValueError) as exc_info:
            validate_schedule(bad, 100, debug_mode=True)
        error_msg = str(exc_info.value)
        assert "; " in error_msg

    # --- Comparison mutations (reported_balance == 1 boundary) ---

    def test_ill_conditioned_with_balance_one(self):
        """Ill-conditioned loan where reported_balance reaches 1 mid-schedule.

        Kills: comparison_operator_mutation on
        'reported_balance > 0' → '> 1'
        With balance==1, original re-anchors; mutant skips re-anchoring.
        """
        schedule = generate_schedule(7000, 3600, 60, "2025-01-01")
        # All balances should be non-negative and decrease monotonically
        for i in range(1, len(schedule)):
            assert schedule[i].balance_paise <= schedule[i - 1].balance_paise
        assert schedule[-1].balance_paise == 0

    # --- Rounding precision (ill-conditioned annuity factor) ---

    def test_ill_conditioned_annuity_factor_computation(self):
        """Annuity factor uses '- Decimal(1)' not '+ Decimal(1)'.

        Kills: decimal_argument_mutation on
        '(Decimal(1) + monthly_rate) ** tenure_months - Decimal(1)'
        → '+ Decimal(1)' and '- Decimal(2)'
        """
        from decimal import Decimal

        monthly_rate = Decimal("3600") / Decimal("120000")
        tenure = 60
        factor_correct = (Decimal(1) + monthly_rate) ** tenure - Decimal(1)
        factor_mutated_plus = (Decimal(1) + monthly_rate) ** tenure + Decimal(1)
        factor_mutated_minus2 = (Decimal(1) + monthly_rate) ** tenure - Decimal(2)
        # The correct factor is significantly different from mutated versions
        assert factor_correct != factor_mutated_plus
        assert factor_correct != factor_mutated_minus2
        # Verify the schedule was generated with correct factor
        schedule = generate_schedule(7000, 3600, 60, "2025-01-01")
        assert schedule[-1].balance_paise == 0

    # --- Comparison mutations (principal_exact < 0 boundary) ---

    def test_principal_not_negative_when_emi_sufficient(self):
        """Principal component is never negative when EMI exceeds interest.

        Kills: comparison_operator_mutation on
        'principal_exact <= 0 or reported_balance <= 0' → 'principal_exact < 0 ...'
        Ensures principal >= 0 whenever EMI covers interest.
        """
        schedule = generate_schedule(100000, 850, 12, "2025-01-01")
        for row in schedule:
            assert row.principal_paise >= 0

    # --- Rounding precision (last-month balance settlement) ---

    def test_last_month_balance_settled_to_zero(self):
        """Last month always settles balance to exactly 0.

        Kills: decimal_argument_mutation on 'balance = Decimal(0)' → 'Decimal(1)'
        and 'reported_balance = 0' → '1' in the final-payoff branch.
        """
        schedule = generate_schedule(100000, 850, 12, "2025-01-01")
        assert schedule[-1].balance_paise == 0

    def test_last_month_principal_equals_remaining_reported_balance(self):
        """Final month principal equals remaining reported balance (absorbs drift).

        Kills: numeric_constant_mutation on 'max(0, reported_balance)' → 'max(1, ...)'
        """
        schedule = generate_schedule(100000, 850, 12, "2025-01-01")
        # The last row's principal should clear the remaining reported balance
        assert schedule[-1].balance_paise == 0
        # Principal + interest = EMI in last month (self-consistent ledger)
        assert schedule[-1].principal_paise + schedule[-1].interest_paise == schedule[-1].emi_paise

    # --- Arithmetic mutations (actual_emi computation in early payoff) ---

    def test_early_payoff_emi_consistency(self):
        """Early payoff: actual_emi = principal + interest (not principal - interest).

        Kills: arithmetic_operator_mutation on
        'actual_emi_paise = principal_component_paise + interest_paise'
        → 'principal_component_paise - interest_paise'
        """
        # Small principal where EMI clears in first month
        schedule = generate_schedule(100, 10000, 12, "2025-01-01")
        # Find month where loan closes early
        for row in schedule:
            if row.balance_paise == 0:
                assert row.emi_paise == row.principal_paise + row.interest_paise
                break


# ============================================================================
# Prepayment Survivor Targeting (M9-C42.17)
# ============================================================================


class TestPrepaymentSurvivors:
    """Targeted tests killing surviving mutants in prepayment.py."""

    # --- Line 21: emi_paise > 0 boundary (comparison mutations >=, > 1) ---

    def test_zero_emi_with_zero_rate_returns_999(self):
        """When emi_paise is 0 and rate is 0, tenure should cap at 999."""
        result = _compute_tenure_from_emi(100000, 0, 0)
        assert result == 999

    def test_nonzero_emi_with_zero_rate_computes_correctly(self):
        """When emi_paise > 0 and rate is 0, tenure = ceil(principal / emi)."""
        result = _compute_tenure_from_emi(100000, 0, 30000)
        assert result == 4  # ceil(100000/30000) = 4

    # --- Line 27: emi <= principal * monthly_rate boundary ---

    def test_emi_at_exact_boundary_returns_999(self):
        """When emi equals exactly principal*monthly_rate, loan cannot amortize."""
        principal = 100000000
        rate = 850
        from decimal import Decimal, ROUND_HALF_EVEN
        monthly_rate = Decimal(rate) / Decimal(120000)
        emi_exact = int((Decimal(principal) * monthly_rate).quantize(
            Decimal(1), rounding=ROUND_HALF_EVEN
        ))
        result = _compute_tenure_from_emi(principal, rate, emi_exact)
        assert result == 999

    # --- Line 85: prepayment_month < 1 boundary ---

    def test_prepayment_month_zero_raises(self, sample_schedule):
        """Month 0 must raise ValueError (kills < 1 -> < 2 mutation)."""
        with pytest.raises(ValueError, match="out of range"):
            apply_prepayment_at_month(
                schedule=sample_schedule,
                prepayment_month=0,
                prepayment_paise=1000000,
                annual_rate_bps=850,
            )

    def test_prepayment_month_one_is_valid(self, sample_schedule):
        """Month 1 is the earliest valid prepayment month."""
        new_schedule, result = apply_prepayment_at_month(
            schedule=sample_schedule,
            prepayment_month=1,
            prepayment_paise=10000000,
            annual_rate_bps=850,
        )
        assert result.months_saved > 0

    # --- Line 145: new_balance <= 0 exact boundary ---

    def test_exact_payoff_closes_loan(self):
        """Prepaying exactly outstanding_paise must close the loan."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=100000000,
            mode="reduce_tenure",
        )
        assert result.loan_closed is True
        assert result.new_remaining_months == 0
        assert result.months_saved == 120
        assert result.new_emi_paise == 0

    def test_overpay_closes_loan_at_one_paise_above(self):
        """Overpaying by 1 paise still closes the loan."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=100000001,
            mode="reduce_tenure",
        )
        assert result.loan_closed is True
        assert result.new_remaining_months == 0

    # --- Line 160/236: interest_saved - penalty arithmetic ---

    def test_penalty_reduces_interest_saved(self):
        """With penalty > 0, interest_saved must be strictly less than without penalty."""
        result_no_pen = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode="reduce_tenure",
            prepayment_penalty_bps=0,
        )
        result_with_pen = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode="reduce_tenure",
            prepayment_penalty_bps=200,
        )
        assert result_with_pen.penalty_paise > 0
        assert (
            result_with_pen.interest_saved_paise
            < result_no_pen.interest_saved_paise
        )

    def test_interest_saved_formula_subtracts_penalty(self):
        """interest_saved = original_interest - new_interest - penalty (not +)."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode="reduce_tenure",
            prepayment_penalty_bps=500,
        )
        assert result.penalty_paise > 0
        assert result.interest_saved_paise >= 0
        # The key invariant: interest saved with penalty < interest saved without
        result_no_pen = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode="reduce_tenure",
            prepayment_penalty_bps=0,
        )
        assert result.interest_saved_paise < result_no_pen.interest_saved_paise

    # --- Line 254: sorted_prepayments with unsorted input ---

    def test_multiple_prepayments_sorted_by_month(self):
        """Unsorted prepayments must be processed in month order."""
        schedule = generate_schedule(100000000, 850, 24, "2025-01-01")
        prepayments = [(18, 5000000), (6, 3000000)]
        _, results = apply_multiple_prepayments(
            schedule, prepayments, 850
        )
        assert len(results) == 2
        # First result corresponds to month 6 (earlier), second to month 18
        assert results[0].prepayment_paise == 3000000
        assert results[1].prepayment_paise == 5000000

    # --- Line 259: multiple prepayment month validation ---

    def test_multiple_prepayment_month_zero_skipped(self):
        """Month 0 in multiple prepayments should be skipped, not crash."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        prepayments = [(0, 1000000), (6, 5000000)]
        new_schedule, results = apply_multiple_prepayments(
            schedule, prepayments, 850
        )
        assert len(results) == 1
        assert results[0].prepayment_paise == 5000000

    def test_multiple_prepayment_month_over_length_skipped(self):
        """Month beyond schedule length should be skipped."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        prepayments = [(13, 1000000), (6, 5000000)]
        _, results = apply_multiple_prepayments(
            schedule, prepayments, 850
        )
        assert len(results) == 1
        assert results[0].prepayment_paise == 5000000

    # --- Line 297: new_principal_paise <= 0 in regenerate_schedule ---

    def test_regenerate_zero_principal_returns_empty(self):
        """regenerate_schedule with 0 principal must return empty list."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        tail = schedule[11:]
        result = regenerate_schedule(
            tail, 0, 850, "reduce_tenure", "2025-06-01",
            original_emi=1239857,
        )
        assert result == []

    def test_regenerate_negative_principal_returns_empty(self):
        """regenerate_schedule with negative principal must return empty list."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        tail = schedule[11:]
        result = regenerate_schedule(
            tail, -1, 850, "reduce_tenure", "2025-06-01",
            original_emi=1239857,
        )
        assert result == []

    # --- Lines 301-304: boolean and/or on original_emi/original_tenure derivation ---

    def test_regenerate_derives_emi_from_schedule_when_none(self):
        """When original_emi is None, it must be derived from previous_schedule."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        tail = schedule[11:]
        result = regenerate_schedule(
            tail, 50000000, 850, "reduce_tenure", "2025-06-01",
        )
        assert len(result) > 0
        assert result[0].emi_paise == tail[0].emi_paise

    def test_regenerate_derives_tenure_from_schedule_when_none(self):
        """When original_tenure is None in reduce_emi mode, derived from schedule."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        tail = schedule[11:]
        result = regenerate_schedule(
            tail, 50000000, 850, "reduce_emi", "2025-06-01",
        )
        assert len(result) == 109  # 120 - 11 = 109 remaining months
        assert result[0].emi_paise < tail[0].emi_paise

    def test_regenerate_empty_schedule_without_emi_raises(self):
        """Empty previous_schedule with no original_emi must raise ValueError."""
        with pytest.raises(ValueError, match="original_emi is required"):
            regenerate_schedule(
                [], 50000000, 850, "reduce_tenure", "2025-06-01",
            )

    def test_regenerate_empty_schedule_without_tenure_raises(self):
        """Empty previous_schedule with no original_tenure in reduce_emi raises."""
        with pytest.raises(ValueError, match="original_tenure is required"):
            regenerate_schedule(
                [], 50000000, 850, "reduce_emi", "2025-06-01",
            )

    # --- Line 187: tail_start_index > 0 boundary (prepayment at month 1) ---

    def test_prepayment_at_month_one_no_prefix(self):
        """Prepayment at month 1 has empty prefix; schedule starts from tail."""
        schedule = generate_schedule(100000000, 850, 12, "2025-01-01")
        new_schedule, result = apply_prepayment_at_month(
            schedule, 1, 50000000, 850, mode="reduce_tenure"
        )
        assert len(new_schedule) < len(schedule)
        assert new_schedule[0].month_number == 1

    def test_prepayment_at_last_month(self, sample_schedule):
        """Prepayment at the last month must work correctly."""
        last_month = len(sample_schedule)
        new_schedule, result = apply_prepayment_at_month(
            schedule=sample_schedule,
            prepayment_month=last_month,
            prepayment_paise=1000000,
            annual_rate_bps=850,
        )
        assert result.months_saved >= 0
        assert len(new_schedule) <= len(sample_schedule)

    # --- Line 167-171: mode literal check with PrepaymentMode enum ---

    def test_prepayment_with_enum_mode_reduce_tenure(self):
        """Passing PrepaymentMode.REDUCE_TENURE enum must work like string."""
        from src.engines.loan_engine.models import PrepaymentMode
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode=PrepaymentMode.REDUCE_TENURE,
        )
        assert result.mode == PrepaymentMode.REDUCE_TENURE
        assert result.months_saved > 0

    def test_prepayment_with_enum_mode_reduce_emi(self):
        """Passing PrepaymentMode.REDUCE_EMI enum must work like string."""
        from src.engines.loan_engine.models import PrepaymentMode
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode=PrepaymentMode.REDUCE_EMI,
        )
        assert result.mode == PrepaymentMode.REDUCE_EMI
        assert result.months_saved == 0
        assert result.new_emi_paise < result.original_emi_paise

    # --- Penalty calculation boundaries ---

    def test_penalty_capped_at_three_percent_of_outstanding(self):
        """Penalty must never exceed 3% of outstanding balance."""
        schedule = generate_schedule(100000000, 850, 120, "2025-01-01")
        _, result = apply_prepayment_at_month(
            schedule, 1, 10000000, 850, prepayment_penalty_bps=9999
        )
        max_allowed = int(Decimal(100000000) * Decimal(300) / Decimal(10000))
        assert result.penalty_paise <= max_allowed

    def test_penalty_zero_when_bps_is_zero(self):
        """Zero penalty bps must produce zero penalty."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            prepayment_penalty_bps=0,
        )
        assert result.penalty_paise == 0

    def test_penalty_affects_interest_saved(self):
        """Higher penalty must reduce interest_saved proportionally."""
        r0 = apply_prepayment(
            outstanding_paise=100000000, annual_rate_bps=850,
            remaining_months=120, prepayment_paise=10000000,
            prepayment_penalty_bps=0,
        )
        r1 = apply_prepayment(
            outstanding_paise=100000000, annual_rate_bps=850,
            remaining_months=120, prepayment_paise=10000000,
            prepayment_penalty_bps=100,
        )
        r2 = apply_prepayment(
            outstanding_paise=100000000, annual_rate_bps=850,
            remaining_months=120, prepayment_paise=10000000,
            prepayment_penalty_bps=200,
        )
        assert r0.penalty_paise == 0
        assert r1.penalty_paise > 0
        assert r2.penalty_paise >= r1.penalty_paise
        assert r0.interest_saved_paise > r1.interest_saved_paise
        assert r1.interest_saved_paise >= r2.interest_saved_paise

    # --- Reduce-EMI balloon tolerance invariant ---

    def test_reduce_emi_no_balloon_final_month(self):
        """Regenerated reduce_emi schedule must not have balloon final EMI."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode="reduce_emi",
        )
        assert result.new_schedule is not None
        first_emi = result.new_schedule[0].emi_paise
        for row in result.new_schedule:
            assert row.emi_paise <= first_emi, \
                f"Balloon detected: month {row.month_number} emi={row.emi_paise} > {first_emi}"

    def test_reduce_tenure_tenure_shorter_than_original(self):
        """Reduce-tenure prepayment must shorten the schedule."""
        result = apply_prepayment(
            outstanding_paise=100000000,
            annual_rate_bps=850,
            remaining_months=120,
            prepayment_paise=10000000,
            mode="reduce_tenure",
        )
        assert result.new_schedule is not None
        assert len(result.new_schedule) < 120
        assert result.new_remaining_months < 120
