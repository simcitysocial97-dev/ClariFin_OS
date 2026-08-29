"""M9-C43.6 — Precise-score mutation-strengthening for stress.py.

Asserts exact composite scores (hand-verified against current correct behavior)
and branch coverage for the six behavioural index functions, killing the
constant/operator mutants in stress.py's scoring formulas.
"""

from __future__ import annotations

import pytest
from src.engines.behaviour_engine import stress


class TestLossAversionIndexScoreMutants:
    def test_empty(self) -> None:
        assert stress.loss_aversion_index([]) == {
            "score": 0.5,
            "post_income_velocity": 0.0,
            "recovery_time_days": 0,
        }

    def test_velocity_0_5(self) -> None:
        tx = [
            {"type": "credit", "amount_paise": 200000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-02"},
        ]
        r = stress.loss_aversion_index(tx)
        # velocity = (50+50)/200 = 0.5; normalize(0.5,0,1.5)=0.3333*0.6=0.2
        assert r["post_income_velocity"] == pytest.approx(0.5, rel=1e-5)
        assert r["score"] == pytest.approx(0.2, rel=1e-5)
        assert r["recovery_time_days"] == 0
        assert r["large_expense_count"] == 0

    def test_large_expense(self) -> None:
        tx = [
            {"type": "credit", "amount_paise": 200000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-02"},
            {"type": "debit", "amount_paise": 2000000, "date_iso": "2025-01-03"},
        ]
        r = stress.loss_aversion_index(tx)
        # velocity = (50+50+2000)/200 = 10.5 -> clamp -> score 1.0
        assert r["post_income_velocity"] == pytest.approx(10.5, rel=1e-5)
        assert r["score"] == pytest.approx(1.0, rel=1e-5)
        assert r["recovery_time_days"] == 30
        assert r["large_expense_count"] == 1

    def test_credits_only(self) -> None:
        assert (
            stress.loss_aversion_index(
                [{"type": "credit", "amount_paise": 100, "date_iso": "2025-01-01"}]
            )["score"]
            == 0.5
        )

    def test_debits_only(self) -> None:
        assert (
            stress.loss_aversion_index(
                [{"type": "debit", "amount_paise": 100, "date_iso": "2025-01-01"}]
            )["score"]
            == 0.5
        )


class TestImpulsivityScoreStressMutants:
    def test_empty(self) -> None:
        assert stress.impulsivity_score([]) == {
            "score": 0.5,
            "micro_txn_ratio": 0.0,
            "late_night_ratio": 0.0,
        }

    def test_all_micro_weekend(self) -> None:
        tx = [
            {
                "type": "debit",
                "amount_paise": 30000,
                "date_iso": "2025-01-04",
                "category": "food",
            },
            {
                "type": "debit",
                "amount_paise": 30000,
                "date_iso": "2025-01-04",
                "category": "food",
            },
            {
                "type": "debit",
                "amount_paise": 30000,
                "date_iso": "2025-01-05",
                "category": "food",
            },
        ]
        r = stress.impulsivity_score(tx)
        # micro=1, weekend=1, disc=0 -> 1*0.35 + 0.3333*0.35 + 0 = 0.4667
        assert r["micro_txn_ratio"] == 1.0
        assert r["score"] == pytest.approx(0.4667, rel=1e-3)

    def test_discretionary_weekday(self) -> None:
        tx = [
            {
                "type": "debit",
                "amount_paise": 30000,
                "date_iso": "2025-01-06",
                "category": "Food & Dining",
            },
            {
                "type": "debit",
                "amount_paise": 30000,
                "date_iso": "2025-01-07",
                "category": "Food & Dining",
            },
        ]
        r = stress.impulsivity_score(tx)
        # micro=1, weekend=1, disc=1 -> 1*0.35 + 0.3333*0.35 + 1*0.30 = 0.7667
        assert r["discretionary_ratio"] == 1.0
        assert r["score"] == pytest.approx(0.7667, rel=1e-3)
        assert r["micro_txn_count"] == 2


class TestHabitStabilityStressMutants:
    def test_empty(self) -> None:
        assert stress.habit_stability_score([]) == {
            "score": 0.5,
            "category_cv": 0.0,
            "recurring_predictability": 0.0,
        }

    def test_mixed_cv_recurring(self) -> None:
        tx = [
            {
                "type": "debit",
                "amount_paise": 500000,
                "date_iso": "2025-01-01",
                "description": "NETFLIX",
            },
            {
                "type": "debit",
                "amount_paise": 500000,
                "date_iso": "2025-02-01",
                "description": "NETFLIX",
            },
            {
                "type": "debit",
                "amount_paise": 500000,
                "date_iso": "2025-03-01",
                "description": "NETFLIX",
            },
            {
                "type": "debit",
                "amount_paise": 100000,
                "date_iso": "2025-01-02",
                "category": "X",
            },
            {
                "type": "debit",
                "amount_paise": 100000,
                "date_iso": "2025-01-03",
                "category": "X",
            },
            {
                "type": "debit",
                "amount_paise": 100000,
                "date_iso": "2025-01-04",
                "category": "X",
            },
        ]
        r = stress.habit_stability_score(tx)
        # category_cv across months = 0.7071; recurring=2; rhythm=1
        # score = (1-0.7071)*0.4 + min(1,2/10)*0.3 + 1*0.3 = 0.5714
        assert r["category_cv"] == pytest.approx(0.7071, rel=1e-3)
        assert r["recurring_count"] == 2
        assert r["score"] == pytest.approx(0.5714, rel=1e-3)

    def test_low_cv_steady(self) -> None:
        tx = []
        for m in ("2025-01", "2025-02", "2025-03"):
            for d in (1, 2, 3):
                tx.append(
                    {
                        "type": "debit",
                        "amount_paise": 100000,
                        "date_iso": f"{m}-{d:02d}",
                        "description": "NETFLIX",
                    }
                )
        r = stress.habit_stability_score(tx)
        # category_cv=0, recurring=1, rhythm=1 -> 1*0.4 + 0.1*0.3 + 1*0.3 = 0.73
        assert r["category_cv"] == pytest.approx(0.0, abs=1e-6)
        assert r["score"] == pytest.approx(0.73, rel=1e-3)


class TestFinancialStressStressMutants:
    def test_empty(self) -> None:
        assert stress.financial_stress_index([]) == {
            "score": 0.5,
            "balance_volatility": 0.0,
            "credit_dependency": 0.0,
        }

    def test_balanced(self) -> None:
        tx = [
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-02"},
        ]
        r = stress.financial_stress_index(tx)
        # cv([500,0])=1, credit_dep=1, eom=0, buffer=0.5
        # 0.5*0.3+0.5*0.3+0+(1-0.01666)*0.2 = 0.4967
        assert r["balance_volatility"] == pytest.approx(1.0, rel=1e-5)
        assert r["credit_dependency"] == pytest.approx(1.0, rel=1e-5)
        assert r["score"] == pytest.approx(0.4967, rel=1e-4)

    def test_eom_depletion(self) -> None:
        tx = [
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-28"},
        ]
        r = stress.financial_stress_index(tx)
        # eom ratio 0.5 -> eom_score=1.0 (normalize 0.5,0,0.5) -> stress 0.6967
        assert r["eom_depletion_ratio"] == pytest.approx(0.5, rel=1e-5)
        assert r["score"] == pytest.approx(0.6967, rel=1e-4)

    def test_high_buffer(self) -> None:
        tx = [
            {"type": "credit", "amount_paise": 10000000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 10000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 10000, "date_iso": "2025-01-02"},
        ]
        r = stress.financial_stress_index(tx)
        # buffer_days=998.5 -> buffer_score=1 -> (1-1)*0.2=0; low stress ~0.3001
        assert r["buffer_days"] == pytest.approx(998.5, rel=1e-4)
        assert r["score"] == pytest.approx(0.3001, rel=1e-3)


class TestSavingsDisciplineStressMutants:
    def test_empty(self) -> None:
        assert stress.savings_discipline_score([]) == {
            "score": 0.5,
            "savings_rate": 0.0,
            "momentum": 0.0,
        }

    def test_positive(self) -> None:
        tx = [
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 800000, "date_iso": "2025-01-15"},
        ]
        r = stress.savings_discipline_score(tx)
        # rate=0.2 -> score 0.73
        assert r["savings_rate"] == pytest.approx(0.2, rel=1e-5)
        assert r["score"] == pytest.approx(0.73, rel=1e-4)

    def test_negative(self) -> None:
        tx = [
            {"type": "credit", "amount_paise": 500000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 600000, "date_iso": "2025-01-15"},
        ]
        r = stress.savings_discipline_score(tx)
        # rate=-0.2 -> rate_score=0; consistency=0 -> score 0.27
        assert r["savings_rate"] == pytest.approx(-0.2, rel=1e-5)
        assert r["consistency"] == 0.0
        assert r["score"] == pytest.approx(0.27, rel=1e-4)


class TestDetectRiskStressMutants:
    def test_upi_micro(self) -> None:
        # >10 micro txns on a single day triggers the flag
        tx = [
            {"type": "debit", "amount_paise": 19900, "date_iso": "2025-01-01"}
            for _ in range(12)
        ]
        r = stress.detect_risk_patterns(tx)
        assert r["upi_micro_spend_flag"] is True

    def test_no_upi_micro(self) -> None:
        # 10 txns on one day is at the boundary (not >10)
        tx = [
            {"type": "debit", "amount_paise": 19900, "date_iso": "2025-01-01"}
            for _ in range(10)
        ]
        assert stress.detect_risk_patterns(tx)["upi_micro_spend_flag"] is False

    def test_gambling(self) -> None:
        tx = [
            {
                "type": "debit",
                "amount_paise": 50000,
                "date_iso": "2025-01-01",
                "description": "Dream11",
            }
        ]
        r = stress.detect_risk_patterns(tx)
        assert r["gambling_flag"] is True
        assert r["gambling_transaction_count"] == 1

    def test_loan_clustering(self) -> None:
        tx = [
            {
                "type": "credit",
                "amount_paise": 10000,
                "date_iso": "2025-01-01",
                "description": "Loan app",
            },
            {
                "type": "credit",
                "amount_paise": 15000,
                "date_iso": "2025-01-03",
                "description": "NBFC credit",
            },
        ]
        r = stress.detect_risk_patterns(tx)
        assert r["loan_app_pattern_flag"] is True
        assert r["loan_credit_count"] == 2

    def test_single_loan(self) -> None:
        tx = [
            {
                "type": "credit",
                "amount_paise": 10000,
                "date_iso": "2025-01-01",
                "description": "Loan app",
            }
        ]
        assert stress.detect_risk_patterns(tx)["loan_app_pattern_flag"] is False

    def test_emi_ratio(self) -> None:
        tx = [
            {
                "type": "debit",
                "amount_paise": 50000,
                "date_iso": "2025-01-10",
                "description": "emi payment",
            },
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-15"},
        ]
        r = stress.detect_risk_patterns(tx)
        assert r["emi_ratio"] == pytest.approx(0.5, rel=1e-5)
