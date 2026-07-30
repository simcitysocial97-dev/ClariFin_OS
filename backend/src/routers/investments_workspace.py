"""Investments Intelligence Workspace endpoint.

Returns aggregated investments data matching InvestmentsViewModel format.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.investments_workspace_service import InvestmentsWorkspaceService

# Note: The service file has a typo in the name (investments vs investments)
# This import matches the actual file name

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["investments-workspace"])


def _timed_log(
    endpoint: str, duration_ms: float, success: bool = True, error: str | None = None
) -> None:
    """Emit structured timing log for investments workspace endpoints."""
    log_data = {
        "type": "investments_workspace_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[INVESTMENTS-WS] %s | %.0fms | FAIL: %s", endpoint, duration_ms, error
        )
    else:
        logger.info("[INVESTMENTS-WS] %s | %.0fms", endpoint, duration_ms)


@router.get("/investments")
def get_investments(
    investment_types: str | None = Query(default=None),
    institutions: str | None = Query(default=None),
    statuses: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Get investments summary for the Investments Intelligence Workspace.

    Returns aggregated data matching InvestmentsViewModel format.
    """
    start = time.monotonic()
    service = InvestmentsWorkspaceService()

    # Parse filters from comma-separated strings
    investment_types_list = None
    if investment_types:
        investment_types_list = [it.strip() for it in investment_types.split(",")]

    institutions_list = None
    if institutions:
        institutions_list = [i.strip() for i in institutions.split(",")]

    statuses_list = None
    if statuses:
        statuses_list = [s.strip() for s in statuses.split(",")]

    result = service.get_investments_summary(
        investment_types=investment_types_list,
        institutions=institutions_list,
        statuses=statuses_list,
    )
    _timed_log("GET /investments", (time.monotonic() - start) * 1000)
    return result
