"""Financial Optimization API endpoints.

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
router = APIRouter(prefix="/api/v1/optimization", tags=["optimization"])


def _timed_log(
    endpoint: str,
    household_id: str | None,
    duration_ms: float,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Emit structured timing log for optimization endpoints."""
    log_data = {
        "type": "optimization_request",
        "endpoint": endpoint,
        "household_id": household_id,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[OPTIMIZATION] %s | household_id=%s | %.0fms | FAIL: %s",
            endpoint, household_id, duration_ms, error,
        )
    else:
        logger.info("[OPTIMIZATION] %s | household_id=%s | %.0fms", endpoint, household_id, duration_ms)


# ============================================================
# Master Optimization Plan Endpoint
# ============================================================

@router.get("/plan")
def get_optimization_plan(
    household_id: str = Query(default="primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get comprehensive optimization plan.

    Combines surplus allocation, debt strategy, and goal prioritization.

    Args:
        household_id: Household identifier (default: "primary")

    Returns:
        Dict with recommended_actions, allocation_plan, warnings, confidence
    """
    start = time.monotonic()
    service = FinancialIntelligenceService()

    try:
        result = service.get_optimization_plan(household_id=household_id)
        _timed_log("GET /optimization/plan", household_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /optimization/plan", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Debt Strategy Endpoint
# ============================================================

@router.get("/debt-strategy")
def get_debt_strategy(
    strategy: str = Query(default="avalanche", description="Strategy: avalanche, snowball, or balanced"),
    household_id: str = Query(default="primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get recommended debt payoff strategy ranking.

    Args:
        strategy: Strategy type (avalanche, snowball, balanced)
        household_id: Household identifier (default: "primary")

    Returns:
        Dict with priority_order and strategy
    """
    start = time.monotonic()
    from src.engines.financial_intelligence import rank_debt_payoff_strategy

    try:
        # Get debt data from services
        service = FinancialIntelligenceService()
        loans = service.loan_service.get_loans()
        credit_cards = service.credit_card_service.list_cards()

        debts = [
            {"id": loan.get("id"), "outstanding_paise": int(loan.get("outstanding_paise", 0) or 0), "interest_rate_bps": int(loan.get("interest_rate_bps", 0) or 0)}
            for loan in loans
        ] + [
            {"id": card.get("id"), "outstanding_paise": int(card.get("outstanding_paise", 0) or 0), "interest_rate_bps": int(card.get("interest_rate_bps", 0) or 0)}
            for card in credit_cards
        ]

        result = rank_debt_payoff_strategy(debts=debts, strategy=strategy)
        _timed_log("GET /optimization/debt-strategy", household_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /optimization/debt-strategy", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Goal Priority Endpoint
# ============================================================

@router.get("/goal-priority")
def get_goal_priority(
    household_id: str = Query(default="primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get goal prioritization recommendations.

    Args:
        household_id: Household identifier (default: "primary")

    Returns:
        Dict with priority_order and recommendations
    """
    start = time.monotonic()
    from src.engines.financial_intelligence import optimize_goal_prioritization

    try:
        service = FinancialIntelligenceService()
        goals = service.get_household_goals(household_id=household_id, status=None)

        # Get emergency fund status
        liquidity_result = service.get_liquidity_forecast(forecast_months=3)
        emergency_deficit = max(0, liquidity_result.get("emergency_threshold_paise", 3000000) - int(liquidity_result.get("current_liquidity_paise", 0) or 0))

        emergency_fund_status = {
            "deficit_paise": emergency_deficit,
        }

        result = optimize_goal_prioritization(
            goals=goals,
            emergency_fund_status=emergency_fund_status,
        )
        _timed_log("GET /optimization/goal-priority", household_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /optimization/goal-priority", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise


# ============================================================
# Surplus Allocation Endpoint
# ============================================================

@router.get("/surplus-allocation")
def get_surplus_allocation(
    household_id: str = Query(default="primary", description="Household identifier"),
) -> dict[str, Any]:
    """Get surplus allocation recommendations.

    Args:
        household_id: Household identifier (default: "primary")

    Returns:
        Dict with allocation breakdown
    """
    start = time.monotonic()
    from src.engines.financial_intelligence import optimize_surplus_allocation

    try:
        service = FinancialIntelligenceService()
        cashflow_result = service.get_cashflow_forecast(forecast_months=1)
        monthly_surplus = (
            cashflow_result.get("forecast", [{}])[0].get("expected_surplus_paise", 0) or 0
        )

        loans = service.loan_service.get_loans()
        credit_cards = service.credit_card_service.list_cards()

        debts = [
            {"id": loan.get("id"), "outstanding_paise": int(loan.get("outstanding_paise", 0) or 0), "interest_rate_bps": int(loan.get("interest_rate_bps", 0) or 0)}
            for loan in loans
        ] + [
            {"id": card.get("id"), "outstanding_paise": int(card.get("outstanding_paise", 0) or 0), "interest_rate_bps": int(card.get("interest_rate_bps", 0) or 0)}
            for card in credit_cards
        ]

        goals = service.get_household_goals(household_id=household_id, status=None)

        liquidity_result = service.get_liquidity_forecast(forecast_months=3)
        emergency_deficit = max(0, liquidity_result.get("emergency_threshold_paise", 3000000) - int(liquidity_result.get("current_liquidity_paise", 0) or 0))

        emergency_fund_status = {
            "current_paise": int(liquidity_result.get("current_liquidity_paise", 0) or 0),
            "target_paise": liquidity_result.get("emergency_threshold_paise", 3000000),
            "deficit_paise": emergency_deficit,
        }

        result = optimize_surplus_allocation(
            monthly_surplus_paise=monthly_surplus,
            debts=debts,
            goals=goals,
            emergency_fund_status=emergency_fund_status,
        )
        _timed_log("GET /optimization/surplus-allocation", household_id, (time.monotonic() - start) * 1000)
        return result
    except Exception as e:
        _timed_log(
            "GET /optimization/surplus-allocation", household_id,
            (time.monotonic() - start) * 1000, success=False, error=str(e),
        )
        raise