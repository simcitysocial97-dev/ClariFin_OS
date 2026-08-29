"""M9-C43.7 — Exact structural validation for insights.py and nudges.py.

Kills the dominant surviving mutant classes in these two functions:
- dict KEY renames (``"type"`` -> ``"TYPE"``, ``"XXmessageXX"``, ``"value"`` -> renamed)
- STRING LITERAL mutations (``"warning"`` -> ``"WARNING"``, title case changes)
- DEFAULT value mutations (``.get(k, 0)`` -> ``.get(k, 1)``, ``.get(k, {})`` -> ``None``)
- COMPUTED value mutations (``int(v*100)`` -> ``int(v/100)``)

Strategy: assert the EXACT returned dict (key set + exact type/title/message/metric/
value strings) and feed PARTIAL profiles so missing-key defaults are exercised.
"""

from __future__ import annotations

from src.engines.behaviour_engine.insights import (
    generate_behavioral_insights,
)
from src.engines.behaviour_engine.nudges import generate_nudges

EXPECTED_INSIGHT_KEYS = {"type", "title", "message", "metric", "value"}
EXPECTED_NUDGE_KEYS = {
    "type",
    "priority",
    "title",
    "message",
    "trigger",
    "actionable",
}


def _find(insights: list[dict], title: str) -> dict:
    for i in insights:
        if i["title"] == title:
            return i
    raise AssertionError(f"insight title {title!r} not found in {insights}")


def _find_nudge(nudges: list[dict], title: str) -> dict:
    for n in nudges:
        if n["title"] == title:
            return n
    raise AssertionError(f"nudge title {title!r} not found in {nudges}")


# ============================================================
# insights.py — exact key-set + exact value validation
# ============================================================
class TestInsightExactStructure:
    def test_every_insight_has_exact_keys(self) -> None:
        profile = {
            "behavioral_indices": {
                "loss_aversion": {
                    "post_income_velocity": 0.6,
                    "large_expense_count": 5,
                },
                "impulsivity": {
                    "micro_txn_ratio": 0.5,
                    "weekend_ratio": 1.4,
                    "discretionary_ratio": 0.5,
                    "score": 0.8,
                },
                "habit_stability": {"category_cv": 0.6, "recurring_count": 6},
                "financial_stress": {
                    "buffer_days": 3.0,
                    "credit_dependency": 1.5,
                    "eom_depletion_ratio": 0.3,
                    "score": 0.9,
                },
                "savings_discipline": {
                    "savings_rate": -0.1,
                    "momentum": 0.2,
                    "consistency": 0.4,
                    "score": 0.1,
                },
            },
            "risk_signals": {
                "india_specific": {
                    "upi_micro_spend_flag": True,
                    "gambling_flag": True,
                    "gambling_transaction_count": 2,
                    "loan_app_pattern_flag": True,
                    "emi_ratio": 0.5,
                }
            },
            "temporal_patterns": {"trend": 0.2, "volatility": 0.9},
            "financial_health_score": 80,
            "confidence": 0.4,
        }
        insights = generate_behavioral_insights(profile)
        assert len(insights) > 10
        for ins in insights:
            assert set(ins.keys()) == EXPECTED_INSIGHT_KEYS

    def test_post_income_spike_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "loss_aversion": {"post_income_velocity": 0.6, "large_expense_count": 0}
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Post-Income Spending Spike")
        assert ins["type"] == "warning"
        assert ins["title"] == "Post-Income Spending Spike"
        assert ins["metric"] == "post_income_velocity"
        assert ins["value"] == 0.6
        assert ins["message"] == (
            "60% of income is spent within 72 hours of credit. "
            "This indicates loss aversion behavior—spending gains quickly."
        )

    def test_large_expense_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "loss_aversion": {"post_income_velocity": 0.0, "large_expense_count": 5}
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Large Expense Frequency")
        assert ins["type"] == "info"
        assert ins["metric"] == "large_expense_count"
        assert ins["value"] == 5
        assert ins["message"] == (
            "5 expenses exceeded 2x your median spend. Consider building a buffer for these events."
        )

    def test_micro_txn_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "impulsivity": {
                    "micro_txn_ratio": 0.5,
                    "weekend_ratio": 1.0,
                    "discretionary_ratio": 0.0,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "High Micro-Transaction Rate")
        assert ins["type"] == "warning"
        assert ins["metric"] == "micro_txn_ratio"
        assert ins["value"] == 0.5
        assert ins["message"] == (
            "50% of transactions are under ₹500. Small frequent spends often accumulate to significant amounts."
        )

    def test_weekend_premium_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "impulsivity": {
                    "micro_txn_ratio": 0.0,
                    "weekend_ratio": 1.4,
                    "discretionary_ratio": 0.0,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Weekend Spending Premium")
        assert ins["type"] == "info"
        assert ins["metric"] == "weekend_ratio"
        assert ins["value"] == 1.4
        # (1.4 - 1) * 100 = 39.99... -> int() truncates to 39
        assert ins["message"] == (
            "Weekend spending is 39% higher than weekday average. This may indicate discretionary impulse patterns."
        )

    def test_discretionary_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "impulsivity": {
                    "micro_txn_ratio": 0.0,
                    "weekend_ratio": 1.0,
                    "discretionary_ratio": 0.5,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "High Discretionary Spending")
        assert ins["type"] == "warning"
        assert ins["metric"] == "discretionary_ratio"
        assert ins["value"] == 0.5
        assert ins["message"] == (
            "50% of spending is in discretionary categories (dining, entertainment, shopping). Consider setting category limits."
        )

    def test_unstable_habit_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "habit_stability": {"category_cv": 0.6, "recurring_count": 0}
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Unstable Spending Patterns")
        assert ins["type"] == "warning"
        assert ins["metric"] == "category_cv"
        assert ins["value"] == 0.6
        assert ins["message"] == (
            "Category spending varies 60% month-to-month. Higher consistency enables better planning."
        )

    def test_consistent_habit_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "habit_stability": {"category_cv": 0.1, "recurring_count": 0}
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Consistent Spending Habits")
        assert ins["type"] == "positive"
        assert ins["metric"] == "category_cv"
        assert ins["value"] == 0.1
        assert ins["message"] == (
            "Category spending is highly stable (CV: 10%). This indicates strong financial discipline."
        )

    def test_recurring_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "habit_stability": {"category_cv": 0.0, "recurring_count": 6}
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Strong Recurring Pattern")
        assert ins["type"] == "positive"
        assert ins["metric"] == "recurring_count"
        assert ins["value"] == 6
        assert ins["message"] == (
            "6 recurring expense patterns detected. Predictable expenses reduce financial stress."
        )

    def test_low_buffer_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "financial_stress": {
                    "buffer_days": 3.0,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Low Financial Buffer")
        assert ins["type"] == "warning"
        assert ins["metric"] == "buffer_days"
        assert ins["value"] == 3.0
        assert ins["message"] == (
            "Current buffer covers only 3.0 days of expenses. Target: 30 days minimum for financial security."
        )

    def test_healthy_buffer_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "financial_stress": {
                    "buffer_days": 35.0,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Healthy Financial Buffer")
        assert ins["type"] == "positive"
        assert ins["metric"] == "buffer_days"
        assert ins["value"] == 35.0
        assert ins["message"] == (
            "Buffer covers 35 days of expenses. This provides strong financial resilience."
        )

    def test_credit_dependency_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "financial_stress": {
                    "buffer_days": 30,
                    "credit_dependency": 1.5,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "High Credit Dependency")
        assert ins["type"] == "warning"
        assert ins["metric"] == "credit_dependency"
        assert ins["value"] == 1.5
        assert ins["message"] == (
            "Credit inflows are 150% of debit outflows. This may indicate reliance on borrowed funds."
        )

    def test_eom_depletion_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "financial_stress": {
                    "buffer_days": 30,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.3,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "End-of-Month Depletion")
        assert ins["type"] == "warning"
        assert ins["metric"] == "eom_depletion_ratio"
        assert ins["value"] == 0.3
        assert ins["message"] == (
            "30% of monthly spending occurs in the last 5 days. This pattern often indicates cash flow stress."
        )

    def test_negative_savings_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "savings_discipline": {
                    "savings_rate": -0.1,
                    "momentum": 0.0,
                    "consistency": 0.0,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Negative Savings Rate")
        assert ins["type"] == "warning"
        assert ins["metric"] == "savings_rate"
        assert ins["value"] == -0.1
        assert ins["message"] == (
            "Monthly expenses exceed income by 10%. This is unsustainable long-term."
        )

    def test_strong_savings_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "savings_discipline": {
                    "savings_rate": 0.3,
                    "momentum": 0.0,
                    "consistency": 0.0,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Strong Savings Rate")
        assert ins["type"] == "positive"
        assert ins["metric"] == "savings_rate"
        assert ins["value"] == 0.3
        assert ins["message"] == (
            "Saving 30% of income monthly. This exceeds the recommended 20% target."
        )

    def test_declining_savings_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "savings_discipline": {
                    "savings_rate": 0.0,
                    "momentum": -0.2,
                    "consistency": 0.0,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Declining Savings Trend")
        assert ins["type"] == "warning"
        assert ins["metric"] == "momentum"
        assert ins["value"] == -0.2
        assert ins["message"] == (
            "Savings rate dropped 20% compared to previous period. Review recent expense increases."
        )

    def test_improving_savings_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "savings_discipline": {
                    "savings_rate": 0.0,
                    "momentum": 0.2,
                    "consistency": 0.0,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Improving Savings Trend")
        assert ins["type"] == "positive"
        assert ins["metric"] == "momentum"
        assert ins["value"] == 0.2
        assert ins["message"] == (
            "Savings rate improved 20% compared to previous period. Maintain this trajectory."
        )

    def test_inconsistent_savings_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "savings_discipline": {
                    "savings_rate": 0.0,
                    "momentum": 0.0,
                    "consistency": 0.4,
                    "score": 0.0,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Inconsistent Savings")
        assert ins["type"] == "info"
        assert ins["metric"] == "consistency"
        assert ins["value"] == 0.4
        assert ins["message"] == (
            "Only 40% of months had positive savings. Aim for consistency over intensity."
        )

    def test_upi_micro_spend_exact(self) -> None:
        profile = {"risk_signals": {"india_specific": {"upi_micro_spend_flag": True}}}
        ins = _find(generate_behavioral_insights(profile), "UPI Micro-Spend Clustering")
        assert ins["type"] == "warning"
        assert ins["metric"] == "upi_micro_spend_flag"
        assert ins["value"] is True
        assert ins["message"] == (
            "High frequency of small UPI transactions detected. These often accumulate unnoticed. Consider weekly spend reviews."
        )

    def test_gambling_exact(self) -> None:
        profile = {
            "risk_signals": {
                "india_specific": {
                    "gambling_flag": True,
                    "gambling_transaction_count": 2,
                }
            }
        }
        ins = _find(generate_behavioral_insights(profile), "Gaming/Gambling Transactions")
        assert ins["type"] == "warning"
        assert ins["metric"] == "gambling_flag"
        assert ins["value"] is True
        assert ins["message"] == (
            "2 transactions linked to gaming/gambling platforms detected. Monitor for addictive patterns."
        )

    def test_loan_app_exact(self) -> None:
        profile = {"risk_signals": {"india_specific": {"loan_app_pattern_flag": True}}}
        ins = _find(generate_behavioral_insights(profile), "Loan App Activity")
        assert ins["type"] == "warning"
        assert ins["metric"] == "loan_app_pattern_flag"
        assert ins["value"] is True
        assert ins["message"] == (
            "Multiple loan app credits detected. High-frequency borrowing may indicate financial stress."
        )

    def test_emi_burden_exact(self) -> None:
        profile = {"risk_signals": {"india_specific": {"emi_ratio": 0.5}}}
        ins = _find(generate_behavioral_insights(profile), "High EMI Burden")
        assert ins["type"] == "warning"
        assert ins["metric"] == "emi_ratio"
        assert ins["value"] == 0.5
        assert ins["message"] == (
            "EMI payments consume 50% of income. Recommended maximum is 40% for financial stability."
        )

    def test_upward_trend_exact(self) -> None:
        profile = {"temporal_patterns": {"trend": 0.2, "volatility": 0.0}}
        ins = _find(generate_behavioral_insights(profile), "Upward Spending Trend")
        assert ins["type"] == "warning"
        assert ins["metric"] == "trend"
        assert ins["value"] == 0.2
        assert ins["message"] == (
            "Spending trend is up 20% over the past week. Monitor for sustained increases."
        )

    def test_downward_trend_exact(self) -> None:
        profile = {"temporal_patterns": {"trend": -0.2, "volatility": 0.0}}
        ins = _find(generate_behavioral_insights(profile), "Downward Spending Trend")
        assert ins["type"] == "positive"
        assert ins["metric"] == "trend"
        assert ins["value"] == -0.2
        assert ins["message"] == (
            "Spending trend is down 20% over the past week. Keep this momentum."
        )

    def test_volatility_exact(self) -> None:
        profile = {"temporal_patterns": {"trend": 0.0, "volatility": 0.9}}
        ins = _find(generate_behavioral_insights(profile), "High Spending Volatility")
        assert ins["type"] == "info"
        assert ins["metric"] == "volatility"
        assert ins["value"] == 0.9
        assert ins["message"] == (
            "Daily spending varies significantly (CV: 90%). Smoothing expenses can reduce stress."
        )

    def test_strong_health_exact(self) -> None:
        profile = {"financial_health_score": 80}
        ins = _find(generate_behavioral_insights(profile), "Strong Financial Health")
        assert ins["type"] == "positive"
        assert ins["metric"] == "financial_health_score"
        assert ins["value"] == 80
        assert ins["message"] == (
            "Financial Health Score: 80/100. Your financial behavior shows discipline and stability."
        )

    def test_weak_health_exact(self) -> None:
        profile = {"financial_health_score": 30}
        ins = _find(generate_behavioral_insights(profile), "Financial Health Needs Attention")
        assert ins["type"] == "warning"
        assert ins["metric"] == "financial_health_score"
        assert ins["value"] == 30
        assert ins["message"] == (
            "Financial Health Score: 30/100. Multiple behavioral indicators suggest room for improvement."
        )

    def test_limited_confidence_exact(self) -> None:
        profile = {"confidence": 0.4}
        ins = _find(generate_behavioral_insights(profile), "Limited Data for Analysis")
        assert ins["type"] == "info"
        assert ins["metric"] == "confidence"
        assert ins["value"] == 0.4
        assert ins["message"] == (
            "Confidence level: 40%. More transaction history improves insight accuracy."
        )

    def test_missing_keys_defaults(self) -> None:
        """Profile with missing behavioral_indices/risk_signals/temporal.
        Kills ``get(k, {})`` -> ``get(k, None)`` default mutants."""
        profile = {"financial_health_score": 50, "confidence": 1.0}
        insights = generate_behavioral_insights(profile)
        # With no behavioural data, only the health-score branch may fire.
        for ins in insights:
            assert set(ins.keys()) == EXPECTED_INSIGHT_KEYS
            assert ins["type"] in ("warning", "positive", "info")
            assert isinstance(ins["title"], str)
            assert isinstance(ins["message"], str)
            assert isinstance(ins["metric"], str)
            assert "value" in ins

    def test_empty_profile_returns_empty(self) -> None:
        assert generate_behavioral_insights({}) == []
        assert generate_behavioral_insights(None) == []


# ============================================================
# nudges.py — exact key-set + exact value validation
# ============================================================
class TestNudgeExactStructure:
    def test_every_nudge_has_exact_keys(self) -> None:
        profile = {
            "behavioral_indices": {
                "loss_aversion": {"post_income_velocity": 0.7, "large_expense_count": 0},
                "impulsivity": {
                    "micro_txn_ratio": 0.6,
                    "weekend_ratio": 1.0,
                    "discretionary_ratio": 0.0,
                    "score": 0.8,
                },
                "habit_stability": {"category_cv": 0.7, "recurring_count": 2},
                "financial_stress": {
                    "buffer_days": 3,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.8,
                },
                "savings_discipline": {
                    "savings_rate": 0.05,
                    "momentum": 0.0,
                    "consistency": 0.0,
                    "score": 0.2,
                },
            },
            "risk_signals": {
                "india_specific": {
                    "upi_micro_spend_flag": True,
                    "gambling_flag": True,
                    "loan_app_pattern_flag": True,
                    "emi_ratio": 0.6,
                }
            },
            "financial_health_score": 80,
        }
        nudges = generate_nudges(profile)
        assert len(nudges) > 8
        for n in nudges:
            assert set(n.keys()) == EXPECTED_NUDGE_KEYS

    def test_24_hour_rule_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "impulsivity": {
                    "micro_txn_ratio": 0.0,
                    "weekend_ratio": 1.0,
                    "discretionary_ratio": 0.0,
                    "score": 0.8,
                }
            }
        }
        n = _find_nudge(generate_nudges(profile), "Implement 24-Hour Rule")
        assert n["type"] == "friction"
        assert n["priority"] == 1
        assert n["actionable"] is True
        assert n["trigger"] == "impulse_score > 0.7 (current: 0.80)"
        assert n["message"] == (
            "Your impulse score is high. Before any discretionary purchase over ₹500, wait 24 hours. "
            "This simple friction reduces impulse spending by 30%."
        )

    def test_track_micro_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "impulsivity": {
                    "micro_txn_ratio": 0.6,
                    "weekend_ratio": 1.0,
                    "discretionary_ratio": 0.0,
                    "score": 0.0,
                }
            }
        }
        n = _find_nudge(generate_nudges(profile), "Track Micro-Transactions")
        assert n["type"] == "awareness"
        assert n["priority"] == 2
        assert n["actionable"] is True
        assert n["trigger"] == "micro_txn_ratio > 0.5 (current: 0.60)"
        assert n["message"] == (
            "60% of your transactions are under ₹500. Set a daily micro-spend limit (e.g., ₹200/day) and track weekly totals."
        )

    def test_automate_savings_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "savings_discipline": {
                    "savings_rate": 0.0,
                    "momentum": 0.0,
                    "consistency": 0.0,
                    "score": 0.2,
                }
            }
        }
        n = _find_nudge(generate_nudges(profile), "Automate Savings Transfer")
        assert n["type"] == "habit"
        assert n["priority"] == 1
        assert n["actionable"] is True
        assert n["trigger"] == "savings_score < 0.3 (current: 0.20)"
        assert n["message"] == (
            "Set up an automatic transfer of 10% of income to a separate savings account on payday. "
            "Automation removes the decision friction."
        )

    def test_start_10pct_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "savings_discipline": {
                    "savings_rate": 0.05,
                    "momentum": 0.0,
                    "consistency": 0.0,
                    "score": 0.5,
                }
            }
        }
        n = _find_nudge(generate_nudges(profile), "Start with 10% Target")
        assert n["type"] == "goal"
        assert n["priority"] == 2
        assert n["actionable"] is True
        assert n["trigger"] == "savings_rate < 0.1 (current: 0.05)"
        assert n["message"] == (
            "Your current savings rate is below 10%. Start with a modest 10% target and increase by 1% "
            "each month. Small wins build momentum."
        )

    def test_emergency_buffer_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "financial_stress": {
                    "buffer_days": 30,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.8,
                }
            }
        }
        n = _find_nudge(generate_nudges(profile), "Build Emergency Buffer")
        assert n["type"] == "goal"
        assert n["priority"] == 1
        assert n["actionable"] is True
        assert n["trigger"] == "stress_score > 0.6 (current: 0.80)"
        assert n["message"] == (
            "Your financial stress indicators are elevated. Target a 30-day expense buffer. "
            "Current: 30 days. Start with a 7-day goal."
        )

    def test_pause_spend_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "financial_stress": {
                    "buffer_days": 3,
                    "credit_dependency": 0.0,
                    "eom_depletion_ratio": 0.0,
                    "score": 0.0,
                }
            }
        }
        n = _find_nudge(generate_nudges(profile), "Pause Non-Essential Spending")
        assert n["type"] == "friction"
        assert n["priority"] == 1
        assert n["actionable"] is True
        assert n["trigger"] == "buffer_days < 7 (current: 3)"
        assert n["message"] == (
            "Your buffer covers only 3 days. Consider a 2-week pause on discretionary spending to build a safety cushion."
        )

    def test_delay_income_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "loss_aversion": {"post_income_velocity": 0.7, "large_expense_count": 0}
            }
        }
        n = _find_nudge(generate_nudges(profile), "Delay Post-Income Spending")
        assert n["type"] == "friction"
        assert n["priority"] == 2
        assert n["actionable"] is True
        assert n["trigger"] == "post_income_velocity > 0.6 (current: 0.70)"
        assert n["message"] == (
            "You spend 70% of income within 72 hours. Implement a 48-hour waiting period after salary credit "
            "before any discretionary purchase."
        )

    def test_category_budgets_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "habit_stability": {"category_cv": 0.7, "recurring_count": 5}
            }
        }
        n = _find_nudge(generate_nudges(profile), "Set Category Budgets")
        assert n["type"] == "habit"
        assert n["priority"] == 2
        assert n["actionable"] is True
        assert n["trigger"] == "category_cv > 0.6 (current: 0.70)"
        assert n["message"] == (
            "Your spending varies 70% month-to-month. Set fixed monthly budgets for top 3 categories to build predictability."
        )

    def test_recurring_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "habit_stability": {"category_cv": 0.0, "recurring_count": 2}
            }
        }
        n = _find_nudge(generate_nudges(profile), "Identify Recurring Expenses")
        assert n["type"] == "awareness"
        assert n["priority"] == 3
        assert n["actionable"] is True
        assert n["trigger"] == "recurring_count < 3 (current: 2)"
        assert n["message"] == (
            "Few recurring expense patterns detected. Review your subscriptions and fixed costs. "
            "Predictable expenses reduce decision fatigue."
        )

    def test_upi_limit_exact(self) -> None:
        profile = {"risk_signals": {"india_specific": {"upi_micro_spend_flag": True}}}
        n = _find_nudge(generate_nudges(profile), "Set UPI Daily Limit")
        assert n["type"] == "friction"
        assert n["priority"] == 2
        assert n["actionable"] is True
        assert n["trigger"] == "upi_micro_spend_flag = True"
        assert n["message"] == (
            "High UPI micro-spend activity detected. Consider setting a daily UPI spend limit in your banking app. "
            "Many banks offer this feature."
        )

    def test_review_gaming_exact(self) -> None:
        profile = {"risk_signals": {"india_specific": {"gambling_flag": True}}}
        n = _find_nudge(generate_nudges(profile), "Review Gaming Spending")
        assert n["type"] == "awareness"
        assert n["priority"] == 1
        assert n["actionable"] is True
        assert n["trigger"] == "gambling_flag = True"
        assert n["message"] == (
            "Gaming/gambling transactions detected. These platforms are designed for engagement. "
            "Set strict monthly limits or consider self-exclusion options."
        )

    def test_review_loan_app_exact(self) -> None:
        profile = {"risk_signals": {"india_specific": {"loan_app_pattern_flag": True}}}
        n = _find_nudge(generate_nudges(profile), "Review Loan App Usage")
        assert n["type"] == "awareness"
        assert n["priority"] == 1
        assert n["actionable"] is True
        assert n["trigger"] == "loan_app_pattern_flag = True"
        assert n["message"] == (
            "Multiple loan app credits detected. These often carry high interest rates. "
            "Consider consolidating or building an alternative credit buffer."
        )

    def test_reduce_emi_exact(self) -> None:
        profile = {"risk_signals": {"india_specific": {"emi_ratio": 0.6}}}
        n = _find_nudge(generate_nudges(profile), "Reduce EMI Burden")
        assert n["type"] == "goal"
        assert n["priority"] == 1
        assert n["actionable"] is True
        assert n["trigger"] == "emi_ratio > 0.5 (current: 0.60)"
        assert n["message"] == (
            "EMI payments are 60% of income. Target: under 40%. Consider prepaying high-interest loans or refinancing."
        )

    def test_set_stretch_goals_exact(self) -> None:
        profile = {"financial_health_score": 80}
        n = _find_nudge(generate_nudges(profile), "Set Stretch Goals")
        assert n["type"] == "goal"
        assert n["priority"] == 3
        assert n["actionable"] is True
        assert n["trigger"] == "health_score >= 70 (current: 80)"
        assert n["message"] == (
            "Your financial health score is 80/100. You're ready for stretch goals: increase savings rate by "
            "5% or build a 6-month emergency fund."
        )

    def test_consider_investment_exact(self) -> None:
        profile = {
            "behavioral_indices": {
                "savings_discipline": {
                    "savings_rate": 0.5,
                    "momentum": 0.0,
                    "consistency": 0.0,
                    "score": 0.8,
                }
            }
        }
        n = _find_nudge(generate_nudges(profile), "Consider Investment")
        assert n["type"] == "goal"
        assert n["priority"] == 3
        assert n["actionable"] is True
        assert n["trigger"] == "savings_score > 0.7 (current: 0.80)"
        assert n["message"] == (
            "Your savings discipline is strong. Consider moving excess savings to investment vehicles "
            "(FD, mutual funds) for better returns."
        )

    def test_missing_keys_defaults(self) -> None:
        """Nudges built from a profile missing behavioural sub-keys.
        Kills ``get(k, {})`` -> ``get(k, None)`` default mutants."""
        profile = {"financial_health_score": 50, "confidence": 1.0}
        nudges = generate_nudges(profile)
        for n in nudges:
            assert set(n.keys()) == EXPECTED_NUDGE_KEYS
            assert n["type"] in ("habit", "friction", "goal", "awareness")
            assert isinstance(n["title"], str)
            assert isinstance(n["message"], str)
            assert isinstance(n["trigger"], str)
            assert n["priority"] in (1, 2, 3)
            assert n["actionable"] in (True, False)

    def test_empty_profile_returns_empty(self) -> None:
        assert generate_nudges({}) == []
        assert generate_nudges(None) == []
