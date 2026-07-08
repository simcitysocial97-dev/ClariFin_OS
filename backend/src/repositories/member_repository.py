"""Member domain repository."""
from src.repositories.base import BaseRepository


class MemberRepository(BaseRepository):
    """Repository for member-related operations."""

    def get_all(self) -> list[dict]:
        """Return all members as list of dicts."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT id, name, color, created_at FROM members ORDER BY name")
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def create(self, name: str, color: str = "#6366F1") -> int:
        """Add new family member. Return id."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO members (name, color) VALUES (?, ?)",
                (name, color),
            )
            conn.commit()
        return cur.lastrowid or 0