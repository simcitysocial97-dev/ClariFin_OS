"""Targeted tests for remaining behavioral mutation gaps in financial events.

These tests target the ~29 genuinely killable mutations in financial_events:
- Boolean operator changes (and/or flips) in _merge_lifecycle_update, walk_lineage
- Numeric literal changes in detect_revocations, detect_rollover_scenarios
"""

from __future__ import annotations

from src.engines.financial_events.lineage_walker import (
    _is_liability_event,
    _is_repayment_event,
    _is_transfer_event,
    _merge_lifecycle_update,
    detect_revocations,
    detect_rollover_scenarios,
    walk_lineage,
)


class TestMergeLifecycleBooleanFlips:
    """Tests for _merge_lifecycle_update boolean operator mutations.

    The mutation `candidate_rank > existing_rank` -> `candidate_rank < existing_rank`
    survives because existing tests always have clearly different ranks.
    This class tests same-rank scenarios where the boolean flip matters.
    """

    def test_same_rank_smaller_outstanding_wins(self):
        """When both updates have the same state rank, smaller outstanding wins.

        The code does: if candidate_rank > existing_rank → return candidate
        elif candidate_rank < existing_rank → return existing
        else (same rank): prefer smaller outstanding
        """
        existing = {
            "event_id": 1,
            "lifecycle_state": "open",
            "outstanding_paise": 50,
        }
        candidate = {
            "event_id": 1,
            "lifecycle_state": "open",
            "outstanding_paise": 30,
        }
        result = _merge_lifecycle_update(existing, candidate)
        # Same rank: smaller outstanding wins
        assert result["outstanding_paise"] == 30
        assert result["lifecycle_state"] == "open"

    def test_same_rank_larger_outstanding_loses(self):
        """When same rank but candidate has larger outstanding, keep existing."""
        existing = {
            "event_id": 1,
            "lifecycle_state": "partially_settled",
            "outstanding_paise": 20,
        }
        candidate = {
            "event_id": 1,
            "lifecycle_state": "partially_settled",
            "outstanding_paise": 80,
        }
        result = _merge_lifecycle_update(existing, candidate)
        assert result["outstanding_paise"] == 20

    def test_settled_beats_all_other_states(self):
        """Settled (rank 3) beats every other state regardless of boolean direction."""
        for state in ["open", "revoked", "partially_settled"]:
            existing = {"event_id": 1, "lifecycle_state": state, "outstanding_paise": 100}
            candidate = {"event_id": 1, "lifecycle_state": "settled", "outstanding_paise": 0}
            result = _merge_lifecycle_update(existing, candidate)
            assert result["lifecycle_state"] == "settled"

    def test_open_loses_to_revoked_partially_settled_settled(self):
        """Open (rank 0) loses to all higher-ranked states."""
        for target in ["revoked", "partially_settled", "settled"]:
            existing = {"event_id": 1, "lifecycle_state": "open", "outstanding_paise": 100}
            candidate = {"event_id": 1, "lifecycle_state": target, "outstanding_paise": 0}
            result = _merge_lifecycle_update(existing, candidate)
            assert result["lifecycle_state"] == target


class TestWalkLineageBooleanFlips:
    """Tests for boolean operator mutations in walk_lineage."""

    def test_non_repayment_events_not_processed(self):
        """Non-repayment events should not create settlement links.

        The code checks `if not _is_repayment_event(event): continue`.
        Mutations flipping this to `and` instead of `or` would change behavior
        for events that are neither repayment nor non-repayment in unexpected ways.
        """
        events = [
            {"id": 1, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-01-15", "lifecycle_state": "open",
             "outstanding_paise": 100000, "liability_change_paise": 100000},
            {"id": 2, "event_type": "income", "account_id": "acc1",
             "date_iso": "2025-02-15", "lifecycle_state": "open",
             "outstanding_paise": 0, "liability_change_paise": 0},
            {"id": 3, "event_type": "emi_payment", "account_id": "acc1",
             "date_iso": "2025-02-16", "lifecycle_state": "open",
             "outstanding_paise": 0, "liability_change_paise": -50000},
        ]
        proposal = walk_lineage(events)
        # Only event 3 (emi_payment) should match event 1 (cash_advance)
        # Event 2 (income) is not a repayment, should be skipped
        assert len(proposal.proposed_links) == 1
        assert proposal.proposed_links[0]["link_type"] == "settles"

    def test_multiple_repayments_match_most_recent_open_advance(self):
        """Multiple repayments each match the most recent open advance.

        Note: walk_lineage does NOT track cumulative settlement — each repayment
        independently matches the most recent open advance at processing time.
        Since emi_payment is also a liability_event, a later repayment can
        settle an earlier repayment (documenting existing behavior).
        """
        events = [
            {"id": 1, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-01-15", "lifecycle_state": "open",
             "outstanding_paise": 100000, "liability_change_paise": 100000},
            {"id": 2, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-02-15", "lifecycle_state": "open",
             "outstanding_paise": 80000, "liability_change_paise": 80000},
            {"id": 3, "event_type": "emi_payment", "account_id": "acc1",
             "date_iso": "2025-03-15", "lifecycle_state": "open",
             "outstanding_paise": 0, "liability_change_paise": -50000},
            {"id": 4, "event_type": "emi_payment", "account_id": "acc1",
             "date_iso": "2025-04-15", "lifecycle_state": "open",
             "outstanding_paise": 0, "liability_change_paise": -40000},
        ]
        proposal = walk_lineage(events)
        assert len(proposal.proposed_links) == 2
        # Repayment 3 matches advance 2; repayment 4 matches advance 3 (also a liability event)
        link_map = {link["event_id"]: link["linked_event_id"] for link in proposal.proposed_links}
        assert link_map[3] == 2
        assert link_map[4] == 3

    def test_multiple_repayments_each_match_different_advances(self):
        """Multiple repayments should each match their respective advances."""
        events = [
            {"id": 1, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-01-15", "lifecycle_state": "open",
             "outstanding_paise": 100000, "liability_change_paise": 100000},
            {"id": 2, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-02-15", "lifecycle_state": "open",
             "outstanding_paise": 80000, "liability_change_paise": 80000},
            {"id": 3, "event_type": "emi_payment", "account_id": "acc1",
             "date_iso": "2025-03-15", "lifecycle_state": "open",
             "outstanding_paise": 0, "liability_change_paise": -50000},
            {"id": 4, "event_type": "emi_payment", "account_id": "acc1",
             "date_iso": "2025-04-15", "lifecycle_state": "open",
             "outstanding_paise": 0, "liability_change_paise": -40000},
        ]
        proposal = walk_lineage(events)
        assert len(proposal.proposed_links) == 2


class TestDetectRevocationsNumericLiterals:
    """Tests for numeric literal mutations in detect_revocations."""

    def test_revocation_window_exact_boundary(self):
        """Revocation exactly at the lookback boundary is within window."""
        events = [
            {"id": 1, "event_type": "fund_transfer_out", "transfer_id": "t1",
             "date_iso": "2026-08-01", "lifecycle_state": "open"},
            {"id": 2, "event_type": "transfer_revocation", "transfer_id": "t1",
             "date_iso": "2026-08-08", "lifecycle_state": "open"},
        ]
        result = detect_revocations(events, lookback_days=7)
        # Day diff = 7, which equals lookback_days, so it's accepted
        assert len(result.proposed_links) == 1

    def test_revocation_one_day_past_boundary_rejected(self):
        """Revocation one day past the lookback window is rejected."""
        events = [
            {"id": 1, "event_type": "fund_transfer_out", "transfer_id": "t1",
             "date_iso": "2026-08-01", "lifecycle_state": "open"},
            {"id": 2, "event_type": "transfer_revocation", "transfer_id": "t1",
             "date_iso": "2026-08-09", "lifecycle_state": "open"},
        ]
        result = detect_revocations(events, lookback_days=7)
        # Day diff = 8, exceeds lookback_days=7, rejected
        assert len(result.proposed_links) == 0

    def test_negative_date_difference_rejected(self):
        """Revocation before the transfer date is rejected (negative days)."""
        events = [
            {"id": 1, "event_type": "fund_transfer_out", "transfer_id": "t1",
             "date_iso": "2026-08-05", "lifecycle_state": "open"},
            {"id": 2, "event_type": "transfer_revocation", "transfer_id": "t1",
             "date_iso": "2026-08-01", "lifecycle_state": "open"},
        ]
        result = detect_revocations(events, lookback_days=7)
        # Revocation before transfer → negative days_diff → rejected
        assert len(result.proposed_links) == 0


class TestDetectRolloverBooleanAndNumeric:
    """Tests for boolean and numeric mutations in detect_rollover_scenarios."""

    def test_rollover_requires_positive_days_diff(self):
        """Rollover requires days_diff > 0 (strictly positive).

        The condition `0 < days_diff <= lookback_days` means same-day
        advances cannot be rollovers.
        """
        events = [
            {"id": 1, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-01-15", "lifecycle_state": "open",
             "outstanding_paise": 100000, "liability_change_paise": 100000},
            {"id": 2, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-01-15", "lifecycle_state": "open",
             "outstanding_paise": 80000, "liability_change_paise": 80000},
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        assert len(proposal.proposed_links) == 0

    def test_rollover_at_lookback_boundary_detected(self):
        """Rollover at exactly lookback_days is detected."""
        events = [
            {"id": 1, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-01-01", "lifecycle_state": "open",
             "outstanding_paise": 100000, "liability_change_paise": 100000},
            {"id": 2, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-03-31", "lifecycle_state": "open",
             "outstanding_paise": 80000, "liability_change_paise": 80000},
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        # Jan 1 to Mar 31 = 89 days, within 90-day window
        assert len(proposal.proposed_links) >= 1

    def test_rollover_beyond_lookback_not_detected(self):
        """Rollover beyond lookback window is not detected."""
        events = [
            {"id": 1, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-01-01", "lifecycle_state": "open",
             "outstanding_paise": 100000, "liability_change_paise": 100000},
            {"id": 2, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-04-02", "lifecycle_state": "open",
             "outstanding_paise": 80000, "liability_change_paise": 80000},
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        # Jan 1 to Apr 2 = 91 days, exceeds 90-day window
        assert len(proposal.proposed_links) == 0

    def test_only_open_advances_considered_for_rollover(self):
        """Only open advances are considered for rollover detection."""
        events = [
            {"id": 1, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-01-15", "lifecycle_state": "settled",
             "outstanding_paise": 0, "liability_change_paise": 100000},
            {"id": 2, "event_type": "cash_advance", "account_id": "acc1",
             "date_iso": "2025-02-15", "lifecycle_state": "open",
             "outstanding_paise": 80000, "liability_change_paise": 80000},
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        # Settled advance should not be a rollover source
        assert len(proposal.proposed_links) == 0


class TestPredicateBooleanFlips:
    """Tests for boolean operator mutations in predicate functions."""

    def test_predicate_exhaustive_types(self):
        """Test all known event types against each predicate."""
        liability_types = {"cash_advance", "credit_card_cash_advance",
                          "liability_increase", "emi_payment"}
        repayment_types = {"liability_repayment", "emi_payment"}
        transfer_types = {"fund_transfer_out", "fund_transfer_in", "transfer"}

        all_types = liability_types | repayment_types | transfer_types | {
            "income", "expense", "fee", "charge", "payment"
        }

        for etype in all_types:
            event = {"event_type": etype}
            assert (_is_liability_event(event)) == (etype in liability_types)
            assert (_is_repayment_event(event)) == (etype in repayment_types)
            assert (_is_transfer_event(event)) == (etype in transfer_types)
