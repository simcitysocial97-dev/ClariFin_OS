"""Dashboard summary endpoint."""
from fastapi import APIRouter, HTTPException

from src.repositories import DashboardRepository

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def api_dashboard_summary():
    """
    Get simplified dashboard summary for MVP.

    Returns 4 key metrics:
    - Net Cash Flow
    - Savings Rate %
    - EMI Ratio %
    - Buffer Days
    """
    try:
        repo = DashboardRepository()
        return repo.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
