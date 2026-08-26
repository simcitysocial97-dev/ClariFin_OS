"""Direct unit tests for src/engines/financial_intelligence/forecasting.py.

M9-C42.25 — direct behavioral ownership of forecasting functions: cashflow
projection, liquidity risk matrix, credit dependency forecasting, and cash
shortfall detection. Existing property tests covered shape/membership only;
these tests pin branch semantics.
"""

from decimal import Decimal

from src.engines.financial_intelligence.forecasting import (
    _compute_current_credit_dependency,
    _next_month,
    _weighted_average,
    detect_future_cash_shortfall,
    forecast_cashflow,
    forecast_credit_utilization,
    forecast_liquidity,
)

# ============================================================
# Internal helpers
# ============================================================


def test_next_month_internal_rollover():
    assert _next_month("2025-12") == "2026-01"
    assert _next_month("2025-05") == "2025-06"


def test_next_month_short_string_defaults_to_january():
    assert _next_month("2025") == "2025-02"


def test_weighted_average_empty():
    assert _weighted_average([]) == 0.0


def test_weighted_average_linear():
    assert _weighted_average([10, 20]) == (10 * 1 + 20 * 2) / 3


# ============================================================
# forecast_cashflow
# ============================================================


def test_forecast_cashflow_empty_history_neutral():
    result = forecast_cashflow([])
    assert result["confidence"] == Decimal("0.5")
    assert result["model_version"] == "v1.0-weightedaverage"
    assert len(result["forecast"]) == 3
    for row in result["forecast"]:
        assert row["expected_income_paise"] == 0
        assert row["expected_expense_paise"] == 0
        assert row["expected_surplus_paise"] == 0
    assert result["forecast"][0]["month"] == "2026-01"


def test_forecast_cashflow_months_clamped_to_range():
    assert len(forecast_cashflow([], forecast_months=0)["forecast"]) == 1
    assert len(forecast_cashflow([], forecast_months=13)["forecast"]) == 12


def test_forecast_cashflow_stable_history_exact_projection():
    history = [
        {"month": f"2026-0{i}", "income_paise": 100_000, "expense_paise": 60_000}
        for i in range(1, 4)
    ]
    result = forecast_cashflow(history, forecast_months=2)
    rows = result["forecast"]
    assert len(rows) == 2
    assert rows[0]["month"] == "2026-04"
    for row in rows:
        assert row["expected_income_paise"] == 100_000
        assert row["expected_expense_paise"] == 60_000
        assert row["expected_surplus_paise"] == 40_000
    # Zero variance -> maximum confidence.
    assert result["confidence"] == Decimal("1")


def test_forecast_cashflow_weights_recent_months_higher():
    history = [
        {"month": "2026-01", "income_paise": 100, "expense_paise": 0},
        {"month": "2026-02", "income_paise": 200, "expense_paise": 0},
    ]
    result = forecast_cashflow(history)
    # Weighted average with weights [1,2]: (100 + 400) / 3 = 166.67 -> 167
    assert result["forecast"][0]["expected_income_paise"] == 167


def test_forecast_cashflow_uses_explicit_surplus_for_confidence():
    # Surplus keys override income-expense in the variance input but not in
    # the projected values (which come from income/expense averages).
    history = [
        {"month": "2026-01", "income_paise": 100, "expense_paise": 50, "surplus_paise": 50},
        {"month": "2026-02", "income_paise": 100, "expense_paise": 50, "surplus_paise": 50},
    ]
    result = forecast_cashflow(history)
    assert result["forecast"][0]["expected_surplus_paise"] == 50
    assert result["confidence"] == Decimal("1")


def test_forecast_cashflow_computes_missing_surplus():
    history = [
        {"month": "2026-01", "income_paise": 100, "expense_paise": 30},
    ]
    result = forecast_cashflow(history)
    assert result["forecast"][0]["expected_surplus_paise"] == 70


def test_forecast_cashflow_sorts_history_by_month():
    history = [
        {"month": "2026-03", "income_paise": 300, "expense_paise": 0},
        {"month": "2026-01", "income_paise": 100, "expense_paise": 0},
        {"month": "2026-02", "income_paise": 200, "expense_paise": 0},
    ]
    result = forecast_cashflow(history)
    # Sorted weights: (100*1 + 200*2 + 300*3) / 6 = 1400/6 -> 233
    assert result["forecast"][0]["expected_income_paise"] == 233
    # Forecast starts after the latest month.
    assert result["forecast"][0]["month"] == "2026-04"


def test_forecast_cashflow_negative_surplus_low_confidence():
    history = [
        {"month": "2026-01", "income_paise": 0, "expense_paise": 10_000_000},
        {"month": "2026-02", "income_paise": 10_000_000, "expense_paise": 0},
    ]
    result = forecast_cashflow(history)
    assert result["confidence"] < Decimal("1")


# ============================================================
# forecast_liquidity
# ============================================================


def test_forecast_liquidity_empty_forecast_healthy():
    result = forecast_liquidity(5_000_000, [])
    assert result["months_until_stress"] is None
    assert result["projected_min_balance_paise"] == 5_000_000
    assert result["risk_level"] == "low"


def test_forecast_liquidity_empty_forecast_below_threshold_high():
    result = forecast_liquidity(1_000_000, [])
    assert result["risk_level"] == "high"


def test_forecast_liquidity_empty_forecast_exact_threshold_low():
    result = forecast_liquidity(3_000_000, [])
    assert result["risk_level"] == "low"


def forecast_row(month, surplus):
    return {"month": month, "expected_surplus_paise": surplus}


def test_forecast_liquidity_stress_month_one_is_high():
    result = forecast_liquidity(
        3_000_000, [forecast_row("2026-01", -1)], emergency_threshold_paise=3_000_000
    )
    assert result["months_until_stress"] == 1
    assert result["risk_level"] == "high"


def test_forecast_liquidity_stress_month_two_is_high():
    result = forecast_liquidity(
        3_000_000,
        [forecast_row("2026-01", 0), forecast_row("2026-02", -1)],
        emergency_threshold_paise=3_000_000,
    )
    assert result["months_until_stress"] == 2
    assert result["risk_level"] == "high"


def test_forecast_liquidity_stress_month_three_is_medium():
    result = forecast_liquidity(
        3_000_000,
        [forecast_row("2026-01", 0), forecast_row("2026-02", 0), forecast_row("2026-03", -1)],
        emergency_threshold_paise=3_000_000,
    )
    assert result["months_until_stress"] == 3
    assert result["risk_level"] == "medium"


def test_forecast_liquidity_stress_beyond_three_is_low_when_min_positive():
    result = forecast_liquidity(
        3_000_000,
        [
            forecast_row("2026-01", 0),
            forecast_row("2026-02", 0),
            forecast_row("2026-03", 0),
            forecast_row("2026-04", -1),
        ],
        emergency_threshold_paise=3_000_000,
    )
    assert result["months_until_stress"] == 4
    assert result["projected_min_balance_paise"] == 2_999_999
    # Pinned behavior: stress beyond month 3 with positive min -> 'low'.
    assert result["risk_level"] == "low"


def test_forecast_liquidity_no_stress_but_min_below_threshold_positive_low():
    # Start below threshold, recover immediately: no crossing after start.
    result = forecast_liquidity(
        2_000_000, [forecast_row("2026-01", 2_000_000)], emergency_threshold_paise=3_000_000
    )
    assert result["months_until_stress"] is None
    assert result["projected_min_balance_paise"] == 2_000_000
    assert result["risk_level"] == "low"


def test_forecast_liquidity_projected_min_reconciles():
    surpluses = [-1_000_000, 500_000, -2_000_000]
    result = forecast_liquidity(
        3_000_000, [forecast_row(f"2026-0{i}", s) for i, s in enumerate(surpluses, 1)]
    )
    assert result["projected_min_balance_paise"] == 3_000_000 - 1_000_000 + 500_000 - 2_000_000
    assert result["months_until_stress"] == 1


def test_forecast_liquidity_default_threshold():
    # DEFAULT_EMERGENCY_THRESHOLD_PAISE = 3_000_000
    result = forecast_liquidity(3_000_000, [forecast_row("2026-01", -1)])
    assert result["months_until_stress"] == 1


# ============================================================
# forecast_credit_utilization / _compute_current_credit_dependency
# ============================================================


def test_credit_dependency_from_history_average():
    history = [{"utilization_ratio": Decimal("0.2")}, {"utilization_ratio": Decimal("0.4")}]
    result = forecast_credit_utilization([], history)
    assert result["current_dependency_ratio"] == Decimal("0.3")


def test_credit_utilization_worsening_trend_projects_increase():
    history = [{"utilization_ratio": Decimal("0.2")}, {"utilization_ratio": Decimal("0.4")}]
    result = forecast_credit_utilization([], history)
    assert result["trend"] == "worsening"
    assert result["forecast_dependency_ratio"] == Decimal("0.3") * Decimal("1.1")


def test_credit_utilization_worsening_capped_at_one():
    # [0.9, 1.0]: current 0.95, diff 0.111 -> worsening; 0.95*1.1 > 1 -> capped.
    history = [{"utilization_ratio": Decimal("0.9")}, {"utilization_ratio": Decimal("1.0")}]
    result = forecast_credit_utilization([], history)
    assert result["trend"] == "worsening"
    assert result["forecast_dependency_ratio"] == Decimal("1.0")


def test_credit_utilization_worsening_low_dependency_stays_stable_projection():
    # Worsening trend but current <= 0.1 -> forecast equals current.
    history = [{"utilization_ratio": Decimal("0.01")}, {"utilization_ratio": Decimal("0.09")}]
    result = forecast_credit_utilization([], history)
    assert result["trend"] == "worsening"
    assert result["forecast_dependency_ratio"] == result["current_dependency_ratio"]


def test_credit_utilization_improving_trend_projects_decrease():
    history = [{"utilization_ratio": Decimal("0.4")}, {"utilization_ratio": Decimal("0.2")}]
    result = forecast_credit_utilization([], history)
    assert result["trend"] == "improving"
    assert result["forecast_dependency_ratio"] == Decimal("0.3") * Decimal("0.9")


def test_credit_utilization_stable_projects_current():
    history = [{"utilization_ratio": Decimal("0.5")}]
    result = forecast_credit_utilization([], history)
    assert result["trend"] == "stable"
    assert result["forecast_dependency_ratio"] == Decimal("0.5")


def test_credit_utilization_empty_inputs():
    result = forecast_credit_utilization([], [])
    # No history, no credit events, no revolver behavior -> base 0.1.
    assert result["current_dependency_ratio"] == Decimal("0.1")
    assert result["trend"] == "stable"
    assert result["forecast_dependency_ratio"] == Decimal("0.1")


def test_credit_dependency_falls_back_to_financial_events():
    events = [
        {
            "event_type": "cash_advance",
            "liability_change_paise": 50_000,
            "expense_paise": 100_000,
        }
    ]
    assert _compute_current_credit_dependency(events, []) == Decimal("0.5")


def test_credit_dependency_event_ratio_capped_at_one():
    events = [
        {
            "event_type": "liability_increase",
            "liability_change_paise": 200_000,
            "expense_paise": 100_000,
        }
    ]
    assert _compute_current_credit_dependency(events, []) == Decimal("1.0")


def test_credit_dependency_negative_liability_change_ignored():
    events = [
        {
            "event_type": "cash_advance",
            "liability_change_paise": -10_000,
            "expense_paise": 100_000,
        }
    ]
    assert _compute_current_credit_dependency(events, []) == Decimal("0")


def test_credit_dependency_ignores_other_event_types():
    events = [
        {"event_type": "grocery", "liability_change_paise": 999_999, "expense_paise": 999_999}
    ]
    # No credit events, no revolver behavior -> base 0.1
    assert _compute_current_credit_dependency(events, []) == Decimal("0.1")


def test_credit_dependency_revolver_behavior_defaults_03():
    events = [{"event_type": "payment", "lifecycle_state": "open"}]
    assert _compute_current_credit_dependency(events, []) == Decimal("0.3")


def test_credit_dependency_no_events_defaults_01():
    assert _compute_current_credit_dependency([], []) == Decimal("0.1")


def test_credit_dependency_event_with_zero_expense_returns_zero():
    events = [
        {
            "event_type": "credit_card_cash_advance",
            "liability_change_paise": 50_000,
            "expense_paise": 0,
        }
    ]
    assert _compute_current_credit_dependency(events, []) == Decimal("0")


def test_credit_dependency_history_with_all_none_ratios_is_zero():
    history = [{"utilization_ratio": None}]
    assert _compute_current_credit_dependency([], history) == Decimal("0")


# ============================================================
# detect_future_cash_shortfall
# ============================================================


def liquidity(months_until_stress, projected_min=0, risk_level="low"):
    return {
        "months_until_stress": months_until_stress,
        "projected_min_balance_paise": projected_min,
        "risk_level": risk_level,
    }


def test_shortfall_stress_month_one_critical():
    forecast = [forecast_row("2026-01", -500_000)]
    result = detect_future_cash_shortfall(forecast, liquidity(1, projected_min=-100_000))
    assert result["flag"] is True
    assert result["severity"] == "critical"
    assert result["expected_month"] == "2026-01"
    assert "month 1" in result["reason"]


def test_shortfall_stress_month_two_critical():
    forecast = [forecast_row("2026-01", 0), forecast_row("2026-02", -500_000)]
    result = detect_future_cash_shortfall(forecast, liquidity(2))
    assert result["severity"] == "critical"
    assert result["expected_month"] == "2026-02"


def test_shortfall_stress_month_beyond_forecast_month_is_none():
    forecast = [forecast_row("2026-01", 0)]
    result = detect_future_cash_shortfall(forecast, liquidity(2))
    assert result["severity"] == "critical"
    assert result["expected_month"] is None


def test_shortfall_stress_month_three_warning():
    forecast = [
        forecast_row("2026-01", 0),
        forecast_row("2026-02", 0),
        forecast_row("2026-03", -500_000),
    ]
    result = detect_future_cash_shortfall(forecast, liquidity(3))
    assert result["severity"] == "warning"
    assert result["flag"] is True
    assert result["expected_month"] == "2026-03"


def test_shortfall_negative_surplus_high_risk_warning():
    forecast = [forecast_row("2026-01", -100), forecast_row("2026-02", 0)]
    result = detect_future_cash_shortfall(forecast, liquidity(None, risk_level="high"))
    assert result["severity"] == "warning"
    assert result["expected_month"] == "2026-01"


def test_shortfall_negative_surplus_low_risk_none():
    forecast = [forecast_row("2026-01", -100)]
    result = detect_future_cash_shortfall(forecast, liquidity(None, risk_level="low"))
    assert result["severity"] == "none"
    assert result["flag"] is False
    assert result["expected_month"] is None


def test_shortfall_positive_forecast_none():
    forecast = [forecast_row("2026-01", 100_000)]
    result = detect_future_cash_shortfall(forecast, liquidity(None))
    assert result["severity"] == "none"
    assert "No cash shortfall" in result["reason"]
