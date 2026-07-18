"""Cashflow endpoints."""
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.models.explanation import CashflowResponse
from src.services.cashflow_service import CashflowService

router = APIRouter(prefix="/api", tags=["cashflow"])


@router.get("/cashflow/monthly", response_model=CashflowResponse)
def get_cashflow_monthly(
    months: int = Query(default=6, ge=1, le=12),
    member: str | None = Query(default=None),
) -> CashflowResponse:
    """
    Returns month-by-month income and expense aggregation.
    All monetary values in paise (INTEGER).
    """
    try:
        service = CashflowService()
        return service.calculate_with_explanation(months=months, member=member)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# v1 Cashflow Analysis Endpoint (with financial events)
# ============================================================

@router.get("/v1/cashflow/monthly")
def get_cashflow_monthly_analysis(
    month: str = Query(..., description="Month in YYYY-MM format"),
    scope: str = Query(default="household", description="household or individual"),
    owner_id: str = Query(default="self", description="Owner ID for individual scope"),
    basis: str = Query(default="cash", description="cash or accrual"),
) -> dict[str, Any]:
    """
    Get enriched monthly cashflow analysis with financial events overlay.

    Returns:
        - cash_surplus, true_savings, liability_adjusted_savings
        - net_worth_impact, month_classification
        - credit_dependency_ratio, effective_liquidity_cost_annualized
    """
    try:
        service = CashflowService()
        result = service.get_monthly_analysis(
            month_bucket=month,
            scope=scope,
            owner_id=owner_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
