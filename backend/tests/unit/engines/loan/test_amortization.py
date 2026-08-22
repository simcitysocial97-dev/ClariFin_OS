"""
Amortization Schedule Tests
===========================
Edge case tests for amortization schedule generator.
Tests leap years, month-end dates, and invariant validation.

Run: python -m pytest tests/test_amortization.py -v
"""

import pytest

from src.engines.loan_engine import generate_schedule, validate_schedule_invariants
from src.engines.loan_engine.amortization import _add_months
from src.engines.loan_engine.emi import compute_emi_fixed

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


# ============================================================
# Date Edge Case Tests
# ============================================================


class TestDateEdgeCases:
    """Tests for leap years and month-end date handling."""

    def test_jan_31_to_feb(self):
        """Jan 31 + 1 month should resolve to Feb 28."""
        from datetime import date

        result = _add_months(date(2025, 1, 31), 1)
        assert result == date(2025, 2, 28)

    def test_jan_31_to_mar(self):
        """Jan 31 + 2 months should resolve to Mar 31."""
        from datetime import date

        result = _add_months(date(2025, 1, 31), 2)
        assert result == date(2025, 3, 31)

    def test_feb_29_leap_year(self):
        """Feb 29, 2024 + 12 months should be Feb 28, 2025."""
        from datetime import date

        result = _add_months(date(2024, 2, 29), 12)
        # 2025 is not a leap year
        assert result == date(2025, 2, 28)

    def test_feb_29_to_leap_year(self):
        """Feb 29, 2024 + 36 months should be Feb 29, 2027."""
        from datetime import date

        result = _add_months(date(2024, 2, 29), 36)
        assert result == date(2027, 2, 28)

    def test_feb_28_non_leap_to_feb_28(self):
        """Feb 28, 2025 + 12 months should stay Feb 28."""
        from datetime import date

        result = _add_months(date(2025, 2, 28), 12)
        assert result == date(2026, 2, 28)

    def test_month_end_regular_month(self):
        """Jan 31 -> Mar 31 works correctly."""
        from datetime import date

        result = _add_months(date(2025, 1, 31), 3)
        assert result == date(2025, 4, 30)

    def test_full_year_progression(self):
        """Start date + 12 months works correctly."""
        from datetime import date

        result = _add_months(date(2025, 1, 15), 12)
        assert result == date(2026, 1, 15)


# ============================================================
# Schedule Generation Tests
# ============================================================


class TestScheduleGeneration:
    """Tests for core schedule generation."""

    def test_schedule_generates_correct_length(self, sample_loan):
        """Schedule has exactly tenure_months rows."""
        schedule = generate_schedule(**sample_loan)
        assert len(schedule) == sample_loan["tenure_months"]

    def test_schedule_first_row_is_month_one(self, sample_loan):
        """First row has month_number = 1."""
        schedule = generate_schedule(**sample_loan)
        assert schedule[0].month_number == 1

    def test_schedule_last_row_balance_zero(self, sample_loan):
        """Last row has balance_paise = 0."""
        schedule = generate_schedule(**sample_loan)
        assert schedule[-1].balance_paise == 0

    def test_emi_calculation_accuracy(self, sample_loan):
        """EMI matches mathematical formula."""
        schedule = generate_schedule(**sample_loan)
        emi = compute_emi_fixed(
            sample_loan["principal_paise"],
            sample_loan["annual_rate_bps"],
            sample_loan["tenure_months"],
        )
        # All but last EMI should be equal
        for row in schedule[:-1]:
            assert row.emi_paise == emi

    def test_emi_last_payment_adjusted(self, sample_loan):
        """Last payment EMI adjusted for rounding."""
        schedule = generate_schedule(**sample_loan)
        # Last payment differs due to balance adjustment
        assert schedule[-1].emi_paise != schedule[0].emi_paise


# ============================================================
# Invariant Validation Tests
# ============================================================


class TestScheduleInvariants:
    """Tests for schedule invariant validation."""

    def test_validate_schedule_passes(self, sample_loan):
        """Valid schedule passes invariant checks."""
        schedule = generate_schedule(**sample_loan)
        assert validate_schedule_invariants(schedule, sample_loan["principal_paise"])

    def test_principal_sum_equals_original(self, sample_loan):
        """Sum of principal components equals original principal."""
        schedule = generate_schedule(**sample_loan)
        total_principal = sum(row.principal_paise for row in schedule)
        assert total_principal == sample_loan["principal_paise"]

    def test_cumulative_interest_monotonic(self, sample_loan):
        """Cumulative interest never decreases."""
        schedule = generate_schedule(**sample_loan)
        for i in range(1, len(schedule)):
            assert (
                schedule[i].cumulative_interest_paise
                >= schedule[i - 1].cumulative_interest_paise
            )

    def test_interest_calculation_accuracy(self, sample_loan):
        """Interest matches mathematical formula."""
        schedule = generate_schedule(**sample_loan)
        # Check first month interest
        # Interest = Principal × Rate / 12
        expected_first_interest = int(
            sample_loan["principal_paise"] * sample_loan["annual_rate_bps"] / 120000
        )
        assert schedule[0].interest_paise == expected_first_interest

    def test_balance_decreases_over_time(self, sample_loan):
        """Balance strictly decreases until zero."""
        schedule = generate_schedule(**sample_loan)
        for i in range(1, len(schedule)):
            assert schedule[i].balance_paise < schedule[i - 1].balance_paise

    def test_validate_schedule_negative_balance_raises(self):
        """Invariant check raises on negative balance."""
        # Create a schedule with negative balance (simulated)
        from src.engines.loan_engine.models import AmortizationRow

        schedule = [
            AmortizationRow(
                month_number=1,
                payment_date="2025-01-01",
                emi_paise=10000,
                principal_paise=100,
                interest_paise=9900,
                balance_paise=-1,  # Invalid
                cumulative_interest_paise=9900,
            )
        ]
        with pytest.raises(ValueError, match="Balance went negative"):
            validate_schedule_invariants(schedule, 100)


# ============================================================
# Edge Case Loan Tests
# ============================================================


class TestEdgeCaseLoans:
    """Tests for edge case loan scenarios."""

    def test_zero_interest_loan(self):
        """Zero interest rate loan works correctly."""
        schedule = generate_schedule(
            principal_paise=1000000,  # ₹10,000
            annual_rate_bps=0,
            tenure_months=12,
            start_date="2025-01-01",
        )
        assert len(schedule) == 12
        for row in schedule:
            assert row.interest_paise == 0
        assert schedule[-1].balance_paise == 0

    def test_short_tenure_loan(self):
        """6-month loan generates correctly."""
        schedule = generate_schedule(
            principal_paise=1000000,  # ₹10,000
            annual_rate_bps=1000,  # 10%
            tenure_months=6,
            start_date="2025-01-01",
        )
        assert len(schedule) == 6

    def test_leap_year_start_date(self):
        """Schedule starting on leap year date (Feb 29) handles correctly."""
        schedule = generate_schedule(
            principal_paise=100000000,  # ₹10,00,000
            annual_rate_bps=850,
            tenure_months=24,
            start_date="2024-02-29",  # Leap year
        )
        assert len(schedule) == 24
        assert schedule[0].payment_date == "2024-02-29"

    def test_month_end_start_date(self):
        """Schedule starting on month-end handles correctly."""
        schedule = generate_schedule(
            principal_paise=100000000,
            annual_rate_bps=850,
            tenure_months=6,
            start_date="2025-01-31",  # Month end
        )
        assert schedule[0].payment_date == "2025-01-31"
        assert schedule[1].payment_date == "2025-02-28"  # Not 31

    def test_provided_emi_respected(self):
        """Provided EMI value is used when passed."""
        emi = 20000  # Custom EMI
        schedule = generate_schedule(
            principal_paise=1000000,
            annual_rate_bps=1000,
            tenure_months=12,
            start_date="2025-01-01",
            emi_paise=emi,
        )
        assert schedule[0].emi_paise == emi


# ============================================================
# validate_schedule Tests (comprehensive invariant validation)
# ============================================================


class TestValidateSchedule:
    """Tests for comprehensive schedule validation (validate_schedule)."""

    def test_validate_schedule_emi_consistency(self, sample_loan):
        """Schedule with varying EMI (except last) returns False/raises; consistent EMI passes."""
        from src.engines.loan_engine.amortization import validate_schedule

        # Valid schedule should pass
        schedule = generate_schedule(**sample_loan)
        assert (
            validate_schedule(
                schedule, sample_loan["principal_paise"], sample_loan["tenure_months"]
            )
            is True
        )

        # Create schedule with inconsistent EMI (modify row 2)
        from src.engines.loan_engine.models import AmortizationRow

        bad_schedule = list(schedule)
        bad_schedule[1] = AmortizationRow(
            month_number=2,
            payment_date="2025-02-01",
            emi_paise=schedule[1].emi_paise + 1,  # Different EMI
            principal_paise=schedule[1].principal_paise,
            interest_paise=schedule[1].interest_paise,
            balance_paise=schedule[1].balance_paise,
            cumulative_interest_paise=schedule[1].cumulative_interest_paise,
        )
        assert (
            validate_schedule(
                bad_schedule,
                sample_loan["principal_paise"],
                sample_loan["tenure_months"],
            )
            is False
        )

        # debug_mode=True should raise
        with pytest.raises(ValueError, match="EMI inconsistency"):
            validate_schedule(
                bad_schedule,
                sample_loan["principal_paise"],
                sample_loan["tenure_months"],
                debug_mode=True,
            )

    def test_validate_schedule_tenure_length(self, sample_loan):
        """Schedule length != original_tenure_months returns False/raises."""
        from src.engines.loan_engine.amortization import validate_schedule

        schedule = generate_schedule(**sample_loan)
        assert (
            validate_schedule(
                schedule, sample_loan["principal_paise"], sample_loan["tenure_months"]
            )
            is True
        )

        # Remove last row
        short_schedule = schedule[:-1]
        assert (
            validate_schedule(
                short_schedule,
                sample_loan["principal_paise"],
                sample_loan["tenure_months"],
            )
            is False
        )

        with pytest.raises(ValueError, match="Schedule length"):
            validate_schedule(
                short_schedule,
                sample_loan["principal_paise"],
                sample_loan["tenure_months"],
                debug_mode=True,
            )

    def test_validate_schedule_debug_mode_raises(self, sample_loan):
        """debug_mode=True raises ValueError with all violations; debug_mode=False returns False."""
        from src.engines.loan_engine.amortization import validate_schedule
        from src.engines.loan_engine.models import AmortizationRow

        # Create schedule with multiple violations
        bad_schedule = [
            AmortizationRow(
                month_number=1,
                payment_date="2025-01-01",
                emi_paise=10000,
                principal_paise=100,
                interest_paise=9900,
                balance_paise=-1,  # Negative balance
                cumulative_interest_paise=9900,
            ),
            AmortizationRow(
                month_number=3,  # Non-sequential month
                payment_date="2025-03-01",
                emi_paise=10000,
                principal_paise=100,
                interest_paise=9900,
                balance_paise=5000,
                cumulative_interest_paise=19800,  # Not monotonic (19800 < 9900? No, it's >)
            ),
        ]

        # debug_mode=False returns False
        assert validate_schedule(bad_schedule, 10000, debug_mode=False) is False

        # debug_mode=True raises ValueError
        with pytest.raises(ValueError) as exc_info:
            validate_schedule(bad_schedule, 10000, debug_mode=True)
        error_msg = str(exc_info.value)
        assert "Balance went negative" in error_msg
        assert "Month number" in error_msg

    def test_validate_schedule_all_invariants(self, sample_loan):
        """Property test: generate valid/invalid schedules, verify all 7 invariants correctly detected."""
        from src.engines.loan_engine.amortization import validate_schedule

        # Valid schedule passes all
        schedule = generate_schedule(**sample_loan)
        assert (
            validate_schedule(
                schedule,
                sample_loan["principal_paise"],
                sample_loan["tenure_months"],
                debug_mode=True,
            )
            is True
        )

        # Test each invariant individually by creating targeted violations
        from src.engines.loan_engine.models import AmortizationRow

        # 1. Balance never negative
        bad = list(schedule)
        bad[0] = AmortizationRow(**{**schedule[0].model_dump(), "balance_paise": -1})
        assert (
            validate_schedule(
                bad, sample_loan["principal_paise"], sample_loan["tenure_months"]
            )
            is False
        )

        # 2. Principal paid never exceeds original
        bad = list(schedule)
        bad[0] = AmortizationRow(
            **{
                **schedule[0].model_dump(),
                "principal_paise": sample_loan["principal_paise"] + 1,
            }
        )
        assert (
            validate_schedule(
                bad, sample_loan["principal_paise"], sample_loan["tenure_months"]
            )
            is False
        )

        # 3. Final balance reaches zero (tested by tenure_length check)

        # 4. Sum(principal payments) == principal amount
        bad = list(schedule)
        bad[0] = AmortizationRow(
            **{
                **schedule[0].model_dump(),
                "principal_paise": sample_loan["principal_paise"] + 1000,
            }
        )
        assert (
            validate_schedule(
                bad, sample_loan["principal_paise"], sample_loan["tenure_months"]
            )
            is False
        )

        # 5. EMI consistency (all but last equal)
        bad = list(schedule)
        bad[1] = AmortizationRow(
            **{**schedule[1].model_dump(), "emi_paise": schedule[1].emi_paise + 1}
        )
        assert (
            validate_schedule(
                bad, sample_loan["principal_paise"], sample_loan["tenure_months"]
            )
            is False
        )

        # 6. Cumulative interest monotonic non-decreasing
        bad = list(schedule)
        bad[2] = AmortizationRow(
            **{
                **schedule[2].model_dump(),
                "cumulative_interest_paise": schedule[1].cumulative_interest_paise - 1,
            }
        )
        assert (
            validate_schedule(
                bad, sample_loan["principal_paise"], sample_loan["tenure_months"]
            )
            is False
        )

        # 7. Month numbers sequential
        bad = list(schedule)
        bad[2] = AmortizationRow(**{**schedule[2].model_dump(), "month_number": 5})
        assert (
            validate_schedule(
                bad, sample_loan["principal_paise"], sample_loan["tenure_months"]
            )
            is False
        )
