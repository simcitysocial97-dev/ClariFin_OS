"""Loans Intelligence Workspace endpoint.

Returns aggregated loans data matching LoansViewModel format.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.loans_workspace_service import LoansWorkspaceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["loans-workspace"])


def _timed_log(endpoint: str, duration_ms: float, success: bool = True, error: str | None = None) -> None:
    """Emit structured timing log for loans workspace endpoints."""
    log_data = {
        "type": "loans_workspace_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning("[LOANS-WS] %s | %.0fms | FAIL: %s", endpoint, duration_ms, error)
    else:
        logger.info("[LOANS-WS] %s | %.0fms", endpoint, duration_ms)


@router.get("/loans")
def get_loans(
    loan_types: str | None = Query(default=None),
    lenders: str | None = Query(default=None),
    statuses: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Get loans summary for the Loans Intelligence Workspace.

    Returns aggregated data matching LoansViewModel format.
    """
    start = time.monotonic()
    service = LoansWorkspaceService()

    # Parse filters from comma-separated strings
    loan_types_list = None
    if loan_types:
        loan_types_list = [lt.strip() for lt in loan_types.split(",")]

    lenders_list = None
    if lenders:
        lenders_list = [item.strip() for item in lenders.split(",")]

    statuses_list = None
    if statuses:
        statuses_list = [s.strip() for s in statuses.split(",")]

    result = service.get_loans_summary(
        loan_types=loan_types_list,
        lenders=lenders_list,
        statuses=statuses_list,
    )
    _timed_log("GET /loans", (time.monotonic() - start) * 1000)
    return result
