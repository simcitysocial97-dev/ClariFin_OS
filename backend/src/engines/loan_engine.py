"""
Loan Amortization Engine
========================

Production-grade loan computation engine with daily reducing interest.

Key Principles:
1. All amounts are INTEGER paise (1 rupee = 100 paise)
2. Daily reducing interest calculation (365-day year)
3. Pure functions - no database writes, no side effects
4. Deterministic: same inputs → same output, every time
5. Handles edge cases: 0% interest, early closure, multiple prepayments
"""

from datetime import date, timedelta
from calendar import monthrange
from typing import List, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP

from src.logger import log
from src.utils import add_months


# ============================================================
# Function 1: Compute EMI
# ============================================================

def compute_emi(
    principal_paise: int,
    annual_rate_percent: float,
    tenure_months: int
) -> int:
    """
    Calculate Equated Monthly Installment (EMI) using standard formula.
    
    Formula: EMI = P × r × (1+r)^n / ((1+r)^n - 1)
    Where:
        P = principal
        r = monthly interest rate = annual_rate / 12 / 100
        n = number of months
    
    Args:
        principal_paise: Loan principal in paise
        annual_rate_percent: Annual interest rate (e.g., 8.5 for 8.5%)
        tenure_months: Loan tenure in months
    
    Returns:
        EMI amount in paise (integer)
    
    Edge Case:
        If annual_rate_percent = 0, returns principal // tenure_months
    """
    if tenure_months <= 0:
        return 0
    
    # Handle 0% interest case
    if annual_rate_percent == 0:
        return principal_paise // tenure_months
    
    # Convert to Decimal for precision
    P = Decimal(principal_paise)
    r = Decimal(annual_rate_percent) / Decimal(12) / Decimal(100)
    n = Decimal(tenure_months)
    
    # EMI formula: P × r × (1+r)^n / ((1+r)^n - 1)
    one_plus_r = Decimal(1) + r
    one_plus_r_pow_n = one_plus_r ** n
    
    emi = P * r * one_plus_r_pow_n / (one_plus_r_pow_n - Decimal(1))
    
    # Round to nearest integer
    return int(emi.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


# ============================================================
# Function 2: Generate Ideal Amortization Schedule
# ============================================================

def generate_ideal_schedule(
    principal_paise: int,
    annual_rate_percent: float,
    tenure_months: int,
    start_date: date
) -> List[Dict]:
    """
    Generate ideal amortization schedule with daily reducing interest.
    
    Uses daily interest calculation:
        daily_rate = annual_rate / 100 / 365
        interest = balance × daily_rate × days
    
    Args:
        principal_paise: Loan principal in paise
        annual_rate_percent: Annual interest rate (e.g., 8.5 for 8.5%)
        tenure_months: Loan tenure in months
        start_date: First EMI date
    
    Returns:
        List of period dicts with keys:
            - period: int (1-indexed)
            - emi_date: date
            - emi_paise: int
            - interest_paise: int
            - principal_paise: int
            - remaining_principal_paise: int
    
    Note:
        Final period is adjusted to ensure remaining_principal_paise == 0
    """
    if principal_paise <= 0 or tenure_months <= 0:
        return []
    
    schedule = []
    balance = principal_paise
    emi = compute_emi(principal_paise, annual_rate_percent, tenure_months)
    daily_rate = Decimal(annual_rate_percent) / Decimal(100) / Decimal(365)
    
    current_date = start_date
    previous_date = start_date
    
    for period in range(1, tenure_months + 1):
        # Calculate next EMI date (handle month-end)
        if period == 1:
            emi_date = current_date
        else:
            emi_date = add_months(current_date, period - 1)
        
        # Calculate days since last payment
        days = (emi_date - previous_date).days
        
        # Calculate interest for this period
        if annual_rate_percent == 0:
            interest = 0
        else:
            interest = int((Decimal(balance) * daily_rate * Decimal(days)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        
        # Principal component
        principal_component = emi - interest
        
        # Adjust for final period
        if period == tenure_months:
            # Ensure we don't overpay
            principal_component = balance
            emi = interest + principal_component
        
        # Update balance
        balance -= principal_component
        
        # Ensure balance never goes negative
        if balance < 0:
            principal_component += balance
            balance = 0
        
        schedule.append({
            "period": period,
            "emi_date": emi_date,
            "emi_paise": emi,
            "interest_paise": interest,
            "principal_paise": principal_component,
            "remaining_principal_paise": balance
        })
        
        previous_date = emi_date
        
        # Early exit if loan is fully paid
        if balance <= 0:
            break
    
    return schedule


# ============================================================
# Function 3: Replay Payments (Critical)
# ============================================================

def replay_payments(
    principal_paise: int,
    annual_rate_percent: float,
    start_date: date,
    payments: List[Dict]
) -> Dict:
    """
    Replay actual payments chronologically and recalculate remaining principal.
    
    This is the core function for dynamic loan state computation.
    Supports both EMI and PREPAYMENT types.
    
    Args:
        principal_paise: Original loan principal in paise
        annual_rate_percent: Annual interest rate
        start_date: Loan start date (interest starts accruing from here)
        payments: List of payment dicts sorted chronologically:
            {
                "date": date,
                "amount_paise": int,
                "type": "EMI" | "PREPAYMENT"
            }
    
    Returns:
        Dict with keys:
            - remaining_principal_paise: int
            - accrued_interest_paise: int (unpaid interest)
            - total_interest_paid_paise: int
            - total_principal_paid_paise: int
            - last_date: date
            - payment_history: List[Dict] with processed payments
    """
    if principal_paise <= 0:
        return {
            "remaining_principal_paise": 0,
            "accrued_interest_paise": 0,
            "total_interest_paid_paise": 0,
            "total_principal_paid_paise": 0,
            "last_date": start_date,
            "payment_history": []
        }
    
    balance = principal_paise
    accrued_interest = 0
    total_interest_paid = 0
    total_principal_paid = 0
    last_date = start_date
    daily_rate = Decimal(annual_rate_percent) / Decimal(100) / Decimal(365)
    
    payment_history = []
    
    # Sort payments by date
    sorted_payments = sorted(payments, key=lambda p: p["date"])
    
    for payment in sorted_payments:
        payment_date = payment["date"]
        amount = payment["amount_paise"]
        payment_type = payment.get("type", "EMI")
        
        # Calculate interest from last_date to payment_date
        days = (payment_date - last_date).days
        if days > 0 and annual_rate_percent > 0:
            interest_accrued = int((Decimal(balance) * daily_rate * Decimal(days)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            accrued_interest += interest_accrued
        
        # Process payment
        if payment_type == "PREPAYMENT":
            # Prepayment goes entirely to principal
            principal_payment = min(amount, balance)
            interest_payment = 0
        else:
            # EMI payment: first pay interest, then principal
            interest_payment = min(accrued_interest, amount)
            remaining_after_interest = amount - interest_payment
            principal_payment = min(remaining_after_interest, balance)
        
        # Update totals
        accrued_interest -= interest_payment
        total_interest_paid += interest_payment
        total_principal_paid += principal_payment
        balance -= principal_payment
        
        payment_history.append({
            "date": payment_date,
            "amount_paise": amount,
            "type": payment_type,
            "interest_paid_paise": interest_payment,
            "principal_paid_paise": principal_payment,
            "balance_after_paise": balance,
            "accrued_interest_after_paise": accrued_interest
        })
        
        last_date = payment_date
        
        # Early exit if loan is fully paid
        if balance <= 0:
            balance = 0
            break
    
    return {
        "remaining_principal_paise": balance,
        "accrued_interest_paise": accrued_interest,
        "total_interest_paid_paise": total_interest_paid,
        "total_principal_paid_paise": total_principal_paid,
        "last_date": last_date,
        "payment_history": payment_history
    }


# ============================================================
# Function 4: Forecast from Current State
# ============================================================

def forecast_from_state(
    remaining_principal_paise: int,
    annual_rate_percent: float,
    emi_paise: int,
    from_date: date
) -> Dict:
    """
    Forecast future loan schedule from current state.
    
    Args:
        remaining_principal_paise: Current outstanding principal
        annual_rate_percent: Annual interest rate
        emi_paise: Monthly EMI amount
        from_date: Date to start forecasting from
    
    Returns:
        Dict with keys:
            - months_remaining: int
            - projected_closure_date: date
            - future_interest_paise: int
            - schedule: List[Dict] (future periods)
    """
    if remaining_principal_paise <= 0 or emi_paise <= 0:
        return {
            "months_remaining": 0,
            "projected_closure_date": from_date,
            "future_interest_paise": 0,
            "schedule": []
        }
    
    schedule = []
    balance = remaining_principal_paise
    total_future_interest = 0
    period = 0
    previous_date = from_date
    daily_rate = Decimal(annual_rate_percent) / Decimal(100) / Decimal(365)
    
    while balance > 0 and period < 600:  # Cap at 50 years to prevent infinite loop
        period += 1
        
        # Calculate next EMI date
        emi_date = add_months(from_date, period - 1)
        
        # Calculate days and interest
        days = (emi_date - previous_date).days
        if annual_rate_percent > 0:
            interest = int((Decimal(balance) * daily_rate * Decimal(days)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        else:
            interest = 0
        
        # Principal component
        principal_component = emi_paise - interest
        
        # Adjust for final period
        if principal_component >= balance:
            principal_component = balance
            emi = interest + principal_component
        else:
            emi = emi_paise
        
        balance -= principal_component
        total_future_interest += interest
        
        schedule.append({
            "period": period,
            "emi_date": emi_date,
            "emi_paise": emi,
            "interest_paise": interest,
            "principal_paise": principal_component,
            "remaining_principal_paise": max(0, balance)
        })
        
        previous_date = emi_date
        
        if balance <= 0:
            break
    
    return {
        "months_remaining": len(schedule),
        "projected_closure_date": schedule[-1]["emi_date"] if schedule else from_date,
        "future_interest_paise": total_future_interest,
        "schedule": schedule
    }


# ============================================================
# Function 5: Simulate Prepayment
# ============================================================

def simulate_prepayment(
    loan_details: Dict,
    payments: List[Dict],
    extra_payment_paise: int,
    extra_payment_date: date,
    strategy: str  # "REDUCE_TENURE" or "REDUCE_EMI"
) -> Dict:
    """
    Simulate the impact of making an extra prepayment.
    
    Args:
        loan_details: Dict with keys:
            - principal_paise: int
            - annual_rate_percent: float
            - tenure_months: int
            - start_date: date
            - emi_paise: int (optional, will be computed if not provided)
        payments: List of existing payments (chronological)
        extra_payment_paise: Amount of extra prepayment
        extra_payment_date: Date of extra prepayment
        strategy: "REDUCE_TENURE" or "REDUCE_EMI"
    
    Returns:
        Dict with keys:
            - interest_saved_paise: int
            - months_saved: int
            - new_closure_date: date
            - new_emi_paise: int
            - effective_annual_return_percent: float
            - original_closure_date: date
            - original_future_interest_paise: int
            - new_future_interest_paise: int
    """
    principal = loan_details["principal_paise"]
    rate = loan_details["annual_rate_percent"]
    tenure = loan_details["tenure_months"]
    start_date = loan_details["start_date"]
    emi = loan_details.get("emi_paise") or compute_emi(principal, rate, tenure)
    
    # Replay existing payments up to prepayment date
    existing_payments_before = [p for p in payments if p["date"] <= extra_payment_date]
    state = replay_payments(principal, rate, start_date, existing_payments_before)
    
    # Calculate original forecast (without prepayment)
    original_forecast = forecast_from_state(
        state["remaining_principal_paise"],
        rate,
        emi,
        state["last_date"]
    )
    
    # Add prepayment
    prepayment = {
        "date": extra_payment_date,
        "amount_paise": extra_payment_paise,
        "type": "PREPAYMENT"
    }
    all_payments = existing_payments_before + [prepayment]
    new_state = replay_payments(principal, rate, start_date, all_payments)
    
    # Calculate new forecast based on strategy
    if strategy == "REDUCE_EMI":
        # Recalculate EMI with remaining tenure
        remaining_tenure = original_forecast["months_remaining"]
        if remaining_tenure > 0:
            new_emi = compute_emi(new_state["remaining_principal_paise"], rate, remaining_tenure)
        else:
            new_emi = emi
    else:  # REDUCE_TENURE
        new_emi = emi
    
    new_forecast = forecast_from_state(
        new_state["remaining_principal_paise"],
        rate,
        new_emi,
        new_state["last_date"]
    )
    
    # Calculate savings
    original_future_interest = original_forecast["future_interest_paise"]
    new_future_interest = new_forecast["future_interest_paise"]
    interest_saved = original_future_interest - new_future_interest
    
    months_saved = original_forecast["months_remaining"] - new_forecast["months_remaining"]
    
    # Calculate effective annual return
    effective_return = compute_effective_annual_return(
        extra_payment_paise,
        interest_saved,
        new_forecast["months_remaining"]
    )
    
    return {
        "interest_saved_paise": interest_saved,
        "months_saved": months_saved,
        "new_closure_date": new_forecast["projected_closure_date"],
        "new_emi_paise": new_emi,
        "effective_annual_return_percent": effective_return,
        "original_closure_date": original_forecast["projected_closure_date"],
        "original_future_interest_paise": original_future_interest,
        "new_future_interest_paise": new_future_interest,
        "remaining_principal_after_prepayment_paise": new_state["remaining_principal_paise"]
    }


# ============================================================
# Function 6: Compute Effective Annual Return
# ============================================================

def compute_effective_annual_return(
    investment_paise: int,
    return_paise: int,
    months: int
) -> float:
    """
    Compute the effective annual return (IRR-equivalent) of a prepayment.
    
    This calculates the annualized rate where:
        investment today → returns over remaining tenure
    
    Approximation using compound interest formula:
        (1 + r)^n = (investment + return) / investment
        r = ((investment + return) / investment)^(1/n) - 1
    
    Args:
        investment_paise: Amount invested (prepayment)
        return_paise: Interest saved (return)
        months: Number of months over which return is realized
    
    Returns:
        Annualized return percentage (float, rounded to 2 decimals)
    """
    if investment_paise <= 0 or return_paise <= 0 or months <= 0:
        return 0.0
    
    # Total value at end
    total_value = investment_paise + return_paise
    
    # Calculate monthly rate
    # (1 + r_monthly)^months = total_value / investment
    ratio = Decimal(total_value) / Decimal(investment_paise)
    n = Decimal(months)
    
    # Monthly rate
    monthly_rate = (ratio ** (Decimal(1) / n)) - Decimal(1)
    
    # Annual rate
    annual_rate = monthly_rate * Decimal(12) * Decimal(100)
    
    return float(annual_rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


# ============================================================
# Function 7: Compute Loan Summary
# ============================================================

def compute_loan_summary(
    loan_details: Dict,
    payments: List[Dict],
    as_of_date: Optional[date] = None
) -> Dict:
    """
    Compute comprehensive loan summary including replay and forecast.
    
    Args:
        loan_details: Dict with loan details:
            - principal_paise: int
            - annual_rate_percent: float
            - tenure_months: int
            - start_date: date
            - emi_paise: int (optional)
        payments: List of payment dicts
        as_of_date: Date for summary (default: today)
    
    Returns:
        Dict with keys:
            - principal_original_paise: int
            - principal_remaining_paise: int
            - total_interest_paid_paise: int
            - future_interest_paise: int
            - total_interest_full_term_paise: int
            - completion_percent: float
            - projected_closure_date: date
            - days_to_close: int
            - is_closed: bool
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    principal = loan_details["principal_paise"]
    rate = loan_details["annual_rate_percent"]
    tenure = loan_details["tenure_months"]
    start_date = loan_details["start_date"]
    emi = loan_details.get("emi_paise") or compute_emi(principal, rate, tenure)
    
    # Replay payments up to as_of_date
    payments_before = [p for p in payments if p["date"] <= as_of_date]
    state = replay_payments(principal, rate, start_date, payments_before)
    
    # Forecast from current state
    forecast = forecast_from_state(
        state["remaining_principal_paise"],
        rate,
        emi,
        as_of_date
    )
    
    # Calculate total interest for full term (original schedule)
    ideal_schedule = generate_ideal_schedule(principal, rate, tenure, start_date)
    original_total_interest = sum(p["interest_paise"] for p in ideal_schedule)
    
    # Calculate completion percentage
    if principal > 0:
        completion_percent = round(
            (principal - state["remaining_principal_paise"]) / principal * 100,
            2
        )
    else:
        completion_percent = 100.0
    
    # Days to close
    days_to_close = (forecast["projected_closure_date"] - as_of_date).days
    
    return {
        "principal_original_paise": principal,
        "principal_remaining_paise": state["remaining_principal_paise"],
        "total_interest_paid_paise": state["total_interest_paid_paise"],
        "future_interest_paise": forecast["future_interest_paise"],
        "total_interest_full_term_paise": original_total_interest,
        "completion_percent": completion_percent,
        "projected_closure_date": forecast["projected_closure_date"],
        "days_to_close": max(0, days_to_close),
        "is_closed": state["remaining_principal_paise"] <= 0,
        "months_remaining": forecast["months_remaining"],
        "total_payments_made": len(payments_before)
    }


# ============================================================
# Alias for backward compatibility
# ============================================================

def compute_amortization_schedule(
    principal_paise: int,
    annual_rate: float,
    tenure_months: int
) -> List[Dict]:
    """
    Alias for generate_ideal_schedule for backward compatibility.
    
    Original spec: compute_amortization_schedule(principal_paise, annual_rate, tenure_months)
    Uses default start_date of today.
    
    Args:
        principal_paise: Loan principal in paise
        annual_rate: Annual interest rate (e.g., 8.5 for 8.5%)
        tenure_months: Loan tenure in months
    
    Returns:
        List of month dicts with keys:
            - month_number: int (1-indexed, aliased from 'period')
            - emi_paise: int
            - principal_component_paise: int (aliased from 'principal_paise')
            - interest_component_paise: int (aliased from 'interest_paise')
            - remaining_principal_paise: int
    """
    schedule = generate_ideal_schedule(
        principal_paise=principal_paise,
        annual_rate_percent=annual_rate,
        tenure_months=tenure_months,
        start_date=date.today()
    )
    
    # Map to original spec output format
    return [
        {
            "month_number": p["period"],
            "emi_paise": p["emi_paise"],
            "principal_component_paise": p["principal_paise"],
            "interest_component_paise": p["interest_paise"],
            "remaining_principal_paise": p["remaining_principal_paise"]
        }
        for p in schedule
    ]


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    from datetime import date
    
    log.info("=" * 60)
    log.info("Loan Engine Test")
    log.info("=" * 60)
    
    # Test compute_emi
    emi = compute_emi(5000000000, 8.5, 240)  # 50L, 8.5%, 20 years
    log.info("EMI for 50L, 8.5%%, 20 years: ₹%.2f", emi / 100)
    
    # Test generate_ideal_schedule
    schedule = generate_ideal_schedule(5000000000, 8.5, 240, date(2025, 1, 1))
    log.info("Total periods: %d", len(schedule))
    log.info("First EMI: ₹%.2f on %s", schedule[0]["emi_paise"] / 100, schedule[0]["emi_date"])
    log.info("Last balance: ₹%.2f", schedule[-1]["remaining_principal_paise"] / 100)
    log.info("Total interest over loan term: ₹%.2f", 
             sum(p["interest_paise"] for p in schedule) / 100)
    
    # Test replay_payments
    payments = [
        {"date": date(2025, 2, 1), "amount_paise": emi, "type": "EMI"},
        {"date": date(2025, 3, 1), "amount_paise": emi, "type": "EMI"},
        {"date": date(2025, 4, 1), "amount_paise": 100000000, "type": "PREPAYMENT"},  # 1L prepayment
        {"date": date(2025, 4, 1), "amount_paise": emi, "type": "EMI"},
    ]
    
    state = replay_payments(5000000000, 8.5, date(2025, 1, 1), payments)
    log.info("\nAfter 4 payments (including 1L prepayment):")
    log.info("  Remaining principal: ₹%.2f", state["remaining_principal_paise"] / 100)
    log.info("  Total interest paid: ₹%.2f", state["total_interest_paid_paise"] / 100)
    log.info("  Total principal paid: ₹%.2f", state["total_principal_paid_paise"] / 100)
    
    # Test forecast
    forecast = forecast_from_state(
        state["remaining_principal_paise"],
        8.5,
        emi,
        state["last_date"]
    )
    log.info("\nForecast from current state:")
    log.info("  Months remaining: %d", forecast["months_remaining"])
    log.info("  Projected closure: %s", forecast["projected_closure_date"])
    log.info("  Future interest: ₹%.2f", forecast["future_interest_paise"] / 100)
    
    # Test prepayment simulation
    loan_details = {
        "principal_paise": 5000000000,
        "annual_rate_percent": 8.5,
        "tenure_months": 240,
        "start_date": date(2025, 1, 1),
        "emi_paise": emi
    }
    
    result = simulate_prepayment(
        loan_details,
        payments[:2],  # Only first 2 EMIs before prepayment
        500000000,  # 5L prepayment
        date(2025, 3, 15),
        "REDUCE_TENURE"
    )
    
    log.info("\nPrepayment simulation (5L on 2025-03-15, reduce tenure):")
    log.info("  Interest saved: ₹%.2f", result["interest_saved_paise"] / 100)
    log.info("  Months saved: %d", result["months_saved"])
    log.info("  New closure date: %s", result["new_closure_date"])
    log.info("  Effective annual return: %.2f%%", result["effective_annual_return_percent"])
    
    # Test summary
    summary = compute_loan_summary(loan_details, payments, date(2025, 6, 1))
    log.info("\nLoan summary as of 2025-06-01:")
    log.info("  Original principal: ₹%.2f", summary["principal_original_paise"] / 100)
    log.info("  Remaining principal: ₹%.2f", summary["principal_remaining_paise"] / 100)
    log.info("  Completion: %.2f%%", summary["completion_percent"])
    log.info("  Projected closure: %s", summary["projected_closure_date"])
    
    log.info("\nLoan engine OK")
