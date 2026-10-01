# backend/tests/unit/engines/financial_intelligence/test_projection_contract.py
#
# M9-C71 — Contract tests for the debt-payoff PROJECTION contract.
#
# WHY THIS FILE EXISTS
# --------------------
# `calculate_debt_payoff_projection` returns four keys that a user reads as a
# financial promise:
#
#     estimated_months           "you'll be debt-free in N months"
#     interest_saved_paise       "you'll save ₹X in interest"
#     payoff_order               which debt to attack, and in what order
#     monthly_allocation_paise   how much of your surplus is committed
#
# The projection is used to justify an allocation decision, so a wrong or missing
# key does not fail loudly — it silently tells someone to commit money on the
# strength of a number that is zero, absent, or built from the wrong debts.
#
# The pre-existing tests exercise the arithmetic but never assert the OUTPUT
# SHAPE or the payoff ORDER across loans and cards together, so a renamed key
# (`interest_saved_paise` -> `XXinterest_saved_paiseXX`) or an inverted sort
# would survive untouched. That is what mutation testing surfaced here.
#
# These tests assert the published contract: the four keys are present, the
# numbers are internally consistent, and the order follows the documented
# debt-avalanche rule.

from __future__ import annotations

from decimal import Decimal

from src.engines.financial_intelligence.goal_planner import (
    calculate_debt_payoff_projection,
)

#: The four keys the projection promises its caller.
PROJECTION_KEYS = {
    "estimated_months",
    "interest_saved_paise",
    "payoff_order",
    "monthly_allocation_paise",
}

LOAN_HIGH_RATE = {
    "id": "L1",
    "name": "Credit Card Loan",
    "outstanding_paise": 500_000,
    "interest_rate_bps": 1800,
    "emi_paise": 20_000,
}
LOAN_LOW_RATE = {
    "id": "L2",
    "name": "Home Loan",
    "outstanding_paise": 8_000_000,
    "interest_rate_bps": 700,
    "emi_paise": 60_000,
}
CARD = {
    "id": "C1",
    "name": "Visa",
    "outstanding_paise": 120_000,
    "interest_rate_bps": 2400,
    "minimum_due_paise": 5_000,
}


def _assert_shape(projection: dict) -> None:
    """The promised keys must exist, with usable types, whatever the input."""
    assert (
        set(projection) >= PROJECTION_KEYS
    ), f"projection is missing {PROJECTION_KEYS - set(projection)}"
    assert isinstance(projection["estimated_months"], int)
    assert isinstance(projection["interest_saved_paise"], (int, float))
    assert isinstance(projection["payoff_order"], list)
    assert isinstance(projection["monthly_allocation_paise"], int)
    for item in projection["payoff_order"]:
        assert {"id", "type", "outstanding_paise", "interest_rate_bps"} <= set(item)


# ── the output shape, on every path ──────────────────────────────────────────


class TestProjectionShape:
    def test_nothing_to_pay_off_returns_a_complete_zero_projection(self):
        """The empty case must still return all four keys.

        A caller that reads `projection["interest_saved_paise"]` without a
        default would raise KeyError here if the empty branch omitted it.
        """
        projection = calculate_debt_payoff_projection([], [], 0)

        _assert_shape(projection)
        assert projection["estimated_months"] == 0
        assert projection["interest_saved_paise"] == 0
        assert projection["payoff_order"] == []
        assert projection["monthly_allocation_paise"] == 0

    def test_settled_debts_are_not_projected_as_owed(self):
        """Debts already at zero must not inflate the timeline or the savings."""
        projection = calculate_debt_payoff_projection(
            [{**LOAN_HIGH_RATE, "outstanding_paise": 0}], [], 50_000
        )

        _assert_shape(projection)
        assert projection["payoff_order"] == []

    def test_a_projection_with_debt_is_complete(self):
        projection = calculate_debt_payoff_projection(
            [LOAN_HIGH_RATE, LOAN_LOW_RATE], [CARD], 50_000
        )

        _assert_shape(projection)
        assert len(projection["payoff_order"]) == 3

    def test_savings_are_never_negative(self):
        """Paying debt off sooner cannot save NEGATIVE interest."""
        projection = calculate_debt_payoff_projection(
            [LOAN_HIGH_RATE, LOAN_LOW_RATE], [CARD], 50_000
        )

        assert projection["interest_saved_paise"] >= 0

    def test_months_are_never_negative(self):
        projection = calculate_debt_payoff_projection([LOAN_HIGH_RATE], [CARD], 50_000)

        assert projection["estimated_months"] >= 0


# ── the debt-avalanche ordering rule ─────────────────────────────────────────


class TestProjectionOrdering:
    def test_highest_interest_rate_is_paid_first(self):
        """The documented strategy is avalanche: the most expensive debt first.

        Getting this backwards sends someone to repay 7% debt while 24% credit
        card debt accrues, which is the single most expensive mistake this
        projection can make.
        """
        projection = calculate_debt_payoff_projection([LOAN_LOW_RATE], [CARD], 50_000)

        order = [item["id"] for item in projection["payoff_order"]]
        assert order[0] == "C1", "highest-rate debt was not paid first"

    def test_order_is_sorted_by_rate_descending(self):
        projection = calculate_debt_payoff_projection(
            [LOAN_HIGH_RATE, LOAN_LOW_RATE], [CARD], 50_000
        )

        rates = [item["interest_rate_bps"] for item in projection["payoff_order"]]
        assert rates == sorted(rates, reverse=True)

    def test_loans_and_cards_are_projected_together(self):
        """A credit card is debt too, and the avalanche order must span both.

        Treating cards and loans as separate sequences would let a user pay off
        a 7% home loan before a 24% card.
        """
        projection = calculate_debt_payoff_projection(
            [LOAN_LOW_RATE, LOAN_HIGH_RATE], [CARD], 50_000
        )

        types = {item["type"] for item in projection["payoff_order"]}
        assert types == {"loan", "credit_card"}
        assert len(projection["payoff_order"]) == 3

    def test_ordering_is_stable_for_equal_rates(self):
        """Two debts at the same rate must both appear, neither dropped."""
        a = {**LOAN_HIGH_RATE, "id": "A"}
        b = {**LOAN_HIGH_RATE, "id": "B"}

        projection = calculate_debt_payoff_projection([a, b], [], 50_000)

        assert {item["id"] for item in projection["payoff_order"]} == {"A", "B"}

    def test_every_included_debt_appears_exactly_once(self):
        """A debt must not be projected twice or dropped — both misstate the
        total the user is being asked to commit to."""
        projection = calculate_debt_payoff_projection(
            [LOAN_HIGH_RATE, LOAN_LOW_RATE, {**LOAN_LOW_RATE, "id": "L3"}],
            [CARD],
            50_000,
        )

        ids = [item["id"] for item in projection["payoff_order"]]
        assert sorted(ids) == ["C1", "L1", "L2", "L3"]
        assert len(ids) == len(set(ids))


# ── the allocation arithmetic ────────────────────────────────────────────────


class TestProjectionAllocation:
    def test_allocation_is_the_surplus_times_the_ratio(self):
        """The committed amount is documented as surplus x allocation ratio."""
        projection = calculate_debt_payoff_projection(
            [LOAN_HIGH_RATE], [], 100_000, allocation_ratio=Decimal("0.5")
        )

        assert projection["monthly_allocation_paise"] == 50_000

    def test_a_smaller_surplus_shortens_the_timeline(self):
        """The headline month count must respond to the input that drives it."""
        slow = calculate_debt_payoff_projection([LOAN_HIGH_RATE], [], 20_000)
        fast = calculate_debt_payoff_projection([LOAN_HIGH_RATE], [], 200_000)

        assert fast["estimated_months"] < slow["estimated_months"]

    def test_a_larger_balance_lengthens_the_timeline(self):
        small = calculate_debt_payoff_projection([LOAN_HIGH_RATE], [], 50_000)
        large = calculate_debt_payoff_projection(
            [{**LOAN_HIGH_RATE, "outstanding_paise": 5_000_000}], [], 50_000
        )

        assert large["estimated_months"] > small["estimated_months"]

    def test_zero_surplus_allocates_nothing(self):
        """With nothing spare, nothing may be committed to debt payoff."""
        projection = calculate_debt_payoff_projection(
            [LOAN_HIGH_RATE], [], 0, allocation_ratio=Decimal("1.0")
        )

        assert projection["monthly_allocation_paise"] == 0

    def test_savings_grow_with_the_debt_pool(self):
        """Interest avoided is a function of what is owed, so more debt means
        more interest avoided."""
        small = calculate_debt_payoff_projection([LOAN_LOW_RATE], [], 50_000)
        large = calculate_debt_payoff_projection(
            [{**LOAN_LOW_RATE, "outstanding_paise": 80_000_000}], [], 50_000
        )

        assert large["interest_saved_paise"] > small["interest_saved_paise"]

    def test_paise_values_are_not_reported_as_rupees(self):
        """Balances are paise throughout; a projection that mixes units tells a
        user they owe 100x what they do."""
        projection = calculate_debt_payoff_projection([LOAN_HIGH_RATE], [], 50_000)

        for item in projection["payoff_order"]:
            assert item["outstanding_paise"] == 500_000
        assert projection["interest_saved_paise"] > 0
