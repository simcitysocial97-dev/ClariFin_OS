"""Credit card management endpoints for the new engine.

All endpoints include request timing and structured error logging.
All monetary values in integer paise, all rates in integer basis points.

Follows the same pattern as loans.py - no FinanceDB import, no calculation logic.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter

from src.core.dtos.credit_cards_dto import (
    CreditCardSummaryDTO,
    EmiConversionDTO,
    ForeclosureDTO,
    StatementDTO,
)
from src.core.mappers.credit_card_mapper import CreditCardMapper
from src.errors import NotFoundError
from src.models.credit_card import (
    CreditCardCreateRequest,
    CreditCardUpdateRequest,
)
from src.models.credit_card_emi import EmiConversionRequest
from src.models.credit_card_foreclosure import ForeclosureRequest
from src.models.credit_card_statement import (
    PaymentRecordRequest,
    StatementGenerateRequest,
)
from src.services.credit_card_service import CreditCardService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["credit-cards"])


def _timed_log(
    endpoint: str,
    card_id: str | None,
    duration_ms: float,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Emit structured timing log for credit card endpoints."""
    log_data = {
        "type": "credit_card_request",
        "endpoint": endpoint,
        "card_id": card_id,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[CARD] %s | card_id=%s | %.0fms | FAIL: %s",
            endpoint,
            card_id,
            duration_ms,
            error,
        )
    else:
        logger.info("[CARD] %s | card_id=%s | %.0fms", endpoint, card_id, duration_ms)


# ============================================================
# Credit Card CRUD Endpoints
# ============================================================


@router.get("/credit-cards", response_model=list[CreditCardSummaryDTO])
def list_cards() -> list[CreditCardSummaryDTO]:
    """Get all active credit cards."""
    start = time.monotonic()
    service = CreditCardService()
    cards = service.list_cards()
    result = CreditCardMapper.to_list_dto(cards)
    _timed_log("GET /credit-cards", None, (time.monotonic() - start) * 1000)
    return result


@router.get("/credit-cards/{card_id}", response_model=CreditCardSummaryDTO)
def get_card(card_id: str) -> CreditCardSummaryDTO:
    """Get credit card details."""
    start = time.monotonic()
    service = CreditCardService()
    try:
        card = service.get_card(card_id)
        result = CreditCardMapper.to_dto(card)
        _timed_log("GET /credit-cards/{id}", card_id, (time.monotonic() - start) * 1000)
        return result
    except ValueError as e:
        _timed_log(
            "GET /credit-cards/{id}",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


@router.post("/credit-cards")
def create_card(request: CreditCardCreateRequest) -> dict[str, Any]:
    """Create a new credit card."""
    start = time.monotonic()
    service = CreditCardService()

    # Generate a card ID from bank and last4
    card_id = f"{request.bank}_{request.card_last4 or 'new'}"

    created_id = service.create_card(
        card_id=card_id,
        account_id=request.account_id,
        name=request.name,
        bank=request.bank,
        credit_limit_paise=request.credit_limit_paise,
        interest_rate_bps=request.interest_rate_bps,
        card_last4=request.card_last4,
        annual_fee_paise=request.annual_fee_paise,
        billing_day=request.billing_day,
        due_day_offset=request.due_day_offset,
        notes=request.notes,
    )
    _timed_log("POST /credit-cards", created_id, (time.monotonic() - start) * 1000)
    return {"success": True, "card_id": created_id}


@router.put("/credit-cards/{card_id}")
def update_card(card_id: str, request: CreditCardUpdateRequest) -> dict[str, Any]:
    """Update credit card fields."""
    start = time.monotonic()
    service = CreditCardService()

    update_data: dict[str, Any] = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.credit_limit_paise is not None:
        update_data["credit_limit_paise"] = request.credit_limit_paise
    if request.annual_fee_paise is not None:
        update_data["annual_fee_paise"] = request.annual_fee_paise
    if request.interest_rate_bps is not None:
        update_data["interest_rate_bps"] = request.interest_rate_bps
    if request.billing_day is not None:
        update_data["billing_day"] = request.billing_day
    if request.due_day_offset is not None:
        update_data["due_day_offset"] = request.due_day_offset
    if request.notes is not None:
        update_data["notes"] = request.notes

    updated = service.update_card(card_id, **update_data)
    if not updated:
        _timed_log(
            "PUT /credit-cards/{id}",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error="Not found",
        )
        raise NotFoundError(f"Credit card {card_id} not found")
    _timed_log("PUT /credit-cards/{id}", card_id, (time.monotonic() - start) * 1000)
    return {"success": True}


@router.delete("/credit-cards/{card_id}")
def deactivate_card(card_id: str) -> dict[str, Any]:
    """Soft delete a credit card."""
    start = time.monotonic()
    service = CreditCardService()
    success = service.deactivate_card(card_id)
    if not success:
        _timed_log(
            "DELETE /credit-cards/{id}",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error="Not found",
        )
        raise NotFoundError(f"Credit card {card_id} not found")
    _timed_log("DELETE /credit-cards/{id}", card_id, (time.monotonic() - start) * 1000)
    return {"success": True}


# ============================================================
# Statement Endpoints
# ============================================================


@router.get("/credit-cards/{card_id}/statements", response_model=list[StatementDTO])
def list_statements(card_id: str, limit: int = 12) -> list[StatementDTO]:
    """Get statement history for a card."""
    start = time.monotonic()
    service = CreditCardService()
    statements = service.list_statements(card_id, limit)
    result = CreditCardMapper.to_statement_list_dto(statements)
    _timed_log(
        "GET /credit-cards/{id}/statements", card_id, (time.monotonic() - start) * 1000
    )
    return result


@router.post("/credit-cards/{card_id}/statements", response_model=StatementDTO)
def generate_statement(card_id: str, request: StatementGenerateRequest) -> StatementDTO:
    """Generate a new statement for a credit card."""
    start = time.monotonic()
    service = CreditCardService()
    try:
        statement = service.generate_statement(card_id, request.statement_date)
        result = CreditCardMapper.to_statement_dto(statement)
        _timed_log(
            "POST /credit-cards/{id}/statements",
            card_id,
            (time.monotonic() - start) * 1000,
        )
        return result
    except ValueError as e:
        _timed_log(
            "POST /credit-cards/{id}/statements",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


# ============================================================
# Financial Metric Endpoints
# ============================================================


@router.get("/credit-cards/{card_id}/outstanding")
def get_outstanding(card_id: str) -> dict[str, int]:
    """Get current outstanding balance."""
    start = time.monotonic()
    service = CreditCardService()
    try:
        outstanding = service.calculate_outstanding(card_id)
        _timed_log(
            "GET /credit-cards/{id}/outstanding",
            card_id,
            (time.monotonic() - start) * 1000,
        )
        return {"outstanding_paise": outstanding}
    except ValueError as e:
        _timed_log(
            "GET /credit-cards/{id}/outstanding",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


@router.get("/credit-cards/{card_id}/utilization")
def get_utilization(card_id: str) -> dict[str, int]:
    """Get credit utilization and available credit."""
    start = time.monotonic()
    service = CreditCardService()
    try:
        result = service.calculate_utilization(card_id)
        _timed_log(
            "GET /credit-cards/{id}/utilization",
            card_id,
            (time.monotonic() - start) * 1000,
        )
        return result
    except ValueError as e:
        _timed_log(
            "GET /credit-cards/{id}/utilization",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


@router.get("/credit-cards/{card_id}/metrics")
def get_metrics(card_id: str) -> dict[str, int]:
    """Get core financial metrics for a credit card."""
    start = time.monotonic()
    service = CreditCardService()
    try:
        result = service.get_financial_metrics(card_id)
        _timed_log(
            "GET /credit-cards/{id}/metrics", card_id, (time.monotonic() - start) * 1000
        )
        return result
    except ValueError as e:
        _timed_log(
            "GET /credit-cards/{id}/metrics",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


@router.get("/credit-cards/{card_id}/next-statement-date")
def get_next_statement_date(card_id: str) -> dict[str, str]:
    """Get the next expected statement date."""
    start = time.monotonic()
    service = CreditCardService()
    try:
        next_date = service.get_next_statement_date(card_id)
        _timed_log(
            "GET /credit-cards/{id}/next-statement-date",
            card_id,
            (time.monotonic() - start) * 1000,
        )
        return {"next_statement_date": next_date}
    except ValueError as e:
        _timed_log(
            "GET /credit-cards/{id}/next-statement-date",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


# ============================================================
# Payment Endpoints
# ============================================================


@router.post("/credit-cards/{card_id}/payments", response_model=StatementDTO)
def record_payment(card_id: str, request: PaymentRecordRequest) -> StatementDTO:
    """Record a payment on the latest open statement."""
    start = time.monotonic()
    service = CreditCardService()
    try:
        statement = service.record_payment(
            card_id=card_id,
            amount_paise=request.amount_paise,
            payment_date=request.payment_date,
        )
        result = CreditCardMapper.to_statement_dto(statement)
        _timed_log(
            "POST /credit-cards/{id}/payments",
            card_id,
            (time.monotonic() - start) * 1000,
        )
        return result
    except ValueError as e:
        _timed_log(
            "POST /credit-cards/{id}/payments",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


# ============================================================
# EMI Conversion Endpoints
# ============================================================


@router.post("/credit-cards/{card_id}/emi-conversion", response_model=EmiConversionDTO)
def convert_to_emi(
    card_id: str,
    request: EmiConversionRequest,
) -> EmiConversionDTO:
    """Convert a purchase to EMI.

    Delegates via credit_card_engine -> loan_engine.
    No EMI formula duplication.
    """
    start = time.monotonic()
    service = CreditCardService()
    try:
        result = service.convert_to_emi(
            card_id=card_id,
            amount_paise=request.amount_paise,
            tenure_months=request.tenure_months,
            annual_rate_bps=request.annual_rate_bps,
        )
        response = EmiConversionDTO(
            emi_paise=result.emi_paise,
            total_interest_paise=result.total_interest_paise,
            total_repayment_paise=result.total_repayment_paise,
            monthly_interest_paise=result.monthly_interest_paise,
        )
        _timed_log(
            "POST /credit-cards/{id}/emi-conversion",
            card_id,
            (time.monotonic() - start) * 1000,
        )
        return response
    except ValueError as e:
        _timed_log(
            "POST /credit-cards/{id}/emi-conversion",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


# ============================================================
# Foreclosure Endpoints
# ============================================================


@router.post("/credit-cards/{card_id}/foreclosure", response_model=ForeclosureDTO)
def quote_foreclosure(
    card_id: str,
    request: ForeclosureRequest,
) -> ForeclosureDTO:
    """Quote foreclosure payoff for a credit card EMI.

    Delegates via credit_card_engine -> loan_engine.
    """
    start = time.monotonic()
    service = CreditCardService()
    try:
        result = service.quote_foreclosure(
            card_id=card_id,
            remaining_months=request.remaining_months,
            penalty_bps=request.penalty_bps,
        )
        response = ForeclosureDTO(
            foreclosure_amount_paise=result.foreclosure_amount_paise,
            outstanding_paise=result.outstanding_paise,
            accrued_interest_paise=result.accrued_interest_paise,
            penalty_paise=result.penalty_paise,
        )
        _timed_log(
            "POST /credit-cards/{id}/foreclosure",
            card_id,
            (time.monotonic() - start) * 1000,
        )
        return response
    except ValueError as e:
        _timed_log(
            "POST /credit-cards/{id}/foreclosure",
            card_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e
