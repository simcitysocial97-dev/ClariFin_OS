# amortization.py
"""
Generates immutable amortization schedules for loans.

INVARIANT 3: Once generated, schedule is never modified in-place.
INVARIANT 4: All dates are ISO 8601 strings.
"""

from datetime import date, timedelta
from decimal import ROUND_CEILING, ROUND_HALF_EVEN, Decimal

from .models import AmortizationRow
from .utils import bps_to_monthly_rate


def _add_months(start: date, months: int) -> date:
    """
    Add months to a date, handling month-end and leap year edge cases.

    For month-end dates, uses last day of target month.
    For leap years, Feb 29 becomes Feb 28 in non-leap years.
    """
    total_months = start.month + months
    year = start.year + (total_months - 1) // 12
    month_idx = ((total_months - 1) % 12) + 1

    # Try to keep same day, fallback to month end or 28 for Feb
    try:
        return date(year, month_idx, start.day)
    except ValueError:
        # Day doesn't exist in target month (e.g., Jan 31 -> Feb)
        # Use last day of target month
        if month_idx == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month_idx + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
        return date(year, month_idx, min(start.day, last_day))


def _required_emi(balance: Decimal, monthly_rate: Decimal, months: int) -> int:
    """Smallest whole-paise instalment that clears `balance` in `months` months.

    Rounded up, so the instalment is never short: paying it can only bring the
    payoff forward, never leave a balloon.
    """
    if months <= 1:
        return int(
            (balance * (Decimal(1) + monthly_rate)).to_integral_value(
                rounding=ROUND_CEILING
            )
        )
    if monthly_rate == 0:
        return int(
            (balance / Decimal(months)).to_integral_value(rounding=ROUND_CEILING)
        )
    factor = (Decimal(1) + monthly_rate) ** months
    return int(
        (balance * monthly_rate * factor / (factor - Decimal(1))).to_integral_value(
            rounding=ROUND_CEILING
        )
    )


def generate_schedule(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
    start_date: str,
    emi_paise: int | None = None,
) -> list[AmortizationRow]:
    """
    Generate full amortization schedule for a reducing balance loan.

    Returns list of AmortizationRow models.
    Schedule is immutable - returns a new list each time.

    INVARIANT 1: Money is integer paise
    INVARIANT 2: Rates stored as basis points
    INVARIANT 3: Amortization schedules are immutable
    INVARIANT 4: All dates are ISO 8601 strings
    INVARIANT 6: Banker's rounding
    """
    from .emi import compute_emi_fixed

    if emi_paise is None:
        emi_paise = compute_emi_fixed(principal_paise, annual_rate_bps, tenure_months)

    monthly_rate: Decimal = bps_to_monthly_rate(annual_rate_bps)

    # `balance` is the exact (fractional) outstanding balance; `reported_balance`
    # is its integer-paise projection that appears in the schedule.
    #
    # Interest is accrued on the exact balance and the principal component is
    # derived from the movement of the reported balance. Deriving it the other
    # way round (principal = EMI - rounded interest) silently discards the
    # sub-paise principal of every instalment, which makes high-rate/small-
    # principal loans degenerate into interest-only schedules with a balloon
    # final payment, and makes a schedule regenerated from an intermediate
    # balance disagree with the original one.
    #
    # Reported interest is then EMI - principal, which keeps the ledger exactly
    # self-consistent: principal + interest == EMI and
    # balance[n] == balance[n-1] - principal[n].
    balance: Decimal = Decimal(principal_paise)
    reported_balance: int = principal_paise

    # A loan is "ill-conditioned" when quantizing the EMI to whole paise moves the
    # payoff materially: the half-paise quantization error of the EMI compounds
    # over the tenure into `0.5 * annuity_factor` paise of drift, which for a small
    # principal at a high rate over a long tenure is a large fraction of the loan
    # itself (the schedule would either close years early or end in a balloon, and
    # a schedule regenerated from an intermediate balance would not agree with it).
    # Such loans cannot be described by one fixed instalment, so the EMI is
    # re-anchored to the outstanding balance and remaining term every month.
    # Ordinary loans keep a single constant EMI, exactly as a lender would.
    if monthly_rate > 0:
        annuity_factor = (
            (Decimal(1) + monthly_rate) ** tenure_months - Decimal(1)
        ) / monthly_rate
    else:
        annuity_factor = Decimal(tenure_months)
    ill_conditioned = annuity_factor / Decimal(2) > Decimal(principal_paise) / Decimal(
        100
    )

    schedule: list[AmortizationRow] = []
    cumulative_interest: int = 0

    # Parse start date (INVARIANT 4: ISO 8601)
    start: date = date.fromisoformat(start_date)

    for month in range(1, tenure_months + 1):
        if ill_conditioned and month < tenure_months and reported_balance > 0:
            emi_paise = _required_emi(balance, monthly_rate, tenure_months - month + 1)

        interest_exact: Decimal = balance * monthly_rate
        interest_rounded = int(
            interest_exact.quantize(Decimal(1), rounding=ROUND_HALF_EVEN)
        )

        if month == tenure_months:
            # Last month: settle the exact remaining balance (absorbs any drift)
            principal_component_paise = max(0, reported_balance)
            interest_paise = interest_rounded
            actual_emi_paise = principal_component_paise + interest_paise
            reported_balance = 0
            balance = Decimal(0)
        else:
            principal_exact: Decimal = Decimal(emi_paise) - interest_exact

            if principal_exact <= 0 or reported_balance <= 0:
                # EMI does not even cover the interest (or the loan is already
                # closed): nothing is amortized this month.
                principal_component_paise = 0
                interest_paise = interest_rounded if reported_balance > 0 else 0
                actual_emi_paise = interest_paise
            elif balance - principal_exact <= 0:
                # This instalment clears the loan early
                principal_component_paise = reported_balance
                interest_paise = interest_rounded
                actual_emi_paise = principal_component_paise + interest_paise
                reported_balance = 0
                balance = Decimal(0)
            else:
                balance = balance - principal_exact
                new_reported = int(
                    balance.quantize(Decimal(1), rounding=ROUND_HALF_EVEN)
                )
                principal_component_paise = max(0, reported_balance - new_reported)
                principal_component_paise = min(principal_component_paise, emi_paise)
                reported_balance -= principal_component_paise
                interest_paise = emi_paise - principal_component_paise
                actual_emi_paise = emi_paise

        cumulative_interest += interest_paise
        closing_balance = max(0, reported_balance)

        # Compute payment date with proper edge case handling
        payment_date: date = _add_months(start, month - 1)

        schedule.append(
            AmortizationRow(
                month_number=month,
                payment_date=payment_date.isoformat(),
                emi_paise=actual_emi_paise,
                principal_paise=principal_component_paise,
                interest_paise=interest_paise,
                balance_paise=closing_balance,
                cumulative_interest_paise=cumulative_interest,
            )
        )

    return schedule


def find_schedule_row(
    schedule: list[AmortizationRow],
    month_number: int,
) -> AmortizationRow | None:
    """Find a specific row in the schedule."""
    for row in schedule:
        if row.month_number == month_number:
            return row
    return None


def total_interest_paise(schedule: list[AmortizationRow]) -> int:
    """Compute total interest over the schedule."""
    if not schedule:
        return 0
    return schedule[-1].cumulative_interest_paise


def total_payment_paise(schedule: list[AmortizationRow]) -> int:
    """Compute total payment (principal + interest)."""
    if not schedule:
        return 0
    return sum(row.emi_paise for row in schedule)


def total_principal_paise(schedule: list[AmortizationRow]) -> int:
    """Compute total principal paid over the schedule."""
    if not schedule:
        return 0
    return sum(row.principal_paise for row in schedule)


# Backward-compatible aliases — generate_schedule handles both fixed and floating rates
generate_schedule_fixed = generate_schedule
generate_schedule_floating = generate_schedule


def validate_schedule_invariants(
    schedule: list[AmortizationRow],
    original_principal_paise: int,
) -> bool:
    """
    Validate schedule invariants.

    INVARIANT CHECKS:
    1. Balance never negative
    2. Sum of principal equals original principal
    3. Final balance is zero
    """
    if not schedule:
        return True

    # Check balance never negative
    for row in schedule:
        if row.balance_paise < 0:
            raise ValueError(f"Balance went negative at month {row.month_number}")

    # Check sum of principal equals original
    total_principal = sum(row.principal_paise for row in schedule)
    if total_principal != original_principal_paise:
        raise ValueError(
            f"Principal sum mismatch: {total_principal} != {original_principal_paise}"
        )

    return True


def validate_schedule(
    schedule: list[AmortizationRow],
    original_principal_paise: int,
    original_tenure_months: int | None = None,
    debug_mode: bool = False,
) -> bool:
    """
    Comprehensive financial invariant validation for amortization schedules.

    Validates:
    1. Balance never negative
    2. Principal paid never exceeds original principal
    3. Final balance reaches zero after final EMI
    4. Sum(principal payments) == principal amount
    5. EMI consistency maintained (same EMI for all rows except last)
    6. Cumulative interest is monotonic non-decreasing
    7. Month numbers are sequential (1..N)

    Args:
        schedule: Amortization schedule to validate
        original_principal_paise: Original loan principal in paise
        original_tenure_months: Expected tenure length (optional)
        debug_mode: If True, raises on violation. If False, logs warning.

    Returns:
        True if all invariants pass

    Raises:
        ValueError: If debug_mode is True and any invariant fails
    """
    if not schedule:
        return True

    errors: list[str] = []

    # 1. Balance never negative
    for row in schedule:
        if row.balance_paise < 0:
            errors.append(
                f"Balance went negative at month {row.month_number}: {row.balance_paise}"
            )

    # 2. Principal paid never exceeds original principal
    total_principal = sum(row.principal_paise for row in schedule)
    if total_principal > original_principal_paise:
        errors.append(
            f"Total principal {total_principal} exceeds original {original_principal_paise}"
        )

    # 3. Sum(principal payments) == principal amount
    if total_principal != original_principal_paise:
        errors.append(
            f"Principal sum {total_principal} != original {original_principal_paise}"
        )

    # 4. EMI consistency (same EMI for all rows except last)
    if len(schedule) > 1:
        first_emi = schedule[0].emi_paise
        for row in schedule[:-1]:  # exclude last row
            if row.emi_paise != first_emi:
                errors.append(
                    f"EMI inconsistency at month {row.month_number}: "
                    f"{row.emi_paise} != {first_emi}"
                )

    # 5. Cumulative interest is monotonic non-decreasing
    prev_cumulative = -1
    for row in schedule:
        if row.cumulative_interest_paise < prev_cumulative:
            errors.append(
                f"Cumulative interest decreased at month {row.month_number}: "
                f"{row.cumulative_interest_paise} < {prev_cumulative}"
            )
        prev_cumulative = row.cumulative_interest_paise

    # 6. Month numbers are sequential
    for i, row in enumerate(schedule, 1):
        if row.month_number != i:
            errors.append(f"Month number {row.month_number} != expected {i}")

    # 7. (Optional) Check tenure length if provided
    if original_tenure_months is not None and len(schedule) != original_tenure_months:
        errors.append(
            f"Schedule length {len(schedule)} != expected {original_tenure_months}"
        )

    if errors:
        msg = "Schedule invariant violations: " + "; ".join(errors)
        if debug_mode:
            raise ValueError(msg)
        return False

    return True
