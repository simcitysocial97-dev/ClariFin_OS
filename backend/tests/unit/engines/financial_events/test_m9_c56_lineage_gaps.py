"""Targeted mutation-survivor tests for financial events lineage walker.

These tests address the highest-priority genuine behavioral gaps identified by
C56 gap analysis. Each test targets specific mutation survivors that reveal
missing boundary assertions, weak default-value handling, and unexercised
defensive paths.

Classification: Category B (High Coverage / Low Mutation) — code executes but
tests fail to distinguish behavioral changes at boundaries.
"""

from __future__ import annotations

import pytest
from src.engines.financial_events.lineage_walker import (
    DEFAULT_REVOCATION_LOOKBACK_DAYS,
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
# walk_lineage: date_iso boundary handling
# Targets: 73 control_flow survivors in x_walk_lineage
# Mutation pattern: event.get("date_iso", "") -> event.get("date_iso", None)
# ============================================================================


class TestWalkLineageDateBoundary:
    """Tests for date_iso boundary conditions in walk_lineage.

    The mutation survivors reveal that changing the default value of
    event.get("date_iso", "") to None is not detected by existing tests.
    This means the code path where date_iso is missing is unexercised.
    """

    def test_advance_with_empty_date_iso_matches(self):
        """Advance with empty date_iso IS matched due to string comparison.

        The comparison `e.get("date_iso", "") <= event_date_iso` uses empty
        string as default. Since "" <= any non-empty date string in Python,
        advances with empty date_iso ARE matched. This test documents the
        actual behavior that the mutation `"" -> None` would change.
        """
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "",
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
        assert len(proposal.proposed_links) == 1
        assert proposal.proposed_links[0]["link_type"] == "settles"

    def test_advance_with_missing_date_iso_matches(self):
        """Advance with missing date_iso key IS matched.

        When date_iso is absent, event.get("date_iso", "") returns "".
        The empty string satisfies "" <= "2025-02-15", so the advance IS
        matched. This documents behavior that `"" -> None` would break.
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
        assert len(proposal.proposed_links) == 1

    def test_repayment_with_empty_date_iso_skipped(self):
        """Repayment with empty date_iso should not settle any advance.

        The date comparison `e.get("date_iso", "") <= event_date_iso`
        must handle empty strings correctly.
        """
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
                "date_iso": "",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []

    def test_same_date_advance_and_repayment_settles(self):
        """Advance and repayment on same date should settle (<= comparison).

        This tests the boundary: advance_date <= repayment_date when
        both dates are equal. The <= operator must include equality.
        """
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
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        assert len(proposal.proposed_links) == 1
        assert proposal.proposed_links[0]["link_type"] == "settles"


# ============================================================================
# walk_lineage: account_id boundary handling
# Targets: control_flow survivors in x_walk_lineage
# Mutation pattern: event.get("account_id", "") -> event.get("account_id", None)
# ============================================================================


class TestWalkLineageAccountIdBoundary:
    """Tests for account_id boundary conditions."""

    def test_event_with_empty_account_id_not_grouped(self):
        """Event with empty account_id should not be grouped for settlement.

        The code checks `if acc_id:` before grouping. Empty string is falsy,
        so events with empty account_id must be excluded from grouping.
        """
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "",
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "emi_payment",
                "account_id": "",
                "date_iso": "2025-02-15",
                "lifecycle_state": "open",
                "outstanding_paise": 0,
                "liability_change_paise": -50000,
                "amount_paise": 50000,
            },
        ]
        proposal = walk_lineage(events)
        assert proposal.proposed_links == []

    def test_event_with_missing_account_id_not_grouped(self):
        """Event with missing account_id key should not be grouped."""
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


# ============================================================================
# detect_revocations: transfer_id boundary handling
# Targets: 64 control_flow survivors in x_detect_revocations
# Mutation pattern: event.get("transfer_id", "") -> event.get("transfer_id", None)
# ============================================================================


class TestDetectRevocationsTransferIdBoundary:
    """Tests for transfer_id boundary conditions in detect_revocations."""

    def test_event_with_empty_transfer_id_not_grouped(self):
        """Event with empty transfer_id should not be grouped.

        The code checks `if transfer_id and _is_transfer_event(event):`
        before grouping. Empty string is falsy.
        """
        events = [
            {
                "id": 1,
                "event_type": "fund_transfer_out",
                "transfer_id": "",
                "date_iso": "2026-08-01",
                "lifecycle_state": "open",
            },
            {
                "id": 2,
                "event_type": "transfer_revocation",
                "transfer_id": "",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_with_mismatched_transfer_id_ignored(self):
        """Revocation for a transfer_id with no matching transfer is ignored."""
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
                "transfer_id": "t2",
                "date_iso": "2026-08-03",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_at_exact_lookback_boundary(self):
        """Revocation at exactly lookback_days boundary is accepted.

        The mutation `days_diff > lookback_days` -> `days_diff >= lookback_days`
        survives because the boundary is not tested. At exactly 7 days,
        the revocation should be accepted (days_diff <= lookback_days).
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
                "date_iso": "2026-08-08",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert len(result.proposed_links) == 1

    def test_revocation_one_day_past_boundary_rejected(self):
        """Revocation one day past lookback window is rejected.

        At days_diff = 8 with lookback_days = 7, the revocation must
        be rejected (days_diff > lookback_days).
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
                "date_iso": "2026-08-09",
                "lifecycle_state": "open",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []


# ============================================================================
# detect_rollover_scenarios: comparison boundary
# Targets: 48 control_flow survivors in x_detect_rollover_scenarios
# Mutation pattern: 0 < days_diff <= lookback_days boundary changes
# ============================================================================


class TestDetectRolloverBoundary:
    """Tests for rollover detection boundary conditions."""

    def test_rollover_at_day_zero_not_detected(self):
        """Rollover at day_diff=0 should NOT be detected.

        The condition is `0 < days_diff <= lookback_days`.
        At days_diff=0, the rollover must not be detected.
        """
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
                "date_iso": "2025-01-15",
                "lifecycle_state": "open",
                "outstanding_paise": 80000,
                "liability_change_paise": 80000,
                "amount_paise": 80000,
            },
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        assert len(proposal.proposed_links) == 0

    def test_rollover_at_day_one_detected(self):
        """Rollover at day_diff=1 should be detected.

        The condition `0 < days_diff` must include day 1.
        """
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
                "date_iso": "2025-01-16",
                "lifecycle_state": "open",
                "outstanding_paise": 80000,
                "liability_change_paise": 80000,
                "amount_paise": 80000,
            },
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        assert len(proposal.proposed_links) == 1

    def test_rollover_at_exact_lookback_boundary(self):
        """Rollover at exactly lookback_days should be detected.

        The condition `days_diff <= lookback_days` must include equality.
        """
        events = [
            {
                "id": 1,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-01-01",
                "lifecycle_state": "open",
                "outstanding_paise": 100000,
                "liability_change_paise": 100000,
                "amount_paise": 100000,
            },
            {
                "id": 2,
                "event_type": "cash_advance",
                "account_id": "acc1",
                "date_iso": "2025-03-31",
                "lifecycle_state": "open",
                "outstanding_paise": 80000,
                "liability_change_paise": 80000,
                "amount_paise": 80000,
            },
        ]
        proposal = detect_rollover_scenarios(events, lookback_days=90)
        assert len(proposal.proposed_links) == 1


# ============================================================================
# _merge_lifecycle_update: default value boundary
# Targets: 31 control_flow survivors in x__merge_lifecycle_update
# Mutation pattern: existing.get("lifecycle_state", "open") -> None
# ============================================================================


class TestMergeLifecycleBoundary:
    """Tests for _merge_lifecycle_update default value handling."""

    def test_merge_with_none_existing_returns_candidate(self):
        """When existing is None, candidate is returned unchanged."""
        candidate = {"event_id": 1, "lifecycle_state": "settled", "outstanding_paise": 0}
        result = _merge_lifecycle_update(None, candidate)
        assert result == candidate

    def test_merge_existing_with_missing_state_uses_open_default(self):
        """Existing update with missing lifecycle_state uses 'open' default.

        The code does: existing.get("lifecycle_state", "open").
        When lifecycle_state is missing, it defaults to 'open' (rank 0).
        """
        existing = {"event_id": 1, "outstanding_paise": 50}
        candidate = {"event_id": 1, "lifecycle_state": "settled", "outstanding_paise": 0}
        result = _merge_lifecycle_update(existing, candidate)
        assert result["lifecycle_state"] == "settled"

    def test_merge_both_same_state_smaller_outstanding_wins(self):
        """When both updates have same state, smaller outstanding wins."""
        existing = {"event_id": 1, "lifecycle_state": "partially_settled", "outstanding_paise": 100}
        candidate = {"event_id": 1, "lifecycle_state": "partially_settled", "outstanding_paise": 50}
        result = _merge_lifecycle_update(existing, candidate)
        assert result["outstanding_paise"] == 50

    def test_merge_settled_beats_partially_settled(self):
        """Settled state (rank 3) beats partially_settled (rank 2)."""
        existing = {"event_id": 1, "lifecycle_state": "partially_settled", "outstanding_paise": 50}
        candidate = {"event_id": 1, "lifecycle_state": "settled", "outstanding_paise": 0}
        result = _merge_lifecycle_update(existing, candidate)
        assert result["lifecycle_state"] == "settled"

    def test_merge_open_loses_to_revoked(self):
        """Revoked state (rank 1) beats open state (rank 0)."""
        existing = {"event_id": 1, "lifecycle_state": "open", "outstanding_paise": 100}
        candidate = {"event_id": 1, "lifecycle_state": "revoked", "outstanding_paise": 0}
        result = _merge_lifecycle_update(existing, candidate)
        assert result["lifecycle_state"] == "revoked"


# ============================================================================
# Predicate functions: missing event_type handling
# Targets: control_flow survivors in x__is_*_event functions
# Mutation pattern: event.get("event_type", "") -> event.get("event_type", None)
# ============================================================================


class TestPredicateMissingEventType:
    """Tests for predicate functions when event_type is missing.

    The mutation `event.get("event_type", "")` -> `event.get("event_type", None)`
    survives because tests always provide event_type. When missing, the
    default value changes behavior.
    """

    def test_is_liability_event_with_missing_type(self):
        """Event with missing event_type is not a liability event."""
        assert _is_liability_event({}) is False

    def test_is_repayment_event_with_missing_type(self):
        """Event with missing event_type is not a repayment event."""
        assert _is_repayment_event({}) is False

    def test_is_transfer_event_with_missing_type(self):
        """Event with missing event_type is not a transfer event."""
        assert _is_transfer_event({}) is False

    def test_is_revocable_event_with_missing_type(self):
        """Event with missing event_type is not revocable."""
        assert _is_revocable_event({}) is False

    def test_is_liability_event_with_none_type(self):
        """Event with None event_type is not a liability event."""
        assert _is_liability_event({"event_type": None}) is False

    def test_is_repayment_event_with_none_type(self):
        """Event with None event_type is not a repayment event."""
        assert _is_repayment_event({"event_type": None}) is False


# ============================================================================
# _parse_date_iso: boundary conditions
# ============================================================================


class TestParseDateIsoBoundary:
    """Tests for _parse_date_iso boundary conditions."""

    def test_parse_none_returns_none(self):
        """Parsing None returns None."""
        assert _parse_date_iso(None) is None

    def test_parse_empty_string_returns_none(self):
        """Parsing empty string returns None."""
        assert _parse_date_iso("") is None

    def test_parse_valid_date(self):
        """Parsing valid ISO date returns datetime."""
        from datetime import datetime
        result = _parse_date_iso("2025-01-15")
        assert result == datetime(2025, 1, 15)


# ============================================================================
# detect_revocations: lifecycle_state default handling
# Targets: control_flow survivors
# Mutation pattern: event.get("lifecycle_state", "") -> event.get("lifecycle_state", None)
# ============================================================================


class TestDetectRevocationsLifecycleBoundary:
    """Tests for lifecycle_state default in detect_revocations."""

    def test_revocation_event_with_empty_lifecycle_state_skipped(self):
        """Revocation event with empty lifecycle_state is not processed.

        The code checks `lifecycle_state != "open"` to skip.
        Empty string != "open", so it's skipped.
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
                "lifecycle_state": "",
            },
        ]
        result = detect_revocations(events, lookback_days=7)
        assert result.proposed_links == []

    def test_revocation_event_with_missing_lifecycle_state_skipped(self):
        """Revocation event with missing lifecycle_state is skipped."""
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
