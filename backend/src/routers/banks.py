"""Bank listing endpoint."""

from fastapi import APIRouter

from src.services.bank_service import BankService

router = APIRouter(prefix="/api", tags=["banks"])


@router.get("/banks")
async def get_banks() -> list[str]:
    """
    List all known banks from uploaded statements.

    Returns:
        List of unique bank names
    """
    service = BankService()
    return service.get_banks()
