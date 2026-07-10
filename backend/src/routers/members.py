"""Member management endpoints."""
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from src.repositories.member_repository import MemberRepository

router = APIRouter(prefix="/api", tags=["members"])


class MemberCreate(BaseModel):
    """Member creation request."""
    name: str
    color: str = "#6366F1"


@router.get("/members")
async def get_members() -> dict[str, Any]:
    """
    Get all members.

    Returns list of members who have transactions.
    """
    repo = MemberRepository()
    return {"members": repo.get_all()}


@router.post("/members")
async def create_member(member: MemberCreate) -> dict[str, Any]:
    """
    Create a new member.

    Args:
        member: Member details

    Returns:
        Success message and member id
    """
    repo = MemberRepository()
    member_id = repo.create(member.name, member.color)
    return {"success": True, "id": member_id}
