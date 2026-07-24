"""Reconciliation Intelligence Workspace endpoint.

Returns aggregated reconciliation data matching ReconciliationViewModel format.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.reconciliation_workspace_service import ReconciliationWorkspaceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["reconciliation-workspace"])


def _timed_log(endpoint: str, duration_ms: float, success: bool = True, error: str | None = None) -> None:
    """Emit structured timing log for reconciliation workspace endpoints."""
    log_data = {
        "type": "reconciliation_workspace_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning("[RECON-WS] %s | %.0fms | FAIL: %s", endpoint, duration_ms, error)
    else:
        logger.info("[RECON-WS] %s | %.0fms", endpoint, duration_ms)


@router.get("/reconciliation")
def get_reconciliation(
    status: str | None = Query(default=None),
    banks: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Get reconciliation summary for the Reconciliation Intelligence Workspace.

    Returns aggregated data matching ReconciliationViewModel format.
    """
    start = time.monotonic()
    service = ReconciliationWorkspaceService()

    # Parse filters from comma-separated strings
    status_list = None
    if status:
        status_list = [s.strip() for s in status.split(",")]

    banks_list = None
    if banks:
        banks_list = [b.strip() for b in banks.split(",")]

    result = service.get_reconciliation_summary(
        status=status_list,
        banks=banks_list,
    )
    _timed_log("GET /reconciliation", (time.monotonic() - start) * 1000)
    return result
