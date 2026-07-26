"""
Cashflow Engine - Pure calculation library
=========================================

Deterministic monthly cashflow analysis combining transaction aggregates
with financial events (credit conversions, EMI payments, etc.).

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.

Sign Conventions:
- Income/Expense: income_paise positive, expense_paise positive
- asset_change_paise: Positive = asset increase, Negative = asset decrease
- liability_change_paise: Positive = liability increase (borrowing), Negative = decrease (repayment)
- Net worth impact = asset_change_paise - liability_change_paise
"""

from decimal import Decimal
from typing import Any

# ============================================================
# Month Classification Constants
# ============================================================


class MonthClassification:
    SURPLUS = "surplus"
    DEFICIT_COVERED_BY_CREDIT = "deficit_covered_by_credit"
    DEFICIT = "deficit"


# ============================================================
# Core Computation
# ============================================================


def compute_monthly_cashflow(
    cash_summary: dict[str, Any],
    financial_events: list[dict[str, Any]],
    scope: str,
    owner_id: str | None,
) -> dict[str, Any]:
    """
    Compute monthly cashflow analysis with financial events overlay.

    Args:
        cash_summary: Dict with keys:
            - income_paise: Total income from transactions
            - expense_paise: Total expenses from transactions
            - net_paise: Raw income - expense (cash basis)
        financial_events: List of event dicts with keys:
            - amount_paise: Event amount
            - asset_change_paise: Asset impact (can be negative)
            - liability_change_paise: Liability impact (positive=borrowing)
            - expense_paise: Expense component
            - income_paise: Income component
            - event_type: Type of event
            - provider: Source (CRED, etc.)
        scope: "household" or "individual"
        owner_id: Owner filter (None = all owners in household)

    Returns:
        Dict with:
            - cash_surplus: Raw income - expense (cash basis)
            - true_savings: Income - expense - fees - liability_increase
            - liability_adjusted_savings: true_savings - total_liability_increase
            - net_worth_impact: asset_change - liability_change
            - month_classification: surplus / deficit_covered_by_credit / deficit
            - credit_dependency_ratio: Credit-funded expenses / total expenses
            - total_fees_paise: Sum of all event fees
            - total_credit_advance_paise: Sum of credit advance amounts
            - effective_liquidity_cost_annualized: Simple annualized fee estimate
    """
    income = int(cash_summary.get("income_paise", 0) or 0)
    expense = int(cash_summary.get("expense_paise", 0) or 0)

    # Aggregate event impacts
    total_fees = 0
    total_asset_change = 0
    total_liability_increase = 0  # Only positive liability changes (borrowing)
    total_credit_funded = 0

    for event in financial_events:
        event_amount = int(event.get("amount_paise", 0) or 0)
        event_type = event.get("event_type", "")
        asset_change = int(event.get("asset_change_paise", 0) or 0)

        if event_type in (
            "cash_advance",
            "credit_card_cash_advance",
            "liability_increase",
        ):
            # Cash advance adds to credit-funded pool
            total_credit_funded += abs(asset_change)
            total_liability_increase += event_amount

        if (
            event_type in ("cash_advance", "credit_card_cash_advance")
            and event_amount > 0
            and asset_change > 0
        ):
            # Fee = amount_transacted - asset_received
            # For CRED: amount (debit) > asset_change (credit received)
            fee_estimate = event_amount - asset_change
            total_fees += max(0, fee_estimate)

        # Track asset changes
        total_asset_change += asset_change

    # Cash surplus (cash basis): income - expenses + credit advances received
    # Credit advances inflate available cash but create liabilities
    cash_surplus = income - expense + total_credit_funded

    # True savings (accrual basis): income - expenses - fees
    # Fees are the actual cost of credit, not the liability principal
    true_savings = income - expense - total_fees

    # Liability-adjusted: true savings minus liability increases (principal borrowed)
    # This represents the net savings after accounting for borrowed money
    liability_adjusted = true_savings - total_liability_increase

    # Net worth impact = assets - liabilities
    net_worth_impact = total_asset_change - total_liability_increase

    # Month classification
    has_credit_events = any(
        e.get("event_type")
        in ("cash_advance", "credit_card_cash_advance", "liability_increase")
        for e in financial_events
    )

    if cash_surplus > 0 and not has_credit_events:
        month_classification = MonthClassification.SURPLUS
    elif cash_surplus <= 0 and has_credit_events:
        month_classification = MonthClassification.DEFICIT_COVERED_BY_CREDIT
    elif cash_surplus <= 0 and not has_credit_events:
        month_classification = MonthClassification.DEFICIT
    else:
        month_classification = MonthClassification.SURPLUS

    # Credit dependency ratio
    if expense > 0:
        credit_dependency_ratio = Decimal(str(total_credit_funded)) / Decimal(
            str(expense)
        )
    else:
        credit_dependency_ratio = Decimal("0")

    # Effective liquidity cost annualized (simple: fee * 12)
    effective_liquidity_cost_annualized = total_fees * 12

    return {
        "cash_surplus": cash_surplus,
        "true_savings": true_savings,
        "liability_adjusted_savings": liability_adjusted,
        "net_worth_impact": net_worth_impact,
        "month_classification": month_classification,
        "credit_dependency_ratio": round(credit_dependency_ratio, 4),
        "total_fees_paise": total_fees,
        "total_credit_advance_paise": total_credit_funded,
        "effective_liquidity_cost_annualized": effective_liquidity_cost_annualized,
        "scope": scope,
        "owner_id": owner_id,
    }
