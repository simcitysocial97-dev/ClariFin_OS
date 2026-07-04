"""
Investments Router
==================
Endpoints for investment management and portfolio tracking.
"""

from typing import Optional
from fastapi import APIRouter, Query

from src.dependencies import (
    get_db,
    InvestmentCreate,
    InvestmentUpdate,
)
from src.logger import log
from src.errors import NotFoundError

# Import round function for gain/loss percentage calculation
from builtins import round

router = APIRouter()


@router.get("/api/investments")
def get_investments(active_only: bool = Query(False)):
    """Get all investments.
    
    Args:
        active_only: If True, return only active investments
    """
    db = get_db()
    investments = db.get_investments(active_only=active_only)
    return {"investments": investments, "total": len(investments)}


@router.get("/api/investments/{investment_id}")
def get_investment(investment_id: int):
    """Get a single investment by ID."""
    db = get_db()
    
    investment = db.get_investment(investment_id)
    if not investment:
        raise NotFoundError("Investment", investment_id)
    
    return investment


@router.post("/api/investments")
def create_investment(investment: InvestmentCreate):
    """Create a new investment."""
    db = get_db()
    
    investment_dict = {
        "name": investment.name,
        "type": investment.type,
        "platform": investment.platform,
        "invested_paise": investment.invested_paise,
        "current_value_paise": investment.current_value_paise,
        "units": investment.units,
        "purchase_date": investment.purchase_date,
        "maturity_date": investment.maturity_date,
        "linked_account_id": investment.linked_account_id,
        "is_active": 1 if investment.is_active else 0,
        "notes": investment.notes,
    }
    
    investment_id = db.insert_investment(investment_dict)
    log.info("Investment created: %s (%s)", investment.name, investment.type)
    
    # Return the created investment
    created = db.get_investment(investment_id)
    return created


@router.put("/api/investments/{investment_id}")
def update_investment(investment_id: int, investment: InvestmentUpdate):
    """Update an existing investment."""
    db = get_db()
    
    # Check if investment exists
    existing = db.get_investment(investment_id)
    if not existing:
        raise NotFoundError("Investment", investment_id)
    
    # Build update dict
    update_dict = {}
    if investment.name is not None:
        update_dict["name"] = investment.name
    if investment.type is not None:
        update_dict["type"] = investment.type
    if investment.platform is not None:
        update_dict["platform"] = investment.platform
    if investment.invested_paise is not None:
        update_dict["invested_paise"] = investment.invested_paise
    if investment.current_value_paise is not None:
        update_dict["current_value_paise"] = investment.current_value_paise
    if investment.units is not None:
        update_dict["units"] = investment.units
    if investment.is_active is not None:
        update_dict["is_active"] = 1 if investment.is_active else 0
    if investment.notes is not None:
        update_dict["notes"] = investment.notes
    
    if not update_dict:
        return existing
    
    updated = db.update_investment(investment_id, update_dict)
    if not updated:
        raise NotFoundError("Investment", investment_id)
    
    log.info("Investment updated: %s", investment_id)
    
    # Return the updated investment
    return db.get_investment(investment_id)


@router.delete("/api/investments/{investment_id}")
def delete_investment(investment_id: int):
    """Delete an investment."""
    db = get_db()
    
    deleted = db.delete_investment(investment_id)
    if not deleted:
        raise NotFoundError("Investment", investment_id)
    
    log.info("Investment deleted: %s", investment_id)
    return {"success": True, "message": "Investment deleted successfully"}


@router.get("/api/investments/summary")
def get_investments_summary():
    """Get aggregate summary of all active investments.
    
    Returns:
        Total invested, total current value, total gain/loss, and percentage.
    """
    db = get_db()
    
    # Use raw SQL for aggregation as specified in requirements
    with db.connection() as conn:
        cur = conn.execute("""
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(invested_paise), 0) as total_invested,
                COALESCE(SUM(current_value_paise), 0) as total_current_value
            FROM investments WHERE is_active = 1
        """)
        row = cur.fetchone()
    
    count = row["count"]
    total_invested = row["total_invested"]
    total_current_value = row["total_current_value"]
    
    # Compute gain/loss
    total_gain_loss_paise = total_current_value - total_invested
    gain_loss_percent = 0.0
    if total_invested > 0:
        gain_loss_percent = (total_gain_loss_paise / total_invested) * 100
    
    return {
        "count": count,
        "total_invested_paise": total_invested,
        "total_current_value_paise": total_current_value,
        "total_gain_loss_paise": total_gain_loss_paise,
        "gain_loss_percent": round(gain_loss_percent, 2),
    }
