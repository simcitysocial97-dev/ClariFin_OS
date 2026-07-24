"""Cashflow Intelligence Workspace endpoint.

Returns aggregated cashflow data matching CashflowViewModel format.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.cashflow_workspace_service import CashflowWorkspaceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["cashflow-workspace"])


def _timed_log(endpoint: str, duration_ms: float, success: bool = True, error: str | None = None) -> None:
    """Emit structured timing log for cashflow workspace endpoints."""
    log_data = {
        "type": "cashflow_workspace_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning("[CASHFLOW-WS] %s | %.0fms | FAIL: %s", endpoint, duration_ms, error)
    else:
        logger.info("[CASHFLOW-WS] %s | %.0fms", endpoint, duration_ms)


@router.get("/cashflow")
def get_cashflow(
    period: str = Query(default="monthly"),
) -> dict[str, Any]:
    """
    Get cashflow summary for the Cashflow Truth Workspace.

    Returns aggregated data matching CashflowViewModel format.
    All monetary values in paise (integer).
    """
    start = time.monotonic()
    service = CashflowWorkspaceService()

    result = service.get_cashflow_summary(period=period)
    _timed_log("GET /cashflow", (time.monotonic() - start) * 1000)
    return result
