"""
Tax Calculator
==============
Calculates Indian tax benefits for loan interest and principal repayment.

Section 24: Home loan interest deduction
Section 80C: Principal repayment deduction

INVARIANT 1-6 enforced throughout.
"""

from src.engines.loan_engine.amortization_builder import generate_schedule

# Tax limits in paise
SECTION_24_OLD_LIMIT_PAISE: int = 20000000      # ₹2,00,000
SECTION_24_NEW_LIMIT_PAISE: int = 30000000      # ₹3,00,000
SECTION_80C_LIMIT_PAISE: int = 15000000          # ₹1,50,000


def compute_section_24_benefit(
    interest_paise: int,
    is_new_regime: bool = False,
    pre_emi_interest_paise: int = 0,
) -> int:
    """
    Compute Section 24 tax benefit for home loan interest.

    Args:
        interest_paise: Total interest paid in the year (paise)
        is_new_regime: True for new tax regime (higher limit)
        pre_emi_interest_paise: Interest during under-construction period

    Returns:
        Tax savings in paise (assuming 20% tax bracket)
    """
    limit = SECTION_24_NEW_LIMIT_PAISE if is_new_regime else SECTION_24_OLD_LIMIT_PAISE
    deductible_paise = min(interest_paise, limit)

    # Additionally, pre-EMI interest can be claimed up to ₹50,000 total
    pre_emi_deductible = min(pre_emi_interest_paise, 5000000)
    total_deductible = min(deductible_paise + pre_emi_deductible, limit)

    # 20% tax bracket
    tax_rate_bps = 2000  # 20%
    tax_savings_paise = int(total_deductible * tax_rate_bps / 100)

    return tax_savings_paise


def compute_section_80c_benefit(
    principal_paise: int,
) -> int:
    """
    Compute Section 80C tax benefit for principal repayment.

    Args:
        principal_paise: Total principal repaid in the year (paise)

    Note: ₹1,50,000 limit is across ALL 80C investments, not just loans.
    Returns tax savings in paise (assuming 20% tax bracket).
    """
    deductible_paise = min(principal_paise, SECTION_80C_LIMIT_PAISE)

    # 20% tax bracket
    tax_rate_bps = 2000
    tax_savings_paise = int(deductible_paise * tax_rate_bps / 100)

    return tax_savings_paise


def compute_annual_benefits(
    loan_id: int,
    schedule: list[dict[str, int]],
    year_index: int,
    months_per_year: int = 12,
) -> dict[str, int]:
    """
    Compute annual tax benefits for a loan.

    Args:
        loan_id: Loan identifier
        schedule: Full amortization schedule
        year_index: 0-based year index

    Returns:
        Dict with interest_paise, principal_paise, section_24_benefit_paise, section_80c_benefit_paise
    """
    start_month = year_index * months_per_year
    end_month = start_month + months_per_year

    year_rows = [
        row for row in schedule
        if start_month < row["month_number"] <= end_month
    ]

    if not year_rows:
        return {
            "interest_paise": 0,
            "principal_paise": 0,
            "section_24_benefit_paise": 0,
            "section_80c_benefit_paise": 0,
        }

    interest_paise = sum(row["interest_paise"] for row in year_rows)
    principal_paise = sum(row["principal_paise"] for row in year_rows)

    return {
        "interest_paise": interest_paise,
        "principal_paise": principal_paise,
        "section_24_benefit_paise": compute_section_24_benefit(interest_paise),
        "section_80c_benefit_paise": compute_section_80c_benefit(principal_paise),
    }


def compute_total_lifetime_tax_savings(
    principal_paise: int,
    annual_rate_bps: int,
    tenure_months: int,
    start_date: str,
) -> int:
    """
    Compute total lifetime tax savings for a loan.

    Returns sum of Section 24 and 80C benefits over the loan tenure.
    """
    schedule = generate_schedule(
        principal_paise=principal_paise,
        annual_rate_bps=annual_rate_bps,
        tenure_months=tenure_months,
        start_date=start_date,
    )

    total_section_24 = 0
    total_section_80c = 0

    for year_idx in range(tenure_months // 12 + 1):
        benefits = compute_annual_benefits(
            loan_id=0,
            schedule=[row.model_dump() for row in schedule],
            year_index=year_idx,
        )
        total_section_24 += benefits["section_24_benefit_paise"]
        total_section_80c += benefits["section_80c_benefit_paise"]

    return total_section_24 + total_section_80c
