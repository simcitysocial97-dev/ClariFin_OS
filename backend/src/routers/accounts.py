"""Account balance and running balance endpoints."""
from fastapi import APIRouter, HTTPException, Query

from src.repositories import AccountRepository

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("")
def api_get_accounts():
    """Get all accounts with their computed balances."""
    try:
        repo = AccountRepository()
        accounts = repo.get_accounts_list()
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}/balance")
def api_get_account_balance(account_id: str):
    """Get current balance for a specific account."""
    try:
        repo = AccountRepository()
        result = repo.compute_account_balance(account_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}/running-balance")
def api_get_running_balance(account_id: str, limit: int = Query(1, ge=1, le=1000)):
    """Get running balance history for an account."""
    try:
        repo = AccountRepository()
        result = repo.compute_running_balance(account_id)
        # Return limited results
        return {
            "account_id": account_id,
            "transactions": result[:limit],
            "total": len(result),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
