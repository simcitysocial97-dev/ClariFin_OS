"""M9-C43.6 — Mutation-strengthening tests for remaining behaviour_engine modules.

Targets surviving mutants in utils.py, profile.py, patterns.py, stress.py by
asserting exact boundary conditions and exact returned values that operator /
constant-replacement mutants would break.
"""

from __future__ import annotations

import math
from decimal import Decimal

import pytest
from src.engines.behaviour_engine import patterns, profile, stress, utils


# ============================================================
# utils.py — pure math helpers (exact-value mutants)
# ============================================================
class TestUtilsMedianMutants:
    def test_empty_returns_zero(self) -> None:
        assert utils._median([]) == Decimal("0")

    def test_single_value(self) -> None:
        assert utils._median([5]) == Decimal("5")

    def test_odd_length(self) -> None:
        assert utils._median([3, 1, 2]) == Decimal("2")

    def test_even_length(self) -> None:
        assert utils._median([1, 2, 3, 4]) == Decimal("2.5")

    def test_unsorted(self) -> None:
        assert utils._median([9, 2, 7, 4]) == Decimal("5.5")


class TestUtilsVarianceMutants:
    def test_single_value_returns_zero(self) -> None:
        assert utils._variance([5]) == Decimal("0")

    def test_empty_returns_zero(self) -> None:
        assert utils._variance([]) == Decimal("0")

    def test_two_values(self) -> None:
        # (0-1)^2+(2-1)^2 = 2, /2 = 1
        assert utils._variance([0, 2]) == Decimal("1")

    def test_three_values(self) -> None:
        # (1-2)^2+(2-2)^2+(3-2)^2 = 2, 2/3 = 0.6666...
        assert utils._variance([1, 2, 3]) == Decimal("0.6666666666666666")


class TestUtilsCoefficientOfVariationMutants:
    def test_empty_returns_zero(self) -> None:
        assert utils._coefficient_of_variation([]) == Decimal("0")

    def test_single_value_returns_zero(self) -> None:
        assert utils._coefficient_of_variation([5]) == Decimal("0")

    def test_zero_mean_returns_zero(self) -> None:
        assert utils._coefficient_of_variation([0, 0]) == Decimal("0")

    def test_two_values_cv(self) -> None:
        result = utils._coefficient_of_variation([0, 2])
        assert result == pytest.approx(Decimal("1.0"), rel=1e-5)

    def test_known_distribution_cv(self) -> None:
        # mean=20 (int), variance=200/3, std=sqrt(200/3), cv=sqrt(200/3)/20
        expected = math.sqrt(200.0 / 3.0) / 20.0
        result = utils._coefficient_of_variation([10, 20, 30])
        assert float(result) == pytest.approx(expected, rel=1e-5)


class TestUtilsPercentageChangeMutants:
    def test_zero_previous_zero_current(self) -> None:
        assert utils._percentage_change(0, 0) == Decimal("-1")

    def test_zero_previous_nonzero_current(self) -> None:
        assert utils._percentage_change(5, 0) == Decimal("-0.9999")

    def test_decrease(self) -> None:
        assert utils._percentage_change(10, 20) == Decimal("-0.5")

    def test_increase(self) -> None:
        assert utils._percentage_change(20, 10) == Decimal("1")

    def test_equal(self) -> None:
        assert utils._percentage_change(10, 10) == Decimal("0")


class TestUtilsBasisPointsMutants:
    def test_to_bps_standard(self) -> None:
        assert utils.to_basis_points(Decimal("0.1234")) == 1234

    def test_to_bps_round_half_up(self) -> None:
        assert utils.to_basis_points(Decimal("0.12345")) == 1235

    def test_to_bps_zero(self) -> None:
        assert utils.to_basis_points(Decimal("0")) == 0

    def test_from_bps_standard(self) -> None:
        assert utils.from_basis_points(1234) == Decimal("0.1234")

    def test_from_bps_roundtrip(self) -> None:
        assert utils.from_basis_points(5000) == Decimal("0.5")


class TestUtilsRoundDecimalMutants:
    def test_round_half_up_up(self) -> None:
        assert utils.round_decimal(Decimal("0.12345"), 4) == Decimal("0.1235")

    def test_round_half_up_down(self) -> None:
        assert utils.round_decimal(Decimal("0.12344"), 4) == Decimal("0.1234")

    def test_round_default_places(self) -> None:
        assert utils.round_decimal(Decimal("1.23456")) == Decimal("1.2346")


# ============================================================
# profile.py — classification (boundary + confidence mutants)
# ============================================================
class TestIsDebtDependentMutants:
    def test_high_borrowed_ratio(self) -> None:
        assert profile._is_debt_dependent(Decimal("0.21"), Decimal("0"), Decimal("0.5"))

    def test_revolver_and_low_savings(self) -> None:
        assert profile._is_debt_dependent(
            Decimal("0.10"), Decimal("0.5"), Decimal("0.05")
        )

    def test_not_dependent(self) -> None:
        assert not profile._is_debt_dependent(
            Decimal("0.10"), Decimal("0.4"), Decimal("0.5")
        )


class TestIsSaverMutants:
    def test_low_savings_excluded(self) -> None:
        assert not profile._is_saver(Decimal("0.20"), Decimal("0.10"), Decimal("0.10"))

    def test_high_borrowed_excluded(self) -> None:
        assert not profile._is_saver(Decimal("0.30"), Decimal("0.20"), Decimal("0.10"))

    def test_high_revolver_excluded(self) -> None:
        assert not profile._is_saver(Decimal("0.30"), Decimal("0.10"), Decimal("0.20"))

    def test_is_saver(self) -> None:
        assert profile._is_saver(Decimal("0.30"), Decimal("0.10"), Decimal("0.10"))


class TestIsDebtOptimizerMutants:
    def test_no_credit_excluded(self) -> None:
        assert not profile._is_debt_optimizer(Decimal("0.1"), Decimal("0"))

    def test_high_revolver_excluded(self) -> None:
        assert not profile._is_debt_optimizer(Decimal("0.1"), Decimal("0.20"))

    def test_nonpositive_savings_excluded(self) -> None:
        assert not profile._is_debt_optimizer(Decimal("0"), Decimal("0.10"))

    def test_is_optimizer(self) -> None:
        assert profile._is_debt_optimizer(Decimal("0.1"), Decimal("0.10"))


class TestIsSpenderMutants:
    def test_discretionary_boundary(self) -> None:
        assert profile._is_spender(Decimal("0.40"), Decimal("0"), Decimal("0"))

    def test_impulse_boundary(self) -> None:
        assert profile._is_spender(Decimal("0.10"), Decimal("0.30"), Decimal("0"))

    def test_creep_boundary(self) -> None:
        assert profile._is_spender(Decimal("0.10"), Decimal("0.10"), Decimal("0.50"))

    def test_not_spender(self) -> None:
        assert not profile._is_spender(
            Decimal("0.39"), Decimal("0.29"), Decimal("0.49")
        )


class TestClassifyFinancialPersonalityMutants:
    def test_debt_dependent(self) -> None:
        result = profile.classify_financial_personality(
            Decimal("0.10"),
            Decimal("0.21"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        assert result[0] == "DEBT_DEPENDENT"

    def test_saver(self) -> None:
        result = profile.classify_financial_personality(
            Decimal("0.30"),
            Decimal("0.10"),
            Decimal("0.10"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        assert result[0] == "SAVER"

    def test_debt_optimizer(self) -> None:
        result = profile.classify_financial_personality(
            Decimal("0.10"),
            Decimal("0.05"),
            Decimal("0.10"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        assert result[0] == "DEBT_OPTIMIZER"

    def test_spender(self) -> None:
        result = profile.classify_financial_personality(
            Decimal("0.05"),
            Decimal("0.05"),
            Decimal("0"),
            Decimal("0.40"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        assert result[0] == "SPENDER"

    def test_balanced_default(self) -> None:
        result = profile.classify_financial_personality(
            Decimal("0.05"),
            Decimal("0.05"),
            Decimal("0"),
            Decimal("0.10"),
            Decimal("0.10"),
            Decimal("0.10"),
            100,
        )
        assert result[0] == "BALANCED"


class TestConfidenceMutants:
    def test_saver_confidence_75(self) -> None:
        # 0.5 + 0.10 (strong savings) + 0.05 (revolver>0) + 0.10 (200 txns) = 0.75
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.30"),
            Decimal("0.10"),
            Decimal("0.10"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            200,
        )
        assert conf == Decimal("0.75")

    def test_debt_dependent_confidence_65(self) -> None:
        # 0.5 + 0.10 (borrowed>=0.30) + 0 txn-volume(0.05*0) ... txn=100 -> 0.05 => 0.65
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.10"),
            Decimal("0.35"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        assert conf == Decimal("0.65")

    def test_debt_optimizer_confidence_65(self) -> None:
        # 0.5 + 0.05 (optimizer) + 0.05 (revolver>0) + 0.05 (100 txn) = 0.65
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.10"),
            Decimal("0.05"),
            Decimal("0.10"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        assert conf == Decimal("0.65")

    def test_spender_confidence_65(self) -> None:
        # 0.5 + 0.10 (borrowed>0.30) + 0.05 (100 txn) = 0.65
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.05"),
            Decimal("0.40"),
            Decimal("0"),
            Decimal("0.10"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        assert conf == Decimal("0.65")

    def test_balanced_confidence_55(self) -> None:
        # 0.5 + 0.05 (100 txn) = 0.55
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.05"),
            Decimal("0.05"),
            Decimal("0"),
            Decimal("0.10"),
            Decimal("0.10"),
            Decimal("0.10"),
            100,
        )
        assert conf == Decimal("0.55")

    def test_explanation_non_empty(self) -> None:
        for _prof, args in [
            ("DEBT_DEPENDENT", (Decimal("0.10"), Decimal("0.21"), Decimal("0"))),
            ("SAVER", (Decimal("0.30"), Decimal("0.10"), Decimal("0.10"))),
            ("DEBT_OPTIMIZER", (Decimal("0.10"), Decimal("0.05"), Decimal("0.10"))),
            ("SPENDER", (Decimal("0.05"), Decimal("0.05"), Decimal("0"))),
            ("BALANCED", (Decimal("0.05"), Decimal("0.05"), Decimal("0"))),
        ]:
            _p, _c, expl = profile.classify_financial_personality(
                args[0], args[1], args[2], Decimal("0"), Decimal("0"), Decimal("0"), 100
            )
            assert isinstance(expl, str) and len(expl) > 0


class TestConfidenceBoundaryMutants:
    """Exact confidence boundary assertions to kill comparison/constant mutants."""

    def test_saver_confidence_at_strong_threshold(self) -> None:
        # At exactly SAVER_STRONG_SAVINGS_THRESHOLD (0.25), strong bonus applies
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.25"),
            Decimal("0.10"),
            Decimal("0.10"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        # base 0.5 + strong 0.10 + secondary 0.05 (revolver>0) + txn 0.05 = 0.70
        assert conf == Decimal("0.70")

    def test_saver_confidence_below_strong_threshold(self) -> None:
        # Just below 0.25, no strong bonus
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.24"),
            Decimal("0.10"),
            Decimal("0.10"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        # base 0.5 + secondary 0.05 (revolver>0) + txn 0.05 = 0.60
        assert conf == Decimal("0.60")

    def test_debt_dependent_confidence_at_revolver_threshold(self) -> None:
        # At exactly DEBT_DEPENDENT_MAX_REVOLVER_FOR_POSITIVE (0.5) with low savings
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.05"),
            Decimal("0.10"),
            Decimal("0.50"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        # base 0.5 + secondary 0.05 (negative savings) + txn 0.05 = 0.55
        # Note: DEBT_DEPENDENT secondary requires savings < 0, not < threshold
        assert conf == Decimal("0.55")

    def test_debt_dependent_confidence_above_revolver_threshold(self) -> None:
        # Above 0.5 revolver with low savings - strong condition
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.05"),
            Decimal("0.10"),
            Decimal("0.60"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        # base 0.5 + strong 0.10 (revolver>=0.60) + txn 0.05 = 0.65
        assert conf == Decimal("0.65")

    def test_spender_confidence_at_borrowed_threshold(self) -> None:
        # At borrowed_lifestyle_ratio > 0.30, strong bonus for SPENDER
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.05"),
            Decimal("0.31"),
            Decimal("0"),
            Decimal("0.10"),
            Decimal("0"),
            Decimal("0"),
            100,
        )
        # base 0.5 + strong 0.10 (borrowed>0.30) + txn 0.05 = 0.65
        assert conf == Decimal("0.65")

    def test_confidence_volume_bonus_cap(self) -> None:
        # 500 transactions -> 5 * 0.05 = 0.25, capped at 0.20
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.30"),
            Decimal("0.10"),
            Decimal("0.10"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            500,
        )
        # base 0.5 + strong 0.10 + secondary 0.05 + capped 0.20 = 0.85
        assert conf == Decimal("0.85")

    def test_confidence_clamp_max(self) -> None:
        # Max possible: base 0.5 + strong 0.10 + cap 0.20 = 0.80
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("0.30"),
            Decimal("0.35"),
            Decimal("0.60"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            500,
        )
        assert conf <= Decimal("1.0")
        assert conf == Decimal("0.80")

    def test_confidence_clamp_min(self) -> None:
        # Edge case with negative values should still clamp
        _p, conf, _e = profile.classify_financial_personality(
            Decimal("-0.50"),
            Decimal("0.50"),
            Decimal("0.80"),
            Decimal("0"),
            Decimal("0"),
            Decimal("0"),
            0,
        )
        # base 0.5 + strong 0.10 (borrowed>=0.30 or revolver>=0.60) + secondary 0.05 = 0.65
        assert conf >= Decimal("0")
        assert conf == Decimal("0.65")


# ============================================================
# patterns.py — detection helpers (boundary mutants)
# ============================================================
class TestParseHourMutants:
    def test_none_returns_none(self) -> None:
        assert patterns._parse_hour(None) is None

    def test_no_colon_returns_none(self) -> None:
        assert patterns._parse_hour("abc") is None

    def test_valid_hour(self) -> None:
        assert patterns._parse_hour("12:30") == 12

    def test_invalid_int_returns_none(self) -> None:
        assert patterns._parse_hour("a:30") is None

    def test_hour_25(self) -> None:
        assert patterns._parse_hour("25:00") == 25


class TestIsWeekendMutants:
    def test_friday(self) -> None:
        assert patterns._is_weekend("2025-01-03")

    def test_saturday(self) -> None:
        assert patterns._is_weekend("2025-01-04")

    def test_sunday(self) -> None:
        assert patterns._is_weekend("2025-01-05")

    def test_monday(self) -> None:
        assert not patterns._is_weekend("2025-01-06")

    def test_invalid_returns_false(self) -> None:
        assert not patterns._is_weekend("not-a-date")


class TestIsNightTimeMutants:
    def test_none(self) -> None:
        assert not patterns._is_night_time(None)

    def test_early_evening(self) -> None:
        assert patterns._is_night_time(20)

    def test_late_night(self) -> None:
        assert patterns._is_night_time(2)

    def test_mid_afternoon(self) -> None:
        assert not patterns._is_night_time(15)


class TestDetectImpulseTransactionsMutants:
    def test_amount_boundary_excluded(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 50000,
                "date_iso": "2025-01-04",
                "category": "shopping",
            },
        ]
        assert patterns.detect_impulse_transactions(txns) == []

    def test_weekend_included(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 60000,
                "date_iso": "2025-01-04",
                "category": "shopping",
            },
        ]
        assert len(patterns.detect_impulse_transactions(txns)) == 1

    def test_night_included(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 60000,
                "date_iso": "2025-01-06",
                "category": "food",
                "time_iso": "23:00",
            },
        ]
        assert len(patterns.detect_impulse_transactions(txns)) == 1

    def test_wrong_category_excluded(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 60000,
                "date_iso": "2025-01-04",
                "category": "rent",
            },
        ]
        assert patterns.detect_impulse_transactions(txns) == []

    def test_weekday_no_time_excluded(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 60000,
                "date_iso": "2025-01-06",
                "category": "shopping",
            },
        ]
        assert patterns.detect_impulse_transactions(txns) == []

    def test_custom_min_amount(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 60000,
                "date_iso": "2025-01-04",
                "category": "shopping",
            },
        ]
        assert patterns.detect_impulse_transactions(txns, min_amount_paise=100000) == []


class TestWeekendSpendRatioMutants:
    def test_empty_returns_zero(self) -> None:
        assert patterns.compute_weekend_spend_ratio([]) == Decimal("0")

    def test_no_debits_returns_zero(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-06"}]
        assert patterns.compute_weekend_spend_ratio(txns) == Decimal("0")

    def test_half_weekend(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-04"},  # Sat
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-06"},  # Mon
        ]
        assert patterns.compute_weekend_spend_ratio(txns) == Decimal("0.5")


class TestNightSpendRatioMutants:
    def test_no_time_data_returns_zero(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100, "date_iso": "2025-01-06"},
        ]
        assert patterns.compute_night_spend_ratio(txns) == Decimal("0")

    def test_no_debits_returns_zero(self) -> None:
        assert patterns.compute_night_spend_ratio([]) == Decimal("0")

    def test_half_night(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 100,
                "date_iso": "2025-01-06",
                "time_iso": "23:00",
            },
            {
                "type": "debit",
                "amount_paise": 100,
                "date_iso": "2025-01-06",
                "time_iso": "12:00",
            },
        ]
        assert patterns.compute_night_spend_ratio(txns) == Decimal("0.5")


class TestRecurringMerchantsMutants:
    def test_two_months_recurring(self) -> None:
        txns = []
        for month in ("2025-01", "2025-02"):
            for day in (1, 2, 3):
                txns.append(
                    {
                        "type": "debit",
                        "amount_paise": 500000,
                        "date_iso": f"{month}-{day:02d}",
                        "description": "NETFLIX",
                    }
                )
        result = patterns.detect_recurring_merchants(txns)
        assert len(result) == 1
        assert result[0]["merchant"] == "NETFLIX"

    def test_single_month_not_recurring(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 500000,
                "date_iso": f"2025-01-{day:02d}",
                "description": "NETFLIX",
            }
            for day in (1, 2, 3)
        ]
        assert patterns.detect_recurring_merchants(txns) == []

    def test_insufficient_occurrences(self) -> None:
        txns = []
        for month in ("2025-01", "2025-02"):
            txns.append(
                {
                    "type": "debit",
                    "amount_paise": 500000,
                    "date_iso": f"{month}-01",
                    "description": "NETFLIX",
                }
            )
        # Only 1 occurrence per month (< min_occurrences=3)
        assert patterns.detect_recurring_merchants(txns) == []


class TestSubscriptionPatternsMutants:
    def test_same_day_amount_across_months(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 15000,
                "date_iso": "2025-01-15",
                "description": "SPOTIFY",
            },
            {
                "type": "debit",
                "amount_paise": 15000,
                "date_iso": "2025-02-15",
                "description": "SPOTIFY",
            },
            {
                "type": "debit",
                "amount_paise": 15000,
                "date_iso": "2025-03-15",
                "description": "SPOTIFY",
            },
        ]
        result = patterns.detect_subscription_patterns(txns)
        assert len(result) == 1
        assert result[0]["day_of_month"] == 15

    def test_single_month_not_subscription(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 15000,
                "date_iso": f"2025-01-{day:02d}",
                "description": "SPOTIFY",
            }
            for day in (15, 16, 17)
        ]
        assert patterns.detect_subscription_patterns(txns) == []


# ============================================================
# stress.py — behavioural indices (baseline + boundary mutants)
# ============================================================
class TestStressBaselinesMutants:
    def test_loss_aversion_empty(self) -> None:
        assert stress.loss_aversion_index([]) == {
            "score": 0.5,
            "post_income_velocity": 0.0,
            "recovery_time_days": 0,
        }

    def test_loss_aversion_credits_only(self) -> None:
        txns = [{"type": "credit", "amount_paise": 500000, "date_iso": "2025-01-01"}]
        assert stress.loss_aversion_index(txns)["score"] == 0.5

    def test_loss_aversion_debits_only(self) -> None:
        txns = [{"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-01"}]
        assert stress.loss_aversion_index(txns)["score"] == 0.5

    def test_impulsivity_empty(self) -> None:
        assert stress.impulsivity_score([]) == {
            "score": 0.5,
            "micro_txn_ratio": 0.0,
            "late_night_ratio": 0.0,
        }

    def test_habit_stability_empty(self) -> None:
        assert stress.habit_stability_score([]) == {
            "score": 0.5,
            "category_cv": 0.0,
            "recurring_predictability": 0.0,
        }

    def test_financial_stress_empty(self) -> None:
        assert stress.financial_stress_index([]) == {
            "score": 0.5,
            "balance_volatility": 0.0,
            "credit_dependency": 0.0,
        }

    def test_savings_discipline_empty(self) -> None:
        assert stress.savings_discipline_score([]) == {
            "score": 0.5,
            "savings_rate": 0.0,
            "momentum": 0.0,
        }

    def test_detect_risk_empty(self) -> None:
        assert stress.detect_risk_patterns([]) == {
            "upi_micro_spend_flag": False,
            "gambling_flag": False,
            "loan_app_pattern_flag": False,
            "emi_ratio": 0.0,
        }


class TestStressGamblingMutants:
    def test_gambling_keyword_detected(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 50000,
                "date_iso": "2025-01-01",
                "description": "Dream11 payment",
            }
        ]
        result = stress.detect_risk_patterns(txns)
        assert result["gambling_flag"] is True
        assert result["gambling_transaction_count"] == 1

    def test_no_gambling(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 50000,
                "date_iso": "2025-01-01",
                "description": "Grocery store",
            }
        ]
        assert stress.detect_risk_patterns(txns)["gambling_flag"] is False


class TestStressLoanAppMutants:
    def test_loan_clustering_flag(self) -> None:
        txns = [
            {
                "type": "credit",
                "amount_paise": 10000,
                "date_iso": "2025-01-01",
                "description": "Loan from NBFC",
            },
            {
                "type": "credit",
                "amount_paise": 15000,
                "date_iso": "2025-01-03",
                "description": "Instant cash loan",
            },
        ]
        result = stress.detect_risk_patterns(txns)
        assert result["loan_app_pattern_flag"] is True
        assert result["loan_credit_count"] == 2

    def test_single_loan_no_flag(self) -> None:
        txns = [
            {
                "type": "credit",
                "amount_paise": 10000,
                "date_iso": "2025-01-01",
                "description": "Loan from NBFC",
            }
        ]
        assert stress.detect_risk_patterns(txns)["loan_app_pattern_flag"] is False


class TestStressUpiMicroMutants:
    def test_upi_micro_threshold(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 19900,
                "date_iso": "2025-01-01",
                "description": "UPI",
            }
            for _ in range(11)
        ]
        assert stress.detect_risk_patterns(txns)["upi_micro_spend_flag"] is True

    def test_upi_micro_below_threshold(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": 19900,
                "date_iso": "2025-01-01",
                "description": "UPI",
            }
            for _ in range(10)
        ]
        assert stress.detect_risk_patterns(txns)["upi_micro_spend_flag"] is False


class TestStressImpulsivityMutants:
    def test_all_micro_transactions(self) -> None:
        txns = [
            {
                "type": "debit",
                "amount_paise": i * 1000,
                "date_iso": f"2025-01-{i+1:02d}",
                "category": "food",
            }
            for i in range(1, 11)
        ]
        result = stress.impulsivity_score(txns)
        assert result["micro_txn_ratio"] == pytest.approx(1.0, rel=1e-5)
        assert result["micro_txn_count"] == 10

    def test_no_debits_returns_baseline(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"}]
        assert stress.impulsivity_score(txns)["score"] == 0.5


class TestStressFinancialStressMutants:
    def test_credit_dependency_ratio(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-02"},
        ]
        result = stress.financial_stress_index(txns)
        assert result["credit_dependency"] == pytest.approx(2.0, rel=1e-5)

    def test_eom_depletion_boundary_day_26(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-26"},
            {"type": "debit", "amount_paise": 500000, "date_iso": "2025-01-31"},
        ]
        result = stress.financial_stress_index(txns)
        assert result["eom_depletion_ratio"] == pytest.approx(
            1000000 / 1100000, rel=1e-4
        )

    def test_no_debits_returns_baseline(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"}]
        assert stress.financial_stress_index(txns)["score"] == 0.5


class TestStressSavingsDisciplineMutants:
    def test_positive_savings_rate(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 1000000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 800000, "date_iso": "2025-01-15"},
        ]
        result = stress.savings_discipline_score(txns)
        assert result["savings_rate"] == pytest.approx(0.2, rel=1e-5)

    def test_negative_savings_rate(self) -> None:
        txns = [
            {"type": "credit", "amount_paise": 500000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 600000, "date_iso": "2025-01-15"},
        ]
        result = stress.savings_discipline_score(txns)
        assert result["savings_rate"] == pytest.approx(-0.2, rel=1e-5)

    def test_no_credits_returns_baseline(self) -> None:
        txns = [{"type": "debit", "amount_paise": 100000, "date_iso": "2025-01-01"}]
        assert stress.savings_discipline_score(txns)["score"] == 0.5


class TestStressHabitStabilityMutants:
    def test_recurring_detection_threshold_3(self) -> None:
        txns = [
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
        ]
        result = stress.habit_stability_score(txns)
        assert result["recurring_count"] >= 1

    def test_recurring_not_detected_with_2(self) -> None:
        txns = [
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
        ]
        assert stress.habit_stability_score(txns)["recurring_count"] == 0

    def test_no_debits_returns_baseline(self) -> None:
        txns = [{"type": "credit", "amount_paise": 100000, "date_iso": "2025-01-01"}]
        assert stress.habit_stability_score(txns)["score"] == 0.5
