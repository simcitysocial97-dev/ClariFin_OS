"""
M9-C39 — Deterministic regression tests for the reduce-EMI prepayment fix.

Root cause: compute_emi_fixed uses ROUND_HALF_EVEN which can round DOWN when
the fractional true EMI lies just below a half-paise boundary. Compounded over
a long tenure at high rate this creates an asymmetric quantization drift where
the regenerated reduce-EMI tail's total payment EXCEEDS the original schedule's
total despite a principal prepayment — violating the financial invariant that
prepayment must reduce (or at worst leave unchanged within tolerance) total
payment.

Fix: in apply_prepayment_at_month (reduce_emi mode), after regenerating the
tail we verify new_total <= original_total + tolerance. If not, we increment
the EMI by 1 and regenerate until the condition holds (typically 1-2 iterations
since each +1 changes total by ~annuity_factor, hundreds of thousands of paise).
"""

from src.engines.loan_engine.amortization import generate_schedule
from src.engines.loan_engine.models import PrepaymentMode
from src.engines.loan_engine.prepayment import apply_prepayment_at_month


class TestC39ReduceEmiRegression:
    """Deterministic regressions for C39 reduce-EMI total-payment invariant."""

    def test_original_failing_case_principal_45563799_rate_3312(self):
        """Exact failing case from Hypothesis: P=45563799, r=33.12%, n=356, prepay=10000 at month 1."""
        principal = 45_563_799
        rate = 3312
        tenure = 356
        start_date = "2000-01-01"
        schedule = generate_schedule(principal, rate, tenure, start_date)

        new_schedule, result = apply_prepayment_at_month(
            schedule,
            prepayment_month=1,
            prepayment_paise=10_000,
            annual_rate_bps=rate,
            mode=PrepaymentMode.REDUCE_EMI,
        )

        orig_total = sum(r.emi_paise for r in schedule)
        new_total = sum(r.emi_paise for r in new_schedule)
        tol = tenure * 10 + 1000

        assert result.new_remaining_months == tenure
        assert result.new_emi_paise <= result.original_emi_paise + 10
        assert (
            new_total <= orig_total + tol
        ), f"new_total={new_total} > orig_total={orig_total}+tol={tol}"

    def test_various_prepayment_months_same_loan(self):
        """Same loan at different prepayment months — invariant must hold everywhere."""
        principal = 45_563_799
        rate = 3312
        tenure = 356
        start_date = "2000-01-01"
        schedule = generate_schedule(principal, rate, tenure, start_date)
        orig_total = sum(r.emi_paise for r in schedule)

        for month in [1, 50, 100, 200, 300, tenure]:
            new_schedule, result = apply_prepayment_at_month(
                schedule,
                prepayment_month=month,
                prepayment_paise=10_000,
                annual_rate_bps=rate,
                mode=PrepaymentMode.REDUCE_EMI,
            )
            orig_rem = len(schedule) - month + 1
            if result.loan_closed:
                assert result.new_remaining_months == 0
                continue
            assert result.new_remaining_months == orig_rem
            new_total = sum(r.emi_paise for r in new_schedule)
            tol = orig_rem * 10 + 1000
            assert (
                new_total <= orig_total + tol
            ), f"month={month}: new_total={new_total} > orig_total={orig_total}+tol={tol}"

    def test_high_rate_low_principal_long_tenure(self):
        """Another extreme: high rate (33.4%), moderate principal, 330 months."""
        principal = 528_715_454  # reconstructed from Hypothesis failure
        rate = 3340
        tenure = 330
        start_date = "2000-01-01"
        schedule = generate_schedule(principal, rate, tenure, start_date)
        orig_total = sum(r.emi_paise for r in schedule)

        new_schedule, result = apply_prepayment_at_month(
            schedule,
            prepayment_month=1,
            prepayment_paise=10_000,
            annual_rate_bps=rate,
            mode=PrepaymentMode.REDUCE_EMI,
        )

        assert result.new_remaining_months == tenure
        new_total = sum(r.emi_paise for r in new_schedule)
        tol = tenure * 10 + 1000
        assert (
            new_total <= orig_total + tol
        ), f"new_total={new_total} > orig_total={orig_total}+tol={tol}"
        assert result.interest_saved_paise > 0

    def test_reduce_tenure_unchanged_by_fix(self):
        """The fix must NOT affect reduce_tenure mode behavior."""
        principal = 45_563_799
        rate = 3312
        tenure = 356
        schedule = generate_schedule(principal, rate, tenure, "2000-01-01")

        new_schedule, result = apply_prepayment_at_month(
            schedule,
            prepayment_month=1,
            prepayment_paise=10_000,
            annual_rate_bps=rate,
            mode=PrepaymentMode.REDUCE_TENURE,
        )

        assert result.new_emi_paise == result.original_emi_paise
        assert result.new_remaining_months < result.original_remaining_months
        new_total = sum(r.emi_paise for r in new_schedule)
        orig_total = sum(r.emi_paise for r in schedule)
        assert new_total <= orig_total

    def test_interest_always_non_negative_after_prepay(self):
        """Prepayment must never increase total interest."""
        principal = 45_563_799
        rate = 3312
        tenure = 356
        schedule = generate_schedule(principal, rate, tenure, "2000-01-01")
        orig_interest = schedule[-1].cumulative_interest_paise

        new_schedule, result = apply_prepayment_at_month(
            schedule,
            prepayment_month=1,
            prepayment_paise=10_000,
            annual_rate_bps=rate,
            mode=PrepaymentMode.REDUCE_EMI,
        )
        new_interest = new_schedule[-1].cumulative_interest_paise

        assert (
            new_interest <= orig_interest
        ), f"interest increased: {new_interest} > {orig_interest}"
        assert result.interest_saved_paise >= 0
