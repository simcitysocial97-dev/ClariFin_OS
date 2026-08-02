"""Net worth business orchestration service."""

from src.core.dtos.net_worth_dto import (
    NetWorthBreakdownItemDTO,
    NetWorthCompositionDTO,
    NetWorthDTO,
)
from src.repositories import NetWorthRepository
from src.services.base import BaseService


class NetWorthService(BaseService):
    """Service for net worth calculation and orchestration."""

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.repo = NetWorthRepository(self.db_path)

    def calculate(self) -> NetWorthDTO:
        """
        Compute net worth from all financial data.

        Net Worth = Assets - Liabilities
        Assets = account balances + investment current values
        Liabilities = loan outstanding + card outstanding (latest statement)

        Returns:
            NetWorthDTO with complete breakdown
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
            key=lambda s: str(
                s.get("statement_period_to") or s.get("imported_at") or ""
            ),
            reverse=True,
        ):
            card_key = f"{stmt.get('bank', '')}_{stmt.get('card_last4', '')}"
            if card_key not in seen_cards:
                seen_cards.add(card_key)
                due = stmt.get("total_amount_due", 0) or 0
                card_outstanding_paise += int(round(due * 100))

        total_liabilities_paise = loan_outstanding_paise + card_outstanding_paise
        net_worth_paise = total_assets_paise - total_liabilities_paise

        # Build composition DTOs
        asset_breakdown = [
            NetWorthBreakdownItemDTO(
                id=str(a["id"]),
                name=a["name"],
                type="account",
                balance_paise=a["balance_paise"],
                percentage=(
                    (a["balance_paise"] / total_assets_paise * 100)
                    if total_assets_paise > 0
                    else 0
                ),
                contribution_paise=a["balance_paise"],
            )
            for a in accounts
        ] + [
            NetWorthBreakdownItemDTO(
                id=str(inv["id"]),
                name=inv["name"],
                type="investment",
                balance_paise=inv["current_value_paise"],
                percentage=(
                    (inv["current_value_paise"] / total_assets_paise * 100)
                    if total_assets_paise > 0
                    else 0
                ),
                contribution_paise=inv["current_value_paise"],
            )
            for inv in investments
        ]

        liability_breakdown = [
            NetWorthBreakdownItemDTO(
                id=str(loan["id"]),
                name=loan["name"],
                type="loan",
                balance_paise=-loan["outstanding_paise"],
                percentage=(
                    (loan["outstanding_paise"] / total_liabilities_paise * 100)
                    if total_liabilities_paise > 0
                    else 0
                ),
                contribution_paise=-loan["outstanding_paise"],
            )
            for loan in loans
        ]

        return NetWorthDTO(
            total_net_worth_paise=net_worth_paise,
            total_assets_paise=total_assets_paise,
            total_liabilities_paise=total_liabilities_paise,
            composition=NetWorthCompositionDTO(
                total_assets_paise=total_assets_paise,
                total_liabilities_paise=total_liabilities_paise,
                asset_breakdown=asset_breakdown,
                liability_breakdown=liability_breakdown,
            ),
            trend=None,
            insights=[],
            evidence_chain=None,
        )
