"""
Projections Router
==================

FastAPI endpoints for financial forecasting and projections.

All business logic is delegated to the projection_engine.
No business logic in this router - only HTTP handling.
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.dependencies import get_db
from src.logger import log
from src.errors import NotFoundError
from src.engines.projection_engine import (
    project_net_worth,
    project_loan_payoff,
    project_goal,
    what_if_analysis,
)

router = APIRouter()


# ============================================================
# Request/Response Models
# ============================================================

class GoalProjectionRequest(BaseModel):
    """Request model for goal projection."""
    monthly_savings_paise: int
    target_paise: int
    current_paise: int = 0
    annual_return: float = 0.0


class WhatIfScenarioRequest(BaseModel):
    """Request model for what-if analysis."""
    increase_savings_by_paise: int = 0
    extra_loan_payment_paise: int = 0
    extra_loan_payment_loan_id: Optional[int] = None
    new_sip_paise: int = 0
    new_sip_type: str = "equity"  # "equity" or "debt"
    equity_return_override_percent: Optional[float] = None


# ============================================================
# Endpoints
# ============================================================

@router.get("/api/projections/networth")
def get_net_worth_projection(
    months: int = Query(60, ge=1, le=600, description="Number of months to project (1-600)"),
    equity_return: float = Query(10.0, ge=0, le=100, description="Expected equity annual return (%)"),
    debt_return: float = Query(7.0, ge=0, le=100, description="Expected debt annual return (%)")
):
    """
    Project net worth over time.

    Uses current assets, liabilities, historical cashflow, and loan projections
to forecast future net worth.

    Query Parameters:
        - months: Number of months to project (default 60, max 600)
        - equity_return: Expected annual return for equity investments (default 10%)
        - debt_return: Expected annual return for debt investments (default 7%)

    Returns:
        Monthly projections with net worth, assets, liabilities,
        assumptions used, and summary statistics.
    """
    log.info("GET /api/projections/networth?months=%d&equity_return=%.1f&debt_return=%.1f",
             months, equity_return, debt_return)

    db = get_db()
    result = project_net_worth(
        db=db,
        months_ahead=months,
        equity_annual_return=equity_return,
        debt_annual_return=debt_return
    )

    return result


@router.get("/api/projections/loan-payoff")
def get_all_loan_payoff_projections():
    """
    Project payoff for all loans.

    Returns payoff projections for all active loans in the system.

    Returns:
        List of payoff projections with loan details, payoff dates,
        remaining amounts, and summary statistics.
    """
    log.info("GET /api/projections/loan-payoff")

    db = get_db()
    all_loans = db.get_loans()

    results = []
    for loan in all_loans:
        try:
            result = project_loan_payoff(
                db=db,
                loan_id=loan["id"]
            )

            # Add loan metadata
            result["loan_id"] = loan["id"]
            result["loan_name"] = loan.get("name")
            result["lender"] = loan.get("lender")

            results.append(result)
        except Exception as e:
            log.warning("Failed to project payoff for loan %d: %s", loan["id"], str(e))
            continue

    return {
        "loans": results,
        "count": len(results),
        "total_remaining_principal_paise": sum(r.get("remaining_principal_paise", 0) for r in results),
        "total_remaining_interest_paise": sum(r.get("total_remaining_interest_paise", 0) for r in results)
    }

@router.get("/api/projections/loan/{loan_id}")
def get_loan_payoff_projection(loan_id: int):
    """
    Project when a specific loan will be fully paid off.

    Uses loan_engine to replay payments and forecast remaining schedule.

    Path Parameters:
        - loan_id: ID of the loan to project

    Returns:
        Payoff date, remaining months, remaining principal,
        total remaining interest, and closed status.
    """
    log.info("GET /api/projections/loan/%d", loan_id)

    # Verify loan exists
    db = get_db()
    loan = db.get_loan(loan_id)
    if not loan:
        raise NotFoundError("Loan", loan_id)

    db = get_db()
    result = project_loan_payoff(
        db=db,
        loan_id=loan_id
    )

    # Add loan metadata
    result["loan_id"] = loan_id
    result["loan_name"] = loan.get("name")
    result["lender"] = loan.get("lender")

    return result


@router.post("/api/projections/goal")
def post_goal_projection(request: GoalProjectionRequest):
    """
    Calculate months needed to reach a financial goal.

    Pure math calculation - no database access.
    Supports edge cases: target already achieved, zero savings, zero return.

    Request Body:
        - monthly_savings_paise: Monthly contribution amount in paise
        - target_paise: Target amount to reach in paise
        - current_paise: Starting balance in paise (default 0)
        - annual_return: Expected annual return percentage (default 0)

    Returns:
        Months needed, projected date, total contributed, total returns,
        and achievability status.
    """
    log.info("POST /api/projections/goal: target=₹%.2f, monthly=₹%.2f",
             request.target_paise / 100, request.monthly_savings_paise / 100)

    result = project_goal(
        monthly_savings_paise=request.monthly_savings_paise,
        target_paise=request.target_paise,
        current_paise=request.current_paise,
        annual_return=request.annual_return
    )

    return result


@router.post("/api/projections/what-if")
def post_what_if_analysis(request: WhatIfScenarioRequest):
    """
    Compare baseline projection with a modified scenario.

    Supports modifications:
    - Increase monthly savings
    - One-time extra loan payment
    - Add new SIP
    - Override equity return rate

    Request Body:
        - increase_savings_by_paise: Additional monthly savings (default 0)
        - extra_loan_payment_paise: One-time extra payment amount (default 0)
        - extra_loan_payment_loan_id: Which loan to apply payment to (default None)
        - new_sip_paise: New monthly SIP amount (default 0)
        - new_sip_type: Type of SIP - "equity" or "debt" (default "equity")
        - equity_return_override_percent: Override equity return rate (default None)

    Returns:
        Baseline and modified projections, differences at 1y/3y/5y,
        and percentage improvement.
    """
    log.info("POST /api/projections/what-if: extra_payment=₹%.2f, new_sip=₹%.2f",
             request.extra_loan_payment_paise / 100, request.new_sip_paise / 100)

    # Build scenario dict
    scenario = {
        "increase_savings_by_paise": request.increase_savings_by_paise,
        "extra_loan_payment_paise": request.extra_loan_payment_paise,
        "extra_loan_payment_loan_id": request.extra_loan_payment_loan_id,
        "new_sip_paise": request.new_sip_paise,
        "new_sip_type": request.new_sip_type,
        "equity_return_override_percent": request.equity_return_override_percent,
    }

    db = get_db()
    result = what_if_analysis(
        db=db,
        scenario=scenario
    )

    return result
