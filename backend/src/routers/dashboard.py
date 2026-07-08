"""Dashboard summary endpoint."""
from fastapi import APIRouter, HTTPException

from src.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def api_dashboard_summary() -> dict:
    """
    Get simplified dashboard summary for MVP.

    Returns 4 key metrics:
    - Net Cash Flow
    - Savings Rate %
    - EMI Ratio %
    - Buffer Days
    """
    try:
        service = DashboardService()
        return service.get_summary().model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
