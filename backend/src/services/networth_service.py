"""Net worth business orchestration service."""

from typing import Any
from src.repositories import NetWorthRepository
from src.services.base import BaseService


class NetWorthService(BaseService):
    """Service for net worth calculation and orchestration."""

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.repo = NetWorthRepository(self.db_path)

    def calculate(self) -> dict[str, Any]:
        """
        Compute net worth from all financial data.

        Net Worth = Assets - Liabilities
        Assets = account balances + investment current values
        Liabilities = loan outstanding + card outstanding (latest statement)

        Returns:
            {
                net_worth_paise: int,
                assets: {total_paise, accounts_paise, investments_paise, account_count, investment_count},
                liabilities: {total_paise, loans_paise, cards_paise, loan_count, card_count},
                is_partial: bool,
                partial_reason: str | None
            }
        """
        data = self.repo.get_networth_data()
        accounts = data["accounts"]
        loans = data["loans"]
        investments = data["investments"]
        statements = data["statements"]

        # Assets
        account_balance_paise = sum(a["balance_paise"] for a in accounts)
        investment_value_paise = sum(i["current_value_paise"] for i in investments)
        total_assets_paise = account_balance_paise + investment_value_paise

        # Liabilities
        loan_outstanding_paise = sum(loan["outstanding_paise"] for loan in loans)

        # Card outstanding from latest statement per card
        card_outstanding_paise = 0
        seen_cards: set[str] = set()
        for stmt in sorted(
            statements,
            key=lambda s: str(s.get("statement_period_to") or s.get("imported_at") or ""),
            reverse=True,
        ):
            card_key = f"{stmt.get('bank', '')}_{stmt.get('card_last4', '')}"
            if card_key not in seen_cards:
                seen_cards.add(card_key)
                due = stmt.get("total_amount_due", 0) or 0
                card_outstanding_paise += int(round(due * 100))

        total_liabilities_paise = loan_outstanding_paise + card_outstanding_paise
        net_worth_paise = total_assets_paise - total_liabilities_paise

        return {
            "net_worth_paise": net_worth_paise,
            "assets": {
                "total_paise": total_assets_paise,
                "accounts_paise": account_balance_paise,
                "investments_paise": investment_value_paise,
                "account_count": len(accounts),
                "investment_count": len(investments),
            },
            "liabilities": {
                "total_paise": total_liabilities_paise,
                "loans_paise": loan_outstanding_paise,
                "cards_paise": card_outstanding_paise,
                "loan_count": len(loans),
                "card_count": len(seen_cards),
            },
            "is_partial": len(accounts) == 0 and len(investments) == 0,
            "partial_reason": (
                "Add accounts and investments for complete net worth"
                if len(accounts) == 0
                else None
            ),
        }
