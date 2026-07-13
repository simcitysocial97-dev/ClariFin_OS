"""Reconciliation domain repository.

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""
from typing import Any

from src.models.reconciliation import Reconciliation
from src.repositories.base import BaseRepository


class ReconciliationRepository(BaseRepository):
    """Repository for reconciliation operations.

    DEPRECATED:
        match_confidence (REAL) is retained only for backward compatibility.
        confidence_bps (INTEGER basis points) is the authoritative confidence field.
        All new writes must populate both fields until match_confidence is removed.
    """

    def get_all_models(self) -> list[Reconciliation]:
        """
        Return all reconciliations as Reconciliation domain models.

        The `amount_paise` column stores integer paise (₹1.00 = 100).
        Handles backward compatibility for legacy databases with `amount REAL`.
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT id, debit_txn_id, credit_txn_id,
                       debit_account_id, credit_account_id,
                       COALESCE(amount_paise, CAST(amount AS INTEGER)) as amount_paise,
                       date_diff_days,
                       match_confidence, match_type, status
                FROM reconciliations
                ORDER BY created_at DESC
            """).fetchall()
        return [Reconciliation.from_db_row(dict(r)) for r in rows]

    def get_reconciliations(self, status: str | None = None) -> list[dict[str, Any]]:
        """
        Get all reconciliations with transaction details.

        Args:
            status: Optional filter by status ('pending', 'confirmed', 'rejected')

        Returns:
            List of reconciliation records with transaction details including bank names
        """
        with self._get_conn() as conn:
            where_clause = "WHERE r.status = ?" if status else ""
            params = [status] if status else []

            sql = f"""
                SELECT
                    r.id,
                    r.debit_txn_id, r.credit_txn_id,
                    r.debit_account_id, r.credit_account_id,
                    r.amount_paise,
                    r.date_diff_days,
                    r.match_confidence, r.match_type,
                    r.status, r.deterministic_key,
                    r.created_at, r.confirmed_at,
                    dt.date as debit_date, dt.date_iso as debit_date_iso,
                    dt.description as debit_description, dt.debit as debit_amount_paise,
                    dt.account_id as debit_bank,
                    ct.date as credit_date, ct.date_iso as credit_date_iso,
                    ct.description as credit_description, ct.credit as credit_amount_paise,
                    ct.account_id as credit_bank
                FROM reconciliations r
                JOIN transactions dt ON r.debit_txn_id = dt.id
                JOIN transactions ct ON r.credit_txn_id = ct.id
                {where_clause}
                ORDER BY r.created_at DESC
            """

            cur = conn.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def get_pending_reconciliations(self) -> list[dict[str, Any]]:
        """Get all pending reconciliations."""
        return self.get_reconciliations(status='pending')

    def insert_reconciliation(
        self,
        debit_txn_id: int,
        credit_txn_id: int,
        debit_account_id: str,
        credit_account_id: str,
        amount: float,
        date_diff_days: int = 0,
        match_confidence: float = 0.0,
        match_type: str = "exact",
        confidence_bps: int | None = None,
    ) -> bool:
        """
        Create a reconciliation record between two transactions.

        Phase 2B: Metadata-only, no ledger mutation.
        Uses INSERT OR IGNORE for idempotency.

        Args:
            confidence_bps: INTEGER basis points (0.0-1.0 * 10000).
                           If None, derived from match_confidence.

        Returns:
            True if inserted, False if already exists (ignored)
        """
        with self._get_conn() as conn:
            # Generate deterministic key (smaller id first for consistency)
            min_id = min(debit_txn_id, credit_txn_id)
            max_id = max(debit_txn_id, credit_txn_id)
            deterministic_key = f"{min_id}:{max_id}"

            # Compute confidence_bps if not provided
            if confidence_bps is None:
                confidence_bps = int(round(match_confidence * 10000))

            # Check if confidence_bps column exists
            has_confidence_bps = False
            col_info = conn.execute("PRAGMA table_info(reconciliations)").fetchall()
            for col in col_info:
                if col[1] == "confidence_bps":
                    has_confidence_bps = True
                    break

            if has_confidence_bps:
                # Use INSERT OR IGNORE for idempotency
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO reconciliations (
                        debit_txn_id, credit_txn_id,
                        debit_account_id, credit_account_id,
                        amount_paise, date_diff_days,
                        match_confidence, match_type,
                        deterministic_key, confidence_bps
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        debit_txn_id, credit_txn_id,
                        debit_account_id, credit_account_id,
                        int(round(amount * 100)), date_diff_days,
                        round(match_confidence, 4), match_type,
                        deterministic_key, confidence_bps
                    ),
                )
            else:
                # Legacy insert without confidence_bps
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO reconciliations (
                        debit_txn_id, credit_txn_id,
                        debit_account_id, credit_account_id,
                        amount_paise, date_diff_days,
                        match_confidence, match_type,
                        deterministic_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        debit_txn_id, credit_txn_id,
                        debit_account_id, credit_account_id,
                        int(round(amount * 100)), date_diff_days,
                        round(match_confidence, 4), match_type,
                        deterministic_key
                    ),
                )

            conn.commit()
            inserted = cur.rowcount > 0
        return inserted

    def confirm_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Confirm a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                UPDATE reconciliations
                SET status = 'confirmed', confirmed_at = datetime('now')
                WHERE id = ? AND status = 'pending'
                """,
                (reconciliation_id,),
            )
            updated = cur.rowcount > 0
        return updated

    def reject_reconciliation(self, reconciliation_id: int) -> bool:
        """
        Reject a pending reconciliation.

        Phase 2B: Updates reconciliation.status only. No ledger mutation.

        Returns:
            True if updated, False if not found or not pending
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                UPDATE reconciliations
                SET status = 'rejected'
                WHERE id = ? AND status = 'pending'
                """,
                (reconciliation_id,),
            )
            updated = cur.rowcount > 0
        return updated

    def get_confirmed_transfer_ids(self) -> list[tuple[int, int]]:
        """
        Get all transaction IDs involved in confirmed transfers.

        Returns list of (debit_txn_id, credit_txn_id) tuples for confirmed reconciliations.
        Used by analytics to exclude transfers from spending totals.
        """
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT debit_txn_id, credit_txn_id
                FROM reconciliations
                WHERE status = 'confirmed'
            """)
            rows = [(row[0], row[1]) for row in cur.fetchall()]
        return rows

    # ============================================================
    # Phase 3: Unreconciled Transaction Fetching
    # ============================================================

    def get_unreconciled_debits(self, household_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get all debit transactions not yet confirmed in a reconciliation.

        Returns transaction dicts with: id, account_id, date_iso, amount_paise,
        debit, credit, description.

        Args:
            household_id: If provided, filter by household (uses account_id as account key).
        """
        confirmed_ids = self.get_confirmed_transfer_ids()
        confirmed_debit_ids = {d for d, _ in confirmed_ids}

        with self._get_conn() as conn:
            if household_id:
                # Filter by accounts in the household
                rows = conn.execute("""
                    SELECT t.id, t.account_id, t.date_iso, t.amount_paise,
                           t.debit, t.credit, t.description
                    FROM transactions t
                    JOIN accounts a ON t.account_id = a.bank
                    WHERE t.id NOT IN ({})
                      AND t.debit > 0
                      AND t.account_id IS NOT NULL AND t.account_id != ''
                      AND t.date_iso IS NOT NULL AND t.date_iso != ''
                      AND a.household_id = ?
                    ORDER BY t.amount_paise ASC, t.date_iso ASC, t.id ASC
                """.format(
                    ",".join("?" for _ in confirmed_debit_ids) if confirmed_debit_ids else "NULL"
                ), list(confirmed_debit_ids) + [household_id]).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, account_id, date_iso, amount_paise,
                           debit, credit, description
                    FROM transactions
                    WHERE id NOT IN ({})
                      AND debit > 0
                      AND account_id IS NOT NULL AND account_id != ''
                      AND date_iso IS NOT NULL AND date_iso != ''
                    ORDER BY amount_paise ASC, date_iso ASC, id ASC
                """.format(
                    ",".join("?" for _ in confirmed_debit_ids) if confirmed_debit_ids else "NULL"
                ), list(confirmed_debit_ids)).fetchall()
        return [dict(row) for row in rows]

    def get_unreconciled_credits(self, household_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get all credit transactions not yet confirmed in a reconciliation.

        Returns transaction dicts with: id, account_id, date_iso, amount_paise,
        debit, credit, description.

        Args:
            household_id: If provided, filter by household (uses account_id as account key).
        """
        confirmed_ids = self.get_confirmed_transfer_ids()
        confirmed_credit_ids = {c for _, c in confirmed_ids}

        with self._get_conn() as conn:
            if household_id:
                rows = conn.execute("""
                    SELECT t.id, t.account_id, t.date_iso, t.amount_paise,
                           t.debit, t.credit, t.description
                    FROM transactions t
                    JOIN accounts a ON t.account_id = a.bank
                    WHERE t.id NOT IN ({})
                      AND t.credit > 0
                      AND t.account_id IS NOT NULL AND t.account_id != ''
                      AND t.date_iso IS NOT NULL AND t.date_iso != ''
                      AND a.household_id = ?
                    ORDER BY t.amount_paise ASC, t.date_iso ASC, t.id ASC
                """.format(
                    ",".join("?" for _ in confirmed_credit_ids) if confirmed_credit_ids else "NULL"
                ), list(confirmed_credit_ids) + [household_id]).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, account_id, date_iso, amount_paise,
                           debit, credit, description
                    FROM transactions
                    WHERE id NOT IN ({})
                      AND credit > 0
                      AND account_id IS NOT NULL AND account_id != ''
                      AND date_iso IS NOT NULL AND date_iso != ''
                    ORDER BY amount_paise ASC, date_iso ASC, id ASC
                """.format(
                    ",".join("?" for _ in confirmed_credit_ids) if confirmed_credit_ids else "NULL"
                ), list(confirmed_credit_ids)).fetchall()
        return [dict(row) for row in rows]

    # ============================================================
    # Phase 3: Audit Log Methods
    # ============================================================

    def insert_audit_log(
        self,
        reconciliation_id: int,
        action: str,
        actor: str = "system",
        reason: str | None = None,
        previous_state: str | None = None,
        new_state: str | None = None,
    ) -> None:
        """
        Insert an audit log entry for reconciliation actions.

        Args:
            reconciliation_id: ID of the reconciliation record.
            action: Action type ('confirm', 'reject', 'undo', 'insert').
            actor: Who performed the action ('system' or username).
            reason: Optional reason for the action.
            previous_state: JSON snapshot of record before change.
            new_state: JSON snapshot of record after change.
        """
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO reconciliation_audit_log (
                    reconciliation_id, action, actor, reason,
                    previous_state, new_state
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (reconciliation_id, action, actor, reason, previous_state, new_state),
            )
            conn.commit()

    def _get_reconciliation_row(self, reconciliation_id: int) -> dict[str, Any] | None:
        """Get a reconciliation row by ID for audit purposes."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM reconciliations WHERE id = ?",
                (reconciliation_id,),
            ).fetchone()
        return dict(row) if row else None

    # ============================================================
    # Phase 3: Undo Reconciliation
    # ============================================================

    # Configurable undo policy: reconciliations confirmed in different months cannot be undone
    UNDO_MONTH_BOUNDARY_LOCK: bool = True  # Set False to allow cross-month undo

    def undo_reconciliation(self, reconciliation_id: int, actor: str = "system") -> bool:
        """
        Revert a confirmed reconciliation back to pending status.

        Phase 3: Only allowed if the reconciliation was confirmed in the current month.
        Logs an 'undo' audit action on success.

        Returns:
            True if undone, False if not found, not confirmed, or blocked by month boundary.
        """
        import json
        from datetime import datetime

        # Get the current reconciliation state
        current = self._get_reconciliation_row(reconciliation_id)
        if not current:
            return False

        if current.get("status") != "confirmed":
            return False

        # Check month boundary lock
        if self.UNDO_MONTH_BOUNDARY_LOCK:
            confirmed_at = current.get("confirmed_at")
            if confirmed_at:
                try:
                    confirmed_month = datetime.strptime(confirmed_at[:7], "%Y-%m")
                    current_month = datetime.now().replace(day=1)
                    if confirmed_month.year != current_month.year or \
                       confirmed_month.month != current_month.month:
                        # Cross-month undo blocked
                        return False
                except (ValueError, TypeError):
                    pass  # If date parsing fails, allow the undo

        # Log the audit entry before change
        previous_state = json.dumps({
            "id": current.get("id"),
            "status": current.get("status"),
            "confirmed_at": current.get("confirmed_at"),
        })

        # Revert to pending
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE reconciliations SET status = 'pending', confirmed_at = NULL WHERE id = ?",
                (reconciliation_id,),
            )
            updated = cur.rowcount > 0
            conn.commit()

        if updated:
            self.insert_audit_log(
                reconciliation_id=reconciliation_id,
                action="undo",
                actor=actor,
                previous_state=previous_state,
                new_state=json.dumps({"id": reconciliation_id, "status": "pending"}),
            )
        return updated
