"""Cashflow Service - Orchestration layer for monthly cashflow analysis.

Coordinates CashflowRepository and FinancialEventRepository to provide
enriched cashflow data with financial events overlay.
"""

from datetime import datetime
from typing import Any

from src.common import DB_PATH
from src.engines.cashflow_engine import compute_monthly_cashflow
from src.models.explanation import (
    CalculationStep,
    CashflowMonth,
    CashflowResponse,
    Confidence,
    Evidence,
    Explanation,
    SourceReference,
)
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

    def calculate_with_explanation(
        self,
        months: int = 6,
        member: str | None = None,
    ) -> CashflowResponse:
        """
        Compute household cashflow with full explainability.

        Returns:
            CashflowResponse with explanation containing:
            - Evidence for each income and expense transaction
            - Source references for each transaction
            - Calculation steps: sum-income, sum-expense, net-cashflow
            - Confidence based on data availability
        """
        # Fetch all monthly cashflow data
        all_months = self.cashflow_repo.get_monthly_cashflow(months=months, member=member)

        # Build evidence and sources for income
        income_evidence: list[Evidence] = []
        income_sources: list[SourceReference] = []
        months_list: list[CashflowMonth] = []

        for month_data in all_months:
            month_key = month_data.get("month_key", "")
            income = int(month_data.get("income_paise", 0) or 0)
            expense = int(month_data.get("expense_paise", 0) or 0)
            txn_count = int(month_data.get("transaction_count", 0) or 0)

            # Build month data
            months_list.append(CashflowMonth(
                month_key=month_key,
                month_label=month_key,
                income_paise=income,
                expense_paise=expense,
                net_paise=income - expense,
                transaction_count=txn_count,
            ))

            if income > 0:
                income_evidence.append(Evidence(
                    id=f"income-{month_key}",
                    type="data",
                    description=f"Income for {month_key}",
                    value=income,
                    sourceId=f"month-{month_key}",
                ))
                income_sources.append(SourceReference(
                    type="transaction",
                    id=f"month-{month_key}",
                    name=f"Income for {month_key}",
                    date=month_key,
                ))

            if expense > 0:
                income_evidence.append(Evidence(
                    id=f"expense-{month_key}",
                    type="data",
                    description=f"Expense for {month_key}",
                    value=expense,
                    sourceId=f"month-{month_key}",
                ))
                income_sources.append(SourceReference(
                    type="transaction",
                    id=f"month-{month_key}",
                    name=f"Expense for {month_key}",
                    date=month_key,
                ))

        # Calculate totals - filter by type and sum integer values
        total_income = sum(
            int(e.value) for e in income_evidence
            if isinstance(e.value, int) and "income" in e.id
        )
        total_expense = sum(
            int(e.value) for e in income_evidence
            if isinstance(e.value, int) and "expense" in e.id
        )
        total_net = total_income - total_expense

        # Calculate confidence
        confidence_bps = 10000
        confidence_reasons: list[str] = []

        if len(income_evidence) == 0:
            confidence_bps -= 2000
            confidence_reasons.append("No transaction data available")

        # Build calculation steps
        calculation_steps: list[CalculationStep] = [
            CalculationStep(
                stepId="sum-income",
                description="Sum all income values",
                operation="ADD",
                inputIds=[e.id for e in income_evidence if "income" in e.id],
                outputId="total-income",
                order=1,
            ),
            CalculationStep(
                stepId="sum-expense",
                description="Sum all expense values",
                operation="ADD",
                inputIds=[e.id for e in income_evidence if "expense" in e.id],
                outputId="total-expense",
                order=2,
            ),
            CalculationStep(
                stepId="net-cashflow",
                description="Net cashflow = income - expense",
                operation="SUBTRACT",
                inputIds=["total-income", "total-expense"],
                outputId="total-net",
                order=3,
            ),
        ]

        # Build explanation
        explanation = Explanation(
            metric="household_cashflow",
            value=total_net,
            confidence=Confidence(
                value=confidence_bps,
                reason=", ".join(confidence_reasons) if confidence_reasons else "Complete data available",
            ),
            evidence=income_evidence,
            sources=income_sources,
            calculationSteps=calculation_steps,
        )

        return CashflowResponse(
            months=months_list,
            period_months=len(months_list),
            total_income_paise=total_income,
            total_expense_paise=total_expense,
            total_net_paise=total_net,
            is_partial=len(income_evidence) == 0,
            partial_reason="No transaction data available" if len(income_evidence) == 0 else None,
            last_updated=datetime.now().isoformat(),
            explanation=explanation,
        )