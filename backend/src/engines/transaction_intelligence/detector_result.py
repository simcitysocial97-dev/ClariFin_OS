"""Transaction Intelligence Detector Result Types.

Common result types for all transaction detectors.
"""
from dataclasses import dataclass
from typing import Literal

SourceType = Literal["computed"] | Literal["bank_statement"] | Literal["user_confirmed"]


@dataclass(frozen=True)
class DetectionResult:
    """Base detection result returned by all transaction detectors.

    Attributes:
        classification: The classification label (e.g., 'liability_payment').
        sub_classification: More specific classification (e.g., 'emi', 'credit_card_payment').
        priority: Detector priority for ordering (higher = more confident).
        confidence_bps: Confidence score in basis points (0-10000).
        source: Source of the detection ('computed', 'bank_statement', 'user_confirmed').
        match_reason: Why this matched (e.g., 'amount_match', 'amount+date', 'description+date').
        matched_entity_id: ID of the matched entity (loan_id, card_id, etc.).
    """
    classification: str
    sub_classification: str
    priority: int  # 60-100 scale
    confidence_bps: int
    source: SourceType
    match_reason: str
    matched_entity_id: int


@dataclass(frozen=True)
class EMIDetectionResult(DetectionResult):
    """EMI-specific detection result with schedule details."""
    schedule_row_id: int | None  # Points to loan_amortization_schedule row
    principal_paise: int
    interest_paise: int
    outstanding_after_paise: int
