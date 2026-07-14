"""Behavior Service - Legacy compatibility wrapper.

DEPRECATED: Use BehaviourService instead. This class delegates to BehaviourService
for backwards compatibility with existing code.
"""

from typing import Any

from src.engines.insight_generator import generate_behavioral_insights
from src.engines.nudge_engine import (
    generate_nudges,
    get_nudge_summary,
    get_top_nudge,
)
from src.services.base import BaseService


class BehaviorService(BaseService):
    """
    Legacy compatibility wrapper for behaviour analysis.

    Delegates to BehaviourService internally. Maintained for backwards compatibility.
    New code should use BehaviourService directly.
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize with db_path for legacy compatibility."""
        super().__init__(db_path)
        # Import lazily to avoid circular imports
        from src.services.behaviour_service import BehaviourService as _BehaviourService
        self._behaviour_service = _BehaviourService(db_path)

    def compute_profile(self) -> dict[str, Any]:
        """Compute behavioral profile from transaction data.

        Delegates to BehaviourService.compute_financial_profile.
        Returns legacy format profile for backwards compatibility.
        """
        result = self._behaviour_service.compute_financial_profile()
        return {
            "profile_type": result.profile_type,
            "confidence": float(result.confidence),
            "explanation": result.explanation,
            "snapshot_date": result.snapshot_date,
            "financial_health_score": 50,  # Would compute from actual wellness score
        }

    def get_cached_profile(self) -> dict[str, Any] | None:
        """Get cached behavioral profile if available."""
        from src.services.behaviour_service import BehaviourService as _BehaviourService
        return _BehaviourService.get_cached_profile()

    def set_cached_profile(self, profile: dict[str, Any]) -> None:
        """Cache behavioral profile."""
        from src.services.behaviour_service import BehaviourService as _BehaviourService
        _BehaviourService.set_cached_profile("default", profile)

    def generate_insights(self, profile: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Generate behavioral insights and nudges.

        If profile is None, computes it first.
        """
        if profile is None:
            profile = self.compute_profile()
        insights = generate_behavioral_insights(profile)
        nudges = generate_nudges(profile)
        top_nudge = get_top_nudge(profile)
        summary = get_nudge_summary(profile)

        return {
            "insights": insights,
            "nudges": nudges,
            "top_nudge": top_nudge,
            "summary": summary,
            "financial_health_score": profile.get("financial_health_score", 50),
            "confidence": profile.get("confidence", 0),
        }
