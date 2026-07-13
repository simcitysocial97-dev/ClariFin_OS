"""Recommendation Engine - Deterministic financial recommendations.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.

Generates actionable recommendations based on financial behaviour metrics:
- Debt Dependency Check (>20%)
- FOIR Check (>50%)
- Liquidity Check (<3 months)
- Subscription Growth Check
"""

from .recommendations import (
    Recommendation,
    RecommendationSeverity,
    check_debt_dependency,
    check_foir,
    check_liquidity,
    compute_recommendations,
    detect_subscription_growth,
)

__all__ = [
    "Recommendation",
    "RecommendationSeverity",
    "check_debt_dependency",
    "check_foir",
    "check_liquidity",
    "compute_recommendations",
    "detect_subscription_growth",
]
