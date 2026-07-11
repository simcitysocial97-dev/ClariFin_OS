"""
Comprehensive Loan Engine Tests
===============================
Tests for the core loan engine functionality (prepayment, amortization, foreclosure, floating rate).

Run: python -m pytest tests/test_loan_engine_comprehensive.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.loan_engine.amortization import (
    generate_schedule,
    total_interest_paise,
    total_payment_paise,
)
from engines.loan_engine.floating_rate import (
    apply_floating_rate_change,
    simulate_floating_rate_schedule,
)
from engines.loan_engine.models import FloatingRateChange
from engines.loan_engine.prepayment import (
    apply_multiple_prepayments,
    apply_prepayment,
    apply_prepayment_at_month,
)

# ============================================================
# Fixtures
# ============================================================


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


# ============================================================
# Prepayment Analyzer Tests
# ============================================================


class TestPrepaymentAnalyzer:
    """Tests for prepayment analyzer functionality."""

    def test_single_prepayment_reduce_tenure(self, sample_loan_info):
        """Single prepayment reduces tenure correctly."""
        result = apply_prepayment(
            outstanding_paise=sample_loan_info["outstanding_paise"],
            annual_rate_bps=sample_loan_info["annual_rate_bps"],
            remaining_months=sample_loan_info["remaining_months"],
            prepayment_paise=10000000,  # ₹1,00,000
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
            prepayment_paise=10000000,  # ₹1,00,000
            mode="reduce_emi",
        )

        assert result.months_saved == 0  # Tenure stays same
        assert result.new_emi_paise < result.original_emi_paise  # New EMI < Original EMI
        assert result.interest_saved_paise > 0

    def test_full_foreclosure(self, sample_loan_info):
        """Full foreclosure closes loan."""
        result = apply_prepayment(
            outstanding_paise=sample_loan_info["outstanding_paise"],
            annual_rate_bps=sample_loan_info["annual_rate_bps"],
            remaining_months=sample_loan_info["remaining_months"],
            prepayment_paise=sample_loan_info["outstanding_paise"],  # Full amount
            mode="reduce_tenure",
        )

        assert result.loan_closed is True
        assert result.new_remaining_months == 0
        assert result.months_saved == sample_loan_info["remaining_months"]

    def test_multiple_prepayments(self, sample_schedule, sample_loan):
        """Multiple prepayments work correctly."""
        prepayments = [(6, 5000000), (12, 3000000)]  # ₹50k at month 6, ₹30k at month 12

        new_schedule, results = apply_multiple_prepayments(
            sample_schedule,
            prepayments,
            sample_loan["annual_rate_bps"],
        )

        assert len(results) == 2
        assert len(new_schedule) < len(sample_schedule)
        assert total_interest_paise(new_schedule) < total_interest_paise(sample_schedule)

    def test_prepayment_with_penalty(self, sample_loan_info):
        """Prepayment with penalty reduces savings."""
        result_with_penalty = apply_prepayment(
            outstanding_paise=sample_loan_info["outstanding_paise"],
            annual_rate_bps=sample_loan_info["annual_rate_bps"],
            remaining_months=sample_loan_info["remaining_months"],
            prepayment_paise=10000000,  # ₹1,00,000
            mode="reduce_tenure",
            prepayment_penalty_bps=200,  # 2% penalty
        )

        result_without_penalty = apply_prepayment(
            outstanding_paise=sample_loan_info["outstanding_paise"],
            annual_rate_bps=sample_loan_info["annual_rate_bps"],
            remaining_months=sample_loan_info["remaining_months"],
            prepayment_paise=10000000,  # ₹1,00,000
            mode="reduce_tenure",
            prepayment_penalty_bps=0,  # No penalty
        )

        assert result_with_penalty.interest_saved_paise < result_without_penalty.interest_saved_paise


# ============================================================
# Dynamic Prepayment Engine Tests
# ============================================================


class TestDynamicPrepaymentEngine:
    """Tests for dynamic prepayment engine."""

    def test_apply_prepayment_at_month(self, sample_schedule):
        """Apply prepayment at specific month."""
        new_schedule, result = apply_prepayment_at_month(
            schedule=sample_schedule,
            prepayment_month=12,
            prepayment_paise=10000000,  # ₹1,00,000
            annual_rate_bps=850,
        )

        assert len(new_schedule) < len(sample_schedule)
        assert result.months_saved > 0
        assert result.interest_saved_paise > 0
        assert new_schedule[11].balance_paise < sample_schedule[11].balance_paise

    def test_floating_rate_change(self, sample_schedule):
        """Floating rate change works correctly."""
        # Increase rate at month 12
        new_schedule = apply_floating_rate_change(
            schedule=sample_schedule,
            change_month=12,
            new_rate_bps=950,  # 9.5%
            mode="adjust_emi",
        )

        assert len(new_schedule) == len(sample_schedule)
        assert new_schedule[11].emi_paise != sample_schedule[11].emi_paise

    def test_floating_rate_tenure_adjustment(self, sample_schedule):
        """Floating rate change with tenure adjustment."""
        # Increase rate at month 12, keep EMI same
        new_schedule = apply_floating_rate_change(
            schedule=sample_schedule,
            change_month=12,
            new_rate_bps=950,  # 9.5%
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
            principal_paise=100000000,  # ₹10,00,000
            initial_rate_bps=850,
            tenure_months=120,
            rate_changes=rate_changes,
        )

        assert len(schedule) == 120
        # EMI should change at month 12 and 24
        # schedule[10] is month 11, schedule[11] is month 12
        assert schedule[10].emi_paise != schedule[11].emi_paise
        # schedule[22] is month 23, schedule[23] is month 24
        assert schedule[22].emi_paise != schedule[23].emi_paise


# ============================================================
# Edge Case Tests
# ============================================================


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
                prepayment_month=121,  # Beyond schedule length
                prepayment_paise=10000000,
                annual_rate_bps=850,
            )

    def test_invalid_rate_change_month(self, sample_schedule):
        """Invalid rate change month should raise error."""
        with pytest.raises(ValueError, match="out of range"):
            apply_floating_rate_change(
                schedule=sample_schedule,
                change_month=121,  # Beyond schedule length
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


# ============================================================
# Amortization Tests
# ============================================================


class TestAmortization:
    """Tests for amortization schedule generation."""

    def test_schedule_generation(self, sample_loan):
        """Schedule is generated correctly."""
        schedule = generate_schedule(**sample_loan)

        assert len(schedule) == sample_loan["tenure_months"]
        assert schedule[0].month_number == 1
        # Last balance should be approximately 0
        assert schedule[-1].balance_paise <= schedule[-1].emi_paise

    def test_schedule_totals(self, sample_schedule):
        """Schedule totals are computed correctly."""
        total_interest = total_interest_paise(sample_schedule)
        total_payment = total_payment_paise(sample_schedule)

        assert total_interest > 0
        assert total_payment > total_interest
        # Total payment should be principal + interest
        assert total_payment == sum(row.emi_paise for row in sample_schedule)
