"""Direct unit tests for src/engines/transaction_intelligence/cash_conversion_detector.py.

M9-C42.25 — direct behavioral ownership of the liquidity-extraction detector:
helper math, provider matching, eligibility filters, zone classification,
disambiguation, confidence ladder, and the unknown-provider structural path.

All monetary values are integer paise. Anomaly TXN-E1 (see C42.25 inventory):
the unknown-provider selection subtracts a bps constant from a paise amount;
current behavior is pinned here intentionally (documented, not silently fixed).
"""

from datetime import datetime

import pytest
from src.engines.transaction_intelligence.cash_conversion_detector import (
    CashConversionResult,
    _calculate_fee_bps,
    _date_difference_days,
    _determine_zone,
    _hungarian_inline,
    _is_savings_or_current,
    _match_description_pattern,
    _match_purpose,
    _parse_date_iso,
    detect,
)

# ============================================================
# Fixtures
# ============================================================

PROVIDER = {
    "provider_name": "CRED",
    "description_pattern": "CRED",
    "typical_settlement_days": 2,
    "fee_min_bps": 100,
    "fee_max_bps": 300,
    "review_fee_min_bps": 301,
    "review_fee_max_bps": 500,
}

PURPOSES = [{"purpose": "rent", "description_pattern": "RENT"}]

DEBIT = {
    "id": 1,
    "description": "CRED CASH LIQUIDITY",
    "debit": 1_000_000,
    "date_iso": "2026-08-01",
    "household_id": 7,
}


def credit(
    txn_id=11, amount=975_000, date="2026-08-02", household=7, account_type="savings"
):
    row = {
        "id": txn_id,
        "account_id": 100 + txn_id,
        "credit": amount,
        "date_iso": date,
        "household_id": household,
    }
    if account_type is not None:
        row["account_type"] = account_type
    return row


# ============================================================
# Helpers
# ============================================================


def test_parse_date_iso_valid():
    assert _parse_date_iso("2026-08-01") == datetime(2026, 8, 1)


def test_parse_date_iso_empty_and_invalid():
    assert _parse_date_iso("") is None
    assert _parse_date_iso("not-a-date") is None
    assert _parse_date_iso("2026-13-01") is None


def test_date_difference_days_positive_and_negative():
    assert _date_difference_days("2026-08-01", "2026-08-03") == 2
    assert _date_difference_days("2026-08-03", "2026-08-01") == -2
    assert _date_difference_days("2026-08-01", "2026-08-01") == 0


def test_date_difference_days_invalid_inputs_force_out_of_window():
    assert _date_difference_days("bad", "2026-08-01") == 999
    assert _date_difference_days("2026-08-01", "") == 999


def test_match_description_pattern_case_insensitive():
    assert _match_description_pattern("Hello World", "world") is True
    assert _match_description_pattern("nothing here", "world") is False


def test_match_description_pattern_empty_and_bad_regex():
    assert _match_description_pattern("", "world") is False
    assert _match_description_pattern("abc", "") is False
    assert _match_description_pattern("abc", "[unclosed") is False


def test_match_purpose_returns_first_match():
    result = _match_purpose("MY RENT PAYMENT", PURPOSES)
    assert result == "rent"


def test_match_purpose_no_match_returns_none():
    assert _match_purpose("GROCERY STORE", PURPOSES) is None


def test_match_purpose_skips_non_string_purpose_values():
    patterns = [
        {"purpose": None, "description_pattern": "RENT"},
        {"purpose": "utilities", "description_pattern": "RENT"},
    ]
    assert _match_purpose("RENT", patterns) == "utilities"


def test_match_purpose_missing_pattern_key_raises():
    # Production contract: every purpose pattern must carry
    # 'description_pattern'; absent key is a configuration error.
    with pytest.raises(KeyError):
        _match_purpose("RENT", [{"purpose": "rent"}])


def test_is_savings_or_current():
    assert _is_savings_or_current("savings") is True
    assert _is_savings_or_current("current") is True
    assert _is_savings_or_current("loan") is False
    assert _is_savings_or_current("credit_card") is False
    assert _is_savings_or_current("") is False


def test_calculate_fee_bps():
    assert _calculate_fee_bps(1_000_000, 975_000) == 250
    assert _calculate_fee_bps(1_000_000, 1_000_000) == 0


def test_calculate_fee_bps_non_positive_debit_returns_zero():
    assert _calculate_fee_bps(0, 5000) == 0
    assert _calculate_fee_bps(-100, 5000) == 0


def test_determine_zone_auto_range_inclusive():
    assert _determine_zone(100, 100, 300, 301, 500) == "auto"
    assert _determine_zone(300, 100, 300, 301, 500) == "auto"
    assert _determine_zone(200, 100, 300, 301, 500) == "auto"


def test_determine_zone_review_range_inclusive():
    assert _determine_zone(301, 100, 300, 301, 500) == "review"
    assert _determine_zone(500, 100, 300, 301, 500) == "review"
    assert _determine_zone(400, 100, 300, 301, 500) == "review"


def test_determine_zone_outside_all_ranges_returns_none():
    assert _determine_zone(99, 100, 300, 301, 500) is None
    assert _determine_zone(501, 100, 300, 301, 500) is None


def test_hungarian_inline_empty_and_no_candidates():
    assert _hungarian_inline([]) == []
    assert _hungarian_inline([[1e9, 1e9], [1e9, 1e9]]) == []


def test_hungarian_inline_greedy_assignment():
    assignments = _hungarian_inline([[1, 2], [3, 4]])
    assert assignments == [(0, 0), (1, 1)]


def test_hungarian_inline_prefers_low_cost_cells():
    assignments = _hungarian_inline([[5, 1], [1, 5]])
    assert set(assignments) == {(0, 1), (1, 0)}


def test_hungarian_inline_never_reuses_row_or_column():
    assignments = _hungarian_inline([[1, 1], [1, 1]])
    rows = [i for i, _ in assignments]
    cols = [j for _, j in assignments]
    assert len(rows) == len(set(rows))
    assert len(cols) == len(set(cols))


# ============================================================
# detect() — guards
# ============================================================


def test_detect_returns_none_for_zero_debit():
    assert detect({**DEBIT, "debit": 0}, [credit()], [PROVIDER], PURPOSES) is None


def test_detect_returns_none_for_negative_debit():
    assert detect({**DEBIT, "debit": -5000}, [credit()], [PROVIDER], PURPOSES) is None


def test_detect_returns_none_for_missing_debit_key():
    debit = {k: v for k, v in DEBIT.items() if k != "debit"}
    assert detect(debit, [credit()], [PROVIDER], PURPOSES) is None


def test_detect_returns_none_without_provider_or_keyword():
    debit = {**DEBIT, "description": "GROCERY STORE PAYMENT"}
    assert detect(debit, [credit()], [PROVIDER], PURPOSES) is None


# ============================================================
# detect() — known provider flow
# ============================================================


def test_detect_known_provider_auto_zone():
    result = detect(DEBIT, [credit()], [PROVIDER], PURPOSES)
    assert isinstance(result, CashConversionResult)
    assert result.matched_credit_transaction_id == 11
    assert result.provider_name == "CRED"
    assert result.zone == "auto"
    assert result.confidence_bps == 8000
    assert result.fee_paise == 25_000
    assert result.fee_bps == 250
    assert result.settlement_days == 1
    assert result.purpose is None
    assert result.match_reason == "provider_match:CRED:fee_in_range"
    assert "zone=auto" in result.narrative
    assert "Rs10000" in result.narrative


def test_detect_first_matching_provider_wins():
    second = {**PROVIDER, "provider_name": "CHEQ", "description_pattern": "CHEQ"}
    result = detect(DEBIT, [credit()], [PROVIDER, second], PURPOSES)
    assert result is not None
    assert result.provider_name == "CRED"


def test_detect_provider_without_settlement_days_defaults_to_two():
    provider = {k: v for k, v in PROVIDER.items() if k != "typical_settlement_days"}
    result = detect(DEBIT, [credit(date="2026-08-05")], [provider], PURPOSES)
    assert result is not None
    assert result.settlement_days == 4


def test_detect_purpose_matched_into_result_and_narrative():
    debit = {**DEBIT, "description": "CRED RENT PAY"}
    result = detect(debit, [credit()], [PROVIDER], PURPOSES)
    assert result is not None
    assert result.purpose == "rent"
    assert "(rent)" in result.narrative


def test_detect_narrative_uses_general_liquidity_when_no_purpose():
    result = detect(DEBIT, [credit()], [PROVIDER], PURPOSES)
    assert result is not None
    assert "(general liquidity)" in result.narrative


# ---------- eligibility boundaries ----------


def test_detect_rejects_credit_date_before_debit():
    assert detect(DEBIT, [credit(date="2026-07-31")], [PROVIDER], PURPOSES) is None


def test_detect_accepts_credit_at_max_settlement_window():
    result = detect(DEBIT, [credit(date="2026-08-05")], [PROVIDER], PURPOSES)
    assert result is not None
    assert result.settlement_days == 4


def test_detect_rejects_credit_beyond_settlement_window():
    assert detect(DEBIT, [credit(date="2026-08-06")], [PROVIDER], PURPOSES) is None


def test_detect_rejects_credit_equal_to_debit():
    assert detect(DEBIT, [credit(amount=1_000_000)], [PROVIDER], PURPOSES) is None


def test_detect_rejects_credit_from_other_household():
    assert detect(DEBIT, [credit(household=8)], [PROVIDER], PURPOSES) is None


def test_detect_rejects_non_savings_or_current_account():
    assert detect(DEBIT, [credit(account_type="loan")], [PROVIDER], PURPOSES) is None


def test_detect_missing_account_type_defaults_to_savings():
    result = detect(DEBIT, [credit(account_type=None)], [PROVIDER], PURPOSES)
    assert result is not None


def test_detect_returns_none_when_no_eligible_credits():
    assert detect(DEBIT, [], [PROVIDER], PURPOSES) is None


# ---------- zone boundaries ----------


def test_detect_auto_zone_at_fee_min_boundary():
    result = detect(DEBIT, [credit(amount=990_000)], [PROVIDER], PURPOSES)
    assert result is not None
    assert result.fee_bps == 100
    assert result.zone == "auto"


def test_detect_auto_zone_at_fee_max_boundary():
    result = detect(DEBIT, [credit(amount=970_000)], [PROVIDER], PURPOSES)
    assert result is not None
    assert result.fee_bps == 300
    assert result.zone == "auto"


def test_detect_review_zone_just_above_auto():
    result = detect(DEBIT, [credit(amount=969_900)], [PROVIDER], PURPOSES)
    assert result is not None
    assert result.fee_bps == 301
    assert result.zone == "review"
    assert result.confidence_bps == 5500


def test_detect_review_zone_at_review_max_boundary():
    result = detect(DEBIT, [credit(amount=950_000)], [PROVIDER], PURPOSES)
    assert result is not None
    assert result.fee_bps == 500
    assert result.zone == "review"


def test_detect_fee_outside_all_ranges_discarded():
    assert detect(DEBIT, [credit(amount=940_000)], [PROVIDER], PURPOSES) is None


def test_detect_mixed_candidates_all_out_of_range_returns_none():
    credits = [credit(txn_id=11, amount=940_000), credit(txn_id=12, amount=930_000)]
    assert detect(DEBIT, credits, [PROVIDER], PURPOSES) is None


# ---------- disambiguation ----------


def test_detect_prefers_auto_zone_over_review_zone():
    credits = [
        credit(txn_id=12, amount=950_000),  # 500 bps -> review
        credit(txn_id=11, amount=975_000),  # 250 bps -> auto
    ]
    result = detect(DEBIT, credits, [PROVIDER], PURPOSES)
    assert result is not None
    assert result.matched_credit_transaction_id == 11
    assert result.zone == "auto"


def test_detect_picks_auto_closest_to_fee_midpoint():
    credits = [
        credit(txn_id=11, amount=975_000),  # 250 bps, distance 50 from midpoint 200
        credit(txn_id=12, amount=980_000),  # 200 bps, distance 0
    ]
    result = detect(DEBIT, credits, [PROVIDER], PURPOSES)
    assert result is not None
    assert result.matched_credit_transaction_id == 12
    assert result.fee_bps == 200


def test_detect_review_candidates_pick_lowest_fee():
    credits = [
        credit(txn_id=11, amount=950_000),  # 500 bps review
        credit(txn_id=12, amount=960_000),  # 400 bps review
    ]
    result = detect(DEBIT, credits, [PROVIDER], PURPOSES)
    assert result is not None
    assert result.matched_credit_transaction_id == 12
    assert result.fee_bps == 400
    assert result.zone == "review"


# ---------- confidence ladder ----------


def test_detect_confidence_bonus_for_user_confirmed_provider():
    provider = {**PROVIDER, "confirmed_by_user": True}
    result = detect(DEBIT, [credit()], [provider], PURPOSES)
    assert result is not None
    assert result.confidence_bps == 9000


def test_detect_confidence_bonus_for_due_date_within_window():
    result = detect(
        DEBIT,
        [credit()],
        [PROVIDER],
        PURPOSES,
        statement_row={"payment_due_date": "2026-08-05"},
    )
    assert result is not None
    assert result.confidence_bps == 9000


def test_detect_due_date_bonus_at_zero_days():
    result = detect(
        DEBIT,
        [credit()],
        [PROVIDER],
        PURPOSES,
        statement_row={"payment_due_date": "2026-08-01"},
    )
    assert result is not None
    assert result.confidence_bps == 9000


def test_detect_due_date_bonus_at_seven_days():
    result = detect(
        DEBIT,
        [credit()],
        [PROVIDER],
        PURPOSES,
        statement_row={"payment_due_date": "2026-08-08"},
    )
    assert result is not None
    assert result.confidence_bps == 9000


def test_detect_no_due_date_bonus_beyond_seven_days():
    result = detect(
        DEBIT,
        [credit()],
        [PROVIDER],
        PURPOSES,
        statement_row={"payment_due_date": "2026-08-09"},
    )
    assert result is not None
    assert result.confidence_bps == 8000


def test_detect_no_due_date_bonus_when_due_before_debit():
    result = detect(
        DEBIT,
        [credit()],
        [PROVIDER],
        PURPOSES,
        statement_row={"payment_due_date": "2026-07-30"},
    )
    assert result is not None
    assert result.confidence_bps == 8000


def test_detect_due_date_bonus_with_slash_format():
    result = detect(
        DEBIT,
        [credit()],
        [PROVIDER],
        PURPOSES,
        statement_row={"payment_due_date": "05/08/2026"},
    )
    assert result is not None
    assert result.confidence_bps == 9000


def test_detect_due_date_bonus_with_dash_dmy_format():
    result = detect(
        DEBIT,
        [credit()],
        [PROVIDER],
        PURPOSES,
        statement_row={"payment_due_date": "05-08-2026"},
    )
    assert result is not None
    assert result.confidence_bps == 9000


def test_detect_invalid_due_date_gives_no_bonus():
    result = detect(
        DEBIT,
        [credit()],
        [PROVIDER],
        PURPOSES,
        statement_row={"payment_due_date": "not-a-date"},
    )
    assert result is not None
    assert result.confidence_bps == 8000


def test_detect_missing_due_date_in_statement_row():
    result = detect(DEBIT, [credit()], [PROVIDER], PURPOSES, statement_row={})
    assert result is not None
    assert result.confidence_bps == 8000


def test_detect_confidence_capped_at_9900():
    provider = {**PROVIDER, "confirmed_by_user": True}
    result = detect(
        DEBIT,
        [credit()],
        [provider],
        PURPOSES,
        statement_row={"payment_due_date": "2026-08-05"},
    )
    assert result is not None
    assert result.confidence_bps == 9900


def test_detect_review_zone_confidence_with_due_bonus():
    result = detect(
        DEBIT,
        [credit(amount=960_000)],
        [PROVIDER],
        PURPOSES,
        statement_row={"payment_due_date": "2026-08-05"},
    )
    assert result is not None
    assert result.confidence_bps == 6500


# ============================================================
# detect() — unknown provider structural path
# ============================================================


def test_detect_unknown_provider_with_liquidity_keyword_and_credit():
    debit = {**DEBIT, "description": "CASH TRANSFER SERVICE"}
    result = detect(debit, [credit(amount=970_000)], [], PURPOSES)
    assert result is not None
    assert result.provider_name is None
    assert result.zone == "unmatched_provider"
    assert result.confidence_bps == 5000
    assert result.match_reason == "unknown_provider_structural_match"
    assert "unknown provider" in result.narrative


def test_detect_unknown_provider_no_keyword_returns_none():
    debit = {**DEBIT, "description": "GROCERY STORE"}
    assert detect(debit, [credit()], [], PURPOSES) is None


def test_detect_unknown_provider_picks_credit_closest_to_225_bps():
    # TXN-E1 FIXED: selection key is now fee_bps vs 225 bps (not shifted by 225 bps).
    # credit 21: 970_000 -> fee=30_000 -> 300 bps (diff 75 from 225)
    # credit 22: 990_000 -> fee=10_000 -> 100 bps (diff 125 from 225)
    # credit 21 is closer to 225 bps target.
    debit = {**DEBIT, "description": "CASH TRANSFER SERVICE"}
    credits = [
        credit(txn_id=21, amount=970_000),
        credit(txn_id=22, amount=990_000),
    ]
    result = detect(debit, credits, [], PURPOSES)
    assert result is not None
    assert result.matched_credit_transaction_id == 21
    assert result.fee_paise == 30_000
    assert result.fee_bps == 300


def test_detect_unknown_provider_requires_credit_above_10000():
    debit = {**DEBIT, "description": "CASH TRANSFER SERVICE", "debit": 50_000}
    assert detect(debit, [credit(amount=10_000)], [], PURPOSES) is None


def test_detect_unknown_provider_accepts_credit_just_above_10000():
    debit = {**DEBIT, "description": "CASH TRANSFER SERVICE", "debit": 50_000}
    result = detect(debit, [credit(amount=10_001)], [], PURPOSES)
    assert result is not None


def test_detect_unknown_provider_requires_credit_below_debit():
    debit = {**DEBIT, "description": "CASH TRANSFER SERVICE"}
    assert detect(debit, [credit(amount=1_000_000)], [], PURPOSES) is None


def test_detect_unknown_provider_requires_same_household():
    debit = {**DEBIT, "description": "CASH TRANSFER SERVICE"}
    assert detect(debit, [credit(household=9)], [], PURPOSES) is None


def test_detect_unknown_provider_no_eligible_credits_returns_none():
    debit = {**DEBIT, "description": "CASH TRANSFER SERVICE"}
    assert detect(debit, [], [], PURPOSES) is None


def test_detect_unknown_provider_matches_purpose():
    debit = {**DEBIT, "description": "CASH RENT WITHDRAWAL"}
    result = detect(debit, [credit(amount=970_000)], [], PURPOSES)
    assert result is not None
    assert result.purpose == "rent"


def test_detect_unknown_provider_settlement_days_computed():
    debit = {**DEBIT, "description": "CASH TRANSFER SERVICE"}
    result = detect(debit, [credit(date="2026-08-03", amount=970_000)], [], PURPOSES)
    assert result is not None
    assert result.settlement_days == 2


def test_detect_unknown_provider_confirms_narrative_amounts():
    debit = {**DEBIT, "description": "CASH TRANSFER SERVICE"}
    result = detect(debit, [credit(amount=970_000)], [], PURPOSES)
    assert result is not None
    assert "Rs10000" in result.narrative
    assert "Rs9700" in result.narrative
    assert "zone=unmatched_provider" in result.narrative
