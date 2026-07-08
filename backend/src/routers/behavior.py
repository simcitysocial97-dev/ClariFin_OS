"""Behavioral analytics and insights endpoints."""
from fastapi import APIRouter, HTTPException

from engines.insight_generator import (
    generate_behavioral_insights,
    generate_summary_text,
)
from engines.nudge_engine import (
    generate_nudges,
    get_nudge_summary,
    get_top_nudge,
)
from src.repositories import BehaviorRepository

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
        repo = BehaviorRepository()
        # Check cache first
        cached = repo.get_cached_profile()
        if cached is not None:
            return cached

        # Compute and cache
        profile = repo.compute_profile()
        repo.set_cached_profile(profile)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        repo = BehaviorRepository()
        # Check cache first
        cached = repo.get_cached_profile()
        if cached is not None:
            profile = cached
        else:
            profile = repo.compute_profile()
            repo.set_cached_profile(profile)

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
        raise HTTPException(status_code=500, detail=str(e))


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
        repo = BehaviorRepository()
        # Check cache first
        cached = repo.get_cached_profile()
        if cached is not None:
            profile = cached
        else:
            profile = repo.compute_profile()
            repo.set_cached_profile(profile)

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
        raise HTTPException(status_code=500, detail=str(e))
