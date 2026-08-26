"""Smoke tests for Transaction Intelligence capability.

M9-C42.25: extended with direct engine wiring so the capability registry
discovery (engine_imports) binds this test domain to the
transaction_intelligence engine. Original smoke tests preserved.
"""

from __future__ import annotations

from src.engines.transaction_intelligence import (
    DetectionResult,
    EMIDetectionResult,
    detect_cash_conversion,
    detect_emi_payment,
    find_loan_candidates_for_account,
)
from src.engines.transaction_intelligence.cc_payment_detector import (
    classify_cc_payment,
    detect_cc_payment,
)

from tests.golden.builders.normal_household import load_normal_household


class TestTransactionIntelligenceCapability:
    """Validate Transaction Intelligence capability wiring."""

    def test_import_transaction_intelligence_engine(self) -> None:
        """Transaction intelligence engine must be importable."""
        from src.engines import transaction_intelligence

        assert transaction_intelligence is not None

    def test_golden_dataset_transaction_scenario(self) -> None:
        """Golden dataset must load and validate."""
        data = load_normal_household()
        assert "transactions" in data

    def test_public_api_exports(self) -> None:
        """Package-level API must expose the detector contracts."""
        assert DetectionResult is not None
        assert EMIDetectionResult is not None
        assert callable(detect_cash_conversion)
        assert callable(detect_emi_payment)
        assert callable(find_loan_candidates_for_account)

    def test_emi_detection_capability_wiring(self) -> None:
        """EMI detector must classify a schedule-backed payment end to end."""
        result = detect_emi_payment(
            {"id": 1, "debit": 1_000_000, "date_iso": "2026-08-01", "description": "EMI"},
            [{"id": 5, "emi_paise": 1_000_000, "next_emi_date": None}],
            {},
        )
        assert result is not None
        assert result.classification == "liability_payment"
        assert result.sub_classification == "emi"
        assert 0 <= result.confidence_bps <= 10000

    def test_cash_conversion_detection_capability_wiring(self) -> None:
        """Cash conversion detector must classify a provider-matched debit."""
        provider = {
            "provider_name": "CRED",
            "description_pattern": "CRED",
            "typical_settlement_days": 2,
            "fee_min_bps": 100,
            "fee_max_bps": 300,
            "review_fee_min_bps": 301,
            "review_fee_max_bps": 500,
        }
        result = detect_cash_conversion(
            {
                "id": 1,
                "description": "CRED CASH",
                "debit": 1_000_000,
                "date_iso": "2026-08-01",
                "household_id": 7,
            },
            [
                {
                    "id": 11,
                    "account_id": 101,
                    "account_type": "savings",
                    "household_id": 7,
                    "credit": 975_000,
                    "date_iso": "2026-08-02",
                }
            ],
            [provider],
            [],
        )
        assert result is not None
        assert result.zone == "auto"
        assert 0 <= result.confidence_bps <= 9900

    def test_cc_payment_detection_capability_wiring(self) -> None:
        """CC payment detector must classify a fully paid statement."""
        txn = {"id": 1, "description": "XX1234 PAYMENT", "amount_paise": 100_000}
        statement = {"id": 9, "total_amount_due": 100_000, "minimum_amount_due": 5_000}
        detected = detect_cc_payment(txn, statement)
        assert detected is not None
        classified = classify_cc_payment(txn, statement)
        assert classified.lifecycle_state == "fully_paid"
        assert classified.remaining_outstanding_paise == 0

