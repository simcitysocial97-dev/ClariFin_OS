"""Financial Goals API endpoints.

All endpoints include request timing and structured error logging.
All monetary values in integer paise, all dates in ISO-8601 format.

Follows the same pattern as other routers - no FinanceDB import,
no calculation logic, pure HTTP delegation to FinancialIntelligenceService.
"""

import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Query

from src.services.financial_intelligence_service import FinancialIntelligenceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


def _timed_log(
    endpoint: str,
    goal_id: str | None,
    duration_ms: float,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Emit structured timing log for goal endpoints."""
    log_data = {
        "type": "goal_request",
        "endpoint": endpoint,
        "goal_id": goal_id,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[GOAL] %s | goal_id=%s | %.0fms | FAIL: %s",
            endpoint, goal_id, duration_ms, error,
        )
    else:
        logger.info("[GOAL] %s | goal_id=%s | %.0fms", endpoint, goal_id, duration_ms)


# ============================================================
# Goal Creation Endpoint
# ============================================================

@router.post("/")
def create_goal(
    household_id: str = Query("primary", description="Household identifier"),
    goal_type: str = Query(
        ...,
        description="Goal type (emergency_fund, debt_payoff, purchase, investment, education, retirement)",
    ),
    name: str = Query(..., min_length=1, max_length=100, description="Goal name"),
    target_amount_paise: int = Query(..., gt=0, description="Target amount in paise"),
    current_amount_paise: int = Query(default=0, ge=0, description="Current saved amount in paise"),
    target_date: str | None = Query(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Target date (YYYY-MM-DD)",
    ),
    priority: str = Query(default="medium", description="Priority: critical, high, medium, low"),
    status: str = Query(default="active", description="Status: active, completed, paused"),
) -> dict[str, Any]:
    """Create a new financial goal.

    Args:
        household_id: Household identifier
        goal_type: Type of goal
        name: Goal name
        target_amount_paise: Target amount in paise
        current_amount_paise: Current saved amount (default: 0)
        target_date: Target completion date (optional)
        priority: Goal priority (default: medium)
        status: Goal status (default: active)

    Returns:
        Created goal with ID
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"
        result = service.create_goal(
            goal_id=goal_id,
            household_id=household_id,
            goal_type=goal_type,
            name=name,
            target_amount_paise=target_amount_paise,
            current_amount_paise=current_amount_paise,
            target_date=target_date,
            priority=priority,
            status=status,
        )
        _timed_log("POST /goals/", goal_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "POST /goals/", None,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# List Goals Endpoint
# ============================================================

@router.get("/")
def list_goals(
    household_id: str = Query("primary", description="Household identifier"),
    status: str | None = Query(None, description="Filter by status: active, completed, paused"),
) -> list[dict[str, Any]]:
    """Get all goals for a household.

    Args:
        household_id: Household identifier
        status: Optional filter by status

    Returns:
        List of financial goals
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_household_goals(household_id=household_id, status=status)
        _timed_log("GET /goals/", household_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /goals/", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Get Single Goal Endpoint
# ============================================================

@router.get("/{goal_id}")
def get_goal(goal_id: str) -> dict[str, Any]:
    """Get a single goal by ID.

    Args:
        goal_id: Goal identifier

    Returns:
        Goal details
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_goal(goal_id=goal_id)
        _timed_log("GET /goals/{goal_id}", goal_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /goals/{goal_id}", goal_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Goal Projection Endpoint
# ============================================================

@router.get("/{goal_id}/projection")
def get_goal_projection(goal_id: str) -> dict[str, Any]:
    """Get goal achievement projection.

    Calculates projected completion timeline based on available monthly surplus.

    Args:
        goal_id: Goal identifier

    Returns:
        Projection with achieved, months_required, confidence
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_goal_projection(goal_id=goal_id)
        _timed_log("GET /goals/{goal_id}/projection", goal_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /goals/{goal_id}/projection", goal_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Goal Health Endpoint
# ============================================================

@router.get("/{goal_id}/health")
def get_goal_health(goal_id: str) -> dict[str, Any]:
    """Get goal health score.

    Returns health score, status, and explanation.

    Args:
        goal_id: Goal identifier

    Returns:
        Health score with status and explanation
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_goal_health(goal_id=goal_id)
        _timed_log("GET /goals/{goal_id}/health", goal_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /goals/{goal_id}/health", goal_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Delete Goal Endpoint
# ============================================================

@router.delete("/{goal_id}")
def delete_goal(goal_id: str) -> dict[str, Any]:
    """Delete a financial goal.

    Args:
        goal_id: Goal identifier

    Returns:
        Deletion confirmation
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.delete_goal(goal_id=goal_id)
        _timed_log("DELETE /goals/{goal_id}", goal_id, (time.monotonic() - start) * 1000)
        return {"deleted": result, "goal_id": goal_id}
    except Exception as e:
        _timed_log(
            "DELETE /goals/{goal_id}", goal_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise
