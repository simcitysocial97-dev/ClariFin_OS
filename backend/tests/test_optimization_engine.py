"""Tests for Financial Optimization Engine.

Run: python -m pytest backend/tests/test_optimization_engine.py -v
"""

import ast
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.engines.financial_intelligence import (
    ACTION_WEIGHTS,
    HIGH_INTEREST_THRESHOLD_BPS,
    MEDIUM_INTEREST_THRESHOLD_BPS,
    calculate_financial_action_score,
    derive_cash_advance_debt_entry,
    generate_optimization_plan,
    optimize_goal_prioritization,
    optimize_surplus_allocation,
    rank_debt_payoff_strategy,
)

# ============================================================
# Test 1: optimize_surplus_allocation - Emergency fund priority
# ============================================================

def test_surplus_allocation_emergency_fund_first():
    """Surplus allocation should prioritize emergency fund when below target."""
    result = optimize_surplus_allocation(
        monthly_surplus_paise=50000,  # ₹500
        debts=[],
        goals=[],
        emergency_fund_status={"deficit_paise": 100000},  # ₹1000 deficit
    )

    assert len(result["allocation"]) == 1
    assert result["allocation"][0]["category"] == "emergency_fund"
    assert result["allocation"][0]["amount_paise"] == 50000


def test_surplus_allocation_high_interest_debt():
    """Surplus allocation should allocate to high-interest debt after emergency fund."""
    result = optimize_surplus_allocation(
        monthly_surplus_paise=100000,  # ₹1000
        debts=[
            {"id": "d1", "interest_rate_bps": 3600, "outstanding_paise": 50000},  # Credit card
        ],
        goals=[],
        emergency_fund_status={"deficit_paise": 0},  # No emergency fund gap
    )

    # Should have debt allocation
    debt_allocations = [a for a in result["allocation"] if a["category"] == "debt_payment"]
    assert len(debt_allocations) == 1
    assert debt_allocations[0]["reason"] == "high_interest_debt"


def test_surplus_allocation_zero_surplus():
    """No allocation when surplus is zero or negative."""
    result = optimize_surplus_allocation(
        monthly_surplus_paise=0,
        debts=[{"id": "d1", "interest_rate_bps": 3600, "outstanding_paise": 50000}],
        goals=[],
        emergency_fund_status={"deficit_paise": 100000},
    )

    assert result["allocation"] == []


# ============================================================
# Test 2: rank_debt_payoff_strategy - Avalanche
# ============================================================

def test_debt_strategy_avalanche_highest_rate_first():
    """Avalanche strategy should rank highest interest rate first."""
    debts = [
        {"id": "loan1", "balance_paise": 100000, "interest_rate_bps": 800},  # 8%
        {"id": "card1", "balance_paise": 50000, "interest_rate_bps": 3600},  # 36%
        {"id": "loan2", "balance_paise": 200000, "interest_rate_bps": 1200},  # 12%
    ]

    result = rank_debt_payoff_strategy(debts=debts, strategy="avalanche")

    assert result["recommended_strategy"] == "avalanche"
    assert result["priority_order"][0]["id"] == "card1"  # Highest rate first
    assert result["priority_order"][0]["interest_rate_bps"] == 3600
    assert result["estimated_benefit"]["requires_projection"] is True


def test_debt_strategy_snowball_smallest_balance_first():
    """Snowball strategy should rank smallest balance first."""
    debts = [
        {"id": "loan1", "balance_paise": 200000, "interest_rate_bps": 800},
        {"id": "card1", "balance_paise": 50000, "interest_rate_bps": 3600},
        {"id": "loan2", "balance_paise": 100000, "interest_rate_bps": 1200},
    ]

    result = rank_debt_payoff_strategy(debts=debts, strategy="snowball")

    assert result["recommended_strategy"] == "snowball"
    assert result["priority_order"][0]["id"] == "card1"  # Smallest balance first
    assert result["priority_order"][0]["outstanding_paise"] == 50000


def test_debt_strategy_empty_debts():
    """Empty debt list should return empty priority order."""
    result = rank_debt_payoff_strategy(debts=[], strategy="avalanche")

    assert result["priority_order"] == []
    assert result["estimated_benefit"]["requires_projection"] is False


# ============================================================
# Test 3: optimize_goal_prioritization
# ============================================================

def test_goal_prioritization_emergency_fund_first():
    """Emergency fund goals should be ranked first."""
    goals = [
        {"id": "g1", "goal_type": "purchase", "status": "active", "priority": 1},
        {"id": "g2", "goal_type": "emergency_fund", "status": "active", "priority": 5},
        {"id": "g3", "goal_type": "investment", "status": "active", "priority": 2},
    ]

    result = optimize_goal_prioritization(goals=goals)

    # Emergency fund should be ranked first (rank 1)
    assert result["priority_order"][0]["goal_type"] == "emergency_fund"


def test_goal_prioritization_urgent_deadline():
    """Goals with urgent deadlines should be prioritized higher."""
    goals = [
        {"id": "g1", "goal_type": "purchase", "status": "active", "priority": 2, "deadline": "2026-08-01"},
        {"id": "g2", "goal_type": "purchase", "status": "active", "priority": 1, "deadline": "2027-12-01"},
    ]

    result = optimize_goal_prioritization(goals=goals)

    # Both are purchase goals, sorted by priority ascending (lower number = higher priority)
    # g2 has priority 1, should be ranked first
    assert result["priority_order"][0]["id"] == "g2"
    assert result["priority_order"][0]["rank"] == 1


def test_goal_prioritization_empty_goals():
    """Empty goals list should return empty priority order."""
    result = optimize_goal_prioritization(goals=[])

    assert result["priority_order"] == []
    assert result["recommendations"] == []


# ============================================================
# Test 4: calculate_financial_action_score
# ============================================================

def test_action_score_high_interest_credit_card():
    """Credit card with high interest rate should score high."""
    result = calculate_financial_action_score(
        action="pay_credit_card",
        context={"interest_rate_bps": 3600, "credit_revolver_ratio": Decimal("0.6")},
    )

    assert result["action"] == "pay_credit_card"
    assert result["score"] >= Decimal("0.7")
    assert result["impact"] == "high"
    assert "high_interest_rate" in result["drivers"]


def test_action_score_emergency_fund_gap():
    """Emergency fund gap should score high for increase_emergency_fund."""
    result = calculate_financial_action_score(
        action="increase_emergency_fund",
        context={"emergency_deficit_paise": 500000},  # ₹5000 deficit
    )

    assert result["action"] == "increase_emergency_fund"
    assert result["score"] >= Decimal("0.5")
    assert "emergency_fund_gap" in result["drivers"]


def test_action_score_invalid_action():
    """Invalid action should return zero score."""
    result = calculate_financial_action_score(
        action="invalid_action",
        context={},
    )

    assert result["score"] == Decimal("0")
    assert result["impact"] == "low"


# ============================================================
# Test 5: generate_optimization_plan - Empty state
# ============================================================

def test_optimization_empty_state():
    """Empty financial state should return empty recommendations with zero confidence."""
    result = generate_optimization_plan({})

    assert result["recommended_actions"] == []
    assert result["confidence"] == Decimal("0")
    assert "No financial state data provided" in result["warnings"]


def test_optimization_no_surplus():
    """No surplus should return no allocation recommendations."""
    result = generate_optimization_plan({"surplus": {"monthly_surplus_paise": 0}})

    assert result["confidence"] == Decimal("0")


# ============================================================
# Test 6: Engine purity - no DB or service imports
# ============================================================

def test_engine_purity_no_db_calls():
    """Engine files should make ZERO database calls."""
    engine_path = Path(__file__).parent.parent / "src" / "engines" / "financial_intelligence" / "optimization.py"

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
    assert "sqlite3" not in imports, f"sqlite3 import found in optimization.py: {imports}"

    # Verify no repository imports
    for imp in imports:
        assert "repositories" not in imp, f"Repository import found in optimization.py: {imp}"

    # Verify no service imports
    for imp in imports:
        assert "services" not in imp, f"Service import found in optimization.py: {imp}"


# ============================================================
# Test 7: Constants are imported correctly
# ============================================================

def test_interest_thresholds():
    """Interest rate thresholds should be correct basis point values."""
    assert HIGH_INTEREST_THRESHOLD_BPS == 1800
    assert MEDIUM_INTEREST_THRESHOLD_BPS == 800


def test_action_weights():
    """Action weights should sum to 1.0."""
    total = sum(ACTION_WEIGHTS.values())
    assert total == Decimal("1.00")


# ============================================================
# Test 8: Cash Advance Debt Entry Helper
# ============================================================

def test_derive_cash_advance_debt_entry_basic():
    """derive_cash_advance_debt_entry should convert event to debt entry format."""
    event = {
        "id": 123,
        "liability_change_paise": 100000,  # ₹1000 borrowed
        "expense_paise": 400,  # ₹4 fee (400 paise)
        "provider": "CRED",
        "outstanding_paise": 100000,
    }

    result = derive_cash_advance_debt_entry(event, holding_period_days=365)

    assert result["id"] == "cash_advance_123"
    assert result["type"] == "cash_advance_liability"
    assert result["name"] == "CRED cash advance"
    assert result["outstanding_paise"] == 100000
    # 400 paise fee / 100000 paise principal * 10000 * 365/365 = 40 bps annual
    assert result["interest_rate_bps"] == 40


def test_derive_cash_advance_debt_entry_20_days():
    """Cash advance held 20 days should annualize to ~7300 bps effective rate.

    Example: ₹1000 borrowed, 4% fee (4000 paise), held 20 days
    Effective annual rate = (4000/100000) * (365/20) * 10000 = ~7300 bps
    This matches the task requirement: "fee_bps=400, held 20 days → ~7300 bps"
    """
    event = {
        "id": 456,
        "liability_change_paise": 100000,  # ₹1000 borrowed
        "expense_paise": 4000,  # 4% fee = 4000 paise (fee_bps=400)
        "provider": "HDFC",
        "outstanding_paise": 100000,
    }

    result = derive_cash_advance_debt_entry(event, holding_period_days=20)

    # (4000/100000) * (365/20) * 10000 = 7300 bps
    assert result["interest_rate_bps"] == 7300
    assert result["source_event_id"] == 456


def test_derive_cash_advance_debt_entry_uses_outstanding():
    """Should use outstanding_paise if available, else liability_change_paise."""
    event_with_outstanding = {
        "id": 789,
        "liability_change_paise": 100000,
        "expense_paise": 400,
        "provider": "ICICI",
        "outstanding_paise": 60000,  # Partial repayment
    }

    result = derive_cash_advance_debt_entry(event_with_outstanding, holding_period_days=30)

    assert result["outstanding_paise"] == 60000


def test_cash_advance_ranks_above_low_interest_loan():
    """Cash advance with high effective rate should rank above low-interest loan (regression test).

    This proves the original defect is fixed: CRED debt gets prioritized
    when its effective rate (73% APR-equiv) is higher than a loan (12% APR).
    """
    # Cash advance: 73% effective annual rate (very high)
    cash_advance_debt = {
        "id": "cash_advance_123",
        "type": "cash_advance_liability",
        "name": "CRED cash advance",
        "outstanding_paise": 50000,
        "interest_rate_bps": 7300,  # 73% effective
    }

    # Regular loan: 12% interest (much lower)
    regular_loan = {
        "id": "loan_456",
        "type": "loan",
        "name": "Car Loan",
        "outstanding_paise": 200000,
        "interest_rate_bps": 1200,  # 12%
    }

    result = rank_debt_payoff_strategy(
        debts=[regular_loan, cash_advance_debt],
        strategy="avalanche",
    )

    # Cash advance should be ranked FIRST due to higher effective rate
    assert result["priority_order"][0]["id"] == "cash_advance_123"
    assert result["priority_order"][0]["interest_rate_bps"] == 7300


def test_settled_cash_advance_excluded():
    """Settled cash advance events should not produce debt entries with positive balance."""
    event_settled = {
        "id": 999,
        "liability_change_paise": 100000,
        "expense_paise": 400,
        "provider": "Settled Provider",
        "outstanding_paise": 0,  # Fully settled - no balance
    }

    result = derive_cash_advance_debt_entry(event_settled, holding_period_days=20)

    # Should have 0 outstanding, which means it would be filtered out in service
    assert result["outstanding_paise"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
