"""Direct unit tests for src/engines/transaction_intelligence/detector_result.py.

M9-C42.25 — establishes direct behavioral ownership of the shared detection
result contracts (frozen dataclasses, field semantics, inheritance).
"""

from dataclasses import FrozenInstanceError

import pytest
from src.engines.transaction_intelligence.detector_result import (
    DetectionResult,
    EMIDetectionResult,
)


def _base_result(**overrides):
    fields = {
        "classification": "liability_payment",
        "sub_classification": "emi",
        "priority": 90,
        "confidence_bps": 9000,
        "source": "computed",
        "match_reason": "amount_match",
        "matched_entity_id": 7,
    }
    fields.update(overrides)
    return DetectionResult(**fields)


def test_detection_result_construction():
    result = _base_result()
    assert result.classification == "liability_payment"
    assert result.sub_classification == "emi"
    assert result.priority == 90
    assert result.confidence_bps == 9000
    assert result.source == "computed"
    assert result.match_reason == "amount_match"
    assert result.matched_entity_id == 7


def test_detection_result_is_frozen():
    result = _base_result()
    with pytest.raises(FrozenInstanceError):
        result.priority = 60


def test_detection_result_equality_is_value_based():
    assert _base_result() == _base_result()
    assert _base_result(priority=80) != _base_result(priority=90)


@pytest.mark.parametrize("source", ["computed", "bank_statement", "user_confirmed"])
def test_detection_result_accepts_all_source_types(source):
    assert _base_result(source=source).source == source


def test_emi_detection_result_extends_base():
    result = EMIDetectionResult(
        classification="liability_payment",
        sub_classification="emi",
        priority=100,
        confidence_bps=8000,
        source="bank_statement",
        match_reason="bank_statement_override",
        matched_entity_id=3,
        schedule_row_id=42,
        principal_paise=600000,
        interest_paise=400000,
        outstanding_after_paise=9000000,
    )
    assert isinstance(result, DetectionResult)
    assert result.schedule_row_id == 42
    assert result.principal_paise == 600000
    assert result.interest_paise == 400000
    assert result.outstanding_after_paise == 9000000


def test_emi_detection_result_allows_null_schedule_row():
    result = EMIDetectionResult(
        classification="liability_payment",
        sub_classification="emi",
        priority=80,
        confidence_bps=7500,
        source="computed",
        match_reason="amount_only",
        matched_entity_id=1,
        schedule_row_id=None,
        principal_paise=0,
        interest_paise=0,
        outstanding_after_paise=1000000,
    )
    assert result.schedule_row_id is None


def test_emi_detection_result_is_frozen():
    result = EMIDetectionResult(
        classification="liability_payment",
        sub_classification="emi",
        priority=90,
        confidence_bps=9000,
        source="computed",
        match_reason="amount_match",
        matched_entity_id=1,
        schedule_row_id=1,
        principal_paise=1,
        interest_paise=1,
        outstanding_after_paise=1,
    )
    with pytest.raises(FrozenInstanceError):
        result.principal_paise = 0
