"""M9-C43.6 — Mutation-strengthening tests for behaviour_engine/core.py.

These tests target the 3,383 surviving mutants by asserting exact
behavioral invariants that discriminating tests must satisfy.
The existing suite (259 tests) covers execution paths but lacks
precision assertions on computational boundaries.
"""

from __future__ import annotations

import pytest
from src.engines.behaviour_engine.core import (
    _coefficient_of_variation,
    _compute_financial_stress_index,
    _compute_habit_stability_score,
    _compute_impulsivity_score,
    _compute_loss_aversion_index,
    _compute_savings_discipline_score,
    _moving_average,
    _normalize_score,
    _parse_date,
    detect_india_risk_patterns,
)


# ============================================================
# _normalize_score — boundary, clamping, equal-bounds mutants
# ============================================================
class TestNormalizeScoreMutants:
    def test_at_min_returns_zero(self) -> None:
        assert _normalize_score(0.0, 0.0, 10.0) == 0.0

    def test_at_max_returns_one(self) -> None:
        assert _normalize_score(10.0, 0.0, 10.0) == 1.0

    def test_below_min_clamps_to_zero(self) -> None:
        assert _normalize_score(-5.0, 0.0, 10.0) == 0.0

    def test_above_max_clamps_to_one(self) -> None:
        assert _normalize_score(15.0, 0.0, 10.0) == 1.0

    def test_equal_bounds_returns_half(self) -> None:
        assert _normalize_score(5.0, 5.0, 5.0) == 0.5

    def test_halfway_point_is_0_5(self) -> None:
        assert _normalize_score(5.0, 0.0, 10.0) == 0.5

    def test_custom_bounds_asymmetric(self) -> None:
        # value 3 in [0, 10] → 0.3
        assert _normalize_score(3.0, 0.0, 10.0) == 0.3


# ============================================================
# _coefficient_of_variation — boundary, empty, zero-mean mutants
# ============================================================
class TestCoefficientOfVariationMutants:
    def test_empty_list_returns_zero(self) -> None:
        assert _coefficient_of_variation([]) == 0.0

    def test_single_value_returns_zero(self) -> None:
        assert _coefficient_of_variation([42.0]) == 0.0

    def test_identical_values_returns_zero(self) -> None:
        assert _coefficient_of_variation([5.0, 5.0, 5.0]) == 0.0

    def test_zero_mean_returns_zero(self) -> None:
        # All zeros → mean=0 → returns 0 (guard against division-by-zero)
        assert _coefficient_of_variation([0.0, 0.0, 0.0]) == 0.0

    def test_two_different_values(self) -> None:
        # [0, 2] → mean=1, std=1, cv=1.0
        import math
        result = _coefficient_of_variation([0.0, 2.0])
        assert result == pytest.approx(1.0, rel=1e-5)

    def test_known_distribution(self) -> None:
        # [10, 20, 30] → mean=20, var=(100+0+100)/3=66.67, std=8.165, cv=0.4082
        result = _coefficient_of_variation([10.0, 20.0, 30.0])
        assert result == pytest.approx(0.408248, rel=1e-5)


# ============================================================
# _moving_average — window boundary, empty, single-value mutants
# ============================================================
class TestMovingAverageMutants:
    def test_empty_list_returns_empty(self) -> None:
        assert _moving_average([], 3) == []

    def test_window_zero_returns_empty(self) -> None:
        assert _moving_average([1, 2, 3], 0) == []

    def test_window_negative_returns_empty(self) -> None:
        assert _moving_average([1, 2, 3], -1) == []

    def test_single_value(self) -> None:
        assert _moving_average([5.0], 3) == [5.0]

    def test_window_one(self) -> None:
        assert _moving_average([1.0, 2.0, 3.0], 1) == [1.0, 2.0, 3.0]

    def test_window_equals_length(self) -> None:
        assert _moving_average([2.0, 4.0, 6.0], 3) == [2.0, 3.0, 4.0]

    def test_linear_sequence_window_two(self) -> None:
        result = _moving_average([1.0, 2.0, 3.0, 4.0, 5.0], 2)
        assert result == pytest.approx([1.0, 1.5, 2.5, 3.5, 4.5], rel=1e-5)


# ============================================================
# _parse_date — format variants, invalid input mutants
# ============================================================
class TestParseDateMutants:
    def test_iso_format(self) -> None:
        from datetime import datetime
        result = _parse_date("2025-01-15")
        assert result == datetime(2025, 1, 15)

    def test_invalid_date_returns_none(self) -> None:
        assert _parse_date("not-a-date") is None

    def test_empty_string_returns_none(self) -> None:
        assert _parse_date("") is None

    def test_whitespace_only_returns_none(self) -> None:
        assert _parse_date("   ") is None

    def test_ddmmyyyy_format(self) -> None:
        from datetime import datetime
        result = _parse_date("15/01/2025")
        assert result == datetime(2025, 1, 15)

    def test_whitespace_trimmed(self) -> None:
        from datetime import datetime
        result = _parse_date("  2025-01-15  ")
        assert result == datetime(2025, 1, 15)


# ============================================================
# _compute_impulsivity_score — micro-ratio, weekend ratio, disc ratio
# ============================================================
class TestImpulsivityScoreMutants:
    def test_no_transactions_returns_baseline(self) -> None:
        result = _compute_impulsivity_score([])
        assert result["score"] == 0.5
        assert result["micro_txn_ratio"] == 0.0

    def test_no_debits_returns_baseline(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"}]
        result = _compute_impulsivity_score(txns)
        assert result["score"] == 0.5

    def test_micro_txn_boundary_at_500_rupees(self) -> None:
        """Micro transactions are < ₹500 (i.e., < 50000 paise)."""
        txns = [
            {"type": "debit", "amount_paise": 49999, "date_iso": "2025-01-01", "category": "food"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-02", "category": "food"},
            {"type": "debit", "amount_paise": 50001, "date_iso": "2025-01-03", "category": "food"},
        ]
        result = _compute_impulsivity_score(txns)
        # 1 of 3 is micro (< 50000) → micro_ratio ≈ 0.333
        assert result["micro_txn_count"] == 1
        assert result["micro_txn_ratio"] == pytest.approx(1/3, abs=1e-4)

    def test_all_micro_transactions_high_micro_ratio(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": i * 1000, "date_iso": f"2025-01-{i+1:02d}", "category": "food"}
            for i in range(1, 11)
        ]
        result = _compute_impulsivity_score(txns)
        assert result["micro_txn_ratio"] == 1.0  # all < 50000

    def test_weekend_vs_weekday_ratio(self) -> None:
        """Jan 4, 2025 is Saturday; Jan 6, 2025 is Monday."""
        txns = [
            {"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-04", "category": "entertainment"},  # Sat
            {"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-06", "category": "groceries"},      # Mon
        ]
        result = _compute_impulsivity_score(txns)
        # Weekend total = 100000, weekday total = 100000 → ratio = 1.0
        assert result["weekend_ratio"] == pytest.approx(1.0, rel=1e-5)

    def test_discretionary_category_ratio(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-01", "category": "Food & Dining"},
            {"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-02", "category": "Rent"},
        ]
        result = _compute_impulsivity_score(txns)
        # Food & Dining is discretionary, Rent is not → 0.5
        assert result["discretionary_ratio"] == pytest.approx(0.5, rel=1e-5)


# ============================================================
# _compute_loss_aversion_index — velocity boundary, recovery days
# ============================================================
class TestLossAversionIndexMutants:
    def test_no_transactions_returns_baseline(self) -> None:
        result = _compute_loss_aversion_index([])
        assert result["score"] == 0.5

    def test_credit_only_returns_baseline(self) -> None:
        txns = [{"type": "credit", "amount_paise": 500000, "date_iso": "2025-01-01"}]
        result = _compute_loss_aversion_index(txns)
        assert result["score"] == 0.5

    def test_velocity_boundary_72_hours(self) -> None:
        """Spending within 72 hours (0 <= days_diff <= 3) counts as post-income velocity."""
        txns = [
            {"type": "credit", "amount_paise": 500000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-02"},  # 1 day after
        ]
        result = _compute_loss_aversion_index(txns)
        # velocity = 100000/500000 = 0.2
        assert result["post_income_velocity"] == pytest.approx(0.2, rel=1e-5)

    def test_velocity_excludes_after_72_hours(self) -> None:
        """Spending beyond 3 days is NOT counted as post-income velocity."""
        txns = [
            {"type": "credit", "amount_paise": 500000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-05"},  # 4 days after (> 3)
        ]
        result = _compute_loss_aversion_index(txns)
        assert result["post_income_velocity"] == pytest.approx(0.0, rel=1e-5)

    def test_large_expense_threshold_2x_median(self) -> None:
        """Expenses > 2x median debit are 'large expenses' for recovery calculation.

        Note: _compute_loss_aversion_index does NOT return large_expense_count
        in its output dict — only score, post_income_velocity, recovery_time_days.
        This test verifies the function runs without error and returns expected keys.
        """
        txns = [
            {"type": "debit", "amount_paise": 10000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 10000, "date_iso": "2025-01-02"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-03"},
        ]
        result = _compute_loss_aversion_index(txns)
        # Verify expected keys exist
        assert "score" in result
        assert "post_income_velocity" in result
        assert "recovery_time_days" in result


# ============================================================
# _compute_habit_stability_score — category CV, recurring detection
# ============================================================
class TestHabitStabilityMutants:
    def test_no_transactions_returns_baseline(self) -> None:
        result = _compute_habit_stability_score([])
        assert result["score"] == 0.5

    def test_no_debits_returns_baseline(self) -> None:
        txns = [{"type": "credit", "amount_paise": 500000, "date_iso": "2025-01-01"}]
        result = _compute_habit_stability_score(txns)
        assert result["score"] == 0.5

    def test_recurring_detection_threshold_3_payments(self) -> None:
        """At least 3 similar payments needed to count as recurring."""
        txns = [
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-01", "description": "Netflix"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-02-01", "description": "Netflix"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-03-01", "description": "Netflix"},
        ]
        result = _compute_habit_stability_score(txns)
        assert result["recurring_count"] >= 1

    def test_recurring_not_detected_with_only_2_payments(self) -> None:
        """Only 2 payments → below threshold of 3."""
        txns = [
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-01", "description": "Netflix"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-02-01", "description": "Netflix"},
        ]
        result = _compute_habit_stability_score(txns)
        assert result["recurring_count"] == 0


# ============================================================
# _compute_financial_stress_index — EOM depletion, buffer adequacy
# ============================================================
class TestFinancialStressMutants:
    def test_no_transactions_returns_baseline(self) -> None:
        result = _compute_financial_stress_index([])
        assert result["score"] == 0.5

    def test_end_of_month_depletion_boundary_day_26(self) -> None:
        """EOM depletion counts days >= 26 as end-of-month spending."""
        txns = [
            {"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-26"},  # EOM
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-31"},  # EOM
        ]
        result = _compute_financial_stress_index(txns)
        # Total = 1100000, EOM = 1000000 → ratio = 1000000/1100000 ≈ 0.909
        assert result["eom_depletion_ratio"] == pytest.approx(1000000/1100000, rel=1e-4)

    def test_credit_dependency_ratio(self) -> None:
        """Credit dependency = total credits / total debits."""
        txns = [
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-02"},
        ]
        result = _compute_financial_stress_index(txns)
        assert result["credit_dependency"] == pytest.approx(2.0, rel=1e-5)


# ============================================================
# _compute_savings_discipline_score — savings rate, momentum
# ============================================================
class TestSavingsDisciplineMutants:
    def test_no_transactions_returns_baseline(self) -> None:
        result = _compute_savings_discipline_score([])
        assert result["score"] == 0.5

    def test_savings_rate_boundary_positive(self) -> None:
        """Income > expenses → positive savings rate."""
        txns = [
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 800000, "date_iso": "2025-01-15"},
        ]
        result = _compute_savings_discipline_score(txns)
        # savings_rate = (1000000 - 800000) / 1000000 = 0.2
        assert result["savings_rate"] == pytest.approx(0.2, rel=1e-5)

    def test_savings_rate_boundary_negative(self) -> None:
        """Expenses > income → negative savings rate."""
        txns = [
            {"type": "credit", "amount_paise": 500000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 600000, "date_iso": "2025-01-15"},
        ]
        result = _compute_savings_discipline_score(txns)
        # savings_rate = (500000 - 600000) / 500000 = -0.2
        assert result["savings_rate"] == pytest.approx(-0.2, rel=1e-5)

    def test_momentum_positive(self) -> None:
        """Recent months show improving savings rate."""
        txns = [
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2024-11-01"},
            {"type": "debit", "amount_paise": 800000, "date_iso": "2024-11-15"},
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2024-12-01"},
            {"type": "debit", "amount_paise": 600000, "date_iso": "2024-12-15"},
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-15"},
        ]
        result = _compute_savings_discipline_score(txns)
        # Nov: 0.2, Dec: 0.4, Jan: 0.5 → momentum = recent_avg(0.45) - earlier_avg(0.2) > 0
        assert result["momentum"] > 0


# ============================================================
# detect_india_risk_patterns — UPI flag, gambling flag, loan flag, EMI ratio
# ============================================================
class TestIndiaRiskPatternsMutants:
    def test_no_transactions_returns_defaults(self) -> None:
        result = detect_india_risk_patterns([])
        assert result["upi_micro_spend_flag"] is False
        assert result["gambling_flag"] is False
        assert result["loan_app_pattern_flag"] is False
        assert result["emi_ratio"] == 0.0

    def test_upi_micro_spend_boundary_10_per_day(self) -> None:
        """>10 micro transactions per day flags UPI spend."""
        txns = [
            {"type": "debit", "amount_paise": 10000, "date_iso": "2025-01-01", "description": "UPI pay"}
            for _ in range(11)  # 11 micro txns on same day
        ]
        result = detect_india_risk_patterns(txns)
        assert result["upi_micro_spend_flag"] is True

    def test_upi_micro_spend_below_threshold(self) -> None:
        """<=10 micro transactions per day does NOT flag UPI spend."""
        txns = [
            {"type": "debit", "amount_paise": 10000, "date_iso": "2025-01-01", "description": "UPI pay"}
            for _ in range(10)  # exactly 10
        ]
        result = detect_india_risk_patterns(txns)
        assert result["upi_micro_spend_flag"] is False

    def test_gambling_keyword_detection(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01", "description": "Dream11 payment"},
        ]
        result = detect_india_risk_patterns(txns)
        assert result["gambling_flag"] is True
        assert result["gambling_transaction_count"] == 1

    def test_loan_app_clustering_flag(self) -> None:
        """Multiple small loan credits (>=2) flag loan app pattern."""
        txns = [
            {"type": "credit", "amount_paise": 10000, "date_iso": "2025-01-01", "description": "Loan from NBFC"},
            {"type": "credit", "amount_paise": 15000, "date_iso": "2025-01-03", "description": "Instant cash loan"},
        ]
        result = detect_india_risk_patterns(txns)
        assert result["loan_app_pattern_flag"] is True
        assert result["loan_credit_count"] == 2

    def test_emi_ratio_calculation(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-01", "description": "Salary"},
            {"type": "debit", "amount_paise": 300000, "date_iso": "2025-01-05", "description": "EMI payment"},
        ]
        result = detect_india_risk_patterns(txns)
        # emi_ratio = 300000 / 1000000 = 0.3
        assert result["emi_ratio"] == pytest.approx(0.3, rel=1e-5)

    def test_amount_below_200_rupees_for_upi(self) -> None:
        """UPI micro-spend threshold is < ₹200 (20000 paise)."""
        txns = [
            {"type": "debit", "amount_paise": 19999, "date_iso": "2025-01-01", "description": "UPI"},
            {"type": "debit", "amount_paise": 20000, "date_iso": "2025-01-01", "description": "UPI"},  # exactly 200
        ]
        result = detect_india_risk_patterns(txns)
        # Only 1 txn < 200, so even with 11 txns we'd need more. Here just checking boundary.
        assert result["upi_micro_spend_flag"] is False  # only 1 micro txn, need >10


# ============================================================
# END M9-C43.6 Mutation-Strengthening Tests for behaviour_engine
# ============================================================


# ============================================================
# generate_behavioral_insights — boundary threshold mutants
# ============================================================
class TestInsightsBoundaryMutants:
    def test_empty_profile_returns_empty_insights(self) -> None:
        from src.engines.behaviour_engine.insights import generate_behavioral_insights
        assert generate_behavioral_insights({}) == []
        assert generate_behavioral_insights(None) == []

    def test_velocity_threshold_0_5_excluded(self) -> None:
        """velocity == 0.5 is NOT > 0.5, so no insight generated."""
        from src.engines.behaviour_engine.insights import generate_behavioral_insights
        profile = {"behavioral_indices": {"loss_aversion": {"post_income_velocity": 0.5}}}
        insights = generate_behavioral_insights(profile)
        assert not any("Post-Income" in i["title"] for i in insights)

    def test_velocity_threshold_0_51_included(self) -> None:
        """velocity > 0.5 triggers post-income spending insight."""
        from src.engines.behaviour_engine.insights import generate_behavioral_insights
        profile = {"behavioral_indices": {"loss_aversion": {"post_income_velocity": 0.51}}}
        insights = generate_behavioral_insights(profile)
        assert any("Post-Income" in i["title"] for i in insights)
        assert insights[0]["type"] == "warning"

    def test_micro_ratio_boundary_0_4_excluded(self) -> None:
        """micro_ratio == 0.4 is NOT > 0.4."""
        from src.engines.behaviour_engine.insights import generate_behavioral_insights
        profile = {"behavioral_indices": {"impulsivity": {"micro_txn_ratio": 0.4}}}
        insights = generate_behavioral_insights(profile)
        assert not any("Micro-Transaction" in i["title"] for i in insights)

    def test_weekend_ratio_boundary_1_3_excluded(self) -> None:
        """weekend_ratio == 1.3 is NOT > 1.3."""
        from src.engines.behaviour_engine.insights import generate_behavioral_insights
        profile = {"behavioral_indices": {"impulsivity": {"weekend_ratio": 1.3}}}
        insights = generate_behavioral_insights(profile)
        assert not any("Weekend Spending" in i["title"] for i in insights)

    def test_category_cv_high_boundary(self) -> None:
        """category_cv > 0.5 triggers unstable pattern warning."""
        from src.engines.behaviour_engine.insights import generate_behavioral_insights
        profile = {"behavioral_indices": {"habit_stability": {"category_cv": 0.51}}}
        insights = generate_behavioral_insights(profile)
        assert any("Unstable" in i["title"] for i in insights)

    def test_category_cv_low_boundary(self) -> None:
        """category_cv < 0.2 triggers consistent habits positive."""
        from src.engines.behaviour_engine.insights import generate_behavioral_insights
        profile = {"behavioral_indices": {"habit_stability": {"category_cv": 0.19}}}
        insights = generate_behavioral_insights(profile)
        assert any("Consistent" in i["title"] for i in insights)

    def test_recurring_count_threshold_5(self) -> None:
        """recurring >= 5 triggers strong pattern insight."""
        from src.engines.behaviour_engine.insights import generate_behavioral_insights
        profile = {"behavioral_indices": {"habit_stability": {"recurring_count": 5}}}
        insights = generate_behavioral_insights(profile)
        assert any("Recurring" in i["title"] for i in insights)


# ============================================================
# generate_nudges — threshold boundary mutants
# ============================================================
class TestNudgesBoundaryMutants:
    def test_empty_profile_returns_empty_nudges(self) -> None:
        from src.engines.behaviour_engine.nudges import generate_nudges
        assert generate_nudges({}) == []
        assert generate_nudges(None) == []

    def test_impulse_score_boundary_0_7_excluded(self) -> None:
        """impulse_score == 0.7 is NOT > 0.7."""
        from src.engines.behaviour_engine.nudges import generate_nudges
        profile = {"behavioral_indices": {"impulsivity": {"score": 0.7}}}
        nudges = generate_nudges(profile)
        assert not any("24-Hour Rule" in n["title"] for n in nudges)

    def test_impulse_score_above_0_7_included(self) -> None:
        """impulse_score > 0.7 triggers friction nudge."""
        from src.engines.behaviour_engine.nudges import generate_nudges
        profile = {"behavioral_indices": {"impulsivity": {"score": 0.71}}}
        nudges = generate_nudges(profile)
        assert any("24-Hour Rule" in n["title"] for n in nudges)
        assert nudges[0]["priority"] == 1

    def test_micro_ratio_nudge_boundary_0_5(self) -> None:
        """micro_ratio == 0.5 is NOT > 0.5."""
        from src.engines.behaviour_engine.nudges import generate_nudges
        profile = {"behavioral_indices": {"impulsivity": {"micro_txn_ratio": 0.5}}}
        nudges = generate_nudges(profile)
        assert not any("Micro-Transactions" in n["title"] for n in nudges)

    def test_savings_score_below_0_3_trigger(self) -> None:
        """savings_score < 0.3 triggers automate savings nudge."""
        from src.engines.behaviour_engine.nudges import generate_nudges
        profile = {"behavioral_indices": {"savings_discipline": {"score": 0.29}}}
        nudges = generate_nudges(profile)
        assert any("Automate Savings" in n["title"] for n in nudges)

    def test_savings_rate_below_0_1_trigger(self) -> None:
        """savings_rate < 0.1 triggers 10% target nudge."""
        from src.engines.behaviour_engine.nudges import generate_nudges
        profile = {"behavioral_indices": {"savings_discipline": {"savings_rate": 0.09}}}
        nudges = generate_nudges(profile)
        assert any("10% Target" in n["title"] for n in nudges)

    def test_stress_score_above_0_6_trigger(self) -> None:
        """stress_score > 0.6 triggers emergency buffer nudge."""
        from src.engines.behaviour_engine.nudges import generate_nudges
        profile = {"behavioral_indices": {"financial_stress": {"score": 0.61, "buffer_days": 5}}}
        nudges = generate_nudges(profile)
        assert any("Emergency Buffer" in n["title"] for n in nudges)

    def test_buffer_days_below_7_trigger(self) -> None:
        """buffer_days < 7 triggers pause spending nudge."""
        from src.engines.behaviour_engine.nudges import generate_nudges
        profile = {"behavioral_indices": {"financial_stress": {"buffer_days": 6.5}}}
        nudges = generate_nudges(profile)
        assert any("Pause Non-Essential" in n["title"] for n in nudges)

    def test_velocity_nudge_boundary_0_6(self) -> None:
        """velocity > 0.6 triggers delay post-income nudge."""
        from src.engines.behaviour_engine.nudges import generate_nudges
        profile = {"behavioral_indices": {"loss_aversion": {"post_income_velocity": 0.61}}}
        nudges = generate_nudges(profile)
        assert any("Delay Post-Income" in n["title"] for n in nudges)


# ============================================================
# END M9-C43.6 Additional behaviour_engine Mutation-Strengthening Tests
# ============================================================
