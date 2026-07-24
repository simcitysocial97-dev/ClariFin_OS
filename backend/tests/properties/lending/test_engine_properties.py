"""Property tests for Lending domain — Loan Engine + Credit Card Engine."""
from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.domain.invariants import assert_loan_schedule_valid


class TestLoanEngineProperties:
    """Property tests for Loan Engine (business capability: lending)."""

    @given(
        principal_paise=st.integers(min_value=100000, max_value=10000000),
        annual_rate_bps=st.integers(min_value=600, max_value=2400),
        tenure_months=st.integers(min_value=6, max_value=360),
    )
    @settings(max_examples=20)
    def test_loan_amortization_schedule_valid(
        self, principal_paise: int, annual_rate_bps: int, tenure_months: int
    ) -> None:
        """Amortization schedule must satisfy all loan invariants."""
        from src.engines.loan_engine.amortization import generate_schedule
        from src.engines.loan_engine.emi import compute_emi_fixed

        emi = compute_emi_fixed(principal_paise, annual_rate_bps, tenure_months)
        schedule = generate_schedule(
            principal_paise, annual_rate_bps, tenure_months,
            start_date="2026-01-01", emi_paise=emi,
        )
        assert len(schedule) == tenure_months
        # Verify balance decreases monotonically
        for i in range(len(schedule) - 1):
            assert schedule[i].balance_paise >= schedule[i + 1].balance_paise
        assert schedule[-1].balance_paise == 0

    @given(
        principal_paise=st.integers(min_value=100000, max_value=5000000),
        annual_rate_bps=st.integers(min_value=600, max_value=2400),
        tenure_months=st.integers(min_value=12, max_value=120),
    )
    @settings(max_examples=20)
    def test_loan_emi_reduces_outstanding(
        self, principal_paise: int, annual_rate_bps: int, tenure_months: int
    ) -> None:
        """After first EMI, outstanding must be less than principal."""
        from src.engines.loan_engine.amortization import generate_schedule
        from src.engines.loan_engine.emi import compute_emi_fixed

        emi = compute_emi_fixed(principal_paise, annual_rate_bps, tenure_months)
        schedule = generate_schedule(
            principal_paise, annual_rate_bps, tenure_months,
            start_date="2026-01-01", emi_paise=emi,
        )
        if schedule:
            assert schedule[0].balance_paise < principal_paise
            assert schedule[-1].balance_paise == 0

    @given(
        principal_paise=st.integers(min_value=100000, max_value=10000000),
        annual_rate_bps=st.integers(min_value=600, max_value=2400),
        tenure_months=st.integers(min_value=12, max_value=360),
        prepayment_paise=st.integers(min_value=10000, max_value=500000),
    )
    @settings(max_examples=20)
    def test_loan_prepayment_reduces_interest(
        self,
        principal_paise: int,
        annual_rate_bps: int,
        tenure_months: int,
        prepayment_paise: int,
    ) -> None:
        """Prepayment must reduce total interest or keep it same."""
        from src.engines.loan_engine.amortization import generate_schedule, total_interest_paise
        from src.engines.loan_engine.emi import compute_emi_fixed
        from src.engines.loan_engine.prepayment import apply_prepayment_at_month

        emi = compute_emi_fixed(principal_paise, annual_rate_bps, tenure_months)
        original = generate_schedule(
            principal_paise, annual_rate_bps, tenure_months,
            start_date="2026-01-01", emi_paise=emi,
        )
        prepay_month = min(3, tenure_months - 1)
        new_schedule, _ = apply_prepayment_at_month(
            schedule=original,
            prepayment_month=prepay_month,
            prepayment_paise=prepayment_paise,
            annual_rate_bps=annual_rate_bps,
        )
        orig_interest = total_interest_paise(original)
        new_interest = total_interest_paise(new_schedule)
        assert new_interest <= orig_interest

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
        assert len(schedule) == tenure_months
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
        assert emi > 0
        schedule = generate_schedule(
            principal_paise=principal_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=tenure_months,
            start_date="2025-01-01",
            emi_paise=emi,
        )
        total_principal = sum(row.principal_paise for row in schedule)
        assert abs(total_principal - principal_paise) <= tenure_months

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

        original_schedule = generate_schedule(
            principal_paise=outstanding_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=remaining_months,
            start_date="2025-01-01",
        )
        original_interest = total_interest_paise(original_schedule)
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


class TestCreditCardEngineProperties:
    """Property tests for Credit Card Engine (business capability: lending)."""

    @given(
        limit_paise=st.integers(min_value=100000, max_value=5000000),
        outstanding_paise=st.integers(min_value=0, max_value=5000000),
    )
    @settings(max_examples=20)
    def test_credit_card_utilization_valid(
        self, limit_paise: int, outstanding_paise: int
    ) -> None:
        """Credit utilization is in [0, 10000] bps."""
        from src.engines.credit_card_engine.utilization import compute_utilization

        outstanding = min(outstanding_paise, limit_paise)  # cannot exceed limit
        utilization_bps = compute_utilization(outstanding, limit_paise)
        assert 0 <= utilization_bps <= 10000
        if outstanding == 0:
            assert utilization_bps == 0

    @given(
        limit_paise=st.integers(min_value=100000, max_value=5000000),
        outstanding_paise=st.integers(min_value=0, max_value=5000000),
    )
    @settings(max_examples=20)
    def test_credit_card_available_credit(
        self, limit_paise: int, outstanding_paise: int
    ) -> None:
        """Available credit = limit - outstanding."""
        from src.engines.credit_card_engine.utilization import compute_available_credit

        outstanding = min(outstanding_paise, limit_paise)
        available = compute_available_credit(limit_paise, outstanding)
        assert available == limit_paise - outstanding
        assert available >= 0
