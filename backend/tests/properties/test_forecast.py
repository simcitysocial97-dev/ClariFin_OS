"""Property tests for Forecast Engine using Hypothesis."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Import domain invariants
from tests.domain.invariants import assert_forecast_invariants


class TestForecastEngineProperties:
    """Property tests for financial forecasting functions."""

    @given(
        month_data=st.lists(
            st.fixed_dictionaries({
                "month": st.just("2025-01"),
                "income_paise": st.integers(min_value=50000, max_value=1000000),
                "expense_paise": st.integers(min_value=50000, max_value=1000000),
                "surplus_paise": st.integers(min_value=-100000, max_value=1000000),
            }),
            min_size=1,
            max_size=12,
        ),
    )
    @settings(max_examples=20)
    def test_forecast_result_invariants(self, month_data: list[dict[str, Any]]) -> None:
        """Forecast output must satisfy invariants."""
        from src.engines.financial_intelligence import forecast_cashflow

        result = forecast_cashflow(month_data, forecast_months=3)

        assert_forecast_invariants(result)

        # Verify forecast has correct number of months
        assert len(result["forecast"]) == 3

    @given(
        current_liquidity_paise=st.integers(min_value=1000000, max_value=100000000),
        surplus_values=st.lists(
            st.integers(min_value=-100000, max_value=500000),
            min_size=1,
            max_size=12,
        ),
        threshold_paise=st.integers(min_value=1000000, max_value=50000000),
    )
    @settings(max_examples=20)
    def test_liquidity_forecast_with_funding(
        self,
        current_liquidity_paise: int,
        surplus_values: list[int],
        threshold_paise: int,
    ) -> None:
        """Liquidity forecast with positive starting balance."""
        from src.engines.financial_intelligence import forecast_liquidity

        cashflow_forecast = [
            {"month": f"2025-0{m}", "expected_surplus_paise": surplus}
            for m, surplus in enumerate(surplus_values, 1)
        ]

        result = forecast_liquidity(
            current_liquidity_paise=current_liquidity_paise,
            cashflow_forecast=cashflow_forecast,
            emergency_threshold_paise=threshold_paise,
        )

        # Risk level must be valid
        assert result["risk_level"] in ("low", "warning", "high")


class TestCreditEngineProperties:
    """Property tests for credit card engine."""

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

        # All values must be integers
        assert isinstance(result["emi_paise"], int)
        assert isinstance(result["total_interest_paise"], int)
        assert isinstance(result["total_repayment_paise"], int)

        # EMI must be positive
        assert result["emi_paise"] > 0

        # Total repayment = EMI * tenure
        assert result["total_repayment_paise"] == result["emi_paise"] * tenure_months

        # Total interest >= 0
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

        # Utilization is in basis points (0-10000)
        assert 0 <= util <= 10000, f"Utilization {util} out of bps bounds"
