"""
Categories Router
=================
Endpoints for category management and listing.
"""

from typing import Optional, List
from fastapi import APIRouter

from src.dependencies import (
    get_db,
    CategoryUpdate,
    BulkCategoryUpdate,
)
from src.logger import log
from src.errors import NotFoundError

router = APIRouter()


@router.get("/api/categories")
def get_categories(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    drill_category: Optional[str] = None,
):
    """Get category summary with totals, monthly breakdown, and drill-down data.
    
    Args:
        date_from: Optional start date filter
        date_to: Optional end date filter
        drill_category: Optional category to drill down into (returns transactions)
    """
    db = get_db()
    
    # Get category summary
    summary_raw = db.get_category_summary(date_from, date_to)
    
    # Calculate total for percentage
    total_amount = sum(s.get("total_amount", 0) for s in summary_raw)
    
    # Format summary with display fields
    summary = []
    for s in summary_raw:
        amount = s.get("total_amount", 0)
        count = s.get("count", 0)
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        summary.append({
            "category": s.get("category", "Uncategorized"),
            "amount": amount,
            "amount_display": f"₹{amount:,.2f}",
            "count": count,
            "count_display": f"{count}",
            "percentage": percentage,
            "percentage_display": f"{percentage:.1f}%",
        })
    
    # Sort by amount descending
    summary = sorted(summary, key=lambda x: x["amount"], reverse=True)

    # Get monthly breakdown for stacked bar chart
    category_trends = db.get_category_totals_by_month()

    # Transform to monthly breakdown format
    from collections import defaultdict
    monthly_data = defaultdict(lambda: defaultdict(float))
    for trend in category_trends:
        month = trend.get("month", "")
        category = trend.get("category", "Uncategorized")
        total = trend.get("total", 0)
        monthly_data[month][category] = total

    monthly_breakdown = []
    for month in sorted(k for k in monthly_data.keys() if k is not None):
        month_entry = {"month": month}
        month_entry.update(monthly_data[month])
        monthly_breakdown.append(month_entry)
    
    # Get drill transactions if a category is specified
    drill_transactions = []
    if drill_category:
        filters = {"category": drill_category}
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        
        txns = db.get_all_transactions(filters)
        for t in txns:
            drill_transactions.append({
                "id": t.get("id"),
                "date": t.get("date"),
                "date_display": t.get("date"),
                "description": t.get("description", ""),
                "description_display": t.get("description", "")[:50],
                "amount": t.get("amount", 0),
                "amount_display": f"₹{t.get('amount', 0):,.2f}",
                "type": t.get("type", ""),
                "category": t.get("category", "Uncategorized"),
                "bank": t.get("bank", ""),
            })
    
    # Get uncategorized patterns
    uncategorized_raw = db.get_uncategorized_patterns(limit=20)
    uncategorized_patterns = []
    for p in uncategorized_raw:
        uncategorized_patterns.append({
            "description": p.get("description", ""),
            "count": p.get("count", 0),
            "total": p.get("total_amount", 0),
            "total_display": f"₹{p.get('total_amount', 0):,.2f}",
        })
    
    return {
        "summary": summary,
        "monthly_breakdown": monthly_breakdown,
        "drill_transactions": drill_transactions,
        "uncategorized_patterns": uncategorized_patterns,
    }


@router.get("/api/categories/list")
def get_categories_list():
    """Get list of all unique categories."""
    db = get_db()
    # Get from transactions
    raw = db.get_all_transactions()
    categories = sorted(set(t.get("category", "Uncategorized") for t in raw))
    return {"categories": categories}


@router.put("/api/transactions/{transaction_id}/category")
def update_transaction_category(
    transaction_id: int,
    update: CategoryUpdate,
):
    """Update category for a single transaction."""
    db = get_db()
    updated = db.update_category(
        transaction_id,
        update.category,
        update.subcategory,
    )
    if not updated:
        raise NotFoundError("Transaction", transaction_id)
    log.info("Category updated: transaction %d → %s", transaction_id, update.category)
    return {"success": True}


@router.post("/api/transactions/bulk-category-update")
def bulk_update_categories(update: BulkCategoryUpdate):
    """Update category for multiple transactions."""
    db = get_db()
    count = db.bulk_update_category(update.ids, update.category)
    log.info("Bulk category update: %d transactions → %s", count, update.category)
    return {"updated": count}
