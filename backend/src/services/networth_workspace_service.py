"""Net Worth Intelligence Workspace Service.

Returns aggregated net worth data matching NetWorthViewModel format.
"""

from typing import Any

from src.repositories.account_repository import AccountRepository
from src.repositories.credit_card_statement_repository import CreditCardStatementRepository
from src.repositories.investment_repository import InvestmentRepository
from src.repositories.loan_repository import LoanRepository
from src.services.base import BaseService


class NetWorthWorkspaceService(BaseService):
    """Service for net worth workspace aggregation."""

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.account_repo = AccountRepository(self.db_path)
        self.investment_repo = InvestmentRepository(self.db_path)
        self.loan_repo = LoanRepository(self.db_path)
        self.statement_repo = CreditCardStatementRepository(self.db_path)

    def get_networth_summary(
        self,
        date_range: dict[str, str | None] | None = None,
        account_types: list[str] | None = None,
        period: str = "1M",
    ) -> dict[str, Any]:
        """Get net worth summary for the workspace.

        Returns aggregated data matching NetWorthViewModel format.
        """
        # Get all accounts
        all_accounts = self.account_repo.list_accounts()

        # Apply account type filter
        accounts = all_accounts
        if account_types:
            accounts = [a for a in accounts if a.get("account_type") in account_types]

        # Get all investments
        all_investments = self.investment_repo.list_investments()
        investments = all_investments

        # Get all loans
        all_loans = self.loan_repo.list_loans()
        loans = all_loans

        # Get all statements for card balances
        all_statements = self.statement_repo.list_all_statements()

        # Calculate totals
        account_balance_paise = sum(a.get("balance_paise", 0) for a in accounts)
        investment_value_paise = sum(i.get("current_value_paise", 0) for i in investments)
        total_assets_paise = account_balance_paise + investment_value_paise

        loan_outstanding_paise = sum(loan.get("outstanding_paise", 0) for loan in loans)

        # Card outstanding from latest statement per card
        card_outstanding_paise = 0
        seen_cards: set[str] = set()
        for stmt in sorted(
            all_statements,
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

        # Build asset breakdown
        asset_breakdown = []
        for acc in accounts:
            balance = acc.get("balance_paise", 0)
            percentage = int(balance / total_assets_paise * 100) if total_assets_paise > 0 else 0
            asset_breakdown.append({
                "id": acc.get("account_id", ""),
                "name": acc.get("name", ""),
                "type": acc.get("account_type", ""),
                "balance_paise": balance,
                "percentage": percentage,
                "contribution_paise": balance,
            })

        for inv in investments:
            value = inv.get("current_value_paise", 0)
            percentage = int(value / total_assets_paise * 100) if total_assets_paise > 0 else 0
            asset_breakdown.append({
                "id": inv.get("investment_id", ""),
                "name": inv.get("name", ""),
                "type": inv.get("investment_type", ""),
                "balance_paise": value,
                "percentage": percentage,
                "contribution_paise": value,
            })

        # Build liability breakdown
        liability_breakdown = []
        for loan in loans:
            outstanding = loan.get("outstanding_paise", 0)
            percentage = int(outstanding / total_liabilities_paise * 100) if total_liabilities_paise > 0 else 0
            liability_breakdown.append({
                "id": loan.get("loan_id", ""),
                "name": loan.get("name", ""),
                "type": loan.get("loan_type", ""),
                "balance_paise": -outstanding,  # Negative for liabilities
                "percentage": percentage,
                "contribution_paise": -outstanding,
            })

        for stmt in all_statements:
            if stmt.get("bank") and stmt.get("card_last4"):
                card_key = f"{stmt.get('bank')}_{stmt.get('card_last4')}"
                if card_key in seen_cards:
                    due = stmt.get("total_amount_due", 0) or 0
                    due_paise = int(round(due * 100))
                    percentage = int(due_paise / total_liabilities_paise * 100) if total_liabilities_paise > 0 else 0
                    liability_breakdown.append({
                        "id": f"card_{card_key}",
                        "name": f"Credit Card {stmt.get('card_last4', '')}",
                        "type": "credit_card",
                        "balance_paise": -due_paise,
                        "percentage": percentage,
                        "contribution_paise": -due_paise,
                    })
                    seen_cards.discard(card_key)  # Only add once

        # Generate insights
        insights = []
        if net_worth_paise > 0:
            insights.append({
                "type": "positive",
                "severity": "medium",
                "message": f"Net worth is positive: ₹{net_worth_paise / 100:,.2f}",
            })

        if total_liabilities_paise > total_assets_paise:
            insights.append({
                "type": "warning",
                "severity": "high",
                "message": "Liabilities exceed assets. Consider debt reduction strategies.",
            })

        return {
            "total_net_worth_paise": net_worth_paise,
            "total_assets_paise": total_assets_paise,
            "total_liabilities_paise": total_liabilities_paise,
            "composition": {
                "total_assets_paise": total_assets_paise,
                "total_liabilities_paise": total_liabilities_paise,
                "asset_breakdown": asset_breakdown,
                "liability_breakdown": liability_breakdown,
            },
            "trend": {
                "direction": "up" if net_worth_paise > 0 else "down",
                "percentage_change": 0,
                "period": period,
            },
            "insights": insights,
            "evidence_chain": {
                "summary": f"Net worth calculated from {len(accounts)} accounts, {len(investments)} investments, {len(loans)} loans",
                "evidence": [
                    {
                        "type": "account_data",
                        "summary": f"Total accounts: {len(accounts)}",
                        "source": "account_repository",
                        "confidence": 95,
                    },
                    {
                        "type": "investment_data",
                        "summary": f"Total investments: {len(investments)}",
                        "source": "investment_repository",
                        "confidence": 95,
                    },
                    {
                        "type": "loan_data",
                        "summary": f"Total loans: {len(loans)}",
                        "source": "loan_repository",
                        "confidence": 95,
                    },
                ],
                "calculation_steps": [
                    {
                        "name": "Net Worth Calculation",
                        "description": "Net Worth = Assets - Liabilities",
                        "inputs": {
                            "account_count": len(accounts),
                            "investment_count": len(investments),
                            "loan_count": len(loans),
                        },
                        "outputs": {
                            "total_net_worth_paise": net_worth_paise,
                            "total_assets_paise": total_assets_paise,
                            "total_liabilities_paise": total_liabilities_paise,
                        },
                    },
                ],
                "source_references": ["accounts", "investments", "loans", "statements"],
                "confidence_score": 90,
            },
            "filters": {
                "date_range": date_range,
                "account_types": account_types,
                "period": period,
            },
            "navigation": {
                "deep_link": "/net-worth",
                "cross_references": {
                    "accounts": "/accounts",
                    "investments": "/investments",
                    "loans": "/loans",
                    "credit_cards": "/credit-cards",
                },
            },
        }
