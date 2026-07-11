"""Loan management endpoints."""

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

router = APIRouter(prefix="/api", tags=["loans"])


# ============================================================
# Loan CRUD Endpoints (via LoanService)
# ============================================================

@router.get("/loans")
def get_loans() -> list[dict[str, Any]]:
    """Get all active loans via LoanService.

    Returns array of loan objects directly (not wrapped in object).
    """
    service = LoanService()
    loans = service.get_loans()
    return [LoanResponse.from_loan_dict(loan).model_dump() for loan in loans]


@router.get("/loans/{loan_id}")
def get_loan(loan_id: int) -> dict[str, Any]:
    """Get loan details via LoanService."""
    service = LoanService()
    try:
        loan = service.get_loan(loan_id)
        return LoanResponse.from_loan_dict(loan).model_dump()
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans")
def create_loan(request: LoanCreateRequest) -> dict[str, Any]:
    """Create a new loan via LoanService.

    Uses rate_bps as canonical field; converts to interest_rate for repository.
    """
    service = LoanService()
    # Convert rate_bps to interest_rate float for repository compatibility
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
    return {"success": True, "loan_id": created_id}


@router.put("/loans/{loan_id}")
def update_loan(loan_id: int, request: LoanUpdateRequest) -> dict[str, Any]:
    """Update loan via LoanService."""
    service = LoanService()

    # Build update kwargs with proper field mapping
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
        raise NotFoundError(f"Loan {loan_id} not found")
    return {"success": True}


@router.delete("/loans/{loan_id}")
def delete_loan(loan_id: int) -> dict[str, Any]:
    """Soft delete loan via LoanService."""
    service = LoanService()
    success = service.delete_loan(loan_id)
    if not success:
        raise NotFoundError(f"Loan {loan_id} not found")
    return {"success": True}


# ============================================================
# Schedule and Simulation Endpoints
# ============================================================

@router.get("/loans/{loan_id}/schedule")
def get_loan_schedule(loan_id: int) -> dict[str, Any]:
    """Get amortization schedule via LoanService.

    Returns schedule with loan_id, emi_paise, total_interest_paise, and schedule rows.
    """
    service = LoanService()
    try:
        result = service.get_schedule(loan_id)
        return ScheduleResponse.from_schedule_data(
            loan_id=loan_id,
            emi_paise=result["emi_paise"],
            total_interest_paise=result["total_interest_paise"],
            schedule=result["schedule"],
        ).model_dump()
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/prepayment-simulation")
def simulate_prepayment(
    loan_id: int,
    request: PrepaymentSimulationRequest,
) -> dict[str, Any]:
    """Simulate prepayment via LoanSimulationService.

    Returns spec-compliant response with original_interest_paise, new_interest_paise, etc.
    """
    sim_service = LoanSimulationService()
    try:
        result = sim_service.simulate_prepayment(
            loan_id,
            request.amount_paise,
            request.mode,
        )
        # Transform to spec format
        return PrepaymentSimulationResponse(
            original_interest_paise=result["original_interest_paise"],
            new_interest_paise=result["new_interest_paise"],
            interest_saved_paise=result["interest_saved_paise"],
            tenure_saved_months=result["tenure_saved_months"],
        ).model_dump()
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/foreclosure-simulation")
def simulate_foreclosure(loan_id: int) -> dict[str, Any]:
    """Simulate foreclosure via LoanSimulationService.

    Returns spec-compliant response with outstanding_paise, penalty_paise, foreclosure_amount_paise.
    """
    sim_service = LoanSimulationService()
    try:
        result = sim_service.simulate_foreclosure(loan_id)
        return ForeclosureSimulationResponse(
            outstanding_paise=result["outstanding_paise"],
            penalty_paise=result["penalty_paise"],
            foreclosure_amount_paise=result["foreclosure_amount_paise"],
        ).model_dump()
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/rate-change-simulation")
def simulate_rate_change(
    loan_id: int,
    request: RateChangeSimulationRequest,
) -> dict[str, Any]:
    """Simulate rate change via LoanSimulationService.

    Uses request body instead of query params.
    """
    sim_service = LoanSimulationService()
    try:
        result = sim_service.simulate_rate_change(loan_id, request.month, request.new_rate_bps)
        return result
    except ValueError as e:
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
        return PaymentResponse(success=True, payment_id=payment_id).model_dump()
    except ValueError as e:
        raise NotFoundError(str(e)) from e


# ============================================================
# Analysis Endpoints
# ============================================================

@router.get("/loans/analysis/priority")
def get_loan_priority() -> list[dict[str, Any]]:
    """Get prepayment priority ranking via LoanAnalysisService.

    Returns array of recommendations matching spec format.
    """
    analysis_service = LoanAnalysisService()
    recommendations = analysis_service.analyze_loan_priority()
    return [{"loan_id": r.loan_id, "action": r.action, "reason": r.reason,
             "interest_saved_paise": r.interest_saved_paise, "tenure_saved_months": r.tenure_saved_months}
            for r in recommendations]


@router.post("/loans/{loan_id}/analysis/prepayment-vs-foreclosure")
def analyze_prepayment_vs_foreclosure(
    loan_id: int,
    request: PaymentRequest,  # Reuse for surplus_paise
) -> dict[str, Any]:
    """Compare prepayment vs foreclosure via LoanAnalysisService."""
    analysis_service = LoanAnalysisService()
    try:
        recommendation = analysis_service.analyze_prepayment_vs_foreclosure(loan_id, request.amount_paise)
        return {
            "loan_id": recommendation.loan_id,
            "action": recommendation.action,
            "reason": recommendation.reason,
            "interest_saved_paise": recommendation.interest_saved_paise,
            "tenure_saved_months": recommendation.tenure_saved_months,
        }
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/analysis/surplus-allocation")
def analyze_surplus_allocation(request: PaymentRequest) -> dict[str, Any]:
    """Analyze surplus allocation via LoanAnalysisService."""
    analysis_service = LoanAnalysisService()
    result = analysis_service.analyze_surplus_allocation(request.amount_paise)
    return {
        "surplus_paise": result.surplus_paise,
        "recommendations": [{"loan_id": r.loan_id, "action": r.action, "reason": r.reason,
                            "interest_saved_paise": r.interest_saved_paise, "tenure_saved_months": r.tenure_saved_months}
                           for r in result.recommendations],
        "total_interest_saved_paise": result.total_interest_saved_paise,
    }
