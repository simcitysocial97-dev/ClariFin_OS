"""Managed accounts endpoints (DB-backed)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.errors import NotFoundError
from src.repositories import AccountRepository

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
def api_get_managed_accounts() -> dict:
    """Get all persistently stored accounts."""
    try:
        repo = AccountRepository()
        accounts = repo.get_all_accounts()
        return {"accounts": accounts, "total": len(accounts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accounts/manage")
def api_create_managed_account(account: AccountCreate) -> dict:
    """Create a new persistent account."""
    try:
        repo = AccountRepository()
        created = repo.create_account(
            name=account.name,
            bank=account.bank,
            account_type=account.account_type,
            balance_paise=account.balance_paise,
            account_number_last4=account.account_number_last4,
            notes=account.notes
        )
        return {"success": True, "account": created}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/accounts/manage/{account_id}")
def api_update_managed_account(account_id: str, account: AccountUpdate) -> dict:
    """Update an existing account."""
    try:
        repo = AccountRepository()
        updated = repo.update_account(
            account_id,
            **{k: v for k, v in account.model_dump().items() if v is not None}
        )
        if not updated:
            raise NotFoundError(f"Account {account_id} not found")
        return {"success": True, "account": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/accounts/manage/{account_id}")
def api_delete_managed_account(account_id: str) -> dict:
    """Soft delete an account."""
    try:
        repo = AccountRepository()
        success = repo.delete_account(account_id)
        if not success:
            raise NotFoundError(f"Account {account_id} not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/balance")
def api_get_account_balance(account_id: str) -> dict:
    """Get computed balance for an account."""
    try:
        repo = AccountRepository()
        balance = repo.compute_account_balance(account_id)
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
