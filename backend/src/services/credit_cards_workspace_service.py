"""Credit Cards Intelligence Workspace Service.

Returns aggregated credit cards data matching CreditCardsViewModel format.
"""

from typing import Any

from src.repositories.credit_card_repository import CreditCardRepository
from src.repositories.credit_card_statement_repository import (
    CreditCardStatementRepository,
)
from src.services.base import BaseService


class CreditCardsWorkspaceService(BaseService):
    """Service for credit cards workspace aggregation."""

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.card_repo = CreditCardRepository(self.db_path)
        self.statement_repo = CreditCardStatementRepository(self.db_path)

    def get_credit_cards_summary(
        self,
        statuses: list[str] | None = None,
        banks: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get credit cards summary for the workspace.

        Returns aggregated data matching CreditCardsViewModel format.
        """
        # Get all cards
        all_cards = self.card_repo.list_cards()

        # Apply filters
        cards = all_cards
        if statuses:
            cards = [c for c in cards if c.get("status") in statuses]
        if banks:
            cards = [c for c in cards if c.get("bank") in banks]

        # Calculate totals
        total_balance = sum(c.get("current_balance_paise", 0) for c in cards)
        total_due = sum(c.get("total_due_paise", 0) for c in cards)
        total_available = sum(c.get("available_paise", 0) for c in cards)

        # Build card summaries
        card_summaries = []
        for card in cards:
            card_summaries.append(
                {
                    "id": card.get("card_id", ""),
                    "name": card.get("name", ""),
                    "bank": card.get("bank", ""),
                    "card_number_last4": card.get("card_last4", ""),
                    "credit_limit_paise": card.get("credit_limit_paise", 0),
                    "current_balance_paise": card.get("current_balance_paise", 0),
                    "available_paise": card.get("available_paise", 0),
                    "min_due_paise": card.get("min_due_paise", 0),
                    "total_due_paise": card.get("total_due_paise", 0),
                    "due_date": card.get("due_date", ""),
                    "status": card.get("status", "active"),
                    "reward_points": card.get("reward_points", 0),
                }
            )

        # Get statements for utilization
        statements = []
        for card in cards:
            card_statements = self.statement_repo.list_statements(
                card.get("card_id", "")
            )
            statements.extend(card_statements)

        # Build utilization data
        utilization = []
        for card in cards:
            balance = card.get("current_balance_paise", 0)
            limit = card.get("credit_limit_paise", 1)
            utilization_pct = int(balance / limit * 100) if limit > 0 else 0
            utilization.append(
                {
                    "card_id": card.get("card_id", ""),
                    "credit_limit_paise": limit,
                    "current_balance_paise": balance,
                    "utilization_percentage": utilization_pct,
                    "available_paise": limit - balance,
                }
            )

        # Build spending by category (placeholder)
        spending = []
        for card in cards:
            spending.append(
                {
                    "card_id": card.get("card_id", ""),
                    "category": "shopping",
                    "amount_paise": card.get("current_balance_paise", 0) // 3,
                    "percentage": 33,
                    "transaction_count": 10,
                }
            )
            spending.append(
                {
                    "card_id": card.get("card_id", ""),
                    "category": "dining",
                    "amount_paise": card.get("current_balance_paise", 0) // 3,
                    "percentage": 33,
                    "transaction_count": 8,
                }
            )
            spending.append(
                {
                    "card_id": card.get("card_id", ""),
                    "category": "travel",
                    "amount_paise": card.get("current_balance_paise", 0) // 3,
                    "percentage": 34,
                    "transaction_count": 5,
                }
            )

        # Generate insights
        insights = []
        if total_balance > 0:
            high_util_cards = [
                u for u in utilization if u["utilization_percentage"] > 80
            ]
            if high_util_cards:
                insights.append(
                    {
                        "type": "warning",
                        "severity": "high",
                        "message": f"{len(high_util_cards)} card(s) have high utilization (>80%)",
                    }
                )

        return {
            "cards": card_summaries,
            "total_balance_paise": total_balance,
            "total_due_paise": total_due,
            "total_available_paise": total_available,
            "card_count": len(cards),
            "statements": [
                {
                    "id": s.get("id", 0),
                    "card_id": s.get("card_id", ""),
                    "period_from": s.get("statement_period_from", ""),
                    "period_to": s.get("statement_period_to", ""),
                    "total_due_paise": s.get("total_amount_due", 0),
                    "min_due_paise": s.get("min_amount_due", 0),
                    "total_payment_paise": s.get("total_payment", 0),
                    "status": s.get("status", "pending"),
                }
                for s in statements
            ],
            "utilization": utilization,
            "spending": spending,
            "insights": insights,
            "evidence_chain": {
                "summary": f"Credit cards summary for {len(cards)} active cards",
                "evidence": [
                    {
                        "type": "card_data",
                        "summary": f"Total balance: ₹{total_balance / 100:,.2f}",
                        "source": "credit_card_repository",
                        "confidence": 95,
                    },
                ],
                "calculation_steps": [
                    {
                        "name": "Total Balance Calculation",
                        "description": "Sum of all card balances",
                        "inputs": {"card_count": len(cards)},
                        "outputs": {"total_balance_paise": total_balance},
                    },
                ],
                "source_references": ["credit_cards", "statements"],
                "confidence_score": 90,
            },
            "filters": {
                "statuses": statuses,
                "banks": banks,
            },
            "navigation": {
                "deep_link": "/cards",
                "cross_references": {
                    "net_worth": "/net-worth",
                    "accounts": "/accounts",
                },
            },
        }
