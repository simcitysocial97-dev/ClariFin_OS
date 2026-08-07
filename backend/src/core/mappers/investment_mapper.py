"""Investment Mapper

Transforms investment domain objects into InvestmentDTO instances.
This is the ONLY location where investment API responses are constructed.
"""

from typing import Any

from src.core.dtos.investments_dto import (
    AssetAllocationDTO,
    HoldingDTO,
    InvestmentInsightDTO,
    InvestmentsDTO,
    InvestmentSummaryDTO,
    PerformanceDTO,
)


class InvestmentMapper:
    """Mapper for investment domain objects to DTOs."""

    @staticmethod
    def to_dto(investments_data: dict[str, Any]) -> InvestmentsDTO:
        """Convert investments data to InvestmentsDTO."""
        return InvestmentsDTO(
            investments=InvestmentMapper._to_investment_summaries(
                investments_data.get("investments", [])
            ),
            total_value_paise=investments_data.get("total_value_paise", 0),
            total_invested_paise=investments_data.get("total_invested_paise", 0),
            total_returns_paise=investments_data.get("total_returns_paise", 0),
            investment_count=investments_data.get("investment_count", 0),
            insights=InvestmentMapper._to_insights(
                investments_data.get("insights", [])
            ),
            evidence_chain=investments_data.get("evidence_chain"),
        )

    @staticmethod
    def _to_investment_summaries(
        investments: list[dict[str, Any]],
    ) -> list[InvestmentSummaryDTO]:
        """Convert investment data to InvestmentSummaryDTO list."""
        return [
            InvestmentSummaryDTO(
                id=inv.get("id", ""),
                name=inv.get("name", "Unknown"),
                type=inv.get("type", "other"),
                institution=inv.get("institution", ""),
                current_value_paise=inv.get("current_value_paise", 0),
                invested_paise=inv.get("invested_paise", 0),
                returns_paise=inv.get("returns_paise", 0),
                returns_percentage=inv.get("returns_percentage", 0.0),
                returns_ytd_bps=inv.get("returns_ytd_bps", 0),
                status=inv.get("status", "active"),
            )
            for inv in investments
        ]

    @staticmethod
    def _to_insights(insights: list[dict[str, Any]]) -> list[InvestmentInsightDTO]:
        """Convert insights to InvestmentInsightDTO list."""
        return [
            InvestmentInsightDTO(
                type=insight.get("type", "info"),
                severity=insight.get("severity", "medium"),
                message=insight.get("message", ""),
                action_url=insight.get("action_url"),
            )
            for insight in insights
        ]

    @staticmethod
    def to_performance_dto(performance_data: dict[str, Any]) -> PerformanceDTO:
        """Convert performance data to PerformanceDTO."""
        return PerformanceDTO(
            date=performance_data.get("date", ""),
            value_paise=performance_data.get("value_paise", 0),
            returns_bps=performance_data.get("returns_bps", 0),
            day_change_bps=performance_data.get("day_change_bps", 0),
        )

    @staticmethod
    def to_allocation_dto(allocation_data: dict[str, Any]) -> AssetAllocationDTO:
        """Convert allocation data to AssetAllocationDTO."""
        return AssetAllocationDTO(
            type=allocation_data.get("type", "other"),
            value_paise=allocation_data.get("value_paise", 0),
            percentage=allocation_data.get("percentage", 0.0),
            count=allocation_data.get("count", 0),
        )

    @staticmethod
    def to_holding_dto(holding_data: dict[str, Any]) -> HoldingDTO:
        """Convert holding data to HoldingDTO."""
        return HoldingDTO(
            id=holding_data.get("id", ""),
            name=holding_data.get("name", "Unknown"),
            type=holding_data.get("type", "other"),
            symbol=holding_data.get("symbol"),
            quantity=holding_data.get("quantity", 0.0),
            purchase_price_paise=holding_data.get("purchase_price_paise", 0),
            current_price_paise=holding_data.get("current_price_paise", 0),
            current_value_paise=holding_data.get("current_value_paise", 0),
            invested_paise=holding_data.get("invested_paise", 0),
            returns_paise=holding_data.get("returns_paise", 0),
            returns_percentage=holding_data.get("returns_percentage", 0.0),
            last_updated=holding_data.get("last_updated", ""),
        )
