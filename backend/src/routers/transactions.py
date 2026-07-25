"""Transaction listing and analytics endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.services.transaction_service import TransactionService

router = APIRouter(prefix="/api", tags=["transactions"])


@router.get("/transactions", response_model=list[dict[str, Any]])
def get_transactions(
    search: str | None = None,
    bank: str | None = "All",
    category: str | None = "All",
    type: str | None = "All",
    member: str | None = "All",
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    """Get transactions as enriched dictionaries."""
    try:
        service = TransactionService()
        return service.get_transactions(
            search=search,
            bank=bank,
            category=category,
            type=type,
            member=member,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
def get_overview(
    exclude_transfers: bool = Query(True),
    member: str | None = "All",
) -> dict[str, Any]:
    """Get overview metrics and charts."""
    try:
        service = TransactionService()
        return service.get_overview(
            exclude_transfers=exclude_transfers,
            member=member,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
def get_categories(
    exclude_transfers: bool = Query(True),
    member: str | None = "All",
    drill_category: str | None = None,
) -> dict[str, Any]:
    """Get category summary and breakdown."""
    try:
        service = TransactionService()
        return service.get_categories(
            exclude_transfers=exclude_transfers,
            member=member,
            drill_category=drill_category,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
def get_analytics(
    exclude_transfers: bool = Query(True),
    member: str | None = "All",
) -> dict[str, Any]:
    """Get analytics data."""
    try:
        service = TransactionService()
        return service.get_analytics(
            exclude_transfers=exclude_transfers,
            member=member,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
