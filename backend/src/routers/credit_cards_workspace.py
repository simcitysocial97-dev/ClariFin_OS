"""Credit Cards Intelligence Workspace endpoint.

Returns aggregated credit cards data matching CreditCardsViewModel format.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.credit_cards_workspace_service import CreditCardsWorkspaceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["credit-cards-workspace"])


def _timed_log(endpoint: str, duration_ms: float, success: bool = True, error: str | None = None) -> None:
    """Emit structured timing log for credit cards workspace endpoints."""
    log_data = {
        "type": "credit_cards_workspace_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning("[CARDS-WS] %s | %.0fms | FAIL: %s", endpoint, duration_ms, error)
    else:
        logger.info("[CARDS-WS] %s | %.0fms", endpoint, duration_ms)


@router.get("/credit-cards")
def get_credit_cards(
    statuses: str | None = Query(default=None),
    banks: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Get credit cards summary for the Credit Cards Intelligence Workspace.

    Returns aggregated data matching CreditCardsViewModel format.
    """
    start = time.monotonic()
    service = CreditCardsWorkspaceService()

    # Parse filters from comma-separated strings
    statuses_list = None
    if statuses:
        statuses_list = [s.strip() for s in statuses.split(",")]

    banks_list = None
    if banks:
        banks_list = [b.strip() for b in banks.split(",")]

    result = service.get_credit_cards_summary(
        statuses=statuses_list,
        banks=banks_list,
    )
    _timed_log("GET /credit-cards", (time.monotonic() - start) * 1000)
    return result
