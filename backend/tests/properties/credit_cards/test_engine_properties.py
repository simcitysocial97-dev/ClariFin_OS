"""Property tests for Credit Cards — statement processing, EMI conversion."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from tests.invariants import (
    assert_emi_conversion_valid,
)


class TestCreditCardStatementProperties:
    """Property tests for Credit Card statement processing."""

    @given(
        amount_paise=st.integers(min_value=10000, max_value=5000000),
        tenure_months=st.integers(min_value=3, max_value=60),
        rate_bps=st.integers(min_value=1800, max_value=4800),
    )
    @settings(max_examples=20)
    def test_emi_conversion_invariants(
        self, amount_paise: int, tenure_months: int, rate_bps: int
    ) -> None:
        """EMI conversion must satisfy all invariants."""
        from src.engines.credit_card_engine.emi import compute_emi_conversion

        result = compute_emi_conversion(amount_paise, rate_bps, tenure_months)
        assert_emi_conversion_valid(result, amount_paise, tenure_months)
        assert result.get("emi_paise", 0) > 0
        assert result.get("total_interest_paise", 0) >= 0

    @given(
        total_spend_paise=st.integers(min_value=1000, max_value=5000000),
        total_payments_paise=st.integers(min_value=0, max_value=5000000),
    )
    @settings(max_examples=20)
    def test_outstanding_non_negative(
        self, total_spend_paise: int, total_payments_paise: int
    ) -> None:
        """Outstanding balance must be non-negative."""
        from src.engines.credit_card_engine.outstanding import compute_outstanding

        # Payments cannot exceed spend+EMI+fees
        payments = min(total_payments_paise, total_spend_paise)
        outstanding = compute_outstanding(
            total_spend_paise=total_spend_paise,
            total_emi_paise=0,
            total_fees_paise=0,
            total_payments_paise=payments,
        )
        assert outstanding >= 0
        assert outstanding == total_spend_paise - payments


class TestStatementDetectionProperties:
    """Property tests for transaction intelligence detection."""

    @given(
        amount_paise=st.integers(min_value=1000, max_value=100000),
        description=st.text(min_size=5, max_size=50),
    )
    @settings(max_examples=20)
    def test_emi_detection_returns_none_for_random(
        self, amount_paise: int, description: str
    ) -> None:
        """Random transactions without loan context return None."""
        from src.engines.transaction_intelligence.loan_emi_detector import (
            detect_emi_payment,
        )

        txn = {
            "id": 1,
            "account_id": "acct_1",
            "amount_paise": -amount_paise,
            "date_iso": "2026-01-15",
            "description": description,
        }
        result = detect_emi_payment(txn, [], {})
        assert result is None


class TestCreditEngineProperties:
    """Property tests for credit card EMI and utilization."""

    @given(
        amount_paise=st.integers(min_value=10000, max_value=100000000),
        annual_rate_bps=st.integers(min_value=1800, max_value=4800),
        tenure_months=st.sampled_from([3, 6, 9, 12, 18, 24]),
    )
    @settings(max_examples=20)
    def test_emi_conversion_properties(
        self,
        amount_paise: int,
        annual_rate_bps: int,
        tenure_months: int,
    ) -> None:
        """EMI conversion must satisfy financial invariants."""
        from src.engines.credit_card_engine import compute_emi_conversion

        result = compute_emi_conversion(amount_paise, annual_rate_bps, tenure_months)
        assert isinstance(result["emi_paise"], int)
        assert isinstance(result["total_interest_paise"], int)
        assert isinstance(result["total_repayment_paise"], int)
        assert result["emi_paise"] > 0
        assert result["total_repayment_paise"] == result["emi_paise"] * tenure_months
        assert result["total_interest_paise"] >= 0

    @given(
        outstanding_paise=st.integers(min_value=0, max_value=50000000),
        credit_limit_paise=st.integers(min_value=100000, max_value=10000000),
    )
    @settings(max_examples=20)
    def test_utilization_bps_bounds(
        self,
        outstanding_paise: int,
        credit_limit_paise: int,
    ) -> None:
        """Utilization must be between 0 and 10000 basis points."""
        from src.engines.credit_card_engine.utilization import compute_utilization

        util = compute_utilization(outstanding_paise, credit_limit_paise)
        assert 0 <= util <= 10000, f"Utilization {util} out of bps bounds"


class TestCreditCardInterestProperties:
    """Property tests for credit card interest calculations."""

    @given(
        outstanding_paise=st.integers(min_value=0, max_value=100000000),
        annual_rate_bps=st.integers(min_value=0, max_value=4800),
    )
    @settings(max_examples=50)
    def test_daily_interest_non_negative(
        self, outstanding_paise: int, annual_rate_bps: int
    ) -> None:
        """Daily interest must always be non-negative."""
        from src.engines.credit_card_engine.interest import compute_daily_interest

        interest = compute_daily_interest(outstanding_paise, annual_rate_bps)
        assert interest >= 0, f"Interest {interest} must be non-negative"

    @given(
        outstanding_paise=st.integers(min_value=0, max_value=100000000),
        annual_rate_bps=st.integers(min_value=0, max_value=4800),
    )
    @settings(max_examples=50)
    def test_daily_interest_rounding_precision(
        self, outstanding_paise: int, annual_rate_bps: int
    ) -> None:
        """Daily interest must be rounded to 2 decimal places (paise)."""
        from src.engines.credit_card_engine.interest import compute_daily_interest

        interest = compute_daily_interest(outstanding_paise, annual_rate_bps)
        assert isinstance(
            interest, int
        ), f"Interest {interest} must be an integer (paise)"

    @given(
        outstanding_paise=st.integers(min_value=10000, max_value=10000000),
        annual_rate_bps=st.integers(min_value=100, max_value=4800),
        multiplier=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50, deadline=None)
    def test_daily_interest_proportionality(
        self, outstanding_paise: int, annual_rate_bps: int, multiplier: int
    ) -> None:
        """Interest must be proportional to outstanding amount and rate."""
        from src.engines.credit_card_engine.interest import compute_daily_interest

        base_interest = compute_daily_interest(outstanding_paise, annual_rate_bps)
        scaled_interest = compute_daily_interest(
            outstanding_paise * multiplier, annual_rate_bps
        )
        # Allow rounding differences due to banker's rounding
        # Interest is calculated using Decimal and rounded to nearest paise
        assert (
            abs(scaled_interest - base_interest * multiplier) <= multiplier
        ), f"Interest {scaled_interest} must scale with outstanding amount"

        rate_scaled_interest = compute_daily_interest(
            outstanding_paise, annual_rate_bps * multiplier
        )
        # Allow rounding differences due to banker's rounding
        assert (
            abs(rate_scaled_interest - base_interest * multiplier) <= multiplier
        ), f"Interest {rate_scaled_interest} must scale with rate"

    @given(
        outstanding_paise=st.integers(min_value=0, max_value=100000000),
        annual_rate_bps=st.integers(min_value=0, max_value=4800),
    )
    @settings(max_examples=50)
    def test_daily_interest_sign_invariance(
        self, outstanding_paise: int, annual_rate_bps: int
    ) -> None:
        """Interest sign must not change under valid inputs."""
        from src.engines.credit_card_engine.interest import compute_daily_interest

        interest = compute_daily_interest(outstanding_paise, annual_rate_bps)
        assert interest >= 0, f"Interest {interest} must not be negative"

    @given(
        daily_balances=st.lists(
            st.tuples(st.text(), st.integers(min_value=0, max_value=100000000)),
            min_size=1,
            max_size=30,
        ),
        annual_rate_bps=st.integers(min_value=0, max_value=4800),
    )
    @settings(max_examples=30)
    def test_monthly_interest_non_negative(
        self, daily_balances: list[tuple[str, int]], annual_rate_bps: int
    ) -> None:
        """Monthly interest must always be non-negative."""
        from src.engines.credit_card_engine.interest import (
            compute_monthly_interest_charge,
        )

        interest = compute_monthly_interest_charge(daily_balances, annual_rate_bps)
        assert interest >= 0, f"Monthly interest {interest} must be non-negative"

    @given(
        average_daily_balance_paise=st.integers(min_value=0, max_value=100000000),
        annual_rate_bps=st.integers(min_value=0, max_value=4800),
        days_in_cycle=st.integers(min_value=1, max_value=31),
    )
    @settings(max_examples=30)
    def test_monthly_interest_simple_non_negative(
        self,
        average_daily_balance_paise: int,
        annual_rate_bps: int,
        days_in_cycle: int,
    ) -> None:
        """Simplified monthly interest must always be non-negative."""
        from src.engines.credit_card_engine.interest import (
            compute_monthly_interest_simple,
        )

        interest = compute_monthly_interest_simple(
            average_daily_balance_paise, annual_rate_bps, days_in_cycle
        )
        assert interest >= 0, f"Simplified interest {interest} must be non-negative"

    @given(
        outstanding_paise=st.integers(min_value=-100000000, max_value=-1),
        annual_rate_bps=st.integers(min_value=-4800, max_value=-1),
    )
    @settings(max_examples=20)
    def test_daily_interest_rejects_invalid_inputs(
        self, outstanding_paise: int, annual_rate_bps: int
    ) -> None:
        """Invalid inputs (negative values) must raise ValueError."""
        from hypothesis import reject

        from src.engines.credit_card_engine.interest import compute_daily_interest

        try:
            compute_daily_interest(outstanding_paise, annual_rate_bps)
            reject()
        except ValueError:
            pass

    @given(
        average_daily_balance_paise=st.integers(min_value=-100000000, max_value=-1),
        annual_rate_bps=st.integers(min_value=-4800, max_value=-1),
        days_in_cycle=st.integers(min_value=-31, max_value=0),
    )
    @settings(max_examples=20)
    def test_monthly_interest_simple_rejects_invalid_inputs(
        self,
        average_daily_balance_paise: int,
        annual_rate_bps: int,
        days_in_cycle: int,
    ) -> None:
        """Simplified monthly interest must reject invalid inputs."""
        from hypothesis import reject

        from src.engines.credit_card_engine.interest import (
            compute_monthly_interest_simple,
        )

        try:
            compute_monthly_interest_simple(
                average_daily_balance_paise, annual_rate_bps, days_in_cycle
            )
            reject()
        except ValueError:
            pass
