"""Integration tests for Financial Intelligence Report.

Tests the composition of multiple services and engines:
- BehaviourService → behaviour profile
- CashflowService → monthly analysis
- LoanService → loans
- CreditCardService → credit cards
- Optimization engine → optimization plan

Verifies that FinancialIntelligenceService.get_financial_intelligence_report()
correctly orchestrates and aggregates all components.
Note: Uses engine functions directly to avoid database dependencies.
"""

from decimal import Decimal

from src.engines.financial_intelligence.intelligence import (
    generate_financial_intelligence_report,
)


class TestFinancialIntelligenceEngineIntegration:
    """Integration tests for intelligence engine composition."""

    def test_financial_intelligence_report_integration_with_all_domains(self):
        """Test full integration with mocked domain data."""
        # Simulate data from all domains combined
        financial_state = {
            "cashflow": {
                "monthly_surplus_paise": 300000,
                "income_paise": 1000000,
                "expense_paise": 700000,
            },
            "liquidity": {
                "risk_level": "low",
                "months_until_stress": None,
                "projected_min_balance_paise": 1000000,
            },
            "debts": [
                {"id": "loan-1", "type": "loan", "outstanding_paise": 50000000, "interest_rate_bps": 850},
                {"id": "card-1", "type": "credit_card", "outstanding_paise": 500000, "interest_rate_bps": 3600},
            ],
            "goals": [
                {"id": "goal-1", "goal_type": "emergency_fund", "target_amount_paise": 3000000, "status": "active"},
            ],
            "behaviour": {
                "wellness_score": Decimal("75"),
                "credit_revolver_ratio": Decimal("0.3"),
                "debt_cycle_score": 40,
            },
            "forecasts": {
                "cashflow": {"forecast": [{"month": "2026-01"}]},
                "credit": {"trend": "stable", "current_dependency_ratio": Decimal("0.2")},
            },
            "optimization": {
                "recommended_actions": [{"action": "increase_investment", "impact": "medium"}],
                "warnings": [],
            },
        }

        result = generate_financial_intelligence_report(financial_state)

        # Verify all sections exist
        assert "snapshot" in result
        assert "health_score" in result
        assert "priorities" in result
        assert "risks" in result
        assert "opportunities" in result
        assert "confidence" in result

        # Verify snapshot contains all domain data
        assert result["snapshot"]["cashflow"]["monthly_surplus_paise"] == 300000
        assert len(result["snapshot"]["debts"]) == 2
        assert len(result["snapshot"]["goals"]) == 1

    def test_financial_intelligence_report_risk_aggregation(self):
        """Test that risks are aggregated from multiple sources."""
        financial_state = {
            "cashflow": {"monthly_surplus_paise": 500000},
            "liquidity": {
                "risk_level": "high",
                "months_until_stress": 1,
                "projected_min_balance_paise": 100000,
            },
            "debts": [],
            "goals": [],
            "behaviour": {"debt_cycle_score": 80},  # High debt cycle
            "forecasts": {
                "credit": {"trend": "worsening"},  # Deteriorating credit
            },
            "optimization": {"warnings": ["Emergency fund below target"]},
        }

        result = generate_financial_intelligence_report(financial_state)

        # Should have multiple risk sources
        risks = result["risks"]
        assert len(risks) > 0
        risk_types = {r["type"] for r in risks}
        assert "liquidity_stress" in risk_types or "debt_cycle" in risk_types

    def test_financial_intelligence_report_opportunities(self):
        """Test that opportunities are identified correctly."""
        financial_state = {
            "cashflow": {"monthly_surplus_paise": 600000},  # High surplus
            "liquidity": {},
            "debts": [],
            "goals": [
                {"goal_type": "emergency_fund", "status": "active", "target_amount_paise": 3000000, "current_amount_paise": 1000000},
            ],
            "behaviour": {"wellness_score": Decimal("70")},
            "forecasts": {},
            "optimization": {"warnings": []},
        }

        result = generate_financial_intelligence_report(financial_state)

        # Should identify surplus opportunity
        opportunities = result["opportunities"]
        assert len(opportunities) > 0
        assert any(o["type"] == "surplus_investment" for o in opportunities)