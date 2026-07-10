"""Dashboard summary endpoint."""
from fastapi import APIRouter, HTTPException

from src.models.dashboard import DashboardSummary
from src.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def api_dashboard_summary() -> DashboardSummary:
    """
    Get dashboard summary with behavior insights.

    Returns:
    - behavior_score: Financial health score (0-1)
    - spending_this_month: Total spending for current month
    - top_category: Most common spending category
    - insights: Personalized insights
    - nudges: Action recommendations
    - reconciliation_pending: Count of pending transfers
    - large_transactions: Significant transactions (>= ₹10,000)
    """
    try:
        service = DashboardService()
        return service.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
