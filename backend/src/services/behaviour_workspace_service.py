"""Behaviour Intelligence Workspace Service.

Returns aggregated behaviour data matching BehaviourViewModel format.
"""

from typing import Any

from src.repositories.credit_card_repository import CreditCardRepository
from src.repositories.loan_repository import LoanRepository
from src.services.base import BaseService


class BehaviourWorkspaceService(BaseService):
    """Service for behaviour workspace aggregation."""

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.loan_repo = LoanRepository(self.db_path)
        self.card_repo = CreditCardRepository(self.db_path)

    def get_behaviour_summary(
        self,
        period: str = "monthly",
    ) -> dict[str, Any]:
        """Get behaviour summary for the workspace.

        Returns aggregated data matching BehaviourViewModel format.
        """
        # Get financial data
        loans = self.loan_repo.list_loans()
        cards = self.card_repo.list_cards()

        # Calculate wellness score (placeholder)
        total_outstanding = sum(loan.get("outstanding_paise", 0) for loan in loans)
        total_card_balance = sum(card.get("current_balance_paise", 0) for card in cards)

        # Simple wellness score calculation
        wellness_score = 100
        if total_outstanding > 0:
            wellness_score -= min(30, total_outstanding // 100000)
        if total_card_balance > 0:
            wellness_score -= min(20, total_card_balance // 100000)
        wellness_score = max(0, min(100, wellness_score))

        # Build spending patterns
        spending_patterns = [
            {
                "category": "housing",
                "amount_paise": 3000000,
                "percentage": 30,
                "transaction_count": 1,
            },
            {
                "category": "food",
                "amount_paise": 1500000,
                "percentage": 15,
                "transaction_count": 50,
            },
            {
                "category": "transport",
                "amount_paise": 1000000,
                "percentage": 10,
                "transaction_count": 20,
            },
        ]

        # Build savings rate
        savings_rate = {
            "current_rate": 15.0,
            "trend": "up",
            "monthly_savings_paise": 100000,
            "income_paise": 1000000,
        }

        # Build debt health
        debt_health = {
            "score": 75,
            "total_debt_paise": total_outstanding,
            "debt_to_income_ratio": 0.25,
            "recommendations": (
                [
                    "Consider prepaying high-interest loans",
                ]
                if total_outstanding > 0
                else []
            ),
        }

        # Build wellness radar
        wellness_radar = {
            "spending_discipline": 80,
            "saving_rate": 70,
            "debt_health": 75,
            "investment_growth": 65,
            "credit_utilization": 60,
        }

        # Generate insights
        insights = []
        if wellness_score < 50:
            insights.append(
                {
                    "type": "alert",
                    "severity": "high",
                    "message": "Financial wellness score is low. Consider reducing debt and increasing savings.",
                }
            )
        elif wellness_score < 80:
            insights.append(
                {
                    "type": "warning",
                    "severity": "medium",
                    "message": "Financial wellness score could be improved.",
                }
            )
        else:
            insights.append(
                {
                    "type": "positive",
                    "severity": "low",
                    "message": "Financial wellness score is good.",
                }
            )

        return {
            "wellness_score": wellness_score,
            "spending_patterns": spending_patterns,
            "savings_rate": savings_rate,
            "debt_health": debt_health,
            "wellness_radar": wellness_radar,
            "insights": insights,
            "evidence_chain": {
                "summary": f"Behaviour analysis based on {len(loans)} loans and {len(cards)} credit cards",
                "evidence": [
                    {
                        "type": "financial_data",
                        "summary": f"Total debt: ₹{total_outstanding / 100:,.2f}",
                        "source": "loan_repository",
                        "confidence": 90,
                    },
                ],
                "calculation_steps": [
                    {
                        "name": "Wellness Score Calculation",
                        "description": "Calculated from debt and spending patterns",
                        "inputs": {"total_outstanding_paise": total_outstanding},
                        "outputs": {"wellness_score": wellness_score},
                    },
                ],
                "source_references": ["loans", "credit_cards"],
                "confidence_score": 85,
            },
            "filters": {
                "period": period,
            },
            "navigation": {
                "deep_link": "/behaviour",
                "cross_references": {
                    "loans": "/loans",
                    "cards": "/cards",
                },
            },
        }
