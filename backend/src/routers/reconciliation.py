"""Reconciliation matching and confirmation endpoints."""
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.common import format_inr
from src.models.explanation import ReconciliationResponse
from src.repositories import ReconciliationRepository
from src.services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/api/reconciliations", tags=["reconciliation"])


@router.get("")
def api_get_reconciliations(status: str | None = None) -> dict[str, Any]:
    """
    Get all reconciliations with transaction details.

    Phase 2B: Metadata-only, no ledger mutation.

    Args:
        status: Optional filter ('pending', 'confirmed', 'rejected')
    """
    try:
        repo = ReconciliationRepository()
        reconciliations = repo.get_reconciliations(status)

        # Enrich with display fields
        for r in reconciliations:
            # Amount is stored as paise, convert to rupees for display
            amount_paise = r.get("amount_paise", 0) or 0
            amount = amount_paise / 100.0 if amount_paise else 0
            r["amount_display"] = format_inr(amount)
            r["confidence_display"] = f"{r.get('match_confidence', 0) * 100:.0f}%"

        return {"reconciliations": reconciliations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
def api_get_pending_reconciliations() -> dict[str, Any]:
    """Get all pending reconciliations."""
    return api_get_reconciliations(status="pending")


@router.get("/scan", response_model=ReconciliationResponse)
def api_scan_reconciliations(household_id: str | None = None) -> ReconciliationResponse:
    """
    Scan for potential transfer matches across accounts.

    Phase 2B.1: Deterministic matching with confidence scoring.
    Phase 3: Uses repository for data fetching, pure engine.

    Args:
        household_id: Optional household filter. If None, scans all households.

    Returns ReconciliationResponse with matches and explanation.
    """
    try:
        service = ReconciliationService()
        return service.scan_with_explanation(household_id=household_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
def api_create_reconciliation(
    debit_txn_id: int = Query(..., description="Debit transaction ID"),
    credit_txn_id: int = Query(..., description="Credit transaction ID"),
    debit_account_id: str = Query(..., description="Debit account ID"),
    credit_account_id: str = Query(..., description="Credit account ID"),
    amount_paise: int = Query(..., description="Matched amount in paise (₹1.00 = 100)"),
    date_diff_days: int = Query(0, description="Days between transaction dates"),
    confidence_bps: int = Query(..., description="Confidence in basis points (0-10000)"),
    match_type: str = Query("exact", description="'exact', 'window', 'fuzzy', or 'manual'"),
) -> dict[str, Any]:
    """
    Create a reconciliation record between two transactions.

    Phase 2B: Metadata-only, no ledger mutation.
    Phase 3: Uses amount_paise and confidence_bps for precision.

    Breaking change: amount_paise (int) replaces amount (float).
    confidence_bps (int) replaces match_confidence (float).
    """
    try:
        repo = ReconciliationRepository()
        # Convert paise to rupees for backward-compatible repository call
        amount_rupees = amount_paise / 100.0
        match_confidence = confidence_bps / 10000.0

        inserted = repo.insert_reconciliation(
            debit_txn_id=debit_txn_id,
            credit_txn_id=credit_txn_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            amount=amount_rupees,
            date_diff_days=date_diff_days,
            match_confidence=match_confidence,
            match_type=match_type,
            confidence_bps=confidence_bps,
        )
        return {"success": True, "inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-insert")
def api_batch_insert_reconciliations(household_id: str | None = None) -> dict[str, Any]:
    """
    Scan and insert all potential matches as pending reconciliations.

    Uses INSERT OR IGNORE for idempotency - existing records are not duplicated.
    """
    try:
        service = ReconciliationService()
        matches = service.scan_potential_matches(household_id=household_id)

        repo = ReconciliationRepository()
        inserted_count = 0
        for m in matches:
            inserted = repo.insert_reconciliation(
                debit_txn_id=m["debit_txn_id"],
                credit_txn_id=m["credit_txn_id"],
                debit_account_id=m["debit_account_id"],
                credit_account_id=m["credit_account_id"],
                amount=m["amount"],
                date_diff_days=m["date_diff_days"],
                match_confidence=m["match_confidence"],
                match_type=m["match_type"],
                confidence_bps=m.get("confidence_bps"),
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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{reconciliation_id}/confirm")
def api_confirm_reconciliation(reconciliation_id: int) -> dict[str, Any]:
    """
    Confirm a pending reconciliation.

    Phase 2B: Updates reconciliation.status only. No ledger mutation.
    Phase 3: Logs audit action.
    """
    try:
        service = ReconciliationService()
        updated = service.confirm_reconciliation_with_audit(reconciliation_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Reconciliation not found or not pending")
        return {"success": True, "status": "confirmed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{reconciliation_id}/reject")
def api_reject_reconciliation(reconciliation_id: int) -> dict[str, Any]:
    """
    Reject a pending reconciliation.

    Phase 2B: Updates reconciliation.status only. No ledger mutation.
    Phase 3: Logs audit action.
    """
    try:
        service = ReconciliationService()
        updated = service.reject_reconciliation_with_audit(reconciliation_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Reconciliation not found or not pending")
        return {"success": True, "status": "rejected"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{reconciliation_id}/undo")
def api_undo_reconciliation(reconciliation_id: int) -> dict[str, Any]:
    """
    Revert a confirmed reconciliation back to pending status.

    Phase 3: Only allowed if confirmed in the current month.
    Logs an 'undo' audit action on success.
    """
    try:
        repo = ReconciliationRepository()
        updated = repo.undo_reconciliation(reconciliation_id)

        if not updated:
            # Check if it's a month boundary block
            raise HTTPException(
                status_code=400,
                detail="Undo not allowed - reconciliation confirmed in a different month or not found",
            )
        return {"success": True, "status": "pending", "action": "undo"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def api_get_reconciliation_stats(
    household_id: str | None = Query(None, description="Household identifier"),
) -> dict[str, Any]:
    """
    Get reconciliation statistics for health score calculation.

    Computes coverage ratio, accuracy score, and health score.

    Args:
        household_id: Optional household filter. If None, computes stats for all transactions.

    Returns:
        Dict with coverage_ratio, accuracy_score, health_score, total_transactions,
        matched_transactions, confirmed_count, rejected_count
    """
    try:
        service = ReconciliationService()
        stats = service.get_reconciliation_stats(household_id=household_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
