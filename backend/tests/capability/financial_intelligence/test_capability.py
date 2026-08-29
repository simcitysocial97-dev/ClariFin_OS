"""Smoke tests for Financial Intelligence capability.

M9-C42.25 — registers financial_intelligence as a real capability test-domain.
The engine (intelligence aggregation + optimization + scenario + goal planning)
is a genuine production capability: it has a router, a service, and a pure
function layer. This binds the engine via direct import and exercises the
public report pipeline with deterministic paise inputs.
"""

from __future__ import annotations

from decimal import Decimal

from src.engines.financial_intelligence import (
    build_financial_snapshot,
    calculate_emergency_fund_target,
    calculate_goal_projection,
    compare_scenario,
    generate_financial_intelligence_report,
    generate_optimization_plan,
    optimize_surplus_allocation,
    simulate_expense_reduction,
)


class TestFinancialIntelligenceCapability:
    """Validate Financial Intelligence capability wiring and invariants."""

    def test_import_financial_intelligence_engine(self) -> None:
        """Financial intelligence engine must be importable."""
        from src.engines import financial_intelligence

        assert financial_intelligence is not None

    def test_public_api_exports(self) -> None:
        """Package-level API must expose the canonical functions."""
        assert callable(build_financial_snapshot)
        assert callable(generate_optimization_plan)
        assert callable(generate_financial_intelligence_report)
        assert callable(calculate_goal_projection)
        assert callable(optimize_surplus_allocation)

    def test_intelligence_report_produces_valid_structure(self) -> None:
        """Master report must emit snapshot, health score, and confidence."""
        state = {
            "cashflow": {"monthly_surplus_paise": 100_000},
            "liquidity": {
                "risk_level": "low",
                "months_until_stress": None,
                "projected_min_balance_paise": 5_000_000,
            },
            "debts": [],
            "goals": [],
            "behaviour": {"wellness_score": 75},
            "forecasts": {"cashflow": {"forecast": [], "confidence": Decimal("0.8")}},
            "optimization": {"recommended_actions": [], "warnings": []},
        }
        report = generate_financial_intelligence_report(state)
        assert report["health_score"] == Decimal("75")
        assert "snapshot" in report
        assert "priorities" in report
        assert "risks" in report
        assert 0 <= report["health_score"] <= 100

    def test_optimization_plan_wiring(self) -> None:
        """Optimization plan must allocate a positive surplus."""
        state = {
            "surplus": {"monthly_surplus_paise": 100_000},
            "debts": [],
            "goals": [],
            "forecast": {"current_liquidity_paise": 9_000_000},
            "risk": {"credit_revolver_ratio": "0"},
        }
        result = generate_optimization_plan(state)
        assert result["allocation_plan"]
        assert result["confidence"] > 0

    def test_goal_projection_paise_invariant(self) -> None:
        """Goal projection must keep all amounts as integer paise."""
        result = calculate_emergency_fund_target(100_000, months_of_cover=6)
        assert isinstance(result["recommended_target_paise"], int)
        assert result["recommended_target_paise"] == 600_000

    def test_scenario_comparison_wiring(self) -> None:
        """Scenario simulation + comparison must round-trip deterministically."""
        base = [{"expected_surplus_paise": 50_000}]
        sim = simulate_expense_reduction(100_000, 10_000, base, forecast_months=1)
        comparison = compare_scenario(
            {"cumulative_benefit_paise": 0},
            {"cumulative_benefit_paise": sim["cumulative_benefit_paise"]},
        )
        assert comparison["delta"]["cumulative_benefit_paise"] == 10_000
