"""Recommendation Service - Personalized financial recommendations.

Provides personalized financial recommendations based on behavior patterns,
spending habits, and financial goals.
"""

from decimal import Decimal
from typing import Any

from src.engines.recommendation_engine.recommendations import compute_recommendations


class RecommendationService:
    """Service for generating personalized financial recommendations."""

    def get_recommendations(self, household_id: str = "primary") -> dict[str, Any]:
        """Get personalized financial recommendations for a household.

        Args:
            household_id: Household identifier (default: "primary")

        Returns:
            Dict with recommendations and supporting data
        """
        # In a real implementation, this would fetch the household's financial data
        # and behavior profile to generate personalized recommendations.
        # For now, return sample recommendations.

        # Sample financial profile for demonstration
        profile: dict[str, object] = {
            "borrowed_lifestyle_ratio": Decimal(
                "0.35"
            ),  # 35% of income goes to debt payments
            "foir": Decimal("0.45"),  # 45% debt-to-income ratio
            "liquidity_months": 1,  # 1.2 months of expenses saved (rounded)
            "current_subscriptions": list[dict[str, Any]](),  # No subscriptions in demo
        }

        recommendations = compute_recommendations(**profile)  # type: ignore[arg-type]

        return {
            "recommendations": [
                r.dict() if hasattr(r, "dict") else r for r in recommendations
            ],
            "profile": {
                k: float(v) if isinstance(v, Decimal) else v for k, v in profile.items()
            },
            "model_version": "v1.0-recommendation-engine",
        }

    def get_recommendation_details(self, recommendation_id: str) -> dict[str, Any]:
        """Get detailed information about a specific recommendation.

        Args:
            recommendation_id: Recommendation identifier

        Returns:
            Dict with detailed recommendation information
        """
        # In a real implementation, this would return detailed information
        # about the specific recommendation, including evidence, calculations,
        # and action steps.

        return {
            "id": recommendation_id,
            "title": "Build Emergency Fund",
            "description": "Save 3-6 months of living expenses for financial security.",
            "priority": "high",
            "estimated_impact": "High",
            "action_steps": [
                "Calculate your monthly expenses",
                "Set a target of 3-6 months of expenses",
                "Open a separate high-yield savings account",
                "Set up automatic transfers",
            ],
            "evidence": [
                "Current emergency fund covers only 1.2 months of expenses",
                "Recent unexpected expense of ₹25,000 caused credit card debt",
                "63% of Indians cannot cover a ₹50,000 emergency (RBI survey)",
            ],
            "confidence": 0.95,
        }
