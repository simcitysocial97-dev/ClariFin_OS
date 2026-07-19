"""Investments Intelligence Workspace Service.

Returns aggregated investments data matching InvestmentsViewModel format.
"""

from typing import Any

from src.repositories.investment_repository import InvestmentRepository
from src.services.base import BaseService


class InvestmentsWorkspaceService(BaseService):
    """Service for investments workspace aggregation."""

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.investment_repo = InvestmentRepository(self.db_path)

    def get_investments_summary(
        self,
        investment_types: list[str] | None = None,
        institutions: list[str] | None = None,
        statuses: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get investments summary for the workspace.

        Returns aggregated data matching InvestmentsViewModel format.
        """
        # Get all investments
        all_investments = self.investment_repo.list_investments()

        # Apply filters
        investments = all_investments
        if investment_types:
            investments = [i for i in investments if i.get("investment_type") in investment_types]
        if institutions:
            investments = [i for i in investments if i.get("institution") in institutions]
        if statuses:
            investments = [i for i in investments if i.get("status") in statuses]

        # Calculate totals
        total_value = sum(i.get("current_value_paise", 0) for i in investments)
        total_invested = sum(i.get("invested_paise", 0) for i in investments)
        total_returns = total_value - total_invested

        # Build investment summaries
        investment_summaries = []
        for inv in investments:
            investment_summaries.append({
                "id": inv.get("investment_id", ""),
                "name": inv.get("name", ""),
                "institution": inv.get("institution", ""),
                "investment_type": inv.get("investment_type", ""),
                "invested_paise": inv.get("invested_paise", 0),
                "current_value_paise": inv.get("current_value_paise", 0),
                "returns_paise": inv.get("current_value_paise", 0) - inv.get("invested_paise", 0),
                "returns_percentage": int((inv.get("current_value_paise", 0) - inv.get("invested_paise", 0)) / inv.get("invested_paise", 1) * 100) if inv.get("invested_paise", 0) > 0 else 0,
                "status": inv.get("status", "active"),
            })

        # Build performance data (placeholder)
        performance = []
        for inv in investments:
            performance.append({
                "investment_id": inv.get("investment_id", ""),
                "date": "2025-01-01",
                "value_paise": inv.get("current_value_paise", 0),
                "returns_paise": inv.get("current_value_paise", 0) - inv.get("invested_paise", 0),
            })

        # Build asset allocation
        allocation = []
        for inv in investments:
            allocation.append({
                "investment_id": inv.get("investment_id", ""),
                "type": inv.get("investment_type", ""),
                "value_paise": inv.get("current_value_paise", 0),
                "percentage": int(inv.get("current_value_paise", 0) / total_value * 100) if total_value > 0 else 0,
            })

        # Build holdings table
        holdings = []
        for inv in investments:
            holdings.append({
                "id": inv.get("investment_id", ""),
                "name": inv.get("name", ""),
                "type": inv.get("investment_type", ""),
                "institution": inv.get("institution", ""),
                "invested_paise": inv.get("invested_paise", 0),
                "value_paise": inv.get("current_value_paise", 0),
                "returns_paise": inv.get("current_value_paise", 0) - inv.get("invested_paise", 0),
                "returns_percentage": int((inv.get("current_value_paise", 0) - inv.get("invested_paise", 0)) / inv.get("invested_paise", 1) * 100) if inv.get("invested_paise", 0) > 0 else 0,
                "status": inv.get("status", "active"),
            })

        # Generate insights
        insights = []
        if total_returns > 0:
            insights.append({
                "type": "positive",
                "severity": "medium",
                "message": f"Total returns: ₹{total_returns / 100:,.2f}",
            })

        return {
            "investments": investment_summaries,
            "total_value_paise": total_value,
            "total_invested_paise": total_invested,
            "total_returns_paise": total_returns,
            "investment_count": len(investments),
            "performance": performance,
            "allocation": allocation,
            "holdings": holdings,
            "insights": insights,
            "evidence_chain": {
                "summary": f"Investments summary for {len(investments)} active investments",
                "evidence": [
                    {
                        "type": "investment_data",
                        "summary": f"Total value: ₹{total_value / 100:,.2f}",
                        "source": "investment_repository",
                        "confidence": 95,
                    },
                ],
                "calculation_steps": [
                    {
                        "name": "Total Value Calculation",
                        "description": "Sum of all investment current values",
                        "inputs": {"investment_count": len(investments)},
                        "outputs": {"total_value_paise": total_value},
                    },
                ],
                "source_references": ["investments"],
                "confidence_score": 90,
            },
            "filters": {
                "investment_types": investment_types,
                "institutions": institutions,
                "statuses": statuses,
            },
            "navigation": {
                "deep_link": "/investments",
                "cross_references": {
                    "net_worth": "/net-worth",
                    "accounts": "/accounts",
                },
            },
        }
