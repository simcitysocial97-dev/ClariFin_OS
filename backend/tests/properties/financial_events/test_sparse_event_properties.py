"""
Sparse-event contract for the financial-events lineage walker — M9-C71.

`walk_lineage`, `detect_revocations` and `detect_rollover_scenarios` read
upstream payload fields with documented defaults:

    event.get("account_id", "")          an event with no account is not grouped
    event.get("id", 0)                   an event with no id is event 0
    event.get("lifecycle_state", ...)    see TestLifecycleStateDefault
    event.get("date_iso", "")            an event with no date sorts first
    event.get("event_type", "")          an event with no type is inert
    event.get("transfer_id", "")         an event with no transfer is unlinked

These are load-bearing: the walker ingests event dicts assembled by several
upstream producers, and a producer that omits an optional field must not
silently change the lineage that gets written.

The mutation campaign showed the opposite. Every one of those `event.get(...)`
default-value mutants SURVIVED the existing suite (181 survivors across
`walk_lineage`, `detect_revocations` and `detect_rollover_scenarios` alone),
because every pre-existing fixture supplied every field, so the default branch
was never executed and could not be observed.

Note on technique: `dict.get(key, default)` only substitutes the default when
the key is ABSENT, so every case here OMITS the key rather than setting it to
`None`. A mutation that swaps a default for `None` is behaviourally
indistinguishable for an absent key; these tests pin the defaults that are
observable in the returned proposal (link ids, ordering, grouping).

Each test names the default it pins, so a failure reports which contract broke.
"""

from __future__ import annotations

from src.engines.financial_events.lineage_walker import (
    detect_revocations,
    detect_rollover_scenarios,
    walk_lineage,
)

_MISSING = object()


def _without(event: dict, *keys: str) -> dict:
    """Copy of *event* with *keys* removed (so `.get` takes its default)."""
    out = dict(event)
    for key in keys:
        out.pop(key, None)
    return out


def _advance(**overrides):
    """A cash advance with the full field set, minus anything overridden."""
    event = {
        "id": 1,
        "account_id": "acc_liability",
        "event_type": "cash_advance",
        "date_iso": "2025-01-01",
        "lifecycle_state": "open",
        "outstanding_paise": 100_000,
        "liability_change_paise": 100_000,
    }
    event.update(overrides)
    return event


def _repayment(**overrides):
    """A repayment with the full field set, minus anything overridden."""
    event = {
        "id": 2,
        "account_id": "acc_liability",
        "event_type": "liability_repayment",
        "date_iso": "2025-01-05",
        "lifecycle_state": "open",
        "outstanding_paise": 0,
        "liability_change_paise": -40_000,
    }
    event.update(overrides)
    return event


def _settles(proposal) -> list[dict]:
    return [x for x in proposal.proposed_links if x["link_type"] == "settles"]


# ── account_id default: "" → falsy → the event is not grouped ───────────────


class TestAccountIdDefault:
    def test_repayment_without_account_id_produces_no_settlement(self):
        """No account_id → the repayment is grouped under the empty key, which
        holds no advances, so no `settles` link may be produced.

        The default must stay falsy. A truthy sentinel would let an
        account-less payment match an unrelated advance and write a bogus link.
        """
        proposal = walk_lineage([_advance(), _without(_repayment(), "account_id")])
        assert _settles(proposal) == []
        assert proposal.lifecycle_updates == []

    def test_advance_without_account_id_is_not_a_settlement_candidate(self):
        """No account_id → the advance is invisible to the liability group, so
        the repayment finds no counterpart."""
        proposal = walk_lineage([_without(_advance(), "account_id"), _repayment()])
        assert _settles(proposal) == []

    def test_both_without_account_id_is_inert(self):
        proposal = walk_lineage(
            [_without(_advance(), "account_id"), _without(_repayment(), "account_id")]
        )
        assert _settles(proposal) == []
        assert proposal.superseded_events == []

    def test_explicit_empty_account_id_behaves_like_the_absent_default(self):
        """`account_id=""` and an absent account_id must be indistinguishable:
        the grouping guard is `if acc_id:`, so the empty string is falsy exactly
        like the `""` default. This pins that the two paths agree."""
        absent = walk_lineage([_advance(), _without(_repayment(), "account_id")])
        empty = walk_lineage([_advance(), _repayment(account_id="")])
        assert absent.proposed_links == empty.proposed_links

    def test_matched_pair_still_settles(self):
        """Control: the same pair WITH account_id settles. Without this the
        assertions above would be satisfied by any behaviour at all."""
        proposal = walk_lineage([_advance(), _repayment()])
        assert len(_settles(proposal)) == 1


# ── lifecycle_state default ────────────────────────────────────────────────


class TestLifecycleStateDefault:
    def test_advance_without_lifecycle_state_is_excluded(self):
        """No lifecycle_state on the advance → the candidate filter
        `e.get("lifecycle_state") in ("open", "partially_settled")` reads
        `None`, which is not in the vocabulary, so the advance is not a
        candidate. Only the repayment side consults the `"open"` default.

        The default must not smuggle an advance into the settleable set.
        """
        proposal = walk_lineage(
            [_without(_advance(), "lifecycle_state"), _repayment()]
        )
        assert _settles(proposal) == []

    def test_repayment_without_lifecycle_state_is_excluded(self):
        """No lifecycle_state on the repayment → the main loop's
        `event.get("lifecycle_state", "open")` reads `"open"` and the payment
        proceeds; but its advance counterpart still has to satisfy the
        candidate filter, so an otherwise-valid pair does settle. This pins
        that the repayment-side default is the *permissive* one."""
        proposal = walk_lineage(
            [_advance(), _without(_repayment(), "lifecycle_state")]
        )
        assert len(_settles(proposal)) == 1

    def test_advance_without_state_and_repayment_with_state_still_settles(self):
        """The asymmetry above is the contract: the candidate filter is strict
        about the advance, the main loop is permissive about the repayment."""
        proposal = walk_lineage(
            [_without(_advance(), "lifecycle_state"), _repayment()]
        )
        assert _settles(proposal) == []

    def test_settled_state_still_excludes_the_advance(self):
        """Control: an explicit terminal state excludes the advance too."""
        proposal = walk_lineage(
            [_advance(lifecycle_state="settled"), _repayment()]
        )
        assert _settles(proposal) == []

    def test_partially_settled_advance_remains_a_candidate(self):
        """Control: the permissive state is accepted, so the strictness above
        is about the missing key, not about the filter."""
        proposal = walk_lineage(
            [_advance(lifecycle_state="partially_settled"), _repayment()]
        )
        assert len(_settles(proposal)) == 1


# ── id default: 0 → observable in the returned proposal ────────────────────


class TestIdDefault:
    def test_advance_without_id_is_matched_as_event_zero(self):
        """No id on the advance → `event.get("id", 0)`, and the proposal
        surfaces that id verbatim, so the default is directly observable: the
        link's `linked_event_id` and the lifecycle update's `event_id` must
        both be the integer 0."""
        proposal = walk_lineage([_without(_advance(), "id"), _repayment(id=5)])

        settles = _settles(proposal)
        assert len(settles) == 1
        assert settles[0]["event_id"] == 5
        assert settles[0]["linked_event_id"] == 0
        assert proposal.lifecycle_updates == [
            {"event_id": 0, "lifecycle_state": "partially_settled", "outstanding_paise": 60_000}
        ]

    def test_repayment_without_id_is_not_a_settlement_candidate(self):
        """No id on the repayment → 0, and the "advance must be earlier"
        guard (`advance_id < payment_id`) then rejects every real advance,
        because 0 is not greater than any real id. So the default must stay
        the falsy integer 0 rather than a sentinel that would reorder them."""
        proposal = walk_lineage([_advance(), _without(_repayment(), "id")])
        assert _settles(proposal) == []
        assert proposal.lifecycle_updates == []


# ── date_iso default: "" → sorts first, compares as the earliest date ───────


class TestDateIsoDefault:
    def test_advance_without_date_still_matches(self):
        """No date_iso on the advance → `""`, and the temporal guard is
        `advance_date <= payment_date`, which `""` satisfies. The default must
        stay the empty string; any non-empty sentinel would be compared
        literally and could exclude the advance."""
        proposal = walk_lineage([_without(_advance(), "date_iso"), _repayment()])
        assert len(_settles(proposal)) == 1

    def test_dated_advance_is_preferred_over_an_undated_one(self):
        """`open_advances.sort(key=date_iso, reverse=True)` compares the RAW
        values, and `""` sorts below every real ISO date, so an undated
        advance is a valid candidate but never the one that gets linked.

        This is precisely why the default must stay the empty string: any
        non-empty sentinel would be compared as a literal date and would
        out-rank a genuine advance date, silently settling the wrong advance.
        The payment id is 5 so that BOTH advances clear the "advance must be
        earlier" guard, so the result is decided by the ordering and not by
        the id filter.
        """
        undated = _without(_advance(id=1), "date_iso")
        dated = _advance(id=3, date_iso="2025-01-04")
        proposal = walk_lineage([undated, dated, _repayment(id=5)])

        settles = _settles(proposal)
        assert len(settles) == 1
        assert settles[0]["linked_event_id"] == 3

    def test_the_undated_advance_still_settles_when_it_is_the_only_candidate(self):
        """Control: the undated advance is not excluded, it is merely
        out-ranked. Without this, the previous test would also pass if the
        default made undated advances disappear entirely."""
        proposal = walk_lineage([_without(_advance(), "date_iso"), _repayment()])
        assert len(_settles(proposal)) == 1

    def test_repayment_without_date_does_not_outrank_a_later_advance(self):
        """No date_iso on the repayment → `""`, and a real advance date is NOT
        <= `""`, so the advance is excluded."""
        proposal = walk_lineage(
            [_advance(date_iso="2025-06-01"), _without(_repayment(), "date_iso")]
        )
        assert _settles(proposal) == []


# ── event_type default: "" → the event is inert ────────────────────────────


class TestEventTypeDefault:
    def test_advance_without_type_is_not_a_liability(self):
        """No event_type → `""`, which is in no predicate's vocabulary, so the
        event is neither a candidate advance nor a repayment."""
        proposal = walk_lineage([_without(_advance(), "event_type"), _repayment()])
        assert _settles(proposal) == []

    def test_repayment_without_type_is_not_a_repayment(self):
        proposal = walk_lineage([_advance(), _without(_repayment(), "event_type")])
        assert _settles(proposal) == []

    def test_typeless_transfer_leg_is_excluded_while_the_typed_one_is_revoked(self):
        """A leg with no event_type is not in the transfer vocabulary, so it is
        never grouped. The typed leg of the SAME transfer is still revoked, so
        this isolates the `event_type` default rather than the whole
        revocation path."""
        typeless = _without(_transfer(1, "out"), "event_type")
        proposal = detect_revocations([typeless, _transfer(2, "in"), _revocation()])

        assert proposal.superseded_events == [2]
        assert [x["linked_event_id"] for x in proposal.proposed_links] == [2]

    def test_transfer_with_no_legs_at_all_is_never_revoked(self):
        """Both legs typeless → nothing is grouped, so the revocation has no
        target and must produce nothing."""
        proposal = detect_revocations(
            [
                _without(_transfer(1, "out"), "event_type"),
                _without(_transfer(2, "in"), "event_type"),
                _revocation(),
            ]
        )
        assert proposal.proposed_links == []
        assert proposal.superseded_events == []

    def test_typeless_revocation_is_ignored(self):
        revocation = _revocation()
        revocation.pop("event_type")
        proposal = detect_revocations(
            [_transfer(1, "out"), _transfer(2, "in"), revocation]
        )
        assert proposal.proposed_links == []


# ── transfer_id default: "" → the leg is not grouped ───────────────────────


def _transfer(event_id: int, side: str, **overrides):
    event = {
        "id": event_id,
        "account_id": f"acc_{side}",
        "event_type": f"fund_transfer_{side}",
        "date_iso": "2025-01-01",
        "lifecycle_state": "open",
        "amount_paise": 5_000,
        "transfer_id": "trx_9",
    }
    event.update(overrides)
    return event


def _revocation(**overrides):
    event = {
        "id": 90,
        "account_id": "acc_savings",
        "event_type": "transfer_revocation",
        "date_iso": "2025-01-03",
        # A revocation is itself an event: without this state it is skipped by
        # the `lifecycle_state != "open"` guard and nothing is ever revoked.
        "lifecycle_state": "open",
        "transfer_id": "trx_9",
        "revocation_reason": "requested_by_user",
    }
    event.update(overrides)
    return event


class TestTransferIdDefault:
    def test_matched_transfer_is_revoked_on_both_legs(self):
        """Control: with a transfer_id on both legs and the revocation, the
        proposal supersedes both legs. Every default case below is only
        meaningful next to this one."""
        proposal = detect_revocations(
            [_transfer(1, "out"), _transfer(2, "in"), _revocation()]
        )
        assert sorted(proposal.superseded_events) == [1, 2]
        assert {u["lifecycle_state"] for u in proposal.lifecycle_updates} == {"revoked"}
        assert sorted(x["linked_event_id"] for x in proposal.proposed_links) == [1, 2]

    def test_leg_without_transfer_id_is_never_revoked(self):
        """No transfer_id → `""` is falsy, so the leg is not grouped and the
        revocation can never reach it. The default must stay falsy."""
        proposal = detect_revocations(
            [
                _without(_transfer(1, "out"), "transfer_id"),
                _transfer(2, "in"),
                _revocation(),
            ]
        )
        assert 1 not in proposal.superseded_events
        assert 1 not in [x["linked_event_id"] for x in proposal.proposed_links]

    def test_revocation_without_transfer_id_revokes_nothing(self):
        proposal = detect_revocations(
            [
                _transfer(1, "out"),
                _transfer(2, "in"),
                _without(_revocation(), "transfer_id"),
            ]
        )
        assert proposal.proposed_links == []
        assert proposal.superseded_events == []

    def test_unknown_transfer_id_revokes_nothing(self):
        """`events_by_transfer.get(transfer_id, [])` — the default must be an
        empty collection, not a truthy one that would revoke a phantom."""
        proposal = detect_revocations(
            [
                _transfer(1, "out"),
                _transfer(2, "in"),
                _revocation(transfer_id="trx_absent"),
            ]
        )
        assert proposal.proposed_links == []
        assert proposal.superseded_events == []


# ── rollover detection: the same default contract ──────────────────────────


def _rollover_pair():
    """Two open advances whose dates are 10 days apart → one rolls over."""
    source = _advance(id=1, date_iso="2025-01-01")
    target = _advance(id=2, date_iso="2025-01-11")
    return source, target


class TestRolloverSparseEvents:
    def test_intact_advances_roll_over(self):
        """Control: two dated open advances 10 days apart produce the link."""
        proposal = detect_rollover_scenarios(list(_rollover_pair()))
        assert [x for x in proposal.proposed_links if x["link_type"] == "rolls_over"]

    def test_advance_without_id_is_a_rollover_source_recorded_as_zero(self):
        """No id on the source → 0. The source filter compares
        `e.get("id") != event_id`, so 0 still differs from the target id and the
        source is admitted; the `0` is then surfaced verbatim in the link, which
        makes the id default directly observable on the rollover path."""
        source, target = _rollover_pair()
        source = _without(source, "id")
        proposal = detect_rollover_scenarios([source, target])

        rollovers = [x for x in proposal.proposed_links if x["link_type"] == "rolls_over"]
        assert rollovers == [{"event_id": 2, "linked_event_id": 0, "link_type": "rolls_over"}]

    def test_advance_without_liability_change_is_not_a_source(self):
        """The source filter requires a positive `liability_change_paise`. A
        missing amount defaults to 0, which is not > 0, so the pair must not
        roll over."""
        source, target = _rollover_pair()
        source = _without(source, "liability_change_paise")
        proposal = detect_rollover_scenarios([source, target])
        assert [x for x in proposal.proposed_links if x["link_type"] == "rolls_over"] == []

    def test_advance_without_date_is_neither_source_nor_target(self):
        """No date_iso → `_parse_date_iso("")` returns None, so the advance is
        skipped entirely. The default must stay the empty string."""
        source, target = _rollover_pair()
        target = _without(target, "date_iso")
        proposal = detect_rollover_scenarios([source, target])
        assert [x for x in proposal.proposed_links if x["link_type"] == "rolls_over"] == []

    def test_advance_without_type_is_not_a_rollover_candidate(self):
        source, target = _rollover_pair()
        target = _without(target, "event_type")
        proposal = detect_rollover_scenarios([source, target])
        assert [x for x in proposal.proposed_links if x["link_type"] == "rolls_over"] == []


# ── sparse payloads must not crash ─────────────────────────────────────────


class TestSparsePayloadTolerance:
    def test_completely_empty_event_is_inert(self):
        """An event with no fields at all must be ignored, not raise."""
        proposal = walk_lineage([{}])
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []
        assert proposal.superseded_events == []

    def test_empty_event_list_returns_an_empty_proposal(self):
        proposal = walk_lineage([])
        assert proposal.proposed_links == []
        assert proposal.lifecycle_updates == []
        assert proposal.superseded_events == []

    def test_detection_helpers_tolerate_empty_payloads(self):
        empty = detect_revocations([{}])
        assert empty.proposed_links == []
        assert empty.superseded_events == []

    def test_completely_empty_event_does_not_block_the_rest(self):
        """An unusable event in the batch must not prevent the usable ones from
        producing lineage."""
        proposal = walk_lineage([{}, _advance(), _repayment()])
        assert len(_settles(proposal)) == 1
