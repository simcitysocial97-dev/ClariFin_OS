# backend/tests/unit/engines/financial_intelligence/test_ranking_output_contract.py
#
# M9-C71 — Contract tests for the debt-ranking OUTPUT contract, on every path.
#
# WHY THIS FILE EXISTS
# --------------------
# `rank_debt_payoff_strategy` returns the debt order a user is told to follow,
# and it has FOUR return points: an invalid-strategy fallback, an empty list,
# an all-settled list, and the ranked result. Each builds its own dict.
#
# The pre-existing tests assert `recommended_strategy` only on the ranked path,
# so the three early returns could rename that key — or drop it — without a
# single failure. A caller doing `result["recommended_strategy"]` on an
# empty-debt account then gets a KeyError, or silently reads a default and
# believes it was advised to use the wrong strategy.
#
# Each entry in `priority_order` carries `outstanding_paise` and
# `minimum_payment_paise`, which are what a plan UI renders next to each debt.
# Nothing asserted those keys, so they could be renamed without detection.
#
# These tests assert the output contract on EVERY return path, which is what
# makes the renamed-key mutants killable.

from __future__ import annotations

import pytest
from src.engines.financial_intelligence.optimization import (
    rank_debt_payoff_strategy,
)

VALID_STRATEGIES = {"avalanche", "snowball", "balanced"}

#: Every debt the ranking may be given.
DEBTS = [
    {
        "id": "high_rate",
        "type": "credit_card",
        "outstanding_paise": 150_000,
        "interest_rate_bps": 2400,
        "minimum_payment_paise": 5_000,
    },
    {
        "id": "low_rate",
        "type": "loan",
        "outstanding_paise": 4_000_000,
        "interest_rate_bps": 700,
        "minimum_payment_paise": 40_000,
    },
]

#: The keys every returned ranking entry must carry.
ENTRY_KEYS = {
    "id",
    "type",
    "outstanding_paise",
    "interest_rate_bps",
    "minimum_payment_paise",
}

#: Every input that produces a return from the function.
ALL_INPUTS = [
    ("normal", DEBTS, "avalanche"),
    ("empty_list", [], "avalanche"),
    ("all_settled", [{"id": "x", "outstanding_paise": 0}], "avalanche"),
    ("invalid_strategy", DEBTS, "not-a-strategy"),
    ("empty_and_invalid", [], "nonsense"),
]


def _assert_top_level(result: dict) -> None:
    """The top-level contract, on every path.

    A caller reads these three keys before deciding what to render, so all
    three must exist whatever the input.
    """
    assert {
        "recommended_strategy",
        "priority_order",
        "estimated_benefit",
    } <= set(result), f"missing top-level keys: {set(result)}"
    assert result["recommended_strategy"] in VALID_STRATEGIES, (
        f"recommended_strategy {result['recommended_strategy']!r} is not a "
        "recognised strategy, so a caller cannot label the advice"
    )
    assert isinstance(result["priority_order"], list)
    assert isinstance(result["estimated_benefit"], dict)
    assert "requires_projection" in result["estimated_benefit"]


def _assert_entries(result: dict) -> None:
    for entry in result["priority_order"]:
        assert set(entry) >= ENTRY_KEYS, (
            f"ranking entry is missing {ENTRY_KEYS - set(entry)}; a plan UI "
            "renders these next to each debt"
        )
        assert isinstance(entry["outstanding_paise"], int)
        assert isinstance(entry["minimum_payment_paise"], int)


# ── the top-level contract, on every return path ─────────────────────────────


class TestRankingTopLevelShape:
    @pytest.mark.parametrize(("label", "debts", "strategy"), ALL_INPUTS)
    def test_every_path_returns_the_promised_keys(self, label, debts, strategy):
        result = rank_debt_payoff_strategy(debts, strategy=strategy)

        _assert_top_level(result)
        _assert_entries(result)

    @pytest.mark.parametrize(("label", "debts", "strategy"), ALL_INPUTS)
    def test_every_path_reports_a_valid_strategy(self, label, debts, strategy):
        """An unrecognised strategy falls back to avalanche, and the RESPONSE
        says so — otherwise the caller labels wrong advice as correct."""
        result = rank_debt_payoff_strategy(debts, strategy=strategy)

        assert result["recommended_strategy"] in VALID_STRATEGIES

    def test_the_empty_path_still_names_its_strategy(self):
        """The specific gap: an empty debt list previously returned no
        `recommended_strategy` assertion, so the key could be renamed here."""
        result = rank_debt_payoff_strategy([])

        assert result["recommended_strategy"] == "avalanche"
        assert result["priority_order"] == []
        assert result["estimated_benefit"]["requires_projection"] is False

    def test_the_all_settled_path_still_names_its_strategy(self):
        """Same gap on the all-settled path, a different `return` statement."""
        result = rank_debt_payoff_strategy([{"id": "x", "outstanding_paise": 0}])

        assert result["recommended_strategy"] == "avalanche"
        assert result["priority_order"] == []
        assert result["estimated_benefit"]["requires_projection"] is False

    def test_a_snowball_request_is_honoured_on_the_empty_path(self):
        """The fallback replaces an INVALID strategy, not a valid one."""
        result = rank_debt_payoff_strategy([], strategy="snowball")

        assert result["recommended_strategy"] == "snowball"

    def test_an_invalid_strategy_falls_back_to_avalanche(self):
        result = rank_debt_payoff_strategy(DEBTS, strategy="martingale")

        assert result["recommended_strategy"] == "avalanche"


# ── the entry contract ───────────────────────────────────────────────────────


class TestRankingEntryContract:
    @pytest.mark.parametrize("strategy", sorted(VALID_STRATEGIES))
    def test_every_strategy_produces_complete_entries(self, strategy):
        result = rank_debt_payoff_strategy(DEBTS, strategy=strategy)

        assert result["priority_order"], f"{strategy} produced no ordering"
        _assert_entries(result)

    def test_entries_carry_the_balance_the_user_owes(self):
        """`outstanding_paise` is the number shown beside each debt."""
        result = rank_debt_payoff_strategy(DEBTS)

        by_id = {e["id"]: e for e in result["priority_order"]}
        assert by_id["high_rate"]["outstanding_paise"] == 150_000
        assert by_id["low_rate"]["outstanding_paise"] == 4_000_000

    def test_entries_carry_the_minimum_payment(self):
        """The minimum payment is what the plan tells them to send."""
        result = rank_debt_payoff_strategy(DEBTS)

        by_id = {e["id"]: e for e in result["priority_order"]}
        assert by_id["high_rate"]["minimum_payment_paise"] == 5_000
        assert by_id["low_rate"]["minimum_payment_paise"] == 40_000

    def test_entries_carry_the_interest_rate_that_justified_the_order(self):
        result = rank_debt_payoff_strategy(DEBTS)

        by_id = {e["id"]: e for e in result["priority_order"]}
        assert by_id["high_rate"]["interest_rate_bps"] == 2400
        assert by_id["low_rate"]["interest_rate_bps"] == 700

    def test_an_unknown_debt_type_is_labelled_rather_than_dropped(self):
        """A debt of an unrecognised type must still appear, typed unknown."""
        result = rank_debt_payoff_strategy(
            [{"id": "mystery", "outstanding_paise": 100_000}]
        )

        assert len(result["priority_order"]) == 1
        assert result["priority_order"][0]["type"] == "unknown"

    def test_every_active_debt_appears_exactly_once(self):
        """Neither dropping nor double-counting a debt: both misstate what the
        user is being asked to repay."""
        result = rank_debt_payoff_strategy(DEBTS)

        ids = [e["id"] for e in result["priority_order"]]
        assert sorted(ids) == sorted(d["id"] for d in DEBTS)
        assert len(ids) == len(set(ids))

    def test_settled_debts_never_appear(self):
        result = rank_debt_payoff_strategy(
            DEBTS + [{"id": "paid", "outstanding_paise": 0}]
        )

        assert "paid" not in [e["id"] for e in result["priority_order"]]

    def test_avalanche_puts_the_most_expensive_debt_first(self):
        result = rank_debt_payoff_strategy(DEBTS, strategy="avalanche")

        assert result["priority_order"][0]["id"] == "high_rate"

    def test_snowball_puts_the_smallest_balance_first(self):
        result = rank_debt_payoff_strategy(DEBTS, strategy="snowball")

        assert result["priority_order"][0]["id"] == "high_rate"

    def test_both_strategies_include_every_debt(self):
        """Whatever the strategy, the SET of debts is the same; only the order
        differs. A strategy that silently dropped a debt would look like advice."""
        sets = []
        for strategy in sorted(VALID_STRATEGIES):
            result = rank_debt_payoff_strategy(DEBTS, strategy=strategy)
            sets.append({e["id"] for e in result["priority_order"]})

        assert sets[0] == sets[1] == sets[2] == {"high_rate", "low_rate"}
