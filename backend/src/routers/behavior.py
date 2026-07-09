"""Behavioral analytics and insights endpoints."""
from fastapi import APIRouter, HTTPException

from src.engines.insight_generator import generate_summary_text
from src.services import BehaviorService

router = APIRouter(prefix="/api/behavior", tags=["behavior"])


@router.get("/summary")
def api_behavior_summary() -> dict:
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
        service = BehaviorService()
        # Check cache first
        cached = service.get_cached_profile()
        if cached is not None:
            return cached

        # Compute and cache
        profile = service.compute_profile()
        service.set_cached_profile(profile)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score")
def api_behavior_score() -> dict:
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
        service = BehaviorService()
        # Check cache first
        cached = service.get_cached_profile()
        if cached is not None:
            profile = cached
        else:
            profile = service.compute_profile()
            service.set_cached_profile(profile)

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
def api_behavior_insights() -> dict:
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
        service = BehaviorService()
        # Check cache first
        cached = service.get_cached_profile()
        if cached is not None:
            profile = cached
        else:
            profile = service.compute_profile()
            service.set_cached_profile(profile)

        insights_result = service.generate_insights(profile)

        return {
            "insights": insights_result["insights"],
            "nudges": insights_result["nudges"],
            "top_nudge": insights_result["top_nudge"],
            "summary": insights_result["summary"],
            "financial_health_score": insights_result["financial_health_score"],
            "confidence": insights_result["confidence"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
