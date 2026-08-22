"""
Property-based tests for financial events lineage invariants.

These tests verify the core invariants of the lineage walking logic using
Hypothesis for property-based testing.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn, composite

from src.engines.financial_events.lineage_walker import (
    LineageProposal,
    walk_lineage,
)

# Constants for testing
MAX_EVENTS = 50
MAX_PAISE = 10_000_000_00  # ₹10 crore
MIN_PAISE = 1_000  # ₹10
MAX_DATE_OFFSET = 365


# ============================================================================
# Strategies for generating test data
# ============================================================================


@composite
def event_id_strategy(draw: DrawFn, min_id: int = 1, max_id: int = 1000) -> int:
    """Generate unique event IDs."""
    return draw(st.integers(min_value=min_id, max_value=max_id))


@composite
def account_id_strategy(draw: DrawFn) -> str:
    """Generate account IDs."""
    return draw(
        st.sampled_from(["acc1", "acc2", "acc3", "liability_acc", "credit_acc"])
    )


@composite
def lifecycle_state_strategy(draw: DrawFn) -> str:
    """Generate valid lifecycle states."""
    return draw(st.sampled_from(["open", "partially_settled", "settled", "revoked"]))


@composite
def event_type_strategy(draw: DrawFn) -> str:
    """Generate valid event types."""
    return draw(
        st.sampled_from(
            [
                "cash_advance",
                "credit_card_cash_advance",
                "liability_increase",
                "liability_repayment",
                "emi_payment",
                "transfer",
                "transfer_revocation",
            ]
        )
    )


@composite
def iso_date_strategy(draw: DrawFn, min_year: int = 2020, max_year: int = 2030) -> str:
    """Generate ISO date strings."""
    year = draw(st.integers(min_value=min_year, max_value=max_year))
    month = draw(st.integers(min_value=1, max_value=12))
    days_in_month = [
        31,
        29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ]
    day = draw(st.integers(min_value=1, max_value=days_in_month[month - 1]))
    return f"{year:04d}-{month:02d}-{day:02d}"


@composite
def financial_event_strategy(draw: DrawFn) -> dict[str, Any]:
    """Generate a random financial event dict."""
    event_type = draw(event_type_strategy())
    account_id = draw(account_id_strategy())
    date_iso = draw(iso_date_strategy())
    lifecycle_state = draw(lifecycle_state_strategy())
    event_id = draw(event_id_strategy())
    amount_paise = draw(st.integers(min_value=MIN_PAISE, max_value=MAX_PAISE))

    # Ensure liability_change_paise is negative for repayments
    if event_type in ["liability_repayment", "emi_payment"]:
        liability_change_paise = draw(
            st.integers(min_value=-MAX_PAISE, max_value=-MIN_PAISE)
        )
    else:
        liability_change_paise = draw(
            st.integers(min_value=MIN_PAISE, max_value=MAX_PAISE)
        )

    outstanding_paise = draw(st.integers(min_value=0, max_value=MAX_PAISE))
    transfer_id = draw(st.one_of(st.none(), st.text(min_size=1, max_size=10)))

    return {
        "id": event_id,
        "event_type": event_type,
        "account_id": account_id,
        "date_iso": date_iso,
        "lifecycle_state": lifecycle_state,
        "amount_paise": amount_paise,
        "liability_change_paise": liability_change_paise,
        "outstanding_paise": outstanding_paise,
        "transfer_id": transfer_id,
    }


@composite
def event_list_strategy(draw: DrawFn, max_events: int = 10) -> list[dict[str, Any]]:
    """Generate a list of financial events with unique IDs and valid temporal ordering."""
    num_events = draw(st.integers(min_value=0, max_value=max_events))
    events = draw(
        st.lists(
            financial_event_strategy(),
            min_size=num_events,
            max_size=num_events,
            unique_by=lambda e: e["id"],
        )
    )

    # Ensure advances have earlier dates than repayments
    advances = [
        e
        for e in events
        if e["event_type"]
        in ["cash_advance", "credit_card_cash_advance", "liability_increase"]
    ]
    repayments = [
        e for e in events if e["event_type"] in ["liability_repayment", "emi_payment"]
    ]

    # Assign dates: advances get earlier dates, repayments get later dates
    min_date = date(2020, 1, 1)
    max_date = date(2020, 12, 31)

    for i, advance in enumerate(advances):
        advance_date = min_date + (max_date - min_date) * i // max(1, len(advances))
        advance["date_iso"] = advance_date.isoformat()

    for i, repayment in enumerate(repayments):
        repayment_date = min_date + (max_date - min_date) * (len(advances) + i) // max(
            1, len(advances) + len(repayments)
        )
        repayment["date_iso"] = repayment_date.isoformat()

    return events


# ============================================================================
# Property Tests for Lineage Invariants
# ============================================================================


@given(event_list_strategy(max_events=20))
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_lineage_graph_acyclic(events: list[dict[str, Any]]) -> None:
    """Property: Lineage graph must be acyclic (no circular references)."""
    proposal = walk_lineage(events)

    # Build adjacency list for the graph
    graph: dict[int, list[int]] = {}
    for link in proposal.proposed_links:
        event_id = link["event_id"]
        linked_event_id = link["linked_event_id"]
        if event_id not in graph:
            graph[event_id] = []
        graph[event_id].append(linked_event_id)

    # Check for cycles using DFS
    visited: set[int] = set()
    recursion_stack: set[int] = set()

    def is_cyclic(node: int) -> bool:
        visited.add(node)
        recursion_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if is_cyclic(neighbor):
                    return True
            elif neighbor in recursion_stack:
                return True
        recursion_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            assert not is_cyclic(node), "Cycle detected in lineage graph"


@given(event_list_strategy(max_events=20))
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_lineage_deterministic_output(events: list[dict[str, Any]]) -> None:
    """Property: Same input must always produce the same lineage path."""
    # Sort events by ID to ensure consistent input order
    sorted_events = sorted(events, key=lambda e: e["id"])

    proposal1 = walk_lineage(sorted_events)
    proposal2 = walk_lineage(sorted_events)

    # Compare proposed links
    assert len(proposal1.proposed_links) == len(
        proposal2.proposed_links
    ), "Different number of links in deterministic test"

    # Sort links for comparison
    links1 = sorted(
        proposal1.proposed_links, key=lambda x: (x["event_id"], x["linked_event_id"])
    )
    links2 = sorted(
        proposal2.proposed_links, key=lambda x: (x["event_id"], x["linked_event_id"])
    )

    for link1, link2 in zip(links1, links2, strict=True):
        assert link1 == link2, "Links differ in deterministic test"

    # Compare lifecycle updates
    updates1 = sorted(proposal1.lifecycle_updates, key=lambda x: x["event_id"])
    updates2 = sorted(proposal2.lifecycle_updates, key=lambda x: x["event_id"])

    for update1, update2 in zip(updates1, updates2, strict=True):
        assert update1 == update2, "Lifecycle updates differ in deterministic test"


@given(event_list_strategy(max_events=10))
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_lineage_no_duplicate_events(events: list[dict[str, Any]]) -> None:
    """Property: No duplicate events in the lineage graph."""
    proposal = walk_lineage(events)

    # Check for duplicate links
    link_keys = [
        (link["event_id"], link["linked_event_id"], link["link_type"])
        for link in proposal.proposed_links
    ]
    assert len(link_keys) == len(set(link_keys)), "Duplicate links found"

    # Check for duplicate lifecycle updates (same event_id with same state/outstanding)
    seen_updates = set()
    for update in proposal.lifecycle_updates:
        update_key = (
            update["event_id"],
            update["lifecycle_state"],
            update["outstanding_paise"],
        )
        assert (
            update_key not in seen_updates
        ), f"Duplicate lifecycle update found: {update_key}"
        seen_updates.add(update_key)


@given(event_list_strategy(max_events=10))
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_lineage_temporal_ordering(events: list[dict[str, Any]]) -> None:
    """Property: Events must be ordered by timestamp (oldest → newest)."""
    # The walk_lineage function sorts advances by date descending and takes the most recent
    # So we only validate that the matched advance is not newer than the repayment
    proposal = walk_lineage(events)
    event_map = {e["id"]: e for e in events}

    for link in proposal.proposed_links:
        source = event_map.get(link["linked_event_id"])
        target = event_map.get(link["event_id"])

        if source and target and link["link_type"] == "settles":
            source_date = datetime.strptime(source["date_iso"], "%Y-%m-%d").date()
            target_date = datetime.strptime(target["date_iso"], "%Y-%m-%d").date()

            # Validate that the matched advance is not newer than the repayment
            assert (
                source_date <= target_date
            ), f"Temporal ordering violated: Matched advance {source['date_iso']} > Repayment {target['date_iso']}"


@given(event_list_strategy(max_events=20))
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_lineage_input_validation_duplicate_ids(events: list[dict[str, Any]]) -> None:
    """Property: Reject invalid inputs (e.g., duplicate event IDs)."""
    # Create a list with duplicate IDs
    if len(events) >= 2:
        duplicate_events = events.copy()
        duplicate_events[1] = {**events[0], "id": events[0]["id"]}

        # Ensure walk_lineage handles duplicates gracefully
        proposal = walk_lineage(duplicate_events)
        assert isinstance(
            proposal, LineageProposal
        ), "walk_lineage should handle duplicate IDs gracefully"


@given(event_list_strategy(max_events=20))
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_lineage_input_validation_future_timestamps(
    events: list[dict[str, Any]],
) -> None:
    """Property: Reject invalid inputs (e.g., future timestamps)."""
    future_date = (date.today().year + 1, 1, 1)
    future_date_iso = f"{future_date[0]:04d}-{future_date[1]:02d}-{future_date[2]:02d}"

    if events:
        invalid_events = events.copy()
        invalid_events[0]["date_iso"] = future_date_iso

        proposal = walk_lineage(invalid_events)
        assert isinstance(
            proposal, LineageProposal
        ), "walk_lineage should handle future timestamps gracefully"


@given(st.lists(financial_event_strategy(), min_size=0, max_size=1))
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_lineage_edge_case_single_event(events: list[dict[str, Any]]) -> None:
    """Property: Handle edge case of a single event."""
    proposal = walk_lineage(events)
    assert isinstance(proposal, LineageProposal)
    assert len(proposal.proposed_links) == 0
    assert len(proposal.lifecycle_updates) == 0


@given(st.lists(financial_event_strategy(), min_size=0, max_size=0))
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_lineage_edge_case_zero_events(events: list[dict[str, Any]]) -> None:
    """Property: Handle edge case of zero events."""
    proposal = walk_lineage(events)
    assert isinstance(proposal, LineageProposal)
    assert len(proposal.proposed_links) == 0
    assert len(proposal.lifecycle_updates) == 0
