"""Loan management endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from src.errors import NotFoundError
from src.repositories.loan_repository import LoanRepository

router = APIRouter(prefix="/api", tags=["loans"])


class LoanCreate(BaseModel):
    """Loan creation request."""
    name: str
    lender: str
    loan_type: str  # personal | home | vehicle | education | gold | other
    principal_paise: int
    outstanding_paise: int
    interest_rate: float
    disbursed_date: str
    tenure_months: int | None = None
    emi_paise: int | None = None
    next_emi_date: str | None = None
    gold_weight_grams: float | None = None
    gold_purity: str | None = None
    interest_type: str = 'reducing'
    notes: str | None = None


class LoanUpdate(BaseModel):
    """Loan update request."""
    outstanding_paise: int | None = None
    interest_rate: float | None = None
    tenure_months: int | None = None
    emi_paise: int | None = None
    next_emi_date: str | None = None
    notes: str | None = None


class PrepaymentRequest(BaseModel):
    """Prepayment simulation request."""
    prepayment_paise: int
    mode: str = 'reduce_tenure'  # reduce_tenure | reduce_emi


@router.get("/loans")
def get_loans() -> dict:
    """Get all active loans (domain models) with computed summary."""
    repo = LoanRepository()
    loans = repo.get_all_models()
    raw = repo.get_all()

    total_outstanding = sum(r['outstanding_paise'] for r in raw)
    total_principal = sum(loan.principal.paise for loan in loans)
    total_emi = sum(loan.emi.paise for loan in loans)

    return {
        "loans": loans,
        "summary": {
            "total_loans": len(loans),
            "total_outstanding_paise": total_outstanding,
            "total_principal_paise": total_principal,
            "total_monthly_emi_paise": total_emi,
        }
    }


@router.post("/loans")
def create_loan(loan: LoanCreate) -> dict:
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
def update_loan(loan_id: str, loan: LoanUpdate) -> dict:
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
def delete_loan(loan_id: str) -> dict:
    """Soft delete a loan."""
    repo = LoanRepository()
    success = repo.delete(loan_id)
    if not success:
        raise NotFoundError(f"Loan {loan_id} not found")
    return {"success": True}


@router.get("/loans/{loan_id}/schedule")
def get_loan_schedule(loan_id: str) -> dict:
    """Get amortization schedule for a loan."""
    from src.engines.loan_engine import compute_amortization_schedule

    repo = LoanRepository()
    loan = repo.get_by_id(loan_id)
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found")

    if loan['loan_type'] == 'gold':
        return {"error": "Gold loans do not have fixed amortization schedules"}

    if not loan['tenure_months'] or not loan['disbursed_date']:
        return {"error": "Loan missing tenure or disbursed_date for schedule"}

    schedule = compute_amortization_schedule(
        principal_paise=loan['outstanding_paise'],
        annual_rate=loan['interest_rate'],
        tenure_months=loan['tenure_months'],
        disbursed_date=loan['disbursed_date'],
        emi_paise=loan['emi_paise'],
    )

    total_interest = sum(s['interest_paise'] for s in schedule)
    return {
        "loan_id": loan_id,
        "schedule": schedule,
        "total_payments": len(schedule),
        "total_interest_paise": total_interest,
        "total_payment_paise": sum(s['emi_paise'] for s in schedule),
    }


@router.post("/loans/{loan_id}/prepayment-simulation")
def simulate_prepayment(loan_id: str, request: PrepaymentRequest) -> dict:
    """Simulate impact of a prepayment."""
    from src.engines.loan_engine import compute_prepayment_impact, compute_remaining_months

    repo = LoanRepository()
    loan = repo.get_by_id(loan_id)
    if not loan:
        raise NotFoundError(f"Loan {loan_id} not found")

    remaining_months = compute_remaining_months(
        loan['outstanding_paise'],
        loan['interest_rate'],
        loan['emi_paise']
    ) if loan['emi_paise'] else loan['tenure_months'] or 0

    result = compute_prepayment_impact(
        outstanding_paise=loan['outstanding_paise'],
        annual_rate=loan['interest_rate'],
        remaining_months=remaining_months,
        prepayment_paise=request.prepayment_paise,
        mode=request.mode,
    )
    return result
