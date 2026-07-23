"""Property tests for Forecasting — financial intelligence forecasting."""
from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))



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
            {"month": "2026-01", "income_paise": income_paise, "expense_paise": expense_paise,
             "surplus_paise": income_paise - expense_paise},
            {"month": "2026-02", "income_paise": income_paise, "expense_paise": expense_paise,
             "surplus_paise": income_paise - expense_paise},
            {"month": "2026-03", "income_paise": income_paise, "expense_paise": expense_paise,
             "surplus_paise": income_paise - expense_paise},
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
            {"month": "2026-01", "income_paise": income_paise, "expense_paise": expense_paise,
             "surplus_paise": income_paise - expense_paise},
            {"month": "2026-02", "income_paise": income_paise, "expense_paise": expense_paise,
             "surplus_paise": income_paise - expense_paise},
        ]
        result = forecast_cashflow(history, forecast_months=2)
        if "confidence_bps" in result:
            assert 0 <= result["confidence_bps"] <= 10000
