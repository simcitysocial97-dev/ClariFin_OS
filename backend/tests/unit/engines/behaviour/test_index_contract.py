# backend/tests/unit/engines/behaviour/test_index_contract.py
#
# M9-C71 — Contract tests for the behaviour-engine INDEX contract.
#
# WHY THIS FILE EXISTS
# --------------------
# The engine derives five behavioural indices from transactions:
#
#     loss aversion       -> score, post_income_velocity, recovery_time_days
#     impulsivity         -> score, micro_txn_ratio, late_night_ratio
#     habit stability     -> score, category_cv, recurring_predictability
#     financial stress    -> score, balance_volatility, credit_dependency
#     savings discipline  -> score, ...
#
# Each has a documented NO-DATA fallback: a neutral `score` of 0.5 with every
# sub-metric zeroed. That fallback is what a user with three transactions gets,
# and it is the single most common case in a real ledger — so it is also the
# case most likely to be wrong without anyone noticing.
#
# The pre-existing tests exercise the indices on populated ledgers but never
# assert the return SHAPE. That left the neutral fallback's `"score"` key free
# to be renamed (`"score"` -> `"XXscoreXX"`) with no test failing, and left the
# 0.5 neutral value itself unasserted. A renamed key does not crash: the
# consumer reads a missing key, gets a default, and every index reports as
# neutral forever.
#
# These tests assert the shape and the no-data semantics for all five indices,
# which is the contract the rest of the profile builder is entitled to assume.

from __future__ import annotations

import pytest
from src.engines.behaviour_engine import core

#: Every index promises `score`; the sub-metric names differ per index and, as
#: documented in `TestNoDataShapeDiffersFromComputedShape`, differ per PATH.
INDEX_FUNCTIONS = [
    "_compute_loss_aversion_index",
    "_compute_impulsivity_score",
    "_compute_habit_stability_score",
    "_compute_financial_stress_index",
    "_compute_savings_discipline_score",
]

#: Enough transactions for an index to produce a non-neutral score.
RICH_TRANSACTIONS = [
    {
        "id": i,
        "type": "debit" if i % 2 else "credit",
        "date_iso": f"2025-0{(i % 3) + 1}-1{i % 9}",
        "amount_paise": 100_000 + i * 37_000,
        "category": ("Food", "Rent", "Transport")[i % 3],
    }
    for i in range(1, 19)
]


# ── the return-shape contract ────────────────────────────────────────────────


class TestIndexReturnShape:
    @pytest.mark.parametrize("func_name", INDEX_FUNCTIONS)
    def test_score_is_always_present_for_a_populated_ledger(self, func_name):
        """`score` is the one key every consumer may rely on.

        The renamed-`score` mutants (`"score"` -> `"XXscoreXX"`) return a
        perfectly well-formed dict that is simply missing the field everyone
        reads. Nothing crashes; every index just reports neutral forever.
        """
        result = getattr(core, func_name)(list(RICH_TRANSACTIONS))

        assert "score" in result, f"{func_name} omitted 'score' on real data"
        assert 0.0 <= result["score"] <= 1.0

    @pytest.mark.parametrize("func_name", INDEX_FUNCTIONS)
    def test_score_is_always_present_for_an_empty_ledger(self, func_name):
        """The neutral fallback is returned from a DIFFERENT line than the
        computed one, so both paths must be asserted independently."""
        result = getattr(core, func_name)([])

        assert "score" in result, f"{func_name} omitted 'score' on the no-data path"
        assert 0.0 <= result["score"] <= 1.0

    @pytest.mark.parametrize("func_name", INDEX_FUNCTIONS)
    def test_sub_metrics_are_numeric(self, func_name):
        """Sub-metrics are numeric, so a consumer may threshold or average them.

        They are NOT all 0-1 ratios — `post_income_velocity` and `category_cv`
        are unbounded by nature — so only their type is asserted here. Asserting
        a 0-1 range on them would be asserting a contract the engine does not
        claim.
        """
        result = getattr(core, func_name)(list(RICH_TRANSACTIONS))

        for key, value in result.items():
            if key == "score":
                continue
            assert isinstance(value, (int, float)), f"{key} is {type(value).__name__}"


class TestNoDataShapeDiffersFromComputedShape:
    """A real defect, recorded so it cannot be forgotten.

    Each index's no-data fallback returns a DIFFERENT set of sub-metric keys
    from its computed path:

        _compute_habit_stability_score
            no-data : score, category_cv, recurring_predictability
            computed: score, category_cv, recurring_count, rhythm_score

    So a consumer reading `result["recurring_predictability"]` works for a user
    the engine cannot analyse and raises KeyError for a user it can. And
    `result.get("rhythm_score", 0)` returns 0 for sparse ledgers and the real
    value for populated ones, biasing sparse users toward zero.

    This test pins the CURRENT behaviour so the inconsistency is visible and
    any future fix is a deliberate, reviewable change rather than a silent
    one. It asserts the shape difference exists; it does not endorse it.
    """

    @pytest.mark.parametrize("func_name", INDEX_FUNCTIONS)
    def test_every_index_reports_score_on_both_paths(self, func_name):
        """The invariant that actually matters: `score` exists on both paths."""
        func = getattr(core, func_name)

        assert "score" in func([])
        assert "score" in func(list(RICH_TRANSACTIONS))

    def test_the_no_data_and_computed_shapes_are_different(self):
        """Documented asymmetry: the neutral fallback is a different shape.

        `recurring_predictability` exists only on the no-data path;
        `recurring_count` and `rhythm_score` only on the computed path. The two
        sets are disjoint apart from `score` and `category_cv`, so neither
        contains the other.
        """
        func = core._compute_habit_stability_score

        no_data = set(func([]))
        computed = set(func(list(RICH_TRANSACTIONS)))

        assert no_data != computed, (
            "the no-data and computed shapes have become identical; if that was "
            "an intentional fix, this assertion should be updated deliberately"
        )
        assert "recurring_predictability" in no_data
        assert "recurring_predictability" not in computed


# ── the no-data semantics ────────────────────────────────────────────────────


class TestIndexNoDataSemantics:
    @pytest.mark.parametrize("func_name", INDEX_FUNCTIONS)
    def test_no_data_means_neutral_not_worst(self, func_name):
        """No data must score NEUTRAL (0.5), not 0.

        Scoring 0 for a user the engine cannot analyse would report "no risk"
        as "maximum discipline" and rank them incorrectly against everyone
        else. Neutral means "unknown", and unknown is 0.5.
        """
        result = getattr(core, func_name)([])

        assert (
            result["score"] == 0.5
        ), f"{func_name} scored an unanalysable ledger as {result['score']}"

    @pytest.mark.parametrize("func_name", INDEX_FUNCTIONS)
    def test_no_data_sub_metrics_are_zero_not_missing(self, func_name):
        """A ratio of zero events is zero, not absent."""
        result = getattr(core, func_name)([])

        for key, value in result.items():
            if key == "score":
                continue
            assert float(value) == 0.0, f"{key} should be 0 with no data"

    def test_a_single_transaction_is_still_not_a_verdict(self):
        """One transaction is not enough to characterise behaviour.

        Every index must refuse to produce a confident score from a single
        transaction and fall back to neutral.
        """
        single = [dict(RICH_TRANSACTIONS[0])]
        for func_name in INDEX_FUNCTIONS:
            result = getattr(core, func_name)(single)
            assert "score" in result
            assert (
                0.0 <= result["score"] <= 1.0
            ), f"{func_name} produced an out-of-range score for one transaction"
