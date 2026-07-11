"""Loan management endpoints.

All endpoints include request timing and structured error logging.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter

from src.errors import NotFoundError
from src.models.loan import LoanCreateRequest, LoanResponse, LoanUpdateRequest, ScheduleResponse
from src.models.loan_payment import LoanPaymentCreate
from src.models.loan_simulation import (
    ForeclosureSimulationResponse,
    PaymentRequest,
    PaymentResponse,
    PrepaymentSimulationRequest,
    PrepaymentSimulationResponse,
    RateChangeSimulationRequest,
)
from src.services import LoanAnalysisService, LoanService, LoanSimulationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["loans"])


def _timed_log(endpoint: str, loan_id: int | None, duration_ms: float, success: bool = True, error: str | None = None) -> None:
    """Emit structured timing log for loan endpoints."""
    log_data = {
        "type": "loan_request",
        "endpoint": endpoint,
        "loan_id": loan_id,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning("[LOAN] %s | loan_id=%s | %.0fms | FAIL: %s", endpoint, loan_id, duration_ms, error)
    else:
        logger.info("[LOAN] %s | loan_id=%s | %.0fms", endpoint, loan_id, duration_ms)


# ============================================================
# Loan CRUD Endpoints (via LoanService)
# ============================================================

@router.get("/loans")
def get_loans() -> list[dict[str, Any]]:
    """Get all active loans via LoanService.

    Returns array of loan objects directly (not wrapped in object).
    """
    start = time.monotonic()
    service = LoanService()
    loans = service.get_loans()
    result = [LoanResponse.from_loan_dict(loan).model_dump() for loan in loans]
    _timed_log("GET /loans", None, (time.monotonic() - start) * 1000)
    return result


@router.get("/loans/{loan_id}")
def get_loan(loan_id: int) -> dict[str, Any]:
    """Get loan details via LoanService."""
    start = time.monotonic()
    service = LoanService()
    try:
        loan = service.get_loan(loan_id)
        result = LoanResponse.from_loan_dict(loan).model_dump()
        _timed_log("GET /loans/{id}", loan_id, (time.monotonic() - start) * 1000)
        return result
    except ValueError as e:
        _timed_log("GET /loans/{id}", loan_id, (time.monotonic() - start) * 1000, success=False, error=str(e))
        raise NotFoundError(str(e)) from e


@router.post("/loans")
def create_loan(request: LoanCreateRequest) -> dict[str, Any]:
    """Create a new loan via LoanService.

    Uses rate_bps as canonical field; converts to interest_rate for repository.
    """
    start = time.monotonic()
    service = LoanService()
    interest_rate = request.rate_bps / 100.0
    created_id = service.create_loan(
        name=request.name,
        lender=request.lender,
        loan_type=request.loan_type,
        principal_paise=request.principal_paise,
        outstanding_paise=request.outstanding_paise or request.principal_paise,
        interest_rate=interest_rate,
        disbursed_date=request.disbursed_date,
        tenure_months=request.tenure_months,
        emi_paise=request.emi_paise,
    )
    _timed_log("POST /loans", created_id, (time.monotonic() - start) * 1000)
    return {"success": True, "loan_id": created_id}


@router.put("/loans/{loan_id}")
def update_loan(loan_id: int, request: LoanUpdateRequest) -> dict[str, Any]:
    """Update loan via LoanService."""
    start = time.monotonic()
    service = LoanService()

    update_data: dict[str, Any] = {}
    if request.outstanding_paise is not None:
        update_data["outstanding_paise"] = request.outstanding_paise
    if request.rate_bps is not None:
        update_data["interest_rate"] = request.rate_bps / 100.0
    if request.tenure_months is not None:
        update_data["tenure_months"] = request.tenure_months
    if request.emi_paise is not None:
        update_data["emi_paise"] = request.emi_paise
    if request.notes is not None:
        update_data["notes"] = request.notes

    updated = service.update_loan(loan_id, **update_data)
    if not updated:
        _timed_log("PUT /loans/{id}", loan_id, (time.monotonic() - start) * 1000, success=False, error="Not found")
        raise NotFoundError(f"Loan {loan_id} not found")
    _timed_log("PUT /loans/{id}", loan_id, (time.monotonic() - start) * 1000)
    return {"success": True}


@router.delete("/loans/{loan_id}")
def delete_loan(loan_id: int) -> dict[str, Any]:
    """Soft delete loan via LoanService."""
    start = time.monotonic()
    service = LoanService()
    success = service.delete_loan(loan_id)
    if not success:
        _timed_log("DELETE /loans/{id}", loan_id, (time.monotonic() - start) * 1000, success=False, error="Not found")
        raise NotFoundError(f"Loan {loan_id} not found")
    _timed_log("DELETE /loans/{id}", loan_id, (time.monotonic() - start) * 1000)
    return {"success": True}


# ============================================================
# Schedule and Simulation Endpoints
# ============================================================

@router.get("/loans/{loan_id}/schedule")
def get_loan_schedule(loan_id: int) -> dict[str, Any]:
    """Get amortization schedule via LoanService.

    Returns schedule with loan_id, emi_paise, total_interest_paise, and schedule rows.
    """
    start = time.monotonic()
    service = LoanService()
    try:
        result = service.get_schedule(loan_id)

        # Check for large schedules (>360 rows) and log warning
        schedule_rows = result["schedule"]
        if len(schedule_rows) > 360:
            logger.warning(
                "Large schedule generated: loan_id=%s, rows=%d",
                loan_id, len(schedule_rows)
            )

        response = ScheduleResponse.from_schedule_data(
            loan_id=loan_id,
            emi_paise=result["emi_paise"],
            total_interest_paise=result["total_interest_paise"],
            schedule=schedule_rows,
        ).model_dump()
        _timed_log("GET /loans/{id}/schedule", loan_id, (time.monotonic() - start) * 1000)
        return response
    except ValueError as e:
        _timed_log("GET /loans/{id}/schedule", loan_id, (time.monotonic() - start) * 1000, success=False, error=str(e))
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/prepayment-simulation")
def simulate_prepayment(
    loan_id: int,
    request: PrepaymentSimulationRequest,
) -> dict[str, Any]:
    """Simulate prepayment via LoanSimulationService.

    Returns spec-compliant response with original_interest_paise, new_interest_paise, etc.
    """
    start = time.monotonic()
    sim_service = LoanSimulationService()
    try:
        result = sim_service.simulate_prepayment(
            loan_id,
            request.amount_paise,
            request.mode,
        )
        response = PrepaymentSimulationResponse(
            original_interest_paise=result["original_interest_paise"],
            new_interest_paise=result["new_interest_paise"],
            interest_saved_paise=result["interest_saved_paise"],
            tenure_saved_months=result["tenure_saved_months"],
        ).model_dump()
        _timed_log("POST /loans/{id}/prepayment-simulation", loan_id, (time.monotonic() - start) * 1000)
        return response
    except ValueError as e:
        _timed_log("POST /loans/{id}/prepayment-simulation", loan_id, (time.monotonic() - start) * 1000, success=False, error=str(e))
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/foreclosure-simulation")
def simulate_foreclosure(loan_id: int) -> dict[str, Any]:
    """Simulate foreclosure via LoanSimulationService.

    Returns spec-compliant response with outstanding_paise, penalty_paise, foreclosure_amount_paise.
    """
    start = time.monotonic()
    sim_service = LoanSimulationService()
    try:
        result = sim_service.simulate_foreclosure(loan_id)
        response = ForeclosureSimulationResponse(
            outstanding_paise=result["outstanding_paise"],
            penalty_paise=result["penalty_paise"],
            foreclosure_amount_paise=result["foreclosure_amount_paise"],
        ).model_dump()
        _timed_log("POST /loans/{id}/foreclosure-simulation", loan_id, (time.monotonic() - start) * 1000)
        return response
    except ValueError as e:
        _timed_log("POST /loans/{id}/foreclosure-simulation", loan_id, (time.monotonic() - start) * 1000, success=False, error=str(e))
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/rate-change-simulation")
def simulate_rate_change(
    loan_id: int,
    request: RateChangeSimulationRequest,
) -> dict[str, Any]:
    """Simulate rate change via LoanSimulationService.

    Uses request body instead of query params.
    """
    start = time.monotonic()
    sim_service = LoanSimulationService()
    try:
        result = sim_service.simulate_rate_change(loan_id, request.month, request.new_rate_bps)
        _timed_log("POST /loans/{id}/rate-change-simulation", loan_id, (time.monotonic() - start) * 1000)
        return result
    except ValueError as e:
        _timed_log("POST /loans/{id}/rate-change-simulation", loan_id, (time.monotonic() - start) * 1000, success=False, error=str(e))
        raise NotFoundError(str(e)) from e


# ============================================================
# Payment Endpoints
# ============================================================

@router.post("/loans/{loan_id}/payments")
def record_loan_payment(
    loan_id: int,
    request: PaymentRequest,
) -> dict[str, Any]:
    """Record a loan payment via LoanService."""
    start = time.monotonic()
    service = LoanService()
    try:
        payment = LoanPaymentCreate(
            loan_id=loan_id,
            payment_date=request.payment_date,
            amount_paise=request.amount_paise,
            principal_paise=request.principal_paise or 0,
            interest_paise=request.interest_paise or 0,
            late_fee_paise=request.late_fee_paise if request.late_fee_paise is not None else 0,
            source_account_id=request.source_account_id,
        )
        payment_id = service.record_payment(payment)
        _timed_log("POST /loans/{id}/payments", loan_id, (time.monotonic() - start) * 1000)
        return PaymentResponse(success=True, payment_id=payment_id).model_dump()
    except ValueError as e:
        _timed_log("POST /loans/{id}/payments", loan_id, (time.monotonic() - start) * 1000, success=False, error=str(e))
        raise NotFoundError(str(e)) from e


# ============================================================
# Analysis Endpoints
# ============================================================

@router.get("/loans/analysis/priority")
def get_loan_priority() -> list[dict[str, Any]]:
    """Get prepayment priority ranking via LoanAnalysisService.

    Returns array of recommendations matching spec format.
    """
    start = time.monotonic()
    analysis_service = LoanAnalysisService()
    recommendations = analysis_service.analyze_loan_priority()
    result = [{"loan_id": r.loan_id, "action": r.action, "reason": r.reason,
             "interest_saved_paise": r.interest_saved_paise, "tenure_saved_months": r.tenure_saved_months}
            for r in recommendations]
    _timed_log("GET /loans/analysis/priority", None, (time.monotonic() - start) * 1000)
    return result


@router.post("/loans/{loan_id}/analysis/prepayment-vs-foreclosure")
def analyze_prepayment_vs_foreclosure(
    loan_id: int,
    request: PaymentRequest,  # Reuse for surplus_paise
) -> dict[str, Any]:
    """Compare prepayment vs foreclosure via LoanAnalysisService."""
    start = time.monotonic()
    analysis_service = LoanAnalysisService()
    try:
        recommendation = analysis_service.analyze_prepayment_vs_foreclosure(loan_id, request.amount_paise)
        result = {
            "loan_id": recommendation.loan_id,
            "action": recommendation.action,
            "reason": recommendation.reason,
            "interest_saved_paise": recommendation.interest_saved_paise,
            "tenure_saved_months": recommendation.tenure_saved_months,
        }
        _timed_log("POST /loans/{id}/analysis/prepayment-vs-foreclosure", loan_id, (time.monotonic() - start) * 1000)
        return result
    except ValueError as e:
        _timed_log("POST /loans/{id}/analysis/prepayment-vs-foreclosure", loan_id, (time.monotonic() - start) * 1000, success=False, error=str(e))
        raise NotFoundError(str(e)) from e


@router.post("/loans/analysis/surplus-allocation")
def analyze_surplus_allocation(request: PaymentRequest) -> dict[str, Any]:
    """Analyze surplus allocation via LoanAnalysisService."""
    start = time.monotonic()
    analysis_service = LoanAnalysisService()
    result = analysis_service.analyze_surplus_allocation(request.amount_paise)
    response = {
        "surplus_paise": result.surplus_paise,
        "recommendations": [{"loan_id": r.loan_id, "action": r.action, "reason": r.reason,
                            "interest_saved_paise": r.interest_saved_paise, "tenure_saved_months": r.tenure_saved_months}
                           for r in result.recommendations],
        "total_interest_saved_paise": result.total_interest_saved_paise,
    }
    _timed_log("POST /loans/analysis/surplus-allocation", None, (time.monotonic() - start) * 1000)
    return response