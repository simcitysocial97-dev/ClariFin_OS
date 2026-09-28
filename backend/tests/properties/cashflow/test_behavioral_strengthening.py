"""Behavioral strengthening tests for the Cashflow Engine (M9-C42.23 Batch 2).

These tests pin precise, domain-meaningful financial semantics so that
incorrect implementations become detectable under mutation testing:

  * cash_surplus = income - expense + credit_funded
  * true_savings = income - expense - fees
  * liability_adjusted_savings = true_savings - liability_increase
  * net_worth_impact = asset_change - liability_increase
  * fee_estimate = max(0, event_amount - asset_change) for cash advances
  * credit_dependency_ratio = credit_funded / expense (0 when expense == 0)
  * effective_liquidity_cost_annualized = total_fees * 12
  * month_classification boundary semantics (surplus / deficit-covered / deficit)

Assertions use concrete paise values derived directly from the documented
contract. They are deterministic and do not depend on time, randomness, or
external services.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from src.engines.cashflow_engine import (
    MonthClassification,
    compute_monthly_cashflow,
)


def _run(
    income: int = 0,
    expense: int = 0,
    events: list[dict[str, Any]] | None = None,
    scope: str = "household",
    owner_id: str = "self",
) -> dict[str, Any]:
    cash_summary = {"income_paise": income, "expense_paise": expense}
    return compute_monthly_cashflow(
        cash_summary=cash_summary,
        financial_events=events or [],
        scope=scope,
        owner_id=owner_id,
    )


def test_no_events_cash_surplus_true_savings_and_classification() -> None:
    """With no events, surplus == true_savings == income - expense."""
    r = _run(income=100000, expense=40000)
    assert r["cash_surplus"] == 60000
    assert r["true_savings"] == 60000
    assert r["liability_adjusted_savings"] == 60000
    assert r["net_worth_impact"] == 0
    assert r["total_fees_paise"] == 0
    assert r["total_credit_advance_paise"] == 0
    assert r["credit_dependency_ratio"] == 0.0
    assert r["effective_liquidity_cost_annualized"] == 0
    assert r["month_classification"] == MonthClassification.SURPLUS


def test_zero_cash_surplus_without_credit_is_deficit() -> None:
    """At exactly zero surplus with no credit events, classification is deficit."""
    r = _run(income=10000, expense=10000)
    assert r["cash_surplus"] == 0
    assert r["month_classification"] == MonthClassification.DEFICIT


def test_credit_advance_records_fee_liability_and_credit_funded() -> None:
    """A cash advance contributes to fees, liability, and credit-funded cash."""
    events = [
        {
            "event_type": "cash_advance",
            "amount_paise": 50000,
            "asset_change_paise": 45000,
            "expense_paise": 0,
            "income_paise": 0,
        }
    ]
    r = _run(events=events)
    # cash_surplus = 0 - 0 + credit_funded(45000)
    assert r["cash_surplus"] == 45000
    # fee = max(0, amount - asset_change) = 5000
    assert r["total_fees_paise"] == 5000
    # true_savings = income - expense - fees = -5000
    assert r["true_savings"] == -5000
    # liability_adjusted = true_savings - liability_increase(50000) = -55000
    assert r["liability_adjusted_savings"] == -55000
    # net_worth_impact = asset_change(45000) - liability_increase(50000) = -5000
    assert r["net_worth_impact"] == -5000
    # annualized cost = fees * 12
    assert r["effective_liquidity_cost_annualized"] == 60000
    assert r["total_credit_advance_paise"] == 45000
    # surplus cash but credit events present -> still classified surplus (else branch)
    assert r["month_classification"] == MonthClassification.SURPLUS


def test_deficit_classification_without_credit() -> None:
    """Negative surplus without credit events is a plain deficit."""
    r = _run(income=0, expense=10000)
    assert r["cash_surplus"] == -10000
    assert r["month_classification"] == MonthClassification.DEFICIT


def test_deficit_covered_by_credit_classification() -> None:
    """Negative surplus with credit events is deficit-covered-by-credit."""
    events = [
        {
            "event_type": "cash_advance",
            "amount_paise": 6000,
            "asset_change_paise": 5000,
            "expense_paise": 0,
            "income_paise": 0,
        }
    ]
    r = _run(income=0, expense=10000, events=events)
    assert r["cash_surplus"] == -5000
    assert r["month_classification"] == MonthClassification.DEFICIT_COVERED_BY_CREDIT


def test_surplus_with_credit_events_classified_surplus() -> None:
    """Positive surplus with credit events falls through to surplus (else branch)."""
    events = [
        {
            "event_type": "cash_advance",
            "amount_paise": 6000,
            "asset_change_paise": 5000,
            "expense_paise": 0,
            "income_paise": 0,
        }
    ]
    r = _run(income=100000, expense=0, events=events)
    assert r["cash_surplus"] == 105000
    assert r["month_classification"] == MonthClassification.SURPLUS


def test_credit_dependency_ratio_with_expense() -> None:
    """credit_dependency_ratio = credit_funded / expense."""
    events = [
        {
            "event_type": "cash_advance",
            "amount_paise": 6000,
            "asset_change_paise": 5000,
            "expense_paise": 0,
            "income_paise": 0,
        }
    ]
    r = _run(income=0, expense=10000, events=events)
    assert r["credit_dependency_ratio"] == Decimal("0.5")


def test_zero_expense_yields_zero_credit_dependency_ratio() -> None:
    """When expense is zero, the ratio is defined as 0 (no division by zero)."""
    events = [
        {
            "event_type": "cash_advance",
            "amount_paise": 50000,
            "asset_change_paise": 45000,
            "expense_paise": 0,
            "income_paise": 0,
        }
    ]
    r = _run(income=0, expense=0, events=events)
    assert r["credit_dependency_ratio"] == 0.0


def test_liability_increase_records_liability_without_fee() -> None:
    """A liability_increase event adds liability and asset change but no fee."""
    events = [
        {
            "event_type": "liability_increase",
            "amount_paise": 20000,
            "asset_change_paise": 0,
            "expense_paise": 0,
            "income_paise": 0,
        }
    ]
    r = _run(events=events)
    # asset_change is 0 -> not counted as credit-funded advance
    assert r["total_credit_advance_paise"] == 0
    assert r["total_fees_paise"] == 0
    # liability_increase contributes to liability but not to credit_funded
    assert r["liability_adjusted_savings"] == -20000
    assert r["net_worth_impact"] == -20000
    assert r["month_classification"] == MonthClassification.DEFICIT_COVERED_BY_CREDIT


def test_non_credit_event_only_affects_asset_change() -> None:
    """Non-credit events affect only net worth via asset_change."""
    events = [
        {
            "event_type": "repayment",
            "amount_paise": 0,
            "asset_change_paise": -5000,
            "expense_paise": 0,
            "income_paise": 0,
        }
    ]
    r = _run(events=events)
    assert r["total_credit_advance_paise"] == 0
    assert r["total_fees_paise"] == 0
    assert r["net_worth_impact"] == -5000
    assert r["month_classification"] == MonthClassification.DEFICIT
