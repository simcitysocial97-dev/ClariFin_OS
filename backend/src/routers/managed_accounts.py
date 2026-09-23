"""Managed accounts endpoints (DB-backed)."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from src.errors import NotFoundError
from src.services.account_service import AccountService

router = APIRouter(prefix="/api", tags=["accounts"])


class AccountCreate(BaseModel):
    """Account creation request."""

    name: str
    bank: str
    account_type: str = "savings"
    balance_paise: int
    account_number_last4: str | None = None
    notes: str | None = None


class AccountUpdate(BaseModel):
    """Account update request."""

    name: str | None = None
    bank: str | None = None
    account_type: str | None = None
    balance_paise: int | None = None
    account_number_last4: str | None = None
    notes: str | None = None


@router.get("/accounts/manage")
def api_get_managed_accounts() -> dict[str, Any]:
    """Get all persistently stored accounts."""
    service = AccountService()
    accounts = service.list_accounts()
    return {"accounts": accounts, "total": len(accounts)}


@router.post("/accounts/manage")
def api_create_managed_account(account: AccountCreate) -> dict[str, Any]:
    """Create a new persistent account."""
    service = AccountService()
    created = service.create_account(
        name=account.name,
        bank=account.bank,
        account_type=account.account_type,
        balance_paise=account.balance_paise,
        account_number_last4=account.account_number_last4,
        notes=account.notes,
    )
    return {"success": True, "account": created}


@router.put("/accounts/manage/{account_id}")
def api_update_managed_account(
    account_id: str, account: AccountUpdate
) -> dict[str, Any]:
    """Update an existing account."""
    service = AccountService()
    updated = service.update_account(
        account_id,
        **{k: v for k, v in account.model_dump().items() if v is not None},
    )
    if not updated:
        raise NotFoundError(f"Account {account_id} not found")
    return {"success": True, "account": updated}


@router.delete("/accounts/manage/{account_id}")
def api_delete_managed_account(account_id: str) -> dict[str, Any]:
    """Soft delete an account."""
    service = AccountService()
    success = service.deactivate_account(account_id)
    if not success:
        raise NotFoundError(f"Account {account_id} not found")
    return {"success": True}


@router.get("/accounts/{account_id}/balance")
def api_get_account_balance(account_id: str) -> dict[str, Any]:
    """Get computed balance for an account."""
    service = AccountService()
    balance = service.compute_account_balance(account_id)
    return balance


@router.get("/accounts/{account_id}/running-balance")
def api_get_account_running_balance(account_id: str) -> list[dict[str, Any]]:
    """Get running balance for an account."""
    service = AccountService()
    running = service.compute_running_balance(account_id)
    return running
