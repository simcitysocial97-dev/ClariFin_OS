"""Member business logic service."""

from typing import Any

from src.repositories.member_repository import MemberRepository
from src.services.base import BaseService


class MemberService(BaseService):
    """Service for member-related business logic."""

    def __init__(self) -> None:
        super().__init__(repository=MemberRepository())

    def get_members(self) -> list[dict[str, Any]]:
        """Return all members."""
        assert self.repository is not None
        return self.repository.get_all()  # type: ignore[attr-defined,no-any-return]

    def get_member_by_id(self, member_id: int) -> dict[str, Any] | None:
        """Return member by ID."""
        assert self.repository is not None
        with self.repository._get_conn() as conn:
            cur = conn.execute(
                "SELECT id, name, color, created_at FROM members WHERE id = ?",
                (member_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def create_member(self, name: str, color: str = "#6366F1") -> int:
        """Create a new member. Return member ID."""
        assert self.repository is not None
        return self.repository.create(name, color)  # type: ignore[attr-defined,no-any-return]

    def update_member(self, member_id: int, name: str, color: str) -> bool:
        """Update member details. Return success status."""
        assert self.repository is not None
        with self.repository._get_conn() as conn:
            cur = conn.execute(
                "UPDATE members SET name = ?, color = ? WHERE id = ?",
                (name, color, member_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def delete_member(self, member_id: int) -> bool:
        """Delete member by ID. Return success status."""
        assert self.repository is not None
        with self.repository._get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM members WHERE id = ?",
                (member_id,),
            )
            conn.commit()
            return cur.rowcount > 0
