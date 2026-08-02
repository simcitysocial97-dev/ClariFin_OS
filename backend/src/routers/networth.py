"""Net worth endpoint."""

from fastapi import APIRouter

from src.core.dtos.net_worth_dto import NetWorthDTO
from src.services import NetWorthService

router = APIRouter(prefix="/api", tags=["networth"])


@router.get("/networth", response_model=NetWorthDTO)
def get_networth() -> NetWorthDTO:
    """
    Compute net worth from all financial data.

    Net Worth = Assets - Liabilities
    Assets = account balances + investment current values
    Liabilities = loan outstanding + card outstanding
    """
    service = NetWorthService()
    return service.calculate()
