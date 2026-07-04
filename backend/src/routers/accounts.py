"""
Accounts Router
===============
Endpoints for accounts, cards, and members management.
"""

from typing import Optional, List
from fastapi import APIRouter, Query

from src.dependencies import (
    get_db,
    MemberCreate,
    AccountCreate,
    AccountUpdate,
    CardCreate,
    CardUpdate,
)
from src.engines.balance_engine import (
    compute_running_balance,
    compute_account_balance,
    validate_statement_balance,
    get_accounts_list,
)
from src.logger import log
from decimal import Decimal
from src.errors import NotFoundError
from src.utils import format_paise
from src.utils.money import to_paise

router = APIRouter()


@router.get("/api/accounts")
def api_get_accounts(
    account_type: Optional[str] = Query(None),
    exclude_type: Optional[str] = Query(None),
):
    """Get all managed accounts from the database.
    
    Args:
        account_type: Filter by account type (savings, current, credit_card, etc.)
        exclude_type: Exclude accounts of this type (e.g., 'credit_card' to exclude cards)
    
    By default, returns only bank accounts (excludes credit cards which should appear in Cards tab).
    """
    db = get_db()
    accounts = db.get_accounts(include_inactive=False)
    
    # Filter out credit cards by default (they should appear in Cards tab)
    if exclude_type:
        accounts = [a for a in accounts if a.get("account_type") != exclude_type]
    else:
        # Default: exclude credit cards
        accounts = [a for a in accounts if a.get("account_type") != "credit_card"]
    
    # Apply account_type filter if specified
    if account_type:
        accounts = [a for a in accounts if a.get("account_type") == account_type]
    
    # Format display fields
    from src.utils import format_paise
    for account in accounts:
        account["balance_display"] = format_paise(account.get("balance_paise", 0))
        credit_limit = account.get("credit_limit_paise", 0)
        account["credit_limit_display"] = format_paise(credit_limit) if credit_limit > 0 else None
    
    return {"accounts": accounts, "total": len(accounts)}


@router.get("/api/accounts/{account_id}")
def api_get_account(account_id: int):
    """Get a single account by ID."""
    db = get_db()
    account = db.get_account(account_id)
    
    if not account:
        raise NotFoundError("Account", account_id)
    
    # Format display fields
    from src.utils import format_paise
    account["balance_display"] = format_paise(account.get("balance_paise", 0))
    credit_limit = account.get("credit_limit_paise", 0)
    account["credit_limit_display"] = format_paise(credit_limit) if credit_limit > 0 else None
    
    return account


@router.post("/api/accounts")
def api_create_account(account_data: dict):
    """Create a new managed account."""
    db = get_db()
    
    # Map frontend field names to DB field names
    account_dict = {
        "name": account_data.get("name", ""),
        "bank_name": account_data.get("bank_name", ""),
        "account_type": account_data.get("account_type", "savings"),
        "account_number_masked": account_data.get("account_number_masked", "XXXX"),
        "balance_paise": to_paise(Decimal(str(account_data.get("balance", 0) or 0))),
        "credit_limit_paise": to_paise(Decimal(str(account_data.get("credit_limit", 0) or 0))),
        "currency": account_data.get("currency", "INR"),
        "color": account_data.get("color", "#6366F1"),
        "icon": account_data.get("icon", "building"),
    }
    
    account_id = db.create_account(account_dict)
    log.info("Account created: %s (%s)", account_dict["name"], account_dict["bank_name"])
    
    # Return the created account
    account = db.get_account(account_id)
    from src.utils import format_paise
    account["balance_display"] = format_paise(account.get("balance_paise", 0))
    credit_limit = account.get("credit_limit_paise", 0)
    account["credit_limit_display"] = format_paise(credit_limit) if credit_limit > 0 else None
    
    return account


@router.put("/api/accounts/{account_id}")
def api_update_account(account_id: int, account_data: dict):
    """Update an existing account."""
    db = get_db()
    
    # Check if account exists
    existing = db.get_account(account_id)
    if not existing:
        raise NotFoundError("Account", account_id)
    
    # Map frontend field names to DB field names
    update_dict = {}
    field_mapping = {
        "name": "name",
        "bank_name": "bank_name",
        "account_type": "account_type",
        "account_number_masked": "account_number_masked",
        "color": "color",
        "icon": "icon",
        "currency": "currency",
    }
    
    for frontend_field, db_field in field_mapping.items():
        if frontend_field in account_data:
            update_dict[db_field] = account_data[frontend_field]
    
    # Handle balance conversion (rupees to paise)
    if "balance" in account_data:
        update_dict["balance_paise"] = to_paise(Decimal(str(account_data["balance"] or 0)))

    if "credit_limit" in account_data:
        update_dict["credit_limit_paise"] = to_paise(Decimal(str(account_data["credit_limit"] or 0)))
    
    if not update_dict:
        return existing
    
    updated = db.update_account(account_id, update_dict)
    if not updated:
        raise NotFoundError("Account", account_id)
    
    log.info("Account updated: %s", account_id)
    
    # Return the updated account
    account = db.get_account(account_id)
    from src.utils import format_paise
    account["balance_display"] = format_paise(account.get("balance_paise", 0))
    credit_limit = account.get("credit_limit_paise", 0)
    account["credit_limit_display"] = format_paise(credit_limit) if credit_limit > 0 else None
    
    return account


@router.delete("/api/accounts/{account_id}")
def api_delete_account(account_id: int):
    """Soft-delete an account."""
    db = get_db()
    
    deleted = db.delete_account(account_id)
    if not deleted:
        raise NotFoundError("Account", account_id)
    
    log.info("Account deleted: %s", account_id)
    return {"success": True, "message": "Account deleted successfully"}


@router.get("/api/accounts/{account_id}/balance")
def api_get_account_balance(account_id: str):
    """Get balance for a specific account."""
    db = get_db()
    balance = compute_account_balance(db, account_id)
    return {"account_id": account_id, "balance": balance}


@router.get("/api/accounts/{account_id}/running-balance")
def api_get_running_balance(account_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Get running balance history for an account."""
    db = get_db()
    history = compute_running_balance(db, account_id)
    # Apply limit after computation
    if limit:
        history = history[:limit]
    return {"account_id": account_id, "history": history}


@router.get("/api/members")
def get_members():
    """Get all family members."""
    db = get_db()
    members = db.get_members()
    return {"members": members}


@router.post("/api/members")
def create_member(member: MemberCreate):
    """Create a new family member."""
    db = get_db()
    member_id = db.add_member(member.name, member.color)
    log.info("Member created: %s", member.name)
    return {"id": member_id, "name": member.name, "color": member.color}


@router.get("/api/banks")
def get_banks():
    """Get list of all banks."""
    db = get_db()
    banks = db.get_banks()
    return {"banks": banks}
