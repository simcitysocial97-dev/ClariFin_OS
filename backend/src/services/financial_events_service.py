"""Financial Events Service - Orchestration layer for event lifecycle management.

Coordinates event creation, lineage walking, and persistence.
No DB access in engines - this layer handles all database writes.
"""
import json
from typing import Any

from src.engines.financial_events.lineage_walker import (
    DEFAULT_ROLLOVER_LOOKBACK_DAYS,
    walk_lineage,
)
from src.models.financial_event import FinancialEvent
from src.repositories.financial_event_repository import FinancialEventRepository


class FinancialEventsService:
    """
    Orchestrates financial event persistence and lineage management.

    Flow:
    1. Create FinancialEvent from classification results
    2. Persist event via FinancialEventRepository
    3. Walk lineage to detect settles/funds/rolls_over links
    4. Persist links and update lifecycle states
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.event_repo = FinancialEventRepository(db_path)

    def create_and_persist_event(
        self,
        event_type: str,
        transaction_ids: list[int],
        account_id: str,
        amount_paise: int = 0,
        asset_change_paise: int = 0,
        liability_change_paise: int = 0,
        expense_paise: int = 0,
        income_paise: int = 0,
        date_iso: str = "",
        category: str = "",
        sub_type: str | None = None,
        provider: str | None = None,
        confidence_bps: int = 0,
        household_id: str = "primary",
        owner_id: str = "self",
    ) -> int:
        """
        Create a FinancialEvent and persist it.

        Returns the database ID of the created event.
        """
        event = FinancialEvent(
            event_type=event_type,
            transaction_ids=transaction_ids,
            amount_paise=amount_paise,
            asset_change_paise=asset_change_paise,
            liability_change_paise=liability_change_paise,
            expense_paise=expense_paise,
            income_paise=income_paise,
            date_iso=date_iso,
            account_id=account_id,
            category=category,
            sub_type=sub_type,
            provider=provider,
            confidence_bps=confidence_bps,
            household_id=household_id,
            owner_id=owner_id,
        )
        return self.event_repo.insert_event(event)

    def process_lineage_for_household(
        self,
        household_id: str = "primary",
        lookback_days: int = DEFAULT_ROLLOVER_LOOKBACK_DAYS,
    ) -> dict[str, Any]:
        """
        Walk lineage for all events in a household and apply updates.

        Returns summary of changes made.
        """
        # Fetch all events for the household
        events = self.event_repo.get_events_by_type("", household_id)  # Get all types
        all_events = []
        for event_type in [
            "income", "expense", "transfer", "liability_increase",
            "liability_decrease", "cash_advance", "emi_payment",
            "liability_repayment", "credit_card_cash_advance", "transfer_internal"
        ]:
            all_events.extend(self.event_repo.get_events_by_type(event_type, household_id))

        # Walk lineage
        proposal = walk_lineage(all_events, lookback_days)

        # Apply lifecycle updates
        for update in proposal.lifecycle_updates:
            self.event_repo.update_lifecycle(
                event_id=update["event_id"],
                lifecycle_state=update["lifecycle_state"],
                outstanding_paise=update["outstanding_paise"],
            )

        # Persist links
        for link in proposal.proposed_links:
            self.event_repo.insert_link(
                event_id=link["event_id"],
                linked_event_id=link["linked_event_id"],
                link_type=link["link_type"],
            )

        return {
            "links_created": len(proposal.proposed_links),
            "lifecycle_updates": len(proposal.lifecycle_updates),
        }

    def get_events_with_links(
        self,
        month_bucket: str,
        household_id: str = "primary",
    ) -> list[dict[str, Any]]:
        """
        Get all events for a month with their link information.

        Returns enriched event dicts including link_details.
        """
        events = self.event_repo.get_events_for_month(month_bucket, household_id)

        for event in events:
            links = self.event_repo.get_links_for_event(event["id"])
            event["links"] = links

        return events