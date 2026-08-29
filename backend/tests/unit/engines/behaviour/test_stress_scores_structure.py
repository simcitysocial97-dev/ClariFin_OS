"""M9-C43.7 — Structural validation for stress.py scoring functions.

Targets the dominant surviving mutant classes in:
- stress.loss_aversion_index (77 survivors)
- stress.impulsivity_score (102)
- stress.habit_stability_score (63)
- stress.financial_stress_index (52)
- stress.savings_discipline_score (67)
- stress.detect_risk_patterns (111, partially covered in test_core_risk_structure)

Kills: dict KEY renames, STRING literal changes, DEFAULT value mutations
(.get(k,0)->.get(k,1)), and COMPUTED constant mutations (/100.0 -> /101.0,
operator swaps in score formulas).
"""

from __future__ import annotations

import pytest

from src.engines.behaviour_engine import stress

# Exact key sets observed from source
LOSS_KEYS = {"score", "post_income_velocity", "recovery_time_days", "large_expense_count"}
IMP_KEYS = {"score", "micro_txn_ratio", "late_night_ratio", "weekend_ratio", "discretionary_ratio", "micro_txn_count"}
HABIT_KEYS = {"score", "category_cv", "recurring_predictability", "recurring_count", "rhythm_score"}
FSTRESS_KEYS = {"score", "balance_volatility", "buffer_days", "credit_dependency", "eom_depletion_ratio"}
SAV_KEYS = {"score", "savings_rate", "momentum", "consistency", "positive_savings_months"}


class TestLossAversionStructure:
    def test_empty(self) -> None:
        r = stress.loss_aversion_index([])
        assert LOSS_KEYS >= set(r.keys())
        assert r["score"] == 0.5
        assert r["post_income_velocity"] == 0.0
        assert r["recovery_time_days"] == 0

    def test_all_credits(self) -> None:
        r = stress.loss_aversion_index(
            [{"type": "credit", "amount_paise": 100, "date_iso": "2025-01-01"}]
        )
        assert LOSS_KEYS >= set(r.keys())
        assert r["score"] == 0.5

    def test_exact_velocity(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 200000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-02"},
        ]
        r = stress.loss_aversion_index(txns)
        assert LOSS_KEYS >= set(r.keys())
        assert r["post_income_velocity"] == pytest.approx(0.5, abs=1e-6)
        assert r["score"] == pytest.approx(0.2, abs=1e-4)
        assert r["recovery_time_days"] == 0
        assert r["large_expense_count"] == 0

    def test_large_expense(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 200000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-02"},
            {"type": "debit", "amount_paise": 2000000, "date_iso": "2025-01-03"},
        ]
        r = stress.loss_aversion_index(txns)
        assert LOSS_KEYS >= set(r.keys())
        assert r["post_income_velocity"] == pytest.approx(10.5, abs=1e-6)
        assert r["score"] == pytest.approx(1.0, abs=1e-4)
        assert r["recovery_time_days"] == 30
        assert r["large_expense_count"] == 1

    def test_missing_date_iso(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 200000},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
        ]
        r = stress.loss_aversion_index(txns)
        assert LOSS_KEYS >= set(r.keys())
        assert isinstance(r["score"], float)


class TestImpulsivityStructure:
    def test_empty(self) -> None:
        r = stress.impulsivity_score([])
        assert IMP_KEYS >= set(r.keys())
        assert r["score"] == 0.5
        assert r["micro_txn_ratio"] == 0.0
        assert r["late_night_ratio"] == 0.0

    def test_all_micro_weekend(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-05", "category": "Food & Dining"},
        ]
        r = stress.impulsivity_score(txns)
        assert IMP_KEYS >= set(r.keys())
        assert r["micro_txn_ratio"] == pytest.approx(1.0, abs=1e-6)
        assert r["weekend_ratio"] == pytest.approx(1.0, abs=1e-6)
        assert r["discretionary_ratio"] == pytest.approx(1.0, abs=1e-6)
        assert r["micro_txn_count"] == 3
        # score = 0.35*0.3333 + 0.35*0.3333 + 0.30*0.3333? check
        assert r["score"] == pytest.approx(0.7667, abs=1e-3)

    def test_discretionary_weekday(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-06", "category": "Food & Dining"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-07", "category": "Food & Dining"},
        ]
        r = stress.impulsivity_score(txns)
        assert IMP_KEYS >= set(r.keys())
        assert r["discretionary_ratio"] == pytest.approx(1.0, abs=1e-6)
        assert r["score"] == pytest.approx(0.7667, abs=1e-3)
        assert r["micro_txn_count"] == 2

    def test_missing_keys(self) -> None:
        txns = [{"type": "debit", "amount_paise": 30000}]
        r = stress.impulsivity_score(txns)
        assert IMP_KEYS >= set(r.keys())
        assert isinstance(r["score"], float)


class TestHabitStabilityStressStructure:
    def test_empty(self) -> None:
        r = stress.habit_stability_score([])
        assert HABIT_KEYS >= set(r.keys())
        assert r["score"] == 0.5
        assert r["category_cv"] == 0.0
        assert r["recurring_predictability"] == 0.0

    def test_recurring(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-01", "description": "NETFLIX", "category": "X"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-02-01", "description": "NETFLIX", "category": "X"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-03-01", "description": "NETFLIX", "category": "X"},
        ]
        r = stress.habit_stability_score(txns)
        assert HABIT_KEYS >= set(r.keys())
        assert r["category_cv"] == pytest.approx(0.0, abs=1e-6)
        assert r["recurring_count"] == 1
        assert r["rhythm_score"] == pytest.approx(1.0, abs=1e-6)
        assert r["score"] == pytest.approx(0.73, abs=1e-3)

    def test_missing_category(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-01", "description": "X"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-02-01", "description": "X"},
        ]
        r = stress.habit_stability_score(txns)
        assert HABIT_KEYS >= set(r.keys())
        assert isinstance(r["score"], float)


class TestFinancialStressStructure:
    def test_empty(self) -> None:
        r = stress.financial_stress_index([])
        assert FSTRESS_KEYS >= set(r.keys())
        assert r["score"] == 0.5
        assert r["balance_volatility"] == 0.0
        assert r["credit_dependency"] == 0.0

    def test_exact(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
        ]
        r = stress.financial_stress_index(txns)
        assert FSTRESS_KEYS >= set(r.keys())
        assert r["balance_volatility"] == pytest.approx(0.0, abs=1e-6)
        assert r["credit_dependency"] == pytest.approx(2.0, abs=1e-6)
        assert r["buffer_days"] == pytest.approx(1.0, abs=1e-6)
        assert r["score"] == pytest.approx(0.4933, abs=1e-4)

    def test_missing_keys(self) -> None:
        txns = [{"type": "debit", "amount_paise": 50000}]
        r = stress.financial_stress_index(txns)
        assert FSTRESS_KEYS >= set(r.keys())
        assert isinstance(r["score"], float)


class TestSavingsDisciplineStressStructure:
    def test_empty(self) -> None:
        r = stress.savings_discipline_score([])
        assert SAV_KEYS >= set(r.keys())
        assert r["score"] == 0.5
        assert r["savings_rate"] == 0.0
        assert r["momentum"] == 0.0

    def test_exact(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 80000, "date_iso": "2025-01-15"},
        ]
        r = stress.savings_discipline_score(txns)
        assert SAV_KEYS >= set(r.keys())
        assert r["savings_rate"] == pytest.approx(0.2, abs=1e-6)
        assert r["momentum"] == 0
        assert r["consistency"] == 1.0
        assert r["positive_savings_months"] == 1
        assert r["score"] == pytest.approx(0.73, abs=1e-3)

    def test_missing_keys(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000}]
        r = stress.savings_discipline_score(txns)
        assert SAV_KEYS >= set(r.keys())
        assert isinstance(r["score"], float)
