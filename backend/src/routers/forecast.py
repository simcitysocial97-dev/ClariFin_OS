"""Forecast Intelligence Workspace endpoint.

Returns aggregated forecast data matching ForecastViewModel format.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["forecast"])


def _timed_log(endpoint: str, duration_ms: float, success: bool = True, error: str | None = None) -> None:
    """Emit structured timing log for forecast endpoints."""
    log_data = {
        "type": "forecast_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning("[FORECAST] %s | %.0fms | FAIL: %s", endpoint, duration_ms, error)
    else:
        logger.info("[FORECAST] %s | %.0fms", endpoint, duration_ms)


@router.get("/forecast")
def get_forecast(
    horizon: int = Query(default=12, ge=1, le=60),
    scenarios: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Get forecast summary for the Forecast Intelligence Workspace.

    Returns aggregated data matching ForecastViewModel format.
    """
    start = time.monotonic()
    service = ForecastService()

    # Parse scenarios from comma-separated string
    scenarios_list = None
    if scenarios:
        scenarios_list = [s.strip() for s in scenarios.split(",")]

    result = service.get_forecast_summary(
        horizon_months=horizon,
        scenarios=scenarios_list,
    )
    _timed_log("GET /forecast", (time.monotonic() - start) * 1000)
    return result
