"""Member management endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

from src.common import get_db

router = APIRouter(prefix="/api", tags=["members"])


class MemberCreate(BaseModel):
    """Member creation request."""
    name: str
    color: str = "#6366F1"


@router.get("/members")
async def get_members():
    """
    Get all members.

    Returns list of members who have transactions.
    """
    db = get_db()
    return {"members": db.get_members()}


@router.post("/members")
async def create_member(member: MemberCreate):
    """
    Create a new member.

    Args:
        member: Member details

    Returns:
        Success message and member id
    """
    db = get_db()
    member_id = db.add_member(member.name, member.color)
    return {"success": True, "id": member_id}
