"""Net worth endpoint."""
from fastapi import APIRouter

from src.services import NetWorthService

router = APIRouter(prefix="/api", tags=["networth"])


@router.get("/networth")
def get_networth() -> dict:
    """
    Compute net worth from all financial data.

    Net Worth = Assets - Liabilities
    Assets = account balances + investment current values
    Liabilities = loan outstanding + card outstanding
    """
    service = NetWorthService()
    return service.calculate()
