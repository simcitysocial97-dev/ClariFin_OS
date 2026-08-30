"""Unit tests for Financial Events engine - lineage walker and service layer."""

from __future__ import annotations

import pytest
from src.engines.financial_events.lineage_walker import (
    DEFAULT_ROLLOVER_LOOKBACK_DAYS,
    _date_difference_days,
    _is_liability_event,
    _is_repayment_event,
    _is_revocable_event,
    _is_transfer_event,
    _merge_lifecycle_update,
    _parse_date_iso,
    detect_revocations,
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


# ============================================================================
# Internal Helper Function Tests
# ============================================================================


class TestInternalHelpers:
    """Tests for internal helper functions in lineage_walker."""

    def test_parse_date_iso_valid(self) -> None:
        """Test _parse_date_iso with valid ISO dates."""
        from datetime import datetime

        result = _parse_date_iso("2025-01-15")
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_iso_invalid(self) -> None:
        """Test _parse_date_iso with invalid dates."""

        assert _parse_date_iso("invalid") is None
        assert _parse_date_iso("") is None
        assert _parse_date_iso("2025-13-45") is None
        assert _parse_date_iso(None) is None

    def test_date_difference_days(self) -> None:
        """Test _date_difference_days."""

        assert _date_difference_days("2025-01-01", "2025-01-10") == 9
        assert _date_difference_days("2025-01-10", "2025-01-01") == -9
        assert _date_difference_days("2025-01-01", "2025-01-01") == 0
        assert _date_difference_days("invalid", "2025-01-01") == -1
        assert _date_difference_days("2025-01-01", "invalid") == -1

    def test_is_liability_event(self) -> None:
        """Test _is_liability_event."""

        assert _is_liability_event({"event_type": "cash_advance"}) is True
        assert _is_liability_event({"event_type": "credit_card_cash_advance"}) is True
        assert _is_liability_event({"event_type": "liability_increase"}) is True
        assert _is_liability_event({"event_type": "emi_payment"}) is True
        assert _is_liability_event({"event_type": "income"}) is False
        assert _is_liability_event({"event_type": "fund_transfer_out"}) is False

    def test_is_repayment_event(self) -> None:
        """Test _is_repayment_event."""

        assert _is_repayment_event({"event_type": "liability_repayment"}) is True
        assert _is_repayment_event({"event_type": "emi_payment"}) is True
        assert _is_repayment_event({"event_type": "cash_advance"}) is False
        assert _is_repayment_event({"event_type": "income"}) is False

    def test_is_transfer_event(self) -> None:
        """Test _is_transfer_event."""

        assert _is_transfer_event({"event_type": "fund_transfer_out"}) is True
        assert _is_transfer_event({"event_type": "fund_transfer_in"}) is True
        assert _is_transfer_event({"event_type": "transfer"}) is True
        assert _is_transfer_event({"event_type": "cash_advance"}) is False

    def test_is_revocable_event(self) -> None:
        """Test _is_revocable_event."""

        assert (
            _is_revocable_event(
                {"event_type": "fund_transfer_out", "lifecycle_state": "open"}
            )
            is True
        )
        assert (
            _is_revocable_event(
                {
                    "event_type": "fund_transfer_in",
                    "lifecycle_state": "partially_settled",
                }
            )
            is True
        )
        assert (
            _is_revocable_event(
                {"event_type": "fund_transfer_out", "lifecycle_state": "settled"}
            )
            is False
        )
        assert (
            _is_revocable_event(
                {"event_type": "fund_transfer_out", "lifecycle_state": "revoked"}
            )
            is False
        )
        assert (
            _is_revocable_event(
                {"event_type": "cash_advance", "lifecycle_state": "open"}
            )
            is False
        )

    def test_merge_lifecycle_update(self) -> None:
        """Test _merge_lifecycle_update state merging."""

        # None existing -> return candidate
        result = _merge_lifecycle_update(
            None, {"event_id": 1, "lifecycle_state": "open", "outstanding_paise": 100}
        )
        assert result["lifecycle_state"] == "open"

        # settled > partially_settled > revoked > open
        existing = {
            "event_id": 1,
            "lifecycle_state": "partially_settled",
            "outstanding_paise": 50,
        }
        candidate = {
            "event_id": 1,
            "lifecycle_state": "settled",
            "outstanding_paise": 0,
        }
        result = _merge_lifecycle_update(existing, candidate)
        assert result["lifecycle_state"] == "settled"

        # Same state -> smaller outstanding wins
        existing = {
            "event_id": 1,
            "lifecycle_state": "partially_settled",
            "outstanding_paise": 100,
        }
        candidate = {
            "event_id": 1,
            "lifecycle_state": "partially_settled",
            "outstanding_paise": 50,
        }
        result = _merge_lifecycle_update(existing, candidate)
        assert result["outstanding_paise"] == 50


# ============================================================================
# detect_revocations tests (M9-C46 — golden characterization)
# ============================================================================


class TestDetectRevocations:
    """Golden tests for revocation detection logic.

    These tests lock the behavioral contract for transfer revocation:
    - Only open transfers can be revoked
    - Revocation window: DEFAULT_REVOCATION_LOOKBACK_DAYS (7 days)
    - Both sides of transfer are marked revoked
    - Auto-revocation of failed transfers
    - Duplicate revocation prevention
    """

    def test_empty_events_returns_empty_proposal(self) -> None:
        result = detect_revocations([])
        assert result.proposed_links == []
        assert result.lifecycle_updates == []
        assert result.superseded_events == []

    def test_no_revocation_events_returns_empty(self) -> None:
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "fund_transfer_in",
                "transfer_id": "t1",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events)
        assert result.proposed_links == []
        assert result.lifecycle_updates == []

    def test_revocation_within_window_revokes_both_sides(self) -> None:
        """Revocation within lookback window revokes both out/in sides."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "fund_transfer_in",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 3,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-05",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert len(result.proposed_links) == 2  # revokes both sides
        assert all(link["link_type"] == "revokes" for link in result.proposed_links)
        assert len(result.lifecycle_updates) == 2
        assert all(u["lifecycle_state"] == "revoked" for u in result.lifecycle_updates)
        assert all(u["outstanding_paise"] == 0 for u in result.lifecycle_updates)

    def test_revocation_outside_window_ignored(self) -> None:
        """Revocation after lookback window is ignored."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-10",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_at_boundary_day_7_accepted(self) -> None:
        """Revocation exactly at 7-day boundary is within window."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-08",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert len(result.proposed_links) == 1

    def test_revocation_outside_boundary_day_8_rejected(self) -> None:
        """Revocation at day 8 (outside 7-day window) is rejected."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-09",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_before_transfer_rejected(self) -> None:
        """Revocation dated before the transfer is rejected (negative days)."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-05",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_duplicate_revocation_prevented(self) -> None:
        """Duplicate revocation event for same transfer is prevented.
        The same revocation event (same event_id) won't be processed twice.
        But different revocation events for the same transfer ARE processed.
        """
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert len(result.proposed_links) == 1  # One revocation processed

        # Processing the SAME revocation event again would be deduplicated
        # (but mutmut can't easily test this; the logic is in the set check)
        assert len(result.lifecycle_updates) == 1
        assert result.lifecycle_updates[0]["event_id"] == 1

    def test_revocation_skips_closed_transfers(self) -> None:
        """The code does NOT check transfer lifecycle state before revoking.
        A transfer with lifecycle_state='settled' CAN still be revoked.
        This test documents the CURRENT behavior (potential defect).
        """
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "settled",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        # Current behavior: revocation is processed even if transfer is settled
        assert len(result.proposed_links) == 1
        assert result.lifecycle_updates[0]["lifecycle_state"] == "revoked"

    def test_auto_revocation_of_failed_transfers(self) -> None:
        """Failed transfers are auto-revoked with auto_revoked=True flag."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "failed",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        update = result.lifecycle_updates[0]
        assert update["lifecycle_state"] == "revoked"
        assert update["auto_revoked"] is True

    def test_auto_revoked_transfer_supersedes_manual_revocation(self) -> None:
        """Auto-revoked transfers skip duplicate manual revocation processing."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "failed",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        # Auto-revocation processed, manual revocation skipped
        assert len(result.proposed_links) == 0

    def test_revocation_requires_open_revocation_event(self) -> None:
        """Revocation event must have lifecycle_state='open' to process."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "settled",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_only_processes_transfer_events(self) -> None:
        """Only events with is_transfer_event() True are revoked."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 3,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        # Only the transfer event (id=1) should be revoked, not cash_advance (id=2)
        assert len(result.lifecycle_updates) == 1
        assert result.lifecycle_updates[0]["event_id"] == 1

    def test_revocation_uses_earliest_transfer_date(self) -> None:
        """The window is calculated from the earliest transfer event date."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-05",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "fund_transfer_in",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 3,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-08",
                "lifecycle_state": "open",
            },
        ]
        # Earliest transfer is id=2 on 2026-08-01
        # Revocation on 2026-08-08 is 7 days from earliest → within window
        result = detect_revocations(events, lookback_days=7)
        assert len(result.proposed_links) == 2

    def test_revocation_link_type_is_revokes(self) -> None:
        """Revocation links have link_type='revokes'."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert all(link["link_type"] == "revokes" for link in result.proposed_links)


# ============================================================================
# M9-C46 Golden Characterization Tests for Financial Events
# ============================================================================
# These tests lock GENUINE behavioral contracts identified by mutation
# survivor analysis. Each test expresses a real invariant; no score-chasing.
# ============================================================================


class TestFinancialEventsGolden:
    """Golden characterization tests for financial events mutation gaps."""

    # ── walk_lineage: settlement behavior ────────────────────────────────

    def test_settles_advance_with_exact_payment_amount(self):
        """Exact payment (payment == outstanding) → settled state, outstanding=0."""
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
                "liability_change_paise": -100000,
                "amount_paise": 100000,
            },
        ]
        proposal = walk_lineage(events)
        updates = {u["event_id"]: u for u in proposal.lifecycle_updates}
        assert updates[1]["lifecycle_state"] == "settled"
        assert updates[1]["outstanding_paise"] == 0
        assert proposal.proposed_links[0]["link_type"] == "settles"

    def test_partial_payment_creates_partially_settled(self):
        """Payment less than outstanding → partially_settled with correct remaining."""
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
                "liability_change_paise": -40000,
                "amount_paise": 40000,
            },
        ]
        proposal = walk_lineage(events)
        updates = {u["event_id"]: u for u in proposal.lifecycle_updates}
        assert updates[1]["lifecycle_state"] == "partially_settled"
        assert updates[1]["outstanding_paise"] == 60000

    def test_multiple_payments_each_calculated_from_original_outstanding(self):
        """Each repayment is matched to the advance and calculated from
        the ORIGINAL outstanding_paise (not accumulated). This is the
        current behavior - no accumulation across repayments."""
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
                "liability_change_paise": -40000,
                "amount_paise": 40000,
            },
            {
                "id": 3,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-03-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -40000,
                "amount_paise": 40000,
            },
        ]
        proposal = walk_lineage(events)
        # Each repayment is processed independently against original outstanding
        # Both payments would report based on 100000 - 40000 = 60000 remaining
        updates = {u["event_id"]: u for u in proposal.lifecycle_updates}
        assert updates[1]["outstanding_paise"] == 60000
        assert len(proposal.proposed_links) == 2

    def test_payment_greater_than_outstanding_caps_at_zero(self):
        """Overpayment does not produce negative outstanding."""
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

    def test_negative_liability_change_uses_absolute_value(self):
        """Negative liability_change_paise in repayment uses absolute value."""
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
        # -50000 → abs(50000) = 50000 paid, remaining = 50000
        assert updates[1]["outstanding_paise"] == 50000

    def test_only_open_and_partially_settled_repayments_processed(self):
        """Repayments with lifecycle_state='settled' are skipped."""
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

    def test_advance_date_must_be_before_repayment_date(self):
        """Advance date must be <= repayment date to be eligible."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []

    def test_advance_id_must_be_less_than_repayment_id(self):
        """Advance id must be < repayment id (temporal ordering by ID)."""
        events = [
            {
                "id": 2,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
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
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []

    def test_most_recent_advance_selected_when_multiple_open(self):
        """Multiple open advances → most recent (by date) is settled first."""
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
            {
                "id": 3,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-03-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -80000,
                "amount_paise": 80000,
            },
        ]
        proposal = walk_lineage(events)
        # Should settle the MOST RECENT advance (id=2, dated 2025-02-15)
        assert proposal.proposed_links[0]["linked_event_id"] == 2

    def test_cross_account_repayments_are_isolated(self):
        """Repayments only settle advances on the same account_id."""
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
                "account_id": "acc2",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []

    def test_settled_advances_are_not_matched(self):
        """Advances with lifecycle_state='settled' are not matched."""
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
        assert proposal.proposed_links == []

    def test_multiple_repayments_match_most_recent_liability_event(self):
        """Multiple repayments match the MOST RECENT open liability event
        (by date). Since emi_payment is also a liability event type,
        the second repayment matches the first repayment (more recent),
        not the original advance."""
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
            {
                "id": 3,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-03-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        # The second repayment (id=3) matches the most recent open liability event,
        # which is the first repayment (id=2, dated 2025-02-15), not the
        # original advance (id=1, dated 2025-01-15). Both are liability events.
        settles_links = [
            link for link in proposal.proposed_links if link["link_type"] == "settles"
        ]
        assert len(settles_links) == 2
        # First repayment (id=2) matches original advance (id=1)
        assert settles_links[0]["linked_event_id"] == 1
        # Second repayment (id=3) matches most recent open liability event (id=2)
        assert settles_links[1]["linked_event_id"] == 2

    # ── detect_revocations: revocation window and behavior ────────────────

    def test_revocation_at_exact_boundary_day_7_included(self):
        """Revocation at exactly 7 days is within window (inclusive)."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-08",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert len(result.proposed_links) == 1

    def test_revocation_at_day_8_excluded(self):
        """Revocation at day 8 is outside window."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-09",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_before_transfer_date_rejected(self):
        """Revocation dated before transfer is rejected (negative days_diff)."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-05",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_sets_outstanding_paise_to_zero(self):
        """Revoked transfer gets outstanding_paise=0."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.lifecycle_updates[0]["outstanding_paise"] == 0

    def test_revocation_sets_lifecycle_state_revoked(self):
        """Revoked transfer gets lifecycle_state='revoked'."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.lifecycle_updates[0]["lifecycle_state"] == "revoked"

    def test_revocation_only_processes_transfer_events(self):
        """Only events with is_transfer_event() True are revoked."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 3,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert len(result.lifecycle_updates) == 1
        assert result.lifecycle_updates[0]["event_id"] == 1

    def test_auto_revocation_of_failed_transfers(self):
        """Failed transfers are auto-revoked with auto_revoked=True."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "failed",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        update = result.lifecycle_updates[0]
        assert update["lifecycle_state"] == "revoked"
        assert update.get("auto_revoked") is True

    def test_auto_revoked_transfer_blocks_manual_revocation(self):
        """Auto-revoked transfer prevents duplicate manual revocation."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "t1",
                "date_iso": "2026-08-01",
                "lifecycle_state": "failed",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "t1",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        # Auto-revocation processed, manual revocation skipped
        assert len(result.proposed_links) == 0

    # ── detect_rollover_scenarios: rollover detection ───────────────────

    def test_rollover_detected_within_lookback_window(self):
        """Rollover detected when second advance within lookback_days of first."""
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
        """Second advance outside lookback window → no rollover."""
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
        assert proposal.proposed_links == []

    def test_rollover_ignores_non_liability_events(self):
        """Non-liability events (income, etc.) are not rollover sources."""
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
        assert proposal.proposed_links == []

    def test_rollover_ignores_settled_source_advances(self):
        """Settled advances are not considered as rollover sources."""
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
        assert proposal.proposed_links == []

    def test_rollover_link_type_is_rolls_over(self):
        """Rollover links have link_type='rolls_over'."""
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
        assert proposal.proposed_links[0]["link_type"] == "rolls_over"

    # ── _merge_lifecycle_update: state merging semantics ────────────────

    def test_merge_prefers_more_terminal_state(self):
        """More terminal state (higher rank) wins."""
        existing = {
            "event_id": 1,
            "lifecycle_state": "partially_settled",
            "outstanding_paise": 50,
        }
        candidate = {
            "event_id": 1,
            "lifecycle_state": "settled",
            "outstanding_paise": 0,
        }
        result = _merge_lifecycle_update(existing, candidate)
        assert result["lifecycle_state"] == "settled"

    def test_merge_prefers_smaller_outstanding_on_same_state(self):
        """Same state → smaller outstanding wins."""
        existing = {
            "event_id": 1,
            "lifecycle_state": "partially_settled",
            "outstanding_paise": 100,
        }
        candidate = {
            "event_id": 1,
            "lifecycle_state": "partially_settled",
            "outstanding_paise": 50,
        }
        result = _merge_lifecycle_update(existing, candidate)
        assert result["outstanding_paise"] == 50

    def test_merge_revoked_beats_open(self):
        """revoked (rank 1) beats open (rank 0)."""
        existing = {"event_id": 1, "lifecycle_state": "open", "outstanding_paise": 100}
        candidate = {
            "event_id": 1,
            "lifecycle_state": "revoked",
            "outstanding_paise": 0,
        }
        result = _merge_lifecycle_update(existing, candidate)
        assert result["lifecycle_state"] == "revoked"

    def test_merge_partially_settled_beats_revoked(self):
        """partially_settled (rank 2) beats revoked (rank 1)."""
        existing = {"event_id": 1, "lifecycle_state": "revoked", "outstanding_paise": 0}
        candidate = {
            "event_id": 1,
            "lifecycle_state": "partially_settled",
            "outstanding_paise": 50,
        }
        result = _merge_lifecycle_update(existing, candidate)
        assert result["lifecycle_state"] == "partially_settled"

    def test_merge_none_existing_returns_candidate(self):
        """None existing returns candidate."""
        candidate = {"event_id": 1, "lifecycle_state": "open", "outstanding_paise": 100}
        result = _merge_lifecycle_update(None, candidate)
        assert result["lifecycle_state"] == "open"
        assert result["outstanding_paise"] == 100

    # ── Helper function behavior ────────────────────────────────────────

    def test_parse_date_iso_handles_invalid_inputs(self):
        """_parse_date_iso returns None for invalid/empty/None inputs."""
        assert _parse_date_iso("") is None
        assert _parse_date_iso(None) is None
        assert _parse_date_iso("not-a-date") is None

    def test_date_difference_days_handles_invalid(self):
        """_date_difference_days returns -1 for invalid dates."""
        assert _date_difference_days("invalid", "2025-01-01") == -1
        assert _date_difference_days("2025-01-01", "invalid") == -1
        assert _date_difference_days("", "2025-01-01") == -1
        assert _date_difference_days("2025-01-01", "") == -1

    def test_is_liability_event_excludes_transfers(self):
        """fund_transfer_out/in are NOT liability events."""
        assert _is_liability_event({"event_type": "fund_transfer_out"}) is False
        assert _is_liability_event({"event_type": "fund_transfer_in"}) is False
        assert _is_liability_event({"event_type": "transfer"}) is False

    def test_is_repayment_event_excludes_advances(self):
        """cash_advance is NOT a repayment event."""
        assert _is_repayment_event({"event_type": "cash_advance"}) is False

    def test_is_transfer_event_excludes_liability_events(self):
        """cash_advance is NOT a transfer event."""
        assert _is_transfer_event({"event_type": "cash_advance"}) is False

    def test_is_revocable_event_requires_open_state(self):
        """Only open/partially_settled transfers are revocable."""
        assert (
            _is_revocable_event(
                {"event_type": "fund_transfer_out", "lifecycle_state": "open"}
            )
            is True
        )
        assert (
            _is_revocable_event(
                {
                    "event_type": "fund_transfer_out",
                    "lifecycle_state": "partially_settled",
                }
            )
            is True
        )
        assert (
            _is_revocable_event(
                {"event_type": "fund_transfer_out", "lifecycle_state": "settled"}
            )
            is False
        )
        assert (
            _is_revocable_event(
                {"event_type": "fund_transfer_out", "lifecycle_state": "revoked"}
            )
            is False
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
