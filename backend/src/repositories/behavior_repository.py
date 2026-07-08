"""Behavior domain repository."""
from src.common import DB_PATH
from src.engines.behavior_engine import (
    compute_behavior_profile,
    get_cached_behavior_profile,
    set_cached_behavior_profile,
)
from src.engines.insight_generator import (
    generate_behavioral_insights,
)
from src.engines.nudge_engine import (
    generate_nudges,
    get_nudge_summary,
    get_top_nudge,
)


class BehaviorRepository:
    """Repository for behavior operations."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DB_PATH

    def compute_profile(self) -> dict:
        """Compute behavioral profile from transaction data."""
        return compute_behavior_profile(self.db_path)

    def get_cached_profile(self) -> dict | None:
        """Get cached behavioral profile if available."""
        return get_cached_behavior_profile(self.db_path)

    def set_cached_profile(self, profile: dict) -> None:
        """Cache behavioral profile."""
        set_cached_behavior_profile(self.db_path, profile)

    def generate_insights(self, profile: dict | None = None) -> dict:
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

