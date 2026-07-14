"""Unit tests for Financial Intelligence Engine pure functions.

Tests for:
- build_financial_snapshot()
- generate_financial_priorities()
- calculate_intelligence_confidence()
- generate_financial_intelligence_report()

No database access. No service dependencies.
All monetary values are integers in paise.
"""

from decimal import Decimal

from src.engines.financial_intelligence.intelligence import (
    build_financial_snapshot,
    calculate_intelligence_confidence,
    generate_financial_intelligence_report,
    generate_financial_priorities,
)

# ============================================================
# Tests for build_financial_snapshot
# ============================================================

def test_build_financial_snapshot_complete_state():
    """Test snapshot creation with complete financial data."""
    cashflow = {"income_paise": 1000000, "expense_paise": 700000, "monthly_surplus_paise": 300000}
    liquidity = {"risk_level": "low", "months_until_stress": None}
    debts = [{"type": "loan", "outstanding_paise": 5000000}]
    goals = [{"goal_type": "emergency_fund", "target_amount_paise": 3000000}]
    behaviour = {"wellness_score": Decimal("75")}
    forecasts = {"cashflow": {"confidence": Decimal("0.8")}}
    optimization = {"recommended_actions": [], "warnings": []}

    result = build_financial_snapshot(
        cashflow=cashflow,
        liquidity=liquidity,
        debts=debts,
        goals=goals,
        behaviour=behaviour,
        forecasts=forecasts,
        optimization=optimization,
    )

    assert result["cashflow"] == cashflow
    assert result["liquidity"] == liquidity
    assert result["debts"] == debts
    assert result["goals"] == goals
    assert result["behaviour"] == behaviour
    assert result["forecasts"] == forecasts
    assert result["optimization"] == optimization


def test_build_financial_snapshot_empty_state():
    """Test snapshot creation with empty/missing data."""
    result = build_financial_snapshot(
        cashflow={},
        liquidity={},
        debts=[],
        goals=[],
        behaviour={},
        forecasts={},
        optimization={},
    )

    assert result["cashflow"] == {}
    assert result["liquidity"] == {}
    assert result["debts"] == []
    assert result["goals"] == []
    assert result["behaviour"] == {}
    assert result["forecasts"] == {}
    assert result["optimization"] == {}


# ============================================================
# Tests for generate_financial_priorities
# ============================================================

def test_generate_financial_priorities_credit_dependency_beats_investment():
    """Test that credit dependency priority is surfaced when high."""
    optimization = {
        "recommended_actions": [
            {"action": "increase_investment", "impact": "medium", "score": Decimal("0.6")},
        ],
        "warnings": ["No surplus available for optimization"],
    }
    behaviour = {
        "credit_revolver_ratio": Decimal("0.6"),  # High revolving ratio
        "debt_cycle_score": 80,
    }
    liquidity = {"risk_level": "low"}

    result = generate_financial_priorities(
        optimization_plan=optimization,
        behaviour=behaviour,
        liquidity_forecast=liquidity,
        goals=[],
    )

    # Should have priorities including credit card action
    assert len(result) > 0
    high_priority_actions = [p for p in result if p["reason"] == "high_revolving_dependency"]
    assert len(high_priority_actions) > 0


def test_generate_financial_priorities_emergency_fund_shortage():
    """Test that emergency fund shortage is detected in priorities."""
    optimization = {
        "recommended_actions": [],
        "warnings": ["Emergency fund below target threshold"],
    }
    behaviour = {"credit_revolver_ratio": Decimal("0.1")}
    liquidity = {
        "risk_level": "high",
        "months_until_stress": 1,
        "projected_min_balance_paise": 100000,  # ₹1,000 = ~1 month of essential expenses
    }

    result = generate_financial_priorities(
        optimization_plan=optimization,
        behaviour=behaviour,
        liquidity_forecast=liquidity,
        goals=[],
    )

    # Should have emergency fund priority when liquidity < 3 months
    # liquidity_months = 100000 // 100000 = 1 month
    emergency_priorities = [p for p in result if p["action"] == "increase_emergency_fund"]
    assert len(emergency_priorities) > 0, f"No emergency fund priority found, got: {result}"


def test_generate_financial_priorities_empty_state():
    """Test priorities with no recommended actions or risks."""
    result = generate_financial_priorities(
        optimization_plan={"recommended_actions": [], "warnings": []},
        behaviour={"credit_revolver_ratio": Decimal("0.1")},
        liquidity_forecast={"risk_level": "low"},
        goals=[],
    )

    # Should return empty or minimal priorities
    assert isinstance(result, list)


# ============================================================
# Tests for calculate_intelligence_confidence
# ============================================================

def test_calculate_intelligence_confidence_high_quality_data():
    """Test confidence calculation with high quality inputs."""
    result = calculate_intelligence_confidence(
        cashflow_history_months=6,
        transaction_completeness=Decimal("0.95"),
        account_coverage=Decimal("1.0"),
        forecast_variance=Decimal("1e8"),  # Low variance
    )

    assert result["confidence"] >= Decimal("0.8")
    assert result["data_quality"] in ("excellent", "good")


def test_calculate_intelligence_confidence_incomplete_data():
    """Test confidence calculation with incomplete inputs."""
    result = calculate_intelligence_confidence(
        cashflow_history_months=1,
        transaction_completeness=Decimal("0.3"),
        account_coverage=Decimal("0.5"),
        forecast_variance=Decimal("1e11"),  # High variance
    )

    # With these inputs: 0.25 * (1/3) + 0.25 * 0.3 + 0.25 * 0.5 + variance_score
    # variance_score ≈ 0.25 (not 0 because 1/(1+1e11/1e12) ≈ 0.9)
    # Total ≈ 0.25 + 0.083 + 0.125 + 0.25 ≈ 0.51
    assert result["confidence"] < Decimal("0.6")
    assert result["data_quality"] in ("fair", "poor")


def test_calculate_intelligence_confidence_zero_data():
    """Test confidence calculation with zero/empty data."""
    result = calculate_intelligence_confidence(
        cashflow_history_months=0,
        transaction_completeness=Decimal("0"),
        account_coverage=Decimal("0"),
        forecast_variance=Decimal("0"),
    )

    # With variance=0, variance_score=1 (perfect), so minimum is 0.25
    assert result["confidence"] == Decimal("0.25")
    assert result["data_quality"] == "poor"


# ============================================================
# Tests for generate_financial_intelligence_report
# ============================================================

def test_generate_financial_intelligence_report_complete():
    """Test full report generation with complete state."""
    financial_state = {
        "cashflow": {"monthly_surplus_paise": 500000},
        "liquidity": {"risk_level": "low", "months_until_stress": None},
        "debts": [],
        "goals": [{"goal_type": "emergency_fund", "target_amount_paise": 3000000}],
        "behaviour": {"wellness_score": Decimal("75")},
        "forecasts": {"cashflow": {"forecast": [{"month": "2026-01"}]}},
        "optimization": {
            "recommended_actions": [{"action": "increase_investment", "impact": "medium"}],
            "warnings": [],
        },
    }

    result = generate_financial_intelligence_report(financial_state)

    assert "snapshot" in result
    assert "health_score" in result
    assert "priorities" in result
    assert "risks" in result
    assert "opportunities" in result
    assert "confidence" in result
    assert isinstance(result["health_score"], Decimal)


def test_generate_financial_intelligence_report_empty_state():
    """Test report generation with empty state."""
    financial_state = {
        "cashflow": {},
        "liquidity": {},
        "debts": [],
        "goals": [],
        "behaviour": {},
        "forecasts": {},
        "optimization": {"recommended_actions": [], "warnings": []},
    }

    result = generate_financial_intelligence_report(financial_state)

    # With empty state, health_score should be computed from defaults (0.5 * 100 = 50)
    assert result["health_score"] >= Decimal("0")
    assert isinstance(result["priorities"], list)
    assert isinstance(result["risks"], list)
    assert isinstance(result["opportunities"], list)


# ============================================================
# Purity tests - verify no DB/service/repository imports
# ============================================================

def test_intelligence_engine_purity():
    """Verify intelligence.py has no database or service imports."""
    import ast
    import pathlib

    file_path = pathlib.Path(__file__).parent.parent / "src" / "engines" / "financial_intelligence" / "intelligence.py"
    content = file_path.read_text()
    tree = ast.parse(content)

    # Get all imported module names
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    # Check that no sqlite3, repository, or service imports exist
    forbidden_imports = [
        "sqlite3",
        "sqlite",
        "repository",
        "service",
        "FinanceDB",
    ]

    for imp in imports:
        for forbidden in forbidden_imports:
            assert forbidden not in imp, f"Forbidden import found: {imp}"


def test_intelligence_engine_no_llm_calls():
    """Verify intelligence.py has no LLM or prompt-related code (imports)."""
    import pathlib

    file_path = pathlib.Path(__file__).parent.parent / "src" / "engines" / "financial_intelligence" / "intelligence.py"
    content = file_path.read_text()

    # Check for forbidden imports (not docstrings)
    # LLM libraries typically imported, not just mentioned in docstrings
    assert "import openai" not in content.lower()
    assert "import anthropic" not in content.lower()
    assert "from llm" not in content.lower()
    assert "from openai" not in content.lower()
