"""Bank listing endpoint."""
from fastapi import APIRouter

from src.repositories.bank_repository import BankRepository

router = APIRouter(prefix="/api", tags=["banks"])


@router.get("/banks")
async def get_banks() -> list[str]:
    """
    List all known banks from uploaded statements.

    Returns:
        List of unique bank names
    """
    repo = BankRepository()
    return repo.get_all()
