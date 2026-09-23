"""Cashflow endpoints."""

from fastapi import APIRouter, Query

from src.core.dtos.cashflow_dto import (
    CashflowCategoryResponse,
    CashflowMonthlyResponse,
    CashflowSummaryDTO,
    CashflowTransactionResponse,
)
from src.services import CashflowService

router = APIRouter(prefix="/api", tags=["cashflow"])


@router.get("/cashflow")
def get_cashflow() -> CashflowSummaryDTO:
    """
    Returns cashflow summary with total income, expenses, and net cashflow.
    All monetary values in paise (INTEGER).
    """
    service = CashflowService()
    return service.calculate_summary()


@router.get("/cashflow/monthly")
def get_cashflow_monthly(
    months: int = Query(default=6, ge=1, le=12),
) -> CashflowMonthlyResponse:
    """
    Returns month-by-month income and expense aggregation.
    All monetary values in paise (INTEGER).
    """
    service = CashflowService()
    return service.get_monthly(months=months)


@router.get("/cashflow/categories")
def get_cashflow_categories() -> CashflowCategoryResponse:
    """
    Returns category breakdown for cashflow.
    All monetary values in paise (INTEGER).
    """
    service = CashflowService()
    return service.get_categories()


@router.get("/cashflow/transactions")
def get_cashflow_transactions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> CashflowTransactionResponse:
    """
    Returns transactions for cashflow view.
    All monetary values in paise (INTEGER).
    """
    service = CashflowService()
    return service.get_transactions(limit=limit, offset=offset)
