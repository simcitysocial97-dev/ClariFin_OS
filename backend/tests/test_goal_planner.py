"""Tests for Financial Goal Planner Engine.

Run: python -m pytest backend/tests/test_goal_planner.py -v
"""

import ast
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.engines.financial_intelligence import (
    DEFAULT_GOAL_ALLOCATION_RATIO,
    calculate_debt_payoff_projection,
    calculate_emergency_fund_target,
    calculate_goal_health,
    calculate_goal_projection,
    calculate_household_goal_summary,
)

# ============================================================
# Test 1: Emergency Fund - 6 months expense calculation
# ============================================================

def test_emergency_fund_6_months():
    """
    Emergency fund target should be 6x monthly expenses by default.
    """
    result = calculate_emergency_fund_target(monthly_expenses_paise=50000)

    assert result["recommended_target_paise"] == 300000  # 50000 * 6
    assert result["months_of_cover"] == 6


# ============================================================
# Test 2: Emergency Fund - configurable months
# ============================================================

def test_emergency_fund_configurable_months():
    """
    Emergency fund target should support custom months of cover.
    """
    result = calculate_emergency_fund_target(
        monthly_expenses_paise=50000,
        months_of_cover=3,
    )

    assert result["recommended_target_paise"] == 150000  # 50000 * 3
    assert result["months_of_cover"] == 3


# ============================================================
# Test 3: Goal Projection - Achievable goal
# ============================================================

def test_goal_projection_achievable():
    """
    Goal with sufficient surplus should project completion.
    """
    monthly_surplus_forecast = [
        {"month": "2026-08", "expected_surplus_paise": 20000},
        {"month": "2026-09", "expected_surplus_paise": 20000},
        {"month": "2026-10", "expected_surplus_paise": 20000},
        {"month": "2026-11", "expected_surplus_paise": 20000},
        {"month": "2026-12", "expected_surplus_paise": 20000},
        {"month": "2027-01", "expected_surplus_paise": 20000},
    ]

    # Target: 50000, Current: 0, Allocation: 50% -> 10000/month, 5 months for 50000
    result = calculate_goal_projection(
        target_amount_paise=50000,
        current_amount_paise=0,
        monthly_surplus_forecast=monthly_surplus_forecast,
        allocation_ratio=DEFAULT_GOAL_ALLOCATION_RATIO,
    )

    assert result["achieved"] is True
    assert result["months_required"] == 5  # 5 months * 10000 = 50000
    assert result["confidence"] > Decimal("0")


# ============================================================
# Test 4: Goal Projection - Already achieved
# ============================================================

def test_goal_projection_already_achieved():
    """
    Goal already achieved should return achieved=True.
    """
    result = calculate_goal_projection(
        target_amount_paise=50000,
        current_amount_paise=60000,
        monthly_surplus_forecast=[],
    )

    assert result["achieved"] is True
    assert result["months_required"] == 0


# ============================================================
# Test 5: Goal Projection - Impossible goal (no surplus)
# ============================================================

def test_goal_projection_no_surplus():
    """
    Goal with no surplus forecast should not be achievable.
    """
    result = calculate_goal_projection(
        target_amount_paise=100000,
        current_amount_paise=0,
        monthly_surplus_forecast=[],
    )

    assert result["achieved"] is False
    assert result["months_required"] is None


# ============================================================
# Test 6: Goal Projection - Partial surplus allocation
# ============================================================

def test_goal_projection_partial_allocation():
    """
    Goal projection should respect allocation ratio.
    """
    monthly_surplus_forecast = [
        {"month": "2026-08", "expected_surplus_paise": 100000},
    ]

    result = calculate_goal_projection(
        target_amount_paise=50000,
        current_amount_paise=0,
        monthly_surplus_forecast=monthly_surplus_forecast,
        allocation_ratio=Decimal("0.25"),  # 25% allocation
    )

    assert result["achieved"] is False  # 25000 < 50000
    assert result["months_required"] is None


# ============================================================
# Test 7: Debt Payoff - Priority ordering by interest rate
# ============================================================

def test_debt_payoff_priority_ordering():
    """
    Debt payoff should prioritize highest interest rate first.
    """
    loans = [
        {
            "id": 1,
            "name": "Personal Loan",
            "outstanding_paise": 100000,
            "interest_rate_bps": 1200,  # 12%
        },
        {
            "id": 2,
            "name": "Home Loan",
            "outstanding_paise": 500000,
            "interest_rate_bps": 800,  # 8%
        },
    ]
    credit_cards = [
        {
            "id": "card_1",
            "name": "Credit Card",
            "outstanding_paise": 50000,
            "interest_rate_bps": 3600,  # 36% - highest
        },
    ]

    result = calculate_debt_payoff_projection(
        loans=loans,
        credit_cards=credit_cards,
        monthly_surplus_paise=20000,
    )

    assert len(result["payoff_order"]) == 3
    # Credit card should be first (highest interest)
    assert result["payoff_order"][0]["type"] == "credit_card"
    assert result["payoff_order"][0]["interest_rate_bps"] == 3600


# ============================================================
# Test 8: Debt Payoff - Credit card priority
# ============================================================

def test_debt_payoff_credit_card_priority():
    """
    Credit cards with higher rates should be paid before lower-rate loans.
    """
    loans = [
        {
            "id": 1,
            "name": "Education Loan",
            "outstanding_paise": 200000,
            "interest_rate_bps": 900,  # 9%
        },
    ]
    credit_cards = [
        {
            "id": "card_1",
            "name": "Premium Card",
            "outstanding_paise": 30000,
            "interest_rate_bps": 4200,  # 42% - much higher than loan
        },
    ]

    result = calculate_debt_payoff_projection(
        loans=loans,
        credit_cards=credit_cards,
        monthly_surplus_paise=15000,
    )

    # Credit card first due to higher interest
    assert result["payoff_order"][0]["type"] == "credit_card"


# ============================================================
# Test 9: Goal Health - On track
# ============================================================

def test_goal_health_on_track():
    """
    Goal with sufficient progress should be on track.
    """
    result = calculate_goal_health(
        target_amount_paise=100000,
        current_amount_paise=60000,
        months_required=3,
        projected_completion_month="2026-09",
        target_date="2026-12-31",
    )

    assert result["status"] == "on_track"
    assert result["score"] == Decimal("0.6")


# ============================================================
# Test 10: Goal Health - At risk
# ============================================================

def test_goal_health_at_risk():
    """
    Goal slightly behind schedule should be at_risk.
    """
    result = calculate_goal_health(
        target_amount_paise=100000,
        current_amount_paise=30000,
        months_required=10,
        projected_completion_month="2027-06",
        target_date="2027-03-31",  # 3 months behind
    )

    assert result["status"] == "at_risk"


# ============================================================
# Test 11: Goal Health - Behind
# ============================================================

def test_goal_health_behind():
    """
    Goal significantly behind should be 'behind'.
    """
    result = calculate_goal_health(
        target_amount_paise=100000,
        current_amount_paise=10000,
        months_required=24,
        projected_completion_month="2028-06",
        target_date="2026-12-31",  # 18 months behind!
    )

    assert result["status"] == "behind"


# ============================================================
# Test 12: Engine purity - no DB calls
# ============================================================

def test_engine_purity_no_db_calls():
    """
    Engine files should make ZERO database calls.
    This test verifies no sqlite3 or repository imports in engine code.
    """
    engine_path = Path(__file__).parent.parent / "src" / "engines" / "financial_intelligence" / "goal_planner.py"

    source = engine_path.read_text()
    tree = ast.parse(source)

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")

    # Verify no sqlite3 imports
    assert "sqlite3" not in imports, f"sqlite3 import found in goal_planner.py: {imports}"

    # Verify no repository imports
    for imp in imports:
        assert "repositories" not in imp, f"Repository import found in goal_planner.py: {imp}"


# ============================================================
# Test 13: Household Goal Summary
# ============================================================

def test_household_goal_summary():
    """
    Household summary should aggregate goal counts correctly.
    """
    goals = [
        {"id": "g1", "status": "active", "priority": "medium"},
        {"id": "g2", "status": "active", "priority": "critical"},
        {"id": "g3", "status": "completed", "priority": "high"},
    ]
    projections = [
        {"status": "on_track"},
        {"status": "behind"},
        {"status": "completed"},
    ]

    result = calculate_household_goal_summary(goals, projections)

    assert result["total_goals"] == 3
    assert result["completed"] == 1
    assert result["on_track"] == 1
    assert len(result["critical_goals"]) == 1  # g2 is critical and active


# ============================================================
# Test 14: Goal health - no target date
# ============================================================

def test_goal_health_no_target_date():
    """
    Goal without target date should use progress ratio for status.
    """
    result = calculate_goal_health(
        target_amount_paise=100000,
        current_amount_paise=25000,
        months_required=10,
        projected_completion_month="2027-06",
        target_date=None,
    )

    assert result["status"] == "at_risk"  # 25% progress


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
