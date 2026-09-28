# backend/tests/properties/transaction_intelligence/test_cc_payment_contract.py
#
# M9-C71 — Contract tests for the credit-card payment LIFECYCLE contract.
#
# WHY THIS FILE EXISTS
# --------------------
# `classify_cc_payment` converts one number — what the customer paid — into a
# credit-card lifecycle state. That state drives revolving-balance reporting and
# delinquency, so its boundaries are contractual:
#
#     no statement row matched                 ->  unknown        / unmatched
#     payment >= total_due - 100 paise         ->  fully_paid     (rounding tol)
#     payment >= minimum_due                   ->  revolving
#     payment <  minimum_due                   ->  payment_received
#
# The existing property test in test_detector_properties.py asserts
# relationships between `payment`, `due`, `min_due` and `remaining_outstanding`,
# but never asserts WHICH state a given payment produces, nor the confidence or
# match_reason that accompanies it. A classifier that returned `revolving` for
# every partial payment, or `fully_paid` for every payment, would satisfy those
# relationships in many cases while being wrong at exactly the boundaries that
# matter.
#
# These tests pin the boundaries. They are written against the published
# behaviour, not against any mutant, and none of them touches a private helper.

from __future__ import annotations

import pytest
from src.engines.transaction_intelligence.cc_payment_detector import (
    classify_cc_payment,
)

# A ₹5,000 statement with a ₹1,000 minimum due, expressed in paise.
STATEMENT = {
    "id": 7,
    "total_amount_due": 500_000,
    "minimum_amount_due": 100_000,
}


def _txn(amount_paise: int) -> dict:
    return {
        "id": 1,
        "account_id": "ACC-1",
        "amount_paise": amount_paise,
        "date_iso": "2025-03-05",
        "description": "CREDIT CARD PAYMENT",
    }


# ── the unmatched case ───────────────────────────────────────────────────────


class TestCCUnmatched:
    def test_no_statement_row_is_unmatched_and_low_confidence(self):
        """Without a statement there is no lifecycle to report, so confidence
        must be the lowest tier and no amounts may be invented."""
        result = classify_cc_payment(_txn(300_000), None)

        assert result.classification == "credit_card_payment_unmatched"
        assert result.lifecycle_state == "unknown"
        assert result.match_reason == "no_matching_statement_found"
        assert result.confidence_bps == 2000
        assert result.matched_statement_id is None

    def test_unmatched_reports_no_statement_amounts(self):
        """Statement-derived amounts must be zero, not copied from the payment."""
        result = classify_cc_payment(_txn(300_000), None)

        assert result.statement_amount_paise == 0
        assert result.minimum_due_paise == 0
        assert result.remaining_outstanding_paise == 0
        # The payment itself IS known, and must still be reported.
        assert result.payment_amount_paise == 300_000

    def test_missing_amount_key_is_treated_as_zero(self):
        """An absent amount is a payment of nothing, not of unknown size."""
        txn = _txn(0)
        del txn["amount_paise"]

        result = classify_cc_payment(txn, STATEMENT)

        assert result.payment_amount_paise == 0
        assert result.lifecycle_state == "payment_received"


# ── the lifecycle ladder, one test per state ─────────────────────────────────


class TestCCLifecycleStates:
    def test_exact_full_payment_is_fully_paid(self):
        result = classify_cc_payment(_txn(500_000), STATEMENT)

        assert result.classification == "credit_card_payment"
        assert result.lifecycle_state == "fully_paid"
        assert result.match_reason == "full_payment_matched"
        assert result.confidence_bps == 9500
        assert result.remaining_outstanding_paise == 0

    def test_overpayment_is_fully_paid_with_no_negative_balance(self):
        """Paying more than the statement clears it; the balance cannot go
        negative, because a negative outstanding is not a real state and would
        propagate into net-worth reporting."""
        result = classify_cc_payment(_txn(600_000), STATEMENT)

        assert result.lifecycle_state == "fully_paid"
        assert result.remaining_outstanding_paise == 0
        assert result.remaining_outstanding_paise >= 0

    def test_full_payment_tolerates_a_small_rounding_shortfall(self):
        """A 100-paise shortfall is bank rounding, not a partial payment.

        The tolerance is one rupee; a payment short by more than that is a
        genuinely partial payment and must be `revolving`.
        """
        result = classify_cc_payment(_txn(499_950), STATEMENT)

        assert result.lifecycle_state == "fully_paid"
        assert result.remaining_outstanding_paise == 0

    def test_payment_just_beyond_the_tolerance_is_revolving(self):
        result = classify_cc_payment(_txn(499_800), STATEMENT)

        assert result.lifecycle_state == "revolving"
        assert result.remaining_outstanding_paise == 200

    def test_payment_equal_to_minimum_due_is_revolving(self):
        """Meeting the minimum exactly is a valid partial payment, not a
        below-minimum one."""
        result = classify_cc_payment(_txn(100_000), STATEMENT)

        assert result.lifecycle_state == "revolving"
        assert result.match_reason == "partial_payment_above_minimum"
        assert result.confidence_bps == 8500

    def test_payment_below_minimum_is_payment_received(self):
        """A payment too small to be a valid card payment still happened, and
        the contract says so with the lowest of the three matched states."""
        result = classify_cc_payment(_txn(50_000), STATEMENT)

        assert result.lifecycle_state == "payment_received"
        assert result.match_reason == "payment_below_minimum_due"
        assert result.confidence_bps == 7000

    def test_every_matched_state_reports_the_matched_statement(self):
        """The caller needs the statement id to reconcile against, in all three
        matched states."""
        for amount, expected in (
            (500_000, "fully_paid"),
            (100_000, "revolving"),
            (50_000, "payment_received"),
        ):
            result = classify_cc_payment(_txn(amount), STATEMENT)
            assert result.matched_statement_id == 7
            assert result.lifecycle_state == expected

    def test_partial_states_report_the_remaining_balance(self):
        """Only a cleared statement has no remaining balance; every partial
        payment must quantify what is still owed."""
        for amount in (100_000, 50_000, 200_000):
            result = classify_cc_payment(_txn(amount), STATEMENT)
            assert result.remaining_outstanding_paise == 500_000 - amount


# ── the ordering invariant the whole classifier rests on ─────────────────────


class TestCCStateOrdering:
    def test_lifecycle_is_monotonic_in_payment_amount(self):
        """Paying more must never yield a worse lifecycle state.

        This is the invariant that makes the classifier safe to use without
        re-deriving the boundaries, and it fails loudly if a comparison is
        inverted or a branch is reordered.
        """
        order = {
            "payment_received": 0,
            "revolving": 1,
            "fully_paid": 2,
        }
        previous = -1
        for amount in (0, 50_000, 99_999, 100_000, 250_000, 499_899, 499_950, 500_000):
            result = classify_cc_payment(_txn(amount), STATEMENT)
            rank = order[result.lifecycle_state]
            assert rank >= previous, (
                f"paying {amount} paise produced a worse state "
                f"({result.lifecycle_state}) than a smaller payment"
            )
            previous = rank

    def test_confidence_is_monotonic_in_state_strength(self):
        """Stronger evidence must never report lower confidence."""
        expected = {"payment_received": 7000, "revolving": 8500, "fully_paid": 9500}
        for amount in (50_000, 100_000, 500_000):
            result = classify_cc_payment(_txn(amount), STATEMENT)
            assert result.confidence_bps == expected[result.lifecycle_state]

    def test_unmatched_is_the_weakest_state(self):
        """No statement is weaker evidence than a poor partial payment."""
        unmatched = classify_cc_payment(_txn(1), None)
        weakest_match = classify_cc_payment(_txn(1), STATEMENT)

        assert unmatched.confidence_bps < weakest_match.confidence_bps
        assert unmatched.lifecycle_state == "unknown"
        assert weakest_match.lifecycle_state == "payment_received"


# ── amount handling ──────────────────────────────────────────────────────────


class TestCCAmountConversion:
    @pytest.mark.parametrize(
        ("total_due", "expected_paise", "why"),
        [
            (500_000, 500_000, "an int is already paise"),
            (5_000.0, 500_000, "a float is rupees, so it is scaled"),
            ("5000.00", 500_000, "a decimal string is rupees, so it is scaled"),
            ("5000", 5_000, "a plain integer string is already paise"),
            ("5,000.00", 500_000, "thousands separators are stripped before scaling"),
        ],
    )
    def test_statement_amounts_are_normalised_to_paise(
        self, total_due, expected_paise, why
    ):
        """A statement amount arrives in one of four shapes, and every money
        comparison in this classifier is in paise.

        The string cases are the sharp edge: a string's UNIT is inferred from
        whether it contains a decimal point, so "5000" is five thousand paise
        (₹50) while "5000.00" is five thousand rupees (₹5,000). Both are
        plausible statement text, and getting the unit wrong shifts every
        lifecycle boundary by 100x — so the heuristic is pinned here rather
        than left to be rediscovered.
        """
        statement = dict(STATEMENT, total_amount_due=total_due)
        payment = expected_paise

        result = classify_cc_payment(_txn(payment), statement)

        assert result.statement_amount_paise == expected_paise, why
        # Paying exactly the normalised amount must clear the statement.
        assert result.lifecycle_state == "fully_paid", why

    def test_a_string_amount_in_paise_is_not_rescaled(self):
        """The sharpest edge, stated directly: "5000" is 5,000 paise.

        If this were treated as rupees, a ₹50 payment would clear a ₹5,000
        statement and every downstream balance would be wrong by 100x.
        """
        statement = dict(STATEMENT, total_amount_due="5000")

        result = classify_cc_payment(_txn(5_000), statement)

        assert result.statement_amount_paise == 5_000
        assert result.lifecycle_state == "fully_paid"

    def test_unparseable_amounts_are_treated_as_zero(self):
        """A corrupt statement must not crash the classifier, and must not be
        silently turned into a real balance either."""
        statement = dict(STATEMENT, total_amount_due="not-a-number")

        result = classify_cc_payment(_txn(1_000), statement)

        assert result.statement_amount_paise == 0
        assert result.lifecycle_state == "fully_paid"

    def test_missing_statement_amounts_are_treated_as_zero(self):
        """An absent total is a zero balance, so any payment clears it."""
        result = classify_cc_payment(_txn(1_000), {"id": 7})

        assert result.statement_amount_paise == 0
        assert result.minimum_due_paise == 0
        assert result.lifecycle_state == "fully_paid"
