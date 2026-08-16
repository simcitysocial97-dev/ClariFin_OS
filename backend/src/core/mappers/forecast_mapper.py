"""Forecast Mapper

Transforms forecast domain objects into ForecastDTO instances.
This is the ONLY location where forecast API responses are constructed.
"""

from typing import Any

from src.core.dtos.forecast_dto import (
    CashflowProjectionDTO,
    ConfidenceIntervalDTO,
    ForecastDTO,
    ForecastInsightDTO,
    ForecastScenarioDTO,
    ForecastSummaryDTO,
    NetWorthProjectionDTO,
)


class ForecastMapper:
    """Mapper for forecast domain objects to DTOs."""

    @staticmethod
    def to_dto(forecast_data: dict[str, Any]) -> ForecastDTO:
        """Convert forecast data to ForecastDTO."""
        return ForecastDTO(
            summary=ForecastMapper._to_summary_dto(forecast_data.get("summary", {})),
            net_worth_projections=ForecastMapper._to_net_worth_projections(
                forecast_data.get("net_worth_projections", [])
            ),
            cashflow_projections=ForecastMapper._to_cashflow_projections(
                forecast_data.get("cashflow_projections", [])
            ),
            scenarios=ForecastMapper._to_scenarios(forecast_data.get("scenarios", [])),
            confidence_intervals=ForecastMapper._to_confidence_intervals(
                forecast_data.get("confidence_intervals", [])
            ),
            insights=ForecastMapper._to_insights(forecast_data.get("insights", [])),
            evidence_chain=forecast_data.get("evidence_chain"),
        )

    @staticmethod
    def _to_summary_dto(summary_data: dict[str, Any]) -> ForecastSummaryDTO:
        """Convert summary data to ForecastSummaryDTO."""
        return ForecastSummaryDTO(
            horizon_months=summary_data.get("horizon_months", 12),
            current_net_worth_paise=summary_data.get("current_net_worth_paise", 0),
            projected_net_worth_paise=summary_data.get("projected_net_worth_paise", 0),
            projected_growth_paise=summary_data.get("projected_growth_paise", 0),
            projected_growth_percentage=summary_data.get(
                "projected_growth_percentage", 0.0
            ),
        )

    @staticmethod
    def _to_net_worth_projections(
        projections: list[dict[str, Any]],
    ) -> list[NetWorthProjectionDTO]:
        """Convert net worth projections to NetWorthProjectionDTO list."""
        return [
            NetWorthProjectionDTO(
                date=proj.get("date", ""),
                projected_paise=proj.get("projected_paise", 0),
                lower_bound_paise=proj.get("lower_bound_paise", 0),
                upper_bound_paise=proj.get("upper_bound_paise", 0),
            )
            for proj in projections
        ]

    @staticmethod
    def _to_cashflow_projections(
        projections: list[dict[str, Any]],
    ) -> list[CashflowProjectionDTO]:
        """Convert cashflow projections to CashflowProjectionDTO list."""
        return [
            CashflowProjectionDTO(
                month=proj.get("month", ""),
                income_paise=proj.get("income_paise", 0),
                expenses_paise=proj.get("expenses_paise", 0),
                net_paise=proj.get("net_paise", 0),
            )
            for proj in projections
        ]

    @staticmethod
    def _to_scenarios(scenarios: list[dict[str, Any]]) -> list[ForecastScenarioDTO]:
        """Convert scenarios to ForecastScenarioDTO list."""
        return [
            ForecastScenarioDTO(
                name=scenario.get("name", ""),
                description=scenario.get("description", ""),
                probability_bps=scenario.get("probability_bps", 0),
                net_worth_projections=ForecastMapper._to_net_worth_projections(
                    scenario.get("net_worth_projections", [])
                ),
                cashflow_projections=ForecastMapper._to_cashflow_projections(
                    scenario.get("cashflow_projections", [])
                ),
            )
            for scenario in scenarios
        ]

    @staticmethod
    def _to_confidence_intervals(
        intervals: list[dict[str, Any]],
    ) -> list[ConfidenceIntervalDTO]:
        """Convert confidence intervals to ConfidenceIntervalDTO list."""
        return [
            ConfidenceIntervalDTO(
                level=interval.get("level", 95),
                lower_paise=interval.get("lower_paise", 0),
                upper_paise=interval.get("upper_paise", 0),
            )
            for interval in intervals
        ]

    @staticmethod
    def _to_insights(insights: list[dict[str, Any]]) -> list[ForecastInsightDTO]:
        """Convert insights to ForecastInsightDTO list."""
        return [
            ForecastInsightDTO(
                type=insight.get("type", "info"),
                severity=insight.get("severity", "medium"),
                message=insight.get("message", ""),
                action_url=insight.get("action_url"),
            )
            for insight in insights
        ]
