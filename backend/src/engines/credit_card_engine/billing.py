"""
Billing Engine - Pure calculation module
========================================
Statement date generation, due date calculation, minimum due computation.

All monetary values in paise (integer).
All rates in basis points (integer).

Reuses _add_months from loan_engine for month-end-safe date arithmetic.
"""
import calendar
from datetime import date, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from src.engines.loan_engine.amortization import _add_months


def compute_due_date(statement_date: date, due_day_offset: int) -> date:
    """
    Compute the payment due date as a fixed number of days after the statement date.

    Args:
        statement_date: The statement date (date object).
        due_day_offset: Number of days after statement date (typically 21).

    Returns:
        Due date as a date object.

    INVARIANT 4: All dates are ISO 8601 compatible.
    """
    if due_day_offset < 0:
        raise ValueError("due_day_offset must be non-negative")
    return statement_date + timedelta(days=due_day_offset)


def compute_next_statement_date(
    billing_day: int,
    reference_date: date,
    last_statement_date: date | None = None,
) -> date:
    """
    Determine the next statement date based on billing_day.

    Uses _add_months from loan_engine for month-end safety
    (e.g., Jan 31 billing_day -> Feb 28 in non-leap year).

    Args:
        billing_day: Day of month for statement generation (1-31).
        reference_date: Current date (typically today).
        last_statement_date: Previous statement date, if any.

    Returns:
        Next statement date as a date object.

    INVARIANT 4: All dates are ISO 8601 compatible.
    """
    if billing_day < 1 or billing_day > 31:
        raise ValueError("billing_day must be between 1 and 31")

    if last_statement_date is not None:
        # Advance to the next occurrence of billing_day after last_statement_date
        # Handle month-end and leap-year edge cases
        candidate = _next_billing_day_after(last_statement_date, billing_day)

        # If candidate is not after the last statement date, advance one more month
        if candidate <= last_statement_date:
            candidate = _add_months(candidate, 1)

        # If candidate is in the past relative to reference_date, advance
        if candidate < reference_date:
            candidate = _add_months(candidate, 1)

        return candidate

    # First statement: use current month's billing_day
    try:
        candidate = date(reference_date.year, reference_date.month, billing_day)
    except ValueError:
        # billing_day exceeds month length (e.g., 31 in Feb)
        # Use last day of current month
        if reference_date.month == 12:
            next_month = date(reference_date.year + 1, 1, 1)
        else:
            next_month = date(reference_date.year, reference_date.month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        candidate = date(
            reference_date.year, reference_date.month, min(billing_day, last_day)
        )

    # If candidate is in the past, advance to next month
    if candidate < reference_date:
        return _add_months(candidate, 1)

    return candidate


def _next_billing_day_after(start_date: date, billing_day: int) -> date:
    """Find the next occurrence of billing_day on or after start_date."""
    _, last_day_current = calendar.monthrange(start_date.year, start_date.month)
    try:
        candidate = date(start_date.year, start_date.month, min(billing_day, last_day_current))
    except ValueError:
        # Fallback safety (though min() with monthrange prevents ValueError)
        if start_date.month == 12:
            candidate = date(start_date.year + 1, 1, min(billing_day, 31))
        else:
            _, last_day_next = calendar.monthrange(start_date.year, start_date.month + 1)
            candidate = date(start_date.year, start_date.month + 1, min(billing_day, last_day_next))
    return candidate


def compute_statement_dates(
    billing_day: int,
    due_day_offset: int,
    reference_date: date,
    last_statement_date: date | None = None,
) -> dict[str, str]:
    """
    Compute both statement date and due date in one call.

    Args:
        billing_day: Day of month for statement generation (1-31).
        due_day_offset: Days after statement date for payment due.
        reference_date: Current date.
        last_statement_date: Previous statement date, if any.

    Returns:
        dict with 'statement_date' and 'due_date' as ISO 8601 strings.
    """
    stmt_date = compute_next_statement_date(
        billing_day=billing_day,
        reference_date=reference_date,
        last_statement_date=last_statement_date,
    )
    due = compute_due_date(stmt_date, due_day_offset)
    return {
        "statement_date": stmt_date.isoformat(),
        "due_date": due.isoformat(),
    }


def compute_minimum_due(
    total_outstanding_paise: int,
    min_due_pct_bps: int = 500,
    floor_paise: int = 10000,
) -> int:
    """
    Compute minimum payment due.

    Standard formula: max(floor, total_outstanding * min_due_pct / 10000)

    Args:
        total_outstanding_paise: Total outstanding balance in paise.
        min_due_pct_bps: Minimum due percentage in basis points (default 500 = 5%).
        floor_paise: Minimum absolute floor in paise (default 10000 = ₹100).

    Returns:
        Minimum due amount in paise (int).

    INVARIANT 1: Money is always integer paise.
    """
    if total_outstanding_paise < 0:
        raise ValueError("total_outstanding_paise must be non-negative")
    if min_due_pct_bps < 0 or min_due_pct_bps > 10000:
        raise ValueError("min_due_pct_bps must be between 0 and 10000")
    if floor_paise < 0:
        raise ValueError("floor_paise must be non-negative")

    if total_outstanding_paise == 0:
        return 0

    # Calculate percentage-based minimum due
    pct_amount = (
        Decimal(total_outstanding_paise) * Decimal(min_due_pct_bps) / Decimal(10000)
    )
    pct_amount_paise = int(pct_amount.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

    result = max(floor_paise, pct_amount_paise)
    return min(result, total_outstanding_paise)
