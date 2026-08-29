"""Direct unit tests for src/engines/financial_intelligence/intelligence.py.

M9-C42.25 — direct behavioral ownership of the intelligence aggregator:
snapshot building, priority generation, confidence metadata, risk aggregation,
opportunity identification, health scoring, and the master report.
"""

from decimal import Decimal

from src.engines.financial_intelligence.intelligence import (
    _aggregate_risks,
    _compute_health_score,
    _extract_liquidity_months,
    _get_action_reason,
    _identify_opportunities,
    build_financial_snapshot,
    calculate_intelligence_confidence,
    generate_financial_intelligence_report,
    generate_financial_priorities,
)

# ============================================================
# build_financial_snapshot
# ============================================================


def test_snapshot_passes_through_all_inputs():
    snapshot = build_financial_snapshot(
        cashflow={"income_paise": 1},
        liquidity={"risk_level": "low"},
        debts=[{"id": 1}],
        goals=[{"id": 2}],
        behaviour={"wellness_score": 80},
        forecasts={"cashflow": {}},
        optimization={"allocation_plan": []},
    )
    assert snapshot["cashflow"] == {"income_paise": 1}
    assert snapshot["liquidity"] == {"risk_level": "low"}
    assert snapshot["debts"] == [{"id": 1}]
    assert snapshot["goals"] == [{"id": 2}]
    assert snapshot["behaviour"] == {"wellness_score": 80}
    assert snapshot["forecasts"] == {"cashflow": {}}
    assert snapshot["optimization"] == {"allocation_plan": []}


# ============================================================
# Small helpers
# ============================================================


def test_extract_liquidity_months_positive():
    assert _extract_liquidity_months({"projected_min_balance_paise": 250_000}) == 2


def test_extract_liquidity_months_negative_clamped_zero():
    assert _extract_liquidity_months({"projected_min_balance_paise": -100_000}) == 0


def test_extract_liquidity_months_missing():
    assert _extract_liquidity_months({}) == 0


def test_get_action_reason_map():
    assert (
        _get_action_reason("increase_emergency_fund", {}, {})
        == "emergency_fund_below_target"
    )
    assert _get_action_reason("reduce_expenses", {}, {}) == "negative_surplus_detected"
    assert (
        _get_action_reason("increase_investment", {}, {})
        == "surplus_available_for_investing"
    )
    assert (
        _get_action_reason("unknown_action", {}, {})
        == "financial_optimization_identified"
    )


def test_get_action_reason_credit_card_depends_on_revolver():
    low = _get_action_reason(
        "pay_credit_card", {}, {"credit_revolver_ratio": Decimal("0.1")}
    )
    high = _get_action_reason(
        "pay_credit_card", {}, {"credit_revolver_ratio": Decimal("0.6")}
    )
    assert low == "optimizing_debt"
    assert high == "high_revolving_dependency"


# ============================================================
# generate_financial_priorities
# ============================================================


def plan(actions):
    return {"recommended_actions": actions}


def test_priorities_passthrough_ranked_in_order():
    result = generate_financial_priorities(
        plan(
            [
                {"action": "pay_credit_card", "impact": "high"},
                {"action": "reduce_expenses"},
            ]
        ),
        {},
        {"projected_min_balance_paise": 1_000_000},  # months=10 -> no emergency add
        [],
    )
    assert [p["rank"] for p in result] == [1, 2]
    assert result[0]["action"] == "pay_credit_card"
    assert result[0]["reason"] == "optimizing_debt"
    assert result[0]["impact"] == "high"
    assert result[1]["action"] == "reduce_expenses"
    assert result[1]["impact"] == "medium"  # default when missing


def test_priorities_emergency_injected_when_liquidity_low():
    result = generate_financial_priorities(
        plan([]), {}, {"projected_min_balance_paise": 0}, []
    )
    assert result[0]["action"] == "increase_emergency_fund"
    assert result[0]["reason"] == "emergency_fund_below_target"
    assert result[0]["impact"] == "high"


def test_priorities_emergency_medium_impact_for_one_to_three_months():
    result = generate_financial_priorities(
        plan([]), {}, {"projected_min_balance_paise": 250_000}, []
    )
    assert result[0]["impact"] == "medium"


def test_priorities_no_emergency_injection_above_three_months():
    result = generate_financial_priorities(
        plan([]), {}, {"projected_min_balance_paise": 300_000}, []
    )
    assert result == []


def test_priorities_emergency_not_duplicated():
    result = generate_financial_priorities(
        plan([{"action": "increase_emergency_fund", "impact": "medium"}]),
        {},
        {"projected_min_balance_paise": 0},
        [],
    )
    actions = [p["action"] for p in result]
    assert actions.count("increase_emergency_fund") == 1


def test_priorities_emergency_rank_gate_blocks_fourth_slot():
    actions = [
        {"action": "a1"},
        {"action": "a2"},
        {"action": "a3"},
    ]
    result = generate_financial_priorities(
        plan(actions), {}, {"projected_min_balance_paise": 0}, []
    )
    assert "increase_emergency_fund" not in [p["action"] for p in result]


def test_priorities_credit_dependency_injected():
    result = generate_financial_priorities(
        plan([]),
        {"credit_revolver_ratio": Decimal("0.6")},
        {"projected_min_balance_paise": 1_000_000},
        [],
    )
    assert result[0]["action"] == "pay_credit_card"
    assert result[0]["reason"] == "high_revolving_dependency"
    assert result[0]["impact"] == "high"


def test_priorities_credit_dependency_not_duplicated():
    result = generate_financial_priorities(
        plan([{"action": "pay_credit_card", "impact": "high"}]),
        {"credit_revolver_ratio": Decimal("0.6")},
        {"projected_min_balance_paise": 1_000_000},
        [],
    )
    assert [p["action"] for p in result].count("pay_credit_card") == 1


def test_priorities_capped_at_five():
    actions = [{"action": f"a{i}"} for i in range(6)]
    result = generate_financial_priorities(
        plan(actions), {}, {"projected_min_balance_paise": 1_000_000}, []
    )
    assert len(result) == 5
    assert [p["rank"] for p in result] == [1, 2, 3, 4, 5]


# ============================================================
# calculate_intelligence_confidence
# ============================================================


def test_confidence_perfect_inputs_excellent():
    result = calculate_intelligence_confidence(
        3, Decimal("1"), Decimal("1"), Decimal("0")
    )
    assert result["confidence"] == Decimal("1")
    assert result["data_quality"] == "excellent"


def test_confidence_good_band():
    result = calculate_intelligence_confidence(
        3, Decimal("0.8"), Decimal("0.8"), Decimal("1e20")
    )
    # 0.25 * (1 + 0.8 + 0.8 + ~0) = 0.65 -> good
    assert result["data_quality"] == "good"


def test_confidence_fair_band():
    result = calculate_intelligence_confidence(
        1, Decimal("0.5"), Decimal("0.5"), Decimal("0")
    )
    # 0.25 * (0.3333 + 0.5 + 0.5 + 1) ~= 0.5833 -> fair
    assert result["data_quality"] == "fair"


def test_confidence_poor_band():
    result = calculate_intelligence_confidence(
        0, Decimal("0"), Decimal("0"), Decimal("0")
    )
    # 0.25 * (0 + 0 + 0 + 1) = 0.25 -> poor
    assert result["data_quality"] == "poor"


def test_confidence_months_score_capped_at_three():
    capped = calculate_intelligence_confidence(
        10, Decimal("1"), Decimal("1"), Decimal("0")
    )
    exact = calculate_intelligence_confidence(
        3, Decimal("1"), Decimal("1"), Decimal("0")
    )
    assert capped["confidence"] == exact["confidence"] == Decimal("1")


def test_confidence_clamps_out_of_range_inputs():
    result = calculate_intelligence_confidence(
        3, Decimal("1.5"), Decimal("-0.5"), Decimal("0")
    )
    # completeness clamped to 1, coverage clamped to 0
    assert result["confidence"] == Decimal("0.25") * (
        Decimal("1") + Decimal("1") + Decimal("0") + Decimal("1")
    )


def test_confidence_factors_recorded():
    result = calculate_intelligence_confidence(
        6, Decimal("1"), Decimal("1"), Decimal("0")
    )
    assert result["factors"]["data_months"] == 6
    assert result["factors"]["transaction_completeness"] == Decimal("1")
    assert result["factors"]["account_coverage"] == Decimal("1")
    assert result["factors"]["forecast_variance"] == Decimal("0")


# ============================================================
# _aggregate_risks / _identify_opportunities / _compute_health_score
# ============================================================


def test_aggregate_risks_empty_when_all_healthy():
    risks = _aggregate_risks(
        {"risk_level": "low"},
        {"trend": "stable", "current_dependency_ratio": Decimal("0.1")},
        {},
        {},
    )
    assert risks == []


def test_aggregate_risks_high_liquidity_critical():
    liquidity = {
        "risk_level": "high",
        "months_until_stress": 1,
        "projected_min_balance_paise": -5,
    }
    risks = _aggregate_risks(liquidity, {}, {}, {})
    assert risks[0]["type"] == "liquidity_stress"
    assert risks[0]["severity"] == "critical"
    assert risks[0]["source"] == "forecasting_engine"
    assert risks[0]["details"]["months_until_stress"] == 1


def test_aggregate_risks_medium_liquidity_warning():
    risks = _aggregate_risks(
        {"risk_level": "medium", "months_until_stress": 3}, {}, {}, {}
    )
    assert risks[0]["severity"] == "warning"


def test_aggregate_risks_credit_trend_worsening():
    risks = _aggregate_risks(
        {}, {"trend": "worsening", "current_dependency_ratio": Decimal("0")}, {}, {}
    )
    assert risks[0]["type"] == "credit_dependency"


def test_aggregate_risks_dependency_ratio_decimal_gate():
    risks = _aggregate_risks(
        {},
        {"trend": "stable", "current_dependency_ratio": Decimal("0.4")},
        {},
        {},
    )
    assert any(r["type"] == "credit_dependency" for r in risks)


def test_aggregate_risks_dependency_ratio_float_not_flagged():
    # Pinned behavior: only Decimal-typed ratios trigger the >0.3 gate.
    risks = _aggregate_risks(
        {}, {"trend": "stable", "current_dependency_ratio": 0.4}, {}, {}
    )
    assert risks == []


def test_aggregate_risks_debt_cycle_threshold():
    at_limit = _aggregate_risks({}, {}, {}, {"debt_cycle_score": 70})
    above = _aggregate_risks({}, {}, {}, {"debt_cycle_score": 71})
    assert at_limit == []
    assert above[0]["type"] == "debt_cycle"


def test_aggregate_risks_optimization_warnings_passthrough():
    risks = _aggregate_risks({}, {}, {"warnings": ["w1", "w2"]}, {})
    assert [r["details"]["message"] for r in risks] == ["w1", "w2"]
    assert all(r["type"] == "optimization_warning" for r in risks)


def test_identify_opportunities_high_surplus():
    opps = _identify_opportunities({"monthly_surplus_paise": 500_001}, {}, [])
    assert opps[0]["type"] == "surplus_investment"
    assert opps[0]["potential_benefit_paise"] == 500_001 * 12


def test_identify_opportunities_surplus_at_threshold_none():
    assert _identify_opportunities({"monthly_surplus_paise": 500_000}, {}, []) == []


def test_identify_opportunities_emergency_goal_proximity():
    goals = [
        {
            "goal_type": "emergency_fund",
            "status": "active",
            "target_amount_paise": 100_000,
            "current_amount_paise": 40_000,
        }
    ]
    opps = _identify_opportunities({"monthly_surplus_paise": 10_000}, {}, goals)
    assert opps[0]["type"] == "goal_proximity"
    assert opps[0]["potential_benefit_paise"] == 60_000


def test_identify_opportunities_goal_requires_surplus():
    goals = [
        {
            "goal_type": "emergency_fund",
            "status": "active",
            "target_amount_paise": 100_000,
            "current_amount_paise": 40_000,
        }
    ]
    assert _identify_opportunities({"monthly_surplus_paise": 0}, {}, goals) == []


def test_compute_health_score_wellness_passthrough():
    assert _compute_health_score({"wellness_score": "82.5"}) == Decimal("82.5")


def test_compute_health_score_invalid_wellness_raises_pinned_fin_e3():
    # FIN-E3 anomaly pinned: the (ValueError, TypeError) guard does not catch
    # decimal.InvalidOperation raised by non-numeric wellness strings.
    from decimal import InvalidOperation

    import pytest

    with pytest.raises(InvalidOperation):
        _compute_health_score({"wellness_score": "abc"})


def test_compute_health_score_falsy_zero_inputs_coalesce_pinned_fin_e4():
    # FIN-E4 anomaly pinned: falsy values (0) coalesce to defaults
    # (debt_cycle 0 -> 50, stability 0 -> 0.5), so the naive minimum is 10,
    # not 0. Documented; negative stability reaches the true clamp.
    result = _compute_health_score(
        {"debt_cycle_score": 100, "credit_revolver_ratio": 1, "cashflow_stability": 0}
    )
    assert result == Decimal("10.0")


def test_compute_health_score_clamped_at_zero():
    result = _compute_health_score(
        {"debt_cycle_score": 100, "credit_revolver_ratio": 1, "cashflow_stability": -1}
    )
    assert result == Decimal("0")


def test_compute_health_score_max_with_falsy_defaults_pinned_fin_e4():
    # debt_cycle 0 -> default 50, revolver 0 -> 0, stability 1 -> 0.8 scaled.
    result = _compute_health_score(
        {"debt_cycle_score": 0, "credit_revolver_ratio": 0, "cashflow_stability": 1}
    )
    assert result == Decimal("80")


# ============================================================
# generate_financial_intelligence_report
# ============================================================


def test_report_empty_state_structure():
    report = generate_financial_intelligence_report({})
    assert report["health_score"] == Decimal("70")
    assert report["risks"] == []
    assert report["opportunities"] == []
    # Empty liquidity reads as 0 projected months -> emergency priority injected.
    assert report["priorities"][0]["action"] == "increase_emergency_fund"
    assert report["snapshot"]["cashflow"] == {}
    assert report["confidence"]["data_quality"] in ("excellent", "good", "fair", "poor")


def test_report_full_state_aggregates_all_sections():
    state = {
        "cashflow": {"monthly_surplus_paise": 600_000},
        "liquidity": {
            "risk_level": "high",
            "months_until_stress": 1,
            "projected_min_balance_paise": -1,
        },
        "debts": [],
        "goals": [
            {
                "goal_type": "emergency_fund",
                "status": "active",
                "target_amount_paise": 500_000,
                "current_amount_paise": 100_000,
            }
        ],
        "behaviour": {
            "wellness_score": 82,
            "credit_revolver_ratio": Decimal("0.6"),
            "debt_cycle_score": 71,
        },
        "forecasts": {
            "cashflow": {
                "forecast": [
                    {"month": "2026-01"},
                    {"month": "2026-02"},
                    {"month": "2026-03"},
                ],
                "confidence": 0.9,
            },
            "credit": {
                "trend": "worsening",
                "current_dependency_ratio": Decimal("0.5"),
            },
        },
        "optimization": {
            "recommended_actions": [{"action": "pay_credit_card", "impact": "high"}],
            "warnings": ["w"],
        },
    }
    report = generate_financial_intelligence_report(state)
    assert report["health_score"] == Decimal("82")
    types = [r["type"] for r in report["risks"]]
    assert "liquidity_stress" in types
    assert "credit_dependency" in types
    assert "debt_cycle" in types
    assert "optimization_warning" in types
    opp_types = [o["type"] for o in report["opportunities"]]
    assert "surplus_investment" in opp_types
    assert "goal_proximity" in opp_types
    assert report["priorities"][0]["action"] == "pay_credit_card"


def test_report_confidence_uses_forecast_horizon_months():
    state_with_horizon = {
        "forecasts": {
            "cashflow": {"forecast": [{"month": f"2026-0{i}"} for i in range(1, 4)]}
        },
    }
    state_without_horizon: dict = {"forecasts": {"cashflow": {"forecast": []}}}
    with_horizon = generate_financial_intelligence_report(state_with_horizon)
    without_horizon = generate_financial_intelligence_report(state_without_horizon)
    # months=3 (full score) -> excellent; months=0 -> good (0.675).
    assert with_horizon["confidence"]["data_quality"] == "excellent"
    assert without_horizon["confidence"]["data_quality"] == "good"


def test_report_defaults_for_missing_behaviour_data():
    report = generate_financial_intelligence_report({})
    # transaction_completeness default 0.8, account_coverage default 0.9,
    # forecast variance default 0.5 -> ~0.675 -> good
    assert report["confidence"]["data_quality"] == "good"
