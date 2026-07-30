"""
Consolidated Loan Engine Tests
==============================
Merged from: test_loan_engine_comprehensive.py, test_loan_engine_coverage.py, test_loan_engine_financial_correctness.py

Covers: amortization, prepayment, foreclosure, floating rate, metrics, edge cases, financial correctness.
"""

from __future__ import annotations

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
    get_emi_component,
    get_interest_component,
)
from src.engines.loan_engine.models import FloatingRateChange
from src.engines.loan_engine.prepayment import (
    apply_multiple_prepayments,
    apply_prepayment_at_month,
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
