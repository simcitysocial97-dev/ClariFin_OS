"""Bank domain repository."""
from src.repositories.base import BaseRepository


class BankRepository(BaseRepository):
    """Repository for bank-related operations."""

    def get_all(self) -> list[str]:
        """Get all distinct bank names."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT DISTINCT bank FROM statements ORDER BY bank")
            rows = [row[0] for row in cur.fetchall()]
        return rows
