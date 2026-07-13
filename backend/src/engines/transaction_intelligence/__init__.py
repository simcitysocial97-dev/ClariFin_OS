"""Transaction Intelligence Engine.

Pure detectors for classifying transactions based on patterns.
Supports EMI detection, credit card payments, cash conversions, etc.
"""
from src.engines.transaction_intelligence.detector_result import DetectionResult, EMIDetectionResult
from src.engines.transaction_intelligence.loan_emi_detector import (
    detect_emi_payment,
    find_loan_candidates_for_account,
)

__all__ = [
    "DetectionResult",
    "EMIDetectionResult",
    "detect_emi_payment",
    "find_loan_candidates_for_account",
]
