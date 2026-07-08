"""Behavioral analytics and insights endpoints."""
from fastapi import APIRouter

from engines.behavior_engine import (
    compute_behavior_profile,
    get_cached_behavior_profile,
    set_cached_behavior_profile,
)
from engines.insight_generator import (
    generate_behavioral_insights,
    generate_summary_text,
)
from engines.nudge_engine import (
    generate_nudges,
    get_nudge_summary,
    get_top_nudge,
)
from src.common import DB_PATH

router = APIRouter(prefix="/api/behavior", tags=["behavior"])


@router.get("/summary")
def api_behavior_summary():
    """
    Get comprehensive behavioral profile.

    Phase 3: Advanced Behavioral Intelligence Layer.

    Returns:
        {
            "temporal_patterns": {...},
            "behavioral_indices": {...},
            "risk_signals": {...},
            "confidence": float (0–1),
            "financial_health_score": float (0–100)
        }
    """
    try:
        # Check cache first
        cached = get_cached_behavior_profile(DB_PATH)
        if cached is not None:
            return cached

        # Compute and cache
        profile = compute_behavior_profile(DB_PATH)
        set_cached_behavior_profile(DB_PATH, profile)
        return profile
    except Exception as e:
        raise Exception(e)


@router.get("/score")
def api_behavior_score():
    """
    Get financial health score with breakdown.

    Phase 3: Composite health score with component breakdown.

    Returns:
        {
            "financial_health_score": float (0–100),
            "confidence": float (0–1),
            "components": {...},
            "summary": str
        }
    """
    try:
        # Check cache first
        cached = get_cached_behavior_profile(DB_PATH)
        if cached is not None:
            profile = cached
        else:
            profile = compute_behavior_profile(DB_PATH)
            set_cached_behavior_profile(DB_PATH, profile)

        indices = profile.get("behavioral_indices", {})

        return {
            "financial_health_score": profile.get("financial_health_score", 50),
            "confidence": profile.get("confidence", 0),
            "components": {
                "savings_discipline": indices.get("savings_discipline", {}).get("score", 0.5),
                "habit_stability": indices.get("habit_stability", {}).get("score", 0.5),
                "impulsivity": indices.get("impulsivity", {}).get("score", 0.5),
                "financial_stress": indices.get("financial_stress", {}).get("score", 0.5),
                "loss_aversion": indices.get("loss_aversion", {}).get("score", 0.5),
            },
            "risk_flags": profile.get("risk_signals", {}),
            "summary": generate_summary_text(profile),
        }
    except Exception as e:
        raise Exception(e)


@router.get("/insights")
def api_behavior_insights():
    """
    Get behavioral insights and nudges.

    Phase 3: Evidence-based insights with actionable suggestions.

    Returns:
        {
            "insights": [...],
            "nudges": [...],
            "top_nudge": {...},
            "summary": str
        }
    """
    try:
        # Check cache first
        cached = get_cached_behavior_profile(DB_PATH)
        if cached is not None:
            profile = cached
        else:
            profile = compute_behavior_profile(DB_PATH)
            set_cached_behavior_profile(DB_PATH, profile)

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
    except Exception as e:
        raise Exception(e)
