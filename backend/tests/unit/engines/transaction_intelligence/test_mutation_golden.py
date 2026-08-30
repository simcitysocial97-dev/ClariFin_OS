"""M9-C46 — transaction_intelligence golden characterization tests.

Locks GENUINE behavioral contracts identified by C45 backlog + C46 gap
analysis. Each test expresses a real invariant; no score-chasing, no
Class-B label/format assertions, no Class-E artificial kills.
"""

from __future__ import annotations

import pytest
from src.engines.transaction_intelligence.cash_conversion_detector import (
    _calculate_fee_bps,
    _hungarian_inline,
    detect,
)
from src.engines.transaction_intelligence.cc_payment_detector import (
    _convert_to_paise,
    classify_cc_payment,
    detect_cc_payment,
    determine_payment_channel,
    extract_card_last4,
)
from src.engines.transaction_intelligence.loan_emi_detector import (
    _amount_within_tolerance,
    detect_emi_payment,
)

# ── Shared fixtures ───────────────────────────────────────────────────────────

DEBIT_CASH = {
    "id": 1,
    "description": "CASH TRANSFER",
    "debit": 100_000,
    "date_iso": "2026-08-01",
    "household_id": 7,
}

PROVIDER_CRED = {
    "provider_name": "CRED",
    "description_pattern": "CRED",
    "typical_settlement_days": 2,
    "fee_min_bps": 100,
    "fee_max_bps": 300,
    "review_fee_min_bps": 301,
    "review_fee_max_bps": 500,
}

PURPOSES = [{"purpose": "rent", "description_pattern": "RENT"}]


def _credit(txn_id=11, amount=90_000, date="2026-08-02", household=7):
    return {
        "id": txn_id,
        "account_id": 100 + txn_id,
        "credit": amount,
        "date_iso": date,
        "household_id": household,
        "account_type": "savings",
    }


TXN_CC = {
    "id": 1,
    "description": "CC PAYMENT",
    "amount_paise": 1_000_000,
    "date_iso": "2026-08-01",
}
STATEMENT = {"id": 9, "total_amount_due": 1_000_000, "minimum_amount_due": 50_000}


# ═══════════════════════════════════════════════════════════════════════════════
# A1: Card pattern bypasses amount-window rejection
# ═══════════════════════════════════════════════════════════════════════════════
# Genuine contract: if a card reference is in the description, the
# 10_000 < amount <= 500_000 window rejection is NOT applied.


@pytest.mark.parametrize(
    "desc,amount,expected_none",
    [
        # Pattern present → bypasses window even at/in/out range
        ("TXN 5678 DONE", 100_000, False),  # in window but pattern → unmatched
        ("TXN 5678 DONE", 500_000, False),  # at upper boundary, pattern
        ("TXN 5678 DONE", 500_001, False),  # above upper, pattern → still unmatched
    ],
)
def test_card_pattern_bypasses_amount_window(desc, amount, expected_none):
    txn = {**TXN_CC, "description": desc, "amount_paise": amount}
    result = detect_cc_payment(txn, None)
    if expected_none:
        assert result is None
    else:
        assert result is not None
        assert result.classification == "credit_card_payment_unmatched"


def test_no_pattern_in_window_no_statement_returns_none():
    """No keywords, no card pattern, amount in window, no statement → None.
    This is the normal rejection path for the window guard."""
    txn = {**TXN_CC, "description": "SOME GENERIC PAYMENT", "amount_paise": 100_000}
    assert detect_cc_payment(txn, None) is None


# ═══════════════════════════════════════════════════════════════════════════════
# A3: Amount window boundaries (no keyword, no pattern)
# ═══════════════════════════════════════════════════════════════════════════════


def test_window_boundary_10000_not_rejected():
    """Amount EXACTLY 10_000: the check is `10000 < amount` so 10_000
    fails the condition → NOT rejected → falls through to classify."""
    txn = {**TXN_CC, "description": "GENERIC", "amount_paise": 10_000}
    result = detect_cc_payment(txn, None)
    # Not in window, so not rejected; falls through to classify → unmatched
    assert result is not None
    assert result.classification == "credit_card_payment_unmatched"


def test_window_just_above_10000_rejected():
    """10_001 is in the window `10000 < amt <= 500000` → rejected (None)."""
    txn = {**TXN_CC, "description": "GENERIC", "amount_paise": 10_001}
    assert detect_cc_payment(txn, None) is None


def test_window_upper_boundary_500000_rejected():
    """Amount 500_000 is in window (`<= 500000`) → rejected."""
    txn = {**TXN_CC, "description": "GENERIC", "amount_paise": 500_000}
    assert detect_cc_payment(txn, None) is None


def test_window_above_500000_not_rejected():
    """500_001 is outside the window → NOT rejected → unmatched."""
    txn = {**TXN_CC, "description": "GENERIC", "amount_paise": 500_001}
    result = detect_cc_payment(txn, None)
    assert result is not None
    assert result.classification == "credit_card_payment_unmatched"


# ═══════════════════════════════════════════════════════════════════════════════
# A2: Each CC keyword triggers detection
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "keyword_desc",
    [
        "PAYMENT XX1234",  # XX + digits pattern
        "CREDIT CARD PAYMENT",  # "CREDIT CARD" keyword
        "CC PAYMENT REF",  # "CC PAYMENT" keyword
        "CARD PAYMENT 4567",  # "CARD PAYMENT" keyword
        "HDFC CREDIT MONTHLY",  # "HDFC CREDIT" keyword
        "ICICI CREDIT BILL",  # "ICICI CREDIT" keyword
        "AXIS CREDIT MONTHLY",  # "AXIS CREDIT" keyword
        "SBI CARD MONTHLY",  # "SBI CARD" keyword
        "IDFC FIRST BILL",  # "IDFC FIRST"
        "INDUSIND CARD PAY",  # "INDUSIND"
    ],
)
def test_cc_keyword_triggers_detection(keyword_desc):
    """Each keyword in the cc_keywords list must be sufficient to trigger
    the detection gate. Mutating (removing) any keyword from the list
    would break the corresponding test → killable."""
    txn = {**TXN_CC, "description": keyword_desc, "amount_paise": 100_000}
    result = detect_cc_payment(txn, None)
    # Keyword present → gate opens → no statement → unmatched (not None)
    assert result is not None
    assert result.classification == "credit_card_payment_unmatched"


# ═══════════════════════════════════════════════════════════════════════════════
# A17: Payment channel priority order (first-match wins in ordered list)
# ═══════════════════════════════════════════════════════════════════════════════


def test_channel_cred_beats_cheq_spaylater_nobroker():
    assert determine_payment_channel("CRED CHEQ S-PA NOBROKER PAY") == "CRED"


def test_channel_cheq_beats_spaylater():
    assert determine_payment_channel("CHEQ S-PA") == "CHEQ"


def test_channel_spaylater_beats_nobroker():
    assert determine_payment_channel("S-PA NOBROKER") == "SPAYLATER"


def test_channel_nobroker_default():
    assert determine_payment_channel("NOBROKER PAYMENT") == "NOBROKER"


def test_channel_direct_for_unknown():
    assert determine_payment_channel("JUST A PAYMENT") == "DIRECT"


# ═══════════════════════════════════════════════════════════════════════════════
# A18: _convert_to_paise edge cases
# ═══════════════════════════════════════════════════════════════════════════════


def test_convert_to_paise_truncates_float_down():
    """int(12.345 * 100) = int(1234.5) = 1234 (truncation, not rounding)."""
    assert _convert_to_paise(12.345) == 1234


def test_convert_to_paise_empty_string_zero():
    assert _convert_to_paise("") == 0


def test_convert_to_paise_none_zero():
    assert _convert_to_paise(None) == 0


def test_convert_to_paise_comma_string():
    """'1,234.56' → strip commas → 1234.56 * 100 = 123456."""
    assert _convert_to_paise("1,234.56") == 123456


# ═══════════════════════════════════════════════════════════════════════════════
# A8: Overpayment pins remaining at 0
# ═══════════════════════════════════════════════════════════════════════════════


def test_overpayment_fully_paid_zero_remaining():
    """Payment > full due → fully_paid, remaining hardcoded 0.
    Guards against max(0, due-pay) regression producing negative value."""
    txn = {**TXN_CC, "amount_paise": 200_000}
    stmt = {**STATEMENT, "total_amount_due": 100_000, "minimum_amount_due": 50_000}
    result = classify_cc_payment(txn, stmt)
    assert result.lifecycle_state == "fully_paid"
    assert result.remaining_outstanding_paise == 0
    assert result.confidence_bps == 9500


def test_payment_at_due_minus_100_boundary_fully_paid():
    """payment >= due - 100 → fully_paid (the boundary is inclusive)."""
    txn = {**TXN_CC, "amount_paise": 999_900}
    stmt = {**STATEMENT, "total_amount_due": 1_000_000, "minimum_amount_due": 50_000}
    result = classify_cc_payment(txn, stmt)
    assert result.lifecycle_state == "fully_paid"


def test_payment_at_due_minus_101_revolving():
    """payment = due - 101 → NOT fully_paid (boundary exclusive) → revolving
    if >= min_due."""
    txn = {**TXN_CC, "amount_paise": 999_899}
    stmt = {**STATEMENT, "total_amount_due": 1_000_000, "minimum_amount_due": 50_000}
    result = classify_cc_payment(txn, stmt)
    assert result.lifecycle_state == "revolving"
    assert result.remaining_outstanding_paise == 101


# ═══════════════════════════════════════════════════════════════════════════════
# A7: Cross-loan tier interaction (higher priority wins regardless of order)
# ═══════════════════════════════════════════════════════════════════════════════


def test_earlier_loan_lower_tier_loses_to_later_loan_higher_tier():
    """Loan1 first in list matches only by keyword (p60). Loan2 matches by
    amount (p80). Loan2 must win: `80 > 60` replaces."""
    txn = {
        "id": 1,
        "debit": 500_000,
        "date_iso": "2026-08-01",
        "description": "EMI PAYMENT",
    }
    loans = [
        {
            "id": 1,
            "emi_paise": 1_000_000,
            "lender": "HDFC",
        },  # no amount match, keyword match
        {"id": 2, "emi_paise": 500_000, "lender": "ICICI"},  # amount match → p80
    ]
    result = detect_emi_payment(txn, loans, schedule_lookup={})
    assert result is not None
    assert result.matched_entity_id == 2
    assert result.priority == 80


def test_single_loan_amount_match_wins_over_no_match():
    """Only one loan matches the amount; the other doesn't match at all."""
    txn = {
        "id": 1,
        "debit": 1_000_000,
        "date_iso": "2026-08-01",
        "description": "SOME PAYMENT",
    }
    loans = [
        {"id": 1, "emi_paise": 1_000_000, "lender": "HDFC"},  # amount match
        {"id": 2, "emi_paise": 500_000, "lender": "ICICI"},  # no match
    ]
    result = detect_emi_payment(txn, loans, schedule_lookup={})
    assert result is not None
    assert result.matched_entity_id == 1
    assert result.priority == 80
    assert result.source == "computed"
    assert result.match_reason == "amount_only"


# ═══════════════════════════════════════════════════════════════════════════════
# A6: EMI or-fallback quirk (debit=0 falls through to amount_paise)
# ═══════════════════════════════════════════════════════════════════════════════


def test_emi_debit_zero_uses_amount_paise_fallback():
    """`int(debit or amount_paise or 0)`: debit=0 is falsy → amount_paise
    is used. This is a documented quirk (Category E5 — latent defect).
    The test pins CURRENT behavior so a future fix is intentional."""
    txn = {
        "id": 1,
        "debit": 0,
        "amount_paise": 1_000_000,
        "date_iso": "2026-08-01",
        "description": "MONTHLY EMI",
    }
    loans = [{"id": 1, "emi_paise": 1_000_000, "lender": "HDFC"}]
    result = detect_emi_payment(txn, loans, schedule_lookup={})
    assert result is not None
    assert result.matched_entity_id == 1


def test_emi_debit_zero_amount_zero_returns_none():
    """Both zero → 0 after `or` chain → rejected by `<= 0` guard."""
    txn = {
        "id": 1,
        "debit": 0,
        "amount_paise": 0,
        "date_iso": "2026-08-01",
        "description": "EMI",
    }
    loans = [{"id": 1, "emi_paise": 1_000_000, "lender": "HDFC"}]
    assert detect_emi_payment(txn, loans, schedule_lookup={}) is None


# ═══════════════════════════════════════════════════════════════════════════════
# A10: Fee bps truncation
# ═══════════════════════════════════════════════════════════════════════════════


def test_fee_bps_sub_paise_truncates_to_zero():
    """A 1-paise fee on a 1_000_001 debit → int(1*10000/1_000_001) = int(0.0099...) = 0."""
    assert _calculate_fee_bps(1_000_001, 1_000_000) == 0


def test_fee_bps_300():
    """30_000 paise fee on 1_000_000 debit → 3% → int(30000*10000/1000000) = 300 bps."""
    assert _calculate_fee_bps(1_000_000, 970_000) == 300


def test_fee_bps_299():
    """29_900 paise fee → int(29900*10000/1000000) = int(299.0) = 299 bps."""
    assert _calculate_fee_bps(1_000_000, 970_100) == 299


def test_fee_bps_negative_debit_returns_zero():
    """Non-positive debit → 0 (guard)."""
    assert _calculate_fee_bps(0, 0) == 0
    assert _calculate_fee_bps(-100, 0) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# A11: Hungarian 1e8 exclusion boundary
# ═══════════════════════════════════════════════════════════════════════════════


def test_hungarian_excludes_cost_at_1e8():
    assert _hungarian_inline([[1e8]]) == []


def test_hungarian_includes_cost_just_below_1e8():
    assert _hungarian_inline([[99_999_999.0]]) == [(0, 0)]


def test_hungarian_zero_cost_diagonal():
    result = _hungarian_inline([[0.0, 100.0], [100.0, 0.0]])
    assert sorted(result) == [(0, 0), (1, 1)]


def test_hungarian_empty_matrix():
    assert _hungarian_inline([]) == []


# ═══════════════════════════════════════════════════════════════════════════════
# A16: Card number extraction edge cases
# ═══════════════════════════════════════════════════════════════════════════════


def test_card_extract_rejects_standalone_when_desc_starts_20xx():
    """Description starting '20xx' (year-like) → standalone 4-digit rejection."""
    assert extract_card_last4("2025 CARD 1234") is None


def test_card_extract_xx_beats_masked():
    """XX1234 has priority over ****4321 when both present."""
    assert extract_card_last4("XX1234 ****4321") == "1234"


def test_card_extract_first_standalone_wins():
    """Multiple standalone 4-digit references → first one."""
    assert extract_card_last4("TXN 1111 2222") == "1111"


def test_card_extract_masked_format():
    assert extract_card_last4("CARD ****4321") == "4321"


# ═══════════════════════════════════════════════════════════════════════════════
# A20: Tolerance truncation for non-round EMIs
# ═══════════════════════════════════════════════════════════════════════════════


def test_tolerance_truncation_non_round_emi():
    """int(101_001 * 0.01) = int(1010.01) = 1010 (truncation).
    ±1010 → within; ±1011 → outside."""
    assert _amount_within_tolerance(101_001 + 1010, 101_001) is True
    assert _amount_within_tolerance(101_001 - 1010, 101_001) is True
    assert _amount_within_tolerance(101_001 + 1011, 101_001) is False
    assert _amount_within_tolerance(101_001 - 1011, 101_001) is False


def test_tolerance_exact_emi_matches():
    assert _amount_within_tolerance(500_000, 500_000) is True


def test_tolerance_zero_expected_rejected():
    """expected == 0 → always False (guard against divide-by-zero)."""
    assert _amount_within_tolerance(1_000_000, 0) is False


# ═══════════════════════════════════════════════════════════════════════════════
# A4: Each liquidity keyword triggers unknown-provider path
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "keyword",
    ["CRED", "CHEQ", "SPAID", "NOBROKER", "LIQUIDITY", "CASH"],
)
def test_liquidity_keyword_triggers_unknown_provider_path(keyword):
    """Each keyword in the liquidity_keywords list must be sufficient to
    pass the unknown-provider gate (no provider pattern matches)."""
    txn = {
        "id": 1,
        "description": keyword,
        "debit": 100_000,
        "date_iso": "2026-08-01",
        "household_id": 7,
    }
    credits = [_credit(amount=50_000)]
    result = detect(txn, credits, [], PURPOSES)
    assert result is not None
    assert result.zone == "unmatched_provider"
    assert result.confidence_bps == 5000


# ═══════════════════════════════════════════════════════════════════════════════
# A5: Unknown-provider path has no date window filter (Category E6 documented)
# ═══════════════════════════════════════════════════════════════════════════════


def test_unknown_provider_allows_large_settlement_gap():
    """The unknown-provider path does NOT enforce [0, settlement+2] window.
    A credit 365 days after debit is still eligible. Documents current
    behavior (potential defect E6 — intentional if intended, bug if not)."""
    txn = {
        "id": 1,
        "description": "CASH TRANSFER",
        "debit": 100_000,
        "date_iso": "2026-08-01",
        "household_id": 7,
    }
    # Credit 365 days later — would be rejected by known-provider window
    credits = [_credit(txn_id=99, amount=50_000, date="2027-07-31", household=7)]
    result = detect(txn, credits, [], PURPOSES)
    assert result is not None
    assert result.zone == "unmatched_provider"
    assert result.settlement_days > 360


# ═══════════════════════════════════════════════════════════════════════════════
# A22: Disambiguation tie-break (min() stability → first in list wins)
# ═══════════════════════════════════════════════════════════════════════════════


def test_cash_disambiguation_first_credit_on_fee_tie():
    """Two credits with identical fee_bps → min() picks first in list.
    This locks the tie-break behavior (depends on input order)."""
    txn = {
        "id": 1,
        "description": "CRED PAYMENT",
        "debit": 100_000,
        "date_iso": "2026-08-01",
        "household_id": 7,
    }
    # Both credits produce identical fee → 10_000 paise = 1000 bps
    # But 1000 bps is outside auto (100-300) AND review (301-500) ranges
    # → both get zone=None → both discarded → None
    # Let me use a fee that IS in range: fee = 1500 paise → 150 bps (auto)
    credits = [
        _credit(txn_id=1, amount=98_500),  # fee=1500, bps=1500 → outside
        _credit(txn_id=2, amount=98_500),  # same
    ]
    # 1500 paise on 100_000 debit → int(1500*10000/100_000) = 150 bps → in auto range
    # Both same → first (id=1) wins
    result = detect(txn, credits, [PROVIDER_CRED], PURPOSES)
    assert result is not None
    assert result.matched_credit_transaction_id == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
