"""M9-C43.6 — Mutation-strengthening for credit_dependency.py.

Precise-value + branch-coverage tests for all public functions, killing the
constant/operator mutants in credit_dependency.py's scoring logic.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from src.engines.behaviour_engine import credit_dependency as cd


class TestArtificialIncomeFlagMutants:
    def test_no_artificial(self) -> None:
        r = cd.artificial_income_flag([{"event_type": "salary", "amount_paise": 100000, "id": 1}])
        assert r["flag"] is False
        assert r["artificial_income_paise"] == 0
        assert r["excluded_event_ids"] == []

    def test_detects_cash_advance(self) -> None:
        events = [
            {"event_type": "cash_advance", "amount_paise": 50000, "id": 7},
            {"event_type": "credit_card_cash_advance", "amount_paise": 30000, "id": 8},
            {"event_type": "salary", "amount_paise": 100000, "id": 9},
        ]
        r = cd.artificial_income_flag(events)
        assert r["flag"] is True
        assert r["artificial_income_paise"] == 80000
        assert r["excluded_event_ids"] == [7, 8]

    def test_zero_amount_skipped(self) -> None:
        events = [{"event_type": "cash_advance", "amount_paise": 0, "id": 1}]
        assert cd.artificial_income_flag(events)["flag"] is False


class TestCreditDependencyRatioMutants:
    def test_basic(self) -> None:
        events = [
            {"liability_change_paise": 40000},
            {"liability_change_paise": 0},
            {"liability_change_paise": 10000},
        ]
        assert cd.credit_dependency_ratio(events, {"expense_paise": 100000}) == Decimal("0.5")

    def test_zero_expenses(self) -> None:
        assert cd.credit_dependency_ratio([{"liability_change_paise": 500}], {"expense_paise": 0}) == Decimal("0")

    def test_no_liability(self) -> None:
        assert cd.credit_dependency_ratio([{"liability_change_paise": 0}], {"expense_paise": 100}) == Decimal("0")


class TestTransactorVsRevolverMutants:
    def test_transactor(self) -> None:
        events = [
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "settled", "id": 1},
            {"account_id": "C1", "event_type": "liability_increase", "lifecycle_state": "settled", "id": 2},
        ]
        r = cd.transactor_vs_revolver(events, "C1")
        assert r["type"] == "transactor"
        assert r["confidence"] == Decimal("1.0")
        assert r["settled_count"] == 2

    def test_revolver(self) -> None:
        events = [
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "open", "id": 1},
        ]
        r = cd.transactor_vs_revolver(events, "C1")
        assert r["type"] == "revolver"
        assert r["confidence"] == Decimal("1.0")
        assert r["revolving_count"] == 1

    def test_proportional_revolver(self) -> None:
        events = [
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "open", "id": 1},
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "open", "id": 2},
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "settled", "id": 3},
        ]
        r = cd.transactor_vs_revolver(events, "C1")
        assert r["type"] == "revolver"
        # revolving=2, settled=1 -> 2/3
        assert float(r["confidence"]) == pytest.approx(0.6667, rel=1e-3)

    def test_proportional_transactor(self) -> None:
        events = [
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "settled", "id": 1},
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "settled", "id": 2},
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "open", "id": 3},
        ]
        r = cd.transactor_vs_revolver(events, "C1")
        assert r["type"] == "transactor"
        assert float(r["confidence"]) == pytest.approx(0.6667, rel=1e-3)

    def test_equal_defaults_transactor(self) -> None:
        events = [
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "settled", "id": 1},
            {"account_id": "C1", "event_type": "credit_card_cash_advance", "lifecycle_state": "open", "id": 2},
        ]
        r = cd.transactor_vs_revolver(events, "C1")
        assert r["type"] == "transactor"
        assert r["confidence"] == Decimal("0.5")

    def test_no_events(self) -> None:
        r = cd.transactor_vs_revolver([], "C1")
        assert r["type"] == "transactor"
        assert r["confidence"] == Decimal("0")


class TestRevolverRatioMutants:
    def test_basic(self) -> None:
        events = [
            {"event_type": "credit_card_cash_advance", "month_bucket": "2025-01", "lifecycle_state": "open"},
            {"event_type": "liability_increase", "month_bucket": "2025-01", "lifecycle_state": "settled"},
            {"event_type": "credit_card_cash_advance", "month_bucket": "2025-02", "lifecycle_state": "rolls_over"},
        ]
        assert cd.revolver_ratio(events) == Decimal("1.0")

    def test_no_credit_events(self) -> None:
        assert cd.revolver_ratio([{"event_type": "salary"}]) == Decimal("0")

    def test_partial_month(self) -> None:
        events = [
            {"event_type": "credit_card_cash_advance", "month_bucket": "2025-01", "lifecycle_state": "open"},
            {"event_type": "credit_card_cash_advance", "month_bucket": "2025-01", "lifecycle_state": "settled"},
            {"event_type": "credit_card_cash_advance", "month_bucket": "2025-02", "lifecycle_state": "settled"},
        ]
        # Month 01 has revolving; month 02 doesn't -> 1/2 = 0.5
        assert cd.revolver_ratio(events) == Decimal("0.5")


class TestDebtRollingFlagMutants:
    def test_link_rolls_over(self) -> None:
        events = [{"id": 1, "links": [{"link_type": "rolls_over"}], "lifecycle_state": "open"}]
        r = cd.debt_rolling_flag(events)
        assert r["flag"] is True
        assert r["count"] == 1
        assert r["event_ids"] == [1]

    def test_lifecycle_rolls_over(self) -> None:
        events = [{"id": 2, "links": [], "lifecycle_state": "rolls_over"}]
        assert cd.debt_rolling_flag(events)["flag"] is True

    def test_no_rolling(self) -> None:
        events = [{"id": 3, "links": [{"link_type": "settles"}], "lifecycle_state": "settled"}]
        assert cd.debt_rolling_flag(events)["flag"] is False


class TestLiquidityExtractionMutants:
    def test_basic(self) -> None:
        events = [
            {"event_type": "cash_advance", "amount_paise": 10000, "date_iso": "2025-01-01"},
            {"event_type": "credit_card_cash_advance", "amount_paise": 20000, "date_iso": "2025-01-10"},
        ]
        r = cd.liquidity_extraction_frequency(events)
        assert r["count"] == 2
        assert r["total_paise"] == 30000
        assert r["avg_days_between"] == 4

    def test_empty(self) -> None:
        r = cd.liquidity_extraction_frequency([])
        assert r["count"] == 0
        assert r["avg_days_between"] is None

    def test_single_no_avg(self) -> None:
        events = [{"event_type": "cash_advance", "amount_paise": 10000, "date_iso": "2025-01-01"}]
        r = cd.liquidity_extraction_frequency(events)
        assert r["count"] == 1
        assert r["avg_days_between"] is None


class TestHouseholdDivergenceMutants:
    def test_detects_cross_owner(self) -> None:
        events = [
            {"id": 1, "owner_id": "A", "household_id": "H", "links": [{"link_type": "funds", "linked_event_id": 2}]},
            {"id": 2, "owner_id": "B", "household_id": "H", "links": []},
        ]
        r = cd.household_divergence(events)
        assert r["flag"] is True
        assert r["count"] == 1
        assert r["divergent_links"][0]["from_owner"] == "A"

    def test_same_owner_no_divergence(self) -> None:
        events = [
            {"id": 1, "owner_id": "A", "household_id": "H", "links": [{"link_type": "funds", "linked_event_id": 2}]},
            {"id": 2, "owner_id": "A", "household_id": "H", "links": []},
        ]
        assert cd.household_divergence(events)["flag"] is False

    def test_non_fund_link_ignored(self) -> None:
        events = [
            {"id": 1, "owner_id": "A", "household_id": "H", "links": [{"link_type": "related", "linked_event_id": 2}]},
            {"id": 2, "owner_id": "B", "household_id": "H", "links": []},
        ]
        assert cd.household_divergence(events)["flag"] is False


class TestFinancialStressIndexMutants:
    def test_high_stress(self) -> None:
        events = [
            {"event_type": "credit_card_cash_advance", "amount_paise": 50000,
             "liability_change_paise": 50000, "date_iso": "2025-01-01", "id": 1,
             "links": [{"link_type": "rolls_over", "linked_event_id": 2}]},
            {"event_type": "liability_increase", "liability_change_paise": 30000,
             "date_iso": "2025-01-02", "id": 2},
        ]
        cf = {"credit_dependency_ratio": 1.5, "cash_surplus": -50000, "expense_paise": 100000}
        r = cd.financial_stress_index(events, cf)
        # components: credit_dep 0.75, debt_rolling 0.3333, liquidity 0.2, revolving 0, cashflow 1.0
        # score = 0.30*0.75 + 0.25*0.3333 + 0.20*0.2 + 0.15*0 + 0.10*1.0 = 0.4483
        assert r["score"] == pytest.approx(Decimal("0.4483"), rel=1e-3)
        assert r["components"]["credit_dependency"] == pytest.approx(Decimal("0.75"), rel=1e-3)
        assert r["flag"] is False

    def test_zero_stress(self) -> None:
        cf = {"credit_dependency_ratio": 0.0, "cash_surplus": 100000, "expense_paise": 100000}
        r = cd.financial_stress_index([], cf)
        assert r["score"] == Decimal("0.0")
        assert r["flag"] is False

    def test_high_stress_flag(self) -> None:
        # Force score > 0.6 via extreme credit dependency + cashflow deficit
        cf = {"credit_dependency_ratio": 2.0, "cash_surplus": -100000, "expense_paise": 100000}
        events = [
            {"id": 1, "links": [{"link_type": "rolls_over"}], "lifecycle_state": "open"},
            {"event_type": "cash_advance", "amount_paise": 50000, "date_iso": "2025-01-01"},
            {"event_type": "cash_advance", "amount_paise": 50000, "date_iso": "2025-01-02"},
            {"event_type": "cash_advance", "amount_paise": 50000, "date_iso": "2025-01-03"},
            {"event_type": "cash_advance", "amount_paise": 50000, "date_iso": "2025-01-04"},
            {"event_type": "cash_advance", "amount_paise": 50000, "date_iso": "2025-01-05"},
            {"event_type": "cash_advance", "amount_paise": 50000, "date_iso": "2025-01-06"},
        ]
        r = cd.financial_stress_index(events, cf)
        assert r["flag"] is True
