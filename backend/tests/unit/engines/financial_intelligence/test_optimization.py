"""Direct unit tests for src/engines/financial_intelligence/optimization.py.

M9-C42.25 — direct behavioral ownership of the optimization engine: cash
advance debt derivation, surplus allocation cascade, debt strategy ranking,
goal prioritization, action scoring, and the master plan orchestrator.
"""

from decimal import Decimal

from src.engines.financial_intelligence.optimization import (
    _sum_high_interest_debt,
    calculate_financial_action_score,
    derive_cash_advance_debt_entry,
    generate_optimization_plan,
    optimize_goal_prioritization,
    optimize_surplus_allocation,
    rank_debt_payoff_strategy,
)

# ============================================================
# derive_cash_advance_debt_entry
# ============================================================


def test_cash_advance_entry_effective_rate():
    event = {
        "id": 42,
        "provider": "XYZ",
        "liability_change_paise": 100_000,
        "expense_paise": 3_000,
    }
    entry = derive_cash_advance_debt_entry(event, holding_period_days=30)
    assert entry["id"] == "cash_advance_42"
    assert entry["type"] == "cash_advance_liability"
    assert entry["name"] == "XYZ cash advance"
    assert entry["outstanding_paise"] == 100_000
    assert entry["interest_rate_bps"] == 3650
    assert entry["source_event_id"] == 42


def test_cash_advance_entry_zero_holding_period_uses_one_day():
    event = {"id": 1, "liability_change_paise": 100_000, "expense_paise": 3_000}
    entry = derive_cash_advance_debt_entry(event, holding_period_days=0)
    assert entry["interest_rate_bps"] == round(0.03 * 10000 * 365)


def test_cash_advance_entry_zero_expense_zero_rate():
    event = {"id": 1, "liability_change_paise": 100_000, "expense_paise": 0}
    entry = derive_cash_advance_debt_entry(event, 30)
    assert entry["interest_rate_bps"] == 0


def test_cash_advance_entry_zero_liability_zero_rate():
    event = {"id": 1, "liability_change_paise": 0, "expense_paise": 3_000}
    entry = derive_cash_advance_debt_entry(event, 30)
    assert entry["interest_rate_bps"] == 0


def test_cash_advance_entry_explicit_outstanding_wins():
    event = {
        "id": 1,
        "liability_change_paise": 100_000,
        "expense_paise": 1_000,
        "outstanding_paise": 55_000,
    }
    assert derive_cash_advance_debt_entry(event, 10)["outstanding_paise"] == 55_000


def test_cash_advance_entry_settled_outstanding_zero_preserved():
    event = {
        "id": 1,
        "liability_change_paise": 100_000,
        "expense_paise": 1_000,
        "outstanding_paise": 0,
    }
    assert derive_cash_advance_debt_entry(event, 10)["outstanding_paise"] == 0


def test_cash_advance_entry_missing_metadata_defaults():
    entry = derive_cash_advance_debt_entry(
        {"liability_change_paise": 1, "expense_paise": 1}, 5
    )
    assert entry["id"] == "cash_advance_unknown"
    assert entry["name"] == "Unknown cash advance"
    assert entry["source_event_id"] is None


# ============================================================
# optimize_surplus_allocation
# ============================================================


def test_allocation_zero_surplus_empty():
    result = optimize_surplus_allocation(0, [], [], {})
    assert result["allocation"] == []
    assert result["expected_impact"] == {}


def test_allocation_negative_surplus_empty():
    assert optimize_surplus_allocation(-100, [], [], {})["allocation"] == []


def test_allocation_full_cascade():
    debts = [
        {"id": "hd", "interest_rate_bps": 2000, "outstanding_paise": 100_000},
        {"id": "md", "interest_rate_bps": 1200, "outstanding_paise": 100_000},
    ]
    goals = [{"id": "g1", "goal_type": "retirement", "status": "active"}]
    result = optimize_surplus_allocation(
        100_000, debts, goals, {"deficit_paise": 40_000}
    )
    categories = [(a["category"], a["amount_paise"]) for a in result["allocation"]]
    assert categories == [
        ("emergency_fund", 40_000),
        ("debt_payment", 36_000),
        ("debt_payment", 14_400),
        ("goal_saving", 3_840),
        ("investment", 5_760),
    ]
    assert result["allocation"][1]["reason"] == "high_interest_debt"
    assert result["allocation"][1]["debt_ids"] == ["hd"]
    assert result["allocation"][2]["reason"] == "medium_interest_debt"
    # FIN-E5 FIXED: total_allocated_paise now correctly includes investment slice
    assert sum(a["amount_paise"] for a in result["allocation"]) == 100_000
    assert result["expected_impact"]["total_allocated_paise"] == 100_000
    assert result["expected_impact"]["remaining_paise"] == 5_760


def test_allocation_emergency_swallows_all_surplus():
    result = optimize_surplus_allocation(100_000, [], [], {"deficit_paise": 500_000})
    assert len(result["allocation"]) == 1
    assert result["allocation"][0]["amount_paise"] == 100_000


def test_allocation_no_deficit_skips_emergency():
    result = optimize_surplus_allocation(100_000, [], [], {"deficit_paise": 0})
    assert result["allocation"] == [
        {
            "category": "investment",
            "amount_paise": 100_000,
            "reason": "remaining_surplus",
        }
    ]


def test_allocation_low_interest_debt_skipped():
    debts = [{"id": "ld", "interest_rate_bps": 500, "outstanding_paise": 100_000}]
    result = optimize_surplus_allocation(100_000, debts, [], {})
    assert [a["category"] for a in result["allocation"]] == ["investment"]


def test_allocation_completed_and_emergency_goals_excluded():
    goals = [
        {"id": "g1", "goal_type": "emergency_fund", "status": "active"},
        {"id": "g2", "goal_type": "retirement", "status": "completed"},
    ]
    result = optimize_surplus_allocation(100_000, [], goals, {})
    assert [a["category"] for a in result["allocation"]] == ["investment"]


def test_allocation_boundary_rates_1800_high_800_medium():
    debts = [
        {"id": "at1800", "interest_rate_bps": 1800, "outstanding_paise": 10},
        {"id": "at800", "interest_rate_bps": 800, "outstanding_paise": 10},
        {"id": "at799", "interest_rate_bps": 799, "outstanding_paise": 10},
    ]
    result = optimize_surplus_allocation(100_000, debts, [], {})
    reasons = [a.get("reason") for a in result["allocation"]]
    assert "high_interest_debt" in reasons
    assert "medium_interest_debt" in reasons
    high = next(
        a for a in result["allocation"] if a.get("reason") == "high_interest_debt"
    )
    medium = next(
        a for a in result["allocation"] if a.get("reason") == "medium_interest_debt"
    )
    assert high["debt_ids"] == ["at1800"]
    assert medium["debt_ids"] == ["at800"]


# ============================================================
# rank_debt_payoff_strategy
# ============================================================

DEBTS = [
    {
        "id": "low_rate_big",
        "type": "loan",
        "interest_rate_bps": 800,
        "outstanding_paise": 1_000_000,
    },
    {
        "id": "high_rate_small",
        "type": "credit_card",
        "interest_rate_bps": 3600,
        "outstanding_paise": 100_000,
    },
    {
        "id": "mid_rate_mid",
        "type": "loan",
        "interest_rate_bps": 1200,
        "outstanding_paise": 400_000,
    },
]


def test_rank_invalid_strategy_falls_back_avalanche():
    result = rank_debt_payoff_strategy(DEBTS, strategy="bogus")
    assert result["recommended_strategy"] == "avalanche"
    assert result["priority_order"][0]["id"] == "high_rate_small"


def test_rank_empty_debts():
    result = rank_debt_payoff_strategy([])
    assert result["priority_order"] == []
    assert result["estimated_benefit"]["requires_projection"] is False


def test_rank_zero_balance_debts_excluded():
    debts = [{"id": "z", "interest_rate_bps": 999, "outstanding_paise": 0}]
    result = rank_debt_payoff_strategy(debts)
    assert result["priority_order"] == []
    assert result["estimated_benefit"]["requires_projection"] is False


def test_rank_avalanche_orders_by_rate_desc():
    result = rank_debt_payoff_strategy(DEBTS)
    assert [d["id"] for d in result["priority_order"]] == [
        "high_rate_small",
        "mid_rate_mid",
        "low_rate_big",
    ]
    assert result["estimated_benefit"]["requires_projection"] is True


def test_rank_snowball_orders_by_balance_asc():
    result = rank_debt_payoff_strategy(DEBTS, strategy="snowball")
    assert [d["id"] for d in result["priority_order"]] == [
        "high_rate_small",
        "mid_rate_mid",
        "low_rate_big",
    ]
    assert result["recommended_strategy"] == "snowball"


def test_rank_balanced_hybrid_score():
    debts = [
        {"id": "A", "interest_rate_bps": 2000, "outstanding_paise": 10_000},
        {"id": "B", "interest_rate_bps": 3000, "outstanding_paise": 1_000_000},
    ]
    result = rank_debt_payoff_strategy(debts, strategy="balanced")
    # A: 0.28 + 3.0 = 3.28 beats B: 0.42 + 0.03 = 0.45
    assert [d["id"] for d in result["priority_order"]] == ["A", "B"]


def test_rank_balance_paise_fallback_key():
    debts = [{"id": "x", "interest_rate_bps": 100, "balance_paise": 12_345}]
    result = rank_debt_payoff_strategy(debts)
    assert result["priority_order"][0]["outstanding_paise"] == 12_345


def test_rank_minimum_payment_fallback_to_minimum_due():
    debts = [
        {
            "id": "cc",
            "interest_rate_bps": 100,
            "outstanding_paise": 5_000,
            "minimum_due_paise": 77,
        }
    ]
    result = rank_debt_payoff_strategy(debts)
    assert result["priority_order"][0]["minimum_payment_paise"] == 77


# ============================================================
# optimize_goal_prioritization
# ============================================================


def test_goal_prioritization_empty():
    result = optimize_goal_prioritization([])
    assert result == {"priority_order": [], "recommendations": []}


def test_goal_prioritization_type_ordering():
    goals = [
        {"id": "other", "goal_type": "vacation", "status": "active"},
        {"id": "debt", "goal_type": "debt_payoff", "status": "active"},
        {"id": "ef", "goal_type": "emergency_fund", "status": "active"},
    ]
    result = optimize_goal_prioritization(goals)
    assert [g["id"] for g in result["priority_order"]] == ["ef", "debt", "other"]
    assert [g["rank"] for g in result["priority_order"]] == [1, 2, 3]


def test_goal_prioritization_user_priority_within_type():
    goals = [
        {"id": "e2", "goal_type": "emergency_fund", "status": "active", "priority": 3},
        {"id": "e1", "goal_type": "emergency_fund", "status": "active", "priority": 1},
    ]
    result = optimize_goal_prioritization(goals)
    assert [g["id"] for g in result["priority_order"]] == ["e1", "e2"]


def test_goal_prioritization_completed_excluded():
    goals = [{"id": "done", "goal_type": "vacation", "status": "completed"}]
    result = optimize_goal_prioritization(goals)
    assert result["priority_order"] == []


def test_goal_prioritization_recommendations():
    result = optimize_goal_prioritization(
        [{"id": "g", "goal_type": "vacation", "status": "active"}],
        emergency_fund_status={"deficit_paise": 100},
        debt_status={"total_high_interest_debt_paise": 50},
    )
    recs = [r["recommendation"] for r in result["recommendations"]]
    assert "prioritize_emergency_fund" in recs
    assert "consider_debt_consolidation" in recs


def test_goal_prioritization_no_recommendations_when_healthy():
    result = optimize_goal_prioritization(
        [{"id": "g", "goal_type": "vacation", "status": "active"}],
        emergency_fund_status={"deficit_paise": 0},
        debt_status={"total_high_interest_debt_paise": 0},
    )
    assert result["recommendations"] == []


# ============================================================
# calculate_financial_action_score
# ============================================================


def test_action_score_invalid_action():
    result = calculate_financial_action_score("fly_to_moon", {})
    assert result == {
        "action": "fly_to_moon",
        "score": Decimal("0"),
        "impact": "low",
        "drivers": [],
    }


def test_action_score_pay_credit_card_high_context():
    context = {
        "interest_rate_bps": 2000,
        "credit_revolver_ratio": Decimal("0.6"),
        "debt_goals_count": 1,
    }
    result = calculate_financial_action_score("pay_credit_card", context)
    assert result["score"] == Decimal("0.88")
    assert result["impact"] == "high"
    assert set(result["drivers"]) == {
        "high_interest_rate",
        "reduces_revolver_risk",
        "urgent_interest_cost",
    }


def test_action_score_pay_credit_card_medium_context():
    context = {"interest_rate_bps": 900, "credit_revolver_ratio": Decimal("0.3")}
    result = calculate_financial_action_score("pay_credit_card", context)
    assert result["score"] == Decimal("0.53")
    assert result["impact"] == "medium"
    assert "reduces_credit_risk" in result["drivers"]


def test_action_score_apr_bps_fallback_key():
    result = calculate_financial_action_score(
        "pay_credit_card", {"apr_bps": 2000, "credit_revolver_ratio": Decimal("0.1")}
    )
    assert "high_interest_rate" in result["drivers"]


def test_action_score_low_revolver_no_risk_driver():
    result = calculate_financial_action_score(
        "pay_credit_card", {"credit_revolver_ratio": Decimal("0.1")}
    )
    assert not any(d.startswith("reduces_") for d in result["drivers"])


def test_action_score_emergency_fund_urgent():
    context = {"emergency_deficit_paise": 10_000, "months_until_stress": 1}
    result = calculate_financial_action_score("increase_emergency_fund", context)
    assert result["score"] == Decimal("0.69")
    assert result["impact"] == "medium"
    assert "emergency_fund_gap" in result["drivers"]
    assert "liquidity_stress_approaching" in result["drivers"]
    assert "aligns_with_stability" in result["drivers"]


def test_action_score_emergency_fund_no_gap_later_stress():
    context = {"emergency_deficit_paise": 0, "months_until_stress": 5}
    result = calculate_financial_action_score("increase_emergency_fund", context)
    assert "emergency_fund_gap" not in result["drivers"]
    assert "liquidity_stress_approaching" not in result["drivers"]


def test_action_score_emergency_fund_unknown_stress():
    result = calculate_financial_action_score("increase_emergency_fund", {})
    # 0.3*0.35 + 0.3*0.30 + 0.5*0.20 + 0.9*0.15 = 0.43
    assert result["score"] == Decimal("0.43")


def test_action_score_reduce_expenses():
    result = calculate_financial_action_score("reduce_expenses", {})
    assert result["score"] == Decimal("0.41")
    assert result["impact"] == "medium"
    assert "immediate_cash_flow_improvement" in result["drivers"]


def test_action_score_increase_investment_with_goals():
    result = calculate_financial_action_score(
        "increase_investment", {"investment_goals_count": 2}
    )
    assert result["score"] == Decimal("0.40")


def test_action_score_increase_investment_without_goals_low():
    result = calculate_financial_action_score("increase_investment", {})
    assert result["score"] == Decimal("0.32")
    assert result["impact"] == "low"


# ============================================================
# generate_optimization_plan
# ============================================================


def test_plan_empty_state():
    result = generate_optimization_plan({})
    assert result["recommended_actions"] == []
    assert result["allocation_plan"] == {}
    assert result["warnings"] == ["No financial state data provided"]
    assert result["confidence"] == Decimal("0")


def test_plan_full_state():
    state = {
        "surplus": {"monthly_surplus_paise": 100_000},
        "debts": [{"id": "d1", "interest_rate_bps": 2000, "outstanding_paise": 50_000}],
        "goals": [{"id": "g1", "goal_type": "debt_payoff", "status": "active"}],
        "forecast": {
            "emergency_threshold_paise": 3_000_000,
            "current_liquidity_paise": 1_000_000,
            "confidence": 0.9,
        },
        "risk": {"credit_revolver_ratio": "0.6"},
    }
    result = generate_optimization_plan(state)
    actions = [a["action"] for a in result["recommended_actions"]]
    assert actions == ["pay_credit_card", "increase_emergency_fund"]
    assert "Emergency fund below target threshold" in result["warnings"]
    assert "High-interest debt present" in result["warnings"]
    assert result["confidence"] == Decimal("0.9")
    # Entire surplus consumed by the 2M emergency deficit.
    assert result["allocation_plan"] == [
        {
            "category": "emergency_fund",
            "amount_paise": 100_000,
            "reason": "emergency_fund_below_target",
        }
    ]


def test_plan_no_surplus_warning_and_zero_confidence():
    state = {
        "surplus": {"monthly_surplus_paise": 0},
        "debts": [],
        "goals": [],
        "forecast": {},
    }
    result = generate_optimization_plan(state)
    assert "No surplus available for optimization" in result["warnings"]
    assert result["confidence"] == Decimal("0")


def test_plan_confidence_defaults_to_07_with_surplus():
    state = {"surplus": {"monthly_surplus_paise": 100}, "forecast": {}}
    result = generate_optimization_plan(state)
    assert result["confidence"] == Decimal("0.7")


def test_plan_invalid_forecast_confidence_raises_pinned_fin_e3():
    # FIN-E3 anomaly pinned: contextlib.suppress(ValueError, TypeError) does
    # not catch decimal.InvalidOperation from malformed confidence strings.
    from decimal import InvalidOperation

    import pytest

    state = {
        "surplus": {"monthly_surplus_paise": 100},
        "forecast": {"confidence": "junk"},
    }
    with pytest.raises(InvalidOperation):
        generate_optimization_plan(state)


def test_plan_action_score_filtered_at_half():
    # Low revolver, no emergency deficit, no stress -> emergency action < 0.5.
    state = {
        "surplus": {"monthly_surplus_paise": 100_000},
        "debts": [],
        "goals": [],
        "forecast": {"current_liquidity_paise": 9_000_000},
        "risk": {"credit_revolver_ratio": "0"},
    }
    result = generate_optimization_plan(state)
    actions = [a["action"] for a in result["recommended_actions"]]
    assert "increase_emergency_fund" not in actions


# ============================================================
# _sum_high_interest_debt
# ============================================================


def test_sum_high_interest_debt_only_threshold_and_above():
    debts = [
        {"interest_rate_bps": 2000, "outstanding_paise": 100},
        {"interest_rate_bps": 1000, "outstanding_paise": 50},
        {"interest_rate_bps": 1800, "balance_paise": 7},
    ]
    assert _sum_high_interest_debt(debts) == 107


def test_sum_high_interest_debt_empty():
    assert _sum_high_interest_debt([]) == 0
