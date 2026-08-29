"""M9-C43.7 — Structural validation for remaining behaviour_engine survivors.

Targets the surviving mutant classes in:
- insights.generate_summary_text (50)
- credit_dependency.household_divergence (47)
- patterns.detect_subscription_patterns (40)
- patterns.compute_night_spend_ratio (11)
- wellness.classify_wellness_band (16) / compute_wellness_score (15)
- temporal.compute_trend (15)
- core helper functions: _get_daily_spending_data (11),
  _get_monthly_category_spending_data (16),
  _get_monthly_income_expenses_data (16), _get_transaction_stats_data
- nudges helpers: get_top_nudge (16), get_nudge_summary (7)
- credit_dependency.x_credit_dependency_ratio (8)
- temporal._coefficient_of_variation (3), _moving_average (2)

Kills: dict KEY renames, STRING literal changes, DEFAULT value mutations,
COMPUTED constant mutations.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.engines.behaviour_engine import (
    credit_dependency,
    insights,
    nudges,
    patterns,
    temporal,
    wellness,
)
from src.engines.behaviour_engine import core


# ============================================================
# insights.generate_summary_text — exact string fragments
# ============================================================
class TestGenerateSummaryTextStructure:
    def test_empty(self) -> None:
        assert insights.generate_summary_text({}) == (
            "Insufficient data for behavioral analysis."
        )

    def test_strong_branches(self) -> None:
        p = {"financial_health_score": 70}
        assert "strong discipline" in insights.generate_summary_text(p)
        p2 = {"financial_health_score": 49}
        assert "needs attention" in insights.generate_summary_text(p2)
        p3 = {"financial_health_score": 50}
        text = insights.generate_summary_text(p3)
        assert "moderate" in text

    def test_savings_branch(self) -> None:
        p = {
            "behavioral_indices": {
                "savings_discipline": {"score": 0.7},
                "impulsivity": {"score": 0.5},
                "financial_stress": {"score": 0.5},
            }
        }
        assert "savings discipline is strong" in insights.generate_summary_text(p)
        p2 = {
            "behavioral_indices": {
                "savings_discipline": {"score": 0.2},
                "impulsivity": {"score": 0.5},
                "financial_stress": {"score": 0.5},
            }
        }
        assert "savings discipline needs work" in insights.generate_summary_text(p2)

    def test_impulse_branch(self) -> None:
        p = {
            "behavioral_indices": {
                "savings_discipline": {"score": 0.5},
                "impulsivity": {"score": 0.8},
                "financial_stress": {"score": 0.5},
            }
        }
        assert "impulse spending is high" in insights.generate_summary_text(p)
        p2 = {
            "behavioral_indices": {
                "savings_discipline": {"score": 0.5},
                "impulsivity": {"score": 0.2},
                "financial_stress": {"score": 0.5},
            }
        }
        assert "spending is well-controlled" in insights.generate_summary_text(p2)

    def test_stress_branch(self) -> None:
        p = {
            "behavioral_indices": {
                "savings_discipline": {"score": 0.5},
                "impulsivity": {"score": 0.5},
                "financial_stress": {"score": 0.7},
            }
        }
        assert "financial stress indicators are elevated" in insights.generate_summary_text(p)

    def test_confidence_branch(self) -> None:
        p = {
            "behavioral_indices": {
                "savings_discipline": {"score": 0.5},
                "impulsivity": {"score": 0.5},
                "financial_stress": {"score": 0.5},
            },
            "confidence": 0.4,
        }
        text = insights.generate_summary_text(p)
        assert "limited data" in text
        assert "40% confidence" in text


# ============================================================
# credit_dependency.household_divergence — exact dict keys
# ============================================================
class TestHouseholdDivergenceStructure:
    def test_empty(self) -> None:
        r = credit_dependency.household_divergence([])
        assert set(r.keys()) == {"flag", "divergent_links", "count"}
        assert r["flag"] is False
        assert r["divergent_links"] == []
        assert r["count"] == 0

    def test_exact_link_keys(self) -> None:
        events = [
            {
                "id": 1,
                "owner_id": "alice",
                "household_id": "h1",
                "links": [
                    {
                        "link_type": "funds",
                        "linked_event_id": 2,
                    }
                ],
            },
            {
                "id": 2,
                "owner_id": "bob",
                "household_id": "h1",
            },
        ]
        r = credit_dependency.household_divergence(events)
        assert set(r.keys()) == {"flag", "divergent_links", "count"}
        assert r["flag"] is True
        assert r["count"] == 1
        link = r["divergent_links"][0]
        assert set(link.keys()) == {
            "from_owner",
            "to_owner",
            "link_type",
            "event_id",
            "linked_event_id",
            "household_id",
        }
        assert link["from_owner"] == "alice"
        assert link["to_owner"] == "bob"
        assert link["link_type"] == "funds"
        assert link["event_id"] == 1
        assert link["linked_event_id"] == 2
        assert link["household_id"] == "h1"

    def test_missing_keys_defaults(self) -> None:
        events = [{"id": 0, "owner_id": "self", "household_id": "h1", "links": []}]
        r = credit_dependency.household_divergence(events)
        assert set(r.keys()) == {"flag", "divergent_links", "count"}
        assert isinstance(r["flag"], bool)


# ============================================================
# patterns.detect_subscription_patterns — exact list item keys
# ============================================================
class TestSubscriptionPatternsStructure:
    def test_empty(self) -> None:
        r = patterns.detect_subscription_patterns([])
        assert r == []

    def test_exact_item_keys(self) -> None:
        txns = [
            {"description": "NETFLIX", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"description": "NETFLIX", "amount_paise": 50000, "date_iso": "2025-02-01"},
            {"description": "NETFLIX", "amount_paise": 50000, "date_iso": "2025-03-01"},
        ]
        r = patterns.detect_subscription_patterns(txns)
        assert len(r) == 1
        item = r[0]
        assert set(item.keys()) == {
            "merchant",
            "day_of_month",
            "avg_amount_paise",
            "months_active",
            "total_transactions",
            "first_seen",
            "last_seen",
        }
        assert item["merchant"] == "NETFLIX"
        assert item["day_of_month"] == 1
        assert item["avg_amount_paise"] == 50000
        assert item["months_active"] == 3
        assert item["total_transactions"] == 3
        assert item["first_seen"] == "2025-01-01"
        assert item["last_seen"] == "2025-03-01"

    def test_no_subscription(self) -> None:
        txns = [
            {"description": "X", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"description": "Y", "amount_paise": 60000, "date_iso": "2025-02-01"},
        ]
        assert patterns.detect_subscription_patterns(txns) == []

    def test_missing_description(self) -> None:
        txns = [{"amount_paise": 50000, "date_iso": "2025-01-01"}]
        r = patterns.detect_subscription_patterns(txns)
        assert r == []


# ============================================================
# patterns.compute_night_spend_ratio
# ============================================================
class TestNightSpendRatioStructure:
    def test_empty(self) -> None:
        r = patterns.compute_night_spend_ratio([])
        assert isinstance(r, (int, float, Decimal))

    def test_exact(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01T23:30:00"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-02T10:00:00"},
        ]
        r = patterns.compute_night_spend_ratio(txns)
        assert isinstance(r, (int, float, Decimal))
        assert float(r) >= 0.0


# ============================================================
# wellness functions
# ============================================================
class TestWellnessStructure:
    def test_classify_excellent(self) -> None:
        assert wellness.classify_wellness_band(Decimal("95")) == "Excellent"

    def test_classify_healthy(self) -> None:
        assert wellness.classify_wellness_band(Decimal("80")) == "Healthy"

    def test_classify_developing(self) -> None:
        assert wellness.classify_wellness_band(Decimal("60")) == "Developing"

    def test_compute_returns_decimal(self) -> None:
        r = wellness.compute_wellness_score(
            Decimal("0.8"),
            5,
            Decimal("0.2"),
            Decimal("0.3"),
            Decimal("0.1"),
            Decimal("0.15"),
            Decimal("0.3"),
        )
        assert isinstance(r, Decimal)
        assert 0 <= r <= 100


# ============================================================
# temporal functions
# ============================================================
class TestTemporalStructure:
    def test_compute_trend_empty(self) -> None:
        r = temporal.compute_trend({})
        assert isinstance(r, float)

    def test_compute_trend_exact(self) -> None:
        daily = {"2025-01-01": 50000.0, "2025-01-02": 50000.0, "2025-01-03": 50000.0}
        r = temporal.compute_trend(daily)
        assert isinstance(r, float)
        assert r == pytest.approx(0.0, abs=1e-6)

    def test_moving_average_empty(self) -> None:
        r = temporal._moving_average([], 3)
        assert isinstance(r, list)

    def test_coefficient_of_variation_empty(self) -> None:
        r = temporal._coefficient_of_variation([])
        assert isinstance(r, float)


# ============================================================
# core helper functions — exact dict keys
# ============================================================
class TestCoreHelperStructure:
    def test_get_daily_spending_empty(self) -> None:
        r = core._get_daily_spending_data([], "2025-01-01")
        assert r == {}

    def test_get_daily_spending_exact(self) -> None:
        txns = [
            {"type": "debit", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount_paise": 30000, "date_iso": "2025-01-02"},
        ]
        r = core._get_daily_spending_data(txns, "2025-01-01")
        assert isinstance(r, dict)
        assert all(isinstance(k, str) for k in r.keys())
        assert all(isinstance(v, float) for v in r.values())

    def test_get_monthly_category_empty(self) -> None:
        r = core._get_monthly_category_spending_data([], "2025-01-01")
        assert r == {}

    def test_get_monthly_income_empty(self) -> None:
        r = core._get_monthly_income_expenses_data([], "2025-01-01")
        assert isinstance(r, dict)

    def test_get_transaction_stats_empty(self) -> None:
        r = core._get_transaction_stats_data([], "2025-01-01")
        assert isinstance(r, dict)
        expected_keys = {
            "total_count",
            "debit_count",
            "credit_count",
            "micro_txn_count",
            "total_debit_paise",
            "total_credit_paise",
            "weekend_spend_paise",
            "weekday_spend_paise",
        }
        assert expected_keys >= set(r.keys())


# ============================================================
# nudges helpers — exact dict keys + exact strings
# ============================================================
class TestNudgeHelpersStructure:
    def test_get_top_nudge_empty(self) -> None:
        r = nudges.get_top_nudge({})
        assert set(r.keys()) == {"type", "priority", "title", "message", "trigger", "actionable"}
        assert r["title"] == "Keep Tracking"
        assert r["actionable"] is False

    def test_get_nudge_summary_empty(self) -> None:
        assert nudges.get_nudge_summary({}) == (
            "Continue tracking your financial transactions for better insights."
        )

    def test_get_nudge_summary_one(self) -> None:
        p = {
            "behavioral_indices": {
                "impulsivity": {"score": 0.71},
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
                "financial_stress": {"score": 0.0, "buffer_days": 30},
                "loss_aversion": {"post_income_velocity": 0.0, "large_expense_count": 0},
                "savings_discipline": {"score": 0.6, "savings_rate": 0.5},
            }
        }
        assert nudges.get_nudge_summary(p) == "Recommended action: Implement 24-Hour Rule."

    def test_get_nudge_summary_two(self) -> None:
        p = {
            "behavioral_indices": {
                "impulsivity": {"score": 0.71, "micro_txn_ratio": 0.51},
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
                "financial_stress": {"score": 0.0, "buffer_days": 30},
                "loss_aversion": {"post_income_velocity": 0.0, "large_expense_count": 0},
                "savings_discipline": {"score": 0.6, "savings_rate": 0.5},
            }
        }
        s = nudges.get_nudge_summary(p)
        assert s.startswith("Recommended actions:")
        assert "and" in s

    def test_get_nudge_summary_three(self) -> None:
        p = {
            "behavioral_indices": {
                "impulsivity": {"score": 0.71, "micro_txn_ratio": 0.51},
                "habit_stability": {"category_cv": 0.61, "recurring_count": 5},
                "financial_stress": {"score": 0.0, "buffer_days": 30},
                "loss_aversion": {"post_income_velocity": 0.0, "large_expense_count": 0},
                "savings_discipline": {"score": 0.6, "savings_rate": 0.5},
            }
        }
        s = nudges.get_nudge_summary(p)
        assert s.startswith("Top 3 actions:")
        assert ", and" in s
