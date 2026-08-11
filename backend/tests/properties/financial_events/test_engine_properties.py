"""
Property-based tests for financial events engine.

These tests verify the invariants and business rules of the lineage walking
functions using property-based testing techniques.
"""

from __future__ import annotations

from datetime import date

from hypothesis import given, settings
from hypothesis import strategies as st

from src.engines.financial_events.lineage_walker import (
    LineageProposal,
    detect_rollover_scenarios,
    walk_lineage,
)

# Constants for testing
MAX_EVENTS = 50
MAX_PAISE = 10_000_000_00  # ₹10 crore
MIN_PAISE = 1_000  # ₹10
MAX_DATE_OFFSET = 365


# Strategies for generating test data
@st.composite
def event_id_strategy(draw, min_id=1, max_id=1000):
    """Generate event IDs ensuring uniqueness within a drawn sample."""
    return draw(st.integers(min_value=min_id, max_value=max_id))


@st.composite
def account_id_strategy(draw):
    """Generate account IDs."""
    return draw(st.sampled_from(["acc1", "acc2", "acc3", "acc_checking", "acc_credit"]))


@st.composite
def lifecycle_state_strategy(draw):
    """Generate valid lifecycle states."""
    return draw(
        st.sampled_from(
            ["open", "partially_settled", "settled", "rolls_over", "superseded"]
        )
    )


@st.composite
def event_type_strategy(draw):
    """Generate valid event types."""
    return draw(
        st.sampled_from(
            [
                "cash_advance",
                "credit_card_cash_advance",
                "liability_increase",
                "liability_decrease",
                "emi_payment",
                "liability_repayment",
                "income",
                "expense",
                "transfer",
                "transfer_internal",
            ]
        )
    )


@st.composite
def iso_date_strategy(draw, min_year=2020, max_year=2030):
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


@st.composite
def financial_event_strategy(draw):
    """Generate a random financial event dict."""
    event_type = draw(event_type_strategy())
    account_id = draw(account_id_strategy())
    date_iso = draw(iso_date_strategy())
    lifecycle_state = draw(lifecycle_state_strategy())
    event_id = draw(event_id_strategy())
    amount_paise = draw(st.integers(min_value=0, max_value=MAX_PAISE))
    liability_change_paise = draw(
        st.integers(min_value=-MAX_PAISE, max_value=MAX_PAISE)
    )
    asset_change_paise = draw(st.integers(min_value=0, max_value=MAX_PAISE))
    expense_paise = draw(st.integers(min_value=0, max_value=MAX_PAISE))
    income_paise = draw(st.integers(min_value=0, max_value=MAX_PAISE))
    outstanding_paise = draw(st.integers(min_value=0, max_value=MAX_PAISE))

    return {
        "id": event_id,
        "event_type": event_type,
        "account_id": account_id,
        "date_iso": date_iso,
        "lifecycle_state": lifecycle_state,
        "amount_paise": amount_paise,
        "liability_change_paise": liability_change_paise,
        "asset_change_paise": asset_change_paise,
        "expense_paise": expense_paise,
        "income_paise": income_paise,
        "outstanding_paise": outstanding_paise,
    }


@st.composite
def event_list_strategy(draw, max_events=20):
    """Generate a list of financial events."""
    num_events = draw(st.integers(min_value=0, max_value=max_events))
    return draw(
        st.lists(
            financial_event_strategy(),
            min_size=0,
            max_size=num_events,
            unique_by=lambda e: e["id"],
        )
    )


# ============================================================================
# walk_lineage Property Tests
# ============================================================================


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_walk_lineage_returns_valid_proposal(events):
    """Property: walk_lineage always returns a valid LineageProposal."""
    proposal = walk_lineage(events)
    assert isinstance(proposal, LineageProposal)
    assert isinstance(proposal.proposed_links, list)
    assert isinstance(proposal.lifecycle_updates, list)
    assert isinstance(proposal.superseded_events, list)


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_walk_lineage_no_duplicate_links(events):
    """Property: walk_lineage never creates duplicate links in a single run."""
    proposal = walk_lineage(events)
    link_keys = [
        (link["event_id"], link["linked_event_id"], link["link_type"])
        for link in proposal.proposed_links
    ]
    assert len(link_keys) == len(set(link_keys)), "Duplicate links found"


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_walk_lineage_repayment_earlier_than_advance(events):
    """Property: A repayment can only settle advances with earlier IDs."""
    proposal = walk_lineage(events)
    for link in proposal.proposed_links:
        assert (
            link["event_id"] > link["linked_event_id"]
        ), f"Repayment {link['event_id']} settled advance {link['linked_event_id']} which has equal or later ID"


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_walk_lineage_settled_outstanding_non_negative(events):
    """Property: After settlement, outstanding is never negative."""
    proposal = walk_lineage(events)
    for update in proposal.lifecycle_updates:
        assert (
            update["outstanding_paise"] >= 0
        ), f"Outstanding became negative: {update['outstanding_paise']}"


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_walk_lineage_link_count_matches_updates(events):
    """Property: Number of proposed links equals number of lifecycle updates."""
    proposal = walk_lineage(events)
    assert len(proposal.proposed_links) == len(
        proposal.lifecycle_updates
    ), f"Mismatch: {len(proposal.proposed_links)} links vs {len(proposal.lifecycle_updates)} updates"


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_walk_lineage_all_events_same_account_isolated(events):
    """Property: Repayments only match advances on the same account."""
    proposal = walk_lineage(events)
    event_map = {e["id"]: e for e in events}
    for link in proposal.proposed_links:
        repayment = event_map.get(link["event_id"])
        advance = event_map.get(link["linked_event_id"])
        if repayment and advance:
            assert (
                repayment["account_id"] == advance["account_id"]
            ), f"Cross-account match: repayment on {repayment['account_id']} matched advance on {advance['account_id']}"


@given(
    st.lists(
        financial_event_strategy(), min_size=0, max_size=30, unique_by=lambda e: e["id"]
    )
)
@settings(max_examples=5, deadline=None)
def test_walk_lineage_repayment_state_filter(events):
    """Property: Only open/partially_settled repayments generate links."""
    proposal = walk_lineage(events)
    event_map = {e["id"]: e for e in events}
    for link in proposal.proposed_links:
        repayment = event_map.get(link["event_id"])
        if repayment:
            assert repayment["lifecycle_state"] in (
                "open",
                "partially_settled",
            ), f"Repayment {link['event_id']} with state {repayment['lifecycle_state']} generated a link"


@given(
    st.lists(
        financial_event_strategy(), min_size=0, max_size=30, unique_by=lambda e: e["id"]
    )
)
@settings(max_examples=5, deadline=None)
def test_walk_lineage_advance_state_filter(events):
    """Property: Only open/partially_settled advances are settled."""
    proposal = walk_lineage(events)
    event_map = {e["id"]: e for e in events}
    for update in proposal.lifecycle_updates:
        advance = event_map.get(update["event_id"])
        if advance:
            assert advance["lifecycle_state"] in (
                "open",
                "partially_settled",
            ), f"Advance {update['event_id']} with state {advance['lifecycle_state']} was settled"


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_walk_lineage_monotonic_outstanding(events):
    """Property: Settlement reduces or maintains outstanding monotonically."""
    proposal = walk_lineage(events)
    event_map = {e["id"]: e for e in events}
    for update in proposal.lifecycle_updates:
        advance = event_map.get(update["event_id"])
        if advance:
            original = advance.get("outstanding_paise", 0)
            new = update["outstanding_paise"]
            assert (
                new <= original
            ), f"Outstanding increased for event {update['event_id']}: {original} -> {new}"


# ============================================================================
# detect_rollover_scenarios Property Tests
# ============================================================================


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_detect_rollover_returns_valid_proposal(events):
    """Property: detect_rollover_scenarios always returns a valid LineageProposal."""
    proposal = detect_rollover_scenarios(events)
    assert isinstance(proposal, LineageProposal)
    assert isinstance(proposal.proposed_links, list)
    assert isinstance(proposal.lifecycle_updates, list)
    assert isinstance(proposal.superseded_events, list)


@given(
    st.lists(
        financial_event_strategy(), min_size=0, max_size=20, unique_by=lambda e: e["id"]
    ),
    st.integers(min_value=1, max_value=365),
)
@settings(max_examples=5, deadline=None)
def test_detect_rollover_lookback_respected(events, lookback_days):
    """Property: Rolls_over links are only created within the lookback window."""
    proposal = detect_rollover_scenarios(events, lookback_days=lookback_days)
    event_map = {e["id"]: e for e in events}
    for link in proposal.proposed_links:
        source = event_map.get(link["linked_event_id"])
        target = event_map.get(link["event_id"])
        if source and target:
            source_date = date.fromisoformat(source.get("date_iso", "2025-01-01"))
            target_date = date.fromisoformat(target.get("date_iso", "2025-01-01"))
            days_diff = (target_date - source_date).days
            assert (
                0 < days_diff <= lookback_days
            ), f"Rollover link days_diff {days_diff} exceeds lookback {lookback_days}"


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_detect_rollover_only_open_advances(events):
    """Property: Only open advances generate rollover links."""
    proposal = detect_rollover_scenarios(events)
    event_map = {e["id"]: e for e in events}
    for link in proposal.proposed_links:
        target = event_map.get(link["event_id"])
        if target:
            assert (
                target["lifecycle_state"] == "open"
            ), f"Rollover target {link['event_id']} has state {target['lifecycle_state']}"


@given(
    st.integers(min_value=0, max_value=100000000),
    st.integers(min_value=0, max_value=100000000),
)
@settings(max_examples=5, deadline=None)
def test_detect_rollover_requires_positive_liability_change(liability_a, liability_b):
    """Property: Rollover sources must have positive liability_change_paise."""
    events = [
        {
            "id": 1,
            "event_type": "cash_advance",
            "account_id": "acc1",
            "date_iso": "2025-01-15",
            "lifecycle_state": "open",
            "outstanding_paise": 100000,
            "liability_change_paise": liability_a,
            "amount_paise": 100000,
        },
        {
            "id": 2,
            "event_type": "cash_advance",
            "account_id": "acc1",
            "date_iso": "2025-02-15",
            "lifecycle_state": "open",
            "outstanding_paise": 80000,
            "liability_change_paise": liability_b,
            "amount_paise": 80000,
        },
    ]
    proposal = detect_rollover_scenarios(events, lookback_days=90)
    event_map = {e["id"]: e for e in events}
    for link in proposal.proposed_links:
        source = event_map.get(link["linked_event_id"])
        if source:
            assert (
                source["liability_change_paise"] > 0
            ), f"Rollover source {link['linked_event_id']} has non-positive liability_change_paise"


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_detect_rollover_target_after_source(events):
    """Property: Rollover target event must be after source event."""
    proposal = detect_rollover_scenarios(events)
    event_map = {e["id"]: e for e in events}
    for link in proposal.proposed_links:
        source = event_map.get(link["linked_event_id"])
        target = event_map.get(link["event_id"])
        if source and target:
            assert (
                target["date_iso"] > source["date_iso"]
            ), f"Rollover target {link['event_id']} date {target.get('date_iso')} is not after source {link['linked_event_id']} date {source.get('date_iso')}"


# ============================================================================
# Cross-Function Properties
# ============================================================================


@given(event_list_strategy(max_events=20))
@settings(max_examples=5, deadline=None)
def test_both_functions_return_valid_structure(events):
    """Property: Both lineage functions return structurally valid proposals."""
    proposal1 = walk_lineage(events)
    proposal2 = detect_rollover_scenarios(events)
    for p in (proposal1, proposal2):
        assert hasattr(p, "proposed_links")
        assert hasattr(p, "lifecycle_updates")
        assert hasattr(p, "superseded_events")
        assert isinstance(p.proposed_links, list)
        assert isinstance(p.lifecycle_updates, list)
        assert isinstance(p.superseded_events, list)
