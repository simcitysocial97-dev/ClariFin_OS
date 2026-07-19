"""Forecast Service - Orchestration layer for forecast operations.

Coordinates repositories and engines to implement business logic for the Forecast Intelligence Workspace.
No direct database access - uses repositories only.
"""

from typing import Any

from src.repositories.credit_card_repository import CreditCardRepository
from src.repositories.investment_repository import InvestmentRepository
from src.repositories.loan_repository import LoanRepository
from src.services.base import BaseService


class ForecastService(BaseService):
    """Service for forecast calculation and orchestration."""

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.loan_repo = LoanRepository(self.db_path)
        self.card_repo = CreditCardRepository(self.db_path)
        self.investment_repo = InvestmentRepository(self.db_path)

    def get_forecast_summary(
        self,
        horizon_months: int = 12,
        scenarios: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get forecast summary for the workspace.

        Returns aggregated data matching ForecastViewModel format.
        """
        # Get current financial state
        loans = self.loan_repo.list_loans()
        cards = self.card_repo.list_cards()
        investments = self.investment_repo.list_investments()

        # Calculate current net worth
        total_assets = sum(inv.get("current_value_paise", 0) for inv in investments)
        total_liabilities = sum(loan.get("outstanding_paise", 0) for loan in loans)
        current_net_worth = total_assets - total_liabilities

        # Simple projection: assume 5% annual growth for assets, 0% for liabilities
        monthly_growth_rate = 0.05 / 12
        projected_net_worth = int(current_net_worth * (1 + monthly_growth_rate) ** horizon_months)

        # Calculate growth
        projected_growth = projected_net_worth - current_net_worth
        growth_percentage = (projected_growth / current_net_worth * 100) if current_net_worth > 0 else 0

        return {
            "summary": {
                "horizon_months": horizon_months,
                "current_net_worth_paise": current_net_worth,
                "projected_net_worth_paise": projected_net_worth,
                "projected_growth_paise": projected_growth,
                "projected_growth_percentage": round(growth_percentage, 2),
            },
            "net_worth_projections": self._generate_projections(
                current_net_worth, monthly_growth_rate, horizon_months
            ),
            "cashflow_projections": self._generate_cashflow_projections(horizon_months),
            "scenarios": self._generate_scenarios(
                current_net_worth, total_liabilities, horizon_months, scenarios
            ),
            "confidence_intervals": [
                {"level": 90, "lower_paise": int(current_net_worth * 0.9), "upper_paise": int(current_net_worth * 1.1)},
                {"level": 95, "lower_paise": int(current_net_worth * 0.85), "upper_paise": int(current_net_worth * 1.15)},
                {"level": 99, "lower_paise": int(current_net_worth * 0.8), "upper_paise": int(current_net_worth * 1.2)},
            ],
            "insights": self._generate_insights(current_net_worth, projected_net_worth),
            "evidence_chain": {
                "summary": f"Forecast calculated based on {len(loans)} loans, {len(cards)} cards, {len(investments)} investments",
                "evidence": [
                    {
                        "type": "current_state",
                        "summary": f"Current net worth: ₹{current_net_worth / 100:,.2f}",
                        "source": "net_worth_calculation",
                        "confidence": 95,
                    },
                ],
                "calculation_steps": [
                    {
                        "name": "Net Worth Calculation",
                        "description": "Assets minus liabilities",
                        "inputs": {"assets": total_assets, "liabilities": total_liabilities},
                        "outputs": {"net_worth": current_net_worth},
                    },
                ],
                "source_references": ["loans", "credit_cards", "investments"],
                "confidence_score": 85,
            },
            "filters": {
                "horizon": horizon_months,
                "scenarios": scenarios,
            },
            "navigation": {
                "deep_link": "/forecast",
                "cross_references": {
                    "net_worth": "/net-worth",
                    "cashflow": "/cashflow",
                },
            },
        }

    def _generate_projections(
        self,
        current_net_worth: int,
        monthly_growth_rate: float,
        horizon_months: int,
    ) -> list[dict[str, Any]]:
        """Generate net worth projections over time."""
        from datetime import date, timedelta

        projections = []
        for month in range(1, horizon_months + 1):
            projected = int(current_net_worth * (1 + monthly_growth_rate) ** month)
            lower = int(projected * 0.9)
            upper = int(projected * 1.1)

            # Calculate date
            future_date = date.today() + timedelta(days=30 * month)

            projections.append({
                "date": future_date.isoformat(),
                "projected_paise": projected,
                "lower_bound_paise": lower,
                "upper_bound_paise": upper,
            })

        return projections

    def _generate_cashflow_projections(self, horizon_months: int) -> list[dict[str, Any]]:
        """Generate cashflow projections over time."""
        from datetime import date, timedelta

        projections = []
        for month in range(1, horizon_months + 1):
            future_date = date.today() + timedelta(days=30 * month)
            month_label = future_date.strftime("%Y-%m")

            # Placeholder values - would be calculated from actual data
            income = 10000000  # ₹1,00,000
            expenses = 6000000  # ₹60,000
            net = income - expenses

            projections.append({
                "month": month_label,
                "income_paise": income,
                "expenses_paise": expenses,
                "net_paise": net,
            })

        return projections

    def _generate_scenarios(
        self,
        current_net_worth: int,
        total_liabilities: int,
        horizon_months: int,
        scenarios: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Generate forecast scenarios."""
        if scenarios is None or len(scenarios) == 0:
            # Default scenarios
            scenarios = ["conservative", "base", "optimistic"]

        result = []
        for scenario in scenarios:
            if scenario == "conservative":
                growth_rate = 0.02 / 12  # 2% annual
                probability = 7000  # 70%
            elif scenario == "optimistic":
                growth_rate = 0.08 / 12  # 8% annual
                probability = 3000  # 30%
            else:  # base
                growth_rate = 0.05 / 12  # 5% annual
                probability = 5000  # 50%

            projected = int(current_net_worth * (1 + growth_rate) ** horizon_months)

            result.append({
                "name": scenario.capitalize(),
                "description": f"{scenario.capitalize()} growth scenario",
                "probability_bps": probability,
                "net_worth_projections": [
                    {
                        "date": f"202{horizon_months}-01-01",
                        "projected_paise": projected,
                        "lower_bound_paise": int(projected * 0.9),
                        "upper_bound_paise": int(projected * 1.1),
                    },
                ],
                "cashflow_projections": [],
            })

        return result

    def _generate_insights(self, current_net_worth: int, projected_net_worth: int) -> list[dict[str, Any]]:
        """Generate forecast insights."""
        insights = []

        if projected_net_worth > current_net_worth:
            growth_pct = (projected_net_worth - current_net_worth) / current_net_worth * 100
            insights.append({
                "type": "positive",
                "severity": "medium",
                "message": f"Net worth projected to grow {growth_pct:.1f}% over the forecast period",
            })

        if current_net_worth < 0:
            insights.append({
                "type": "alert",
                "severity": "high",
                "message": "Current net worth is negative. Consider reducing liabilities.",
            })

        return insights
