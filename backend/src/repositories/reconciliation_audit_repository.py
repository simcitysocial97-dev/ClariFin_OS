"""Reconciliation audit log repository.

Tracks all actions (confirm, reject, modify, split, undo) performed on
reconciliation records for full traceability.

LOC WATCH: No repository file > 200 LOC.
"""
from typing import Any

from src.repositories.base import BaseRepository


class ReconciliationAuditRepository(BaseRepository):
    """Repository for reconciliation audit log operations."""

    def insert_audit_log(
        self,
        reconciliation_id: int,
        action: str,
        actor: str,
        reason: str | None = None,
        previous_state: str | None = None,
        new_state: str | None = None,
    ) -> int | None:
        """Record an action on a reconciliation.

        Args:
            reconciliation_id: FK to reconciliations.id
            action: One of 'confirm', 'reject', 'modify', 'split', 'undo'
            actor: Identifier of the user or system that performed the action
            reason: Optional explanation for the action
            previous_state: JSON snapshot of the reconciliation before the action
            new_state: JSON snapshot of the reconciliation after the action

        Returns:
            The new audit log entry ID, or None if the FK constraint failed
            (reconciliation_id does not exist).
        """
        with self._get_conn() as conn:
            try:
                cur = conn.execute(
                    """
                    INSERT INTO reconciliation_audit_log
                        (reconciliation_id, action, actor, reason,
                         previous_state, new_state)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        reconciliation_id,
                        action,
                        actor,
                        reason,
                        previous_state,
                        new_state,
                    ),
                )
                conn.commit()
                return cur.lastrowid
            except Exception:
                # FK violation or other constraint error
                return None

    def get_audit_trail(
        self, reconciliation_id: int
    ) -> list[dict[str, Any]]:
        """Retrieve all audit log entries for a reconciliation, oldest first.

        Args:
            reconciliation_id: The reconciliation to look up.

        Returns:
            List of audit log entry dicts, ordered by timestamp ascending.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, reconciliation_id, action, actor, timestamp,
                       reason, previous_state, new_state
                FROM reconciliation_audit_log
                WHERE reconciliation_id = ?
                ORDER BY timestamp ASC
                """,
                (reconciliation_id,),
            ).fetchall()
        return [dict(r) for r in rows]
