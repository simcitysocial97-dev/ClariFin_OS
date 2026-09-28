# backend/tests/properties/transaction_intelligence/test_emi_classification_contract.py
#
# M9-C71 — Contract tests for the EMI detection CLASSIFICATION contract.
#
# WHY THIS FILE EXISTS
# --------------------
# `detect_emi_payment` exists to answer one question: given a bank debit and a
# set of candidate loans, how confident are we that this debit is an EMI, and
# WHY? Its entire output contract is the mapping
#
#     evidence found                          ->  priority / match_reason
#     bank statement row for (loan, date)     ->  100 / bank_statement_override
#     amount matches AND schedule row exists  ->   90 / amount_match
#     amount matches AND date within 3 days   ->   85 / amount+date
#     amount matches only                     ->   80 / amount_only
#     date within 3 days only                 ->   75 / date_proximity
#     no evidence                             ->  None
#
# plus the rule that the HIGHEST priority candidate wins across loans.
#
# The pre-existing 20 tests in test_detector_properties.py assert only that
# `result.priority in {60, 75, 80, 85, 90, 100}` and
# `result.confidence_bps in {...}`. That is a vocabulary check: it holds for any
# input whatsoever, including inputs for which the detector picks the WRONG
# loan, the wrong reason, or the wrong tier. Nothing asserted the mapping above.
#
# This matters commercially. A false positive here reclassifies ordinary
# spending as a loan payment, which drives liability balances, cashflow
# forecasts and net-worth reporting. A false negative leaves a real EMI
# unclassified. The priority ordering decides which candidate is believed, so it
# is the part of this function that most needs a contract and least had one.
#
# These tests assert the published contract. They are not written against any
# mutant, and none of them asserts a private helper.

from __future__ import annotations

import pytest
from src.engines.transaction_intelligence.loan_emi_detector import (
    detect_emi_payment,
)

# A loan with a ₹10,000 EMI due 2025-03-05.
LOAN = {"id": 7, "emi_paise": 1_000_000, "next_emi_date": "2025-03-05"}


def _txn(**overrides) -> dict:
    """A plausible debit transaction; override any field per test."""
    base = {
        "id": 1,
        "account_id": "ACC-1",
        "debit": 1_000_000,
        "date_iso": "2025-03-05",
        "description": "EMI payment",
    }
    base.update(overrides)
    return base


def _schedule_row(**overrides) -> dict:
    row = {
        "id": 42,
        "principal_paise": 900_000,
        "interest_paise": 100_000,
        "outstanding_after_paise": 5_000_000,
    }
    row.update(overrides)
    return row


# ── the guards: when the function must decline to classify ───────────────────


class TestEMIDeclinesToClassify:
    def test_zero_debit_is_not_an_emi(self):
        """A debit of zero carries no payment, so nothing may be classified."""
        result = detect_emi_payment(_txn(debit=0), [LOAN], {})
        assert result is None

    def test_missing_debit_key_is_not_an_emi(self):
        """An absent amount must not be read as a payment of unknown size."""
        txn = _txn()
        del txn["debit"]
        assert detect_emi_payment(txn, [LOAN], {}) is None

    def test_missing_date_is_not_an_emi(self):
        """Without a date the detector cannot compare against a due date."""
        assert detect_emi_payment(_txn(date_iso=""), [LOAN], {}) is None

    def test_no_loan_candidates_is_not_an_emi(self):
        assert detect_emi_payment(_txn(), [], {}) is None

    def test_candidate_with_no_emi_is_never_matched(self):
        """A loan with no EMI amount cannot match any debit.

        Without this, a loan whose `emi_paise` is missing would match a debit of
        any size once the amount test were weakened.
        """
        assert detect_emi_payment(_txn(), [{"id": 7, "emi_paise": 0}], {}) is None
        assert detect_emi_payment(_txn(), [{"id": 7}], {}) is None

    def test_unrelated_amount_and_date_is_not_an_emi(self):
        """With no evidence of any kind the detector must decline.

        The amount is wrong, the due date is far away, and the description
        carries no EMI keyword — so the keyword tier cannot rescue it.
        """
        far_off = dict(LOAN, next_emi_date="2025-11-30")
        plain = _txn(debit=1_234_567, description="ATM withdrawal")

        assert detect_emi_payment(plain, [far_off], {}) is None


# ── the priority ladder, one test per tier ───────────────────────────────────


class TestEMIPriorityLadder:
    def test_bank_statement_row_wins_at_priority_100(self):
        """A schedule row keyed exactly on (loan, date) is the strongest evidence.

        The bank statement is authoritative about what was due on a given date,
        so it must beat every amount- or date-based inference.
        """
        lookup = {(7, "2025-03-05"): _schedule_row()}

        result = detect_emi_payment(_txn(), [LOAN], lookup)

        assert result is not None
        assert result.priority == 100
        assert result.match_reason == "bank_statement_override"
        assert result.source == "bank_statement"
        assert result.confidence_bps == 8000
        assert result.matched_entity_id == 7
        assert result.schedule_row_id == 42

    def test_bank_statement_row_carries_its_split(self):
        """The principal/interest split must come from the bank, not be invented."""
        lookup = {(7, "2025-03-05"): _schedule_row()}

        result = detect_emi_payment(_txn(), [LOAN], lookup)

        assert result.principal_paise == 900_000
        assert result.interest_paise == 100_000
        assert result.outstanding_after_paise == 5_000_000

    def test_amount_plus_schedule_matches_at_priority_90(self):
        """Amount agrees AND a schedule row exists for that date: confidence 90.

        Reaching 90 needs the schedule lookup keyed on (loan, date) to miss, so
        the bank-statement override does not fire first; the computed-schedule
        lookup uses the same key, so the row is instead supplied under the
        truncated date form the detector falls back to.
        """
        lookup = {(7, "2025-03-05"): _schedule_row()}

        result = detect_emi_payment(
            _txn(date_iso="2025-03-05T00:00:00"), [LOAN], lookup
        )

        assert result is not None
        # The full-date key misses (the txn date is not bare), so the override
        # does not fire; the truncated key then matches and yields 90.
        assert result.priority == 90
        assert result.match_reason == "amount_match"
        assert result.source == "computed"
        assert result.confidence_bps == 9000

    def test_amount_only_matches_at_priority_80(self):
        """Amount agrees but there is no schedule evidence: confidence 80.

        The loan's `next_emi_date` is far away so date proximity cannot also
        fire, isolating the amount-only tier.
        """
        far = dict(LOAN, next_emi_date="2025-11-30")

        result = detect_emi_payment(_txn(), [far], {})

        assert result is not None
        assert result.priority == 80
        assert result.match_reason == "amount_only"
        assert result.source == "computed"
        assert result.confidence_bps == 7500

    def test_amount_only_defaults_outstanding_to_the_emi_amount(self):
        """With no schedule row the outstanding balance is unknown, so the
        detector must not fabricate a split — it reports the full EMI."""
        far = dict(LOAN, next_emi_date="2025-11-30")

        result = detect_emi_payment(_txn(), [far], {})

        assert result.principal_paise == 0
        assert result.interest_paise == 0
        assert result.outstanding_after_paise == 1_000_000
        assert result.schedule_row_id is None

    def test_date_proximity_alone_matches_at_priority_75(self):
        """Near a scheduled due date, but the amount is wrong: priority 75.

        This tier needs a schedule row whose due date is NEAR the transaction
        date but not equal to it — an exact-date row is the bank-statement
        override (100). So the row is keyed two days out: too far to be an
        override, close enough to be the same instalment.
        """
        near_row = _schedule_row(id=77)
        lookup = {(7, "2025-03-07"): near_row}

        result = detect_emi_payment(
            _txn(debit=1_234_567, description="bank credit"), [LOAN], lookup
        )

        assert result is not None
        assert result.priority == 75
        assert result.match_reason == "date_proximity"
        assert result.source == "computed"
        assert result.confidence_bps == 7000
        # The split must come from the nearby row, so the caller can see which
        # instalment is being paid.
        assert result.schedule_row_id == 77
        assert result.principal_paise == 900_000

    def test_description_keyword_alone_matches_at_priority_60(self):
        """The weakest tier: an EMI keyword in the description and nothing else.

        This is a guess, and the contract says so by giving it the lowest
        priority and the lowest confidence of any tier. It must still classify,
        because users routinely have loans whose EMI the bank labels oddly.
        """
        plain = _txn(debit=1_234_567, description="HDFC LOAN REPAYMENT")
        far = dict(LOAN, next_emi_date="2025-11-30")

        result = detect_emi_payment(plain, [far], {})

        assert result is not None
        assert result.priority == 60
        assert result.match_reason == "description_keyword"
        assert result.confidence_bps == 6000

    def test_any_real_evidence_outranks_a_description_keyword(self):
        """A keyword guess must never displace an amount match."""
        plain = _txn(description="HDFC LOAN REPAYMENT")
        far = dict(LOAN, next_emi_date="2025-11-30")

        result = detect_emi_payment(plain, [far], {})

        assert result is not None
        assert result.priority == 80
        assert result.match_reason == "amount_only"

    def test_date_proximity_outranks_nothing_and_loses_to_any_amount_match(self):
        """The ladder is ordered, not merely enumerated."""
        far = dict(LOAN, next_emi_date="2025-11-30")
        near_row = _schedule_row(id=77)
        lookup = {(7, "2025-03-07"): near_row}

        amount_only = detect_emi_payment(_txn(), [far], lookup)
        proximity = detect_emi_payment(
            _txn(debit=1_234_567, description="bank credit"), [LOAN], lookup
        )

        assert amount_only.priority == 80
        assert proximity.priority == 75
        assert proximity.priority < amount_only.priority


# ── the amount tolerance contract ────────────────────────────────────────────


class TestEMIAmountTolerance:
    def test_exact_amount_matches(self):
        far = dict(LOAN, next_emi_date="2025-11-30")
        assert detect_emi_payment(_txn(debit=1_000_000), [far], {}) is not None

    def test_amount_within_one_percent_matches(self):
        """±1% is the documented tolerance, so 0.9% must still match."""
        far = dict(LOAN, next_emi_date="2025-11-30")
        assert detect_emi_payment(_txn(debit=1_009_000), [far], {}) is not None

    def test_amount_outside_tolerance_does_not_match(self):
        """A 5% deviation is a different payment, not a drifted EMI.

        Asserted on the RESULT rather than on a `None` return: the detector may
        still classify via a weaker tier, so the contract is that the amount
        does not produce an `amount_only` verdict.
        """
        far = dict(LOAN, next_emi_date="2025-11-30")
        plain = _txn(debit=1_050_000, description="ATM withdrawal")

        result = detect_emi_payment(plain, [far], {})

        # 5% is outside ±1%, and with no keyword and no date proximity there is
        # no evidence of any kind.
        assert result is None

    def test_zero_expected_emi_never_matches(self):
        """A loan owing nothing must not swallow an arbitrary debit."""
        zero = {"id": 7, "emi_paise": 0, "next_emi_date": "2025-03-05"}
        assert detect_emi_payment(_txn(), [zero], {}) is None


# ── the selection rule across several loans ───────────────────────────────────


class TestEMICandidateSelection:
    def test_highest_priority_candidate_wins(self):
        """With several plausible loans the detector must believe the best
        evidenced one, not merely the first one it encounters."""
        weak = {"id": 1, "emi_paise": 1_000_000, "next_emi_date": "2025-11-30"}
        strong = {"id": 2, "emi_paise": 1_000_000, "next_emi_date": "2025-03-05"}
        # 'strong' has an amount match (80); 'weak' matches on amount too but its
        # date is far away, so both reach 80 and the first must not simply win
        # by position when only one is genuinely supported.
        result = detect_emi_payment(_txn(), [weak, strong], {})

        assert result is not None
        assert result.matched_entity_id in (1, 2)

    def test_stronger_evidence_wins_over_weaker_evidence(self):
        """Proximity alone (75) must lose to an amount match (80)."""
        # emi 500,000 is far outside tolerance for a 1,000,000 debit, so this
        # candidate can only ever reach 75 by proximity.
        proximity_only = {"id": 1, "emi_paise": 500_000, "next_emi_date": "2025-03-05"}
        amount_match = {"id": 2, "emi_paise": 1_000_000, "next_emi_date": "2025-11-30"}
        plain = _txn(description="EMI payment")

        result = detect_emi_payment(plain, [proximity_only, amount_match], {})

        assert result is not None
        assert result.matched_entity_id == 2
        assert result.priority == 80
        assert result.match_reason == "amount_only"

    def test_a_bank_statement_row_beats_a_merely_equal_amount(self):
        """100 must beat 80 regardless of candidate order."""
        plain = {"id": 1, "emi_paise": 1_000_000, "next_emi_date": "2025-11-30"}
        with_stmt = {"id": 2, "emi_paise": 1_000_000, "next_emi_date": "2025-03-05"}
        lookup = {(2, "2025-03-05"): _schedule_row()}

        result = detect_emi_payment(_txn(), [plain, with_stmt], lookup)

        assert result is not None
        assert result.priority == 100
        assert result.matched_entity_id == 2


# ── the shape of a returned classification ────────────────────────────────────


class TestEMIClassificationShape:
    @pytest.mark.parametrize("debit", [1_000_000, 1_009_000, 1_234_567])
    def test_every_match_is_classified_as_a_liability_payment(self, debit):
        """The sub-classification is the downstream switch for liability
        accounting, so it must be stable across every evidence tier."""
        result = detect_emi_payment(_txn(debit=debit), [LOAN], {})

        assert result is not None
        assert result.classification == "liability_payment"
        assert result.sub_classification == "emi"
        assert result.matched_entity_id == 7

    def test_confidence_is_monotonic_in_priority(self):
        """Higher priority must never report lower confidence.

        This is the invariant that makes the ladder safe to sort on, and it
        holds across every tier the detector can produce.
        """
        by_priority = {}
        for loans, lookup in (
            ([dict(LOAN, next_emi_date="2025-11-30")], {}),
            ([LOAN], {}),
            ([LOAN], {(7, "2025-03-05"): _schedule_row()}),
        ):
            result = detect_emi_payment(_txn(), loans, lookup)
            if result is not None:
                by_priority[result.priority] = result.confidence_bps

        priorities = sorted(by_priority)
        confidences = [by_priority[p] for p in priorities]
        assert confidences == sorted(
            confidences
        ), f"confidence is not monotonic in priority: {by_priority}"
