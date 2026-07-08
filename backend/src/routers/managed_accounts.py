"""Managed accounts endpoints (DB-backed)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import FinanceDB
from errors import NotFoundError

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
def api_get_managed_accounts():
    """Get all persistently stored accounts."""
    try:
        with FinanceDB() as db:
            accounts = db.get_all_accounts()
            return {"accounts": accounts, "total": len(accounts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accounts/manage")
def api_create_managed_account(account: AccountCreate):
    """Create a new persistent account."""
    try:
        with FinanceDB() as db:
            created = db.create_account(
                account_id=0,  # Will use auto-increment
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
def api_update_managed_account(account_id: str, account: AccountUpdate):
    """Update an existing account."""
    try:
        with FinanceDB() as db:
            updated = db.update_account(
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
def api_delete_managed_account(account_id: str):
    """Soft delete an account."""
    try:
        with FinanceDB() as db:
            success = db.delete_account(account_id)
            if not success:
                raise NotFoundError(f"Account {account_id} not found")
            return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
