"""Financial Goal domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""

from typing import Any

from src.repositories.base import BaseRepository


class FinancialGoalRepository(BaseRepository):
    """Repository for financial goal CRUD operations.

    Only handles persistence. All calculations belong to goal_planner engine.
    """

    # ============================================================
    # Goal CRUD Operations
    # ============================================================

    def create_goal(
        self,
        goal_id: str,
        household_id: str,
        goal_type: str,
        name: str,
        target_amount_paise: int,
        current_amount_paise: int = 0,
        owner_id: str | None = None,
        target_date: str | None = None,
        priority: str = "medium",
        status: str = "active",
    ) -> str:
        """Create a new financial goal record. Returns the goal ID."""
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO financial_goals (
                    id, household_id, owner_id, goal_type, name,
                    target_amount_paise, current_amount_paise, target_date,
                    priority, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
                (
                    goal_id,
                    household_id,
                    owner_id,
                    goal_type,
                    name,
                    target_amount_paise,
                    current_amount_paise,
                    target_date,
                    priority,
                    status,
                ),
            )
            conn.commit()
        return goal_id

    def get_goal(self, goal_id: str) -> dict[str, Any] | None:
        """Get a single goal by ID as a raw dict."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM financial_goals WHERE id = ?", (goal_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_household_goals(
        self,
        household_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all goals for a household.

        Args:
            household_id: Household identifier
            status: Optional filter by status (active, completed, paused)

        Returns:
            List of goal dicts sorted by priority (critical first)
        """
        with self._get_conn() as conn:
            if status:
                rows = conn.execute(
                    """
                    SELECT * FROM financial_goals
                    WHERE household_id = ? AND status = ?
                    ORDER BY
                        CASE priority
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        created_at DESC
                """,
                    (household_id, status),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM financial_goals
                    WHERE household_id = ?
                    ORDER BY
                        CASE priority
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        created_at DESC
                """,
                    (household_id,),
                ).fetchall()
        return [dict(r) for r in rows]

    def update_goal(
        self,
        goal_id: str,
        **kwargs: str | int | None,
    ) -> dict[str, Any] | None:
        """Update goal fields. Only updates provided fields."""
        allowed = {
            "name",
            "target_amount_paise",
            "current_amount_paise",
            "target_date",
            "priority",
            "status",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return self.get_goal(goal_id)

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        set_clause += ", updated_at = datetime('now')"
        values = list(updates.values()) + [goal_id]

        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE financial_goals SET {set_clause} WHERE id = ?", values
            )
            conn.commit()
        return self.get_goal(goal_id)

    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal record by ID."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM financial_goals WHERE id = ?", (goal_id,))
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False

    def count_goals_by_status(
        self,
        household_id: str,
    ) -> dict[str, int]:
        """Count goals by status for a household.

        Returns:
            Dict with counts for active, completed, on_track, at_risk
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT status, COUNT(*) as count
                FROM financial_goals
                WHERE household_id = ?
                GROUP BY status
            """,
                (household_id,),
            ).fetchall()

        counts = {"active": 0, "completed": 0, "on_track": 0, "at_risk": 0}
        for row in rows:
            status = row["status"]
            if status in counts:
                counts[status] = row["count"]

        return counts
