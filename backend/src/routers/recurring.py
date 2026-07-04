"""
Recurring Transactions Router
=============================
Endpoints for managing recurring transactions and subscriptions.
"""

from typing import Optional
from fastapi import APIRouter, Query

from src.dependencies import (
    get_db,
    RecurringTransactionCreate,
    RecurringTransactionUpdate,
)
from src.logger import log
from src.errors import NotFoundError

router = APIRouter()


@router.get("/api/recurring")
def get_recurring_transactions(active_only: bool = Query(False)):
    """Get all recurring transactions.
    
    Args:
        active_only: If True, return only active recurring transactions
    """
    db = get_db()
    recurring = db.get_recurring_transactions(active_only=active_only)
    return {"recurring": recurring, "total": len(recurring)}


@router.get("/api/recurring/{recurring_id}")
def get_recurring_transaction(recurring_id: int):
    """Get a single recurring transaction by ID."""
    db = get_db()
    
    # Get all and filter by ID (db doesn't have get_single method)
    recurring_list = db.get_recurring_transactions(active_only=False)
    recurring = next((r for r in recurring_list if r.get("id") == recurring_id), None)
    
    if not recurring:
        raise NotFoundError("Recurring transaction", recurring_id)
    
    return recurring


@router.post("/api/recurring")
def create_recurring_transaction(recurring: RecurringTransactionCreate):
    """Create a new recurring transaction."""
    db = get_db()
    
    recurring_dict = {
        "description": recurring.description,
        "amount_paise": recurring.amount_paise,
        "type": recurring.type,
        "category": recurring.category,
        "frequency": recurring.frequency,
        "account_id": recurring.account_id,
        "next_due_date": recurring.next_due_date,
        "is_active": 1 if recurring.is_active else 0,
        "notes": recurring.notes,
    }
    
    recurring_id = db.insert_recurring_transaction(recurring_dict)
    log.info("Recurring transaction created: %s (%s)", recurring.description, recurring.frequency)
    
    # Return the created recurring transaction
    recurring_list = db.get_recurring_transactions(active_only=False)
    created = next((r for r in recurring_list if r.get("id") == recurring_id), None)
    return created


@router.put("/api/recurring/{recurring_id}")
def update_recurring_transaction(recurring_id: int, recurring: RecurringTransactionUpdate):
    """Update an existing recurring transaction."""
    db = get_db()
    
    # Check if recurring transaction exists
    recurring_list = db.get_recurring_transactions(active_only=False)
    existing = next((r for r in recurring_list if r.get("id") == recurring_id), None)
    if not existing:
        raise NotFoundError("Recurring transaction", recurring_id)
    
    # Build update dict
    update_dict = {}
    if recurring.description is not None:
        update_dict["description"] = recurring.description
    if recurring.amount_paise is not None:
        update_dict["amount_paise"] = recurring.amount_paise
    if recurring.type is not None:
        update_dict["type"] = recurring.type
    if recurring.category is not None:
        update_dict["category"] = recurring.category
    if recurring.frequency is not None:
        update_dict["frequency"] = recurring.frequency
    if recurring.next_due_date is not None:
        update_dict["next_due_date"] = recurring.next_due_date
    if recurring.is_active is not None:
        update_dict["is_active"] = 1 if recurring.is_active else 0
    if recurring.notes is not None:
        update_dict["notes"] = recurring.notes
    
    if not update_dict:
        return existing
    
    updated = db.update_recurring_transaction(recurring_id, update_dict)
    if not updated:
        raise NotFoundError("Recurring transaction", recurring_id)
    
    log.info("Recurring transaction updated: %s", recurring_id)
    
    # Return the updated recurring transaction
    recurring_list = db.get_recurring_transactions(active_only=False)
    return next((r for r in recurring_list if r.get("id") == recurring_id), None)


@router.delete("/api/recurring/{recurring_id}")
def delete_recurring_transaction(recurring_id: int):
    """Delete a recurring transaction."""
    db = get_db()
    
    deleted = db.delete_recurring_transaction(recurring_id)
    if not deleted:
        raise NotFoundError("Recurring transaction", recurring_id)
    
    log.info("Recurring transaction deleted: %s", recurring_id)
    return {"success": True, "message": "Recurring transaction deleted successfully"}


@router.post("/api/recurring/detect")
def detect_recurring():
    """Trigger auto-detection engine for recurring transactions.
    
    This endpoint analyzes transaction history to automatically
    identify recurring patterns (subscriptions, EMIs, rent, etc.).
    """
    from src.engines.recurring_engine import detect_recurring_transactions, save_detected_recurring
    from src.dependencies import DB_PATH
    
    log.info("Recurring transaction detection requested")
    
    detected = detect_recurring_transactions(DB_PATH)
    saved = save_detected_recurring(DB_PATH, detected)
    
    log.info("Recurring detection: %d found, %d new saved", len(detected), saved)
    
    return {"detected": detected, "new_saved": saved}
