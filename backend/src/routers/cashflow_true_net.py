"""
True Net Cashflow Router
=========================

Endpoints for true net income calculation that excludes debt recycling activities.
"""

from fastapi import APIRouter, Query, Depends
from src.db.core import FinanceDB
from src.dependencies import get_db
from src.engines.cashflow_engine_true_net import compute_true_monthly_cashflow

router = APIRouter()

@router.get("/api/cashflow/true-monthly")
def get_true_monthly_cashflow(
    month: str = Query(..., description="Month in YYYY-MM format"),
    db: FinanceDB = Depends(get_db)
):
    """Get true net monthly income excluding recycled money."""
    result = compute_true_monthly_cashflow(db, month)
    return result