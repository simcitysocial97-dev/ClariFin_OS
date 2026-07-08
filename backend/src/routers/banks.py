"""Bank listing endpoint."""
from fastapi import APIRouter

from src.common import get_db

router = APIRouter(prefix="/api", tags=["banks"])


@router.get("/banks")
async def get_banks():
    """
    List all known banks from uploaded statements.

    Returns:
        List of unique bank names
    """
    db = get_db()
    return db.get_banks()
