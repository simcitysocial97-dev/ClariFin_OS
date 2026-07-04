"""
Transactions Router
===================
Endpoints for transaction listing and management.
"""

from typing import Optional
from fastapi import APIRouter, Query

from src.dependencies import (
    get_db,
    enrich_transaction,
    compute_is_large,
)

router = APIRouter()


@router.get("/api/transactions")
def get_transactions(
    search: Optional[str] = None,
    bank: Optional[str] = "All",
    category: Optional[str] = "All",
    type: Optional[str] = "All",
    member: Optional[str] = "All",
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Get transactions with filters and pagination."""
    db = get_db()
    filters = {}
    if search:
        filters["search"] = search
    if bank and bank != "All":
        filters["bank"] = bank
    if category and category != "All":
        filters["category"] = category
    if type and type != "All":
        filters["type"] = type
    if member and member != "All":
        filters["member"] = member

    result = db.get_all_transactions_with_bank(filters, page=page, per_page=per_page)
    enriched = [enrich_transaction(dict(t)) for t in result["items"]]
    enriched = compute_is_large(enriched)

    return {
        "transactions": enriched,
        "pagination": {
            "page": result["page"],
            "per_page": result["per_page"],
            "total": result["total"],
            "has_next": result["has_next"],
        }
    }
