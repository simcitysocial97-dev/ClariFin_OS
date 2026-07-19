"""Loans Intelligence Workspace Service.

Returns aggregated loans data matching LoansViewModel format.
"""

from typing import Any

from src.repositories.loan_repository import LoanRepository
from src.services.base import BaseService


class LoansWorkspaceService(BaseService):
    """Service for loans workspace aggregation."""

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.loan_repo = LoanRepository(self.db_path)

    def get_loans_summary(
        self,
        loan_types: list[str] | None = None,
        lenders: list[str] | None = None,
        statuses: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get loans summary for the workspace.

        Returns aggregated data matching LoansViewModel format.
        """
        # Get all loans
        all_loans = self.loan_repo.list_loans()

        # Apply filters
        loans = all_loans
        if loan_types:
            loans = [loan for loan in loans if loan.get("loan_type") in loan_types]
        if lenders:
            loans = [loan for loan in loans if loan.get("lender") in lenders]
        if statuses:
            loans = [loan for loan in loans if loan.get("status") in statuses]

        # Calculate totals
        total_outstanding = sum(loan.get("outstanding_paise", 0) for loan in loans)
        total_emi = sum(loan.get("emi_paise", 0) for loan in loans)

        # Build loan summaries
        loan_summaries = []
        for loan in loans:
            loan_summaries.append({
                "id": loan.get("loan_id", 0),
                "name": loan.get("name", ""),
                "lender": loan.get("lender", ""),
                "loan_type": loan.get("loan_type", ""),
                "principal_paise": loan.get("principal_paise", 0),
                "outstanding_paise": loan.get("outstanding_paise", 0),
                "interest_rate": loan.get("interest_rate", 0),
                "tenure_months": loan.get("tenure_months", 0),
                "emi_paise": loan.get("emi_paise", 0),
                "disbursed_date": loan.get("disbursed_date", ""),
                "status": loan.get("status", "active"),
            })

        # Build amortization schedule (placeholder)
        amortization = []
        for loan in loans:
            amortization.append({
                "loan_id": loan.get("loan_id", 0),
                "schedule": [
                    {
                        "month": m,
                        "date": f"2025-{m:02d}-01",
                        "emi_paise": loan.get("emi_paise", 0),
                        "principal_paise": loan.get("emi_paise", 0) // 2,
                        "interest_paise": loan.get("emi_paise", 0) // 2,
                        "balance_paise": max(0, loan.get("outstanding_paise", 0) - m * (loan.get("emi_paise", 0) // 2)),
                    }
                    for m in range(1, min(13, loan.get("tenure_months", 0) + 1))
                ],
            })

        # Build payment progress
        payment_progress = []
        for loan in loans:
            principal = loan.get("principal_paise", 0)
            outstanding = loan.get("outstanding_paise", 0)
            progress = int((principal - outstanding) / principal * 100) if principal > 0 else 0
            payment_progress.append({
                "loan_id": loan.get("loan_id", 0),
                "progress_percentage": progress,
                "principal_paise": principal,
                "outstanding_paise": outstanding,
                "total_paid_paise": principal - outstanding,
            })

        # Build interest analysis
        interest_analysis = []
        for loan in loans:
            rate = loan.get("interest_rate", 0)
            interest_paise = int(loan.get("outstanding_paise", 0) * rate / 100)
            interest_analysis.append({
                "loan_id": loan.get("loan_id", 0),
                "rate": rate,
                "interest_paise": interest_paise,
                "category": "high" if rate > 12 else "medium" if rate > 8 else "low",
            })

        # Generate insights
        insights = []
        if total_outstanding > 0:
            high_interest = [ia for ia in interest_analysis if ia["category"] == "high"]
            if high_interest:
                insights.append({
                    "type": "warning",
                    "severity": "high",
                    "message": f"{len(high_interest)} loan(s) have high interest rates (>12%)",
                })

        return {
            "loans": loan_summaries,
            "total_outstanding_paise": total_outstanding,
            "total_emi_paise": total_emi,
            "loan_count": len(loans),
            "amortization": amortization,
            "payment_progress": payment_progress,
            "interest_analysis": interest_analysis,
            "insights": insights,
            "evidence_chain": {
                "summary": f"Loans summary for {len(loans)} active loans",
                "evidence": [
                    {
                        "type": "loan_data",
                        "summary": f"Total outstanding: ₹{total_outstanding / 100:,.2f}",
                        "source": "loan_repository",
                        "confidence": 95,
                    },
                ],
                "calculation_steps": [
                    {
                        "name": "Total Outstanding Calculation",
                        "description": "Sum of all loan outstanding balances",
                        "inputs": {"loan_count": len(loans)},
                        "outputs": {"total_outstanding_paise": total_outstanding},
                    },
                ],
                "source_references": ["loans"],
                "confidence_score": 90,
            },
            "filters": {
                "loan_types": loan_types,
                "lenders": lenders,
                "statuses": statuses,
            },
            "navigation": {
                "deep_link": "/loans",
                "cross_references": {
                    "net_worth": "/net-worth",
                    "accounts": "/accounts",
                },
            },
        }
