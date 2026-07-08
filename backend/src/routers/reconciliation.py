"""Reconciliation matching and confirmation endpoints."""
from fastapi import APIRouter, HTTPException, Query

from src.common import format_inr
from src.repositories import ReconciliationRepository

router = APIRouter(prefix="/api/reconciliations", tags=["reconciliation"])


@router.get("")
def api_get_reconciliations(status: str | None = None) -> dict:
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
            # Amount is already in rupees in new schema
            amount = r.get("amount", 0)
            r["amount_display"] = format_inr(amount)
            r["confidence_display"] = f"{r.get('match_confidence', 0) * 100:.0f}%"

        return {"reconciliations": reconciliations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
def api_get_pending_reconciliations() -> dict:
    """Get all pending reconciliations."""
    return api_get_reconciliations(status="pending")


@router.get("/scan")
def api_scan_reconciliations() -> dict:
    """
    Scan for potential transfer matches across accounts.

    Phase 2B.1: Deterministic matching with confidence scoring.

    Returns potential matches that can be saved as reconciliations.
    """
    try:
        repo = ReconciliationRepository()
        matches = repo.scan_potential_matches()

        # Enrich with display fields
        for m in matches:
            m["amount_display"] = format_inr(m.get("amount", 0))
            m["confidence_display"] = f"{m.get('match_confidence', 0) * 100:.0f}%"

        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
def api_create_reconciliation(
    debit_txn_id: int = Query(..., description="Debit transaction ID"),
    credit_txn_id: int = Query(..., description="Credit transaction ID"),
    debit_account_id: str = Query(..., description="Debit account ID"),
    credit_account_id: str = Query(..., description="Credit account ID"),
    amount: float = Query(..., description="Matched amount in rupees"),
    date_diff_days: int = Query(0, description="Days between transaction dates"),
    match_confidence: float = Query(..., description="Confidence score 0.0-1.0"),
    match_type: str = Query("exact", description="'exact', 'window', 'fuzzy', or 'manual'"),
) -> dict:
    """
    Create a reconciliation record between two transactions.

    Phase 2B: Metadata-only, no ledger mutation.
    Uses INSERT OR IGNORE for idempotency.
    """
    try:
        repo = ReconciliationRepository()
        inserted = repo.insert_reconciliation(
            debit_txn_id=debit_txn_id,
            credit_txn_id=credit_txn_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            amount=amount,
            date_diff_days=date_diff_days,
            match_confidence=match_confidence,
            match_type=match_type,
        )
        return {"success": True, "inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-insert")
def api_batch_insert_reconciliations() -> dict:
    """
    Scan and insert all potential matches as pending reconciliations.

    Uses INSERT OR IGNORE for idempotency - existing records are not duplicated.
    """
    try:
        repo = ReconciliationRepository()
        matches = repo.scan_potential_matches()

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
def api_confirm_reconciliation(reconciliation_id: int) -> dict:
    """
    Confirm a pending reconciliation.

    Phase 2B: Updates reconciliation.status only. No ledger mutation.
    """
    try:
        repo = ReconciliationRepository()
        updated = repo.confirm_reconciliation(reconciliation_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Reconciliation not found or not pending")
        return {"success": True, "status": "confirmed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{reconciliation_id}/reject")
def api_reject_reconciliation(reconciliation_id: int) -> dict:
    """
    Reject a pending reconciliation.

    Phase 2B: Updates reconciliation.status only. No ledger mutation.
    """
    try:
        repo = ReconciliationRepository()
        updated = repo.reject_reconciliation(reconciliation_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Reconciliation not found or not pending")
        return {"success": True, "status": "rejected"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))