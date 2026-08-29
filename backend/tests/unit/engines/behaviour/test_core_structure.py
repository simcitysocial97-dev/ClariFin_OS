"""M9-C43.7 — Structural validation for core.py score/profile functions.

Targets the dominant surviving mutant classes in:
- core._compute_financial_stress_index (61 survivors)
- core._compute_savings_discipline_score (56)
- core._compute_impulsivity_score (56)
- core._compute_temporal_patterns (57)
- core.compute_behavior_profile (59)
- core._compute_loss_aversion_index / _compute_habit_stability_score (covered in test_core_risk_structure)

Kills: dict KEY renames, STRING literal changes, DEFAULT value mutations, and
COMPUTED constant mutations.
"""

from __future__ import annotations

import pytest
from src.engines.behaviour_engine import core

FSTRESS_KEYS = {"score", "balance_volatility", "credit_dependency", "eom_depletion_ratio", "buffer_days"}
SAV_KEYS = {"score", "savings_rate", "momentum", "consistency", "positive_savings_months"}
IMP_KEYS = {"score", "micro_txn_ratio", "late_night_ratio", "weekend_ratio", "discretionary_ratio", "micro_txn_count"}
TEMPORAL_KEYS = {
    "trend",
    "seasonality",
    "residual_volatility",
    "coefficient_of_variation",
    "daily_spending",
    "weekly_pattern",
}


class TestCoreFinancialStressStructure:
    def test_empty(self) -> None:
        r = core._compute_financial_stress_index([])
        assert set(r.keys()) <= FSTRESS_KEYS
        assert r["score"] == 0.5
        assert r["balance_volatility"] == 0.0
        assert r["credit_dependency"] == 0.0

    def test_exact(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
        ]
        r = core._compute_financial_stress_index(txns)
        assert set(r.keys()) <= FSTRESS_KEYS
        assert r["balance_volatility"] == pytest.approx(0.0, abs=1e-6)
        assert r["credit_dependency"] == pytest.approx(2.0, abs=1e-6)
        assert r["buffer_days"] == pytest.approx(1.0, abs=1e-6)
        assert r["score"] == pytest.approx(0.4933, abs=1e-4)

    def test_missing_keys(self) -> None:
        txns = [{"type": "debit", "amount_paise": 50000}]
        r = core._compute_financial_stress_index(txns)
        assert set(r.keys()) <= FSTRESS_KEYS
        assert isinstance(r["score"], float)


class TestCoreSavingsDisciplineStructure:
    def test_empty(self) -> None:
        r = core._compute_savings_discipline_score([])
        assert set(r.keys()) <= SAV_KEYS
        assert r["score"] == 0.5
        assert r["savings_rate"] == 0.0
        assert r["momentum"] == 0.0

    def test_exact(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 80000, "date_iso": "2025-01-15"},
        ]
        r = core._compute_savings_discipline_score(txns)
        assert set(r.keys()) <= SAV_KEYS
        assert r["savings_rate"] == pytest.approx(0.2, abs=1e-6)
        assert r["momentum"] == 0
        assert r["consistency"] == 1.0
        assert r["positive_savings_months"] == 1
        assert r["score"] == pytest.approx(0.73, abs=1e-3)

    def test_missing_keys(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000}]
        r = core._compute_savings_discipline_score(txns)
        assert set(r.keys()) <= SAV_KEYS
        assert isinstance(r["score"], float)


class TestCoreImpulsivityStructure:
    def test_empty(self) -> None:
        r = core._compute_impulsivity_score([])
        assert set(r.keys()) <= IMP_KEYS
        assert r["score"] == 0.5
        assert r["micro_txn_ratio"] == 0.0
        assert r["late_night_ratio"] == 0.0

    def test_all_micro_weekend(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-05", "category": "Food & Dining"},
        ]
        r = core._compute_impulsivity_score(txns)
        assert set(r.keys()) <= IMP_KEYS
        assert r["micro_txn_ratio"] == pytest.approx(1.0, abs=1e-6)
        assert r["weekend_ratio"] == pytest.approx(1.0, abs=1e-6)
        assert r["discretionary_ratio"] == pytest.approx(1.0, abs=1e-6)
        assert r["micro_txn_count"] == 3
        assert r["score"] == pytest.approx(0.7667, abs=1e-3)

    def test_missing_keys(self) -> None:
        txns = [{"type": "debit", "amount_paise": 30000}]
        r = core._compute_impulsivity_score(txns)
        assert set(r.keys()) <= IMP_KEYS
        assert isinstance(r["score"], float)


class TestCoreTemporalPatternsStructure:
    def test_empty(self) -> None:
        r = core._compute_temporal_patterns([])
        assert set(r.keys()) <= TEMPORAL_KEYS
        for k in TEMPORAL_KEYS:
            if k in r:
                assert isinstance(r[k], (int, float, dict))

    def test_exact(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-02"},
            {"type": "debit", "amount_paise": 70000, "date_iso": "2025-01-03"},
        ]
        r = core._compute_temporal_patterns(txns)
        assert set(r.keys()) <= TEMPORAL_KEYS
        assert isinstance(r["daily_spending"], dict)
        assert isinstance(r["weekly_pattern"], dict)
        assert r["daily_spending"]["2025-01-01"] == 50000.0
        assert r["trend"] == pytest.approx(0.0, abs=1e-6)
        for k in ("seasonality", "residual_volatility", "coefficient_of_variation"):
            assert isinstance(r[k], float)


class TestComputeBehaviorProfileStructure:
    def test_empty(self) -> None:
        profile = core.compute_behavior_profile([])
        assert set(profile.keys()) == {
            "temporal_patterns",
            "behavioral_indices",
            "risk_signals",
            "confidence",
            "financial_health_score",
            "data_quality",
        }
        assert profile["confidence"] == 0.0
        assert isinstance(profile["behavioral_indices"], dict)
        assert isinstance(profile["risk_signals"], dict)

    def test_keys_present(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01", "category": "Salary"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining", "description": "X"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining", "description": "X"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
        ]
        profile = core.compute_behavior_profile(txns)
        # top-level keys + nested key names are exactly as declared
        assert set(profile["temporal_patterns"].keys()) == {
            "trend", "seasonality", "volatility", "weekly_pattern",
        }
        assert set(profile["behavioral_indices"].keys()) == {
            "loss_aversion", "impulsivity", "habit_stability",
            "financial_stress", "savings_discipline",
        }
        assert set(profile["risk_signals"].keys()) == {
            "india_specific", "high_impulsivity", "high_stress", "low_savings",
        }
        assert "confidence" in profile
        assert "financial_health_score" in profile
        assert "data_quality" in profile
