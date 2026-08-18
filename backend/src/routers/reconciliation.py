"""Reconciliation matching and confirmation endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.core.dtos.reconciliation_dto import (
    ReconciliationMatchDTO,
    ReconciliationsListResponse,
    ReconciliationScanResponse,
)
from src.core.mappers.reconciliation_mapper import ReconciliationMapper
from src.services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/api/reconciliation", tags=["reconciliation"])


def _build_match_dto(row: dict[str, Any]) -> ReconciliationMatchDTO:
    """Build a ReconciliationMatchDTO from a service row."""
    return ReconciliationMatchDTO(
        id=row.get("id", 0),
        debit_txn_id=row.get("debit_txn_id", 0),
        credit_txn_id=row.get("credit_txn_id", 0),
        debit_account_id=row.get("debit_account_id", ""),
        credit_account_id=row.get("credit_account_id", ""),
        amount_paise=row.get("amount_paise", 0),
        date_diff_days=row.get("date_diff_days", 0),
        match_confidence_bps=row.get("confidence_bps", 0),
        match_type=row.get("match_type", "exact"),
        status=row.get("status", "pending"),
        created_at=row.get("created_at", ""),
        confirmed_at=row.get("confirmed_at"),
        debit_date=row.get("debit_date", ""),
        debit_date_iso=row.get("debit_date_iso", ""),
        debit_description=row.get("debit_description", ""),
        debit_amount_paise=row.get("debit_amount_paise", 0),
        debit_bank=row.get("debit_bank", ""),
        credit_date=row.get("credit_date", ""),
        credit_date_iso=row.get("credit_date_iso", ""),
        credit_description=row.get("credit_description", ""),
        credit_amount_paise=row.get("credit_amount_paise", 0),
        credit_bank=row.get("credit_bank", ""),
    )


@router.get("", response_model=ReconciliationsListResponse)
def api_get_reconciliations(status: str | None = None) -> ReconciliationsListResponse:
    """
    Get all reconciliations with transaction details.

    Phase 2B: Metadata-only, no ledger mutation.

    Args:
        status: Optional filter ('pending', 'confirmed', 'rejected')
    """
    try:
        service = ReconciliationService()
        rows = service.get_reconciliations(status)
        matches = [_build_match_dto(r) for r in rows]
        return ReconciliationsListResponse(reconciliations=matches)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/pending", response_model=ReconciliationsListResponse)
def api_get_pending_reconciliations() -> ReconciliationsListResponse:
    """Get all pending reconciliations."""
    return api_get_reconciliations(status="pending")


@router.get("/scan", response_model=ReconciliationScanResponse)
def api_scan_reconciliations() -> ReconciliationScanResponse:
    """
    Scan for potential transfer matches across accounts.

    Phase 2B.1: Deterministic matching with confidence scoring.

    Returns potential matches that can be saved as reconciliations.
    """
    try:
        service = ReconciliationService()
        matches = service.scan_potential_matches()
        return ReconciliationScanResponse(matches=matches, count=len(matches))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/create")
def api_create_reconciliation(
    debit_txn_id: int = Query(..., description="Debit transaction ID"),
    credit_txn_id: int = Query(..., description="Credit transaction ID"),
    debit_account_id: str = Query(..., description="Debit account ID"),
    credit_account_id: str = Query(..., description="Credit account ID"),
    amount: float = Query(..., description="Matched amount in rupees"),
    date_diff_days: int = Query(0, description="Days between transaction dates"),
    match_confidence: float = Query(..., description="Confidence score 0.0-1.0"),
    match_type: str = Query(
        "exact", description="'exact', 'window', 'fuzzy', or 'manual'"
    ),
) -> dict[str, Any]:
    """
    Create a reconciliation record between two transactions.

    Phase 2B: Metadata-only, no ledger mutation.
    Uses INSERT OR IGNORE for idempotency.
    """
    try:
        service = ReconciliationService()
        inserted = service.insert_reconciliation(
            debit_txn_id=debit_txn_id,
            credit_txn_id=credit_txn_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            amount_paise=int(amount * 100),
            date_diff_days=date_diff_days,
            confidence_bps=int(
                match_confidence * 10000
                if match_confidence <= 1.0
                else match_confidence
            ),
            match_type=match_type,
        )
        return {"success": True, "inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/batch-insert")
def api_batch_insert_reconciliations() -> dict[str, Any]:
    """
    Scan and insert all potential matches as pending reconciliations.

    Uses INSERT OR IGNORE for idempotency - existing records are not duplicated.
    """
    try:
        service = ReconciliationService()
        matches = service.scan_potential_matches()

        inserted_count = 0
        for m in matches:
            amt_paise = m.get("amount_paise") or int(m.get("amount", 0) * 100)
            conf_bps = m.get("confidence_bps") or int(
                m.get("match_confidence", 0) * 10000
            )

            inserted = service.insert_reconciliation(
                debit_txn_id=m["debit_txn_id"],
                credit_txn_id=m["credit_txn_id"],
                debit_account_id=m["debit_account_id"],
                credit_account_id=m["credit_account_id"],
                amount_paise=amt_paise,
                date_diff_days=m["date_diff_days"],
                confidence_bps=conf_bps,
                match_type=m["match_type"],
            )
            if inserted:
                inserted_count += 1

        return {
            "success": True,
            "scanned": len(matches),
            "inserted": inserted_count,
            "skipped": len(matches) - inserted_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{reconciliation_id}/confirm")
def api_confirm_reconciliation(reconciliation_id: int) -> dict[str, Any]:
    """
    Confirm a pending reconciliation.

    Phase 2B: Updates reconciliation.status only. No ledger mutation.
    """
    try:
        service = ReconciliationService()
        updated = service.confirm_reconciliation(reconciliation_id)
        if not updated:
            raise HTTPException(
                status_code=404, detail="Reconciliation not found or not pending"
            )
        return {"success": True, "status": "confirmed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{reconciliation_id}/reject")
def api_reject_reconciliation(reconciliation_id: int) -> dict[str, Any]:
    """
    Reject a pending reconciliation.

    Phase 2B: Updates reconciliation.status only. No ledger mutation.
    """
    try:
        service = ReconciliationService()
        updated = service.reject_reconciliation(reconciliation_id)
        if not updated:
            raise HTTPException(
                status_code=404, detail="Reconciliation not found or not pending"
            )
        return {"success": True, "status": "rejected"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
