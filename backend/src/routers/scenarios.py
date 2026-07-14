"""Financial Scenario Simulation API endpoints.

All endpoints include request timing and structured error logging.
All monetary values in integer paise, all dates in ISO-8601 format.

Follows the same pattern as other routers - no FinanceDB import,
no calculation logic, pure HTTP delegation to FinancialIntelligenceService.
Scenarios are never persisted - they are pure calculations.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.financial_intelligence_service import FinancialIntelligenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


def _timed_log(
    endpoint: str,
    duration_ms: float,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Emit structured timing log for scenario endpoints."""
    log_data = {
        "type": "scenario_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[SCENARIO] %s | %.0fms | FAIL: %s",
            endpoint, duration_ms, error,
        )
    else:
        logger.info("[SCENARIO] %s | %.0fms", endpoint, duration_ms)


# ============================================================
# Expense Reduction Scenario
# ============================================================

@router.post("/expense-reduction")
def simulate_expense_reduction(
    reduction_paise: int = Query(..., gt=0, description="Monthly expense reduction in paise"),
    household_id: str = Query("primary", description="Household identifier"),
    forecast_months: int = Query(default=12, ge=1, le=12, description="Forecast horizon"),
) -> dict[str, Any]:
    """Simulate expense reduction scenario.

    What happens if monthly expenses reduce?
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.simulate_expense_change(
            reduction_paise=reduction_paise,
            household_id=household_id,
            forecast_months=forecast_months,
        )
        _timed_log("POST /scenarios/expense-reduction", (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "POST /scenarios/expense-reduction",
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Income Change Scenario
# ============================================================

@router.post("/income-change")
def simulate_income_change(
    change_paise: int = Query(..., description="Monthly income change in paise (positive/negative)"),
    household_id: str = Query("primary", description="Household identifier"),
    forecast_months: int = Query(default=12, ge=1, le=12, description="Forecast horizon"),
) -> dict[str, Any]:
    """Simulate income change scenario.

    What happens if salary/income changes?
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.simulate_income_change(
            change_paise=change_paise,
            household_id=household_id,
            forecast_months=forecast_months,
        )
        _timed_log("POST /scenarios/income-change", (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "POST /scenarios/income-change",
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Debt Prepayment Scenario
# ============================================================

@router.post("/debt-prepayment")
def simulate_debt_prepayment(
    extra_payment_paise: int = Query(..., gt=0, description="Extra monthly payment toward debt in paise"),
    household_id: str = Query("primary", description="Household identifier"),
) -> dict[str, Any]:
    """Simulate debt prepayment scenario.

    What happens if I pay extra toward debt?
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.simulate_debt_prepayment(
            extra_payment_paise=extra_payment_paise,
            household_id=household_id,
        )
        _timed_log("POST /scenarios/debt-prepayment", (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "POST /scenarios/debt-prepayment",
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# New Loan Scenario
# ============================================================

@router.post("/new-loan")
def simulate_new_loan(
    principal_paise: int = Query(..., gt=0, description="Loan principal in paise"),
    annual_rate_bps: int = Query(..., gt=0, description="Annual interest rate in basis points"),
    tenure_months: int = Query(..., gt=0, description="Loan tenure in months"),
    household_id: str = Query("primary", description="Household identifier"),
) -> dict[str, Any]:
    """Simulate new loan impact scenario.

    What happens if I take a new loan?
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.simulate_new_loan(
            principal_paise=principal_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=tenure_months,
            household_id=household_id,
        )
        _timed_log("POST /scenarios/new-loan", (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "POST /scenarios/new-loan",
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Credit Behavior Change Scenario
# ============================================================

@router.post("/credit-behaviour")
def simulate_credit_behaviour(
    average_interest_rate_bps: int | None = Query(
        default=None, description="Average credit interest rate in basis points (optional)"
    ),
    household_id: str = Query("primary", description="Household identifier"),
) -> dict[str, Any]:
    """Simulate credit behavior change scenario.

    What happens if revolving behaviour stops?
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.simulate_credit_change(
            household_id=household_id,
            average_interest_rate_bps=average_interest_rate_bps,
        )
        _timed_log("POST /scenarios/credit-behaviour", (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "POST /scenarios/credit-behaviour",
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Compare Scenario
# ============================================================

@router.post("/compare")
def compare_scenarios(
    request: dict[str, Any],
) -> dict[str, Any]:
    """Compare baseline vs scenario results.

    Generic comparison between two financial states.
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        baseline = request.get("baseline", {})
        scenario = request.get("scenario", {})
        result = service.compare_scenarios(baseline, scenario)
        _timed_log("POST /scenarios/compare", (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "POST /scenarios/compare",
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise
