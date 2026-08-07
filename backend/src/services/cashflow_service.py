"""Cashflow business orchestration service."""

from typing import Literal

from src.core.dtos.cashflow_dto import (
    CashflowCategoryDTO,
    CashflowCategoryResponse,
    CashflowMonthlyDTO,
    CashflowMonthlyResponse,
    CashflowSummaryDTO,
    CashflowTransactionDTO,
    CashflowTransactionResponse,
    CashflowTrendDTO,
)
from src.repositories import CashflowRepository, TransactionRepository
from src.services.base import BaseService


class CashflowService(BaseService):
    """Service for cashflow calculation and orchestration."""

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.cashflow_repo = CashflowRepository(self.db_path)
        self.transaction_repo = TransactionRepository(self.db_path)

    def calculate_summary(self) -> CashflowSummaryDTO:
        """
        Compute cashflow summary from all financial data.

        Cashflow = Total Income - Total Expenses
        All monetary values in paise (integer).

        Returns:
            CashflowSummaryDTO with total income, expenses, and net cashflow.
        """
        # Get monthly cashflow data
        monthly_data = self.cashflow_repo.get_monthly_cashflow(months=12)

        # Calculate totals
        total_income = 0
        total_expenses = 0
        transaction_count = 0

        for row in monthly_data:
            total_income += int(row.get("income_paise", 0) or 0)
            total_expenses += int(row.get("expense_paise", 0) or 0)
            transaction_count += int(row.get("transaction_count", 0) or 0)

        # Calculate trend (compare last 2 months)
        trend: CashflowTrendDTO | None = None
        if len(monthly_data) >= 2:
            last_month = monthly_data[-1]
            prev_month = monthly_data[-2]
            last_net = int(last_month.get("income_paise", 0) or 0) - int(
                last_month.get("expense_paise", 0) or 0
            )
            prev_net = int(prev_month.get("income_paise", 0) or 0) - int(
                prev_month.get("expense_paise", 0) or 0
            )

            if prev_net != 0:
                percentage_change = ((last_net - prev_net) / abs(prev_net)) * 100
                direction: Literal["up", "down", "flat"] = (
                    "up"
                    if percentage_change > 0
                    else "down" if percentage_change < 0 else "flat"
                )
            else:
                percentage_change = 0.0
                direction = "flat"

            trend = CashflowTrendDTO(
                direction=direction,
                percentage_change=percentage_change,
                period="1M",
                volatility_score=0.0,
            )

        return CashflowSummaryDTO(
            total_income_paise=total_income,
            total_expenses_paise=total_expenses,
            net_cashflow_paise=total_income - total_expenses,
            transaction_count=transaction_count,
            trend=trend,
            insights=[],
            evidence_chain=None,
        )

    def get_monthly(self, months: int = 6) -> CashflowMonthlyResponse:
        """
        Get monthly cashflow breakdown.

        Args:
            months: Number of months to return (default 6)

        Returns:
            CashflowMonthlyResponse with monthly data.
        """
        rows = self.cashflow_repo.get_monthly_cashflow(months=months)

        monthly_data: list[CashflowMonthlyDTO] = []
        for row in rows:
            month_key = row.get("month_key", "")
            if not month_key:
                continue

            income = int(row.get("income_paise", 0) or 0)
            expense = int(row.get("expense_paise", 0) or 0)

            monthly_data.append(
                CashflowMonthlyDTO(
                    month=month_key,
                    income_paise=income,
                    expenses_paise=expense,
                    net_paise=income - expense,
                    transaction_count=int(row.get("transaction_count", 0) or 0),
                )
            )

        return CashflowMonthlyResponse(
            months=monthly_data, total_count=len(monthly_data)
        )

    def get_categories(self) -> CashflowCategoryResponse:
        """
        Get category breakdown for cashflow.

        Returns:
            CashflowCategoryResponse with category data.
        """
        # Get all transactions to calculate category breakdown
        transactions = self.transaction_repo.get_all_transactions()

        # Group by category
        category_totals: dict[str, int] = {}
        for txn in transactions:
            category = txn.get("category", "uncategorized") or "uncategorized"
            amount = int(txn.get("amount_paise", 0) or 0)
            category_totals[category] = category_totals.get(category, 0) + amount

        # Calculate total for percentage
        total = sum(category_totals.values())

        # Build response
        categories: list[CashflowCategoryDTO] = []
        for category_id, amount in sorted(
            category_totals.items(), key=lambda x: x[1], reverse=True
        ):
            categories.append(
                CashflowCategoryDTO(
                    category_id=category_id,
                    category_name=category_id.replace("_", " ").title(),
                    amount_paise=amount,
                    percentage=(amount / total * 100) if total > 0 else 0.0,
                    transaction_count=sum(
                        1
                        for t in transactions
                        if (t.get("category") or "uncategorized") == category_id
                    ),
                )
            )

        return CashflowCategoryResponse(
            categories=categories, total_count=len(categories)
        )

    def get_transactions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> CashflowTransactionResponse:
        """
        Get transactions for cashflow view.

        Args:
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip

        Returns:
            CashflowTransactionResponse with transaction data.
        """
        transactions = self.transaction_repo.get_all_transactions()

        # Apply pagination
        paginated = transactions[offset : offset + limit]

        txn_data: list[CashflowTransactionDTO] = []
        for txn in paginated:
            txn_data.append(
                CashflowTransactionDTO(
                    id=str(txn.get("id", "")),
                    date=txn.get("date_iso", "") or "",
                    description=txn.get("description", "") or "",
                    amount_paise=int(txn.get("amount_paise", 0) or 0),
                    category=txn.get("category", "uncategorized") or "uncategorized",
                    merchant=txn.get("merchant"),
                )
            )

        return CashflowTransactionResponse(
            transactions=txn_data,
            total=len(transactions),
            limit=limit,
            offset=offset,
        )
