"""Real property/invariant tests for transaction intelligence detectors.

M9-C42.25 — replaces the tautological surface with properties that actually
call production code. Every property here binds src/engines/transaction_intelligence.

Existing tautological tests in test_engine_properties.py are preserved (C42.25
non-goal: no removal of existing tests); this file adds the meaningful surface.
"""

from __future__ import annotations

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from src.engines.transaction_intelligence.cash_conversion_detector import (
    _calculate_fee_bps,
    _date_difference_days,
    _determine_zone,
    _hungarian_inline,
    _is_savings_or_current,
    detect,
)
from src.engines.transaction_intelligence.cc_payment_detector import (
    classify_cc_payment,
    determine_payment_channel,
    extract_card_last4,
)
from src.engines.transaction_intelligence.loan_emi_detector import (
    _amount_within_tolerance,
    _date_near_expected,
    detect_emi_payment,
    find_loan_candidates_for_account,
)

SETTINGS = settings(
    max_examples=25, suppress_health_check=[HealthCheck.differing_executors]
)

PROVIDER = {
    "provider_name": "CRED",
    "description_pattern": "CRED",
    "typical_settlement_days": 2,
    "fee_min_bps": 100,
    "fee_max_bps": 300,
    "review_fee_min_bps": 301,
    "review_fee_max_bps": 500,
}

VALID_ZONES = {"auto", "review", "unmatched_provider"}


def make_debit(debit_paise: int) -> dict:
    return {
        "id": 1,
        "description": "CRED CASH LIQUIDITY",
        "debit": debit_paise,
        "date_iso": "2026-08-01",
        "household_id": 7,
    }


def make_credit(txn_id: int, amount: int) -> dict:
    return {
        "id": txn_id,
        "account_id": 100,
        "account_type": "savings",
        "household_id": 7,
        "credit": amount,
        "date_iso": "2026-08-02",
    }


# ============================================================
# Cash conversion detector
# ============================================================


class TestCashConversionProperties:
    @SETTINGS
    @given(amount=st.integers(max_value=0))
    def test_non_positive_debit_never_detects(self, amount: int) -> None:
        assert (
            detect(make_debit(amount), [make_credit(1, 500_000)], [PROVIDER], [])
            is None
        )

    @SETTINGS
    @given(amount=st.integers(min_value=100_000, max_value=10_000_000))
    def test_credit_above_debit_never_eligible(self, amount: int) -> None:
        credit_row = make_credit(1, amount + 1)
        result = detect(make_debit(amount), [credit_row], [PROVIDER], [])
        assert result is None

    @SETTINGS
    @given(amount=st.integers(min_value=100_000, max_value=10_000_000))
    def test_result_confidence_bounded(self, amount: int) -> None:
        credit_row = make_credit(1, amount - 2_500)
        result = detect(make_debit(amount), [credit_row], [PROVIDER], [])
        if result is not None:
            assert 0 <= result.confidence_bps <= 9900
            assert result.zone in VALID_ZONES

    @SETTINGS
    @given(amount=st.integers(min_value=100_000, max_value=10_000_000))
    def test_fee_arithmetic_reconciles(self, amount: int) -> None:
        credit_amount = amount - (amount // 40)  # ~2.5% fee
        assume(credit_amount > 0)
        result = detect(
            make_debit(amount), [make_credit(1, credit_amount)], [PROVIDER], []
        )
        if result is not None:
            assert result.fee_paise == amount - credit_amount
            assert result.fee_bps == _calculate_fee_bps(amount, credit_amount)

    @SETTINGS
    @given(
        debit=st.integers(min_value=1, max_value=10_000_000),
        credit=st.integers(min_value=0, max_value=10_000_000),
    )
    def test_fee_bps_non_negative_when_credit_leq_debit(
        self, debit: int, credit: int
    ) -> None:
        assume(credit <= debit)
        assert _calculate_fee_bps(debit, credit) >= 0

    @SETTINGS
    @given(fee=st.integers(min_value=0, max_value=2000))
    def test_determine_zone_result_is_valid(self, fee: int) -> None:
        zone = _determine_zone(fee, 100, 300, 301, 500)
        assert zone in ("auto", "review", None)
        if zone == "auto":
            assert 100 <= fee <= 300
        if zone == "review":
            assert 301 <= fee <= 500

    @SETTINGS
    @given(
        matrix=st.lists(
            st.lists(
                st.floats(min_value=0, max_value=1e9, allow_nan=False),
                min_size=2,
                max_size=2,
            ),
            min_size=2,
            max_size=2,
        )
    )
    def test_hungarian_assignments_are_one_to_one(self, matrix) -> None:
        assignments = _hungarian_inline([list(row) for row in matrix])
        rows = [i for i, _ in assignments]
        cols = [j for _, j in assignments]
        assert len(rows) == len(set(rows))
        assert len(cols) == len(set(cols))

    @SETTINGS
    @given(
        account_type=st.sampled_from(
            ["savings", "current", "loan", "credit_card", "od"]
        )
    )
    def test_savings_or_current_predicate(self, account_type: str) -> None:
        assert _is_savings_or_current(account_type) == (
            account_type in ("savings", "current")
        )

    @SETTINGS
    @given(
        day_a=st.integers(min_value=1, max_value=28),
        day_b=st.integers(min_value=1, max_value=28),
    )
    def test_date_difference_antisymmetric(self, day_a: int, day_b: int) -> None:
        a = f"2026-08-{day_a:02d}"
        b = f"2026-08-{day_b:02d}"
        assert _date_difference_days(a, b) == -_date_difference_days(b, a)


# ============================================================
# Credit card payment detector
# ============================================================


class TestCcPaymentProperties:
    @SETTINGS
    @given(desc=st.text(min_size=0, max_size=40))
    def test_card_last4_none_or_four_digits(self, desc: str) -> None:
        result = extract_card_last4(desc)
        assert result is None or (len(result) == 4 and result.isdigit())

    @SETTINGS
    @given(desc=st.text(min_size=0, max_size=60))
    def test_payment_channel_in_known_vocabulary(self, desc: str) -> None:
        assert determine_payment_channel(desc) in (
            "DIRECT",
            "CRED",
            "CHEQ",
            "SPAYLATER",
            "NOBROKER",
            "UNKNOWN",
        )

    @SETTINGS
    @given(
        due=st.integers(min_value=1_000, max_value=10_000_000),
        payment=st.integers(min_value=0, max_value=12_000_000),
        min_due=st.integers(min_value=0, max_value=10_000_000),
    )
    def test_lifecycle_state_consistent_with_amounts(
        self, due: int, payment: int, min_due: int
    ) -> None:
        assume(min_due <= due)
        txn = {
            "id": 1,
            "description": "CC",
            "amount_paise": payment,
            "date_iso": "2026-08-01",
        }
        statement = {"id": 9, "total_amount_due": due, "minimum_amount_due": min_due}
        result = classify_cc_payment(txn, statement)
        if payment >= due - 100:
            assert result.lifecycle_state == "fully_paid"
            assert result.remaining_outstanding_paise == 0
        else:
            assert result.remaining_outstanding_paise == due - payment
            if payment >= min_due:
                assert result.lifecycle_state == "revolving"
            else:
                assert result.lifecycle_state == "payment_received"

    @SETTINGS
    @given(payment=st.integers(min_value=0, max_value=10_000_000))
    def test_unmatched_statement_zeroes_ledger_fields(self, payment: int) -> None:
        txn = {
            "id": 1,
            "description": "CC",
            "amount_paise": payment,
            "date_iso": "2026-08-01",
        }
        result = classify_cc_payment(txn, None)
        assert result.statement_amount_paise == 0
        assert result.minimum_due_paise == 0
        assert result.remaining_outstanding_paise == 0
        assert result.lifecycle_state == "unknown"


# ============================================================
# Loan EMI detector
# ============================================================


class TestLoanEmiProperties:
    VALID_PRIORITIES = {60, 75, 80, 85, 90, 100}
    VALID_CONFIDENCES = {6000, 7000, 7500, 8000, 9000}

    @SETTINGS
    @given(
        expected=st.integers(min_value=1, max_value=10_000_000),
        delta=st.integers(min_value=0, max_value=10_000_000),
    )
    def test_tolerance_symmetric(self, expected: int, delta: int) -> None:
        amount_low = expected - delta
        amount_high = expected + delta
        assume(amount_low > 0)
        assert _amount_within_tolerance(
            amount_low, expected
        ) == _amount_within_tolerance(amount_high, expected)

    @SETTINGS
    @given(expected=st.integers(min_value=1, max_value=10_000_000))
    def test_exact_amount_always_within_tolerance(self, expected: int) -> None:
        assert _amount_within_tolerance(expected, expected) is True

    @SETTINGS
    @given(
        day_a=st.integers(min_value=1, max_value=28),
        day_b=st.integers(min_value=1, max_value=28),
    )
    def test_date_proximity_symmetric(self, day_a: int, day_b: int) -> None:
        a = f"2026-08-{day_a:02d}"
        b = f"2026-08-{day_b:02d}"
        assert _date_near_expected(a, b) == _date_near_expected(b, a)

    @SETTINGS
    @given(
        amount=st.integers(max_value=0),
        date=st.sampled_from(["", "2026-08-01"]),
    )
    def test_zero_amount_or_guarded_inputs_return_none(
        self, amount: int, date: str
    ) -> None:
        txn = {"id": 1, "debit": amount, "date_iso": date, "description": "LOAN EMI"}
        assert detect_emi_payment(txn, [{"id": 1, "emi_paise": 100_000}], {}) is None

    @SETTINGS
    @given(
        emi=st.integers(min_value=1_000, max_value=10_000_000),
        desc=st.sampled_from(["LOAN EMI", "COFFEE", "EMI", "GROCERY"]),
    )
    def test_result_priority_and_confidence_in_vocabulary(
        self, emi: int, desc: str
    ) -> None:
        txn = {
            "id": 1,
            "debit": emi,
            "date_iso": "2026-08-01",
            "description": desc,
        }
        loans = [{"id": 1, "emi_paise": emi, "next_emi_date": None}]
        result = detect_emi_payment(txn, loans, {})
        if result is not None:
            assert result.priority in self.VALID_PRIORITIES
            assert result.confidence_bps in self.VALID_CONFIDENCES
            assert result.classification == "liability_payment"
            assert result.sub_classification == "emi"

    @SETTINGS
    @given(
        emi=st.integers(min_value=1_000, max_value=10_000_000),
        day=st.integers(min_value=1, max_value=28),
    )
    def test_detection_is_deterministic(self, emi: int, day: int) -> None:
        txn = {
            "id": 1,
            "debit": emi,
            "date_iso": f"2026-08-{day:02d}",
            "description": "LOAN EMI",
        }
        loans = [{"id": 1, "emi_paise": emi, "next_emi_date": f"2026-08-{day:02d}"}]
        first = detect_emi_payment(txn, loans, {})
        second = detect_emi_payment(txn, loans, {})
        assert first == second

    @SETTINGS
    @given(
        lender=st.sampled_from(["HDFC", "ICICI", "SBI", "AXIS"]),
        account=st.sampled_from(["HDFC savings", "icici bank", "kotak", "SBI"]),
    )
    def test_candidate_filter_returns_subset(self, lender: str, account: str) -> None:
        loans = [
            {"id": 1, "lender": lender},
            {"id": 2, "lender": "OTHER"},
        ]
        result = find_loan_candidates_for_account(account, loans)
        assert all(loan in loans for loan in result)
