"""Account balance and running balance endpoints."""
from typing import Any
from fastapi import APIRouter, HTTPException, Query

from src.services.account_service import AccountService

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("")
def api_get_accounts() -> dict[str, Any]:
    """Get all accounts with their computed balances."""
    try:
        service = AccountService()
        accounts = service.get_accounts_list()
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}/balance")
def api_get_account_balance(account_id: str) -> dict[str, Any]:
    """Get current balance for a specific account."""
    try:
        service = AccountService()
        result = service.compute_account_balance(account_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}/running-balance")
def api_get_running_balance(
    account_id: str,
    limit: int = Query(1, ge=1, le=1000),
) -> dict[str, Any]:
    """Get running balance history for an account."""
    try:
        service = AccountService()
        result = service.compute_running_balance(account_id)
        return {
            "account_id": account_id,
            "transactions": result[:limit],
            "total": len(result),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
