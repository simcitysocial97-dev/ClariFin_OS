"""Reconciliation Intelligence Workspace Service.

Returns aggregated reconciliation data matching ReconciliationViewModel format.
"""

from typing import Any

from src.repositories.reconciliation_repository import ReconciliationRepository
from src.services.base import BaseService


class ReconciliationWorkspaceService(BaseService):
    """Service for reconciliation workspace aggregation."""

    def __init__(self, db_path: str | None = None) -> None:
        super().__init__(db_path)
        self.recon_repo = ReconciliationRepository(self.db_path)

    def get_reconciliation_summary(
        self,
        status: list[str] | None = None,
        banks: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get reconciliation summary for the workspace.

        Returns aggregated data matching ReconciliationViewModel format.
        """
        # Get all statements
        all_statements = self.recon_repo.list_statements()

        # Apply filters
        statements = all_statements
        if status:
            statements = [s for s in statements if s.get("status") in status]
        if banks:
            statements = [s for s in statements if s.get("bank") in banks]

        # Calculate totals
        total_debit = sum(s.get("total_debit_paise", 0) for s in statements)
        total_credit = sum(s.get("total_credit_paise", 0) for s in statements)
        total_transactions = sum(s.get("transaction_count", 0) for s in statements)
        total_reconciled = sum(s.get("reconciled_count", 0) for s in statements)

        # Build statement summaries
        statement_summaries = []
        for stmt in statements:
            statement_summaries.append(
                {
                    "statement_id": stmt.get("id", 0),
                    "bank": stmt.get("bank", ""),
                    "period_from": stmt.get("period_from", ""),
                    "period_to": stmt.get("period_to", ""),
                    "total_debit_paise": stmt.get("total_debit_paise", 0),
                    "total_credit_paise": stmt.get("total_credit_paise", 0),
                    "transaction_count": stmt.get("transaction_count", 0),
                    "reconciled_count": stmt.get("reconciled_count", 0),
                    "status": stmt.get("status", "pending"),
                }
            )

        # Build status overview
        status_overview = {
            "total_debit_paise": total_debit,
            "total_credit_paise": total_credit,
            "total_transactions": total_transactions,
            "reconciled": total_reconciled,
            "pending": total_transactions - total_reconciled,
            "discrepancies": 0,
            "match_rate": (
                int(total_reconciled / total_transactions * 100)
                if total_transactions > 0
                else 0
            ),
        }

        # Build discrepancies (placeholder)
        discrepancies: list[dict[str, Any]] = []

        # Build audit trail (placeholder)
        audit_trail: list[dict[str, Any]] = []

        # Generate insights
        insights = []
        if status_overview["match_rate"] < 80:
            insights.append(
                {
                    "type": "warning",
                    "severity": "high",
                    "message": f"Match rate is {status_overview['match_rate']}%. Consider reviewing pending reconciliations.",
                }
            )

        return {
            "statements": statement_summaries,
            "discrepancies": discrepancies,
            "status_overview": status_overview,
            "audit_trail": audit_trail,
            "insights": insights,
            "evidence_chain": {
                "summary": f"Reconciliation summary for {len(statements)} statements",
                "evidence": [
                    {
                        "type": "statement_data",
                        "summary": f"Total transactions: {total_transactions}",
                        "source": "reconciliation_repository",
                        "confidence": 95,
                    },
                ],
                "calculation_steps": [
                    {
                        "name": "Match Rate Calculation",
                        "description": "Percentage of reconciled transactions",
                        "inputs": {
                            "total_transactions": total_transactions,
                            "reconciled": total_reconciled,
                        },
                        "outputs": {"match_rate": status_overview["match_rate"]},
                    },
                ],
                "source_references": ["statements"],
                "confidence_score": 90,
            },
            "filters": {
                "status": status,
                "banks": banks,
            },
            "navigation": {
                "deep_link": "/reconciliation",
                "cross_references": {
                    "accounts": "/accounts",
                    "transactions": "/transactions",
                },
            },
        }
