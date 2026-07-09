"""Import mapping domain repository."""
from typing import Any
from src.repositories.base import BaseRepository


class ImportMappingRepository(BaseRepository):
    """Repository for import mapping operations."""

    def save(self, mapping: dict[str, Any]) -> int:
        """Save a column mapping configuration for reuse."""
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO import_mappings
                    (mapping_name, date_column, description_column, amount_column,
                     type_column, debit_value, credit_value, date_format, skip_rows)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mapping.get("mapping_name", "Unnamed"),
                    mapping.get("date_column"),
                    mapping.get("description_column"),
                    mapping.get("amount_column"),
                    mapping.get("type_column"),
                    mapping.get("debit_value", "DR"),
                    mapping.get("credit_value", "CR"),
                    mapping.get("date_format", "%d/%m/%Y"),
                    mapping.get("skip_rows", 0),
                ),
            )
            conn.commit()
        return cur.lastrowid or 0

    def get_all(self) -> list[dict]:
        """Get all saved import mappings."""
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT id, mapping_name, date_column, description_column, amount_column,
                       type_column, debit_value, credit_value, date_format, skip_rows, created_at
                FROM import_mappings
                ORDER BY created_at DESC
            """)
            rows = [dict(row) for row in cur.fetchall()]
        return rows
