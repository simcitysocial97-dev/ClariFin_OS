"""M9-C43.6 — Mutation-strengthening for core.py (behaviour_engine).

Targets the dominant survivor pool in core.py:
- 4 helper functions never exercised by compute_behavior_profile (no-test mutants)
- caching layer
- temporal pattern analysis
- the 5 behavioral index functions with hand-computed exact scores
- end-to-end compute_behavior_profile structure + confidence
"""

from __future__ import annotations

import pytest
from src.engines.behaviour_engine import core


# ============================================================
# Caching layer
# ============================================================
class TestCacheLayerMutants:
    def test_invalidate_clears(self) -> None:
        core.set_cached_behavior_profile("k", {"a": 1})
        assert core.get_cached_behavior_profile("k") == {"a": 1}
        core.invalidate_behavior_cache()
        assert core.get_cached_behavior_profile("k") is None

    def test_get_missing_returns_none(self) -> None:
        core.invalidate_behavior_cache()
        assert core.get_cached_behavior_profile("missing") is None

    def test_set_overwrites(self) -> None:
        core.set_cached_behavior_profile("k", {"a": 1})
        core.set_cached_behavior_profile("k", {"a": 2})
        assert core.get_cached_behavior_profile("k") == {"a": 2}
        core.invalidate_behavior_cache()


# ============================================================
# _parse_date — format variants + invalid
# ============================================================
class TestParseDateMutants:
    def test_none(self) -> None:
        assert core._parse_date(None) is None

    def test_empty(self) -> None:
        assert core._parse_date("") is None

    def test_iso(self) -> None:
        from datetime import datetime
        assert core._parse_date("2025-01-15") == datetime(2025, 1, 15)

    def test_dmy_slash(self) -> None:
        from datetime import datetime
        assert core._parse_date("15/01/2025") == datetime(2025, 1, 15)

    def test_dmy_dash(self) -> None:
        from datetime import datetime
        assert core._parse_date("15-01-2025") == datetime(2025, 1, 15)

    def test_dmy_short_year(self) -> None:
        from datetime import datetime
        assert core._parse_date("15/01/25") == datetime(2025, 1, 15)

    def test_d_b_m_y(self) -> None:
        from datetime import datetime
        assert core._parse_date("15 Jan 2025") == datetime(2025, 1, 15)

    def test_d_b_short(self) -> None:
        from datetime import datetime
        assert core._parse_date("15 Jan 25") == datetime(2025, 1, 15)

    def test_d_dash_b_dash(self) -> None:
        from datetime import datetime
        assert core._parse_date("15-Jan-2025") == datetime(2025, 1, 15)

    def test_d_dash_b_short(self) -> None:
        from datetime import datetime
        assert core._parse_date("15-Jan-25") == datetime(2025, 1, 15)

    def test_strip_whitespace(self) -> None:
        from datetime import datetime
        assert core._parse_date("  2025-01-15  ") == datetime(2025, 1, 15)

    def test_invalid(self) -> None:
        assert core._parse_date("not-a-date") is None


# ============================================================
# _normalize_score — boundaries
# ============================================================
class TestNormalizeScoreCoreMutants:
    def test_equal_bounds(self) -> None:
        assert core._normalize_score(5, 5, 5) == 0.5

    def test_below_min_clamps(self) -> None:
        assert core._normalize_score(-1, 0, 10) == 0.0

    def test_above_max_clamps(self) -> None:
        assert core._normalize_score(20, 0, 10) == 1.0

    def test_midpoint(self) -> None:
        assert core._normalize_score(5, 0, 10) == 0.5

    def test_negative_range(self) -> None:
        assert core._normalize_score(-0.5, -0.5, 0.5) == 0.0


# ============================================================
# Unused helper functions — direct coverage (kills no-test mutants)
# ============================================================
class TestDailySpendingDataMutants:
    def test_basic(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-01"},
            {"type": "credit", "amount_paise": 50, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 200, "date_iso": "2025-01-02"},
        ]
        result = core._get_daily_spending_data(txns, "2025-01-01")
        assert result == {"2025-01-01": 100, "2025-01-02": 200}

    def test_cutoff_excludes_old(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 200, "date_iso": "2025-02-01"},
        ]
        result = core._get_daily_spending_data(txns, "2025-02-01")
        assert result == {"2025-02-01": 200}

    def test_empty(self) -> None:
        assert core._get_daily_spending_data([], "2025-01-01") == {}


class TestMonthlyCategorySpendingMutants:
    def test_basic(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-01", "category": "Food"},
            {"type": "debit", "amount_paise": 200, "date_iso": "2025-01-15", "category": "Food"},
            {"type": "debit", "amount_paise": 300, "date_iso": "2025-02-01", "category": "Rent"},
            {"type": "credit", "amount_paise": 999, "date_iso": "2025-01-01"},
        ]
        result = core._get_monthly_category_spending_data(txns, "2025-01-01")
        assert result["2025-01"]["Food"] == 300.0  # 100 + 200 paise (raw, per impl)
        assert result["2025-02"]["Rent"] == 300.0

    def test_cutoff(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-01", "category": "Food"},
            {"type": "debit", "amount_paise": 200, "date_iso": "2025-03-01", "category": "Food"},
        ]
        result = core._get_monthly_category_spending_data(txns, "2025-03-01")
        assert "2025-01" not in result
        assert result["2025-03"]["Food"] == 200.0

    def test_empty(self) -> None:
        assert core._get_monthly_category_spending_data([], "2025-01-01") == {}


class TestMonthlyIncomeExpensesMutants:
    def test_basic(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 1000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 300, "date_iso": "2025-01-10"},
            {"type": "debit", "amount_paise": 200, "date_iso": "2025-02-01"},
        ]
        result = core._get_monthly_income_expenses_data(txns, "2025-01-01")
        assert result["2025-01"]["income_paise"] == 1000
        assert result["2025-01"]["expenses_paise"] == 300
        assert result["2025-02"]["expenses_paise"] == 200

    def test_cutoff(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 1000, "date_iso": "2025-01-01"},
            {"type": "credit", "amount_paise": 500, "date_iso": "2025-04-01"},
        ]
        result = core._get_monthly_income_expenses_data(txns, "2025-04-01")
        assert "2025-01" not in result
        assert result["2025-04"]["income_paise"] == 500

    def test_empty(self) -> None:
        assert core._get_monthly_income_expenses_data([], "2025-01-01") == {}


class TestTransactionStatsMutants:
    def test_basic(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04"},   # micro (<50000)
            {"type": "debit", "amount_paise": 60000, "date_iso": "2025-01-06"},   # not micro
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
        ]
        stats = core._get_transaction_stats_data(txns, "2025-01-01")
        assert stats["total_count"] == 3
        assert stats["debit_count"] == 2
        assert stats["credit_count"] == 1
        assert stats["micro_txn_count"] == 1
        assert stats["total_debit_paise"] == 90000
        assert stats["total_credit_paise"] == 100000
        # 2025-01-04 is Saturday -> weekend; 2025-01-06 Monday -> weekday
        assert stats["weekend_spend_paise"] == 30000
        assert stats["weekday_spend_paise"] == 60000

    def test_cutoff(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 200, "date_iso": "2025-05-01"},
        ]
        stats = core._get_transaction_stats_data(txns, "2025-05-01")
        assert stats["total_count"] == 1
        assert stats["debit_count"] == 1

    def test_empty(self) -> None:
        stats = core._get_transaction_stats_data([], "2025-01-01")
        assert stats["total_count"] == 0
        assert stats["micro_txn_count"] == 0


# ============================================================
# _get_transactions_90_days / _get_recent_transactions
# ============================================================
class TestTransactionWindowMutants:
    def test_90_days_filters_old(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2000-01-01"},
            {"type": "debit", "amount_paise": 200, "date_iso": "2099-01-01"},
        ]
        result = core._get_transactions_90_days(txns)
        assert len(result) == 1
        assert result[0]["date_iso"] == "2099-01-01"

    def test_recent_limits_and_orders(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-03"},
            {"type": "debit", "amount_paise": 200, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 300, "date_iso": "2025-01-02"},
        ]
        result = core._get_recent_transactions(txns, limit=2)
        assert len(result) == 2
        # limit=2 takes the 2 most recent (01-03, 01-02), returned ascending
        assert result[0]["date_iso"] == "2025-01-02"
        assert result[1]["date_iso"] == "2025-01-03"


# ============================================================
# _compute_temporal_patterns
# ============================================================
class TestTemporalPatternsMutants:
    def test_empty(self) -> None:
        assert core._compute_temporal_patterns([]) == {
            "trend": 0.0, "seasonality": 0.0, "residual_volatility": 0.0,
            "coefficient_of_variation": 0.0, "daily_spending": {}, "weekly_pattern": {},
        }

    def test_no_debits(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100, "date_iso": "2025-01-01"}]
        assert core._compute_temporal_patterns(txns)["trend"] == 0.0

    def test_simple_two_days(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 200, "date_iso": "2025-01-02"},
        ]
        result = core._compute_temporal_patterns(txns)
        # 2025-01-01 Wed, 2025-01-02 Thu -> cv of [100,200] = 0.3333
        assert result["trend"] == 0.0  # ma length < 14
        assert result["seasonality"] == pytest.approx(0.3333, rel=1e-3)
        assert result["residual_volatility"] == pytest.approx(0.3333, rel=1e-3)
        assert result["daily_spending"] == {"2025-01-01": 100, "2025-01-02": 200}


# ============================================================
# _compute_loss_aversion_index — hand-computed exact scores
# ============================================================
class TestLossAversionIndexMutants:
    def test_empty(self) -> None:
        assert core._compute_loss_aversion_index([]) == {
            "score": 0.5, "post_income_velocity": 0.0, "recovery_time_days": 0,
        }

    def test_credits_only(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"}]
        assert core._compute_loss_aversion_index(txns)["score"] == 0.5

    def test_debits_only(self) -> None:
        txns = [{"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-01"}]
        assert core._compute_loss_aversion_index(txns)["score"] == 0.5

    def test_velocity_case(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},  # Rs1000
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-01"},     # Rs300
            {"type": "debit", "amount_paise": 40000, "date_iso": "2025-01-02"},     # Rs400
        ]
        result = core._compute_loss_aversion_index(txns)
        # median_debit = 400; velocity = (300+400)/1000 = 0.7
        # velocity_score = 0.7/1.5 = 0.4667 -> *0.6 = 0.28
        assert result["post_income_velocity"] == pytest.approx(0.7, rel=1e-5)
        assert result["score"] == pytest.approx(0.28, rel=1e-5)
        assert result["recovery_time_days"] == 0
        assert result["large_expense_count"] == 0

    def test_large_expense_recovery(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 40000, "date_iso": "2025-01-02"},
            {"type": "debit", "amount_paise": 2000000, "date_iso": "2025-01-03"},  # Rs20000 > 2*400
        ]
        result = core._compute_loss_aversion_index(txns)
        # large expense Rs20000 within 72h inflates velocity to (300+400+20000)/1000 = 20.7
        # velocity_score clamps to 1.0; recovery=min(30, 20000/400)=30 -> recovery_score=1.0
        # total = 1.0*0.6 + 1.0*0.4 = 1.0
        assert result["large_expense_count"] == 1
        assert result["recovery_time_days"] == 30
        assert result["post_income_velocity"] == pytest.approx(20.7, rel=1e-5)
        assert result["score"] == pytest.approx(1.0, rel=1e-5)


# ============================================================
# _compute_impulsivity_score — hand-computed
# ============================================================
class TestImpulsivityScoreCoreMutants:
    def test_empty(self) -> None:
        assert core._compute_impulsivity_score([]) == {
            "score": 0.5, "micro_txn_ratio": 0.0, "late_night_ratio": 0.0,
        }

    def test_debits_only(self) -> None:
        txns = [{"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-06"}]
        result = core._compute_impulsivity_score(txns)
        assert result["micro_txn_ratio"] == 0.0
        # single Sunday debit -> weekend_ratio=1.0 -> weekend_score=0.3333, others 0
        # score = 0.3333*0.35 = 0.1167
        assert result["score"] == pytest.approx(0.1167, rel=1e-4)

    def test_all_discretionary_weekend(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining"},
        ]
        result = core._compute_impulsivity_score(txns)
        # micro_ratio=1, weekend_ratio=1, disc_ratio=1
        # = 1*0.35 + 0.3333*0.35 + 1*0.30 = 0.7667
        assert result["micro_txn_ratio"] == 1.0
        assert result["discretionary_ratio"] == 1.0
        assert result["score"] == pytest.approx(0.7667, rel=1e-3)
        assert result["micro_txn_count"] == 2


# ============================================================
# _compute_habit_stability_score — hand-computed
# ============================================================
class TestHabitStabilityCoreMutants:
    def test_empty(self) -> None:
        assert core._compute_habit_stability_score([]) == {
            "score": 0.5, "category_cv": 0.0, "recurring_predictability": 0.0,
        }

    def test_debits_only(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"}]
        assert core._compute_habit_stability_score(txns)["score"] == 0.5

    def test_single_category_two_days(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 10000, "date_iso": "2025-01-01", "category": "Food", "description": "X"},
            {"type": "debit", "amount_paise": 10000, "date_iso": "2025-01-02", "category": "Food", "description": "X"},
        ]
        result = core._compute_habit_stability_score(txns)
        # avg_category_cv=0, recurring=0, rhythm cv([1,1])=0 -> rhythm_score=1
        # score = 1*0.40 + 0 + 1*0.30 = 0.70
        assert result["category_cv"] == pytest.approx(0.0, abs=1e-6)
        assert result["recurring_count"] == 0
        assert result["score"] == pytest.approx(0.70, rel=1e-5)


# ============================================================
# _compute_financial_stress_index — hand-computed
# ============================================================
class TestFinancialStressCoreMutants:
    def test_empty(self) -> None:
        assert core._compute_financial_stress_index([]) == {
            "score": 0.5, "balance_volatility": 0.0, "credit_dependency": 0.0,
        }

    def test_no_debits(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"}]
        assert core._compute_financial_stress_index(txns)["score"] == 0.5

    def test_balanced_case(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-02"},
        ]
        result = core._compute_financial_stress_index(txns)
        # running_balance [500, 0]; cv([500,0])=1.0
        # credit_dependency = 1000/1000 = 1.0
        # eom=0; buffer_days = 250/500 = 0.5 -> buffer_score=0.01666
        # stress = 0.5*0.3 + 0.5*0.3 + 0 + (1-0.01666)*0.2 = 0.49666
        assert result["balance_volatility"] == pytest.approx(1.0, rel=1e-5)
        assert result["credit_dependency"] == pytest.approx(1.0, rel=1e-5)
        assert result["eom_depletion_ratio"] == pytest.approx(0.0, abs=1e-6)
        assert result["buffer_days"] == pytest.approx(0.5, rel=1e-5)
        assert result["score"] == pytest.approx(0.4967, rel=1e-4)


# ============================================================
# _compute_savings_discipline_score — hand-computed
# ============================================================
class TestSavingsDisciplineCoreMutants:
    def test_empty(self) -> None:
        assert core._compute_savings_discipline_score([]) == {
            "score": 0.5, "savings_rate": 0.0, "momentum": 0.0,
        }

    def test_single_month(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 80000, "date_iso": "2025-01-15"},
        ]
        result = core._compute_savings_discipline_score(txns)
        # rate = (1000-800)/1000 = 0.2; momentum=0; consistency=1
        assert result["savings_rate"] == pytest.approx(0.2, rel=1e-5)
        assert result["momentum"] == 0.0
        assert result["consistency"] == 1.0
        assert result["score"] == pytest.approx(0.73, rel=1e-4)


# ============================================================
# compute_behavior_profile — end-to-end structure
# ============================================================
class TestComputeBehaviorProfileMutants:
    def _sample_txns(self) -> list[dict]:
        return [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01", "category": "Salary"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining", "description": "X"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-04", "category": "Food & Dining", "description": "X"},
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
        ]

    def test_structure(self) -> None:
        profile = core.compute_behavior_profile(self._sample_txns())
        assert set(profile.keys()) == {
            "temporal_patterns", "behavioral_indices", "risk_signals",
            "confidence", "financial_health_score", "data_quality",
        }
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

    def test_confidence_density(self) -> None:
        txns = self._sample_txns()
        profile = core.compute_behavior_profile(txns)
        # txn_set falls back to recent_transactions (4 txns) -> confidence = 4/200 = 0.02
        assert profile["confidence"] == pytest.approx(0.02, abs=1e-6)
        assert profile["data_quality"]["transactions_analyzed"] == 4

    def test_risk_signals_flags(self) -> None:
        txns = self._sample_txns()
        profile = core.compute_behavior_profile(txns)
        # impulsivity for sample: 2 of 3 debits micro -> micro_ratio=2/3, weekend 2025-01-04 Sat
        # impulsivity ~ 0.35*0.667 + 0.35*0.333 + 0.30*0.667 = 0.233+0.117+0.2 = 0.55
        # high_impulsivity only if >0.7 -> False here
        assert profile["risk_signals"]["high_impulsivity"] is False

    def test_empty_transactions(self) -> None:
        profile = core.compute_behavior_profile([])
        assert profile["confidence"] == 0.0
        assert profile["behavioral_indices"]["loss_aversion"]["score"] == 0.5


# ============================================================
# Edge cases for missing transaction keys (kills default-replacement mutants)
# ============================================================
class TestMissingKeyEdgeCases:
    def test_transaction_missing_date_iso(self) -> None:
        """Test transactions without date_iso key - kills default-replacement mutants in _get_daily_spending_data"""
        txns = [
            {"type": "debit", "amount_paise": 50000},  # missing date_iso
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-01"},
        ]
        # Should not crash and should handle missing date gracefully
        result = core._get_daily_spending_data(txns, "2025-01-01")
        assert isinstance(result, dict)
        assert "2025-01-01" in result
        assert result["2025-01-01"] == 30000

    def test_transaction_missing_type(self) -> None:
        """Test transactions without type key"""
        txns = [
            {"amount_paise": 50000, "date_iso": "2025-01-01"},  # missing type
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-01"},
        ]
        result = core._get_daily_spending_data(txns, "2025-01-01")
        assert isinstance(result, dict)
        assert result.get("2025-01-01") == 30000

    def test_transaction_missing_amount_paise(self) -> None:
        """Test transactions without amount_paise key"""
        txns = [
            {"type": "debit", "date_iso": "2025-01-01"},  # missing amount_paise
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-01"},
        ]
        result = core._get_daily_spending_data(txns, "2025-01-01")
        assert isinstance(result, dict)
        assert result.get("2025-01-01") == 30000

    def test_transaction_with_none_values(self) -> None:
        """Test transactions with None values"""
        txns = [
            {"type": "debit", "amount_paise": None, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-01"},
        ]
        result = core._get_daily_spending_data(txns, "2025-01-01")
        assert isinstance(result, dict)
        assert result.get("2025-01-01") == 30000

    def test_all_credit_transactions(self) -> None:
        """Test with only credit transactions - should return empty dict"""
        txns = [
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "credit", "amount_paise": 50000, "date_iso": "2025-01-02"},
        ]
        result = core._get_daily_spending_data(txns, "2025-01-01")
        assert result == {}

    def test_empty_transaction_list(self) -> None:
        """Test empty transaction list"""
        result = core._get_daily_spending_data([], "2025-01-01")
        assert result == {}


# ============================================================
# _get_monthly_category_spending_data edge cases
# ============================================================
class TestMonthlyCategoryEdgeCases:
    def test_missing_category(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},  # no category
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-15", "category": "Food"},
        ]
        result = core._get_monthly_category_spending_data(txns, "2025-01-01")
        assert isinstance(result, dict)
        # "Food" should be a key in the month dict
        for month_data in result.values():
            assert "Food" in month_data

    def test_missing_date_iso_in_monthly(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 50000},  # missing date_iso
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-15", "category": "Food"},
        ]
        result = core._get_monthly_category_spending_data(txns, "2025-01-01")
        assert isinstance(result, dict)
        for month_data in result.values():
            assert month_data.get("Food") == 30000


# ============================================================
# _get_transaction_stats_data edge cases
# ============================================================
class TestTransactionStatsEdgeCases:
    def test_missing_keys(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 50000},  # missing date_iso
            {"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"},
        ]
        result = core._get_transaction_stats_data(txns, "2025-01-01")
        assert isinstance(result, dict)
        # Keys match the function's return structure
        assert "total_count" in result
        assert "debit_count" in result
        assert "credit_count" in result
        assert "total_debit_paise" in result
        assert "total_credit_paise" in result


# ============================================================
# _parse_date boundary mutants
# ============================================================
class TestParseDateBoundaryMutants:
    def test_invalid_formats(self) -> None:
        assert core._parse_date("not-a-date") is None
        assert core._parse_date("2025/13/01") is None  # invalid month
        assert core._parse_date("2025-02-30") is None  # invalid day
        assert core._parse_date("") is None
        assert core._parse_date(None) is None

    def test_various_valid_formats(self) -> None:
        from datetime import datetime
        assert core._parse_date("2025-01-15") == datetime(2025, 1, 15)
        assert core._parse_date("15/01/2025") == datetime(2025, 1, 15)
        assert core._parse_date("15-01-2025") == datetime(2025, 1, 15)
        assert core._parse_date("15 Jan 2025") == datetime(2025, 1, 15)
        assert core._parse_date("15-Jan-2025") == datetime(2025, 1, 15)
        assert core._parse_date("  2025-01-15  ") == datetime(2025, 1, 15)
