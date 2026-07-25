"""Property tests for Forecasting — financial intelligence forecasting."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.invariant import assert_forecast_invariants


class TestForecastEngineProperties:
    """Property tests for Financial Intelligence forecasting."""

    @given(
        income_paise=st.integers(min_value=100000, max_value=2000000),
        expense_paise=st.integers(min_value=50000, max_value=1500000),
    )
    @settings(max_examples=20)
    def test_forecast_cashflow_returns_dict(
        self,
        income_paise: int,
        expense_paise: int,
    ) -> None:
        """Forecast cashflow returns dict with forecast list."""
        from src.engines.financial_intelligence.forecasting import forecast_cashflow

        history = [
            {
                "month": "2026-01",
                "income_paise": income_paise,
                "expense_paise": expense_paise,
                "surplus_paise": income_paise - expense_paise,
            },
            {
                "month": "2026-02",
                "income_paise": income_paise,
                "expense_paise": expense_paise,
                "surplus_paise": income_paise - expense_paise,
            },
            {
                "month": "2026-03",
                "income_paise": income_paise,
                "expense_paise": expense_paise,
                "surplus_paise": income_paise - expense_paise,
            },
        ]
        result = forecast_cashflow(history, forecast_months=3)
        assert isinstance(result, dict)
        assert "forecast" in result
        assert len(result["forecast"]) == 3

    @given(
        income_paise=st.integers(min_value=100000, max_value=2000000),
        expense_paise=st.integers(min_value=50000, max_value=1500000),
    )
    @settings(max_examples=20)
    def test_forecast_confidence_in_range(
        self,
        income_paise: int,
        expense_paise: int,
    ) -> None:
        """Forecast confidence_bps must be in [0, 10000] range."""
        from src.engines.financial_intelligence.forecasting import forecast_cashflow

        history = [
            {
                "month": "2026-01",
                "income_paise": income_paise,
                "expense_paise": expense_paise,
                "surplus_paise": income_paise - expense_paise,
            },
            {
                "month": "2026-02",
                "income_paise": income_paise,
                "expense_paise": expense_paise,
                "surplus_paise": income_paise - expense_paise,
            },
        ]
        result = forecast_cashflow(history, forecast_months=2)
        if "confidence_bps" in result:
            assert 0 <= result["confidence_bps"] <= 10000

    @given(
        month_data=st.lists(
            st.fixed_dictionaries(
                {
                    "month": st.just("2025-01"),
                    "income_paise": st.integers(min_value=50000, max_value=1000000),
                    "expense_paise": st.integers(min_value=50000, max_value=1000000),
                    "surplus_paise": st.integers(min_value=-100000, max_value=1000000),
                }
            ),
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
        assert result["risk_level"] in ("low", "warning", "high")
