"""Tests for Financial Intelligence Forecasting Engine.

Run: python -m pytest tests/test_financial_forecasting.py -v
"""

import ast
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.engines.financial_intelligence import (
    DEFAULT_EMERGENCY_THRESHOLD_PAISE,
    DEFAULT_FORECAST_MONTHS,
    forecast_cashflow,
    forecast_liquidity,
    forecast_credit_utilization,
    detect_future_cash_shortfall,
)


# ============================================================
# Test 1: Stable income/expense history produces stable forecast
# ============================================================

def test_stable_income_expense_produces_stable_forecast():
    """
    Stable income/expense history should produce stable forecast.
    """
    cashflow_history = [
        {"month": "2026-01", "income_paise": 100000, "expense_paise": 80000, "surplus_paise": 20000},
        {"month": "2026-02", "income_paise": 100000, "expense_paise": 80000, "surplus_paise": 20000},
        {"month": "2026-03", "income_paise": 100000, "expense_paise": 80000, "surplus_paise": 20000},
    ]

    result = forecast_cashflow(cashflow_history, forecast_months=3)

    assert len(result["forecast"]) == 3
    assert result["forecast"][0]["expected_income_paise"] == 100000
    assert result["forecast"][0]["expected_expense_paise"] == 80000
    assert result["forecast"][0]["expected_surplus_paise"] == 20000
    assert result["confidence"] > Decimal("0.5")  # High confidence for stable data


# ============================================================
# Test 2: Increasing expenses shows worsening surplus
# ============================================================

def test_increasing_expenses_worsens_surplus():
    """
    Increasing expenses should show declining surplus in forecast.
    """
    cashflow_history = [
        {"month": "2026-01", "income_paise": 100000, "expense_paise": 70000, "surplus_paise": 30000},
        {"month": "2026-02", "income_paise": 100000, "expense_paise": 75000, "surplus_paise": 25000},
        {"month": "2026-03", "income_paise": 100000, "expense_paise": 80000, "surplus_paise": 20000},
    ]

    result = forecast_cashflow(cashflow_history, forecast_months=3)

    # Weighted average gives more weight to recent months (80000 expense)
    # So forecast should be close to recent trend
    assert result["forecast"][0]["expected_expense_paise"] >= 75000


# ============================================================
# Test 3: Empty history returns safe response
# ============================================================

def test_empty_history_returns_safe_response():
    """
    Empty history should return forecast with zero values.
    """
    result = forecast_cashflow([], forecast_months=3)

    assert len(result["forecast"]) == 3
    assert all(f["expected_income_paise"] == 0 for f in result["forecast"])
    assert all(f["expected_expense_paise"] == 0 for f in result["forecast"])
    assert result["confidence"] == Decimal("0.5")  # Neutral confidence
    assert "model_version" in result


# ============================================================
# Test 4: Healthy liquidity forecast
# ============================================================

def test_healthy_liquidity_forecast():
    """
    Healthy liquidity with positive surplus should show low risk.
    """
    cashflow_forecast = [
        {"month": "2026-04", "expected_surplus_paise": 30000},
        {"month": "2026-05", "expected_surplus_paise": 30000},
        {"month": "2026-06", "expected_surplus_paise": 30000},
    ]

    result = forecast_liquidity(
        current_liquidity_paise=4000000,  # ₹40,000 buffer - above threshold
        cashflow_forecast=cashflow_forecast,
        emergency_threshold_paise=3000000,  # ₹30,000 threshold
    )

    assert result["months_until_stress"] is None
    assert result["projected_min_balance_paise"] >= 3000000
    assert result["risk_level"] == "low"


# ============================================================
# Test 5: Future deficit detection
# ============================================================

def test_future_deficit_detection():
    """
    Negative surplus months should trigger stress detection.
    """
    cashflow_forecast = [
        {"month": "2026-04", "expected_surplus_paise": -400000},  # Large deficit
        {"month": "2026-05", "expected_surplus_paise": -400000},  # Large deficit
        {"month": "2026-06", "expected_surplus_paise": 10000},
    ]

    result = forecast_liquidity(
        current_liquidity_paise=3500000,  # ₹35,000 buffer
        cashflow_forecast=cashflow_forecast,
        emergency_threshold_paise=3000000,  # ₹30,000 threshold
    )

    # Month 1: 3500000 - 400000 = 3100000 (above threshold)
    # Month 2: 3100000 - 400000 = 2700000 (below threshold) -> stress month 2
    assert result["months_until_stress"] == 2
    assert result["risk_level"] == "high"


# ============================================================
# Test 6: Emergency threshold crossing
# ============================================================

def test_emergency_threshold_crossing():
    """
    When projected balance drops below threshold, stress month is identified.
    """
    cashflow_forecast = [
        {"month": "2026-04", "expected_surplus_paise": -100000},
        {"month": "2026-05", "expected_surplus_paise": 50000},
        {"month": "2026-06", "expected_surplus_paise": 50000},
    ]

    result = forecast_liquidity(
        current_liquidity_paise=1000000,  # ₹10,000 - already below threshold
        cashflow_forecast=cashflow_forecast,
        emergency_threshold_paise=3000000,  # ₹30,000
    )

    assert result["months_until_stress"] == 1
    assert result["risk_level"] == "high"


# ============================================================
# Test 7: Stable credit behavior detected
# ============================================================

def test_stable_credit_behavior():
    """
    Stable utilization should show stable trend.
    """
    credit_history = [
        {"month": "2026-01", "utilization_ratio": 0.3},
        {"month": "2026-02", "utilization_ratio": 0.3},
        {"month": "2026-03", "utilization_ratio": 0.3},
    ]

    result = forecast_credit_utilization([], credit_history)

    assert result["trend"] == "stable"
    assert result["current_dependency_ratio"] == Decimal("0.3")
    assert result["forecast_dependency_ratio"] == Decimal("0.3")


# ============================================================
# Test 8: Worsening credit trend detected
# ============================================================

def test_worsening_credit_trend():
    """
    Increasing utilization should show worsening trend.
    """
    credit_history = [
        {"month": "2026-01", "utilization_ratio": 0.2},
        {"month": "2026-02", "utilization_ratio": 0.3},
        {"month": "2026-03", "utilization_ratio": 0.4},
    ]

    result = forecast_credit_utilization([], credit_history)

    assert result["trend"] == "worsening"
    assert result["forecast_dependency_ratio"] > result["current_dependency_ratio"]


# ============================================================
# Test 9: No future shortfall
# ============================================================

def test_no_future_shortfall():
    """
    Positive forecast with healthy liquidity should show no shortfall.
    """
    cashflow_forecast = [
        {"month": "2026-04", "expected_surplus_paise": 50000},
        {"month": "2026-05", "expected_surplus_paise": 50000},
        {"month": "2026-06", "expected_surplus_paise": 50000},
    ]

    liquidity_forecast = {
        "months_until_stress": None,
        "projected_min_balance_paise": 5000000,
        "risk_level": "low",
    }

    result = detect_future_cash_shortfall(cashflow_forecast, liquidity_forecast)

    assert result["flag"] is False
    assert result["severity"] == "none"
    assert result["expected_month"] is None


# ============================================================
# Test 10: Warning shortfall
# ============================================================

def test_warning_shortfall():
    """
    Imminent stress (month 3+) should show warning severity.
    """
    cashflow_forecast = [
        {"month": "2026-04", "expected_surplus_paise": 50000},
        {"month": "2026-05", "expected_surplus_paise": 50000},
        {"month": "2026-06", "expected_surplus_paise": -100000},  # Will trigger stress
    ]

    liquidity_forecast = {
        "months_until_stress": 3,
        "projected_min_balance_paise": 3100000,
        "risk_level": "medium",
    }

    result = detect_future_cash_shortfall(cashflow_forecast, liquidity_forecast)

    assert result["flag"] is True
    assert result["severity"] == "warning"


# ============================================================
# Test 11: Critical shortfall
# ============================================================

def test_critical_shortfall():
    """
    Immediate stress (month 1) should show critical severity.
    """
    cashflow_forecast = [
        {"month": "2026-04", "expected_surplus_paise": -50000},
    ]

    liquidity_forecast = {
        "months_until_stress": 1,
        "projected_min_balance_paise": 1000000,
        "risk_level": "high",
    }

    result = detect_future_cash_shortfall(cashflow_forecast, liquidity_forecast)

    assert result["flag"] is True
    assert result["severity"] == "critical"


# ============================================================
# Test 12: Engine purity - no DB calls
# ============================================================

def test_engine_purity_no_db_calls():
    """
    Engine files should make ZERO database calls.
    This test verifies no sqlite3 or repository imports in engine code.
    """
    engine_package_path = Path(__file__).parent.parent / "src" / "engines" / "financial_intelligence"

    for py_file in engine_package_path.glob("*.py"):
        if py_file.name == "__pycache__":
            continue

        source = py_file.read_text()
        tree = ast.parse(source)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append(module)
                # Check for any imports from src.repositories
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        # Verify no sqlite3 imports
        assert "sqlite3" not in imports, f"sqlite3 import found in {py_file.name}"

        # Verify no repository imports
        for imp in imports:
            assert "repositories" not in imp, f"Repository import found in {py_file.name}: {imp}"


# ============================================================
# Test 13: Deterministic output
# ============================================================

def test_deterministic_output():
    """
    Same input should always produce same output.
    """
    cashflow_history = [
        {"month": "2026-01", "income_paise": 100000, "expense_paise": 80000},
    ]

    result1 = forecast_cashflow(cashflow_history)
    result2 = forecast_cashflow(cashflow_history)

    assert result1 == result2
    assert result1["confidence"] == result2["confidence"]


# ============================================================
# Test 14: Forecast months validation
# ============================================================

def test_forecast_months_validation():
    """
    Forecast months should be clamped to valid range (1-12).
    """
    cashflow_history = [
        {"month": "2026-01", "income_paise": 100000, "expense_paise": 80000},
    ]

    # Test minimum clamping
    result = forecast_cashflow(cashflow_history, forecast_months=0)
    assert len(result["forecast"]) == 1

    # Test maximum clamping
    result = forecast_cashflow(cashflow_history, forecast_months=20)
    assert len(result["forecast"]) == 12


# ============================================================
# Test 15: Credit events analysis
# ============================================================

def test_credit_events_analysis():
    """
    Financial events with credit advances should influence dependency ratio.
    """
    financial_events = [
        {
            "id": 1,
            "event_type": "cash_advance",
            "amount_paise": 30000,
            "liability_change_paise": 30000,
            "month_bucket": "2026-01",
            "lifecycle_state": "open",
        },
    ]

    result = forecast_credit_utilization(financial_events, [])

    assert result["trend"] == "stable"
    assert "model_version" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])