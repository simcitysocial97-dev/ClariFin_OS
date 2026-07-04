"""
Income Sources Router
=====================
Endpoints for income source management.
"""

from typing import Optional
from fastapi import APIRouter, Query

from src.dependencies import (
    get_db,
    IncomeSourceCreate,
    IncomeSourceUpdate,
)
from src.logger import log
from src.errors import NotFoundError

router = APIRouter()


@router.get("/api/income-sources")
def get_income_sources(active_only: bool = Query(False)):
    """Get all income sources.
    
    Args:
        active_only: If True, return only active income sources
    """
    db = get_db()
    sources = db.get_income_sources(active_only=active_only)
    return {"sources": sources, "total": len(sources)}


@router.post("/api/income-sources")
def create_income_source(source: IncomeSourceCreate):
    """Create a new income source."""
    db = get_db()
    
    source_dict = {
        "name": source.name,
        "type": source.type,
        "account_id": source.account_id,
        "amount_paise": source.amount_paise,
        "frequency": source.frequency,
        "start_date": source.start_date,
        "end_date": source.end_date,
        "is_active": 1 if source.is_active else 0,
        "notes": source.notes,
    }
    
    source_id = db.insert_income_source(source_dict)
    log.info("Income source created: %s (%s)", source.name, source.type)
    
    # Return the created source
    sources = db.get_income_sources(active_only=False)
    created = next((s for s in sources if s["id"] == source_id), None)
    return created


@router.put("/api/income-sources/{source_id}")
def update_income_source(source_id: int, source: IncomeSourceUpdate):
    """Update an existing income source."""
    db = get_db()
    
    # Check if source exists
    sources = db.get_income_sources(active_only=False)
    existing = next((s for s in sources if s["id"] == source_id), None)
    if not existing:
        raise NotFoundError("Income Source", source_id)
    
    # Build update dict
    update_dict = {}
    if source.name is not None:
        update_dict["name"] = source.name
    if source.type is not None:
        update_dict["type"] = source.type
    if source.account_id is not None:
        update_dict["account_id"] = source.account_id
    if source.amount_paise is not None:
        update_dict["amount_paise"] = source.amount_paise
    if source.frequency is not None:
        update_dict["frequency"] = source.frequency
    if source.start_date is not None:
        update_dict["start_date"] = source.start_date
    if source.end_date is not None:
        update_dict["end_date"] = source.end_date
    if source.is_active is not None:
        update_dict["is_active"] = 1 if source.is_active else 0
    if source.notes is not None:
        update_dict["notes"] = source.notes
    
    if not update_dict:
        return existing
    
    updated = db.update_income_source(source_id, update_dict)
    if not updated:
        raise NotFoundError("Income Source", source_id)
    
    log.info("Income source updated: %s", source_id)
    
    # Return the updated source
    sources = db.get_income_sources(active_only=False)
    updated_source = next((s for s in sources if s["id"] == source_id), None)
    return updated_source


@router.delete("/api/income-sources/{source_id}")
def delete_income_source(source_id: int):
    """Delete an income source."""
    db = get_db()
    
    deleted = db.delete_income_source(source_id)
    if not deleted:
        raise NotFoundError("Income Source", source_id)
    
    log.info("Income source deleted: %s", source_id)
    return {"success": True, "message": "Income source deleted successfully"}
