"""Direct unit tests for src/engines/transaction_intelligence/cc_payment_detector.py.

M9-C42.25 — direct behavioral ownership of credit-card payment detection:
card-number extraction, channel classification, paise conversion, lifecycle
classification boundaries, and the detection gate.

Anomaly TXN-C2 (see C42.25 inventory): inside the no-keyword/no-pattern gate
the `and not has_card_pattern` guard is tautological; behavior pinned as-is.
"""

from src.engines.transaction_intelligence.cc_payment_detector import (
    _convert_to_paise,
    classify_cc_payment,
    detect_cc_payment,
    determine_payment_channel,
    extract_card_last4,
)

# ============================================================
# extract_card_last4
# ============================================================


def test_extract_card_last4_xx_format():
    assert extract_card_last4("PAYMENT TO XX1234") == "1234"


def test_extract_card_last4_masked_format():
    assert extract_card_last4("CARD ****4321 PAYMENT") == "4321"


def test_extract_card_last4_standalone_digits():
    assert extract_card_last4("TXN 5678 DONE") == "5678"


def test_extract_card_last4_xx_takes_precedence_over_digits():
    assert extract_card_last4("XX1234 9999") == "1234"


def test_extract_card_last4_year_prefix_excluded():
    # Descriptions beginning with a 20xx year are not card references.
    assert extract_card_last4("2025") is None


def test_extract_card_last4_no_pattern():
    assert extract_card_last4("GROCERY STORE") is None
    assert extract_card_last4("") is None


def test_extract_card_last4_long_digit_run_not_matched():
    assert extract_card_last4("REF 123456 END") is None


# ============================================================
# determine_payment_channel
# ============================================================


def test_determine_payment_channel_cred():
    assert determine_payment_channel("CRED PAY") == "CRED"


def test_determine_payment_channel_credit_card_is_direct():
    assert determine_payment_channel("CREDIT CARD PAYMENT") == "DIRECT"


def test_determine_payment_channel_cheq():
    assert determine_payment_channel("CHEQ TRANSFER") == "CHEQ"


def test_determine_payment_channel_chequebook():
    assert determine_payment_channel("CHEQUEBOOK ENTRY") == "CHEQ"


def test_determine_payment_channel_spaylater():
    assert determine_payment_channel("SPAYLATER TXN") == "SPAYLATER"


def test_determine_payment_channel_s_pa_variant():
    assert determine_payment_channel("S-PA INSTALLMENT") == "SPAYLATER"


def test_determine_payment_channel_nobroker():
    assert determine_payment_channel("NOBROKER RENT") == "NOBROKER"


def test_determine_payment_channel_default_direct():
    assert determine_payment_channel("NEFT TRANSFER") == "DIRECT"


def test_determine_payment_channel_case_insensitive():
    assert determine_payment_channel("cred pay") == "CRED"


# ============================================================
# _convert_to_paise
# ============================================================


def test_convert_to_paise_int_passthrough():
    assert _convert_to_paise(12345) == 12345


def test_convert_to_paise_none():
    assert _convert_to_paise(None) == 0


def test_convert_to_paise_float_rupees():
    assert _convert_to_paise(12.5) == 1250


def test_convert_to_paise_string_with_comma_and_decimal():
    assert _convert_to_paise("1,234.50") == 123450


def test_convert_to_paise_integer_string_is_paise():
    assert _convert_to_paise("12345") == 12345


def test_convert_to_paise_invalid_string():
    assert _convert_to_paise("abc") == 0


def test_convert_to_paise_unsupported_type():
    assert _convert_to_paise([1, 2]) == 0


# ============================================================
# classify_cc_payment
# ============================================================

TXN = {"id": 1, "description": "CC PAYMENT", "amount_paise": 1_000_000, "date_iso": "2026-08-01"}
STATEMENT = {"id": 9, "total_amount_due": 1_000_000, "minimum_amount_due": 50_000}


def test_classify_no_statement_unmatched_unknown():
    result = classify_cc_payment(TXN, None)
    assert result.matched_statement_id is None
    assert result.classification == "credit_card_payment_unmatched"
    assert result.lifecycle_state == "unknown"
    assert result.confidence_bps == 2000
    assert result.payment_amount_paise == 1_000_000
    assert result.statement_amount_paise == 0
    assert result.minimum_due_paise == 0
    assert result.remaining_outstanding_paise == 0
    assert result.match_reason == "no_matching_statement_found"


def test_classify_full_payment():
    result = classify_cc_payment(TXN, STATEMENT)
    assert result.matched_statement_id == 9
    assert result.classification == "credit_card_payment"
    assert result.lifecycle_state == "fully_paid"
    assert result.confidence_bps == 9500
    assert result.remaining_outstanding_paise == 0
    assert result.match_reason == "full_payment_matched"


def test_classify_full_payment_at_tolerance_boundary():
    txn = {**TXN, "amount_paise": 999_900}  # due - 100
    result = classify_cc_payment(txn, STATEMENT)
    assert result.lifecycle_state == "fully_paid"


def test_classify_one_paise_below_tolerance_revolves():
    txn = {**TXN, "amount_paise": 999_899}
    result = classify_cc_payment(txn, STATEMENT)
    assert result.lifecycle_state == "revolving"
    assert result.confidence_bps == 8500
    assert result.remaining_outstanding_paise == 1_000_000 - 999_899


def test_classify_partial_payment_above_minimum():
    txn = {**TXN, "amount_paise": 500_000}
    result = classify_cc_payment(txn, STATEMENT)
    assert result.lifecycle_state == "revolving"
    assert result.remaining_outstanding_paise == 500_000
    assert result.match_reason == "partial_payment_above_minimum"


def test_classify_payment_exactly_at_minimum_due():
    txn = {**TXN, "amount_paise": 50_000}
    result = classify_cc_payment(txn, STATEMENT)
    assert result.lifecycle_state == "revolving"


def test_classify_payment_below_minimum_due():
    txn = {**TXN, "amount_paise": 49_999}
    result = classify_cc_payment(txn, STATEMENT)
    assert result.lifecycle_state == "payment_received"
    assert result.confidence_bps == 7000
    assert result.remaining_outstanding_paise == 1_000_000 - 49_999
    assert result.match_reason == "payment_below_minimum_due"


def test_classify_handles_float_and_string_statement_amounts():
    statement = {"id": 5, "total_amount_due": 10000.5, "minimum_amount_due": "500"}
    txn = {**TXN, "amount_paise": 1_000_050}
    result = classify_cc_payment(txn, statement)
    assert result.statement_amount_paise == 1_000_050
    assert result.minimum_due_paise == 500
    assert result.lifecycle_state == "fully_paid"


def test_classify_missing_amount_fields_default_to_zero():
    statement = {"id": 5}
    txn = {**TXN, "amount_paise": 100}
    result = classify_cc_payment(txn, statement)
    # due = 0 -> payment >= due - 100 -> fully_paid
    assert result.statement_amount_paise == 0
    assert result.lifecycle_state == "fully_paid"


def test_classify_propagates_payment_channel():
    result = classify_cc_payment(TXN, None, payment_channel="CRED")
    assert result.payment_channel == "CRED"


# ============================================================
# detect_cc_payment
# ============================================================


def test_detect_cc_payment_keyword_description():
    txn = {**TXN, "description": "HDFC CREDIT CARD PAYMENT XX1234"}
    result = detect_cc_payment(txn, STATEMENT)
    assert result is not None
    assert result.lifecycle_state == "fully_paid"
    assert result.payment_channel == "DIRECT"


def test_detect_cc_payment_channel_cred():
    txn = {**TXN, "description": "CRED CC PAYMENT"}
    result = detect_cc_payment(txn, None)
    assert result is not None
    assert result.payment_channel == "CRED"
    assert result.lifecycle_state == "unknown"


def test_detect_cc_payment_no_marker_low_amount_no_statement_rejected():
    txn = {**TXN, "description": "GROCERY", "amount_paise": 100_000}
    assert detect_cc_payment(txn, None) is None


def test_detect_cc_payment_no_marker_out_of_amount_range_falls_through():
    txn = {**TXN, "description": "GROCERY", "amount_paise": 600_000}
    result = detect_cc_payment(txn, None)
    assert result is not None
    assert result.classification == "credit_card_payment_unmatched"


def test_detect_cc_payment_no_marker_small_amount_falls_through():
    txn = {**TXN, "description": "GROCERY", "amount_paise": 5_000}
    result = detect_cc_payment(txn, None)
    assert result is not None
    assert result.classification == "credit_card_payment_unmatched"


def test_detect_cc_payment_no_marker_with_statement_classifies():
    txn = {**TXN, "description": "GROCERY", "amount_paise": 100_000}
    result = detect_cc_payment(txn, STATEMENT)
    assert result is not None
    # 100_000 >= minimum_due 50_000 -> revolving
    assert result.lifecycle_state == "revolving"


def test_detect_cc_payment_card_pattern_only():
    txn = {**TXN, "description": "PAYMENT XX4444"}
    result = detect_cc_payment(txn, None)
    assert result is not None
    assert result.classification == "credit_card_payment_unmatched"


def test_detect_cc_payment_missing_description():
    txn = {"id": 1, "amount_paise": 1_000_000}
    result = detect_cc_payment(txn, STATEMENT)
    assert result is not None
    assert result.lifecycle_state == "fully_paid"
