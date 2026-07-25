"""Account Link Repository - Persistence only.

All methods are focused solely on data persistence.
No financial calculations or business logic.
"""

import sqlite3
from typing import Any, Literal

from src.repositories.base import BaseRepository

RelationshipType = Literal["TRANSFER", "JOINT", "GUARANTOR"]


class AccountLinkRepository(BaseRepository):
    """Repository for account relationship persistence operations.

    Only handles linking/unlinking accounts.
    All intelligence belongs to account_engine.
    """

    # ============================================================
    # Account Link Operations
    # ============================================================

    def link_accounts(
        self,
        primary_account_id: str,
        linked_account_id: str,
        relationship_type: RelationshipType,
    ) -> bool:
        """Create a link between two accounts.

        Uses UNIQUE constraint to prevent duplicate relationships.
        Returns True if link was created, False if already exists.
        """
        with self._get_conn() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO account_links (
                        primary_account_id, linked_account_id, relationship_type
                    ) VALUES (?, ?, ?)
                    """,
                    (primary_account_id, linked_account_id, relationship_type),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Link already exists
                return False

    def unlink_accounts(self, primary_account_id: str, linked_account_id: str) -> bool:
        """Remove a link between two accounts."""
        with self._get_conn() as conn:
            conn.execute(
                """
                DELETE FROM account_links
                WHERE primary_account_id = ? AND linked_account_id = ?
                """,
                (primary_account_id, linked_account_id),
            )
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False

    def get_linked_accounts(self, account_id: str) -> list[dict[str, Any]]:
        """Get all accounts linked to the given account.

        Returns both primary and linked relationships.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT primary_account_id, linked_account_id, relationship_type, created_at
                FROM account_links
                WHERE primary_account_id = ? OR linked_account_id = ?
                ORDER BY created_at DESC
                """,
                (account_id, account_id),
            ).fetchall()
        return [dict(r) for r in rows]

    def relationship_exists(
        self,
        primary_account_id: str,
        linked_account_id: str,
        relationship_type: RelationshipType | None = None,
    ) -> bool:
        """Check if a specific relationship exists between accounts."""
        with self._get_conn() as conn:
            if relationship_type:
                row = conn.execute(
                    """
                    SELECT 1 FROM account_links
                    WHERE primary_account_id = ? AND linked_account_id = ?
                    AND relationship_type = ?
                    """,
                    (primary_account_id, linked_account_id, relationship_type),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT 1 FROM account_links
                    WHERE primary_account_id = ? AND linked_account_id = ?
                    """,
                    (primary_account_id, linked_account_id),
                ).fetchone()
        return row is not None
