"""
Cards Router
============
Endpoints for credit/debit card management.
"""

from typing import Optional, List
from fastapi import APIRouter, Query

from src.dependencies import get_db
from src.logger import log
from src.errors import NotFoundError

router = APIRouter()


@router.get("/api/cards")
def api_get_cards(
    account_id: Optional[int] = Query(None),
    include_inactive: bool = Query(False),
):
    """Get all cards. Optionally filter by account_id."""
    db = get_db()
    cards = db.get_cards(
        account_id=account_id,
        include_inactive=include_inactive,
    )
    
    # Format credit_limit_display for each card
    from src.utils import format_paise
    for card in cards:
        card["credit_limit_display"] = format_paise(card.get("credit_limit_paise", 0))
    
    return {"cards": cards, "total": len(cards)}


@router.get("/api/cards/{card_id}")
def api_get_card(card_id: int):
    """Get a single card by ID."""
    db = get_db()
    card = db.get_card(card_id)
    
    if not card:
        raise NotFoundError("Card", card_id)
    
    # Format credit_limit_display
    from src.utils import format_paise
    card["credit_limit_display"] = format_paise(card.get("credit_limit_paise", 0))
    
    return card


@router.post("/api/cards")
def api_create_card(card_data: dict):
    """Create a new card."""
    db = get_db()
    
    # Map frontend field names to DB field names if needed
    card_dict = {
        "account_id": card_data.get("account_id"),
        "card_name": card_data.get("card_name", ""),
        "card_type": card_data.get("card_type", "visa"),
        "issuer": card_data.get("issuer", ""),
        "last_four": card_data.get("last_four", "XXXX"),
        "cardholder_name": card_data.get("cardholder_name", ""),
        "credit_limit_paise": card_data.get("credit_limit_paise", 0),
        "billing_date": card_data.get("billing_date", 1),
        "card_color": card_data.get("card_color", "#1E293B"),
        "card_gradient": card_data.get("card_gradient", "from-slate-800 to-slate-900"),
    }
    
    card_id = db.create_card(card_dict)
    log.info("Card created: %s (%s)", card_dict["card_name"], card_dict["issuer"])
    
    # Return the created card
    card = db.get_card(card_id)
    from src.utils import format_paise
    card["credit_limit_display"] = format_paise(card.get("credit_limit_paise", 0))
    
    return card


@router.put("/api/cards/{card_id}")
def api_update_card(card_id: int, card_data: dict):
    """Update an existing card."""
    db = get_db()
    
    # Check if card exists
    existing = db.get_card(card_id)
    if not existing:
        raise NotFoundError("Card", card_id)
    
    # Map frontend field names to DB field names
    update_dict = {}
    field_mapping = {
        "account_id": "account_id",
        "card_name": "card_name",
        "card_type": "card_type",
        "issuer": "issuer",
        "last_four": "last_four",
        "cardholder_name": "cardholder_name",
        "credit_limit_paise": "credit_limit_paise",
        "billing_date": "billing_date",
        "card_color": "card_color",
        "card_gradient": "card_gradient",
    }
    
    for frontend_field, db_field in field_mapping.items():
        if frontend_field in card_data:
            update_dict[db_field] = card_data[frontend_field]
    
    if not update_dict:
        return existing
    
    updated = db.update_card(card_id, update_dict)
    if not updated:
        raise NotFoundError("Card", card_id)
    
    log.info("Card updated: %s", card_id)
    
    # Return the updated card
    card = db.get_card(card_id)
    from src.utils import format_paise
    card["credit_limit_display"] = format_paise(card.get("credit_limit_paise", 0))
    
    return card


@router.delete("/api/cards/{card_id}")
def api_delete_card(card_id: int):
    """Soft-delete a card."""
    db = get_db()
    
    deleted = db.delete_card(card_id)
    if not deleted:
        raise NotFoundError("Card", card_id)
    
    log.info("Card deleted: %s", card_id)
    return {"success": True, "message": "Card deleted successfully"}
