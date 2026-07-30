"""Accounts Intelligence Router - Stage 4 Accounts Intelligence Workspace.

API endpoints for accounts data with full explainability support.
All monetary values in paise (integer).
"""

from typing import Any

from fastapi import APIRouter, Query

from src.core.dtos.accounts_dto import (
    AccountDetailDTO,
    AccountsDTO,
    AccountsHistoryResponse,
    AccountsTransactionsResponse,
)
from src.services import AccountsService

router = APIRouter(prefix="/api/v1", tags=["accounts-intelligence"])


@router.get("/accounts")
def get_accounts(
    account_types: str | None = Query(
        default=None, description="Comma-separated account types"
    ),
    institutions: str | None = Query(
        default=None, description="Comma-separated institutions"
    ),
    statuses: str | None = Query(default=None, description="Comma-separated statuses"),
) -> AccountsDTO:
    """
    Get all accounts with optional filtering.

    Returns accounts list, total balance, type breakdown, and insights.
    All monetary values in paise (integer).
    """
    service = AccountsService()

    # Parse comma-separated filters
    type_list = account_types.split(",") if account_types else None
    inst_list = institutions.split(",") if institutions else None
    status_list = statuses.split(",") if statuses else None

    return service.get_accounts(
        account_types=type_list,
        institutions=inst_list,
        statuses=status_list,
    )


@router.get("/accounts/{account_id}")
def get_account(account_id: int | str) -> AccountDetailDTO:
    """
    Get detailed information for a single account.

    Returns account details including balance and status.
    All monetary values in paise (integer).
    """
    service = AccountsService()
    result = service.get_account_detail(account_id)
    if not result:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return result


@router.get("/accounts/{account_id}/transactions")
def get_account_transactions(
    account_id: int | str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AccountsTransactionsResponse:
    """
    Get transactions for a specific account.

    Returns paginated transaction list.
    All monetary values in paise (integer).
    """
    service = AccountsService()
    return service.get_transactions(account_id=account_id, limit=limit, offset=offset)


@router.get("/accounts/{account_id}/balance-history")
def get_account_balance_history(
    account_id: int | str,
    limit: int = Query(default=90, ge=1, le=365),
) -> AccountsHistoryResponse:
    """
    Get balance history for an account.

    Returns balance history entries.
    All monetary values in paise (integer).
    """
    service = AccountsService()
    return service.get_balance_history(account_id, limit)


@router.get("/accounts/summary")
def get_accounts_summary() -> AccountsDTO:
    """
    Get accounts summary with all accounts.

    Returns summary data including total balance and type breakdown.
    All monetary values in paise (integer).
    """
    service = AccountsService()
    return service.get_summary()


@router.get("/accounts/type-breakdown")
def get_accounts_type_breakdown() -> list[dict[str, Any]]:
    """
    Get account type breakdown for analytics.

    Returns type distribution with counts and balances.
    All monetary values in paise (integer).
    """
    service = AccountsService()
    return [b.model_dump() for b in service.get_type_breakdown()]
