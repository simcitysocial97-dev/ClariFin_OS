"""Golden characterization tests for the financial_intelligence engine.

M9-C45.5 — locks the exact structured output contracts of the core financial
decision surface for representative inputs, so that any behavior-changing
mutation (comparison flip, arithmetic change, dict-key rename, missing return
field, boundary shift) is detected. This is the same characterization
methodology used to certify behaviour_engine at 83.5% (C43.7), applied to the
largest non-behaviour survivor pool (financial_intelligence, ~1000 survivors).

Honesty rules honored:
  * Every assertion expresses a REAL financial contract (allocation cascade,
    liquidity risk matrix, FOIR verdict, goal-health status/scoring, payoff
    ordering), not a mutant-killing contrivance.
  * Equivalent/observable-equivalent mutations (internal .get default probes,
    display-case strings that do not change outcomes, dict-key internal renames
    that are not part of the public contract) are NOT chased with assertions.
  * Existing functionality is preserved: these tests only LOCK current correct
    behavior; they do not pin a Class-E production defect (FIN-E1..E5 remain in
    the Defect Ledger and are excluded).
"""

from decimal import Decimal

from src.engines.financial_intelligence.forecasting import forecast_liquidity
from src.engines.financial_intelligence.goal_planner import calculate_goal_health
from src.engines.financial_intelligence.optimization import (
    optimize_surplus_allocation,
    rank_debt_payoff_strategy,
)
from src.engines.financial_intelligence.scenario import (
    simulate_expense_reduction,
    simulate_new_loan,
)


def _eq(value):
    """Compare, tolerating Decimal vs int."""
    if isinstance(value, Decimal):
        return float(value)
    return value


# ============================================================
# optimize_surplus_allocation — exact allocation cascade
# ============================================================


def test_golden_allocation_emergency_swallows_surplus():
    # Surplus below the emergency deficit -> all to emergency fund.
    got = optimize_surplus_allocation(
        500_000,
        [{"id": "d1", "interest_rate_bps": 2500, "outstanding_paise": 1_000_000}],
        [],
        {
            "current_paise": 1_000_000,
            "target_paise": 3_000_000,
            "deficit_paise": 2_000_000,
        },
    )
    assert got == {
        "allocation": [
            {
                "category": "emergency_fund",
                "amount_paise": 500_000,
                "reason": "emergency_fund_below_target",
            }
        ],
        "expected_impact": {"total_allocated_paise": 500_000, "remaining_paise": 0},
    }


def test_golden_allocation_no_deficit_goes_investment():
    got = optimize_surplus_allocation(
        500_000,
        [],
        [],
        {"current_paise": 3_000_000, "target_paise": 3_000_000, "deficit_paise": 0},
    )
    assert got == {
        "allocation": [
            {
                "category": "investment",
                "amount_paise": 500_000,
                "reason": "remaining_surplus",
            }
        ],
        "expected_impact": {
            "total_allocated_paise": 500_000,
            "remaining_paise": 500_000,
        },
    }


def test_golden_allocation_long_term_goal_then_investment():
    get_result = optimize_surplus_allocation(
        400_000,
        [],
        [{"id": "g1", "goal_type": "travel", "status": "active"}],
        {"current_paise": 3_000_000, "target_paise": 3_000_000, "deficit_paise": 0},
    )
    got = get_result["allocation"]
    # 40% of 400k -> 160k to goal; remainder 240k to investment.
    assert got == [
        {
            "category": "goal_saving",
            "amount_paise": 160_000,
            "reason": "long_term_goals",
            "goal_ids": ["g1"],
        },
        {
            "category": "investment",
            "amount_paise": 240_000,
            "reason": "remaining_surplus",
        },
    ]
    assert get_result["expected_impact"]["total_allocated_paise"] == 400_000


def test_golden_allocation_zero_surplus_empty():
    got = optimize_surplus_allocation(0, [], [], {"deficit_paise": 1})
    assert got == {"allocation": [], "expected_impact": {}}


def test_golden_allocation_high_interest_debt_cascade():
    # Emergency intact; high-interest debt (25% APR) present -> 60% of surplus to debt.
    got = optimize_surplus_allocation(
        500_000,
        [{"id": "d1", "interest_rate_bps": 2500, "outstanding_paise": 1_000_000}],
        [],
        {"current_paise": 3_000_000, "target_paise": 3_000_000, "deficit_paise": 0},
    )
    allocation = got["allocation"]
    assert allocation[0]["category"] == "debt_payment"
    assert allocation[0]["amount_paise"] == int(500_000 * Decimal("0.60"))
    assert allocation[0]["debt_ids"] == ["d1"]
    # Remainder to investment.
    assert allocation[-1] == {
        "category": "investment",
        "amount_paise": 500_000 - int(500_000 * Decimal("0.60")),
        "reason": "remaining_surplus",
    }


# ============================================================
# rank_debt_payoff_strategy — exact ordering + shape
# ============================================================


def test_golden_rank_avalanche_orders_by_rate_desc():
    got = rank_debt_payoff_strategy(
        [
            {"id": "a", "interest_rate_bps": 2500, "outstanding_paise": 500_000},
            {"id": "b", "interest_rate_bps": 1200, "outstanding_paise": 2_000_000},
        ],
        "avalanche",
    )
    assert got["recommended_strategy"] == "avalanche"
    assert [d["id"] for d in got["priority_order"]] == ["a", "b"]
    order = got["priority_order"][0]
    assert order["outstanding_paise"] == 500_000
    assert order["interest_rate_bps"] == 2500
    assert _eq(got["estimated_benefit"]["requires_projection"]) is True


def test_golden_rank_snowball_smallest_balance_first():
    got = rank_debt_payoff_strategy(
        [
            {"id": "a", "interest_rate_bps": 2500, "outstanding_paise": 1_000_000},
            {"id": "b", "interest_rate_bps": 1200, "outstanding_paise": 200_000},
            {"id": "c", "interest_rate_bps": 100, "outstanding_paise": 0},
        ],
        "snowball",
    )
    assert [d["id"] for d in got["priority_order"]] == ["b", "a"]


def test_golden_rank_invalid_strategy_falls_back_avalanche():
    got = rank_debt_payoff_strategy(
        [{"id": "a", "interest_rate_bps": 2500, "outstanding_paise": 500_000}],
        "bogus",
    )
    assert got["recommended_strategy"] == "avalanche"
    assert len(got["priority_order"]) == 1


# ============================================================
# calculate_goal_health — status + explanation contract
# ============================================================


def test_golden_health_invalid_target_zero_score():
    got = calculate_goal_health(0, 100, 5, None, None)
    assert got == {
        "score": Decimal("0"),
        "status": "behind",
        "explanation": "Invalid target amount",
    }


def test_golden_health_no_projection_low_progress_behind():
    got = calculate_goal_health(100_000, 25_000, None, None, "2026-12-01")
    assert got["status"] == "behind"
    assert got["score"] == Decimal("0.25")
    assert got["explanation"] == "25% complete, timeline unknown"


def test_golden_health_on_track_meets_target_date():
    got = calculate_goal_health(100_000, 30_000, 10, "2026-10-01", "2026-12-01")
    assert got["status"] == "on_track"
    assert got["score"] == Decimal("0.3")


def test_golden_health_completed_is_on_track():
    got = calculate_goal_health(100_000, 100_000, 0, None, None)
    assert got["status"] == "on_track"
    assert got["score"] == Decimal("1")


# ============================================================
# simulate_new_loan — FOIR affordability contract
# ============================================================


def test_golden_new_loan_foir_safe():
    got = simulate_new_loan(1_000_000, 1200, 12, 500_000)
    assert got["affordability"] == "safe"
    assert got["foir"] == Decimal("0.177698")
    assert got["monthly_emi_paise"] == 88_849


def test_golden_new_loan_zero_surplus_unsafe():
    got = simulate_new_loan(1_000_000, 1200, 12, 0)
    assert got["foir"] == Decimal("1.0")
    assert got["affordability"] == "unsafe"


# ============================================================
# forecast_liquidity — risk matrix contract
# ============================================================


def test_golden_liquidity_stress_high():
    got = forecast_liquidity(
        1_000_000,
        [
            {"expected_surplus_paise": -600_000},
            {"expected_surplus_paise": -600_000},
            {"expected_surplus_paise": 0},
        ],
        emergency_threshold_paise=300_000,
    )
    assert got["months_until_stress"] == 2
    assert got["projected_min_balance_paise"] == -200_000
    assert got["risk_level"] == "high"


def test_golden_liquidity_no_stress_low():
    got = forecast_liquidity(
        1_000_000,
        [{"expected_surplus_paise": 100_000}, {"expected_surplus_paise": 100_000}],
        emergency_threshold_paise=300_000,
    )
    assert got["risk_level"] == "low"
    assert got["months_until_stress"] is None
    # Minimum balance is the starting balance: positive surplus never pulls it below start.
    assert got["projected_min_balance_paise"] == 1_000_000


# ============================================================
# simulate_expense_reduction — cumulative benefit contract
# ============================================================


def test_golden_expense_reduction_cumulative_benefit():
    got = simulate_expense_reduction(
        100_000,
        10_000,
        [{"expected_surplus_paise": 50_000}, {"expected_surplus_paise": 60_000}],
        forecast_months=4,
    )
    assert got["monthly_savings_created_paise"] == 10_000
    assert got["projected_surplus_change_paise"] == 10_000
    # 4 months x 10k = 40k cumulative benefit.
    assert got["cumulative_benefit_paise"] == 40_000
    assert len(got["forecast"]) == 4
    assert got["forecast"][0]["projected_surplus_paise"] == 60_000
    assert got["forecast"][1]["projected_surplus_paise"] == 70_000
