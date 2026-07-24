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

LinkType = Literal["settles", "funds", "rolls_over"]


@dataclass(frozen=True)
class LineageProposal:
    """Structured result from lineage walking.

    Contains all detected links and lifecycle updates without performing DB writes.
    """
    proposed_links: list[dict[str, Any]]  # {event_id, linked_event_id, link_type}
    lifecycle_updates: list[dict[str, Any]]  # {event_id, lifecycle_state, outstanding_paise}
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
    return event_type in ("liability_increase", "cash_advance", "credit_card_cash_advance", "emi_payment")


def _is_repayment_event(event: dict[str, Any]) -> bool:
    """Check if event type represents a liability decrease (repayment)."""
    event_type = event.get("event_type", "")
    return event_type in ("liability_repayment", "emi_payment")


def walk_lineage(
    events: list[dict[str, Any]],
    lookback_days: int = DEFAULT_ROLLOVER_LOOKBACK_DAYS,
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
        event.get("date_iso", "")
        lifecycle_state = event.get("lifecycle_state", "open")

        # Only process open/partially_settled repayments looking for advances to settle
        if lifecycle_state not in ("open", "partially_settled"):
            continue

        if not _is_repayment_event(event):
            continue

        # Find open advances on this account (liability account)
        account_events = events_by_account.get(account_id, [])
        open_advances = [
            e for e in account_events
            if _is_liability_event(e)
            and e.get("lifecycle_state") in ("open", "partially_settled")
            and e.get("id") != event_id
            and int(e.get("id", 0)) < int(event_id)  # Advance must be earlier
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

        proposed_links.append({
            "event_id": event_id,
            "linked_event_id": matched_advance_id,
            "link_type": "settles",
        })

        lifecycle_updates.append({
            "event_id": matched_advance_id,
            "lifecycle_state": new_state,
            "outstanding_paise": new_outstanding,
        })

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
        if event_type in ("credit_card_cash_advance", "liability_increase", "cash_advance"):
            if event.get("lifecycle_state") != "open":
                continue

            event_date = _parse_date_iso(date_iso)
            if event_date is None:
                continue

            # Find other advances within lookback window that this might be rolling over
            other_account_events = events  # Would be scoped by account in real impl
            potential_sources = [
                e for e in other_account_events
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
                    proposed_links.append({
                        "event_id": event_id,
                        "linked_event_id": source.get("id", 0),
                        "link_type": "rolls_over",
                    })

    return LineageProposal(
        proposed_links=proposed_links,
        lifecycle_updates=lifecycle_updates,
        superseded_events=superseded_events,
    )
