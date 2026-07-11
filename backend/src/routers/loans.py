"""Loan management endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from src.errors import NotFoundError
from src.models.loan_payment import LoanPaymentCreate
from src.repositories.loan_repository import LoanRepository
from src.services import LoanService

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


@router.get("/loans")
def get_loans() -> dict[str, Any]:
    """Get all active loans (domain models) with computed summary."""
    repo = LoanRepository()
    loans = repo.get_all_models()
    raw = repo.get_all()

    total_outstanding = sum(r["outstanding_paise"] for r in raw)
    total_principal = sum(loan.principal.paise for loan in loans)
    total_emi = sum(loan.emi.paise for loan in loans)

    return {
        "loans": loans,
        "summary": {
            "total_loans": len(loans),
            "total_outstanding_paise": total_outstanding,
            "total_principal_paise": total_principal,
            "total_monthly_emi_paise": total_emi,
        },
    }


@router.post("/loans")
def create_loan(loan: LoanCreate) -> dict[str, Any]:
    """Create a new loan record."""
    repo = LoanRepository()
    created = repo.create(
        name=loan.name,
        lender=loan.lender,
        loan_type=loan.loan_type,
        principal_paise=loan.principal_paise,
        outstanding_paise=loan.outstanding_paise,
        interest_rate=loan.interest_rate,
        disbursed_date=loan.disbursed_date,
        tenure_months=loan.tenure_months,
        emi_paise=loan.emi_paise,
        next_emi_date=loan.next_emi_date,
        gold_weight_grams=loan.gold_weight_grams,
        gold_purity=loan.gold_purity,
        interest_type=loan.interest_type,
        notes=loan.notes,
    )
    return {"success": True, "loan": created}


@router.put("/loans/{loan_id}")
def update_loan(loan_id: str, loan: LoanUpdate) -> dict[str, Any]:
    """Update loan outstanding or other fields."""
    repo = LoanRepository()
    updated = repo.update(
        loan_id,
        **{k: v for k, v in loan.model_dump().items() if v is not None}
    )
    if not updated:
        raise NotFoundError(f"Loan {loan_id} not found")
    return {"success": True, "loan": updated}


@router.delete("/loans/{loan_id}")
def delete_loan(loan_id: str) -> dict[str, Any]:
    """Soft delete a loan."""
    repo = LoanRepository()
    success = repo.delete(loan_id)
    if not success:
        raise NotFoundError(f"Loan {loan_id} not found")
    return {"success": True}


@router.get("/loans/{loan_id}/schedule")
def get_loan_schedule(loan_id: int) -> dict[str, Any]:
    """Get amortization schedule for a loan using LoanService."""
    service = LoanService()
    try:
        return service.get_amortization_schedule(loan_id)
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/prepayment-simulation")
def simulate_prepayment(
    loan_id: int,
    request: PrepaymentSimulationRequest
) -> PrepaymentSimulationResponse:
    """Simulate impact of a prepayment using LoanService."""
    service = LoanService()
    try:
        return service.simulate_prepayment(loan_id, request.prepayment_paise, request.mode)  # type: ignore
    except ValueError as e:
        raise NotFoundError(str(e)) from e


@router.post("/loans/{loan_id}/payments")
def record_loan_payment(
    loan_id: int,
    payment: LoanPaymentCreate
) -> dict[str, Any]:
    """Record a loan payment."""
    service = LoanService()
    try:
        payment_id = service.record_payment(payment)
        return {"success": True, "payment_id": payment_id}
    except ValueError as e:
        raise NotFoundError(str(e)) from e
