"""Tests for Behaviour Engine — India-specific credit dependency signals.

Direct unit tests for src/engines/behaviour_engine/credit_dependency.py.
These tests exercise the previously-0%-coverage module so that mutation
testing can measure behavioral effectiveness instead of reporting no_tests.

All monetary values are integers in paise (₹1.00 = 100 paise).
"""

from decimal import Decimal

from src.engines.behaviour_engine.credit_dependency import (
    _normalize_score,
    artificial_income_flag,
    credit_dependency_ratio,
    debt_rolling_flag,
    financial_stress_index,
    household_divergence,
    liquidity_extraction_frequency,
    revolver_ratio,
    transactor_vs_revolver,
)

# ============================================================
# artificial_income_flag
# ============================================================


def test_artificial_income_detects_cash_advance():
    events = [
        {"id": 1, "event_type": "cash_advance", "amount_paise": 50000},
        {"id": 2, "event_type": "credit_card_cash_advance", "amount_paise": 30000},
    ]
    result = artificial_income_flag(events)
    assert result["flag"] is True
    assert result["artificial_income_paise"] == 80000
    assert set(result["excluded_event_ids"]) == {1, 2}


def test_artificial_income_detects_liability_increase():
    events = [
        {"id": 5, "event_type": "liability_increase", "amount_paise": 120000},
    ]
    result = artificial_income_flag(events)
    assert result["flag"] is True
    assert result["artificial_income_paise"] == 120000
    assert result["excluded_event_ids"] == [5]


def test_artificial_income_ignores_zero_amount():
    events = [
        {"id": 1, "event_type": "cash_advance", "amount_paise": 0},
    ]
    result = artificial_income_flag(events)
    assert result["flag"] is False
    assert result["artificial_income_paise"] == 0
    assert result["excluded_event_ids"] == []


def test_artificial_income_no_matching_events():
    events = [
        {"id": 1, "event_type": "salary", "amount_paise": 100000},
        {"id": 2, "event_type": "expense", "amount_paise": 20000},
    ]
    result = artificial_income_flag(events)
    assert result["flag"] is False
    assert result["artificial_income_paise"] == 0


def test_artificial_income_empty():
    result = artificial_income_flag([])
    assert result["flag"] is False
    assert result["excluded_event_ids"] == []


# ============================================================
# credit_dependency_ratio
# ============================================================


def test_credit_dependency_ratio_normal():
    events = [
        {"event_type": "liability_increase", "liability_change_paise": 40000},
        {"event_type": "liability_increase", "liability_change_paise": 60000},
        {"event_type": "salary", "liability_change_paise": 0},
    ]
    cashflow = {"expense_paise": 200000}
    ratio = credit_dependency_ratio(events, cashflow)
    assert ratio == Decimal("0.5")


def test_credit_dependency_ratio_zero_expenses():
    events = [
        {"event_type": "liability_increase", "liability_change_paise": 40000},
    ]
    cashflow = {"expense_paise": 0}
    ratio = credit_dependency_ratio(events, cashflow)
    assert ratio == Decimal("0")


def test_credit_dependency_ratio_no_credit():
    events = [
        {"event_type": "salary", "liability_change_paise": 0},
    ]
    cashflow = {"expense_paise": 150000}
    ratio = credit_dependency_ratio(events, cashflow)
    assert ratio == Decimal("0")


def test_credit_dependency_ratio_handles_missing_keys():
    events = [{"event_type": "liability_increase"}]
    cashflow = {}
    ratio = credit_dependency_ratio(events, cashflow)
    assert ratio == Decimal("0")


# ============================================================
# transactor_vs_revolver
# ============================================================


def test_transactor_vs_revolver_settled_only():
    events = [
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "settled",
        },
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "settled",
        },
    ]
    result = transactor_vs_revolver(events, "C1")
    assert result["type"] == "transactor"
    assert result["confidence"] == Decimal("1.0")
    assert result["settled_count"] == 2
    assert result["revolving_count"] == 0


def test_transactor_vs_revolver_revolving_only():
    events = [
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "open",
        },
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "rolls_over",
        },
    ]
    result = transactor_vs_revolver(events, "C1")
    assert result["type"] == "revolver"
    assert result["confidence"] == Decimal("1.0")
    assert result["revolving_count"] == 2


def test_transactor_vs_revolver_mixed_revolver_wins():
    events = [
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "settled",
        },
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "open",
        },
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "rolls_over",
        },
    ]
    result = transactor_vs_revolver(events, "C1")
    assert result["type"] == "revolver"
    assert result["revolving_count"] == 2
    assert result["settled_count"] == 1
    assert result["confidence"] == Decimal(str(2 / 3))


def test_transactor_vs_revolver_mixed_transactor_wins():
    events = [
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "settled",
        },
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "settled",
        },
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "open",
        },
    ]
    result = transactor_vs_revolver(events, "C1")
    assert result["type"] == "transactor"
    assert result["confidence"] == Decimal(str(2 / 3))


def test_transactor_vs_revolver_equal_counts():
    events = [
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "settled",
        },
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "open",
        },
    ]
    result = transactor_vs_revolver(events, "C1")
    assert result["type"] == "transactor"
    assert result["confidence"] == Decimal("0.5")


def test_transactor_vs_revolver_filters_other_accounts():
    events = [
        {
            "account_id": "C2",
            "event_type": "liability_increase",
            "lifecycle_state": "open",
        },
        {
            "account_id": "C1",
            "event_type": "liability_increase",
            "lifecycle_state": "settled",
        },
    ]
    result = transactor_vs_revolver(events, "C1")
    assert result["settled_count"] == 1
    assert result["revolving_count"] == 0


# ============================================================
# revolver_ratio
# ============================================================


def test_revolver_ratio_normal():
    events = [
        {
            "event_type": "liability_increase",
            "month_bucket": "2025-01",
            "lifecycle_state": "open",
        },
        {
            "event_type": "liability_increase",
            "month_bucket": "2025-01",
            "lifecycle_state": "settled",
        },
        {
            "event_type": "liability_increase",
            "month_bucket": "2025-02",
            "lifecycle_state": "rolls_over",
        },
    ]
    ratio = revolver_ratio(events)
    # 2 months with credit activity, both have revolving activity
    assert ratio == Decimal("1.0")


def test_revolver_ratio_partial_months():
    events = [
        {
            "event_type": "liability_increase",
            "month_bucket": "2025-01",
            "lifecycle_state": "settled",
        },
        {
            "event_type": "liability_increase",
            "month_bucket": "2025-02",
            "lifecycle_state": "rolls_over",
        },
    ]
    ratio = revolver_ratio(events)
    # 2 months, only 1 has revolving activity
    assert ratio == Decimal("0.5")


def test_revolver_ratio_no_credit_activity():
    events = [
        {"event_type": "salary", "month_bucket": "2025-01"},
    ]
    ratio = revolver_ratio(events)
    assert ratio == Decimal("0")


def test_revolver_ratio_empty():
    assert revolver_ratio([]) == Decimal("0")


# ============================================================
# debt_rolling_flag
# ============================================================


def test_debt_rolling_flag_links():
    events = [
        {"id": 1, "links": [{"link_type": "rolls_over", "linked_event_id": 2}]},
        {"id": 2, "links": [{"link_type": "funds", "linked_event_id": 3}]},
    ]
    result = debt_rolling_flag(events)
    assert result["flag"] is True
    assert result["count"] == 1
    assert result["event_ids"] == [1]


def test_debt_rolling_flag_lifecycle_state():
    events = [
        {"id": 7, "lifecycle_state": "rolls_over"},
        {"id": 8, "lifecycle_state": "settled"},
    ]
    result = debt_rolling_flag(events)
    assert result["flag"] is True
    assert result["event_ids"] == [7]


def test_debt_rolling_flag_no_rolling():
    events = [
        {"id": 1, "links": [{"link_type": "funds"}]},
        {"id": 2, "lifecycle_state": "settled"},
    ]
    result = debt_rolling_flag(events)
    assert result["flag"] is False
    assert result["count"] == 0


def test_debt_rolling_flag_empty():
    result = debt_rolling_flag([])
    assert result["flag"] is False


# ============================================================
# liquidity_extraction_frequency
# ============================================================


def test_liquidity_extraction_frequency_multiple():
    events = [
        {"event_type": "cash_advance", "amount_paise": 10000, "date_iso": "2025-01-01"},
        {
            "event_type": "credit_card_cash_advance",
            "amount_paise": 20000,
            "date_iso": "2025-01-10",
        },
        {"event_type": "cash_advance", "amount_paise": 15000, "date_iso": "2025-01-20"},
    ]
    result = liquidity_extraction_frequency(events)
    assert result["count"] == 3
    assert result["total_paise"] == 45000
    # total_days = (10-1) + (20-10) = 19; code does 19 // len(dates) = 19 // 3 = 6
    assert result["avg_days_between"] == 6


def test_liquidity_extraction_frequency_single():
    events = [
        {"event_type": "cash_advance", "amount_paise": 10000, "date_iso": "2025-01-01"},
    ]
    result = liquidity_extraction_frequency(events)
    assert result["count"] == 1
    assert result["total_paise"] == 10000
    assert result["avg_days_between"] is None


def test_liquidity_extraction_frequency_empty():
    result = liquidity_extraction_frequency([])
    assert result["count"] == 0
    assert result["total_paise"] == 0
    assert result["avg_days_between"] is None


def test_liquidity_extraction_frequency_invalid_dates():
    events = [
        {"event_type": "cash_advance", "amount_paise": 10000, "date_iso": "not-a-date"},
    ]
    result = liquidity_extraction_frequency(events)
    assert result["count"] == 1
    assert result["avg_days_between"] is None


# ============================================================
# _normalize_score
# ============================================================


def test_normalize_score_clamps_high():
    assert _normalize_score(5.0, max_val=1.0) == Decimal("1.0")


def test_normalize_score_clamps_low():
    assert _normalize_score(-2.0, max_val=1.0) == Decimal("0")


def test_normalize_score_zero_max():
    assert _normalize_score(5.0, max_val=0) == Decimal("0")


def test_normalize_score_normal():
    assert _normalize_score(0.5, max_val=2.0) == Decimal("0.25")


# ============================================================
# financial_stress_index
# ============================================================


def test_financial_stress_index_high_stress():
    events = [
        {
            "id": 1,
            "event_type": "liability_increase",
            "lifecycle_state": "rolls_over",
            "links": [{"link_type": "rolls_over"}],
        },
        {
            "id": 2,
            "event_type": "liability_increase",
            "lifecycle_state": "rolls_over",
            "links": [{"link_type": "rolls_over"}],
        },
        {
            "id": 3,
            "event_type": "liability_increase",
            "lifecycle_state": "rolls_over",
            "links": [{"link_type": "rolls_over"}],
        },
        {
            "id": 4,
            "event_type": "cash_advance",
            "amount_paise": 50000,
            "date_iso": "2025-01-01",
        },
        {
            "id": 5,
            "event_type": "cash_advance",
            "amount_paise": 50000,
            "date_iso": "2025-01-05",
        },
        {
            "id": 6,
            "event_type": "cash_advance",
            "amount_paise": 50000,
            "date_iso": "2025-01-10",
        },
        {
            "id": 7,
            "event_type": "cash_advance",
            "amount_paise": 50000,
            "date_iso": "2025-01-15",
        },
        {
            "id": 8,
            "event_type": "cash_advance",
            "amount_paise": 50000,
            "date_iso": "2025-01-20",
        },
    ]
    cashflow = {
        "credit_dependency_ratio": 2.0,
        "cash_surplus": -50000,
        "expense_paise": 100000,
    }
    result = financial_stress_index(events, cashflow)
    assert result["flag"] is True
    assert 0.0 <= float(result["score"]) <= 1.0
    assert "credit_dependency" in result["components"]


def test_financial_stress_index_low_stress():
    events = []
    cashflow = {
        "credit_dependency_ratio": 0.1,
        "cash_surplus": 50000,
        "expense_paise": 100000,
    }
    result = financial_stress_index(events, cashflow)
    assert result["flag"] is False
    assert float(result["score"]) < 0.6


# ============================================================
# household_divergence
# ============================================================


def test_household_divergence_detects_cross_owner():
    events = [
        {
            "id": 1,
            "owner_id": "alice",
            "household_id": "h1",
            "links": [{"link_type": "funds", "linked_event_id": 2}],
        },
        {"id": 2, "owner_id": "bob", "household_id": "h1", "links": []},
    ]
    result = household_divergence(events)
    assert result["flag"] is True
    assert result["count"] == 1
    assert result["divergent_links"][0]["from_owner"] == "alice"
    assert result["divergent_links"][0]["to_owner"] == "bob"


def test_household_divergence_same_owner():
    events = [
        {
            "id": 1,
            "owner_id": "alice",
            "household_id": "h1",
            "links": [{"link_type": "funds", "linked_event_id": 2}],
        },
        {"id": 2, "owner_id": "alice", "household_id": "h1", "links": []},
    ]
    result = household_divergence(events)
    assert result["flag"] is False
    assert result["count"] == 0


def test_household_divergence_settles_link():
    events = [
        {
            "id": 1,
            "owner_id": "alice",
            "household_id": "h1",
            "links": [{"link_type": "settles", "linked_event_id": 2}],
        },
        {"id": 2, "owner_id": "bob", "household_id": "h1", "links": []},
    ]
    result = household_divergence(events)
    assert result["flag"] is True


def test_household_divergence_empty():
    result = household_divergence([])
    assert result["flag"] is False
