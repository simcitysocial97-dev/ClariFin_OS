"""Property tests for Credit Cards — statement processing, EMI conversion."""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.invariant import (
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
