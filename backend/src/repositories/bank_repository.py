"""Bank domain repository."""

from typing import Any

from src.repositories.base import BaseRepository


class BankRepository(BaseRepository):
    """Repository for bank-related operations."""

    def get_all(self) -> list[str]:
        """Get all distinct bank names."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT DISTINCT bank FROM statements ORDER BY bank")
            rows = [row[0] for row in cur.fetchall()]
        return rows

    def get_by_id(self, bank_id: int) -> dict[str, Any] | None:
        """Get bank details by ID."""
        with self._get_conn() as conn:
            cur = conn.execute("SELECT * FROM banks WHERE id = ?", (bank_id,))
            row = cur.fetchone()
            if row:
                return dict(row)
        return None

    def create(
        self, name: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create a new bank record."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO banks (name, metadata) VALUES (?, ?)",
                (name, metadata if metadata else {}),
            )
            conn.commit()
            lastrowid = cur.lastrowid
            if lastrowid is None:
                raise ValueError("Failed to create bank record")
            result = self.get_by_id(lastrowid)
            if result is None:
                raise ValueError("Failed to retrieve created bank record")
            return result

    def update(
        self,
        bank_id: int,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Update bank details."""
        with self._get_conn() as conn:
            if name is not None:
                conn.execute("UPDATE banks SET name = ? WHERE id = ?", (name, bank_id))
            if metadata is not None:
                conn.execute(
                    "UPDATE banks SET metadata = ? WHERE id = ?", (metadata, bank_id)
                )
            conn.commit()
            return self.get_by_id(bank_id)

    def delete(self, bank_id: int) -> bool:
        """Delete a bank record."""
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM banks WHERE id = ?", (bank_id,))
            conn.commit()
            return cur.rowcount > 0
