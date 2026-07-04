"""
Behavior Router
===============
Endpoints for behavior analysis, insights, and nudges.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/behavior", tags=["behavior"])

STUB_NOTE = "Behavior analysis is being rebuilt. Real data coming soon."

@router.get("/profile")
async def get_behavior_profile():
    return {
        "status": "pending",
        "note": STUB_NOTE,
        "profile": {
            "loss_aversion_score": 0,
            "impulsivity_score": 0,
            "debt_recycling_frequency": 0,
            "savings_discipline_score": 0,
            "risk_tolerance_score": 0
        }
    }

@router.get("/summary")
async def get_behavior_summary():
    return {
        "status": "pending",
        "note": STUB_NOTE,
        "summary": {}
    }

@router.get("/insights")
async def get_behavior_insights():
    return {
        "status": "pending",
        "note": STUB_NOTE,
        "insights": []
    }

@router.get("/nudges")
async def get_nudges():
    return {
        "status": "pending",
        "note": STUB_NOTE,
        "nudges": []
    }