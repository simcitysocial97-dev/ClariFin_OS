"""Golden characterization tests for common_calculations.

M9-C45.5 — locks the exact structured output contract of
compute_behavioral_insights (a multi-capability shared module). The existing
tests assert membership/properties; these lock the precise insight title,
description text, severity, icon and formatting so that any behavior-changing
mutation (string label, arithmetic percentage, formatting, threshold) is
detected without manufacturing test-only mutants.

Honesty rules:
  * Assertions express real financial-insight contracts (spend-up/down text,
    ₹ formatting, severity levels), not mutant-killing contrivances.
  * The C43-E1 production defect (compute_is_large avg*250000) is NOT pinned;
    compute_is_large is excluded from characterization (human authorization
    required to fix production; existing tests already document its behavior).
"""

from src.common.calculations import compute_behavioral_insights


def test_golden_category_spend_up_exact_output():
    txns = [
        {"type": "debit", "amount_paise": 100000, "month_key": "2026-01", "category": "Food"},
        {"type": "debit", "amount_paise": 100000, "month_key": "2026-02", "category": "Food"},
        {"type": "debit", "amount_paise": 200000, "month_key": "2026-02", "category": "Food"},
    ]
    got = compute_behavioral_insights(txns)
    assert {
        "title": "Food Spending Up",
        "description": "You spent 200% more on Food this month",
        "severity": "warning",
        "icon": "trending-up",
    } in got


def test_golden_category_spend_down_exact_output():
    txns = [
        {"type": "debit", "amount_paise": 300000, "month_key": "2026-01", "category": "Travel"},
        {"type": "debit", "amount_paise": 100000, "month_key": "2026-02", "category": "Travel"},
    ]
    got = compute_behavioral_insights(txns)
    assert {
        "title": "Travel Savings",
        "description": "You spent 66% less on Travel",
        "severity": "positive",
        "icon": "trending-down",
    } in got


def test_golden_overall_spend_up_exact_output():
    txns = [
        {"type": "debit", "amount_paise": 100000, "month_key": "2026-01", "category": "Food"},
        {"type": "debit", "amount_paise": 300000, "month_key": "2026-02", "category": "Food"},
        {"type": "debit", "amount_paise": 500000, "month_key": "2026-02", "category": "Rent"},
    ]
    got = compute_behavioral_insights(txns)
    assert {
        "title": "Spending Trending Up",
        "description": "Overall spending is up 700%",
        "severity": "warning",
        "icon": "alert-triangle",
    } in got


def test_golden_largest_expense_inr_format():
    txns = [
        {"type": "debit", "amount_paise": 500000, "month_key": "2026-02", "category": "Rent", "description_display": "Monthly Apartment Rent", "description": "x"},
    ]
    got = compute_behavioral_insights(txns)
    assert {
        "title": "Largest Expense",
        "description": "Your biggest: Monthly Apartment Rent at ₹5,000.00",
        "severity": "info",
        "icon": "zap",
    } in got


def test_golden_empty_no_insights():
    assert compute_behavioral_insights([]) == []
    assert compute_behavioral_insights([{"type": "credit", "amount_paise": 100}]) == []
