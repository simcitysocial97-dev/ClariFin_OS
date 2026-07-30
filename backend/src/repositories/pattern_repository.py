"""Behaviour pattern domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""

import json
from decimal import Decimal
from typing import Any

from src.repositories.base import BaseRepository


class PatternRepository(BaseRepository):
    """Repository for behaviour pattern operations."""

    def create_pattern(self, pattern_data: dict[str, Any]) -> dict[str, Any] | None:
        """Create a new behaviour pattern."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO behaviour_patterns (
                    pattern_type, pattern_key, household_id, strength_bps,
                    first_observed, last_observed, transaction_count,
                    total_amount_paise, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pattern_data["pattern_type"],
                    pattern_data["pattern_key"],
                    pattern_data.get("household_id", "default"),
                    pattern_data["strength_bps"],
                    pattern_data["first_observed"],
                    pattern_data["last_observed"],
                    pattern_data["transaction_count"],
                    pattern_data.get("total_amount_paise", 0),
                    json.dumps(pattern_data.get("config", {})),
                ),
            )
            conn.commit()

        pattern_id = cursor.lastrowid
        return self.get_pattern_by_id(pattern_id) if pattern_id else None

    def get_pattern_by_id(self, pattern_id: int | str) -> dict[str, Any] | None:
        """Get a single pattern by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM behaviour_patterns WHERE id = ?", (pattern_id,)
            ).fetchone()

        if not row:
            return None

        return self._map_pattern_row(dict(row))

    def get_pattern_by_key(
        self, pattern_type: str, pattern_key: str, household_id: str | None = None
    ) -> dict[str, Any] | None:
        """Get a specific behaviour pattern by key."""
        household_id = household_id or "default"
        with self._get_conn() as conn:
            row = conn.execute(
                """
                SELECT * FROM behaviour_patterns
                WHERE pattern_type = ? AND pattern_key = ? AND household_id = ?
                LIMIT 1
            """,
                (pattern_type, pattern_key, household_id),
            ).fetchone()

        if not row:
            return None

        return self._map_pattern_row(dict(row))

    def get_patterns_by_type(
        self, pattern_type: str, household_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get behaviour patterns by type."""
        household_id = household_id or "default"
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM behaviour_patterns
                WHERE household_id = ? AND pattern_type = ?
                ORDER BY strength_bps DESC, last_observed DESC
            """,
                (household_id, pattern_type),
            ).fetchall()

        return [self._map_pattern_row(dict(row)) for row in rows]

    def update_pattern_strength(
        self, pattern_id: int | str, new_strength_bps: int
    ) -> bool:
        """Update the strength of a behaviour pattern."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE behaviour_patterns
                SET strength_bps = ?, last_observed = datetime('now')
                WHERE id = ?
            """,
                (new_strength_bps, pattern_id),
            )
            conn.commit()
            changes_row = conn.execute("SELECT changes()").fetchone()
        return bool(changes_row[0]) if changes_row else False

    def get_recent_patterns(
        self, days: int = 30, household_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get recently observed behaviour patterns."""
        household_id = household_id or "default"
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM behaviour_patterns
                WHERE household_id = ? AND last_observed >= datetime('now', ?)
                ORDER BY strength_bps DESC, last_observed DESC
            """,
                (household_id, f"-{days} days"),
            ).fetchall()

        return [self._map_pattern_row(dict(row)) for row in rows]

    def get_patterns_by_strength(
        self, min_strength: float = 70.0, household_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get patterns with strength above a threshold.

        Args:
            min_strength: Minimum strength in percentage (0-100 range)
        """
        household_id = household_id or "default"
        # Convert percentage to 0-1 range for internal comparison
        min_strength_decimal = Decimal(str(min_strength)) / Decimal(100)
        min_strength_bps = self._decimal_to_bps(min_strength_decimal)
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM behaviour_patterns
                WHERE household_id = ? AND strength_bps >= ?
                ORDER BY strength_bps DESC
            """,
                (household_id, min_strength_bps),
            ).fetchall()

        return [self._map_pattern_row(dict(row)) for row in rows]

    def _map_pattern_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Map database row to pattern dictionary with proper typing."""
        result = {
            "id": row["id"],
            "pattern_type": row["pattern_type"],
            "pattern_key": row["pattern_key"],
            "household_id": row["household_id"],
            "strength": self._bps_to_decimal(row["strength_bps"]) * Decimal(100),
            "first_observed": row["first_observed"],
            "last_observed": row["last_observed"],
            "transaction_count": row["transaction_count"],
            "total_amount": Decimal(row["total_amount_paise"]) / Decimal(100),
            "created_at": row["created_at"],
        }

        # Parse JSON fields
        if row["metadata_json"]:
            try:
                result["config"] = json.loads(row["metadata_json"])
            except json.JSONDecodeError:
                result["config"] = {}

        return result

    def _bps_to_decimal(self, bps_value: int) -> Decimal:
        """Convert basis points to Decimal."""
        return Decimal(bps_value) / Decimal(10000)

    def _decimal_to_bps(self, decimal_value: Decimal) -> int:
        """Convert Decimal to basis points."""
        return int(decimal_value * Decimal(10000))
