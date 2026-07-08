"""Member domain repository."""
from src.repositories.base import BaseRepository


class MemberRepository(BaseRepository):
    """Repository for member-related operations."""

    def get_all(self):
        """Get all members."""
        return self._db().get_members()

    def create(self, name: str, color: str = "#6366F1"):
        """Create a new member."""
        return self._db().add_member(name, color)
