"""India-specific credit dependency signals for Behaviour Engine.

All functions are pure - no database access.
All monetary values are integers in paise (₹1.00 = 100 paise).
Consumes financial_events (Phase 6) and cashflow_results (Phase 7).
"""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any

# ============================================================
# Artificial Income Flag
# ============================================================


def artificial_income_flag(
    financial_events: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Detect artificial income from credit-funded inflows.

    Identifies events that represent borrowing rather than true income.
    These are credit-card cash advances and liability increases that create
    artificial cash inflows which should be excluded from income trend analysis.

    Args:
        financial_events: List of financial event dicts. Each event should have
                         event_type, liability_change_paise, amount_paise fields.

    Returns:
        Dict with:
            - flag: bool indicating if artificial income was found
            - artificial_income_paise: Total artificial income amount
            - excluded_event_ids: List of event IDs excluded from income calculation
    """
    # Event types that represent credit-funded inflows (not true income)
    artificial_income_types = {
        "cash_advance",
        "credit_card_cash_advance",
        "liability_increase",
    }

    artificial_amount = 0
    excluded_ids: list[int] = []

    for event in financial_events:
        event_type = event.get("event_type", "")
        if event_type in artificial_income_types:
            # For cash advances, the amount represents borrowed money
            # This inflates available cash but creates liability
            amount = event.get("amount_paise", 0) or 0
            if amount > 0:
                artificial_amount += amount
                event_id = event.get("id", 0)
                if event_id:
                    excluded_ids.append(int(event_id))

    return {
        "flag": len(excluded_ids) > 0,
        "artificial_income_paise": artificial_amount,
        "excluded_event_ids": excluded_ids,
        "explanation": (
            f"Found {len(excluded_ids)} artificial income events "
            f"totaling ₹{artificial_amount / 100:.2f}"
            if excluded_ids
            else "No artificial income detected"
        ),
    }


# ============================================================
# Credit Dependency Ratio
# ============================================================


def credit_dependency_ratio(
    financial_events: list[dict[str, Any]],
    cashflow_results: dict[str, Any],
) -> Decimal:
    """
    Compute ratio of credit-funded expenses to total expenses.

    Uses financial events to identify credit-funded spending and cashflow
    results to get total expenses.

    Args:
        financial_events: List of financial event dicts. Credit-funded expenses
                         come from events with liability_change_paise > 0.
        cashflow_results: Dict with expense_paise for the period.

    Returns:
        Decimal ratio between 0 and 1+. Returns Decimal('0') for zero expenses.
    """
    total_expenses = int(cashflow_results.get("expense_paise", 0) or 0)

    credit_funded = 0
    for event in financial_events:
        liability_change = event.get("liability_change_paise", 0) or 0
        # Positive liability change = borrowing (credit-funded spending)
        if liability_change > 0:
            credit_funded += liability_change

    if total_expenses == 0:
        return Decimal("0")

    return Decimal(str(credit_funded)) / Decimal(str(total_expenses))


# ============================================================
# Transactor vs Revolver Classification
# ============================================================


def transactor_vs_revolver(
    financial_events: list[dict[str, Any]],
    card_account_id: str,
) -> dict[str, Any]:
    """
    Classify credit card behavior as transactor or revolver.

    Uses lifecycle states to determine payment behavior:
    - settled: Evidence toward transactor behavior (paid in full)
    - open/partially_settled/rolls_over: Evidence toward revolver behavior (carrying balance)

    Args:
        financial_events: List of financial event dicts.
        card_account_id: Account ID to filter events for.

    Returns:
        Dict with:
            - type: "transactor" or "revolver"
            - confidence: Decimal confidence score (0-1)
            - settled_count: Number of fully settled events
            - revolving_count: Number of open/partial/rolling events
    """
    # Filter events for this credit card account
    card_events = [
        e
        for e in financial_events
        if e.get("account_id", "") == card_account_id
        and e.get("event_type", "")
        in ("credit_card_cash_advance", "liability_increase")
    ]

    settled_count = 0
    revolving_count = 0

    for event in card_events:
        lifecycle_state = event.get("lifecycle_state", "open")
        if lifecycle_state == "settled":
            settled_count += 1
        elif lifecycle_state in ("open", "partially_settled", "rolls_over"):
            revolving_count += 1

    # Determine classification
    if revolving_count == 0 and settled_count > 0:
        card_type = "transactor"
        confidence = Decimal("1.0")
    elif settled_count == 0 and revolving_count > 0:
        card_type = "revolver"
        confidence = Decimal("1.0")
    elif revolving_count > settled_count:
        card_type = "revolver"
        # Confidence based on proportion
        total = settled_count + revolving_count
        confidence = (
            Decimal(str(revolving_count / total)) if total > 0 else Decimal("0")
        )
    elif settled_count > revolving_count:
        card_type = "transactor"
        total = settled_count + revolving_count
        confidence = Decimal(str(settled_count / total)) if total > 0 else Decimal("0")
    else:
        # Equal counts or no events - default to transactor with low confidence
        card_type = "transactor"
        confidence = (
            Decimal("0.5") if (settled_count + revolving_count) > 0 else Decimal("0")
        )

    return {
        "type": card_type,
        "confidence": confidence,
        "settled_count": settled_count,
        "revolving_count": revolving_count,
    }


# ============================================================
# Revolver Ratio
# ============================================================


def revolver_ratio(
    financial_events: list[dict[str, Any]],
) -> Decimal:
    """
    Compute proportion of months with revolving (non-settled) credit behavior.

    Formula: months_with_open_partial_rolling / total_months_with_credit_activity

    Args:
        financial_events: List of financial event dicts with month_bucket and lifecycle_state.

    Returns:
        Decimal ratio between 0 and 1. Returns Decimal('0') if no credit activity.
    """
    months_with_credit: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "revolving": 0}
    )

    for event in financial_events:
        event_type = event.get("event_type", "")
        if event_type in ("credit_card_cash_advance", "liability_increase"):
            month = event.get("month_bucket", "")
            if month:
                months_with_credit[month]["total"] += 1
                lifecycle_state = event.get("lifecycle_state", "open")
                if lifecycle_state in ("open", "partially_settled", "rolls_over"):
                    months_with_credit[month]["revolving"] += 1

    if not months_with_credit:
        return Decimal("0")

    # Count months with any revolving activity
    revolving_months = sum(1 for m in months_with_credit.values() if m["revolving"] > 0)
    total_months = len(months_with_credit)

    if total_months == 0:
        return Decimal("0")

    return Decimal(str(revolving_months / total_months))


# ============================================================
# Debt Rolling Flag
# ============================================================


def debt_rolling_flag(
    financial_events: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Detect debt-rolling patterns via lineage links.

    A debt-rolling scenario exists when a repayment's funding source traces
    to another cash advance within the lookback window.

    Args:
        financial_events: List of financial event dicts. Events with link_type
                         "rolls_over" in their links indicate rolling debt.

    Returns:
        Dict with:
            - flag: bool indicating if debt rolling detected
            - count: Number of rolling debt events
            - event_ids: List of event IDs involved in rolling patterns
    """
    rolling_event_ids: list[int] = []

    for event in financial_events:
        event_id = event.get("id", 0)

        # Check if this event has any links
        links = event.get("links", [])
        for link in links:
            if link.get("link_type") == "rolls_over":
                if event_id:
                    rolling_event_ids.append(int(event_id))
                break

        # Also check lifecycle_state independently
        lifecycle_state = event.get("lifecycle_state", "")
        if lifecycle_state == "rolls_over" and event_id:
            if int(event_id) not in rolling_event_ids:
                rolling_event_ids.append(int(event_id))

    return {
        "flag": len(rolling_event_ids) > 0,
        "count": len(rolling_event_ids),
        "event_ids": rolling_event_ids,
    }


# ============================================================
# Liquidity Extraction Frequency
# ============================================================


def liquidity_extraction_frequency(
    financial_events: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Count cash advance frequency over time.

    Calculates how often credit card cash advances are taken and the spacing
    between them.

    Args:
        financial_events: List of financial event dicts.

    Returns:
        Dict with:
            - count: Number of cash advance events
            - total_paise: Total amount of cash advances
            - avg_days_between: Average days between advances (None if < 2 events)
    """
    cash_advance_types = ("cash_advance", "credit_card_cash_advance")
    advances = [
        e for e in financial_events if e.get("event_type", "") in cash_advance_types
    ]

    if not advances:
        return {
            "count": 0,
            "total_paise": 0,
            "avg_days_between": None,
        }

    # Sort by date
    advances.sort(key=lambda e: e.get("date_iso", ""))

    total_amount = sum(
        (e.get("amount_paise", 0) or 0) + (e.get("liability_change_paise", 0) or 0)
        for e in advances
    )

    # Calculate average days between
    avg_days = None
    dates = []
    for e in advances:
        date_str = e.get("date_iso", "")
        try:
            dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
        except (ValueError, TypeError):
            pass

    if len(dates) >= 2:
        dates.sort()
        total_days = sum((dates[i + 1] - dates[i]).days for i in range(len(dates) - 1))
        avg_days = total_days // len(dates) if len(dates) > 1 else None

    return {
        "count": len(advances),
        "total_paise": total_amount,
        "avg_days_between": avg_days,
    }


# ============================================================
# Financial Stress Index
# ============================================================

# Scoring constants for stress index components
_STRESS_WEIGHTS = {
    "credit_dependency": 0.30,
    "debt_rolling": 0.25,
    "liquidity_extraction": 0.20,
    "revolving": 0.15,
    "cashflow_deficit": 0.10,
}


def _normalize_score(value: float, max_val: float = 1.0) -> Decimal:
    """Normalize value to 0-1 range with clamping."""
    if max_val == 0:
        return Decimal("0")
    normalized = min(1.0, max(0.0, value / max_val))
    return Decimal(str(round(normalized, 4)))


def financial_stress_index(
    financial_events: list[dict[str, Any]],
    cashflow_results: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute composite financial stress index with explicit component weights.

    Formula:
        score = (0.30 * credit_dependency_component) +
                (0.25 * debt_rolling_component) +
                (0.20 * liquidity_extraction_component) +
                (0.15 * revolving_component) +
                (0.10 * cashflow_deficit_component)

    Each component is normalized to 0-1 range.

    Args:
        financial_events: List of financial event dicts.
        cashflow_results: Dict with cashflow analysis including:
                         - cash_surplus, expense_paise, credit_dependency_ratio

    Returns:
        Dict with:
            - score: Decimal stress score (0-1)
            - components: Dict of normalized component scores
            - flag: bool indicating high stress (score > 0.6)
    """
    # Credit dependency component (0-1 scale, already normalized)
    credit_dep_ratio = float(cashflow_results.get("credit_dependency_ratio", 0) or 0)
    credit_dep_score = _normalize_score(credit_dep_ratio, max_val=2.0)

    # Debt rolling component
    rolling_result = debt_rolling_flag(financial_events)
    rolling_score = _normalize_score(float(rolling_result["count"]), max_val=3.0)

    # Liquidity extraction component
    extraction_result = liquidity_extraction_frequency(financial_events)
    # High frequency = more stress (e.g., > 5 advances per period)
    extraction_count = extraction_result["count"]
    extraction_score = _normalize_score(float(extraction_count), max_val=5.0)

    # Revolving component
    revolving_result = revolver_ratio(financial_events)
    revolving_score = _normalize_score(
        float(revolving_result), max_val=1.0
    )  # Already 0-1

    # Cashflow deficit component
    cash_surplus = int(cashflow_results.get("cash_surplus", 0) or 0)
    total_expense = int(cashflow_results.get("expense_paise", 0) or 0)
    if total_expense > 0:
        deficit_ratio = abs(cash_surplus) / total_expense if cash_surplus < 0 else 0
        cashflow_score = _normalize_score(deficit_ratio, max_val=0.5)
    else:
        cashflow_score = Decimal("0")

    # Compute weighted composite score
    components = {
        "credit_dependency": credit_dep_score,
        "debt_rolling": rolling_score,
        "liquidity_extraction": extraction_score,
        "revolving": revolving_score,
        "cashflow_deficit": cashflow_score,
    }

    score = sum(Decimal(str(_STRESS_WEIGHTS[k])) * v for k, v in components.items())

    return {
        "score": Decimal(str(round(float(score), 4))),
        "components": components,
        "flag": float(score) > 0.6,
    }


# ============================================================
# Household Divergence
# ============================================================


def household_divergence(
    financial_events: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Detect cross-owner funding within household.

    Finds lineage links (funds or settles) where linked events have different
    owner_id values while sharing the same household_id.

    Args:
        financial_events: List of financial event dicts with links populated.

    Returns:
        Dict with:
            - flag: bool indicating if cross-owner funding detected
            - divergent_links: List of divergent link details
    """
    divergent_links: list[dict[str, Any]] = []

    # Build lookup for event owner info
    event_owners: dict[int, str] = {}
    for event in financial_events:
        event_id = event.get("id", 0)
        owner_id = event.get("owner_id", "self")
        if event_id:
            event_owners[int(event_id)] = owner_id

    # Check links for cross-owner funding
    for event in financial_events:
        links = event.get("links", [])
        event_owner = event.get("owner_id", "self")
        event_household = event.get("household_id", "primary")

        for link in links:
            link_type = link.get("link_type", "")
            linked_event_id = link.get("linked_event_id", 0)

            # Check funds/settles links
            if link_type in ("funds", "settles"):
                linked_owner = event_owners.get(linked_event_id, "self")

                # Cross-owner if different owner_id
                if event_owner != linked_owner:
                    divergent_links.append(
                        {
                            "from_owner": event_owner,
                            "to_owner": linked_owner,
                            "link_type": link_type,
                            "event_id": event.get("id", 0),
                            "linked_event_id": linked_event_id,
                            "household_id": event_household,
                        }
                    )

    return {
        "flag": len(divergent_links) > 0,
        "divergent_links": divergent_links,
        "count": len(divergent_links),
    }
