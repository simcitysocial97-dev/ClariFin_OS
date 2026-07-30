"""Institution domain repository - Persistence only.

All methods are focused solely on data persistence.
No financial calculations or business logic.
Reference data only.
"""

from typing import Any, Literal

from src.repositories.base import BaseRepository

InstitutionType = Literal["BANK", "WALLET", "BROKER", "OTHER"]


class InstitutionRepository(BaseRepository):
    """Repository for institution reference data persistence operations.

    Only handles CRUD for institutions.
    All financial intelligence belongs to account_engine.
    """

    # ============================================================
    # Institution CRUD Operations
    # ============================================================

    def create(
        self,
        institution_id: str,
        name: str,
        institution_type: InstitutionType,
        interest_rate_bps: int | None = None,
        supported_features_json: str | None = None,
    ) -> str:
        """Create a new institution record.

        Returns the institution_id.
        Handles duplicates gracefully using INSERT OR IGNORE.
        """
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO institutions (
                    institution_id, name, type, interest_rate_bps, supported_features_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    institution_id,
                    name,
                    institution_type,
                    interest_rate_bps,
                    supported_features_json,
                ),
            )
            conn.commit()
        return institution_id

    def get(self, institution_id: str) -> dict[str, Any] | None:
        """Get an institution by ID as a raw dict."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM institutions WHERE institution_id = ?",
                (institution_id,),
            ).fetchone()
        return dict(row) if row else None

    def list(self) -> list[dict[str, Any]]:
        """Get all institutions as raw dicts."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM institutions ORDER BY name").fetchall()
        return [dict(r) for r in rows]

    def update(
        self,
        institution_id: str,
        name: str | None = None,
        institution_type: InstitutionType | None = None,
        interest_rate_bps: int | None = None,
        supported_features_json: str | None = None,
    ) -> dict[str, Any] | None:
        """Update institution fields. Only updates provided fields."""
        updates = {
            k: v
            for k, v in {
                "name": name,
                "type": institution_type,
                "interest_rate_bps": interest_rate_bps,
                "supported_features_json": supported_features_json,
            }.items()
            if v is not None
        }

        if not updates:
            return self.get(institution_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values()) + [institution_id]

        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE institutions SET {set_clause} WHERE institution_id = ?",
                values,
            )
            conn.commit()
        return self.get(institution_id)

    def delete(self, institution_id: str) -> bool:
        """Delete an institution record by ID."""
        with self._get_conn() as conn:
            conn.execute(
                "DELETE FROM institutions WHERE institution_id = ?",
                (institution_id,),
            )
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False
