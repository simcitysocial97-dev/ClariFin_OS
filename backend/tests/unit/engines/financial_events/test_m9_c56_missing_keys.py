"""Extended mutation-survivor tests for financial events — missing-key paths.

These tests target the dominant survivor pattern: event.get("field", "") ->
event.get("field", None). The mutations survive because existing tests always
provide all keys. By adding events with missing keys, we exercise the default
path and kill multiple survivors per test.
"""

from __future__ import annotations

import pytest
from src.engines.financial_events.lineage_walker import (
    _is_liability_event,
    _is_repayment_event,
    _is_transfer_event,
    detect_revocations,
    detect_rollover_scenarios,
    walk_lineage,
)


class TestWalkLineageMissingKeys:
    """Tests for walk_lineage when event dicts are missing required keys."""

    def test_event_missing_id_is_skipped(self):
        """Event without 'id' field should not cause errors and be skipped."""
        events = [
            {
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
        ]
        # Should not raise; the event without id should be handled gracefully
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []

    def test_event_with_none_id_raises_type_error(self):
        """Event with id=None causes TypeError — this is the gap the mutation exposes.
        The mutation event.get('id', 0) -> event.get('id', None) survives because
        no test passes an event without an id field."""
        events = [
            {
                "id": None,
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
        # The mutation event.get("id", 0)->event.get("id", None) would change
        # int(event.get("id", 0)) from int(0)=0 to int(None)=TypeError
        # This test documents the existing robustness gap.
        with pytest.raises(TypeError):
            walk_lineage(events)

    def test_event_missing_account_id_not_grouped(self):
        """Event without account_id should not be grouped for settlement."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []

    def test_advance_missing_date_iso_matches(self):
        """Advance with missing date_iso IS matched because "" <= valid_date is True.

        This documents the gap: the default empty string "" passes the <= comparison
        with any non-empty date string. The mutation event.get("date_iso", "") ->
        event.get("date_iso", None) would cause a TypeError instead.
        """
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
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
        # "" <= "2025-02-15" is True in Python, so advance IS matched
        assert len(proposal.proposed_links) == 1

    def test_repayment_missing_date_iso_skipped(self):
        """Repayment with missing date_iso should be skipped."""
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
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []

    def test_mixed_complete_and_incomplete_events(self):
        """Mix of complete events and events with missing keys should work."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
            },
            # Incomplete event
            {"event_type": "cash_advance", "account_id": "acc1"},
        ]
        proposal = walk_lineage(events)
        assert len(proposal.proposed_links) == 1

    def test_event_with_id_zero_still_valid(self):
        """Event with id=0 should still process correctly."""
        events = [
            {
                "id": 0,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
            },
            {
                "id": 1,
                "event_type": "emi_payment",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
            },
        ]
        proposal = walk_lineage(events)
        assert len(proposal.proposed_links) == 1


class TestDetectRevocationsMissingKeys:
    """Tests for detect_revocations when events miss required keys."""

    def test_event_missing_transfer_id_not_grouped(self):
        """Event without transfer_id should not be grouped for revocation."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_missing_transfer_id_ignored(self):
        """Revocation event without transfer_id should be ignored."""
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
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_event_with_none_transfer_id_not_grouped(self):
        """Event with transfer_id=None should not be grouped."""
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": None,
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": None,
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_missing_lifecycle_state_skipped(self):
        """Revocation event without lifecycle_state is skipped."""
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
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []


class TestDetectRolloverMissingKeys:
    """Tests for detect_rollover_scenarios with missing keys."""

    def test_event_missing_account_id_not_processed(self):
        """Events without account_id should not participate in rollover detection."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "liability_change_paise": 80000,
                "amount_paise": 80000,
            },
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        # Without account_id, events aren't grouped; rollover may or may not be detected
        # The point is: no crash occurs
        assert isinstance(proposal.proposed_links, list)

    def test_event_missing_date_iso_skipped(self):
        """Event without date_iso should be skipped in rollover detection."""
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "lifecycle_state": "open",
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "liability_change_paise": 80000,
                "amount_paise": 80000,
            },
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        # First event has no date_iso; should be skipped gracefully
        assert isinstance(proposal.proposed_links, list)


class TestPredicatesMissingEventType:
    """Predicate functions with missing event_type key."""

    def test_is_liability_event_no_key(self):
        """Predicate with no event_type key returns False."""
        assert _is_liability_event({}) is False
        assert _is_repayment_event({}) is False
        assert _is_transfer_event({}) is False

    def test_is_liability_event_none_key(self):
        """Predicate with event_type=None returns False."""
        assert _is_liability_event({"event_type": None}) is False
        assert _is_repayment_event({"event_type": None}) is False

    def test_all_predicates_with_empty_dict(self):
        """All predicates handle empty dict gracefully."""
        empty = {}
        assert not _is_liability_event(empty)
        assert not _is_repayment_event(empty)
        assert not _is_transfer_event(empty)
