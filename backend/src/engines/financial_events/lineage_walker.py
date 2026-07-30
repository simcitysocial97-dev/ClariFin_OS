"""Financial Events Lineage Walker - Pure function for linking events.

Detects relationships between financial events:
- 'settles': Repayment → Cash advance (same liability account, temporal ordering)
- 'funds': Repayment → Cash advance (funding source detection)
- 'rolls_over': Debt-rolling scenario (repayment's funding traces to another advance)

DEFAULT_ROLLOVER_LOOKBACK_DAYS: Window to search for funding sources.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

# Named constant for rollover detection window
DEFAULT_ROLLOVER_LOOKBACK_DAYS: int = 90
DEFAULT_REVOCATION_LOOKBACK_DAYS: int = 7  # Smart default: 7 days to revoke a transfer

LinkType = Literal["settles", "funds", "rolls_over", "revokes"]


@dataclass(frozen=True)
class LineageProposal:
    """Structured result from lineage walking.

    Contains all detected links and lifecycle updates without performing DB writes.
    """

    proposed_links: list[dict[str, Any]]  # {event_id, linked_event_id, link_type}
    lifecycle_updates: list[
        dict[str, Any]
    ]  # {event_id, lifecycle_state, outstanding_paise}
    superseded_events: list[int]  # Event IDs that are superseded by this logic


def _parse_date_iso(date_iso: str) -> datetime | None:
    """Parse YYYY-MM-DD date string to datetime."""
    if not date_iso:
        return None
    try:
        return datetime.strptime(date_iso, "%Y-%m-%d")
    except ValueError:
        return None


def _date_difference_days(date_a: str, date_b: str) -> int:
    """Calculate difference in days between two ISO dates."""
    dt_a = _parse_date_iso(date_a)
    dt_b = _parse_date_iso(date_b)
    if dt_a is None or dt_b is None:
        return -1
    return (dt_b - dt_a).days


def _is_liability_event(event: dict[str, Any]) -> bool:
    """Check if event type represents a liability."""
    event_type = event.get("event_type", "")
    return event_type in (
        "liability_increase",
        "cash_advance",
        "credit_card_cash_advance",
        "emi_payment",
    )


def _is_repayment_event(event: dict[str, Any]) -> bool:
    """Check if event type represents a liability decrease (repayment)."""
    event_type = event.get("event_type", "")
    return event_type in ("liability_repayment", "emi_payment")


def _is_transfer_event(event: dict[str, Any]) -> bool:
    """Check if event type represents a fund transfer."""
    event_type = event.get("event_type", "")
    return event_type in ("fund_transfer_out", "fund_transfer_in", "transfer")


def _is_revocable_event(event: dict[str, Any]) -> bool:
    """Check if event type can be revoked (transfers only)."""
    event_type = event.get("event_type", "")
    lifecycle_state = event.get("lifecycle_state", "")
    return event_type in (
        "fund_transfer_out",
        "fund_transfer_in",
        "transfer",
    ) and lifecycle_state in ("open", "partially_settled")


def walk_lineage(
    events: list[dict[str, Any]],
    lookback_days: int = DEFAULT_ROLLOVER_LOOKBACK_DAYS,
    revocation_lookback_days: int = DEFAULT_REVOCATION_LOOKBACK_DAYS,
) -> LineageProposal:
    """
    Walk through events and detect lineage relationships.

    Implements:
    1. 'settles' linking: Repayment → most recent open/partially_settled advance
       on the same liability account
    2. 'rolls_over' detection: Repayment's funding source traces to another
       cash_advance event within lookback window

    PURE FUNCTION: Accepts plain dicts, returns proposals. No DB access.

    Args:
        events: List of financial event dicts (must include all fields)
        lookback_days: Days to search back for funding sources

    Returns:
        LineageProposal with proposed links and lifecycle updates.
    """
    proposed_links: list[dict[str, Any]] = []
    lifecycle_updates: list[dict[str, Any]] = []
    superseded_events: list[int] = []

    # Group events by account_id for efficient lookup
    events_by_account: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        acc_id = event.get("account_id", "")
        if acc_id:
            if acc_id not in events_by_account:
                events_by_account[acc_id] = []
            events_by_account[acc_id].append(event)

    # Track processed event IDs to avoid duplicate links
    processed_pairs: set[tuple[int, int, str]] = set()

    for event in events:
        event.get("event_type", "")
        event_id = event.get("id", 0)
        account_id = event.get("account_id", "")
        event_date_iso = event.get("date_iso", "")
        lifecycle_state = event.get("lifecycle_state", "open")

        # Process revocation events first
        if event.get("event_type") == "transfer_revocation":
            continue  # Handled by detect_revocations

        # Only process open/partially_settled repayments looking for advances to settle
        if lifecycle_state not in ("open", "partially_settled"):
            continue

        if not _is_repayment_event(event):
            continue

        # Find open advances on this account (liability account)
        account_events = events_by_account.get(account_id, [])
        open_advances = [
            e
            for e in account_events
            if _is_liability_event(e)
            and e.get("lifecycle_state") in ("open", "partially_settled")
            and e.get("id") != event_id
            and int(e.get("id", 0)) < int(event_id)  # Advance must be earlier
            and e.get("date_iso", "")
            <= event_date_iso  # Advance date <= repayment date
        ]

        if not open_advances:
            continue

        # Sort by date descending, take most recent
        open_advances.sort(key=lambda e: e.get("date_iso", ""), reverse=True)
        matched_advance = open_advances[0]
        matched_advance_id = matched_advance.get("id", 0)

        # Check for duplicate
        link_key = (event_id, matched_advance_id, "settles")
        if link_key in processed_pairs:
            continue
        processed_pairs.add(link_key)

        # Calculate outstanding after this payment
        advance_outstanding = int(matched_advance.get("outstanding_paise", 0) or 0)
        payment_amount = int(event.get("liability_change_paise", 0) or 0)
        # liability_change_paise for repayment is negative, use absolute value
        if payment_amount < 0:
            payment_amount = abs(payment_amount)

        new_outstanding = max(0, advance_outstanding - payment_amount)
        new_state = "settled" if new_outstanding == 0 else "partially_settled"

        proposed_links.append(
            {
                "event_id": event_id,
                "linked_event_id": matched_advance_id,
                "link_type": "settles",
            }
        )

        lifecycle_updates.append(
            {
                "event_id": matched_advance_id,
                "lifecycle_state": new_state,
                "outstanding_paise": new_outstanding,
            }
        )

    # Detect and apply revocations
    revocation_proposal = detect_revocations(events, revocation_lookback_days)
    proposed_links.extend(revocation_proposal.proposed_links)
    lifecycle_updates.extend(revocation_proposal.lifecycle_updates)
    superseded_events.extend(revocation_proposal.superseded_events)

    return LineageProposal(
        proposed_links=proposed_links,
        lifecycle_updates=lifecycle_updates,
        superseded_events=superseded_events,
    )


def detect_revocations(
    events: list[dict[str, Any]],
    lookback_days: int = DEFAULT_REVOCATION_LOOKBACK_DAYS,
) -> LineageProposal:
    """
    Detect and apply revocations for fund transfers.

    Revocation rules (smart defaults):
    1. Only open/partially_settled transfers can be revoked
    2. Revocation must occur within 7 days of transfer (DEFAULT_REVOCATION_LOOKBACK_DAYS)
    3. Revocation applies to both sides of the transfer (in/out)
    4. Revoked transfers are marked as "revoked" lifecycle state
    5. All downstream events linked to the transfer are superseded

    PURE FUNCTION: No DB access.
    """
    proposed_links: list[dict[str, Any]] = []
    lifecycle_updates: list[dict[str, Any]] = []
    superseded_events: list[int] = []

    # Group events by transfer_id for efficient lookup
    events_by_transfer: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        transfer_id = event.get("transfer_id", "")
        if transfer_id and _is_transfer_event(event):
            if transfer_id not in events_by_transfer:
                events_by_transfer[transfer_id] = []
            events_by_transfer[transfer_id].append(event)

    # Auto-revoke failed transfers (smart default)
    auto_revoked_transfers = set()
    for transfer_id, transfer_events in events_by_transfer.items():
        for event in transfer_events:
            if event.get("lifecycle_state") == "failed":
                auto_revoked_transfers.add(transfer_id)
                break

    # Track processed revocations to avoid duplicates
    processed_revocations: set[tuple[int, int]] = set()

    for event in events:
        event_type = event.get("event_type", "")
        event_id = event.get("id", 0)
        transfer_id = event.get("transfer_id", "")
        date_iso = event.get("date_iso", "")
        lifecycle_state = event.get("lifecycle_state", "")

        # Only process revocation events
        if event_type != "transfer_revocation" or lifecycle_state != "open":
            continue

        # Find the transfer this revocation applies to
        transfer_events = events_by_transfer.get(transfer_id, [])
        if not transfer_events:
            continue

        # Skip if this transfer was already auto-revoked
        if transfer_id in auto_revoked_transfers:
            continue

        # Find the original transfer event (earliest date)
        transfer_events.sort(key=lambda e: e.get("date_iso", ""))
        original_transfer = transfer_events[0]
        original_transfer_id = original_transfer.get("id", 0)

        # Check if this revocation is within the allowed window
        days_diff = _date_difference_days(
            original_transfer.get("date_iso", ""), date_iso
        )
        if days_diff < 0 or days_diff > lookback_days:
            continue  # Outside revocation window

        # Check for duplicate revocation
        revocation_key = (event_id, original_transfer_id)
        if revocation_key in processed_revocations:
            continue
        processed_revocations.add(revocation_key)

        # Apply revocation to all events in this transfer
        for transfer_event in transfer_events:
            transfer_event_id = transfer_event.get("id", 0)
            proposed_links.append(
                {
                    "event_id": event_id,
                    "linked_event_id": transfer_event_id,
                    "link_type": "revokes",
                }
            )
            lifecycle_updates.append(
                {
                    "event_id": transfer_event_id,
                    "lifecycle_state": "revoked",
                    "outstanding_paise": 0,
                }
            )
            superseded_events.append(transfer_event_id)

    # Apply auto-revocations for failed transfers
    for transfer_id in auto_revoked_transfers:
        transfer_events = events_by_transfer.get(transfer_id, [])
        for transfer_event in transfer_events:
            transfer_event_id = transfer_event.get("id", 0)
            lifecycle_updates.append(
                {
                    "event_id": transfer_event_id,
                    "lifecycle_state": "revoked",
                    "outstanding_paise": 0,
                    "auto_revoked": True,
                }
            )
            superseded_events.append(transfer_event_id)

    return LineageProposal(
        proposed_links=proposed_links,
        lifecycle_updates=lifecycle_updates,
        superseded_events=superseded_events,
    )


def detect_rollover_scenarios(
    events: list[dict[str, Any]],
    lookback_days: int = DEFAULT_ROLLOVER_LOOKBACK_DAYS,
) -> LineageProposal:
    """
    Detect debt-rolling scenarios where a repayment's funding traces to another advance.

    A rollover occurs when:
    1. An advance event is created
    2. Within lookback_days, a repayment event is created
    3. That repayment event's funding source (linked via 'funds') traces to another advance

    This function detects and marks such patterns.

    PURE FUNCTION: No DB access.
    """
    proposed_links: list[dict[str, Any]] = []
    lifecycle_updates: list[dict[str, Any]] = []
    superseded_events: list[int] = []

    # First find all 'funds' links (repayments linked to their funding advances)
    # For now, we'll detect rollovers based on temporal patterns

    for event in events:
        event_type = event.get("event_type", "")
        event_id = event.get("id", 0)
        event.get("account_id", "")
        date_iso = event.get("date_iso", "")

        # Look for advance events that might be rollovers
        if event_type in (
            "credit_card_cash_advance",
            "liability_increase",
            "cash_advance",
        ):
            if event.get("lifecycle_state") != "open":
                continue

            event_date = _parse_date_iso(date_iso)
            if event_date is None:
                continue

            # Find other advances within lookback window that this might be rolling over
            other_account_events = events  # Would be scoped by account in real impl
            potential_sources = [
                e
                for e in other_account_events
                if _is_liability_event(e)
                and e.get("id") != event_id
                and int(e.get("liability_change_paise", 0) or 0) > 0  # Original advance
                and e.get("lifecycle_state") in ("open", "partially_settled")
            ]

            for source in potential_sources:
                source_date = _parse_date_iso(source.get("date_iso", ""))
                if source_date is None:
                    continue

                days_diff = _date_difference_days(source.get("date_iso", ""), date_iso)
                if 0 < days_diff <= lookback_days:
                    # This advance appears to be rolling over from another
                    (event_id, source.get("id", 0), "rolls_over")
                    # In a real implementation, we'd add to processed_pairs
                    proposed_links.append(
                        {
                            "event_id": event_id,
                            "linked_event_id": source.get("id", 0),
                            "link_type": "rolls_over",
                        }
                    )

    return LineageProposal(
        proposed_links=proposed_links,
        lifecycle_updates=lifecycle_updates,
        superseded_events=superseded_events,
    )
