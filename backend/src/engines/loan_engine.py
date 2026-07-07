"""
Loan Calculation Engine
========================
Computes amortization schedules, gold loan interest,
and prepayment simulations for all loan types.

All monetary values in paise (integer).
"""

import math
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


def compute_emi(principal_paise: int, annual_rate: float, tenure_months: int) -> int:
    """
    Compute EMI using reducing balance formula.
    
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    where r = monthly interest rate, n = tenure in months
    
    Returns EMI in paise (integer).
    """
    if annual_rate == 0:
        return principal_paise // tenure_months
    
    monthly_rate = annual_rate / (12 * 100)
    factor = (1 + monthly_rate) ** tenure_months
    emi = principal_paise * monthly_rate * factor / (factor - 1)
    return int(round(emi))


def compute_amortization_schedule(
    principal_paise: int,
    annual_rate: float,
    tenure_months: int,
    disbursed_date: str,
    emi_paise: int | None = None
) -> list[dict]:
    """
    Generate full amortization schedule for a reducing balance loan.
    
    Returns list of monthly payment records with:
    - month_number
    - payment_date
    - emi_paise
    - principal_paise
    - interest_paise  
    - balance_paise
    """
    if emi_paise is None:
        emi_paise = compute_emi(principal_paise, annual_rate, tenure_months)
    
    monthly_rate = annual_rate / (12 * 100)
    balance = principal_paise
    schedule = []
    
    start = datetime.strptime(disbursed_date, '%Y-%m-%d').date()
    
    for month in range(1, tenure_months + 1):
        interest = int(round(balance * monthly_rate))
        principal_component = emi_paise - interest
        
        # Last payment adjustment
        if month == tenure_months:
            principal_component = balance
            emi_paise = principal_component + interest
        
        balance -= principal_component
        payment_date = start + relativedelta(months=month)
        
        schedule.append({
            'month_number': month,
            'payment_date': payment_date.isoformat(),
            'emi_paise': emi_paise,
            'principal_paise': principal_component,
            'interest_paise': interest,
            'balance_paise': max(0, balance),
        })
    
    return schedule


def compute_prepayment_impact(
    outstanding_paise: int,
    annual_rate: float,
    remaining_months: int,
    prepayment_paise: int,
    mode: str = 'reduce_tenure'
) -> dict:
    """
    Simulate impact of a prepayment.
    
    mode: 'reduce_tenure' keeps EMI same, reduces months
          'reduce_emi' keeps tenure same, reduces EMI
    
    Returns comparison of original vs post-prepayment schedule.
    """
    original_emi = compute_emi(outstanding_paise, annual_rate, remaining_months)
    new_principal = outstanding_paise - prepayment_paise
    
    if new_principal <= 0:
        return {
            'prepayment_paise': prepayment_paise,
            'mode': mode,
            'original_emi_paise': original_emi,
            'new_emi_paise': 0,
            'original_remaining_months': remaining_months,
            'new_remaining_months': 0,
            'interest_saved_paise': 0,
            'loan_closed': True,
        }
    
    if mode == 'reduce_tenure':
        new_months = compute_remaining_months(new_principal, annual_rate, original_emi)
        new_emi = original_emi
    else:
        new_months = remaining_months
        new_emi = compute_emi(new_principal, annual_rate, new_months)
    
    original_total = original_emi * remaining_months
    new_total = new_emi * new_months + prepayment_paise
    interest_saved = original_total - new_total
    
    return {
        'prepayment_paise': prepayment_paise,
        'mode': mode,
        'original_emi_paise': original_emi,
        'new_emi_paise': new_emi,
        'original_remaining_months': remaining_months,
        'new_remaining_months': new_months,
        'months_saved': remaining_months - new_months,
        'interest_saved_paise': max(0, interest_saved),
        'loan_closed': False,
    }


def compute_remaining_months(
    principal_paise: int,
    annual_rate: float,
    emi_paise: int
) -> int:
    """Compute remaining months given principal, rate, and fixed EMI."""
    if annual_rate == 0:
        return math.ceil(principal_paise / emi_paise)
    
    monthly_rate = annual_rate / (12 * 100)
    if emi_paise <= principal_paise * monthly_rate:
        return 999  # EMI doesn't cover interest
    
    months = math.log(emi_paise / (emi_paise - principal_paise * monthly_rate))
    months = months / math.log(1 + monthly_rate)
    return math.ceil(months)


def compute_gold_loan_interest(
    outstanding_paise: int,
    annual_rate: float,
    interest_type: str,
    days: int
) -> int:
    """
    Compute gold loan interest for a given period.
    
    Gold loans charge interest only on outstanding amount.
    interest_type: 'simple' | 'compound'
    
    Returns interest amount in paise.
    """
    if interest_type == 'compound':
        rate_per_day = annual_rate / (365 * 100)
        interest = outstanding_paise * ((1 + rate_per_day) ** days - 1)
    else:
        interest = outstanding_paise * annual_rate * days / (365 * 100)
    
    return int(round(interest))
