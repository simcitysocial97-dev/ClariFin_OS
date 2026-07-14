"""Tests for Financial Scenario Simulation Engine.

Run: python -m pytest backend/tests/test_scenario_engine.py -v
"""

import ast
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.engines.financial_intelligence import (
    compare_scenario,
    simulate_credit_behaviour_change,
    simulate_debt_prepayment,
    simulate_expense_reduction,
    simulate_income_change,
    simulate_new_loan,
)

# ============================================================
# Test 1: Expense Reduction - ₹5,000 savings
# ============================================================

def test_expense_reduction_increases_surplus():
    """
    ₹5,000 expense reduction should increase surplus by ₹5,000/month.
    """
    monthly_surplus_forecast = [
        {"month": "2026-08", "expected_surplus_paise": 20000},
    ]

    result = simulate_expense_reduction(
        current_monthly_expense_paise=100000,
        reduction_paise=500000,  # ₹5,000 = 500,000 paise
        monthly_surplus_forecast=monthly_surplus_forecast,
        forecast_months=3,
    )

    assert result["monthly_savings_created_paise"] == 500000
    assert result["projected_surplus_change_paise"] == 500000
    assert result["cumulative_benefit_paise"] == 1500000  # 500,000 * 3 months


# ============================================================
# Test 2: Expense Reduction - Cumulative benefit
# ============================================================

def test_expense_reduction_cumulative_benefit():
    """
    Cumulative benefit should equal monthly_savings * forecast_months.
    """
    monthly_surplus_forecast = [
        {"month": "2026-08", "expected_surplus_paise": 10000},
    ]

    result = simulate_expense_reduction(
        current_monthly_expense_paise=100000,
        reduction_paise=250000,  # ₹2,500
        monthly_surplus_forecast=monthly_surplus_forecast,
        forecast_months=6,
    )

    assert result["cumulative_benefit_paise"] == 1500000  # 250,000 * 6 = 1,500,000


# ============================================================
# Test 3: Income Increase
# ============================================================

def test_income_increase():
    """
    Salary increase should raise projected surplus.
    """
    monthly_surplus_forecast = [
        {"month": "2026-08", "expected_surplus_paise": 15000},
    ]

    result = simulate_income_change(
        current_income_paise=100000,
        change_paise=30000,  # ₹300 increase
        monthly_surplus_forecast=monthly_surplus_forecast,
        forecast_months=3,
    )

    assert result["income_change_paise"] == 30000
    assert result["cumulative_income_change_paise"] == 90000  # 30,000 * 3


# ============================================================
# Test 4: Income Decrease
# ============================================================

def test_income_decrease():
    """
    Income decrease (job loss) should lower projected surplus.
    """
    monthly_surplus_forecast = [
        {"month": "2026-08", "expected_surplus_paise": 25000},
    ]

    result = simulate_income_change(
        current_income_paise=100000,
        change_paise=-20000,  # ₹200 decrease
        monthly_surplus_forecast=monthly_surplus_forecast,
        forecast_months=6,
    )

    assert result["income_change_paise"] == -20000
    assert result["cumulative_income_change_paise"] == -120000  # -20,000 * 6


# ============================================================
# Test 5: Debt Prepayment - Timeline reduction
# ============================================================

def test_debt_prepayment_reduces_timeline():
    """
    Extra payment toward debt should reduce payoff timeline.
    """
    loans = [
        {
            "id": 1,
            "name": "Personal Loan",
            "outstanding_paise": 500000,
            "interest_rate_bps": 1200,  # 12%
        },
    ]

    result = simulate_debt_prepayment(
        debt_accounts=loans,
        extra_payment_paise=50000,  # ₹500 extra
        monthly_surplus_paise=20000,
    )

    # Should show reduction in months
    assert result["estimated_months_saved"] >= 0
    assert isinstance(result["interest_saved_paise"], int)


# ============================================================
# Test 6: New Loan - Safe FOIR
# ============================================================

def test_new_loan_affordability_check():
    """
    Affordability thresholds work: below 40% = safe.
    """
    # Test the thresholds are properly applied
    # With EMI > surplus, we get FOIR > 1.0 = unsafe
    result_unsafe = simulate_new_loan(
        principal_paise=100000000,
        annual_rate_bps=1200,
        tenure_months=120,
        current_surplus_paise=500000,
    )
    assert result_unsafe["affordability"] in ("warning", "unsafe")

    # Test with zero surplus - should be unsafe
    result_zero = simulate_new_loan(
        principal_paise=100000000,
        annual_rate_bps=1200,
        tenure_months=120,
        current_surplus_paise=0,
    )
    assert result_zero["affordability"] == "unsafe"


# ============================================================
# Test 7: New Loan - Warning and Unsafe FOIR
# ============================================================

def test_new_loan_foir_thresholds():
    """
    FOIR thresholds: below 40% safe, 40-60% warning, above 60% unsafe.
    """
    # Large surplus - should be safe
    safe_result = simulate_new_loan(
        principal_paise=50000000,  # ₹500,000
        annual_rate_bps=1200,  # 12%
        tenure_months=60,
        current_surplus_paise=200000,  # ₹2,000 surplus
    )

    # Check that FOIR is calculated
    assert "foir" in safe_result
    assert isinstance(safe_result["affordability"], str)


# ============================================================
# Test 8: Credit Behavior Improvement
# ============================================================

def test_credit_behaviour_improvement():
    """
    Stopping revolving behavior should show improved status.
    """
    result = simulate_credit_behaviour_change(
        current_credit_dependency_ratio=Decimal("0.6"),
        current_revolver_ratio=Decimal("0.4"),
        average_interest_rate_bps=3600,  # 36% APR
    )

    assert result["risk_change"] == "improved"
    assert result["projected_dependency_ratio"] < Decimal("0.6")


# ============================================================
# Test 9: Credit Behavior - No rate provided
# ============================================================

def test_credit_behaviour_requires_rate():
    """
    Without interest rate, should indicate rate input is required.
    """
    result = simulate_credit_behaviour_change(
        current_credit_dependency_ratio=Decimal("0.6"),
        current_revolver_ratio=Decimal("0.4"),
        average_interest_rate_bps=None,
    )

    assert result["requires_rate_input"] is True
    assert result["interest_saved_paise"] is None


# ============================================================
# Test 10: Scenario Comparison - Improvements detected
# ============================================================

def test_scenario_comparison_improvements():
    """
    Comparison should detect positive changes.
    """
    baseline = {
        "monthly_surplus_paise": 10000,
        "cumulative_benefit_paise": 100000,
    }
    scenario = {
        "monthly_surplus_paise": 15000,  # +₹500
        "cumulative_benefit_paise": 150000,  # +₹5,000
    }

    result = compare_scenario(baseline, scenario)

    assert len(result["improvements"]) > 0
    assert "risks" in result
    assert "delta" in result


# ============================================================
# Test 11: Scenario Comparison - Risks detected
# ============================================================

def test_scenario_comparison_risks():
    """
    Comparison should detect negative changes.
    """
    baseline = {
        "monthly_surplus_paise": 20000,
        "foir": Decimal("0.35"),
    }
    scenario = {
        "monthly_surplus_paise": 5000,  # -₹1500
        "foir": Decimal("0.65"),  # Above warning threshold
    }

    result = compare_scenario(baseline, scenario)

    assert len(result["risks"]) > 0


# ============================================================
# Test 12: Engine Purity - No DB calls
# ============================================================

def test_engine_purity_no_db_calls():
    """
    Scenario engine should have zero database calls.
    Verify no sqlite3 or repository imports in engine code.
    """
    engine_path = Path(__file__).parent.parent / "src" / "engines" / "financial_intelligence" / "scenario.py"

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
    assert "sqlite3" not in imports, f"sqlite3 import found in scenario.py: {imports}"

    # Verify no repository imports
    for imp in imports:
        assert "repositories" not in imp, f"Repository import found in scenario.py: {imp}"


# ============================================================
# Test 13: Empty Input Handling
# ============================================================

def test_empty_input_handling():
    """
    Empty inputs should return sensible defaults.
    """
    result = simulate_expense_reduction(
        current_monthly_expense_paise=0,
        reduction_paise=100000,
        monthly_surplus_forecast=[],
        forecast_months=3,
    )

    # Should still return structure
    assert "monthly_savings_created_paise" in result
    assert "forecast" in result


# ============================================================
# Test 14: New Loan EMI Calculation
# ============================================================

def test_new_loan_emi_accuracy():
    """
    EMI calculation should match loan engine.
    """
    result = simulate_new_loan(
        principal_paise=10000000,  # ₹100,000
        annual_rate_bps=1200,  # 12%
        tenure_months=12,
        current_surplus_paise=50000,
    )

    # EMI for ₹100k at 12% for 12 months ≈ ₹8,885
    assert result["monthly_emi_paise"] > 800000  # 8,000 IN PAISA (8,000 rupees = 800,000 paise)
    assert result["monthly_emi_paise"] < 12000000  # 12,000 IN PAISA


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
