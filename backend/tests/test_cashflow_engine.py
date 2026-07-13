"""Tests for Cashflow Engine.

Run: python -m pytest tests/test_cashflow_engine.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.engines.cashflow_engine import compute_monthly_cashflow  # noqa: E402

# ============================================================
# Test 1: Worked Example (income 80000, expenses 110000)
# ============================================================

def test_worked_example_cash_deficit_covered_by_credit():
    """
    Worked example: income 80000, expenses 110000, CRED extraction net 30000/fee 1250.

    Expected:
    - cash_surplus = 0 (income + credit_received - expenses = 80000 + 30000 - 110000 = 0)
    - true_savings = -31250 (income - expenses - fee = 80000 - 110000 - 1250 = -31250)
    - month_classification = 'deficit_covered_by_credit'
    """
    cash_summary = {
        "income_paise": 80000,
        "expense_paise": 110000,
        "net_paise": -30000,
    }

    # CRED cash advance event:
    # - amount_paise = 31250 (total debit on credit card)
    # - asset_change_paise = 30000 (credit received in bank)
    # - fee = 1250 (amount - asset = 31250 - 30000)
    financial_events = [
        {
            "id": 1,
            "event_type": "cash_advance",
            "amount_paise": 31250,  # Total debit (principal + fee)
            "asset_change_paise": 30000,  # Credit received in bank
            "liability_change_paise": 31250,  # Liability created (principal + fee)
            "expense_paise": 0,
            "income_paise": 0,
            "provider": "CRED",
            "date_iso": "2025-07-15",
        }
    ]

    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id="self",
    )

    # Cash surplus = income - expense + credit_received = 80000 - 110000 + 30000 = 0
    assert result["cash_surplus"] == 0

    # True savings = income - expense - fee = 80000 - 110000 - 1250 = -31250
    assert result["true_savings"] == -31250

    # Month classification = deficit_covered_by_credit
    assert result["month_classification"] == "deficit_covered_by_credit"


# ============================================================
# Test 2: Regression - No events, cash and accrual converge
# ============================================================

def test_regression_no_events_cash_equals_accrual():
    """
    When financial_events is empty, cash and accrual basis should converge.

    cash_surplus = income - expense = 0
    true_savings = income - expense - 0 = 0
    month_classification = surplus (no credit events, and cash_surplus >= 0)
    """
    cash_summary = {
        "income_paise": 100000,
        "expense_paise": 80000,
        "net_paise": 20000,
    }

    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=[],
        scope="household",
        owner_id="self",
    )

    assert result["cash_surplus"] == 20000
    assert result["true_savings"] == 20000  # No fees to subtract
    assert result["month_classification"] == "surplus"


# ============================================================
# Test 3: Pure deficit (no credit events, negative cash surplus)
# ============================================================

def test_pure_deficit_no_credit():
    """
    Income < expenses, no credit events.

    cash_surplus = -20000
    true_savings = -20000
    month_classification = 'deficit'
    """
    cash_summary = {
        "income_paise": 50000,
        "expense_paise": 70000,
        "net_paise": -20000,
    }

    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=[],
        scope="household",
        owner_id="self",
    )

    assert result["cash_surplus"] == -20000
    assert result["true_savings"] == -20000
    assert result["month_classification"] == "deficit"


# ============================================================
# Test 4: Surplus without credit
# ============================================================

def test_pure_surplus_no_credit():
    """
    Income > expenses, no credit events.

    cash_surplus = 30000
    true_savings = 30000
    month_classification = 'surplus'
    """
    cash_summary = {
        "income_paise": 100000,
        "expense_paise": 70000,
        "net_paise": 30000,
    }

    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=[],
        scope="household",
        owner_id="self",
    )

    assert result["cash_surplus"] == 30000
    assert result["true_savings"] == 30000
    assert result["month_classification"] == "surplus"


# ============================================================
# Test 5: Household scope with multiple owners
# ============================================================

def test_household_scope_includes_all_owners():
    """
    Household scope should include events from all owners.
    """
    cash_summary = {
        "income_paise": 100000,
        "expense_paise": 80000,
        "net_paise": 20000,
    }

    # Multiple events from different owners
    financial_events = [
        {
            "id": 1,
            "event_type": "cash_advance",
            "amount_paise": 10000,
            "asset_change_paise": 9800,  # 200 fee
            "liability_change_paise": 10000,
            "owner_id": "self",
        },
        {
            "id": 2,
            "event_type": "cash_advance",
            "amount_paise": 20000,
            "asset_change_paise": 19500,  # 500 fee
            "liability_change_paise": 20000,
            "owner_id": "spouse",
        },
    ]

    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id=None,
    )

    # Both events should be aggregated
    assert result["total_fees_paise"] == 700  # 200 + 500
    assert result["total_credit_advance_paise"] == 29300  # 9800 + 19500


# ============================================================
# Test 6: Individual scope filters events
# ============================================================

def test_individual_scope_filters_owner():
    """
    Individual scope should only include events for the specified owner.
    
    The engine receives pre-filtered events from the service layer.
    This test verifies that with only spouse's events passed, only spouse's fees count.
    """
    cash_summary = {
        "income_paise": 100000,
        "expense_paise": 80000,
        "net_paise": 20000,
    }

    # Only spouse's event (simulating pre-filtered at service layer)
    financial_events = [
        {
            "id": 2,
            "event_type": "cash_advance",
            "amount_paise": 20000,
            "asset_change_paise": 19500,
            "liability_change_paise": 20000,
            "owner_id": "spouse",
        },
    ]

    # Individual scope for "spouse" - engine receives pre-filtered events
    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="individual",
        owner_id="spouse",
    )

    assert result["total_fees_paise"] == 500


# ============================================================
# Test 7: Engine purity - no DB calls
# ============================================================

def test_engine_purity_no_db_calls():
    """
    Engine should make ZERO database calls.
    This test verifies the function signature accepts plain data.
    """
    # The function signature takes plain dicts and lists, not repositories
    # This is by design - no sqlite3 imports in the engine
    import ast

    engine_path = Path(__file__).parent.parent / "src" / "engines" / "cashflow_engine.py"
    engine_source = engine_path.read_text()

    # Parse and check no sqlite3 imports
    tree = ast.parse(engine_source)

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)

    assert "sqlite3" not in imports
    assert "src.repositories" not in imports


# ============================================================
# Test 8: Net worth impact calculation
# ============================================================

def test_net_worth_impact_calculation():
    """
    Net worth impact = asset_change - liability_change.
    """
    cash_summary = {
        "income_paise": 100000,
        "expense_paise": 80000,
        "net_paise": 20000,
    }

    # Cash advance: +30000 assets, +31250 liability (net worth: -1250)
    financial_events = [
        {
            "id": 1,
            "event_type": "cash_advance",
            "amount_paise": 31250,
            "asset_change_paise": 30000,
            "liability_change_paise": 31250,
        }
    ]

    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id="self",
    )

    # Net worth impact = 30000 - 31250 = -1250
    assert result["net_worth_impact"] == -1250


# ============================================================
# Test 9: Credit dependency ratio
# ============================================================

def test_credit_dependency_ratio():
    """
    Credit dependency ratio = credit_funded / expenses.
    """
    cash_summary = {
        "income_paise": 100000,
        "expense_paise": 60000,
        "net_paise": 40000,
    }

    # Credit advance of 30000
    financial_events = [
        {
            "id": 1,
            "event_type": "cash_advance",
            "amount_paise": 30000,
            "asset_change_paise": 30000,
        }
    ]

    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id="self",
    )

    # Credit dependency = 30000 / 60000 = 0.5
    assert result["credit_dependency_ratio"] == 0.5


# ============================================================
# Test 10: Effective liquidity cost annualized
# ============================================================

def test_effective_liquidity_cost_annualized():
    """
    Effective liquidity cost annualized = fee * 12.
    """
    cash_summary = {
        "income_paise": 100000,
        "expense_paise": 80000,
        "net_paise": 20000,
    }

    # Fee of 500 paise
    financial_events = [
        {
            "id": 1,
            "event_type": "cash_advance",
            "amount_paise": 10500,
            "asset_change_paise": 10000,  # Fee = 500
        }
    ]

    result = compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=financial_events,
        scope="household",
        owner_id="self",
    )

    assert result["effective_liquidity_cost_annualized"] == 6000  # 500 * 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
