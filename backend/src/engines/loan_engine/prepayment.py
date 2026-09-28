"""
Prepayment Engine - Pure calculation module
Supports single/multiple prepayments, both reduce-tenure and reduce-EMI modes,
prepayment penalties, dynamic schedule regeneration.
"""

import math
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Literal

from .amortization import generate_schedule, total_interest_paise
from .emi import compute_emi_fixed
from .models import AmortizationRow, PrepaymentMode, PrepaymentResult


def _compute_tenure_from_emi(
    principal_paise: int, annual_rate_bps: int, emi_paise: int
) -> int:
    """Compute months needed to pay off principal with fixed EMI."""
    if annual_rate_bps == 0:
        return math.ceil(principal_paise / emi_paise) if emi_paise > 0 else 999

    monthly_rate = Decimal(annual_rate_bps) / Decimal(120000)
    principal = Decimal(principal_paise)
    emi = Decimal(emi_paise)

    if emi <= principal * monthly_rate:
        return 999

    numerator = emi / (emi - principal * monthly_rate)
    denominator = Decimal(1) + monthly_rate
    months = numerator.ln() / denominator.ln()
    return max(
        1, min(999, int(months.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)))
    )


def compute_remaining_months(
    principal_paise: int, annual_rate_bps: int, emi_paise: int
) -> int:
    return _compute_tenure_from_emi(principal_paise, annual_rate_bps, emi_paise)


def apply_prepayment(
    outstanding_paise: int,
    annual_rate_bps: int,
    remaining_months: int,
    prepayment_paise: int,
    mode: PrepaymentMode = PrepaymentMode.REDUCE_TENURE,
    start_date: str | None = None,
    prepayment_penalty_bps: int = 0,
    existing_schedule: list[AmortizationRow] | None = None,
) -> PrepaymentResult:
    """Simulate prepayment at month 1 (beginning)."""
    original_schedule = existing_schedule
    if original_schedule is None:
        original_schedule = generate_schedule(
            principal_paise=outstanding_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=remaining_months,
            start_date=start_date or "2025-01-01",
        )

    _, result = apply_prepayment_at_month(
        original_schedule,
        1,
        prepayment_paise,
        annual_rate_bps,
        prepayment_penalty_bps,
        mode,
        start_date,
    )
    return result


def apply_prepayment_at_month(
    schedule: list[AmortizationRow],
    prepayment_month: int,
    prepayment_paise: int,
    annual_rate_bps: int,
    prepayment_penalty_bps: int = 0,
    mode: PrepaymentMode | Literal["reduce_tenure", "reduce_emi"] = "reduce_tenure",
    start_date: str | None = None,
) -> tuple[list[AmortizationRow], PrepaymentResult]:
    if prepayment_month < 1 or prepayment_month > len(schedule):
        raise ValueError(f"Prepayment month {prepayment_month} out of range")
    if prepayment_paise <= 0:
        raise ValueError("Prepayment must be positive")

    # Penalty with ROUND_HALF_EVEN (capped at min(remaining_interest, 3% of outstanding balance))
    outstanding_balance = (
        schedule[prepayment_month - 1].balance_paise
        + schedule[prepayment_month - 1].principal_paise
    )
    remaining_interest = sum(
        row.interest_paise for row in schedule[prepayment_month - 1 :]
    )
    max_penalty_paise = int(
        (Decimal(outstanding_balance) * Decimal(300) / Decimal(10000)).quantize(
            Decimal(1), rounding=ROUND_HALF_EVEN
        )
    )
    raw_penalty = (
        Decimal(prepayment_paise) * Decimal(prepayment_penalty_bps) / Decimal(10000)
    )
    # Cap raw penalty at min(remaining_interest, max_penalty_paise) BEFORE rounding
    capped_penalty = min(
        Decimal(remaining_interest), Decimal(max_penalty_paise), raw_penalty
    )
    penalty = int(capped_penalty.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))

    effective_prepayment = prepayment_paise - penalty

    # State at prepayment month
    prepayment_row = schedule[prepayment_month - 1]
    # The balance after payment in this row is closing balance.
    # We need the outstanding balance BEFORE this month's payment.
    # That is balance + principal_paid of this row.
    opening_balance = prepayment_row.balance_paise + prepayment_row.principal_paise
    remaining_balance = (
        opening_balance  # This is the balance before the prepayment month's payment
    )
    # Actually, the prepayment happens at the beginning of the month, before the regular EMI.
    # So we need the balance at the start of the month.
    # Since our schedule stores closing balance, we need the previous month's closing balance.
    # For month 1, previous balance = original principal.
    # For simplicity, we'll use the balance before the prepayment month's payment.
    # We can compute it as: if prepayment_month == 1: outstanding_paise (original) else schedule[prepayment_month-2].balance_paise
    if prepayment_month == 1:
        # The schedule's first row balance is after first payment, but we need opening balance.
        # The opening balance is the original principal.
        # We don't have original principal directly, but we can compute from first row: balance + principal.
        # That's already opening_balance.
        opening_balance = prepayment_row.balance_paise + prepayment_row.principal_paise
    else:
        opening_balance = schedule[prepayment_month - 2].balance_paise

    remaining_balance = opening_balance
    original_emi = prepayment_row.emi_paise
    original_remaining_months = len(schedule) - prepayment_month + 1

    # Apply prepayment
    new_balance = max(0, remaining_balance - effective_prepayment)

    if new_balance <= 0:
        # Loan closed
        new_schedule = schedule[:prepayment_month]
        original_interest = total_interest_paise(schedule)
        new_interest = total_interest_paise(new_schedule)
        interest_saved = original_interest - new_interest

        return new_schedule, PrepaymentResult(
            prepayment_paise=prepayment_paise,
            mode=PrepaymentMode(mode),
            original_emi_paise=original_emi,
            new_emi_paise=0,
            original_remaining_months=original_remaining_months,
            new_remaining_months=0,
            months_saved=original_remaining_months,
            interest_saved_paise=interest_saved - penalty,
            penalty_paise=penalty,
            loan_closed=True,
            new_schedule=new_schedule,
        )

    # Determine mode literal
    mode_literal: Literal["reduce_tenure", "reduce_emi"] = (
        "reduce_tenure"
        if mode in ("reduce_tenure", PrepaymentMode.REDUCE_TENURE)
        else "reduce_emi"
    )

    # Regenerate tail
    # We need to pass the tail starting from prepayment_month
    tail_start_index = prepayment_month - 1
    tail = regenerate_schedule(
        schedule[tail_start_index:],
        new_balance,
        annual_rate_bps,
        mode_literal,
        start_date or schedule[tail_start_index].payment_date,
        original_emi=original_emi,
        original_tenure=original_remaining_months,
    )

    # Combine prefix and tail
    prefix = schedule[:tail_start_index] if tail_start_index > 0 else []
    new_schedule = prefix + tail

    # C39: for reduce_emi, ensure two invariants hold on the regenerated tail:
    #   (a) no balloon larger than the stated EMI (prevents illegal final month)
    #   (b) total payment stays within tolerance of the original schedule
    #       (prevents asymmetric quantization drift from making prepayment
    #       appear to INCREASE total payment).
    # compute_emi_fixed uses ROUND_HALF_EVEN; when the fractional true EMI is
    # just below a half-paise boundary the quantized EMI undershoots, which
    # compounds over a long tenure. Each +1 EMI changes total by roughly
    # -(annuity_factor - n), typically hundreds of thousands of paise — so a
    # bounded loop converges in 1-2 iterations. This logic lives here (not in
    # regenerate_schedule) because we need the original schedule's total for
    # the comparison, and non-prepayment callers of regenerate_schedule
    # (e.g. floating-rate adjustment) must not be affected.
    if mode_literal == "reduce_emi" and new_schedule:
        original_total = sum(r.emi_paise for r in schedule)
        tol = original_remaining_months * 10 + 1000
        for _ in range(20):
            has_balloon = new_schedule[-1].emi_paise > new_schedule[0].emi_paise
            new_total = sum(r.emi_paise for r in new_schedule)
            if not has_balloon and new_total <= original_total + tol:
                break
            bumped_emi = new_schedule[0].emi_paise + 1
            tail = generate_schedule(
                principal_paise=new_balance,
                annual_rate_bps=annual_rate_bps,
                tenure_months=original_remaining_months,
                start_date=start_date or schedule[tail_start_index].payment_date,
                emi_paise=bumped_emi,
            )
            new_schedule = prefix + tail

    # Compute savings
    original_interest = total_interest_paise(schedule)
    new_interest = total_interest_paise(new_schedule)
    interest_saved = original_interest - new_interest

    new_emi = tail[0].emi_paise if tail else 0

    return new_schedule, PrepaymentResult(
        prepayment_paise=prepayment_paise,
        mode=PrepaymentMode(mode),
        original_emi_paise=original_emi,
        new_emi_paise=new_emi,
        original_remaining_months=original_remaining_months,
        new_remaining_months=len(tail),
        months_saved=original_remaining_months - len(tail),
        interest_saved_paise=interest_saved - penalty,
        penalty_paise=penalty,
        loan_closed=False,
        new_schedule=new_schedule,
    )


def apply_multiple_prepayments(
    schedule: list[AmortizationRow],
    prepayments: list[tuple[int, int]],
    annual_rate_bps: int,
    prepayment_penalty_bps: int = 0,
    mode: PrepaymentMode | Literal["reduce_tenure", "reduce_emi"] = "reduce_tenure",
    start_date: str | None = None,
) -> tuple[list[AmortizationRow], list[PrepaymentResult]]:
    if not prepayments:
        return schedule, []

    sorted_prepayments = sorted(prepayments, key=lambda x: x[0])
    current_schedule = schedule.copy()
    results = []

    for month, amount in sorted_prepayments:
        if month < 1 or month > len(current_schedule):
            continue
        new_schedule, result = apply_prepayment_at_month(
            current_schedule,
            month,
            amount,
            annual_rate_bps,
            prepayment_penalty_bps,
            mode,
            start_date,
        )
        current_schedule = new_schedule
        results.append(result)

    return current_schedule, results


def regenerate_schedule(
    previous_schedule: list[AmortizationRow],
    new_principal_paise: int,
    annual_rate_bps: int,
    mode: Literal["reduce_tenure", "reduce_emi"],
    start_date: str,
    original_emi: int | None = None,
    original_tenure: int | None = None,
) -> list[AmortizationRow]:
    """
    Regenerate schedule after prepayment/rate change.

    Args:
        previous_schedule: The tail of the schedule from the prepayment month onwards.
        new_principal_paise: Balance after prepayment.
        annual_rate_bps: Rate for new schedule.
        mode: 'reduce_tenure' (keep EMI) or 'reduce_emi' (keep tenure).
        start_date: Start date of the new tail.
        original_emi: Original EMI (for reduce_tenure mode). If not provided, derive from previous_schedule.
        original_tenure: Original remaining months (for reduce_emi mode). If not provided, derive from previous_schedule.
    """
    if new_principal_paise <= 0:
        return []

    # Derive missing parameters if not provided
    if original_emi is None and previous_schedule:
        original_emi = previous_schedule[0].emi_paise
    if original_tenure is None and previous_schedule:
        original_tenure = len(previous_schedule)

    if mode == "reduce_tenure":
        if original_emi is None:
            raise ValueError("original_emi is required for reduce_tenure mode")
        new_tenure = _compute_tenure_from_emi(
            new_principal_paise, annual_rate_bps, original_emi
        )
        # A prepayment reduces the outstanding principal, so the remaining tenure
        # must never grow beyond the original tail length. Integer EMI/tenure
        # rounding can otherwise push new_tenure up by one month. We clamp only
        # when the principal was actually reduced (prepayment case); when the
        # principal is unchanged (e.g. a floating-rate increase in adjust_tenure
        # mode) the tenure is legitimately allowed to grow.
        if previous_schedule:
            opening_balance = (
                previous_schedule[0].balance_paise
                + previous_schedule[0].principal_paise
            )
            if new_principal_paise < opening_balance:
                new_tenure = min(new_tenure, len(previous_schedule))
        new_emi = original_emi
    else:  # reduce_emi
        if original_tenure is None:
            raise ValueError("original_tenure is required for reduce_emi mode")
        new_tenure = original_tenure
        new_emi = compute_emi_fixed(new_principal_paise, annual_rate_bps, new_tenure)

    # Generate new tail
    new_tail = generate_schedule(
        principal_paise=new_principal_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=new_tenure,
        start_date=start_date,
        emi_paise=new_emi,
    )

    # Adjust month numbers to continue from previous schedule
    if previous_schedule and previous_schedule[0].month_number > 1:
        offset = previous_schedule[0].month_number - 1
        for row in new_tail:
            row.month_number += offset

    return new_tail
