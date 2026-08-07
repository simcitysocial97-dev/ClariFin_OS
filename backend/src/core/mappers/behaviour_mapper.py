"""Behaviour Mapper

Transforms behaviour domain objects into BehaviourDTO instances.
This is the ONLY location where behaviour API responses are constructed.
"""

from typing import Any

from src.core.dtos.behaviour_dto import (
    BehaviourDTO,
    BehaviourInsightDTO,
    BehaviourScoreDTO,
    DebtHealthDTO,
    SavingsRateDTO,
    SpendingPatternDTO,
    WellnessRadarDTO,
)


class BehaviourMapper:
    """Mapper for behaviour domain objects to DTOs."""

    @staticmethod
    def to_dto(behaviour_data: dict[str, Any]) -> BehaviourDTO:
        """Convert behaviour data to BehaviourDTO."""
        return BehaviourDTO(
            wellness_score=BehaviourMapper._to_score_dto(
                behaviour_data.get("wellness_score", {})
            ),
            spending_patterns=BehaviourMapper._to_spending_patterns(
                behaviour_data.get("spending_patterns", [])
            ),
            savings_rate=BehaviourMapper._to_savings_rate_dto(
                behaviour_data.get("savings_rate")
            ),
            debt_health=BehaviourMapper._to_debt_health_dto(
                behaviour_data.get("debt_health")
            ),
            wellness_radar=BehaviourMapper._to_wellness_radar(
                behaviour_data.get("wellness_radar", [])
            ),
            insights=BehaviourMapper._to_insights(behaviour_data.get("insights", [])),
            evidence_chain=behaviour_data.get("evidence_chain"),
        )

    @staticmethod
    def _to_score_dto(score_data: dict[str, Any]) -> BehaviourScoreDTO:
        """Convert score data to BehaviourScoreDTO."""
        if not score_data:
            return BehaviourScoreDTO(score=0, label="Unknown", factors=[])
        return BehaviourScoreDTO(
            score=score_data.get("score", 0),
            label=score_data.get("label", "Unknown"),
            factors=score_data.get("factors", []),
        )

    @staticmethod
    def _to_spending_patterns(
        patterns: list[dict[str, Any]],
    ) -> list[SpendingPatternDTO]:
        """Convert spending patterns to SpendingPatternDTO list."""
        return [
            SpendingPatternDTO(
                category=pattern.get("category", "Unknown"),
                amount_paise=pattern.get("amount_paise", 0),
                percentage=pattern.get("percentage", 0.0),
                trend=pattern.get("trend", "stable"),
                month_over_month_change=pattern.get("month_over_month_change", 0.0),
            )
            for pattern in patterns
        ]

    @staticmethod
    def _to_savings_rate_dto(
        savings_data: dict[str, Any] | None,
    ) -> SavingsRateDTO | None:
        """Convert savings rate data to SavingsRateDTO."""
        if not savings_data:
            return None
        return SavingsRateDTO(
            savings_rate_bps=savings_data.get("savings_rate_bps", 0),
            income_paise=savings_data.get("income_paise", 0),
            savings_paise=savings_data.get("savings_paise", 0),
            period=savings_data.get("period", "1M"),
        )

    @staticmethod
    def _to_debt_health_dto(debt_data: dict[str, Any] | None) -> DebtHealthDTO | None:
        """Convert debt health data to DebtHealthDTO."""
        if not debt_data:
            return None
        return DebtHealthDTO(
            debt_to_income_bps=debt_data.get("debt_to_income_bps", 0),
            total_debt_paise=debt_data.get("total_debt_paise", 0),
            total_income_paise=debt_data.get("total_income_paise", 0),
            health_score=debt_data.get("health_score", 0),
        )

    @staticmethod
    def _to_wellness_radar(radar_data: list[dict[str, Any]]) -> list[WellnessRadarDTO]:
        """Convert wellness radar data to WellnessRadarDTO list."""
        return [
            WellnessRadarDTO(
                dimension=item.get("dimension", "Unknown"),
                score=item.get("score", 0),
                max_score=item.get("max_score", 10000),
            )
            for item in radar_data
        ]

    @staticmethod
    def _to_insights(insights: list[dict[str, Any]]) -> list[BehaviourInsightDTO]:
        """Convert insights to BehaviourInsightDTO list."""
        return [
            BehaviourInsightDTO(
                type=insight.get("type", "info"),
                severity=insight.get("severity", "medium"),
                message=insight.get("message", ""),
                action_url=insight.get("action_url"),
            )
            for insight in insights
        ]
