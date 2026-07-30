"""Behaviour alert domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""

import json
from typing import Any

from src.repositories.base import BaseRepository


class AlertRepository(BaseRepository):
    """Repository for behaviour alert operations."""

    def create_alert(self, alert_data: dict[str, Any]) -> dict[str, Any] | None:
        """Create a new behaviour alert."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO behaviour_alerts (
                    alert_type, alert_code, household_id, severity, title,
                    description, action_url, is_acknowledged, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    alert_data["alert_type"],
                    alert_data["alert_code"],
                    alert_data.get("household_id", "default"),
                    alert_data["severity"],
                    alert_data["title"],
                    alert_data["description"],
                    alert_data.get("action_url"),
                    alert_data.get("is_acknowledged", 0),
                    json.dumps(alert_data.get("metadata", {})),
                ),
            )
            conn.commit()

        alert_id = cursor.lastrowid
        return self.get_alert_by_id(alert_id) if alert_id else None

    def get_alert_by_id(self, alert_id: int | str) -> dict[str, Any] | None:
        """Get a single alert by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM behaviour_alerts WHERE id = ?", (alert_id,)
            ).fetchone()

        if not row:
            return None

        return self._map_alert_row(dict(row))

    def get_active_alerts(
        self, household_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all active (unacknowledged) alerts."""
        household_id = household_id or "default"
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM behaviour_alerts
                WHERE household_id = ? AND is_acknowledged = 0
                ORDER BY
                    CASE severity
                        WHEN 'HIGH' THEN 1
                        WHEN 'MEDIUM' THEN 2
                        WHEN 'LOW' THEN 3
                        ELSE 4
                    END,
                    created_at DESC
            """,
                (household_id,),
            ).fetchall()

        return [self._map_alert_row(dict(row)) for row in rows]

    def get_alerts_by_type(
        self, alert_type: str, household_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get alerts by type."""
        household_id = household_id or "default"
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM behaviour_alerts
                WHERE household_id = ? AND alert_type = ?
                ORDER BY created_at DESC
            """,
                (household_id, alert_type),
            ).fetchall()

        return [self._map_alert_row(dict(row)) for row in rows]

    def acknowledge_alert(self, alert_id: int | str) -> bool:
        """Mark an alert as acknowledged."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE behaviour_alerts
                SET is_acknowledged = 1, acknowledged_at = datetime('now')
                WHERE id = ?
            """,
                (alert_id,),
            )
            conn.commit()
            changes_row = conn.execute("SELECT changes()").fetchone()
        return bool(changes_row[0]) if changes_row else False

    def resolve_alert(self, alert_id: int | str, resolution_notes: str) -> bool:
        """Mark an alert as resolved."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE behaviour_alerts
                SET resolved_at = datetime('now'), resolution_notes = ?
                WHERE id = ?
            """,
                (resolution_notes, alert_id),
            )
            conn.commit()
            changes_row = conn.execute("SELECT changes()").fetchone()
        return bool(changes_row[0]) if changes_row else False

    def get_alert_history(
        self, household_id: str | None = None, days: int = 90
    ) -> list[dict[str, Any]]:
        """Get historical alerts."""
        household_id = household_id or "default"
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM behaviour_alerts
                WHERE household_id = ? AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC
            """,
                (household_id, f"-{days} days"),
            ).fetchall()

        return [self._map_alert_row(dict(row)) for row in rows]

    def _map_alert_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Map database row to alert dictionary with proper typing."""
        result = {
            "id": row["id"],
            "alert_type": row["alert_type"],
            "alert_code": row["alert_code"],
            "household_id": row["household_id"],
            "severity": row["severity"],
            "title": row["title"],
            "description": row["description"],
            "action_url": row["action_url"],
            "is_acknowledged": bool(row["is_acknowledged"]),
            "acknowledged_at": row["acknowledged_at"],
            "created_at": row["created_at"],
            "resolved_at": row["resolved_at"],
            "resolution_notes": row["resolution_notes"],
        }

        # Parse JSON fields
        if row["metadata_json"]:
            try:
                result["metadata"] = json.loads(row["metadata_json"])
            except json.JSONDecodeError:
                result["metadata"] = {}

        return result
