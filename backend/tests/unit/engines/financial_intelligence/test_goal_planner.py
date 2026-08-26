"""Direct unit tests for src/engines/financial_intelligence/goal_planner.py.

M9-C42.25 — direct behavioral ownership of goal projection, emergency fund,
debt payoff, goal health scoring, and household goal summary.
"""

from decimal import Decimal

from src.engines.financial_intelligence.goal_planner import (
    DEFAULT_EMERGENCY_MONTHS,
    DEFAULT_GOAL_ALLOCATION_RATIO,
    _months_to_payoff,
    calculate_debt_payoff_projection,
    calculate_emergency_fund_target,
    calculate_goal_health,
    calculate_goal_projection,
    calculate_household_goal_summary,
)


def row(month, surplus):
    return {"month": month, "expected_surplus_paise": surplus}


def test_goal_allocation_defaults():
    assert Decimal("0.50") == DEFAULT_GOAL_ALLOCATION_RATIO
    assert DEFAULT_EMERGENCY_MONTHS == 6


# ============================================================
# calculate_goal_projection
# ============================================================


def test_projection_already_achieved_exact():
    result = calculate_goal_projection(100_000, 100_000, [])
    assert result["achieved"] is True
    assert result["months_required"] == 0


def test_projection_already_exceeded():
    result = calculate_goal_projection(100_000, 200_000, [])
    assert result["achieved"] is True
    assert result["months_required"] == 0
    assert result["confidence"] == Decimal("1.0")


def test_projection_no_forecast_cannot_project():
    result = calculate_goal_projection(100_000, 10_000, [])
    assert result["achieved"] is False
    assert result["months_required"] is None
    assert result["confidence"] == Decimal("0.0")


def test_projection_single_month_achievement():
    forecast = [row("2026-01", 100_000)]
    result = calculate_goal_projection(50_000, 0, forecast)
    assert result["achieved"] is True
    assert result["projected_completion_month"] == "2026-01"
    assert result["months_required"] == 1


def test_projection_allocates_ratio_of_surplus():
    # Surplus 100_000 * 0.5 = 50_000/month; need 100_000 -> 2 months.
    forecast = [row("2026-01", 100_000), row("2026-02", 100_000)]
    result = calculate_goal_projection(100_000, 0, forecast)
    assert result["achieved"] is True
    assert result["months_required"] == 2
    assert result["projected_completion_month"] == "2026-02"


def test_projection_negative_surplus_ignored():
    forecast = [row("2026-01", -50_000), row("2026-02", 100_000)]
    result = calculate_goal_projection(50_000, 0, forecast)
    assert result["achieved"] is True
    assert result["months_required"] == 2


def test_projection_beyond_horizon_not_achieved():
    forecast = [row("2026-01", 10_000)]
    result = calculate_goal_projection(100_000, 0, forecast)
    assert result["achieved"] is False
    assert result["months_required"] is None


def test_projection_uses_forecast_confidence():
    forecast = [{**row("2026-01", 100_000), "confidence": Decimal("0.7")}]
    result = calculate_goal_projection(50_000, 0, forecast)
    assert result["confidence"] == Decimal("0.7")


def test_projection_invalid_confidence_raises_pinned_fin_e3():
    # FIN-E3 anomaly pinned: confidence parsing catches (ValueError, TypeError)
    # but Decimal(str(...)) raises decimal.InvalidOperation for non-numeric
    # strings, which propagates. Documented; not silently fixed in C42.25.
    from decimal import InvalidOperation

    import pytest

    forecast = [{**row("2026-01", 100_000), "confidence": "not-a-number"}]
    with pytest.raises(InvalidOperation):
        calculate_goal_projection(50_000, 0, forecast)


def test_projection_custom_allocation_ratio():
    forecast = [row("2026-01", 100_000)]
    result = calculate_goal_projection(100_000, 0, forecast, allocation_ratio=Decimal("1.0"))
    assert result["achieved"] is True
    assert result["months_required"] == 1


# ============================================================
# calculate_emergency_fund_target
# ============================================================


def test_emergency_target_six_months_default():
    result = calculate_emergency_fund_target(100_000)
    assert result["recommended_target_paise"] == 600_000
    assert result["months_of_cover"] == 6


def test_emergency_target_custom_months():
    result = calculate_emergency_fund_target(100_000, months_of_cover=3)
    assert result["recommended_target_paise"] == 300_000


def test_emergency_target_zero_expenses():
    result = calculate_emergency_fund_target(0)
    assert result["recommended_target_paise"] == 0


def test_emergency_target_negative_expenses():
    result = calculate_emergency_fund_target(-5)
    assert result["recommended_target_paise"] == 0


# ============================================================
# _months_to_payoff / calculate_debt_payoff_projection
# ============================================================


def test_months_to_payoff_zero_payment():
    assert _months_to_payoff(100_000, 0) is None
    assert _months_to_payoff(100_000, -5) is None


def test_months_to_payoff_ceiling():
    assert _months_to_payoff(100_001, 100_000) == 2
    assert _months_to_payoff(100_000, 100_000) == 1


def test_payoff_projection_no_debt_no_surplus():
    result = calculate_debt_payoff_projection([], [], 0)
    assert result["estimated_months"] == 0
    assert result["payoff_order"] == []


def test_payoff_projection_debt_but_zero_surplus():
    loans = [{"id": 1, "outstanding_paise": 100_000, "interest_rate_bps": 1200}]
    result = calculate_debt_payoff_projection(loans, [], 0)
    # Allocation is zero -> months_to_payoff None -> estimated_months None.
    assert result["estimated_months"] is None
    assert result["monthly_allocation_paise"] == 0


def test_payoff_projection_skips_zero_outstanding():
    loans = [
        {"id": 1, "outstanding_paise": 0, "interest_rate_bps": 1200},
        {"id": 2, "outstanding_paise": 100_000, "interest_rate_bps": 1200},
    ]
    result = calculate_debt_payoff_projection(loans, [], 50_000)
    assert [d["id"] for d in result["payoff_order"]] == [2]


def test_payoff_projection_avalanche_order():
    loans = [
        {"id": 1, "outstanding_paise": 100_000, "interest_rate_bps": 800},
        {"id": 2, "outstanding_paise": 100_000, "interest_rate_bps": 2000},
    ]
    result = calculate_debt_payoff_projection(loans, [], 50_000)
    assert [d["id"] for d in result["payoff_order"]] == [2, 1]


def test_payoff_projection_includes_credit_cards():
    loans = [{"id": "L1", "name": "Home", "outstanding_paise": 100_000, "interest_rate_bps": 800}]
    cards = [{"id": "C1", "name": "CC", "outstanding_paise": 50_000, "interest_rate_bps": 3600}]
    result = calculate_debt_payoff_projection(loans, cards, 30_000)
    assert [d["type"] for d in result["payoff_order"]] == ["credit_card", "loan"]
    assert result["monthly_allocation_paise"] == 15_000  # 30_000 * 0.5


def test_payoff_projection_estimated_months_sum():
    loans = [
        {"id": 1, "outstanding_paise": 100_000, "interest_rate_bps": 1200},
        {"id": 2, "outstanding_paise": 50_000, "interest_rate_bps": 800},
    ]
    result = calculate_debt_payoff_projection(loans, [], 100_000)
    # allocation = 50_000; loan1 -> 2 months, loan2 -> 1 month -> 3
    assert result["estimated_months"] == 3


def test_payoff_projection_interest_saved_positive():
    loans = [{"id": 1, "outstanding_paise": 100_000, "interest_rate_bps": 1200}]
    result = calculate_debt_payoff_projection(loans, [], 50_000)
    # rate 1200 -> 1200/100 = 12; 100_000*12/100 = 12_000
    assert result["interest_saved_paise"] == 12_000


def test_payoff_projection_zero_rate_uses_floor_estimate():
    loans = [{"id": 1, "outstanding_paise": 100_000, "interest_rate_bps": 0}]
    result = calculate_debt_payoff_projection(loans, [], 50_000)
    # rate 0 -> fallback 300 -> 300/100=3 -> 100_000*3/100=3000
    assert result["interest_saved_paise"] == 3000


# ============================================================
# calculate_goal_health
# ============================================================


def test_goal_health_invalid_target():
    result = calculate_goal_health(0, 0, 1, "2026-01", None)
    assert result["status"] == "behind"
    assert result["score"] == Decimal("0")


def test_goal_health_already_achieved():
    result = calculate_goal_health(100_000, 100_000, 0, None, None)
    assert result["status"] == "on_track"
    assert result["score"] == Decimal("1")


def test_goal_health_no_projection_high_progress():
    result = calculate_goal_health(100_000, 80_000, None, None, None)
    assert result["status"] == "on_track"


def test_goal_health_no_projection_mid_progress():
    result = calculate_goal_health(100_000, 60_000, None, None, None)
    assert result["status"] == "at_risk"


def test_goal_health_no_projection_low_progress():
    result = calculate_goal_health(100_000, 10_000, None, None, None)
    assert result["status"] == "behind"


def test_goal_health_on_track_meets_target_date():
    result = calculate_goal_health(100_000, 50_000, 3, "2026-03", "2026-06-30")
    assert result["status"] == "on_track"


def test_goal_health_at_risk_within_three_months():
    result = calculate_goal_health(100_000, 50_000, 3, "2026-08", "2026-06-30")
    assert result["status"] == "at_risk"


def test_goal_health_behind_beyond_three_months():
    result = calculate_goal_health(100_000, 50_000, 3, "2027-06", "2026-06-30")
    assert result["status"] == "behind"


def test_goal_health_invalid_date_falls_back_progress():
    result = calculate_goal_health(100_000, 60_000, 3, "garbage", "also-garbage")
    assert result["status"] == "on_track"


def test_goal_health_score_capped_at_one():
    result = calculate_goal_health(100_000, 200_000, None, None, None)
    assert result["score"] == Decimal("1")


# ============================================================
# calculate_household_goal_summary
# ============================================================


def test_household_goal_summary_empty():
    result = calculate_household_goal_summary([], [])
    assert result["total_goals"] == 0
    assert result["critical_goals"] == []


def test_household_goal_summary_counts():
    goals = [
        {"id": 1, "status": "completed", "priority": "normal"},
        {"id": 2, "status": "active", "priority": "normal"},
    ]
    projections = [{"status": "on_track"}, {"status": "at_risk"}]
    result = calculate_household_goal_summary(goals, projections)
    assert result["total_goals"] == 2
    assert result["completed"] == 1
    assert result["on_track"] == 1
    assert result["at_risk"] == 1


def test_household_goal_summary_critical_active_goals_only():
    goals = [
        {"id": 1, "status": "active", "priority": "critical", "name": "EF", "goal_type": "emergency_fund"},
        {"id": 2, "status": "completed", "priority": "critical", "name": "Done"},
    ]
    projections = [{"status": "behind"}, {"status": "on_track"}]
    result = calculate_household_goal_summary(goals, projections)
    assert len(result["critical_goals"]) == 1
    assert result["critical_goals"][0]["id"] == 1
    assert result["critical_goals"][0]["health"] == "behind"


def test_household_goal_summary_fewer_projections_than_goals():
    goals = [{"id": 1, "status": "active"}, {"id": 2, "status": "active"}]
    projections = [{"status": "on_track"}]
    result = calculate_household_goal_summary(goals, projections)
    # Second goal has no projection -> defaults to 'behind'.
    assert result["on_track"] == 1
