"""Behaviour Engine API endpoints.

All endpoints include request timing and structured error logging.
All monetary values in integer paise, all dates in ISO-8601 format.

Follows the same pattern as other routers - no FinanceDB import,
no calculation logic, pure HTTP delegation to BehaviourService.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.errors import NotFoundError
from src.services.behaviour_service import BehaviourService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/behaviour", tags=["behaviour"])


def _timed_log(
    endpoint: str,
    household_id: str | None,
    duration_ms: float,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Emit structured timing log for behaviour endpoints."""
    log_data = {
        "type": "behaviour_request",
        "endpoint": endpoint,
        "household_id": household_id,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[BEHAVIOUR] %s | household_id=%s | %.0fms | FAIL: %s",
            endpoint, household_id, duration_ms, error,
        )
    else:
        logger.info("[BEHAVIOUR] %s | household_id=%s | %.0fms", endpoint, household_id, duration_ms)


# ============================================================
# Profile Endpoints
# ============================================================


@router.get("/profile")
def get_financial_profile(household_id: str = Query("default", description="Household identifier")) -> dict[str, Any]:
    """Get comprehensive financial behaviour profile.

    Returns financial personality classification based on transaction and account data.

    Args:
        household_id: Household identifier (default: "default")

    Returns:
        FinancialProfileResponse with profile classification
    """
    start = time.monotonic()
    service = BehaviourService()

    try:
        result = service.compute_financial_profile(household_id=household_id)
        _timed_log("GET /behaviour/profile", household_id, (time.monotonic() - start) * 1000)
        return result.model_dump()
    except Exception as e:
        _timed_log(
            "GET /behaviour/profile", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


@router.get("/wellness-score")
def get_wellness_score(household_id: str = Query("default", description="Household identifier")) -> dict[str, Any]:
    """Get the latest financial wellness score.

    Returns wellness score with band classification and component breakdown.

    Args:
        household_id: Household identifier (default: "default")

    Returns:
        WellnessScoreResponse with score, band, and components
    """
    start = time.monotonic()
    service = BehaviourService()

    try:
        result = service.get_wellness_score(household_id=household_id)
        _timed_log("GET /behaviour/wellness-score", household_id, (time.monotonic() - start) * 1000)
        return result.model_dump()
    except NotFoundError:
        _timed_log(
            "GET /behaviour/wellness-score", household_id,
            (time.monotonic() - start) * 1000, success=False, error="No snapshot available",
        )
        raise
    except Exception as e:
        _timed_log(
            "GET /behaviour/wellness-score", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


@router.get("/debt-health")
def get_debt_health(household_id: str = Query("default", description="Household identifier")) -> dict[str, Any]:
    """Get the latest debt health metrics.

    Returns FOIR, credit dependency ratio, debt cycle score, and revolver ratio.

    Args:
        household_id: Household identifier (default: "default")

    Returns:
        DebtHealthResponse with debt health metrics
    """
    start = time.monotonic()
    service = BehaviourService()

    try:
        result = service.get_debt_health(household_id=household_id)
        _timed_log("GET /behaviour/debt-health", household_id, (time.monotonic() - start) * 1000)
        return result.model_dump()
    except NotFoundError:
        _timed_log(
            "GET /behaviour/debt-health", household_id,
            (time.monotonic() - start) * 1000, success=False, error="No snapshot available",
        )
        raise
    except Exception as e:
        _timed_log(
            "GET /behaviour/debt-health", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


@router.get("/cashflow-health")
def get_cashflow_health(household_id: str = Query("default", description="Household identifier")) -> dict[str, Any]:
    """Get the latest cashflow health metrics.

    Returns cashflow stability index, income/expense stability, and monthly surplus.

    Args:
        household_id: Household identifier (default: "default")

    Returns:
        CashflowHealthResponse with cashflow health metrics
    """
    start = time.monotonic()
    service = BehaviourService()

    try:
        result = service.get_cashflow_health(household_id=household_id)
        _timed_log("GET /behaviour/cashflow-health", household_id, (time.monotonic() - start) * 1000)
        return result.model_dump()
    except NotFoundError:
        _timed_log(
            "GET /behaviour/cashflow-health", household_id,
            (time.monotonic() - start) * 1000, success=False, error="No snapshot available",
        )
        raise
    except Exception as e:
        _timed_log(
            "GET /behaviour/cashflow-health", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


@router.get("/patterns")
def get_patterns(
    household_id: str = Query("default", description="Household identifier"),
    pattern_type: str | None = Query(None, description="Filter by pattern type (e.g., IMPULSE, SUBSCRIPTION)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back for patterns"),
) -> list[dict[str, Any]]:
    """Get detected financial patterns.

    Returns patterns like impulse spending and subscriptions with strength scores.

    Args:
        household_id: Household identifier (default: "default")
        pattern_type: Optional filter for specific pattern type
        days: Number of days to look back (1-365, default: 30)

    Returns:
        List of FinancialPattern objects
    """
    start = time.monotonic()
    service = BehaviourService()

    try:
        patterns = service.get_patterns(household_id=household_id, limit=days)

        # Apply pattern_type filter if provided
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]

        result = [p.model_dump() for p in patterns]
        _timed_log("GET /behaviour/patterns", household_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /behaviour/patterns", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


@router.get("/recommendations")
def get_recommendations(
    household_id: str = Query("default", description="Household identifier"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of recommendations to return"),
    severity: str | None = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
) -> dict[str, Any]:
    """Get financial recommendations based on behaviour metrics.

    Returns actionable recommendations sorted by severity.

    Args:
        household_id: Household identifier (default: "default")
        limit: Maximum number of recommendations to return (1-50, default: 10)
        severity: Optional filter for specific severity level

    Returns:
        RecommendationsResponse with triggered recommendations
    """
    start = time.monotonic()
    service = BehaviourService()

    try:
        result = service.get_recommendations(
            household_id=household_id,
            limit=limit,
            severity_filter=severity,
        )
        _timed_log("GET /behaviour/recommendations", household_id, (time.monotonic() - start) * 1000)
        return result.model_dump()
    except NotFoundError:
        _timed_log(
            "GET /behaviour/recommendations", household_id,
            (time.monotonic() - start) * 1000, success=False, error="No snapshot available",
        )
        raise
    except Exception as e:
        _timed_log(
            "GET /behaviour/recommendations", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


@router.get("/monthly-report")
def get_monthly_report(
    period: str | None = Query(None, description="Period in YYYY-MM format (default: current month)"),
    household_id: str = Query("default", description="Household identifier"),
) -> dict[str, Any]:
    """Generate a monthly financial summary report.

    Returns comprehensive summary including wellness, debt, cashflow, patterns, and alerts.

    Args:
        period: Period in YYYY-MM format (default: current month)
        household_id: Household identifier (default: "default")

    Returns:
        MonthlySummaryResponse with comprehensive financial summary
    """
    start = time.monotonic()
    service = BehaviourService()

    # Use current month if no period specified
    if period is None:
        from datetime import date
        period = date.today().strftime("%Y-%m")

    try:
        result = service.generate_monthly_summary(period=period, household_id=household_id)
        _timed_log("GET /behaviour/monthly-report", household_id, (time.monotonic() - start) * 1000)
        return result.model_dump()
    except NotFoundError:
        _timed_log(
            "GET /behaviour/monthly-report", household_id,
            (time.monotonic() - start) * 1000, success=False, error="No snapshot available",
        )
        raise
    except Exception as e:
            _timed_log(
                "GET /behaviour/monthly-report", household_id,
                (time.monotonic() - start) * 1000, success=False, error=str(e),
            )
            raise


# ============================================================
# India-Specific Signal Endpoints (Phase 6/7)
# ============================================================


@router.get("/stress-index")
def get_stress_index(
    month: str = Query(..., description="Month in YYYY-MM format"),
    scope: str = Query("household", description="Scope: household or individual"),
    household_id: str = Query("primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get financial stress index with breakdown components.

    Computes composite stress score including credit dependency, debt rolling,
    liquidity extraction frequency, revolving behavior, and cashflow deficit.

    Args:
        month: Month in YYYY-MM format
        scope: Scope for analysis (household or individual)
        household_id: Household identifier

    Returns:
        Dict with stress score, components, and flag
    """
    start = time.monotonic()
    service = BehaviourService()

    try:
        result = service.get_stress_index(month=month, scope=scope, household_id=household_id)
        _timed_log("GET /behaviour/stress-index", household_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /behaviour/stress-index", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


@router.get("/revolver-status")
def get_revolver_status(
    card_account_id: str = Query(..., description="Credit card account ID"),
    household_id: str = Query("primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get revolver classification for a credit card account.

    Classifies card as transactor (pays in full) or revolver (carries balance)
    based on lifecycle states of events.

    Args:
        card_account_id: Credit card account ID to analyze
        household_id: Household identifier

    Returns:
        Dict with type, confidence, and counts
    """
    start = time.monotonic()
    service = BehaviourService()

    try:
        result = service.get_revolver_status(card_account_id=card_account_id, household_id=household_id)
        _timed_log("GET /behaviour/revolver-status", household_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /behaviour/revolver-status", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


@router.get("/household-divergence")
def get_household_divergence(
    month: str = Query(..., description="Month in YYYY-MM format"),
    household_id: str = Query("primary", description="Household identifier"),
) -> dict[str, Any]:
    """Detect cross-owner funding within household.

    Finds lineage links where events from different owners within the same
    household are connected, indicating potential financial interdependencies.

    Args:
        month: Month in YYYY-MM format
        household_id: Household identifier

    Returns:
        Dict with flag and divergent links
    """
    start = time.monotonic()
    service = BehaviourService()

    try:
        result = service.get_household_divergence(month=month, household_id=household_id)
        _timed_log("GET /behaviour/household-divergence", household_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /behaviour/household-divergence", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise
