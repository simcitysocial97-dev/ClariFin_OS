"""Financial Intelligence API endpoints.

All endpoints include request timing and structured error logging.
All monetary values in integer paise, all dates in ISO-8601 format.

Follows the same pattern as other routers - no FinanceDB import,
no calculation logic, pure HTTP delegation to FinancialIntelligenceService.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.services.financial_intelligence_service import FinancialIntelligenceService

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/financial-intelligence", tags=["financial-intelligence"]
)


def _timed_log(
    endpoint: str,
    household_id: str | None,
    duration_ms: float,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Emit structured timing log for financial intelligence endpoints."""
    log_data = {
        "type": "financial_intelligence_request",
        "endpoint": endpoint,
        "household_id": household_id,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[FINANCIAL_INTELLIGENCE] %s | household_id=%s | %.0fms | FAIL: %s",
            endpoint,
            household_id,
            duration_ms,
            error,
        )
    else:
        logger.info(
            "[FINANCIAL_INTELLIGENCE] %s | household_id=%s | %.0fms",
            endpoint,
            household_id,
            duration_ms,
        )


# ============================================================
# Cashflow Forecast Endpoint
# ============================================================


@router.get("/cashflow-forecast")
def get_cashflow_forecast(
    forecast_months: int = Query(
        default=3, ge=1, le=12, description="Number of months to forecast"
    ),
    household_id: str = Query(default="primary", description="Household identifier"),
    owner_id: str = Query(
        default="self",
        description="Owner filter (self for individual, or different owner)",
    ),
) -> dict[str, Any]:
    """Get cashflow forecast for the household.

    Projects future monthly income, expenses, and surplus using weighted moving average.
    Returns confidence score based on historical variance.
    Uses TRUE cashflow adjusted for artificial income (cash advances, transfers).

    Args:
        forecast_months: Number of months to forecast (1-12, default: 3)
        household_id: Household identifier (default: "primary")
        owner_id: Owner filter - "self" for individual, None for household-wide

    Returns:
        Dict with forecast list and confidence score
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_cashflow_forecast(
            forecast_months=forecast_months,
            household_id=household_id,
            owner_id=owner_id,
        )
        _timed_log(
            "GET /financial-intelligence/cashflow-forecast",
            household_id,
            (time.monotonic() - start) * 1000,
        )
        return result
    except Exception as e:
        _timed_log(
            "GET /financial-intelligence/cashflow-forecast",
            household_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise


# ============================================================
# Liquidity Forecast Endpoint
# ============================================================


@router.get("/liquidity-forecast")
def get_liquidity_forecast(
    forecast_months: int = Query(
        default=3, ge=1, le=12, description="Number of months to forecast"
    ),
    emergency_threshold_paise: int = Query(
        default=3000000,
        description="Emergency threshold in paise (default: 3,000,000 = ₹30,000)",
    ),
    household_id: str = Query(default="primary", description="Household identifier"),
    owner_id: str = Query(
        default="self", description="Owner filter (self for individual)"
    ),
) -> dict[str, Any]:
    """Get liquidity forecast for the household.

    Predicts future liquidity position and identifies potential stress points.

    Args:
        forecast_months: Number of months to forecast (1-12, default: 3)
        emergency_threshold_paise: Emergency threshold in paise (default: 3,000,000 paise = ₹30,000)
        household_id: Household identifier (default: "primary")
        owner_id: Owner filter - "self" for individual, None for household-wide

    Returns:
        Dict with months_until_stress, projected_min_balance_paise, and risk_level
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_liquidity_forecast(
            forecast_months=forecast_months,
            emergency_threshold_paise=emergency_threshold_paise,
            household_id=household_id,
            owner_id=owner_id,
        )
        _timed_log(
            "GET /financial-intelligence/liquidity-forecast",
            household_id,
            (time.monotonic() - start) * 1000,
        )
        return result
    except Exception as e:
        _timed_log(
            "GET /financial-intelligence/liquidity-forecast",
            household_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise


# ============================================================
# Credit Forecast Endpoint
# ============================================================


@router.get("/credit-forecast")
def get_credit_forecast(
    month: str | None = Query(
        default=None, description="Month in YYYY-MM format (default: current month)"
    ),
    household_id: str = Query(default="primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get credit dependency forecast.

    Predicts future credit utilization trends based on revolving behavior.

    Args:
        month: Month in YYYY-MM format (default: current month)
        household_id: Household identifier (default: "primary")

    Returns:
        Dict with current/forecast dependency ratios and trend
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_credit_forecast(month=month, household_id=household_id)
        _timed_log(
            "GET /financial-intelligence/credit-forecast",
            household_id,
            (time.monotonic() - start) * 1000,
        )
        return result
    except Exception as e:
        _timed_log(
            "GET /financial-intelligence/credit-forecast",
            household_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise


# ============================================================
# Financial Outlook Endpoint
# ============================================================


@router.get("/outlook")
def get_financial_outlook(
    forecast_months: int = Query(
        default=3, ge=1, le=12, description="Number of months to forecast"
    ),
    emergency_threshold_paise: int = Query(
        default=3000000,
        description="Emergency threshold in paise (default: 3,000,000 = ₹30,000)",
    ),
    household_id: str = Query(default="primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get comprehensive financial outlook.

    Combines cashflow, liquidity, and credit forecasts with risk flags.

    Args:
        forecast_months: Number of months to forecast (1-12, default: 3)
        emergency_threshold_paise: Emergency threshold in paise (default: 3,000,000 paise = ₹30,000)
        household_id: Household identifier

    Returns:
        Dict with cashflow, liquidity, credit forecasts and risk_flags
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_financial_outlook(
            forecast_months=forecast_months,
            emergency_threshold_paise=emergency_threshold_paise,
            household_id=household_id,
        )
        _timed_log(
            "GET /financial-intelligence/outlook",
            household_id,
            (time.monotonic() - start) * 1000,
        )
        return result
    except Exception as e:
        _timed_log(
            "GET /financial-intelligence/outlook",
            household_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise


# ============================================================
# Financial Intelligence Report Endpoint
# ============================================================


@router.get("/report")
def get_financial_intelligence_report(
    household_id: str = Query(default="primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get comprehensive financial intelligence report.

    Aggregates data from all financial domains:
    - Behaviour (wellness, credit dependency)
    - Cashflow (monthly surplus)
    - Liquidity (forecast)
    - Debts (loans, credit cards)
    - Goals (active goals)
    - Optimization (recommended actions)

    Args:
        household_id: Household identifier (default: "primary")

    Returns:
        IntelligenceReport with snapshot, health_score, priorities, risks, opportunities, confidence
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_financial_intelligence_report(household_id=household_id)
        _timed_log(
            "GET /financial-intelligence/report",
            household_id,
            (time.monotonic() - start) * 1000,
        )
        return result
    except Exception as e:
        _timed_log(
            "GET /financial-intelligence/report",
            household_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise


# ============================================================
# Financial Intelligence Priorities Endpoint
# ============================================================


@router.get("/priorities")
def get_financial_intelligence_priorities(
    household_id: str = Query(default="primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get ranked financial priorities.

    Returns only the priority actions from the intelligence report.

    Args:
        household_id: Household identifier (default: "primary")

    Returns:
        Dict with priorities list
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_financial_intelligence_report(household_id=household_id)
        _timed_log(
            "GET /financial-intelligence/priorities",
            household_id,
            (time.monotonic() - start) * 1000,
        )
        return {"priorities": result.get("priorities", [])}
    except Exception as e:
        _timed_log(
            "GET /financial-intelligence/priorities",
            household_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise


# ============================================================
# Financial Intelligence Confidence Endpoint
# ============================================================


@router.get("/confidence")
def get_financial_intelligence_confidence(
    household_id: str = Query(default="primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get intelligence data quality and confidence.

    Returns only the confidence metadata from the intelligence report.

    Args:
        household_id: Household identifier (default: "primary")

    Returns:
        Confidence metadata with confidence score and data quality label
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_financial_intelligence_report(household_id=household_id)
        _timed_log(
            "GET /financial-intelligence/confidence",
            household_id,
            (time.monotonic() - start) * 1000,
        )
        return {"confidence": result.get("confidence", {})}
    except Exception as e:
        _timed_log(
            "GET /financial-intelligence/confidence",
            household_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise
