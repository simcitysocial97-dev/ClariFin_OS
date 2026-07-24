"""Financial Event Repository - Persistence for FinancialEvent model.

LOC WATCH: No repository file > 200 LOC.
"""
import json
from typing import Any

from src.models.financial_event import FinancialEvent, LifecycleState
from src.repositories.base import BaseRepository


class FinancialEventRepository(BaseRepository):
    """Repository for FinancialEvent persistence operations.

    Handles CRUD for financial events with lifecycle state management.
    All monetary values are integer paise (₹1.00 = 100 paise).
    """

    def insert_event(self, event: FinancialEvent) -> int:
        """
        Insert a financial event record.

        Args:
            event: FinancialEvent model instance

        Returns:
            The database ID of the inserted event.
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO financial_events (
                    event_type, transaction_ids, amount_paise,
                    asset_change_paise, liability_change_paise, expense_paise, income_paise,
                    date_iso, month_bucket, account_id, counterparty_account_id,
                    category, subcategory, sub_type, provider,
                    household_id, owner_id, lifecycle_state, settled_by_event_id,
                    outstanding_paise, superseded_by,
                    confidence, confidence_bps, reviewed_by_user, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_type,
                    json.dumps(event.transaction_ids),
                    event.amount_paise,
                    event.asset_change_paise,
                    event.liability_change_paise,
                    event.expense_paise,
                    event.income_paise,
                    event.date_iso,
                    event.month_bucket or event.date_iso[:7],
                    event.account_id or "",
                    event.counterparty_account_id,
                    event.category or "",
                    event.subcategory,
                    event.sub_type,
                    event.provider,
                    event.household_id or "primary",
                    event.owner_id or "self",
                    event.lifecycle_state or "open",
                    event.settled_by_event_id,
                    event.outstanding_paise,
                    event.superseded_by,
                    event.confidence,
                    event.confidence_bps,
                    1 if event.reviewed_by_user else 0,
                    event.notes,
                    None,  # created_at - will use default from DB
                ),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def get_events_for_month(
        self,
        month_bucket: str,
        household_id: str = "primary",
        owner_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get all financial events for a given month and household.

        Args:
            month_bucket: Month in YYYY-MM format
            household_id: Household identifier (default 'primary')
            owner_id: Optional owner filter (default None = all owners)

        Returns:
            List of event dicts with all fields.
        """
        with self._get_conn() as conn:
            if owner_id:
                rows = conn.execute(
                    """
                    SELECT * FROM financial_events
                    WHERE month_bucket = ? AND household_id = ? AND owner_id = ?
                    ORDER BY date_iso DESC, id DESC
                    """,
                    (month_bucket, household_id, owner_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM financial_events
                    WHERE month_bucket = ? AND household_id = ?
                    ORDER BY date_iso DESC, id DESC
                    """,
                    (month_bucket, household_id),
                ).fetchall()
        return [dict(r) for r in rows]

    def get_open_events_for_account(self, account_id: str) -> list[dict[str, Any]]:
        """
        Get all open financial events for an account.

        Args:
            account_id: Account identifier

        Returns:
            List of open event dicts.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM financial_events
                WHERE account_id = ? AND lifecycle_state = 'open'
                ORDER BY date_iso DESC, id DESC
                """,
                (account_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def update_lifecycle(
        self,
        event_id: int,
        lifecycle_state: LifecycleState,
        outstanding_paise: int = 0,
        settled_by_event_id: int | None = None,
        actor: str = "system",
        caused_by_event_id: int | None = None,
    ) -> bool:
        """
        Update lifecycle state of an event and log the transition.

        Args:
            event_id: Database ID of the event
            lifecycle_state: New state (open, partially_settled, settled, rolls_over, superseded)
            outstanding_paise: Remaining outstanding amount after payment
            settled_by_event_id: ID of event that settled this one (optional)
            actor: Who triggered this change (default: "system")
            caused_by_event_id: ID of the settlement/repayment event that caused this transition

        Returns:
            True if updated, False if not found.
        """
        with self._get_conn() as conn:
            # Fetch current state before update
            cur = conn.execute(
                "SELECT lifecycle_state, outstanding_paise FROM financial_events WHERE id = ?",
                (event_id,),
            )
            row = cur.fetchone()
            if row is None:
                return False

            previous_state = row["lifecycle_state"]
            previous_outstanding = row["outstanding_paise"]

            # Perform the update
            conn.execute(
                """
                UPDATE financial_events
                SET lifecycle_state = ?, outstanding_paise = ?, settled_by_event_id = ?
                WHERE id = ?
                """,
                (lifecycle_state, outstanding_paise, settled_by_event_id, event_id),
            )

            # Log the lifecycle transition
            conn.execute(
                """
                INSERT INTO financial_event_lifecycle_log (
                    event_id, previous_lifecycle_state, new_lifecycle_state,
                    previous_outstanding_paise, new_outstanding_paise,
                    caused_by_event_id, actor
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    previous_state,
                    lifecycle_state,
                    previous_outstanding,
                    outstanding_paise,
                    caused_by_event_id,
                    actor,
                ),
            )

            conn.commit()
        return True

    def insert_link(
        self,
        event_id: int,
        linked_event_id: int,
        link_type: str,  # "settles" | "funds" | "rolls_over"
    ) -> int:
        """
        Create a link between two financial events.

        Args:
            event_id: Source event ID
            linked_event_id: Target event ID
            link_type: Relationship type (settles, funds, rolls_over)

        Returns:
            The database ID of the inserted link.
        """
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO financial_event_links (event_id, linked_event_id, link_type)
                VALUES (?, ?, ?)
                """,
                (event_id, linked_event_id, link_type),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def get_links_for_event(self, event_id: int) -> list[dict[str, Any]]:
        """
        Get all links originating from an event.

        Returns:
            List of link dicts with linked_event_id and link_type.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT linked_event_id, link_type, created_at
                FROM financial_event_links
                WHERE event_id = ?
                ORDER BY created_at ASC
                """,
                (event_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_events_by_type(
        self,
        event_type: str,
        household_id: str = "primary",
    ) -> list[dict[str, Any]]:
        """
        Get all events of a specific type.

        Args:
            event_type: Event type to filter by
            household_id: Household identifier

        Returns:
            List of matching event dicts.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM financial_events
                WHERE event_type = ? AND household_id = ?
                ORDER BY date_iso DESC, id DESC
                """,
                (event_type, household_id),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_open_cash_advance_events(
        self,
        household_id: str = "primary",
        owner_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get open and partially_settled credit_card_cash_advance events.

        These represent outstanding cash advance liabilities that should be
        included in debt optimization ranking.

        Args:
            household_id: Household identifier (default: "primary")
            owner_id: Optional owner filter (default None = all owners)

        Returns:
            List of cash advance event dicts with outstanding liability.
        """
        with self._get_conn() as conn:
            if owner_id:
                rows = conn.execute(
                    """
                    SELECT * FROM financial_events
                    WHERE event_type = 'credit_card_cash_advance'
                      AND household_id = ?
                      AND owner_id = ?
                      AND lifecycle_state IN ('open', 'partially_settled')
                    ORDER BY date_iso DESC, id DESC
                    """,
                    (household_id, owner_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM financial_events
                    WHERE event_type = 'credit_card_cash_advance'
                      AND household_id = ?
                      AND lifecycle_state IN ('open', 'partially_settled')
                    ORDER BY date_iso DESC, id DESC
                    """,
                    (household_id,),
                ).fetchall()
        return [dict(r) for r in rows]

    def get_lifecycle_history(
        self,
        event_id: int,
    ) -> list[dict[str, Any]]:
        """
        Get the lifecycle history for a financial event.

        Args:
            event_id: Database ID of the event

        Returns:
            List of lifecycle log entries ordered by created_at ascending.
            Each entry contains: previous_lifecycle_state, new_lifecycle_state,
            previous_outstanding_paise, new_outstanding_paise, caused_by_event_id,
            actor, created_at.
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    id, event_id, previous_lifecycle_state, new_lifecycle_state,
                    previous_outstanding_paise, new_outstanding_paise,
                    caused_by_event_id, actor, created_at
                FROM financial_event_lifecycle_log
                WHERE event_id = ?
                ORDER BY created_at ASC
                """,
                (event_id,),
            ).fetchall()
        return [dict(r) for r in rows]
