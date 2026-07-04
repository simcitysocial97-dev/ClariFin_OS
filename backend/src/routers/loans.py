"""
Loans Router
============
Endpoints for loan management and payment tracking.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Query, Response
from pydantic import BaseModel

from src.dependencies import (
    get_db,
    LoanCreate,
    LoanUpdate,
    LoanPaymentCreate,
)
from src.logger import log
from src.errors import NotFoundError
from src.engines.loan_engine import (
    compute_emi,
    generate_ideal_schedule,
    replay_payments,
    forecast_from_state,
    simulate_prepayment,
    compute_loan_summary,
)

router = APIRouter()


# ============================================================
# Request/Response Models
# ============================================================

class PrepaymentSimulationRequest(BaseModel):
    extra_payment_paise: int
    extra_payment_date: date
    strategy: str  # "REDUCE_TENURE" or "REDUCE_EMI"


# ============================================================
# Loan CRUD Endpoints
# ============================================================

@router.get("/api/loans")
def get_loans(status: Optional[str] = Query(None)):
    """Get all loans.
    
    Args:
        status: Optional filter by status (active, closed, defaulted)
    """
    db = get_db()
    loans = db.get_loans(status=status)
    return {"loans": loans, "total": len(loans)}


@router.get("/api/loans/{loan_id}")
def get_loan(loan_id: int):
    """Get a single loan by ID with payment history and computed fields."""
    db = get_db()
    
    loan = db.get_loan(loan_id)
    if not loan:
        raise NotFoundError("Loan", loan_id)
    
    # Get payment history
    payments = db.get_loan_payments(loan_id)
    
    # Compute computed fields
    total_paid_paise = sum(p.get("principal_component_paise", 0) for p in payments)
    total_interest_paid_paise = sum(p.get("interest_component_paise", 0) for p in payments)
    
    # Calculate remaining payments
    tenure_months = loan.get("tenure_months")
    remaining_payments = None
    if tenure_months:
        remaining_payments = tenure_months - len(payments)
        if remaining_payments < 0:
            remaining_payments = 0
    
    # Calculate next EMI date
    next_emi_date = None
    if loan.get("status") == "active" and tenure_months:
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        start_date_str = loan.get("start_date")
        if start_date_str:
            try:
                start_date = date.fromisoformat(start_date_str)
            except (ValueError, TypeError):
                from src.utils import parse_date_to_iso
                iso_date = parse_date_to_iso(start_date_str)
                start_date = date.fromisoformat(iso_date) if iso_date else None
            
            if start_date:
                # Calculate next EMI date based on payment count
                payment_count = len(payments)
                next_emi_date_obj = start_date + relativedelta(months=payment_count + 1)
                next_emi_date = next_emi_date_obj.isoformat()
    
    return {
        **loan,
        "payments": payments,
        "payment_count": len(payments),
        "total_paid_paise": total_paid_paise,
        "total_interest_paid_paise": total_interest_paid_paise,
        "remaining_payments": remaining_payments,
        "next_emi_date": next_emi_date,
    }


@router.post("/api/loans", status_code=201)
def create_loan(loan: LoanCreate):
    """Create a new loan."""
    db = get_db()
    
    loan_dict = {
        "name": loan.name,
        "lender": loan.lender,
        "loan_type": loan.loan_type,
        "principal_paise": loan.principal_paise,
        "outstanding_paise": loan.outstanding_paise,
        "interest_rate": loan.interest_rate,
        "emi_paise": loan.emi_paise,
        "tenure_months": loan.tenure_months,
        "start_date": loan.start_date,
        "end_date": loan.end_date,
        "linked_account_id": loan.linked_account_id,
        "status": loan.status,
        "notes": loan.notes,
    }
    
    loan_id = db.insert_loan(loan_dict)
    log.info("Loan created: %s (%s)", loan.name, loan.lender or "Unknown Lender")
    
    # Return the created loan
    created = db.get_loan(loan_id)
    return created


@router.put("/api/loans/{loan_id}")
def update_loan(loan_id: int, loan: LoanUpdate):
    """Update an existing loan."""
    db = get_db()
    
    # Check if loan exists
    existing = db.get_loan(loan_id)
    if not existing:
        raise NotFoundError("Loan", loan_id)
    
    # Build update dict
    update_dict = {}
    if loan.name is not None:
        update_dict["name"] = loan.name
    if loan.lender is not None:
        update_dict["lender"] = loan.lender
    if loan.loan_type is not None:
        update_dict["loan_type"] = loan.loan_type
    if loan.outstanding_paise is not None:
        update_dict["outstanding_paise"] = loan.outstanding_paise
    if loan.interest_rate is not None:
        update_dict["interest_rate"] = loan.interest_rate
    if loan.emi_paise is not None:
        update_dict["emi_paise"] = loan.emi_paise
    if loan.status is not None:
        update_dict["status"] = loan.status
    if loan.notes is not None:
        update_dict["notes"] = loan.notes
    
    if not update_dict:
        return existing
    
    updated = db.update_loan(loan_id, update_dict)
    if not updated:
        raise NotFoundError("Loan", loan_id)
    
    log.info("Loan updated: %s", loan_id)
    
    # Return the updated loan
    return db.get_loan(loan_id)


@router.delete("/api/loans/{loan_id}", status_code=204)
def delete_loan(loan_id: int):
    """Delete a loan and all its payments."""
    db = get_db()
    
    if not db.delete_loan_with_payments(loan_id):
        raise NotFoundError("Loan", loan_id)
    
    return Response(status_code=204)


@router.get("/api/loans/{loan_id}/payments")
def get_loan_payments(loan_id: int):
    """Get payment history for a loan."""
    db = get_db()
    
    # Check if loan exists
    loan = db.get_loan(loan_id)
    if not loan:
        raise NotFoundError("Loan", loan_id)
    
    payments = db.get_loan_payments(loan_id)
    return {"payments": payments, "total": len(payments)}


@router.post("/api/loans/{loan_id}/payments")
def create_loan_payment(loan_id: int, payment: LoanPaymentCreate):
    """Record a payment for a loan."""
    db = get_db()
    
    # Check if loan exists
    loan = db.get_loan(loan_id)
    if not loan:
        raise NotFoundError("Loan", loan_id)
    
    payment_dict = {
        "loan_id": loan_id,
        "transaction_id": payment.transaction_id,
        "principal_component_paise": payment.principal_component_paise,
        "interest_component_paise": payment.interest_component_paise,
        "payment_date": payment.payment_date,
        "remaining_principal_paise": payment.remaining_principal_paise,
    }
    
    payment_id = db.insert_loan_payment(payment_dict)
    log.info("Loan payment recorded: loan %s, payment %s", loan_id, payment_id)
    
    # Return the payment
    payments = db.get_loan_payments(loan_id)
    created = next((p for p in payments if p["id"] == payment_id), None)
    return created


# ============================================================
# Loan Engine Endpoints
# ============================================================

@router.get("/api/loans/{loan_id}/amortization")
def get_loan_amortization(loan_id: int):
    """
    Generate ideal amortization schedule for a loan.
    
    Uses daily reducing interest calculation.
    """
    db = get_db()
    
    # Check if loan exists
    loan = db.get_loan(loan_id)
    if not loan:
        raise NotFoundError("Loan", loan_id)
    
    # Parse start date
    start_date_str = loan.get("start_date")
    if not start_date_str:
        raise NotFoundError("Loan start date", loan_id)
    
    try:
        start_date = date.fromisoformat(start_date_str)
    except (ValueError, TypeError):
        # Try parsing DD/MM/YYYY format
        from src.utils import parse_date_to_iso
        iso_date = parse_date_to_iso(start_date_str)
        if iso_date:
            start_date = date.fromisoformat(iso_date)
        else:
            raise NotFoundError("Valid loan start date", loan_id)
    
    # Generate schedule
    schedule = generate_ideal_schedule(
        principal_paise=loan["principal_paise"],
        annual_rate_percent=loan["interest_rate"],
        tenure_months=loan.get("tenure_months", 0),
        start_date=start_date
    )
    
    # Calculate EMI
    emi = compute_emi(
        principal_paise=loan["principal_paise"],
        annual_rate_percent=loan["interest_rate"],
        tenure_months=loan.get("tenure_months", 0)
    )
    
    total_interest = sum(p["interest_paise"] for p in schedule)
    
    return {
        "loan_id": loan_id,
        "emi_paise": emi,
        "total_periods": len(schedule),
        "total_interest_paise": total_interest,
        "schedule": [
            {
                "period": p["period"],
                "emi_date": p["emi_date"].isoformat(),
                "emi_paise": p["emi_paise"],
                "interest_paise": p["interest_paise"],
                "principal_paise": p["principal_paise"],
                "remaining_principal_paise": p["remaining_principal_paise"]
            }
            for p in schedule
        ]
    }


@router.get("/api/loans/{loan_id}/summary")
def get_loan_summary_endpoint(loan_id: int, as_of: Optional[str] = Query(None)):
    """
    Get comprehensive loan summary with replay and forecast.
    
    Args:
        as_of: Optional date for summary in ISO format (YYYY-MM-DD)
    """
    db = get_db()
    
    # Check if loan exists
    loan = db.get_loan(loan_id)
    if not loan:
        raise NotFoundError("Loan", loan_id)
    
    # Parse start date
    start_date_str = loan.get("start_date")
    if not start_date_str:
        raise NotFoundError("Loan start date", loan_id)
    
    try:
        start_date = date.fromisoformat(start_date_str)
    except (ValueError, TypeError):
        from src.utils import parse_date_to_iso
        iso_date = parse_date_to_iso(start_date_str)
        if iso_date:
            start_date = date.fromisoformat(iso_date)
        else:
            raise NotFoundError("Valid loan start date", loan_id)
    
    # Parse as_of date
    as_of_date = None
    if as_of:
        try:
            as_of_date = date.fromisoformat(as_of)
        except (ValueError, TypeError):
            pass
    
    # Get payments and convert to engine format
    db_payments = db.get_loan_payments(loan_id)
    payments = []
    for p in db_payments:
        payment_date_str = p.get("payment_date")
        if payment_date_str:
            try:
                payment_date = date.fromisoformat(payment_date_str)
            except (ValueError, TypeError):
                from src.utils import parse_date_to_iso
                iso_date = parse_date_to_iso(payment_date_str)
                if iso_date:
                    payment_date = date.fromisoformat(iso_date)
                else:
                    continue
            
            # Determine payment type based on context
            # For now, assume all recorded payments are EMIs
            payments.append({
                "date": payment_date,
                "amount_paise": p.get("principal_component_paise", 0) + p.get("interest_component_paise", 0),
                "type": "EMI"
            })
    
    # Build loan details
    loan_details = {
        "principal_paise": loan["principal_paise"],
        "annual_rate_percent": loan["interest_rate"],
        "tenure_months": loan.get("tenure_months", 0),
        "start_date": start_date,
        "emi_paise": loan.get("emi_paise")
    }
    
    # Compute summary
    summary = compute_loan_summary(loan_details, payments, as_of_date)
    
    # Add loan metadata
    return {
        "loan_id": loan_id,
        "loan_name": loan.get("name"),
        "lender": loan.get("lender"),
        **summary
    }


@router.post("/api/loans/{loan_id}/simulate-prepayment")
def post_simulate_prepayment(loan_id: int, request: PrepaymentSimulationRequest):
    """
    Simulate the impact of making an extra prepayment.
    
    Strategies:
        - REDUCE_TENURE: Keep EMI same, reduce loan tenure
        - REDUCE_EMI: Reduce EMI, keep original tenure
    """
    db = get_db()
    
    # Check if loan exists
    loan = db.get_loan(loan_id)
    if not loan:
        raise NotFoundError("Loan", loan_id)
    
    # Validate strategy
    if request.strategy not in ("REDUCE_TENURE", "REDUCE_EMI"):
        return {
            "error": "Invalid strategy. Must be 'REDUCE_TENURE' or 'REDUCE_EMI'"
        }, 400
    
    # Parse start date
    start_date_str = loan.get("start_date")
    if not start_date_str:
        raise NotFoundError("Loan start date", loan_id)
    
    try:
        start_date = date.fromisoformat(start_date_str)
    except (ValueError, TypeError):
        from src.utils import parse_date_to_iso
        iso_date = parse_date_to_iso(start_date_str)
        if iso_date:
            start_date = date.fromisoformat(iso_date)
        else:
            raise NotFoundError("Valid loan start date", loan_id)
    
    # Get existing payments
    db_payments = db.get_loan_payments(loan_id)
    payments = []
    for p in db_payments:
        payment_date_str = p.get("payment_date")
        if payment_date_str:
            try:
                payment_date = date.fromisoformat(payment_date_str)
            except (ValueError, TypeError):
                from src.utils import parse_date_to_iso
                iso_date = parse_date_to_iso(payment_date_str)
                if iso_date:
                    payment_date = date.fromisoformat(iso_date)
                else:
                    continue
            
            payments.append({
                "date": payment_date,
                "amount_paise": p.get("principal_component_paise", 0) + p.get("interest_component_paise", 0),
                "type": "EMI"
            })
    
    # Build loan details
    loan_details = {
        "principal_paise": loan["principal_paise"],
        "annual_rate_percent": loan["interest_rate"],
        "tenure_months": loan.get("tenure_months", 0),
        "start_date": start_date,
        "emi_paise": loan.get("emi_paise")
    }
    
    # Run simulation
    result = simulate_prepayment(
        loan_details=loan_details,
        payments=payments,
        extra_payment_paise=request.extra_payment_paise,
        extra_payment_date=request.extra_payment_date,
        strategy=request.strategy
    )
    
    # Add loan context
    return {
        "loan_id": loan_id,
        "loan_name": loan.get("name"),
        "extra_payment_paise": request.extra_payment_paise,
        "extra_payment_date": request.extra_payment_date.isoformat(),
        "strategy": request.strategy,
        **result
    }
