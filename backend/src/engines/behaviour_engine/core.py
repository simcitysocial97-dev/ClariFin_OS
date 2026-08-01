"""Behaviour Engine Core — Bridge module for legacy behavior_engine functions.

Re-exports core behavioral intelligence functions from the legacy monolithic
``behavior_engine.py`` module and related insight/nudge engines, providing a
single import path for tests and consumers.

All monetary values are integers in paise (₹1.00 = 100 paise).
"""

from src.engines.behavior_engine import (
    _coefficient_of_variation,
    _compute_financial_stress_index,
    _compute_habit_stability_score,
    _compute_impulsivity_score,
    _compute_loss_aversion_index,
    _compute_savings_discipline_score,
    _moving_average,
    _normalize_score,
    compute_behavior_profile,
    detect_india_risk_patterns,
    get_cached_behavior_profile,
    invalidate_behavior_cache,
    set_cached_behavior_profile,
)
from src.engines.insight_generator import (
    generate_behavioral_insights,
    generate_summary_text,
)
from src.engines.nudge_engine import (
    generate_nudges,
    get_top_nudge,
)

__all__ = [
    # Utility functions
    "_normalize_score",
    "_coefficient_of_variation",
    "_moving_average",
    # Behavioral indices
    "_compute_loss_aversion_index",
    "_compute_impulsivity_score",
    "_compute_habit_stability_score",
    "_compute_financial_stress_index",
    "_compute_savings_discipline_score",
    # Core profile
    "compute_behavior_profile",
    "detect_india_risk_patterns",
    # Insight generation
    "generate_behavioral_insights",
    "generate_summary_text",
    # Nudge engine
    "generate_nudges",
    "get_top_nudge",
    "get_cached_behavior_profile",
    "set_cached_behavior_profile",
    "invalidate_behavior_cache",
]
