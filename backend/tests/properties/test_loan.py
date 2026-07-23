"""Property tests for Loan Engine using Hypothesis."""
from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Import domain invariants
from tests.domain.invariants import assert_loan_schedule_valid


class TestLoanEngineProperties:
    """Property tests for loan engine functions."""

    @given(
        principal_paise=st.integers(min_value=100000, max_value=100000000),
        annual_rate_bps=st.integers(min_value=600, max_value=2400),
        tenure_months=st.integers(min_value=6, max_value=360),
        start_date=st.sampled_from([
            "2025-01-01", "2025-01-15", "2025-02-28", "2025-03-31"
        ]),
    )
    @settings(max_examples=20)
    def test_generate_schedule_invariants(
        self,
        principal_paise: int,
        annual_rate_bps: int,
        tenure_months: int,
        start_date: str,
    ) -> None:
        """Generated schedule must satisfy loan invariants."""
        from src.engines.loan_engine import generate_schedule

        schedule = generate_schedule(
            principal_paise=principal_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=tenure_months,
            start_date=start_date,
        )

        # Convert AmortizationRow models to dicts for invariant checking
        schedule_dicts = [
            {
                "month_number": row.month_number,
                "payment_date": row.payment_date,
                "emi_paise": row.emi_paise,
                "principal_paise": row.principal_paise,
                "interest_paise": row.interest_paise,
                "balance_paise": row.balance_paise,
            }
            for row in schedule
        ]

        assert_loan_schedule_valid(schedule_dicts)

        # Verify schedule length matches tenure
        assert len(schedule) == tenure_months

        # Verify principal and interest are non-negative (EMI can be 0 for final payments)
        for row in schedule:
            assert row.principal_paise >= 0
            assert row.interest_paise >= 0

    @given(
        principal_paise=st.integers(min_value=1000000, max_value=50000000),
        annual_rate_bps=st.integers(min_value=800, max_value=1800),
        tenure_months=st.integers(min_value=12, max_value=240),
    )
    @settings(max_examples=20)
    def test_emi_calculation_consistency(
        self,
        principal_paise: int,
        annual_rate_bps: int,
        tenure_months: int,
    ) -> None:
        """EMI calculation must be internally consistent."""
        from src.engines.loan_engine import compute_emi_fixed, generate_schedule

        emi = compute_emi_fixed(principal_paise, annual_rate_bps, tenure_months)

        # EMI must be positive
        assert emi > 0

        # Generate schedule with computed EMI
        schedule = generate_schedule(
            principal_paise=principal_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=tenure_months,
            start_date="2025-01-01",
            emi_paise=emi,
        )

        # Total principal paid should equal original principal (within rounding)
        total_principal = sum(row.principal_paise for row in schedule)
        assert abs(total_principal - principal_paise) <= tenure_months  # Allow small rounding diff

    @given(
        outstanding_paise=st.integers(min_value=1000000, max_value=50000000),
        annual_rate_bps=st.integers(min_value=600, max_value=2400),
        remaining_months=st.integers(min_value=6, max_value=240),
        prepayment_paise=st.integers(min_value=100000, max_value=20000000),
    )
    @settings(max_examples=20)
    def test_prepayment_interest_saved_non_negative(
        self,
        outstanding_paise: int,
        annual_rate_bps: int,
        remaining_months: int,
        prepayment_paise: int,
    ) -> None:
        """Prepayment should not increase total interest."""
        from src.engines.loan_engine import (
            PrepaymentMode,
            apply_prepayment,
            generate_schedule,
            total_interest_paise,
        )

        # Generate original schedule
        original_schedule = generate_schedule(
            principal_paise=outstanding_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=remaining_months,
            start_date="2025-01-01",
        )
        original_interest = total_interest_paise(original_schedule)

        # Apply prepayment (only if prepayment doesn't exceed outstanding)
        if prepayment_paise < outstanding_paise:
            result = apply_prepayment(
                outstanding_paise=outstanding_paise,
                annual_rate_bps=annual_rate_bps,
                remaining_months=remaining_months,
                prepayment_paise=prepayment_paise,
                mode=PrepaymentMode.REDUCE_TENURE,
                start_date="2025-01-01",
            )

            new_interest = 0
            if result.new_schedule:
                new_interest = total_interest_paise(result.new_schedule)

            assert original_interest - new_interest >= 0 or result.loan_closed
