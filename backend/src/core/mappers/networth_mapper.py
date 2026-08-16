"""Net Worth Mapper

Transforms net worth domain objects into NetWorthDTO instances.
This is the ONLY location where net worth API responses are constructed.
"""

from typing import Any

from src.core.dtos.net_worth_dto import (
    NetWorthBreakdownItemDTO,
    NetWorthCompositionDTO,
    NetWorthDTO,
    NetWorthHistoricalSnapshotDTO,
    NetWorthInsightDTO,
    NetWorthTrendDTO,
)


class NetWorthMapper:
    """Mapper for net worth domain objects to DTOs."""

    @staticmethod
    def to_dto(net_worth_data: dict[str, Any]) -> NetWorthDTO:
        """Convert net worth data to NetWorthDTO."""
        return NetWorthDTO(
            total_net_worth_paise=net_worth_data.get("total_net_worth_paise", 0),
            total_assets_paise=net_worth_data.get("total_assets_paise", 0),
            total_liabilities_paise=net_worth_data.get("total_liabilities_paise", 0),
            composition=NetWorthMapper._to_composition_dto(
                net_worth_data.get("composition", {})
            ),
            trend=NetWorthMapper._to_trend_dto(net_worth_data.get("trend")),
            insights=NetWorthMapper._to_insights(net_worth_data.get("insights", [])),
            evidence_chain=net_worth_data.get("evidence_chain"),
        )

    @staticmethod
    def _to_composition_dto(composition_data: dict[str, Any]) -> NetWorthCompositionDTO:
        """Convert composition data to NetWorthCompositionDTO."""
        return NetWorthCompositionDTO(
            total_assets_paise=composition_data.get("total_assets_paise", 0),
            total_liabilities_paise=composition_data.get("total_liabilities_paise", 0),
            asset_breakdown=NetWorthMapper._to_breakdown_items(
                composition_data.get("asset_breakdown", [])
            ),
            liability_breakdown=NetWorthMapper._to_breakdown_items(
                composition_data.get("liability_breakdown", [])
            ),
        )

    @staticmethod
    def _to_breakdown_items(
        items: list[dict[str, Any]],
    ) -> list[NetWorthBreakdownItemDTO]:
        """Convert breakdown items to NetWorthBreakdownItemDTO list."""
        return [
            NetWorthBreakdownItemDTO(
                id=item.get("id", ""),
                name=item.get("name", "Unknown"),
                type=item.get("type", "other"),
                balance_paise=item.get("balance_paise", 0),
                percentage=item.get("percentage", 0.0),
                contribution_paise=item.get("contribution_paise", 0),
            )
            for item in items
        ]

    @staticmethod
    def _to_trend_dto(trend_data: dict[str, Any] | None) -> NetWorthTrendDTO | None:
        """Convert trend data to NetWorthTrendDTO."""
        if not trend_data:
            return None
        return NetWorthTrendDTO(
            direction=trend_data.get("direction", "flat"),
            percentage_change=trend_data.get("percentage_change", 0.0),
            period=trend_data.get("period", "1M"),
        )

    @staticmethod
    def _to_insights(insights: list[dict[str, Any]]) -> list[NetWorthInsightDTO]:
        """Convert insights to NetWorthInsightDTO list."""
        return [
            NetWorthInsightDTO(
                type=insight.get("type", "info"),
                severity=insight.get("severity", "medium"),
                message=insight.get("message", ""),
                action_url=insight.get("action_url"),
            )
            for insight in insights
        ]

    @staticmethod
    def to_historical_snapshot_dto(
        snapshot_data: dict[str, Any],
    ) -> NetWorthHistoricalSnapshotDTO:
        """Convert historical snapshot data to NetWorthHistoricalSnapshotDTO."""
        return NetWorthHistoricalSnapshotDTO(
            date=snapshot_data.get("date", ""),
            net_worth_paise=snapshot_data.get("net_worth_paise", 0),
            assets_paise=snapshot_data.get("assets_paise", 0),
            liabilities_paise=snapshot_data.get("liabilities_paise", 0),
        )
