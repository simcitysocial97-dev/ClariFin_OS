"""M9-C43.6 — Coverage + mutation-strengthening for insights.py and nudges.py.

Exercises every threshold branch with boundary values and asserts exact
titles/values so operator and constant-replacement mutants are killed.
"""

from __future__ import annotations

from src.engines.behaviour_engine.insights import (
    generate_behavioral_insights,
    generate_summary_text,
)
from src.engines.behaviour_engine.nudges import (
    generate_nudges,
    get_nudge_summary,
    get_top_nudge,
)

BASE_PROFILE = {
    "behavioral_indices": {
        "loss_aversion": {
            "post_income_velocity": 0.0,
            "large_expense_count": 0,
        },
        "impulsivity": {
            "micro_txn_ratio": 0.0,
            "weekend_ratio": 1.0,
            "discretionary_ratio": 0.0,
            "score": 0.0,
        },
        "habit_stability": {
            "category_cv": 0.0,
            "recurring_count": 0,
        },
        "financial_stress": {
            "buffer_days": 30,
            "credit_dependency": 0.0,
            "eom_depletion_ratio": 0.0,
            "score": 0.0,
        },
        "savings_discipline": {
            "savings_rate": 0.0,
            "momentum": 0.0,
            "consistency": 0.0,
            "score": 0.0,
        },
    },
    "risk_signals": {"india_specific": {}},
    "temporal_patterns": {"trend": 0.0, "volatility": 0.0},
    "financial_health_score": 50,
    "confidence": 1.0,
}


def _titles(items: list[dict]) -> set[str]:
    return {i["title"] for i in items}


# ============================================================
# insights.py — full branch coverage
# ============================================================
class TestInsightsFullBranchMutants:
    def test_empty_profile(self) -> None:
        assert generate_behavioral_insights({}) == []
        assert generate_behavioral_insights(None) == []

    def test_loss_aversion_velocity(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.51,
                    "large_expense_count": 0,
                },
            },
        }
        insights = generate_behavioral_insights(p)
        assert "Post-Income Spending Spike" in _titles(insights)

    def test_large_expense_count(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.0,
                    "large_expense_count": 4,
                },
            },
        }
        insights = generate_behavioral_insights(p)
        assert "Large Expense Frequency" in _titles(insights)

    def test_micro_txn_ratio(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "micro_txn_ratio": 0.41,
                },
            },
        }
        assert "High Micro-Transaction Rate" in _titles(generate_behavioral_insights(p))

    def test_weekend_ratio(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "weekend_ratio": 1.31,
                },
            },
        }
        assert "Weekend Spending Premium" in _titles(generate_behavioral_insights(p))

    def test_discretionary_ratio(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "discretionary_ratio": 0.41,
                },
            },
        }
        assert "High Discretionary Spending" in _titles(generate_behavioral_insights(p))

    def test_category_cv_high(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.51, "recurring_count": 0},
            },
        }
        assert "Unstable Spending Patterns" in _titles(generate_behavioral_insights(p))

    def test_category_cv_low(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.19, "recurring_count": 0},
            },
        }
        assert "Consistent Spending Habits" in _titles(generate_behavioral_insights(p))

    def test_recurring_count(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
            },
        }
        assert "Strong Recurring Pattern" in _titles(generate_behavioral_insights(p))

    def test_buffer_days_low(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "buffer_days": 6,
                },
            },
        }
        assert "Low Financial Buffer" in _titles(generate_behavioral_insights(p))

    def test_buffer_days_high(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "buffer_days": 31,
                },
            },
        }
        assert "Healthy Financial Buffer" in _titles(generate_behavioral_insights(p))

    def test_credit_dependency(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "credit_dependency": 1.21,
                },
            },
        }
        assert "High Credit Dependency" in _titles(generate_behavioral_insights(p))

    def test_eom_depletion(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "eom_depletion_ratio": 0.26,
                },
            },
        }
        assert "End-of-Month Depletion" in _titles(generate_behavioral_insights(p))

    def test_savings_rate_negative(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "savings_rate": -0.1,
                },
            },
        }
        assert "Negative Savings Rate" in _titles(generate_behavioral_insights(p))

    def test_savings_rate_positive(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "savings_rate": 0.21,
                },
            },
        }
        assert "Strong Savings Rate" in _titles(generate_behavioral_insights(p))

    def test_momentum_negative(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "momentum": -0.11,
                },
            },
        }
        assert "Declining Savings Trend" in _titles(generate_behavioral_insights(p))

    def test_momentum_positive(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "momentum": 0.11,
                },
            },
        }
        assert "Improving Savings Trend" in _titles(generate_behavioral_insights(p))

    def test_consistency_low(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "consistency": 0.49,
                },
            },
        }
        assert "Inconsistent Savings" in _titles(generate_behavioral_insights(p))

    def test_upi_risk(self) -> None:
        p = {
            **BASE_PROFILE,
            "risk_signals": {"india_specific": {"upi_micro_spend_flag": True}},
        }
        assert "UPI Micro-Spend Clustering" in _titles(generate_behavioral_insights(p))

    def test_gambling_risk(self) -> None:
        p = {
            **BASE_PROFILE,
            "risk_signals": {
                "india_specific": {
                    "gambling_flag": True,
                    "gambling_transaction_count": 2,
                }
            },
        }
        assert "Gaming/Gambling Transactions" in _titles(
            generate_behavioral_insights(p)
        )

    def test_loan_app_risk(self) -> None:
        p = {
            **BASE_PROFILE,
            "risk_signals": {"india_specific": {"loan_app_pattern_flag": True}},
        }
        assert "Loan App Activity" in _titles(generate_behavioral_insights(p))

    def test_emi_risk(self) -> None:
        p = {**BASE_PROFILE, "risk_signals": {"india_specific": {"emi_ratio": 0.41}}}
        assert "High EMI Burden" in _titles(generate_behavioral_insights(p))

    def test_temporal_trend_up(self) -> None:
        p = {**BASE_PROFILE, "temporal_patterns": {"trend": 0.11, "volatility": 0.0}}
        assert "Upward Spending Trend" in _titles(generate_behavioral_insights(p))

    def test_temporal_trend_down(self) -> None:
        p = {**BASE_PROFILE, "temporal_patterns": {"trend": -0.11, "volatility": 0.0}}
        assert "Downward Spending Trend" in _titles(generate_behavioral_insights(p))

    def test_volatility(self) -> None:
        p = {**BASE_PROFILE, "temporal_patterns": {"trend": 0.0, "volatility": 0.81}}
        assert "High Spending Volatility" in _titles(generate_behavioral_insights(p))

    def test_health_high(self) -> None:
        p = {**BASE_PROFILE, "financial_health_score": 71}
        assert "Strong Financial Health" in _titles(generate_behavioral_insights(p))

    def test_health_low(self) -> None:
        p = {**BASE_PROFILE, "financial_health_score": 39}
        assert "Financial Health Needs Attention" in _titles(
            generate_behavioral_insights(p)
        )

    def test_confidence_low(self) -> None:
        p = {**BASE_PROFILE, "confidence": 0.4}
        assert "Limited Data for Analysis" in _titles(generate_behavioral_insights(p))


class TestInsightsSummaryTextMutants:
    def test_empty(self) -> None:
        assert generate_summary_text({}) == "Insufficient data for behavioral analysis."

    def test_health_strong(self) -> None:
        p = {**BASE_PROFILE, "financial_health_score": 80}
        assert "strong discipline" in generate_summary_text(p)

    def test_health_moderate(self) -> None:
        p = {**BASE_PROFILE, "financial_health_score": 55}
        assert "moderate with room" in generate_summary_text(p)

    def test_health_low(self) -> None:
        p = {**BASE_PROFILE, "financial_health_score": 30}
        assert "needs attention" in generate_summary_text(p)

    def test_savings_strong(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.7,
                },
            },
        }
        assert "savings discipline is strong" in generate_summary_text(p)

    def test_savings_weak(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.2,
                },
            },
        }
        assert "savings discipline needs work" in generate_summary_text(p)

    def test_impulse_high(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.8,
                },
            },
        }
        assert "impulse spending is high" in generate_summary_text(p)

    def test_impulse_low(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.2,
                },
            },
        }
        assert "spending is well-controlled" in generate_summary_text(p)

    def test_stress_elevated(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.7,
                },
            },
        }
        assert "financial stress indicators are elevated" in generate_summary_text(p)

    def test_confidence_low_suffix(self) -> None:
        p = {**BASE_PROFILE, "confidence": 0.4}
        assert "limited data" in generate_summary_text(p)


# ============================================================
# nudges.py — full branch coverage
# ============================================================
class TestNudgesFullBranchMutants:
    def test_empty_profile(self) -> None:
        assert generate_nudges({}) == []
        assert generate_nudges(None) == []

    def test_impulse_high(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.71,
                },
            },
        }
        assert "Implement 24-Hour Rule" in _titles(generate_nudges(p))

    def test_micro_ratio(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "micro_txn_ratio": 0.51,
                },
            },
        }
        assert "Track Micro-Transactions" in _titles(generate_nudges(p))

    def test_savings_score_low(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.29,
                },
            },
        }
        assert "Automate Savings Transfer" in _titles(generate_nudges(p))

    def test_savings_rate_low(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "savings_rate": 0.09,
                },
            },
        }
        assert "Start with 10% Target" in _titles(generate_nudges(p))

    def test_stress_high(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.61,
                    "buffer_days": 5,
                },
            },
        }
        assert "Build Emergency Buffer" in _titles(generate_nudges(p))

    def test_buffer_low(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "buffer_days": 6,
                },
            },
        }
        assert "Pause Non-Essential Spending" in _titles(generate_nudges(p))

    def test_velocity(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.61,
                    "large_expense_count": 0,
                },
            },
        }
        assert "Delay Post-Income Spending" in _titles(generate_nudges(p))

    def test_category_cv(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.61, "recurring_count": 10},
            },
        }
        assert "Set Category Budgets" in _titles(generate_nudges(p))

    def test_recurring_low(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.0, "recurring_count": 2},
            },
        }
        assert "Identify Recurring Expenses" in _titles(generate_nudges(p))

    def test_upi_risk(self) -> None:
        p = {
            **BASE_PROFILE,
            "risk_signals": {"india_specific": {"upi_micro_spend_flag": True}},
        }
        assert "Set UPI Daily Limit" in _titles(generate_nudges(p))

    def test_gambling_risk(self) -> None:
        p = {
            **BASE_PROFILE,
            "risk_signals": {"india_specific": {"gambling_flag": True}},
        }
        assert "Review Gaming Spending" in _titles(generate_nudges(p))

    def test_loan_app_risk(self) -> None:
        p = {
            **BASE_PROFILE,
            "risk_signals": {"india_specific": {"loan_app_pattern_flag": True}},
        }
        assert "Review Loan App Usage" in _titles(generate_nudges(p))

    def test_emi_risk(self) -> None:
        p = {**BASE_PROFILE, "risk_signals": {"india_specific": {"emi_ratio": 0.51}}}
        assert "Reduce EMI Burden" in _titles(generate_nudges(p))

    def test_health_high(self) -> None:
        p = {**BASE_PROFILE, "financial_health_score": 71}
        assert "Set Stretch Goals" in _titles(generate_nudges(p))

    def test_savings_score_high(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.71,
                },
            },
        }
        assert "Consider Investment" in _titles(generate_nudges(p))

    def test_exact_nudge_keys(self) -> None:
        """Assert exact dict keys (type/priority/title/message/trigger/actionable)
        so key-rename mutants are killed."""
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.71,
                },
            },
        }
        nudges = generate_nudges(p)
        n = [x for x in nudges if x["title"] == "Implement 24-Hour Rule"][0]
        assert set(n.keys()) == {
            "type",
            "priority",
            "title",
            "message",
            "trigger",
            "actionable",
        }
        assert n["type"] == "friction"
        assert n["priority"] == 1
        assert n["actionable"] is True
        assert "impulse_score" in n["trigger"]


class TestNudgesBoundaryExactMutants:
    def test_impulse_score_boundary(self) -> None:
        # > 0.7 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.7,
                },
            },
        }
        assert "Implement 24-Hour Rule" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.7001,
                },
            },
        }
        assert "Implement 24-Hour Rule" in _titles(generate_nudges(p2))

    def test_micro_ratio_boundary(self) -> None:
        # > 0.5 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "micro_txn_ratio": 0.5,
                },
            },
        }
        assert "Track Micro-Transactions" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "micro_txn_ratio": 0.5001,
                },
            },
        }
        assert "Track Micro-Transactions" in _titles(generate_nudges(p2))

    def test_savings_score_boundary(self) -> None:
        # < 0.3 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.3,
                },
            },
        }
        assert "Automate Savings Transfer" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.2999,
                },
            },
        }
        assert "Automate Savings Transfer" in _titles(generate_nudges(p2))

    def test_savings_rate_boundary(self) -> None:
        # < 0.1 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "savings_rate": 0.1,
                },
            },
        }
        assert "Start with 10% Target" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "savings_rate": 0.0999,
                },
            },
        }
        assert "Start with 10% Target" in _titles(generate_nudges(p2))

    def test_stress_score_boundary(self) -> None:
        # > 0.6 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.6,
                    "buffer_days": 30,
                },
            },
        }
        assert "Build Emergency Buffer" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.6001,
                    "buffer_days": 30,
                },
            },
        }
        assert "Build Emergency Buffer" in _titles(generate_nudges(p2))

    def test_buffer_days_boundary(self) -> None:
        # < 7 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "buffer_days": 7,
                },
            },
        }
        assert "Pause Non-Essential Spending" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "buffer_days": 6.9,
                },
            },
        }
        assert "Pause Non-Essential Spending" in _titles(generate_nudges(p2))

    def test_velocity_boundary(self) -> None:
        # > 0.6 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.6,
                    "large_expense_count": 0,
                },
            },
        }
        assert "Delay Post-Income Spending" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.6001,
                    "large_expense_count": 0,
                },
            },
        }
        assert "Delay Post-Income Spending" in _titles(generate_nudges(p2))

    def test_category_cv_boundary(self) -> None:
        # > 0.6 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.6, "recurring_count": 10},
            },
        }
        assert "Set Category Budgets" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.6001, "recurring_count": 10},
            },
        }
        assert "Set Category Budgets" in _titles(generate_nudges(p2))

    def test_recurring_boundary(self) -> None:
        # < 3 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.0, "recurring_count": 3},
            },
        }
        assert "Identify Recurring Expenses" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.0, "recurring_count": 2},
            },
        }
        assert "Identify Recurring Expenses" in _titles(generate_nudges(p2))

    def test_health_score_boundary(self) -> None:
        # >= 70 boundary
        p = {**BASE_PROFILE, "financial_health_score": 69.9}
        assert "Set Stretch Goals" not in _titles(generate_nudges(p))
        p2 = {**BASE_PROFILE, "financial_health_score": 70}
        assert "Set Stretch Goals" in _titles(generate_nudges(p2))

    def test_savings_high_boundary(self) -> None:
        # > 0.7 boundary (Consider Investment) - disable other triggers
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.7,
                    "savings_rate": 0.5,
                },
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.0,
                    "micro_txn_ratio": 0.0,
                },
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.0,
                    "buffer_days": 30,
                },
                "loss_aversion": {
                    "post_income_velocity": 0.0,
                    "large_expense_count": 0,
                },
            },
        }
        assert "Consider Investment" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.7001,
                    "savings_rate": 0.5,
                },
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.0,
                    "micro_txn_ratio": 0.0,
                },
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.0,
                    "buffer_days": 30,
                },
                "loss_aversion": {
                    "post_income_velocity": 0.0,
                    "large_expense_count": 0,
                },
            },
        }
        assert "Consider Investment" in _titles(generate_nudges(p2))

    def test_emi_boundary(self) -> None:
        # > 0.5 boundary (Reduce EMI Burden) - disable other triggers
        p = {
            **BASE_PROFILE,
            "risk_signals": {"india_specific": {"emi_ratio": 0.5}},
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.6,
                    "savings_rate": 0.5,
                },
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.0,
                    "micro_txn_ratio": 0.0,
                },
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.0,
                    "buffer_days": 30,
                },
                "loss_aversion": {
                    "post_income_velocity": 0.0,
                    "large_expense_count": 0,
                },
            },
        }
        assert "Reduce EMI Burden" not in _titles(generate_nudges(p))
        p2 = {
            **BASE_PROFILE,
            "risk_signals": {"india_specific": {"emi_ratio": 0.5001}},
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.6,
                    "savings_rate": 0.5,
                },
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.0,
                    "micro_txn_ratio": 0.0,
                },
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.0,
                    "buffer_days": 30,
                },
                "loss_aversion": {
                    "post_income_velocity": 0.0,
                    "large_expense_count": 0,
                },
            },
        }
        assert "Reduce EMI Burden" in _titles(generate_nudges(p2))

    def test_get_top_nudge_exact(self) -> None:
        # boundary: get_top_nudge sorts by priority; verify exact key set
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.71,
                },
            },
        }
        top = get_top_nudge(p)
        assert set(top.keys()) == {
            "type",
            "priority",
            "title",
            "message",
            "trigger",
            "actionable",
        }
        assert top["priority"] == 1

    def test_get_nudge_summary_exact(self) -> None:
        # boundary: 0 nudges -> "Continue tracking"
        assert get_nudge_summary({}) == (
            "Continue tracking your financial transactions for better insights."
        )
        # 1 nudge -> "Recommended action: ..."
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.71,
                },
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.0,
                    "buffer_days": 30,
                },
                "loss_aversion": {
                    "post_income_velocity": 0.0,
                    "large_expense_count": 0,
                },
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.6,
                    "savings_rate": 0.5,
                },
            },
        }
        s1 = get_nudge_summary(p)
        assert s1 == "Recommended action: Implement 24-Hour Rule."
        # 2 nudges -> "Recommended actions: A and B"
        p["behavioral_indices"]["impulsivity"]["micro_txn_ratio"] = 0.5001
        s2 = get_nudge_summary(p)
        assert s2.startswith("Recommended actions:")
        assert "and" in s2
        # 3+ nudges -> "Top 3 actions: ..."
        p["behavioral_indices"]["habit_stability"]["category_cv"] = 0.6001
        s3 = get_nudge_summary(p)
        assert s3.startswith("Top 3 actions:")
        assert ", and" in s3


class TestNudgeHelpersMutants:
    def test_get_top_nudge_empty(self) -> None:
        result = get_top_nudge({})
        assert result["title"] == "Keep Tracking"
        assert result["actionable"] is False

    def test_get_top_nudge_nonempty(self) -> None:
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.71,
                },
            },
        }
        result = get_top_nudge(p)
        assert result["title"] == "Implement 24-Hour Rule"

    def test_get_nudge_summary_empty(self) -> None:
        assert get_nudge_summary({}) == (
            "Continue tracking your financial transactions for better insights."
        )

    def _single_nudge_profile(self) -> dict:
        return {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.71,
                },
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.5,
                    "savings_rate": 0.5,
                },
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
            },
        }

    def test_get_nudge_summary_one(self) -> None:
        p = self._single_nudge_profile()
        assert get_nudge_summary(p) == "Recommended action: Implement 24-Hour Rule."

    def test_get_nudge_summary_two(self) -> None:
        p = self._single_nudge_profile()
        p["behavioral_indices"]["impulsivity"]["micro_txn_ratio"] = 0.51
        summary = get_nudge_summary(p)
        assert summary.startswith("Recommended actions:")
        assert "and" in summary

    def test_get_nudge_summary_three(self) -> None:
        p = self._single_nudge_profile()
        p["behavioral_indices"]["impulsivity"]["micro_txn_ratio"] = 0.51
        p["behavioral_indices"]["habit_stability"]["category_cv"] = 0.61
        summary = get_nudge_summary(p)
        assert summary.startswith("Top 3 actions:")
        assert ", and" in summary


# ============================================================
# Exact boundary value mutants — kill operator/constant replacements
# ============================================================
class TestInsightsBoundaryExactMutants:
    """Exact boundary assertions so > / >= / < / <= mutants are killed."""

    def test_velocity_exact_boundary(self) -> None:
        # velocity == 0.5 is the boundary: > 0.5 must be False at exactly 0.5
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.5,
                    "large_expense_count": 0,
                },
            },
        }
        insights = generate_behavioral_insights(p)
        titles = _titles(insights)
        assert "Post-Income Spending Spike" not in titles

        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.5001,
                    "large_expense_count": 0,
                },
            },
        }
        assert "Post-Income Spending Spike" in _titles(generate_behavioral_insights(p2))

    def test_large_expense_exact_boundary(self) -> None:
        # > 3 is boundary: exactly 3 must not trigger
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.0,
                    "large_expense_count": 3,
                },
            },
        }
        assert "Large Expense Frequency" not in _titles(generate_behavioral_insights(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.0,
                    "large_expense_count": 4,
                },
            },
        }
        assert "Large Expense Frequency" in _titles(generate_behavioral_insights(p2))

    def test_micro_ratio_exact_boundary(self) -> None:
        # > 0.4 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "micro_txn_ratio": 0.4,
                },
            },
        }
        assert "High Micro-Transaction Rate" not in _titles(
            generate_behavioral_insights(p)
        )
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "micro_txn_ratio": 0.4001,
                },
            },
        }
        assert "High Micro-Transaction Rate" in _titles(
            generate_behavioral_insights(p2)
        )

    def test_weekend_ratio_exact_boundary(self) -> None:
        # > 1.3 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "weekend_ratio": 1.3,
                },
            },
        }
        assert "Weekend Spending Premium" not in _titles(
            generate_behavioral_insights(p)
        )
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "weekend_ratio": 1.301,
                },
            },
        }
        assert "Weekend Spending Premium" in _titles(generate_behavioral_insights(p2))

    def test_discretionary_exact_boundary(self) -> None:
        # > 0.4 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "discretionary_ratio": 0.4,
                },
            },
        }
        assert "High Discretionary Spending" not in _titles(
            generate_behavioral_insights(p)
        )
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "discretionary_ratio": 0.4001,
                },
            },
        }
        assert "High Discretionary Spending" in _titles(
            generate_behavioral_insights(p2)
        )

    def test_category_cv_both_branches(self) -> None:
        # > 0.5 triggers warning; < 0.2 triggers positive; between is silent
        p_high = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.5001, "recurring_count": 0},
            },
        }
        assert "Unstable Spending Patterns" in _titles(
            generate_behavioral_insights(p_high)
        )
        p_low = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.1999, "recurring_count": 0},
            },
        }
        assert "Consistent Spending Habits" in _titles(
            generate_behavioral_insights(p_low)
        )
        p_mid = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.35, "recurring_count": 0},
            },
        }
        titles = _titles(generate_behavioral_insights(p_mid))
        assert "Unstable Spending Patterns" not in titles
        assert "Consistent Spending Habits" not in titles

    def test_recurring_boundary(self) -> None:
        # >= 5 triggers positive
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.0, "recurring_count": 5},
            },
        }
        assert "Strong Recurring Pattern" in _titles(generate_behavioral_insights(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "habit_stability": {"category_cv": 0.0, "recurring_count": 4},
            },
        }
        assert "Strong Recurring Pattern" not in _titles(
            generate_behavioral_insights(p2)
        )

    def test_buffer_days_both_branches(self) -> None:
        # < 7 warning; > 30 positive
        p_low = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    "buffer_days": 6.9,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.0,
                },
            },
        }
        assert "Low Financial Buffer" in _titles(generate_behavioral_insights(p_low))
        p_high = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    "buffer_days": 30.1,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.0,
                },
            },
        }
        assert "Healthy Financial Buffer" in _titles(
            generate_behavioral_insights(p_high)
        )

    def test_credit_dependency_boundary(self) -> None:
        # > 1.2 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    "buffer_days": 30,
                    "credit_dependency": 1.2,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.0,
                },
            },
        }
        assert "High Credit Dependency" not in _titles(generate_behavioral_insights(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    "buffer_days": 30,
                    "credit_dependency": 1.2001,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.0,
                },
            },
        }
        assert "High Credit Dependency" in _titles(generate_behavioral_insights(p2))

    def test_eom_ratio_boundary(self) -> None:
        # > 0.25 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    "buffer_days": 30,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.25,
                    "score": 0.0,
                },
            },
        }
        assert "End-of-Month Depletion" not in _titles(generate_behavioral_insights(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "financial_stress": {
                    "buffer_days": 30,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.2501,
                    "score": 0.0,
                },
            },
        }
        assert "End-of-Month Depletion" in _titles(generate_behavioral_insights(p2))

    def test_savings_rate_branches(self) -> None:
        # < 0 negative; > 0.2 strong
        p_neg = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    "savings_rate": -0.0001,
                    "momentum": 0.0,
                    "consistency": 0.0,
                    "score": 0.0,
                },
            },
        }
        assert "Negative Savings Rate" in _titles(generate_behavioral_insights(p_neg))
        p_pos = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    "savings_rate": 0.2001,
                    "momentum": 0.0,
                    "consistency": 0.0,
                    "score": 0.0,
                },
            },
        }
        assert "Strong Savings Rate" in _titles(generate_behavioral_insights(p_pos))

    def test_momentum_branches(self) -> None:
        # < -0.1 declining; > 0.1 improving
        p_dec = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    "savings_rate": 0.0,
                    "momentum": -0.1001,
                    "consistency": 0.0,
                    "score": 0.0,
                },
            },
        }
        assert "Declining Savings Trend" in _titles(generate_behavioral_insights(p_dec))
        p_inc = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    "savings_rate": 0.0,
                    "momentum": 0.1001,
                    "consistency": 0.0,
                    "score": 0.0,
                },
            },
        }
        assert "Improving Savings Trend" in _titles(generate_behavioral_insights(p_inc))

    def test_consistency_boundary(self) -> None:
        # < 0.5 boundary
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    "savings_rate": 0.0,
                    "momentum": 0.0,
                    "consistency": 0.5,
                    "score": 0.0,
                },
            },
        }
        assert "Inconsistent Savings" not in _titles(generate_behavioral_insights(p))
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    "savings_rate": 0.0,
                    "momentum": 0.0,
                    "consistency": 0.4999,
                    "score": 0.0,
                },
            },
        }
        assert "Inconsistent Savings" in _titles(generate_behavioral_insights(p2))

    def test_india_risk_flags(self) -> None:
        p = {
            **BASE_PROFILE,
            "risk_signals": {
                "india_specific": {
                    "upi_micro_spend_flag": True,
                    "gambling_flag": True,
                    "gambling_transaction_count": 3,
                    "loan_app_pattern_flag": True,
                    "emi_ratio": 0.4001,
                }
            },
        }
        titles = _titles(generate_behavioral_insights(p))
        assert "UPI Micro-Spend Clustering" in titles
        assert "Gaming/Gambling Transactions" in titles
        assert "Loan App Activity" in titles
        assert "High EMI Burden" in titles
        # emi_ratio == 0.4 is boundary: must be False
        p2 = {**BASE_PROFILE, "risk_signals": {"india_specific": {"emi_ratio": 0.4}}}
        assert "High EMI Burden" not in _titles(generate_behavioral_insights(p2))

    def test_temporal_branches(self) -> None:
        # trend > 0.1 up; < -0.1 down
        p_up = {
            **BASE_PROFILE,
            "temporal_patterns": {"trend": 0.1001, "volatility": 0.0},
        }
        assert "Upward Spending Trend" in _titles(generate_behavioral_insights(p_up))
        p_down = {
            **BASE_PROFILE,
            "temporal_patterns": {"trend": -0.1001, "volatility": 0.0},
        }
        assert "Downward Spending Trend" in _titles(
            generate_behavioral_insights(p_down)
        )
        # volatility > 0.8
        p_vol = {
            **BASE_PROFILE,
            "temporal_patterns": {"trend": 0.0, "volatility": 0.8001},
        }
        assert "High Spending Volatility" in _titles(
            generate_behavioral_insights(p_vol)
        )

    def test_health_score_branches(self) -> None:
        p_high = {**BASE_PROFILE, "financial_health_score": 70}
        assert "Strong Financial Health" in _titles(
            generate_behavioral_insights(p_high)
        )
        p_low = {**BASE_PROFILE, "financial_health_score": 39.9}
        assert "Financial Health Needs Attention" in _titles(
            generate_behavioral_insights(p_low)
        )
        p_mid = {**BASE_PROFILE, "financial_health_score": 50}
        titles = _titles(generate_behavioral_insights(p_mid))
        assert "Strong Financial Health" not in titles
        assert "Financial Health Needs Attention" not in titles

    def test_confidence_boundary(self) -> None:
        p = {**BASE_PROFILE, "confidence": 0.4999}
        assert "Limited Data for Analysis" in _titles(generate_behavioral_insights(p))
        p2 = {**BASE_PROFILE, "confidence": 0.5}
        assert "Limited Data for Analysis" not in _titles(
            generate_behavioral_insights(p2)
        )

    def test_exact_metric_value_keys(self) -> None:
        """Assert exact 'metric' keys so key-rename mutants are killed."""
        p = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "loss_aversion": {
                    "post_income_velocity": 0.51,
                    "large_expense_count": 0,
                },
            },
        }
        insights = generate_behavioral_insights(p)
        spike = [i for i in insights if i["title"] == "Post-Income Spending Spike"][0]
        assert spike["metric"] == "post_income_velocity"
        assert spike["type"] == "warning"
        assert "value" in spike
        # value must be exactly the float passed
        assert spike["value"] == 0.51


class TestGenerateSummaryTextMutants:
    def test_exact_value_branches(self) -> None:
        p = {**BASE_PROFILE}
        text = generate_summary_text(p)
        # health_score default 50 -> moderate branch
        assert "moderate" in text
        p_high = {**BASE_PROFILE, "financial_health_score": 70}
        assert "strong discipline" in generate_summary_text(p_high)
        p_low = {**BASE_PROFILE, "financial_health_score": 49}
        assert "needs attention" in generate_summary_text(p_low)
        # savings/impulse/stress scores
        p2 = {
            **BASE_PROFILE,
            "behavioral_indices": {
                **BASE_PROFILE["behavioral_indices"],
                "savings_discipline": {
                    **BASE_PROFILE["behavioral_indices"]["savings_discipline"],
                    "score": 0.61,
                },
                "impulsivity": {
                    **BASE_PROFILE["behavioral_indices"]["impulsivity"],
                    "score": 0.71,
                },
                "financial_stress": {
                    **BASE_PROFILE["behavioral_indices"]["financial_stress"],
                    "score": 0.61,
                },
            },
        }
        text2 = generate_summary_text(p2)
        assert "savings discipline is strong" in text2
        assert "impulse spending is high" in text2
        assert "financial stress indicators are elevated" in text2
