"""Member management endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.member_service import MemberService

router = APIRouter(prefix="/api", tags=["members"])


class MemberCreate(BaseModel):
    """Member creation request."""

    name: str
    color: str = "#6366F1"


class MemberUpdate(BaseModel):
    """Member update request."""

    name: str
    color: str


@router.get("/members")
async def get_members() -> dict[str, Any]:
    """
    Get all members.

    Returns list of members who have transactions.
    """
    service = MemberService()
    return {"members": service.get_members()}


@router.get("/members/{member_id}")
async def get_member_by_id(member_id: int) -> dict[str, Any]:
    """
    Get member by ID.

    Args:
        member_id: ID of the member

    Returns:
        Member details
    """
    service = MemberService()
    member = service.get_member_by_id(member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"member": member}


@router.post("/members")
async def create_member(member: MemberCreate) -> dict[str, Any]:
    """
    Create a new member.

    Args:
        member: Member details

    Returns:
        Success message and member id
    """
    service = MemberService()
    member_id = service.create_member(member.name, member.color)
    return {"success": True, "id": member_id}


@router.put("/members/{member_id}")
async def update_member(member_id: int, member: MemberUpdate) -> dict[str, Any]:
    """
    Update member details.

    Args:
        member_id: ID of the member
        member: Updated member details

    Returns:
        Success status
    """
    service = MemberService()
    success = service.update_member(member_id, member.name, member.color)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"success": True}


@router.delete("/members/{member_id}")
async def delete_member(member_id: int) -> dict[str, Any]:
    """
    Delete member by ID.

    Args:
        member_id: ID of the member

    Returns:
        Success status
    """
    service = MemberService()
    success = service.delete_member(member_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"success": True}
