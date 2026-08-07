"""Reconciliation Mapper

Transforms reconciliation domain objects into ReconciliationDTO instances.
This is the ONLY location where reconciliation API responses are constructed.
"""

from typing import Any

from src.core.dtos.reconciliation_dto import (
    AuditTrailEntryDTO,
    DiscrepancyDTO,
    ReconciliationDTO,
    ReconciliationInsightDTO,
    ReconciliationSummaryDTO,
    StatusOverviewDTO,
)


class ReconciliationMapper:
    """Mapper for reconciliation domain objects to DTOs."""

    @staticmethod
    def to_dto(reconciliation_data: dict[str, Any]) -> ReconciliationDTO:
        """Convert reconciliation data to ReconciliationDTO."""
        return ReconciliationDTO(
            statements=ReconciliationMapper._to_statement_summaries(
                reconciliation_data.get("statements", [])
            ),
            discrepancies=ReconciliationMapper._to_discrepancies(
                reconciliation_data.get("discrepancies", [])
            ),
            status_overview=ReconciliationMapper._to_status_overview_dto(
                reconciliation_data.get("status_overview", {})
            ),
            audit_trail=ReconciliationMapper._to_audit_trail(
                reconciliation_data.get("audit_trail", [])
            ),
            insights=ReconciliationMapper._to_insights(
                reconciliation_data.get("insights", [])
            ),
            evidence_chain=reconciliation_data.get("evidence_chain"),
        )

    @staticmethod
    def _to_statement_summaries(
        statements: list[dict[str, Any]],
    ) -> list[ReconciliationSummaryDTO]:
        """Convert statement data to ReconciliationSummaryDTO list."""
        return [
            ReconciliationSummaryDTO(
                statement_id=stmt.get("statement_id", 0),
                bank=stmt.get("bank", "Unknown"),
                period_from=stmt.get("period_from", ""),
                period_to=stmt.get("period_to", ""),
                total_debit_paise=stmt.get("total_debit_paise", 0),
                total_credit_paise=stmt.get("total_credit_paise", 0),
                transaction_count=stmt.get("transaction_count", 0),
                reconciled_count=stmt.get("reconciled_count", 0),
                status=stmt.get("status", "pending"),
            )
            for stmt in statements
        ]

    @staticmethod
    def _to_discrepancies(discrepancies: list[dict[str, Any]]) -> list[DiscrepancyDTO]:
        """Convert discrepancies to DiscrepancyDTO list."""
        return [
            DiscrepancyDTO(
                id=disc.get("id", 0),
                transaction_id=disc.get("transaction_id", 0),
                statement_id=disc.get("statement_id", 0),
                type=disc.get("type", "unknown"),
                expected_paise=disc.get("expected_paise", 0),
                actual_paise=disc.get("actual_paise", 0),
                difference_paise=disc.get("difference_paise", 0),
                status=disc.get("status", "pending"),
                notes=disc.get("notes"),
            )
            for disc in discrepancies
        ]

    @staticmethod
    def _to_status_overview_dto(overview_data: dict[str, Any]) -> StatusOverviewDTO:
        """Convert status overview data to StatusOverviewDTO."""
        return StatusOverviewDTO(
            total_transactions=overview_data.get("total_transactions", 0),
            reconciled=overview_data.get("reconciled", 0),
            pending=overview_data.get("pending", 0),
            discrepancies=overview_data.get("discrepancies", 0),
            match_rate=overview_data.get("match_rate", 0.0),
        )

    @staticmethod
    def _to_audit_trail(entries: list[dict[str, Any]]) -> list[AuditTrailEntryDTO]:
        """Convert audit trail entries to AuditTrailEntryDTO list."""
        return [
            AuditTrailEntryDTO(
                id=entry.get("id", 0),
                transaction_id=entry.get("transaction_id", 0),
                action=entry.get("action", ""),
                user=entry.get("user", "system"),
                timestamp=entry.get("timestamp", ""),
                notes=entry.get("notes"),
            )
            for entry in entries
        ]

    @staticmethod
    def _to_insights(insights: list[dict[str, Any]]) -> list[ReconciliationInsightDTO]:
        """Convert insights to ReconciliationInsightDTO list."""
        return [
            ReconciliationInsightDTO(
                type=insight.get("type", "info"),
                severity=insight.get("severity", "medium"),
                message=insight.get("message", ""),
                action_url=insight.get("action_url"),
            )
            for insight in insights
        ]
