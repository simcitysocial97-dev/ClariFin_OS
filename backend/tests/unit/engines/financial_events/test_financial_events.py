"""Unit tests for Financial Events engine - lineage walker and service layer."""

from __future__ import annotations

import pytest

from src.engines.financial_events.lineage_walker import (
    DEFAULT_ROLLOVER_LOOKBACK_DAYS,
    detect_rollover_scenarios,
    walk_lineage,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_events():
    """Sample events for testing lineage."""
    return [
        {
            "id": 1,
            "event_type": "cash_advance",
            "account_id": "acc1",
            "date_iso": "2025-01-15",
            "lifecycle_state": "open",
            "outstanding_paise": 100000,
            "liability_change_paise": 100000,
            "amount_paise": 100000,
        },
        {
            "id": 2,
            "event_type": "emi_payment",
            "account_id": "acc1",
            "date_iso": "2025-02-15",
            "lifecycle_state": "open",
            "outstanding_paise": 0,
            "liability_change_paise": -50000,
            "amount_paise": 50000,
        },
        {
            "id": 3,
            "event_type": "cash_advance",
            "account_id": "acc1",
            "date_iso": "2025-03-15",
            "lifecycle_state": "open",
            "outstanding_paise": 80000,
            "liability_change_paise": 80000,
            "amount_paise": 80000,
        },
        {
            "id": 4,
            "event_type": "emi_payment",
            "account_id": "acc1",
            "date_iso": "2025-04-15",
            "lifecycle_state": "open",
            "outstanding_paise": 0,
            "liability_change_paise": -40000,
            "amount_paise": 40000,
        },
    ]


@pytest.fixture
def sample_events_multiple_accounts():
    """Sample events across multiple accounts."""
    return [
        {
            "id": 1,
            "event_type": "cash_advance",
            "account_id": "acc1",
            "date_iso": "2025-01-15",
            "lifecycle_state": "open",
            "outstanding_paise": 100000,
            "liability_change_paise": 100000,
            "amount_paise": 100000,
        },
        {
            "id": 2,
            "event_type": "emi_payment",
            "account_id": "acc2",
            "date_iso": "2025-02-15",
            "lifecycle_state": "open",
            "outstanding_paise": 0,
            "liability_change_paise": -50000,
            "amount_paise": 50000,
        },
    ]


@pytest.fixture
def sample_events_no_repayments():
    """Events with no repayments."""
    return [
        {
            "id": 1,
            "event_type": "cash_advance",
            "account_id": "acc1",
            "date_iso": "2025-01-15",
            "lifecycle_state": "open",
            "outstanding_paise": 100000,
            "liability_change_paise": 100000,
            "amount_paise": 100000,
        },
    ]


@pytest.fixture
def sample_events_no_advances():
    """Events with no open advances."""
    return [
        {
            "id": 1,
            "event_type": "emi_payment",
            "account_id": "acc1",
            "date_iso": "2025-02-15",
            "lifecycle_state": "open",
            "outstanding_paise": 0,
            "liability_change_paise": -50000,
            "amount_paise": 50000,
        },
    ]


# ============================================================================
# walk_lineage Unit Tests
# ============================================================================


class TestWalkLineage:
    """Unit tests for walk_lineage function."""

    def test_empty_events_returns_empty_proposal(self):
        """Empty event list should produce empty proposal."""
        proposal = walk_lineage([])
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []
        assert proposal.superseded_events == []

    def test_single_repayment_no_advances(self, sample_events_no_advances):
        """Repayment with no open advances should produce no links."""
        proposal = walk_lineage(sample_events_no_advances)
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []

    def test_single_advance_no_repayments(self, sample_events_no_repayments):
        """Advance with no repayments should produce no links."""
        proposal = walk_lineage(sample_events_no_repayments)
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []

    def test_repayment_settles_most_recent_advance(self, sample_events):
        """Repayment should settle the most recent open advance on same account."""
        proposal = walk_lineage(sample_events)
        assert len(proposal.proposed_links) == 2
        assert proposal.proposed_links[0]["event_id"] == 2
        assert proposal.proposed_links[0]["linked_event_id"] == 1
        assert proposal.proposed_links[0]["link_type"] == "settles"
        assert proposal.proposed_links[1]["event_id"] == 4
        assert proposal.proposed_links[1]["linked_event_id"] == 3
        assert proposal.proposed_links[1]["link_type"] == "settles"

    def test_full_payment_sets_settled_state(self):
        """Full payment should set advance state to settled."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 50000,
                "liability_change_paise": 50000,
                "amount_paise": 50000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        updates = {u["event_id"]: u for u in proposal.lifecycle_updates}
        assert updates[1]["lifecycle_state"] == "settled"
        assert updates[1]["outstanding_paise"] == 0

    def test_partial_payment_sets_partially_settled(self):
        """Partial payment should set advance state to partially_settled."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        updates = {u["event_id"]: u for u in proposal.lifecycle_updates}
        assert updates[1]["lifecycle_state"] == "partially_settled"
        assert updates[1]["outstanding_paise"] == 50000

    def test_non_repayment_events_skipped(self, sample_events):
        """Non-repayment events should not process."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "income",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": 0,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []

    def test_cross_account_repayments_isolated(self, sample_events_multiple_accounts):
        """Repayments should only settle advances on the same account."""
        proposal = walk_lineage(sample_events_multiple_accounts)
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []

    def test_settled_repayments_skipped(self, sample_events):
        """Repayments with non-open/non-partially_settled state should be skipped."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "settled",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []

    def test_repayment_larger_than_outstanding(self):
        """Payment larger than outstanding should cap at zero."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 50000,
                "liability_change_paise": 50000,
                "amount_paise": 50000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -100000,
                "amount_paise": 100000,
            },
        ]
        proposal = walk_lineage(events)
        updates = {u["event_id"]: u for u in proposal.lifecycle_updates}
        assert updates[1]["lifecycle_state"] == "settled"
        assert updates[1]["outstanding_paise"] == 0

    def test_negative_liability_change_handled(self):
        """Repayment with negative liability_change_paise should use absolute value."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        updates = {u["event_id"]: u for u in proposal.lifecycle_updates}
        assert updates[1]["lifecycle_state"] == "partially_settled"
        assert updates[1]["outstanding_paise"] == 50000

    def test_non_liability_advances_ignored(self):
        """Non-liability events should not be matched as advances."""
        events = [
            {
                "id": 1,
                "event_type": "income",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": 0,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -100000,
                "amount_paise": 100000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []

    def test_earlier_repayment_does_not_settle_later_advance(self):
        """Repayment with lower ID should not settle advance with higher ID."""
        events = [
            {
                "id": 1,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []

    def test_default_lookback_days(self):
        """Default lookback days should be 90."""
        assert DEFAULT_ROLLOVER_LOOKBACK_DAYS == 90


# ============================================================================
# detect_rollover_scenarios Unit Tests
# ============================================================================


class TestDetectRolloverScenarios:
    """Unit tests for detect_rollover_scenarios function."""

    def test_empty_events_returns_empty(self):
        """Empty events should return empty proposal."""
        proposal = detect_rollover_scenarios([])
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []
        assert proposal.superseded_events == []

    def test_no_open_advances_returns_empty(self):
        """No open advances should return empty proposal."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "settled",
                "outstanding_paise": 0,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
        ]
        proposal = detect_rollover_scenarios(events)
        assert proposal.proposed_links == []

    def test_rollover_detected_within_lookback(self):
        """Advances within lookback window should be linked."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 80000,
                "liability_change_paise": 80000,
                "amount_paise": 80000,
            },
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        assert len(proposal.proposed_links) == 1
        assert proposal.proposed_links[0]["link_type"] == "rolls_over"
        assert proposal.proposed_links[0]["event_id"] == 2
        assert proposal.proposed_links[0]["linked_event_id"] == 1

    def test_rollover_not_detected_outside_lookback(self):
        """Advances outside lookback window should not be linked."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2024-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 80000,
                "liability_change_paise": 80000,
                "amount_paise": 80000,
            },
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        assert len(proposal.proposed_links) == 0

    def test_rollover_ignores_non_liability_events(self):
        """Non-liability events should not be considered as rollover sources."""
        events = [
            {
                "id": 1,
                "event_type": "income",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": 0,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 80000,
                "liability_change_paise": 80000,
                "amount_paise": 80000,
            },
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        assert len(proposal.proposed_links) == 0

    def test_rollover_ignores_settled_advances(self):
        """Settled advances should not be considered for rollover."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "settled",
                "outstanding_paise": 0,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 80000,
                "liability_change_paise": 80000,
                "amount_paise": 80000,
            },
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        assert len(proposal.proposed_links) == 0
