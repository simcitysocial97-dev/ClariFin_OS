"""Net Worth Intelligence Workspace endpoint.

Returns aggregated net worth data matching NetWorthViewModel format.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.networth_workspace_service import NetWorthWorkspaceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["networth-workspace"])


def _timed_log(
    endpoint: str, duration_ms: float, success: bool = True, error: str | None = None
) -> None:
    """Emit structured timing log for net worth workspace endpoints."""
    log_data = {
        "type": "networth_workspace_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[NETWORTH-WS] %s | %.0fms | FAIL: %s", endpoint, duration_ms, error
        )
    else:
        logger.info("[NETWORTH-WS] %s | %.0fms", endpoint, duration_ms)


@router.get("/net-worth")
def get_networth(
    date_range: str | None = Query(default=None),
    account_types: str | None = Query(default=None),
    period: str = Query(default="1M"),
) -> dict[str, Any]:
    """
    Get net worth summary for the Net Worth Intelligence Workspace.

    Returns aggregated data matching NetWorthViewModel format.
    """
    start = time.monotonic()
    service = NetWorthWorkspaceService()

    # Parse filters from comma-separated strings
    date_range_parsed = None
    if date_range:
        parts = date_range.split(",")
        date_range_parsed = {
            "from": parts[0],
            "to": parts[1] if len(parts) > 1 else None,
        }

    account_types_list = None
    if account_types:
        account_types_list = [t.strip() for t in account_types.split(",")]

    result = service.get_networth_summary(
        date_range=date_range_parsed,
        account_types=account_types_list,
        period=period,
    )
    _timed_log("GET /net-worth", (time.monotonic() - start) * 1000)
    return result
