"""Net worth endpoint."""
from fastapi import APIRouter

from src.models.explanation import NetWorthResponse
from src.services import NetWorthService

router = APIRouter(prefix="/api", tags=["networth"])


@router.get("/networth", response_model=NetWorthResponse)
def get_networth() -> NetWorthResponse:
    """
    Compute net worth from all financial data.

    Net Worth = Assets - Liabilities
    Assets = account balances + investment current values
    Liabilities = loan outstanding + card outstanding

    Returns:
        {
            net_worth_paise: int,
            assets: {...},
            liabilities: {...},
            is_partial: bool,
            partial_reason: str | None,
            explanation: NetWorthExplanation
        }
    """
    service = NetWorthService()
    return service.calculate_with_explanation()
