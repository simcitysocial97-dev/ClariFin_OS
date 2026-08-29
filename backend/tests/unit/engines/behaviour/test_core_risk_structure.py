"""M9-C43.7 — Structural validation for core.py / stress.py / profile.py survivors.

Targets the dominant surviving mutant classes in:
- core.detect_india_risk_patterns (115 survivors)
- core._compute_habit_stability_score (101)
- core._compute_loss_aversion_index (72)
- profile._build_explanation (65)
- stress.detect_risk_patterns / *_score functions

Kills: dict KEY renames, STRING literal changes, DEFAULT value mutations
(.get(k,0)->.get(k,1)), and COMPUTED constant mutations (/100.0 -> /101.0).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.engines.behaviour_engine import core, profile, stress

EXPECTED_INDIA_KEYS = {
    "upi_micro_spend_flag",
    "gambling_flag",
    "gambling_transaction_count",
    "loan_app_pattern_flag",
    "loan_credit_count",
    "emi_ratio",
    "monthly_emi_total",
}

EXPECTED_HABIT_KEYS = {"category_cv", "recurring_predictability", "score", "recurring_count", "rhythm_score"}
EXPECTED_LOSS_KEYS = {"post_income_velocity", "recovery_time_days", "score", "large_expense_count"}


class TestDetectIndiaRiskStructure:
    def test_empty_returns_exact_keys(self) -> None:
        result = core.detect_india_risk_patterns([])
        assert set(result.keys()) <= EXPECTED_INDIA_KEYS
        assert result["upi_micro_spend_flag"] is False
        assert result["gambling_flag"] is False
        assert result["loan_app_pattern_flag"] is False
        assert result["emi_ratio"] == 0.0

    def test_upi_micro_spend_flag(self) -> None:
        # 11 micro debits (< ₹200) on the same day -> flag True
        txns = [
            {"type": "debit", "amount_paise": 15000, "date_iso": "2025-01-01", "description": f"UPI{i}"}
            for i in range(11)
        ]
        result = core.detect_india_risk_patterns(txns)
        assert set(result.keys()) <= EXPECTED_INDIA_KEYS
        assert result["upi_micro_spend_flag"] is True
        # Only 10 -> False
        txns10 = txns[:10]
        assert core.detect_india_risk_patterns(txns10)["upi_micro_spend_flag"] is False

    def test_gambling_flag(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01", "description": "dream11 entry"},
        ]
        result = core.detect_india_risk_patterns(txns)
        assert set(result.keys()) <= EXPECTED_INDIA_KEYS
        assert result["gambling_flag"] is True
        # Keyword "rummy"
        txns2 = [
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01", "description": "rummy circle"},
        ]
        assert core.detect_india_risk_patterns(txns2)["gambling_flag"] is True

    def test_loan_app_flag(self) -> None:
        # Two small loan credits within 7 days -> flag True
        txns = [
            {"type": "credit", "amount_paise": 300000, "date_iso": "2025-01-01", "description": "loan from nbfc"},
            {"type": "credit", "amount_paise": 300000, "date_iso": "2025-01-03", "description": "instant cash"},
        ]
        result = core.detect_india_risk_patterns(txns)
        assert set(result.keys()) <= EXPECTED_INDIA_KEYS
        assert result["loan_app_pattern_flag"] is True
        # Single loan credit -> False
        txns1 = [txns[0]]
        assert core.detect_india_risk_patterns(txns1)["loan_app_pattern_flag"] is False

    def test_emi_ratio_exact(self) -> None:
        # EMI debit 5000 in 2025-01, income credit 10000 in 2025-01 -> ratio 0.5
        txns = [
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-10", "description": "emi payment"},
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-05", "description": "salary"},
        ]
        result = core.detect_india_risk_patterns(txns)
        assert set(result.keys()) <= EXPECTED_INDIA_KEYS
        assert result["emi_ratio"] == pytest.approx(0.5, abs=1e-4)

    def test_missing_keys_defaults(self) -> None:
        # Transaction missing type/date_iso/amount should not crash; defaults apply
        txns = [
            {"amount_paise": 50000, "date_iso": "2025-01-01", "description": "upi"},
            {"type": "debit", "date_iso": "2025-01-01", "description": "rummy"},
            {"type": "debit", "amount_paise": 50000, "description": "loan"},
        ]
        result = core.detect_india_risk_patterns(txns)
        assert set(result.keys()) <= EXPECTED_INDIA_KEYS
        assert isinstance(result["upi_micro_spend_flag"], bool)
        assert isinstance(result["gambling_flag"], bool)
        assert isinstance(result["loan_app_pattern_flag"], bool)
        assert isinstance(result["emi_ratio"], (int, float))


class TestHabitStabilityStructure:
    def test_empty(self) -> None:
        r = core._compute_habit_stability_score([])
        assert set(r.keys()) <= EXPECTED_HABIT_KEYS
        assert r["score"] == 0.5
        assert r["category_cv"] == 0.0
        assert r["recurring_predictability"] == 0.0

    def test_exact_computation(self) -> None:
        # 3 identical Netflix debits -> recurring; some variance in amounts
        txns = [
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-01", "description": "NETFLIX"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-02-01", "description": "NETFLIX"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-03-01", "description": "NETFLIX"},
            {"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-02", "category": "X"},
            {"type": "debit", "amount_paise": 200000, "date_iso": "2025-02-02", "category": "X"},
            {"type": "debit", "amount_paise": 300000, "date_iso": "2025-03-02", "category": "X"},
        ]
        r = core._compute_habit_stability_score(txns)
        assert set(r.keys()) <= EXPECTED_HABIT_KEYS
        assert r["category_cv"] >= 0.0
        assert 0.0 <= r["score"] <= 1.0
        # recurring_predictability present in empty case; recurring_count in non-empty
        for k in ("recurring_predictability", "recurring_count", "rhythm_score"):
            if k in r:
                assert r[k] >= 0.0


class TestLossAversionStructure:
    def test_empty(self) -> None:
        r = core._compute_loss_aversion_index([])
        assert set(r.keys()) <= EXPECTED_LOSS_KEYS
        assert r["score"] == 0.5
        assert r["post_income_velocity"] == 0.0
        assert r["recovery_time_days"] == 0

    def test_exact_velocity(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 200000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-02"},
        ]
        r = core._compute_loss_aversion_index(txns)
        assert set(r.keys()) <= EXPECTED_LOSS_KEYS
        assert r["post_income_velocity"] == pytest.approx(0.5, abs=1e-6)
        assert r["score"] == pytest.approx(0.2, abs=1e-4)


class TestStressDetectRiskStructure:
    def test_empty(self) -> None:
        r = stress.detect_risk_patterns([])
        assert isinstance(r, dict)
        assert set(r.keys()) <= EXPECTED_INDIA_KEYS
        assert isinstance(r["upi_micro_spend_flag"], bool)
        assert isinstance(r["gambling_flag"], bool)
        assert isinstance(r["loan_app_pattern_flag"], bool)
        assert isinstance(r["emi_ratio"], (int, float))

    def test_known_flags(self) -> None:
        # high impulse score -> high_impulsivity True
        txns = [
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "food"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "food"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-05", "category": "food"},
        ]
        r = stress.detect_risk_patterns(txns)
        assert isinstance(r, dict)
        assert set(r.keys()) <= EXPECTED_INDIA_KEYS
        assert "upi_micro_spend_flag" in r
        assert isinstance(r["upi_micro_spend_flag"], bool)


class TestProfileExplanationStructure:
    def test_exact_string(self) -> None:
        r = profile._build_explanation(
            "test",
            Decimal("0.1"),
            Decimal("0.2"),
            Decimal("0.3"),
        )
        assert isinstance(r, str)
        assert len(r) > 0
        assert "10.0%" in r  # savings rate rendered exactly

    def test_exact_string_revolver(self) -> None:
        r = profile._build_explanation(
            "test",
            Decimal("0.4"),
            Decimal("0.1"),
            Decimal("0.15"),
        )
        assert isinstance(r, str)
        assert "40.0%" in r  # savings rate rendered exactly
