"""Loan management endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from src.errors import NotFoundError
from src.models.loan_payment import LoanPaymentCreate
from src.services import LoanAnalysisService, LoanService, LoanSimulationService

router = APIRouter(prefix="/api", tags=["loans"])


class LoanCreate(BaseModel):
    """Loan creation request."""

    name: str
    lender: str
    loan_type: str  # personal | home | vehicle | education | gold | other
    principal_paise: int
    outstanding_paise: int
    interest_rate: float
    disbursed_date: str  # ISO 8601 date string
    tenure_months: int | None = None
    emi_paise: int | None = None
    next_emi_date: str | None = None
    gold_weight_grams: float | None = None
    gold_purity: str | None = None
    interest_type: str = "reducing"
    notes: str | None = None

    @field_validator("principal_paise", "outstanding_paise")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure monetary fields are non-negative."""
        if v < 0:
            raise ValueError("Monetary fields must be non-negative")
        return v


class LoanUpdate(BaseModel):
    """Loan update request."""

    outstanding_paise: int | None = None
    interest_rate: float | None = None
    tenure_months: int | None = None
    emi_paise: int | None = None
    next_emi_date: str | None = None
    notes: str | None = None


class PrepaymentSimulationRequest(BaseModel):
    """Prepayment simulation request."""

    prepayment_paise: int
    mode: str = "reduce_tenure"  # reduce_tenure | reduce_emi

    @field_validator("prepayment_paise")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Ensure prepayment amount is positive."""
        if v <= 0:
            raise ValueError("prepayment_paise must be positive")
        return v


class PrepaymentSimulationResponse(BaseModel):
    """Prepayment simulation response model."""

    original_schedule: list[dict[str, Any]]
    new_schedule: list[dict[str, Any]]
    savings: dict[str, int]
    new_remaining_months: int
    new_emi_paise: int | None


class SurplusAllocationRequest(BaseModel):
    """Surplus allocation request."""

    surplus_paise: int

    @field_validator("surplus_paise")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Ensure surplus is positive."""
        if v <= 0:
            raise ValueError("surplus_paise must be positive")
        return v


# ============================================================
# Loan CRUD Endpoints (via LoanService)
# ============================================================

@router.get("/loans")
def get_loans() -> dict[str, Any]:
    """Get all active loans via LoanService."""
    service = LoanService()
    loans = service.get_loans()
    return {"loans": loans, "count": len(loans)}


@router.post("/loans")
def create_loan(loan: LoanCreate) -> dict[str, Any]:
    """Create a new loan via LoanService."""
    service = LoanService()
    created_id = service.create_loan(
        name=loan.name,
        lender=loan.lender,
        loan_type=loan.loan_type,
        principal_paise=loan.principal_paise,
        outstanding_paise=loan.outstanding_paise,
        interest_rate=loan.interest_rate,
        disbursed_date=loan.disbursed_date,
        tenure_months=loan.tenure_months,
        emi_paise=loan.emi_paise,
        notes=loan.notes,
    )
    return {"success": True, "loan_id": created_id}


@router.put("/loans/{loan_id}")
def update_loan(loan_id: int, loan: LoanUpdate) -> dict[str, Any]:
    """Update loan via LoanService."""
    service = LoanService()
    updated = service.update_loan(loan_id, **{k: v for k, v in loan.model_dump().items() if v is not None})
    if not updated:
        raise NotFoundError(f"Loan {loan_id} not found")
    return {"success": True, "loan": updated}


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
    """Get amortization schedule via LoanService."""
    service = LoanService()
    try:
        return service.get_schedule(loan_id)
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/prepayment-simulation")
def simulate_prepayment(
    loan_id: int,
    request: PrepaymentSimulationRequest,
) -> dict[str, Any]:
    """Simulate prepayment via LoanSimulationService."""
    sim_service = LoanSimulationService()
    try:
        return sim_service.simulate_prepayment(loan_id, request.prepayment_paise, request.mode)
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/foreclosure-simulation")
def simulate_foreclosure(loan_id: int) -> dict[str, Any]:
    """Simulate foreclosure via LoanSimulationService."""
    sim_service = LoanSimulationService()
    try:
        return sim_service.simulate_foreclosure(loan_id)
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/rate-change-simulation")
def simulate_rate_change(
    loan_id: int,
    change_month: int,
    new_rate_bps: int,
) -> dict[str, Any]:
    """Simulate rate change via LoanSimulationService."""
    sim_service = LoanSimulationService()
    try:
        return sim_service.simulate_rate_change(loan_id, change_month, new_rate_bps)
    except ValueError as e:
        raise NotFoundError(str(e)) from e


# ============================================================
# Payment Endpoints
# ============================================================

@router.post("/loans/{loan_id}/payments")
def record_loan_payment(
    loan_id: int,
    payment: LoanPaymentCreate,
) -> dict[str, Any]:
    """Record a loan payment via LoanService."""
    service = LoanService()
    try:
        payment_id = service.record_payment(payment)
        return {"success": True, "payment_id": payment_id}
    except ValueError as e:
        raise NotFoundError(str(e)) from e


# ============================================================
# Analysis Endpoints
# ============================================================

@router.get("/loans/analysis/priority")
def get_loan_priority() -> list[dict[str, Any]]:
    """Get prepayment priority ranking via LoanAnalysisService."""
    analysis_service = LoanAnalysisService()
    recommendations = analysis_service.analyze_loan_priority()
    return [r.model_dump() for r in recommendations]


@router.post("/loans/{loan_id}/analysis/prepayment-vs-foreclosure")
def analyze_prepayment_vs_foreclosure(
    loan_id: int,
    request: SurplusAllocationRequest,
) -> dict[str, Any]:
    """Compare prepayment vs foreclosure via LoanAnalysisService."""
    analysis_service = LoanAnalysisService()
    try:
        recommendation = analysis_service.analyze_prepayment_vs_foreclosure(loan_id, request.surplus_paise)
        return recommendation.model_dump()
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/analysis/surplus-allocation")
def analyze_surplus_allocation(request: SurplusAllocationRequest) -> dict[str, Any]:
    """Analyze surplus allocation via LoanAnalysisService."""
    analysis_service = LoanAnalysisService()
    result = analysis_service.analyze_surplus_allocation(request.surplus_paise)
    return {
        "surplus_paise": result.surplus_paise,
        "recommendations": [r.model_dump() for r in result.recommendations],
        "total_interest_saved_paise": result.total_interest_saved_paise,
    }
