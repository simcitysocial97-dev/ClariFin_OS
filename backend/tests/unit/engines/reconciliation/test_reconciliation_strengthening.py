"""Behavioral strengthening tests for reconciliation_engine (M9-C42.23 Batch 5).

Targets the pure scoring helpers whose threshold/arithmetic mutants survived the
C42.21 baseline: confidence weights, the >0.7 description-similarity boundary, the
date-difference tiers (exact=+0.4, within-1-day=+0.3), the 1.0 cap, and the
description-keyword similarity rule.
"""

from __future__ import annotations

from src.engines.reconciliation_engine import (
    _calculate_confidence,
    _simple_description_similarity,
)


def test_confidence_exact_date_and_exact_amount() -> None:
    assert _calculate_confidence(0, True, 0.0) == 0.8


def test_confidence_within_one_day_and_exact_amount() -> None:
    assert _calculate_confidence(1, True, 0.0) == 0.7


def test_confidence_capped_at_one_with_similarity() -> None:
    # 0.4 (date) + 0.4 (amount) + 0.2 (similarity) = 1.0, capped
    assert _calculate_confidence(0, True, 0.8) == 1.0


def test_confidence_similarity_boundary_exactly_0_7_excluded() -> None:
    """Similarity == 0.7 is NOT strictly > 0.7, so no +0.2 bonus."""
    assert _calculate_confidence(0, True, 0.7) == 0.8


def test_confidence_similarity_above_0_7_included() -> None:
    assert _calculate_confidence(0, True, 0.71) == 1.0


def test_confidence_date_diff_two_has_no_date_factor() -> None:
    # date diff 2 -> no date bonus; only exact amount contributes
    assert _calculate_confidence(2, True, 0.0) == 0.4


def test_confidence_amount_not_exact() -> None:
    assert _calculate_confidence(0, False, 0.0) == 0.4
    assert _calculate_confidence(1, False, 0.0) == 0.3


def test_simple_description_similarity_keywords_both() -> None:
    assert _simple_description_similarity("neft transfer", "imps transfer") == 1.0


def test_simple_description_similarity_no_keywords() -> None:
    assert _simple_description_similarity("grocery", "grocery") == 0.0


def test_simple_description_similarity_empty() -> None:
    assert _simple_description_similarity("", "transfer") == 0.0
