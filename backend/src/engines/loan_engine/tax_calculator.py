"""
Tax Calculator
==============
Calculates comprehensive Indian tax benefits for loan interest and principal repayment.

Supports:
- Section 24: Home loan interest deduction
- Section 80C: Principal repayment deduction
- Section 80EE: First-time homebuyer additional interest deduction
- Section 80EEA: Affordable housing additional interest deduction
- Stamp duty and registration charges deduction

INVARIANT 1-6 enforced throughout.
"""

from src.engines.loan_engine.amortization_builder import generate_schedule
from src.engines.loan_engine.types import TaxBenefitResult

# Tax limits in paise
SECTION_24_OLD_LIMIT_PAISE: int = 20000000      # ₹2,00,000
SECTION_24_NEW_LIMIT_PAISE: int = 30000000      # ₹3,00,000
SECTION_80C_LIMIT_PAISE: int = 15000000         # ₹1,50,000
SECTION_80EE_LIMIT_PAISE: int = 5000000         # ₹50,000
SECTION_80EEA_LIMIT_PAISE: int = 15000000       # ₹1,50,000
STAMP_DUTY_LIMIT_PAISE: int = 15000000          # ₹1,50,000

def compute_section_24_benefit(
    interest_paise: int,
    is_new_regime: bool = False,
    pre_emi_interest_paise: int = 0,
    is_self_occupied: bool = True,
) -> int:
    """
    Compute Section 24 tax benefit for home loan interest.

    Args:
        interest_paise: Total interest paid in the year (paise)
        is_new_regime: True for new tax regime (higher limit)
        pre_emi_interest_paise: Interest during under-construction period
        is_self_occupied: True if property is self-occupied

    Returns:
        Tax savings in paise
    """
    if not is_self_occupied:
        # For let-out properties, no limit on interest deduction
        limit = float('inf')
    else:
        limit = SECTION_24_NEW_LIMIT_PAISE if is_new_regime else SECTION_24_OLD_LIMIT_PAISE

    deductible_paise = min(interest_paise, limit)

    # Additionally, pre-EMI interest can be claimed up to ₹50,000 total
    pre_emi_deductible = min(pre_emi_interest_paise, 5000000)
    total_deductible = min(deductible_paise + pre_emi_deductible, limit)

    # Use configurable tax rate
    tax_rate_bps = 2000  # 20% default
    tax_savings_paise = int(total_deductible * tax_rate_bps / 10000)

    return tax_savings_paise

def compute_section_80c_benefit(
    principal_paise: int,
    other_80c_investments_paise: int = 0,
) -> int:
    """
    Compute Section 80C tax benefit for principal repayment.

    Args:
        principal_paise: Total principal repaid in the year (paise)
        other_80c_investments_paise: Other 80C investments (PF, insurance, etc.)

    Note: ₹1,50,000 limit is across ALL 80C investments, not just loans.
    Returns tax savings in paise.
    """
    available_limit = max(0, SECTION_80C_LIMIT_PAISE - other_80c_investments_paise)
    deductible_paise = min(principal_paise, available_limit)

    tax_rate_bps = 2000  # 20% default
    tax_savings_paise = int(deductible_paise * tax_rate_bps / 10000)

    return tax_savings_paise

def compute_section_80ee_benefit(
    interest_paise: int,
    is_first_time_buyer: bool = False,
    loan_sanction_date: str | None = None,
    property_value_paise: int = 0,
) -> int:
    """
    Compute Section 80EE tax benefit for first-time homebuyers.

    Conditions:
    - Loan sanctioned between 1-Apr-2016 and 31-Mar-2017
    - Property value ≤ ₹50,00,000
    - Loan amount ≤ ₹35,00,000
    - No other house owned

    Returns:
        Additional tax savings in paise (up to ₹50,000)
    """
    if not is_first_time_buyer:
        return 0

    # Check if loan was sanctioned in the eligible period
    if loan_sanction_date:
        sanction_year = int(loan_sanction_date[:4])
        if sanction_year < 2016 or sanction_year > 2017:
            return 0

    # Check property value limit (₹50,00,000 = 50,000,000 paise)
    if property_value_paise > 50000000:
        return 0

    deductible_paise = min(interest_paise, SECTION_80EE_LIMIT_PAISE)
    tax_rate_bps = 2000  # 20% default
    tax_savings_paise = int(deductible_paise * tax_rate_bps / 10000)

    return tax_savings_paise

def compute_section_80eea_benefit(
    interest_paise: int,
    is_affordable_housing: bool = False,
    loan_sanction_date: str | None = None,
    property_value_paise: int = 0,
) -> int:
    """
    Compute Section 80EEA tax benefit for affordable housing.

    Conditions:
    - Loan sanctioned between 1-Apr-2019 and 31-Mar-2022
    - Property value ≤ ₹45,00,000
    - Carpet area ≤ 60 sqm (metros) or 90 sqm (non-metros)
    - No other house owned

    Returns:
        Additional tax savings in paise (up to ₹1,50,000)
    """
    if not is_affordable_housing:
        return 0

    # Check if loan was sanctioned in the eligible period
    if loan_sanction_date:
        sanction_year = int(loan_sanction_date[:4])
        if sanction_year < 2019 or sanction_year > 2022:
            return 0

    # Check property value limit (₹45,00,000 = 45,000,000 paise)
    if property_value_paise > 45000000:
        return 0

    deductible_paise = min(interest_paise, SECTION_80EEA_LIMIT_PAISE)
    tax_rate_bps = 2000  # 20% default
    tax_savings_paise = int(deductible_paise * tax_rate_bps / 10000)

    return tax_savings_paise

def compute_stamp_duty_benefit(
    stamp_duty_paise: int,
    registration_charges_paise: int,
    is_first_registration: bool = True,
) -> int:
    """
    Compute stamp duty and registration charges deduction.

    Can be claimed in the year of registration under Section 80C.
    """
    if not is_first_registration:
        return 0

    total_charges = stamp_duty_paise + registration_charges_paise
    deductible_paise = min(total_charges, STAMP_DUTY_LIMIT_PAISE)

    tax_rate_bps = 2000  # 20% default
    tax_savings_paise = int(deductible_paise * tax_rate_bps / 10000)

    return tax_savings_paise

def compute_annual_benefits(
    loan_id: int,
    schedule: list[dict],
    year_index: int,
    tax_rate_bps: int = 2000,
    is_new_regime: bool = False,
    is_self_occupied: bool = True,
    is_first_time_buyer: bool = False,
    is_affordable_housing: bool = False,
    loan_sanction_date: str | None = None,
    property_value_paise: int = 0,
    other_80c_investments_paise: int = 0,
    stamp_duty_paise: int = 0,
    registration_charges_paise: int = 0,
    months_per_year: int = 12,
) -> TaxBenefitResult:
    """
    Compute comprehensive annual tax benefits for a loan.

    Args:
        loan_id: Loan identifier
        schedule: Full amortization schedule
        year_index: 0-based year index
        tax_rate_bps: Tax rate in basis points (e.g., 2000 = 20%)
        is_new_regime: True for new tax regime
        is_self_occupied: True if property is self-occupied
        is_first_time_buyer: True for first-time homebuyers
        is_affordable_housing: True for affordable housing
        loan_sanction_date: Date when loan was sanctioned (ISO format)
        property_value_paise: Property value in paise
        other_80c_investments_paise: Other 80C investments
        stamp_duty_paise: Stamp duty paid in paise
        registration_charges_paise: Registration charges paid in paise
        months_per_year: Number of months per year (default 12)

    Returns:
        TaxBenefitResult with all benefit components
    """
    start_month = year_index * months_per_year
    end_month = start_month + months_per_year

    year_rows = [
        row for row in schedule
        if start_month < row["month_number"] <= end_month
    ]

    if not year_rows:
        return TaxBenefitResult(
            interest_paise=0,
            principal_paise=0,
            section_24_benefit_paise=0,
            section_80c_benefit_paise=0,
            section_80ee_benefit_paise=0,
            section_80eea_benefit_paise=0,
            stamp_duty_benefit_paise=0,
            total_benefit_paise=0,
        )

    interest_paise = sum(row["interest_paise"] for row in year_rows)
    principal_paise = sum(row["principal_paise"] for row in year_rows)

    # Compute all benefits
    section_24 = compute_section_24_benefit(
        interest_paise,
        is_new_regime,
        0,  # pre-EMI interest handled separately
        is_self_occupied,
    )

    section_80c = compute_section_80c_benefit(
        principal_paise,
        other_80c_investments_paise,
    )

    section_80ee = compute_section_80ee_benefit(
        interest_paise,
        is_first_time_buyer,
        loan_sanction_date,
        property_value_paise,
    )

    section_80eea = compute_section_80eea_benefit(
        interest_paise,
        is_affordable_housing,
        loan_sanction_date,
        property_value_paise,
    )

    stamp_duty = compute_stamp_duty_benefit(
        stamp_duty_paise,
        registration_charges_paise,
        year_index == 0,  # Only in first year
    )

    # Adjust for tax rate
    total_benefit = int((section_24 + section_80c + section_80ee + section_80eea + stamp_duty) * tax_rate_bps / 2000)

    return TaxBenefitResult(
        interest_paise=interest_paise,
        principal_paise=principal_paise,
        section_24_benefit_paise=int(section_24 * tax_rate_bps / 2000),
        section_80c_benefit_paise=int(section_80c * tax_rate_bps / 2000),
        section_80ee_benefit_paise=int(section_80ee * tax_rate_bps / 2000),
        section_80eea_benefit_paise=int(section_80eea * tax_rate_bps / 2000),
        stamp_duty_benefit_paise=int(stamp_duty * tax_rate_bps / 2000),
        total_benefit_paise=total_benefit,
    )

def compute_total_lifetime_tax_savings(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
    start_date: str,
    tax_rate_bps: int = 2000,
    is_new_regime: bool = False,
    is_self_occupied: bool = True,
    is_first_time_buyer: bool = False,
    is_affordable_housing: bool = False,
    loan_sanction_date: str | None = None,
    property_value_paise: int = 0,
    other_80c_investments_paise: int = 0,
    stamp_duty_paise: int = 0,
    registration_charges_paise: int = 0,
) -> TaxBenefitResult:
    """
    Compute total lifetime tax savings for a loan.

    Returns sum of all tax benefits over the loan tenure.
    """
    schedule = generate_schedule(
        principal_paise=principal_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=tenure_months,
        start_date=start_date,
    )

    # Convert schedule to dict format
    schedule_dicts = [row.model_dump() for row in schedule]

    total_section_24 = 0
    total_section_80c = 0
    total_section_80ee = 0
    total_section_80eea = 0
    total_stamp_duty = 0
    total_benefit = 0

    for year_idx in range(tenure_months // 12 + 1):
        benefits = compute_annual_benefits(
            loan_id=0,
            schedule=schedule_dicts,
            year_index=year_idx,
            tax_rate_bps=tax_rate_bps,
            is_new_regime=is_new_regime,
            is_self_occupied=is_self_occupied,
            is_first_time_buyer=is_first_time_buyer,
            is_affordable_housing=is_affordable_housing,
            loan_sanction_date=loan_sanction_date,
            property_value_paise=property_value_paise,
            other_80c_investments_paise=other_80c_investments_paise,
            stamp_duty_paise=stamp_duty_paise if year_idx == 0 else 0,
            registration_charges_paise=registration_charges_paise if year_idx == 0 else 0,
        )

        total_section_24 += benefits.section_24_benefit_paise
        total_section_80c += benefits.section_80c_benefit_paise
        total_section_80ee += benefits.section_80ee_benefit_paise
        total_section_80eea += benefits.section_80eea_benefit_paise
        total_stamp_duty += benefits.stamp_duty_benefit_paise
        total_benefit += benefits.total_benefit_paise

    return TaxBenefitResult(
        interest_paise=sum(row["interest_paise"] for row in schedule_dicts),
        principal_paise=sum(row["principal_paise"] for row in schedule_dicts),
        section_24_benefit_paise=total_section_24,
        section_80c_benefit_paise=total_section_80c,
        section_80ee_benefit_paise=total_section_80ee,
        section_80eea_benefit_paise=total_section_80eea,
        stamp_duty_benefit_paise=total_stamp_duty,
        total_benefit_paise=total_benefit,
    )

def compare_tax_regimes(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
    start_date: str,
    tax_rate_old: int = 2000,
    tax_rate_new: int = 2000,
    **kwargs,
) -> dict[str, TaxBenefitResult]:
    """
    Compare tax benefits between old and new tax regimes.

    Returns dict with "old_regime" and "new_regime" results.
    """
    old_regime = compute_total_lifetime_tax_savings(
        principal_paise=principal_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=tenure_months,
        start_date=start_date,
        tax_rate_bps=tax_rate_old,
        is_new_regime=False,
        **kwargs,
    )

    new_regime = compute_total_lifetime_tax_savings(
        principal_paise=principal_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=tenure_months,
        start_date=start_date,
        tax_rate_bps=tax_rate_new,
        is_new_regime=True,
        **kwargs,
    )

    return {
        "old_regime": old_regime,
        "new_regime": new_regime,
    }