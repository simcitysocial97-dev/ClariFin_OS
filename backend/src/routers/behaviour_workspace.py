"""Behaviour Intelligence Workspace endpoint.

Returns aggregated behaviour data matching BehaviourViewModel format.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.behaviour_workspace_service import BehaviourWorkspaceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["behaviour-workspace"])


def _timed_log(
    endpoint: str, duration_ms: float, success: bool = True, error: str | None = None
) -> None:
    """Emit structured timing log for behaviour workspace endpoints."""
    log_data = {
        "type": "behaviour_workspace_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[BEHAVIOUR-WS] %s | %.0fms | FAIL: %s", endpoint, duration_ms, error
        )
    else:
        logger.info("[BEHAVIOUR-WS] %s | %.0fms", endpoint, duration_ms)


@router.get("/behaviour")
def get_behaviour(
    period: str = Query(default="monthly"),
) -> dict[str, Any]:
    """
    Get behaviour summary for the Behaviour Intelligence Workspace.

    Returns aggregated data matching BehaviourViewModel format.
    """
    start = time.monotonic()
    service = BehaviourWorkspaceService()

    result = service.get_behaviour_summary(period=period)
    _timed_log("GET /behaviour", (time.monotonic() - start) * 1000)
    return result
