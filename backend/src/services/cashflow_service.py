"""Cashflow Service - Orchestration layer for monthly cashflow analysis.

Coordinates CashflowRepository and FinancialEventRepository to provide
enriched cashflow data with financial events overlay.
"""

from typing import Any

from src.common import DB_PATH
from src.engines.cashflow_engine import compute_monthly_cashflow
from src.repositories import CashflowRepository
from src.repositories.financial_event_repository import FinancialEventRepository


class CashflowService:
    """
    Orchestrates cashflow analysis combining raw transaction aggregates
    with financial events (credit conversions, EMI payments, etc.).

    Does NOT contain SQL queries - only coordinates repositories and engine.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self.cashflow_repo = CashflowRepository(db_path)
        self.event_repo = FinancialEventRepository(db_path)

    def get_monthly_analysis(
        self,
        month_bucket: str,
        scope: str = "household",
        owner_id: str = "self",
    ) -> dict[str, Any]:
        """
        Get enriched monthly cashflow analysis.

        Args:
            month_bucket: Month in YYYY-MM format
            scope: "household" or "individual"
            owner_id: Owner filter (default "self")

        Returns:
            Dict with cashflow analysis including:
            - cash_surplus, true_savings, liability_adjusted_savings
            - net_worth_impact, month_classification
            - credit_dependency_ratio, effective_liquidity_cost_annualized
        """
        # Fetch plain cashflow aggregates for the month
        # We need to convert month_bucket to filter transactions
        cash_summary = self._get_month_cashflow(month_bucket, owner_id)

        # Fetch financial events for the month
        events = self.event_repo.get_events_for_month(
            month_bucket=month_bucket,
            household_id="primary",
            owner_id=owner_id if scope == "individual" else None,
        )

        # Compute enriched analysis via pure engine
        return compute_monthly_cashflow(
            cash_summary=cash_summary,
            financial_events=events,
            scope=scope,
            owner_id=owner_id,
        )

    def _get_month_cashflow(
        self,
        month_bucket: str,
        member: str | None,
    ) -> dict[str, Any]:
        """
        Get cashflow aggregates for a single month.

        Args:
            month_bucket: Month in YYYY-MM format
            member: Member filter (optional)

        Returns:
            Dict with income_paise, expense_paise, net_paise for the month.
        """
        # Get all monthly data and filter to the requested month
        all_months = self.cashflow_repo.get_monthly_cashflow(months=24, member=member)

        for month_data in all_months:
            if month_data.get("month_key") == month_bucket:
                return {
                    "income_paise": month_data.get("income_paise", 0) or 0,
                    "expense_paise": month_data.get("expense_paise", 0) or 0,
                    "net_paise": (month_data.get("income_paise", 0) or 0) - (month_data.get("expense_paise", 0) or 0),
                }

        # No data for this month - return zeros
        return {
            "income_paise": 0,
            "expense_paise": 0,
            "net_paise": 0,
        }
