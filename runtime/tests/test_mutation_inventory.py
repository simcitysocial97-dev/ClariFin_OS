# runtime/tests/test_mutation_inventory.py
#
# M9-C42.17 — Unit tests for the permanent survivor-inventory classifier.
#
# These verify the CLASSIFICATION LOGIC (pure, no subprocess) so the forensic
# inventory remains reviewable and regression-safe. They never invoke mutmut.
from __future__ import annotations

from runtime.foundation.verification.mutation_inventory import (
    A_REAL_GAP,
    B_EQUIVALENT,
    E_UNKNOWN,
    Classification,
    classify,
    infer_operator,
    parse_counts,
)


def test_message_only_mutation_is_equivalent():
    c = classify(
        '        raise ValueError("outstanding_paise must be non-negative")',
        '        raise ValueError(None)',
    )
    assert isinstance(c, Classification)
    assert c.classification == B_EQUIVALENT
    assert c.subclass == "equivalent_message"


def test_rounding_half_even_removed_is_equivalent():
    c = classify(
        "util.quantize(Decimal(1), rounding=ROUND_HALF_EVEN)",
        "util.quantize(Decimal(1))",
    )
    assert c.classification == B_EQUIVALENT
    assert c.subclass == "equivalent_rounding_default"


def test_rounding_half_up_removed_is_real_gap():
    # ROUND_HALF_UP is NOT Decimal's default -> removing it changes behavior.
    c = classify(
        'return int(x.quantize(Decimal("1"), rounding=ROUND_HALF_UP))',
        'return int(x.quantize(Decimal("1"), rounding=None))',
    )
    assert c.classification == A_REAL_GAP
    assert c.subclass == "real_gap_rounding_precision"


def test_decimal_precision_change_is_real_gap():
    c = classify(
        "Decimal(outstanding) * Decimal(10000) / Decimal(credit_limit)",
        "Decimal(outstanding) * Decimal(10001) / Decimal(credit_limit)",
    )
    assert c.classification == A_REAL_GAP
    assert c.subclass == "real_gap_rounding_precision"


def test_comparison_mutation_is_real_gap():
    c = classify("if a == 0 or b == 0:", "if a == 0 and b == 0:")
    assert c.classification == A_REAL_GAP
    assert c.subclass == "real_gap_comparison"


def test_none_replacement_is_real_gap_constant():
    c = classify("        months_paid=0,", "        months_paid=None,")
    assert c.classification == A_REAL_GAP
    assert c.subclass == "real_gap_constant"


def test_dict_key_mutation_is_real_gap():
    c = classify('            "outstanding_paise": 0,', '            "XXoutstanding_paiseXX": 0,')
    assert c.classification == A_REAL_GAP
    assert c.subclass == "real_gap_dict_key"


def test_numeric_default_mutation_is_real_gap():
    c = classify("    penalty_bps: int = 0,", "    penalty_bps: int = 1,")
    assert c.classification == A_REAL_GAP
    assert c.subclass == "real_gap_numeric_default"


def test_unknown_falls_through():
    c = classify("    pass", "    pass")
    assert c.classification == E_UNKNOWN


def test_infer_operator_message():
    assert infer_operator('raise ValueError("x")', 'raise ValueError("y")') == (
        "exception_message_string_mutation"
    )


def test_parse_counts_totals():
    results = {"a": "killed", "b": "survived", "c": "survived", "d": "no tests"}
    counts = parse_counts(results)
    assert counts["killed"] == 1
    assert counts["survived"] == 2
    assert counts["no_tests"] == 1
