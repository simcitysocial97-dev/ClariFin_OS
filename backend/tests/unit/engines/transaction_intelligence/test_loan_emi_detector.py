"""Direct unit tests for src/engines/transaction_intelligence/loan_emi_detector.py.

M9-C42.25 — direct behavioral ownership of EMI detection: tolerance and date
helpers, the bank-statement override short-circuit, the priority scoring
matrix (100/90/85/80/75/60), schedule row attribution, and candidate filtering.
"""

from src.engines.transaction_intelligence.loan_emi_detector import (
    EMI_KEYWORDS,
    _amount_within_tolerance,
    _date_near_expected,
    _is_emi_description,
    detect_emi_payment,
    find_loan_candidates_for_account,
)

# ============================================================
# Helpers
# ============================================================


def test_is_emi_description_matches_keywords():
    for desc in [
        "HDFC LOAN EMI",
        "emi payment",
        "INSTALLMENT",
        "REPAYMENT",
        "MORTGAGE",
    ]:
        assert _is_emi_description(desc) is True


def test_is_emi_description_rejects_plain_descriptions():
    assert _is_emi_description("GROCERY STORE") is False
    assert _is_emi_description("") is False


def test_emi_keywords_contents():
    assert "emi" in EMI_KEYWORDS
    assert "loan" in EMI_KEYWORDS
    assert "installment" in EMI_KEYWORDS


def test_amount_within_tolerance_exact_match():
    assert _amount_within_tolerance(1_000_000, 1_000_000) is True


def test_amount_within_tolerance_at_boundary():
    assert _amount_within_tolerance(1_010_000, 1_000_000) is True
    assert _amount_within_tolerance(990_000, 1_000_000) is True


def test_amount_within_tolerance_just_outside():
    assert _amount_within_tolerance(1_010_001, 1_000_000) is False
    assert _amount_within_tolerance(989_999, 1_000_000) is False


def test_amount_within_tolerance_zero_expected():
    assert _amount_within_tolerance(100, 0) is False
    assert _amount_within_tolerance(0, 0) is False


def test_date_near_expected_within_three_days():
    assert _date_near_expected("2026-08-01", "2026-08-01") is True
    assert _date_near_expected("2026-08-01", "2026-08-04") is True
    assert _date_near_expected("2026-08-04", "2026-08-01") is True


def test_date_near_expected_beyond_three_days():
    assert _date_near_expected("2026-08-01", "2026-08-05") is False


def test_date_near_expected_invalid_inputs():
    assert _date_near_expected("bad", "2026-08-01") is False
    assert _date_near_expected("2026-08-01", "") is False


def test_date_near_expected_custom_window():
    assert _date_near_expected("2026-08-01", "2026-08-06", days=5) is True
    assert _date_near_expected("2026-08-01", "2026-08-07", days=5) is False


# ============================================================
# detect_emi_payment — guards
# ============================================================


def make_txn(debit=1_000_000, date="2026-08-01", desc="COFFEE SHOP", **extra):
    txn = {
        "id": 1,
        "account_id": "A1",
        "debit": debit,
        "date_iso": date,
        "description": desc,
    }
    txn.update(extra)
    return txn


LOAN = {"id": 5, "emi_paise": 1_000_000, "next_emi_date": None}


def test_detect_returns_none_for_zero_amount():
    assert detect_emi_payment(make_txn(debit=0), [LOAN], {}) is None


def test_detect_returns_none_for_negative_amount():
    assert detect_emi_payment(make_txn(debit=-5), [LOAN], {}) is None


def test_detect_returns_none_for_missing_date():
    assert detect_emi_payment(make_txn(date=""), [LOAN], {}) is None


def test_detect_returns_none_for_empty_candidates():
    assert detect_emi_payment(make_txn(), [], {}) is None


def test_detect_skips_loans_without_positive_emi():
    assert detect_emi_payment(make_txn(), [{"id": 5, "emi_paise": 0}], {}) is None


def test_detect_uses_amount_paise_fallback_key():
    txn = {
        "id": 1,
        "amount_paise": 1_000_000,
        "date_iso": "2026-08-01",
        "description": "COFFEE",
    }
    result = detect_emi_payment(txn, [LOAN], {})
    assert result is not None
    assert result.match_reason == "amount_only"


# ============================================================
# detect_emi_payment — bank statement override (priority 100)
# ============================================================


def test_bank_statement_override_takes_precedence():
    lookup = {
        (5, "2026-08-01"): {
            "id": 77,
            "principal_paise": 600_000,
            "interest_paise": 400_000,
            "outstanding_after_paise": 9_000_000,
        }
    }
    result = detect_emi_payment(make_txn(debit=1), [LOAN], lookup)
    assert result is not None
    assert result.priority == 100
    assert result.confidence_bps == 8000
    assert result.source == "bank_statement"
    assert result.match_reason == "bank_statement_override"
    assert result.matched_entity_id == 5
    assert result.schedule_row_id == 77
    assert result.principal_paise == 600_000
    assert result.interest_paise == 400_000
    assert result.outstanding_after_paise == 9_000_000


def test_bank_statement_override_ignores_amount_mismatch():
    lookup = {(5, "2026-08-01"): {"id": 77}}
    result = detect_emi_payment(make_txn(debit=999), [LOAN], lookup)
    assert result is not None
    assert result.priority == 100
    # Missing row fields default to zero / None-free values.
    assert result.principal_paise == 0
    assert result.interest_paise == 0
    assert result.outstanding_after_paise == 0


def test_bank_statement_override_beats_higher_scoring_computed_match():
    # Amount + schedule would be priority 90; override returns immediately.
    lookup = {
        (5, "2026-08-01"): {"id": 77},
    }
    loan = {**LOAN, "next_emi_date": "2026-08-01"}
    result = detect_emi_payment(make_txn(), [loan], lookup)
    assert result is not None
    assert result.priority == 100
    assert result.source == "bank_statement"


# ============================================================
# detect_emi_payment — computed matches
# ============================================================

SCHEDULE_ROW = {
    "id": 33,
    "principal_paise": 650_000,
    "interest_paise": 350_000,
    "outstanding_after_paise": 8_000_000,
}


def test_amount_plus_schedule_match_priority_90():
    # Long-form date exercises the [:10] truncation: override key uses the
    # raw date (misses), computed key uses truncated date (hits).
    txn = make_txn(date="2026-08-01T00:00:00")
    lookup = {(5, "2026-08-01"): SCHEDULE_ROW}
    result = detect_emi_payment(txn, [LOAN], lookup)
    assert result is not None
    assert result.priority == 90
    assert result.confidence_bps == 9000
    assert result.match_reason == "amount_match"
    assert result.source == "computed"
    assert result.schedule_row_id == 33
    assert result.principal_paise == 650_000
    assert result.interest_paise == 350_000
    assert result.outstanding_after_paise == 8_000_000


def test_amount_only_match_priority_80():
    result = detect_emi_payment(make_txn(), [LOAN], {})
    assert result is not None
    assert result.priority == 80
    assert result.confidence_bps == 7500
    assert result.match_reason == "amount_only"
    assert result.schedule_row_id is None
    assert result.principal_paise == 0
    assert result.interest_paise == 0
    assert result.outstanding_after_paise == 1_000_000


def test_amount_plus_date_proximity_priority_85():
    loan = {**LOAN, "next_emi_date": "2026-08-02"}
    result = detect_emi_payment(make_txn(), [loan], {})
    assert result is not None
    assert result.priority == 85
    assert result.confidence_bps == 7500
    assert result.match_reason == "amount+date"


def test_schedule_match_beats_date_proximity_boost():
    # amount+schedule = 90 must not be downgraded by the 85 date path.
    loan = {**LOAN, "next_emi_date": "2026-08-02"}
    txn = make_txn(date="2026-08-01T00:00:00")
    lookup2 = {(5, "2026-08-01"): SCHEDULE_ROW}
    result = detect_emi_payment(txn, [loan], lookup2)
    assert result is not None
    assert result.priority == 90


def test_date_proximity_only_with_nearby_schedule_priority_75():
    txn = make_txn(debit=2_500_000)  # amount mismatch
    loan = {**LOAN, "next_emi_date": "2026-08-02"}
    lookup = {(5, "2026-08-02"): SCHEDULE_ROW}
    result = detect_emi_payment(txn, [loan], lookup)
    assert result is not None
    assert result.priority == 75
    assert result.confidence_bps == 7000
    assert result.match_reason == "date_proximity"
    assert result.schedule_row_id == 33


def test_date_proximity_without_nearby_schedule_no_match():
    txn = make_txn(debit=2_500_000)
    loan = {**LOAN, "next_emi_date": "2026-08-02"}
    lookup = {(5, "2026-09-15"): SCHEDULE_ROW}
    assert detect_emi_payment(txn, [loan], lookup) is None


def test_date_far_from_expected_no_date_match():
    txn = make_txn(debit=2_500_000)
    loan = {**LOAN, "next_emi_date": "2026-09-01"}
    assert detect_emi_payment(txn, [loan], {}) is None


def test_description_keyword_fallback_priority_60():
    txn = make_txn(debit=2_500_000, desc="HDFC LOAN EMI")
    result = detect_emi_payment(txn, [LOAN], {})
    assert result is not None
    assert result.priority == 60
    assert result.confidence_bps == 6000
    assert result.match_reason == "description_keyword"


def test_description_keyword_does_not_downgrade_better_match():
    txn = make_txn(desc="HDFC LOAN EMI")  # amount matches too
    result = detect_emi_payment(txn, [LOAN], {})
    assert result is not None
    assert result.priority == 80


def test_no_match_returns_none():
    txn = make_txn(debit=2_500_000, desc="COFFEE SHOP")
    assert detect_emi_payment(txn, [LOAN], {}) is None


def test_multiple_loans_best_priority_wins():
    loans = [
        {"id": 1, "emi_paise": 1_000_000, "next_emi_date": None},
        {"id": 2, "emi_paise": 2_500_000, "next_emi_date": "2026-08-01"},
    ]
    txn = make_txn(debit=2_500_000)
    result = detect_emi_payment(txn, loans, {})
    assert result is not None
    # Loan 2: amount match (80) + date proximity -> 85 beats loan 1's none.
    assert result.matched_entity_id == 2
    assert result.priority == 85


def test_first_loan_wins_on_equal_priority():
    loans = [
        {"id": 1, "emi_paise": 1_000_000, "next_emi_date": None},
        {"id": 2, "emi_paise": 1_000_000, "next_emi_date": None},
    ]
    result = detect_emi_payment(make_txn(), loans, {})
    assert result is not None
    assert result.matched_entity_id == 1


def test_result_classification_fields_constant():
    result = detect_emi_payment(make_txn(), [LOAN], {})
    assert result is not None
    assert result.classification == "liability_payment"
    assert result.sub_classification == "emi"


# ============================================================
# find_loan_candidates_for_account
# ============================================================


def test_find_candidates_exact_lender_match():
    loans = [{"id": 1, "lender": "HDFC"}]
    assert find_loan_candidates_for_account("HDFC", loans) == loans


def test_find_candidates_substring_case_insensitive():
    loans = [{"id": 1, "lender": "HDFC"}]
    assert find_loan_candidates_for_account("my hdfc bank acct", loans) == loans


def test_find_candidates_no_match():
    loans = [{"id": 1, "lender": "ICICI"}]
    assert find_loan_candidates_for_account("hdfc", loans) == []


def test_find_candidates_empty_loan_list():
    assert find_loan_candidates_for_account("hdfc", []) == []


def test_find_candidates_missing_lender_is_matched():
    # Known quirk pinned: empty lender string is a substring of every account
    # id, so lender-less loans pass the filter. Documented for reconciliation.
    loans = [{"id": 1}]
    assert find_loan_candidates_for_account("hdfc", loans) == loans
