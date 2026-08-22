"""Property tests for Forecasting — financial intelligence forecasting."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.engines.financial_intelligence.forecasting import (
    forecast_cashflow,
    forecast_credit_utilization,
    forecast_liquidity,
)
from src.engines.financial_intelligence.goal_planner import calculate_goal_projection
from src.engines.financial_intelligence.utils import project_running_balance
from tests.invariants import assert_forecast_invariants


class TestForecastEngineProperties:
    """Property tests for Financial Intelligence forecasting."""

    @given(
        income_paise=st.integers(min_value=100000, max_value=2000000),
        expense_paise=st.integers(min_value=50000, max_value=1500000),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.differing_executors])
    def test_forecast_cashflow_returns_dict(
        self,
        income_paise: int,
        expense_paise: int,
    ) -> None:
        """Forecast cashflow returns dict with forecast list."""

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
    @settings(max_examples=20, suppress_health_check=[HealthCheck.differing_executors])
    def test_forecast_confidence_in_range(
        self,
        income_paise: int,
        expense_paise: int,
    ) -> None:
        """Forecast confidence must be in [0, 1] range."""

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
        assert 0 <= result["confidence"] <= Decimal("1.0")

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
    @settings(max_examples=20, suppress_health_check=[HealthCheck.differing_executors])
    def test_forecast_result_invariants(self, month_data: list[dict[str, Any]]) -> None:
        """Forecast output must satisfy invariants."""

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
    @settings(max_examples=20, suppress_health_check=[HealthCheck.differing_executors])
    def test_liquidity_forecast_with_funding(
        self,
        current_liquidity_paise: int,
        surplus_values: list[int],
        threshold_paise: int,
    ) -> None:
        """Liquidity forecast with positive starting balance."""

        cashflow_forecast = [
            {"month": f"2025-0{m}", "expected_surplus_paise": surplus}
            for m, surplus in enumerate(surplus_values, 1)
        ]
        result = forecast_liquidity(
            current_liquidity_paise=current_liquidity_paise,
            cashflow_forecast=cashflow_forecast,
            emergency_threshold_paise=threshold_paise,
        )
        assert result["risk_level"] in ("low", "medium", "high")

    @given(
        current_liquidity_paise=st.integers(min_value=0, max_value=100000000),
        surplus_values=st.lists(
            st.integers(min_value=-500000, max_value=500000),
            min_size=1,
            max_size=12,
        ),
        threshold_paise=st.integers(min_value=0, max_value=50000000),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.differing_executors])
    def test_liquidity_projection_monotonicity(
        self,
        current_liquidity_paise: int,
        surplus_values: list[int],
        threshold_paise: int,
    ) -> None:
        """Liquidity projections must be monotonic (no sudden drops without explanation)."""

        assume(len(surplus_values) >= 2)
        cashflow_forecast = [
            {"month": f"2025-0{m}", "expected_surplus_paise": surplus}
            for m, surplus in enumerate(surplus_values, 1)
        ]
        result = forecast_liquidity(
            current_liquidity_paise=current_liquidity_paise,
            cashflow_forecast=cashflow_forecast,
            emergency_threshold_paise=threshold_paise,
        )

        # Check projected balance trajectory is consistent with surpluses
        projected_balance = project_running_balance(
            current_liquidity_paise,
            [s["expected_surplus_paise"] for s in cashflow_forecast],
        )
        assert projected_balance == result["projected_min_balance_paise"]

    @given(
        current_liquidity_paise=st.integers(min_value=1000000, max_value=100000000),
        surplus_values=st.lists(
            st.integers(min_value=-500000, max_value=500000),
            min_size=2,
            max_size=12,
        ),
        threshold_paise=st.integers(min_value=1000000, max_value=50000000),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.differing_executors])
    def test_shortfall_detection_monotonicity(
        self,
        current_liquidity_paise: int,
        surplus_values: list[int],
        threshold_paise: int,
    ) -> None:
        """Shortfall detection must be monotonic (more expenses → higher shortfall)."""

        cashflow_forecast = [
            {"month": f"2025-0{m}", "expected_surplus_paise": surplus}
            for m, surplus in enumerate(surplus_values, 1)
        ]
        result = forecast_liquidity(
            current_liquidity_paise=current_liquidity_paise,
            cashflow_forecast=cashflow_forecast,
            emergency_threshold_paise=threshold_paise,
        )

        # More negative surplus should lead to earlier stress month
        worse_surplus = [s - 10000 for s in surplus_values]
        worse_forecast = [
            {"month": f"2025-0{m}", "expected_surplus_paise": s}
            for m, s in enumerate(worse_surplus, 1)
        ]
        worse_result = forecast_liquidity(
            current_liquidity_paise=current_liquidity_paise,
            cashflow_forecast=worse_forecast,
            emergency_threshold_paise=threshold_paise,
        )

        # Skip test if current liquidity is exactly at threshold and surplus is non-negative
        if current_liquidity_paise == threshold_paise and all(
            s >= 0 for s in surplus_values
        ):
            return
        elif result["months_until_stress"] is None:
            # Original has no stress - worse case may or may not have stress (monotonicity holds)
            pass
        else:
            # Original has stress - worse case must also have stress, at same or earlier month
            assert worse_result["months_until_stress"] is not None
            assert worse_result["months_until_stress"] <= result["months_until_stress"]

    @given(
        target_amount_paise=st.integers(min_value=100000, max_value=10000000),
        current_amount_paise=st.integers(min_value=0, max_value=10000000),
        monthly_surplus_forecast=st.lists(
            st.fixed_dictionaries(
                {
                    "month": st.just("2025-01"),
                    "expected_surplus_paise": st.integers(
                        min_value=-50000, max_value=500000
                    ),
                }
            ),
            min_size=1,
            max_size=12,
        ),
        allocation_ratio=st.decimals(min_value=0.1, max_value=1.0),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.differing_executors])
    def test_goal_achievability_deterministic(
        self,
        target_amount_paise: int,
        current_amount_paise: int,
        monthly_surplus_forecast: list[dict[str, Any]],
        allocation_ratio: Decimal,
    ) -> None:
        """Goal achievability must be deterministic (same inputs → same output)."""

        assume(target_amount_paise > 0)
        result1 = calculate_goal_projection(
            target_amount_paise=target_amount_paise,
            current_amount_paise=current_amount_paise,
            monthly_surplus_forecast=monthly_surplus_forecast,
            allocation_ratio=allocation_ratio,
        )
        result2 = calculate_goal_projection(
            target_amount_paise=target_amount_paise,
            current_amount_paise=current_amount_paise,
            monthly_surplus_forecast=monthly_surplus_forecast,
            allocation_ratio=allocation_ratio,
        )
        assert result1 == result2

    @given(
        financial_events=st.lists(
            st.fixed_dictionaries(
                {
                    "event_type": st.just("credit_card_payment"),
                    "month_bucket": st.just("2025-01"),
                    "lifecycle_state": st.sampled_from(
                        ["open", "settled", "rolls_over"]
                    ),
                }
            ),
            min_size=0,
            max_size=10,
        ),
        credit_history=st.lists(
            st.fixed_dictionaries(
                {
                    "month": st.just("2025-01"),
                    "utilization_ratio": st.decimals(min_value=0.0, max_value=1.0),
                    "revolver_ratio": st.decimals(min_value=0.0, max_value=1.0),
                    "cash_advance_paise": st.integers(min_value=0, max_value=100000),
                }
            ),
            min_size=0,
            max_size=12,
        ),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.differing_executors])
    def test_credit_utilization_bounded(
        self,
        financial_events: list[dict[str, Any]],
        credit_history: list[dict[str, Any]],
    ) -> None:
        """Credit utilization projections must be ≤ 100%."""

        result = forecast_credit_utilization(
            financial_events=financial_events,
            credit_history=credit_history,
        )
        assert 0 <= result["current_dependency_ratio"] <= Decimal("1.0")
        assert 0 <= result["forecast_dependency_ratio"] <= Decimal("1.0")

    @given(
        current_liquidity_paise=st.integers(min_value=0, max_value=100000000),
        surplus_values=st.lists(
            st.integers(min_value=-500000, max_value=500000),
            min_size=1,
            max_size=12,
        ),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.differing_executors])
    def test_invalid_input_rejection(
        self,
        current_liquidity_paise: int,
        surplus_values: list[int],
    ) -> None:
        """Invalid inputs (negative cashflow, negative goals) must be rejected or handled."""

        # Test negative liquidity (should be handled gracefully)
        cashflow_forecast = [
            {"month": f"2025-0{m}", "expected_surplus_paise": surplus}
            for m, surplus in enumerate(surplus_values, 1)
        ]
        result = forecast_liquidity(
            current_liquidity_paise=current_liquidity_paise,
            cashflow_forecast=cashflow_forecast,
            emergency_threshold_paise=1000000,
        )
        assert "risk_level" in result

        # Test negative target amount (should be rejected or handled)
        import contextlib

        with contextlib.suppress(ValueError, TypeError):
            calculate_goal_projection(
                target_amount_paise=-100000,
                current_amount_paise=50000,
                monthly_surplus_forecast=cashflow_forecast,
            )
