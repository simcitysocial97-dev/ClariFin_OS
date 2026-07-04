"""
Reconciliation Router
=====================
Endpoints for transaction reconciliation and matching.
"""

from typing import Optional, List
from fastapi import APIRouter, Query

from src.dependencies import get_db
from src.logger import log
from src.errors import NotFoundError

router = APIRouter()


@router.get("/api/reconciliations")
def api_get_reconciliations(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Get reconciliations with pagination."""
    db = get_db()
    result = db.get_reconciliations_paginated(status=status, page=page, per_page=per_page)
    return {
        "reconciliations": result.items,
        "pagination": {
            "page": result.page,
            "per_page": result.per_page,
            "total": result.total,
            "has_next": result.has_next,
        }
    }


@router.get("/api/reconciliations/pending")
def api_get_pending_reconciliations():
    """Get pending reconciliations."""
    db = get_db()
    reconciliations = db.get_pending_reconciliations()
    return {"reconciliations": reconciliations}


@router.get("/api/reconciliation/unmatched")
def api_get_unmatched_transactions():
    """Get unmatched transactions that need reconciliation."""
    db = get_db()
    from src.engines.reconciliation_engine import find_unmatched_transactions

    unmatched = find_unmatched_transactions(db)
    log.info("Unmatched transactions: %d found", len(unmatched))
    return {
        "unmatched_transactions": unmatched,
        "count": len(unmatched),
    }

@router.get("/api/reconciliations/scan")
def api_scan_reconciliations():
    """Scan for potential reconciliations."""
    db = get_db()
    from src.engines.reconciliation_engine import find_potential_matches

    matches = find_potential_matches(db)
    log.info("Reconciliation scan: %d potential matches found", len(matches))
    return {
        "potential_matches": matches,
        "count": len(matches),
    }


@router.post("/api/reconciliations/create")
def api_create_reconciliation(
    debit_txn_id: int,
    credit_txn_id: int,
    amount: float,
):
    """Create a new reconciliation."""
    db = get_db()
    
    # Get transaction details
    all_txns = db.get_all_transactions()
    debit_txn = next((t for t in all_txns if t["id"] == debit_txn_id), None)
    credit_txn = next((t for t in all_txns if t["id"] == credit_txn_id), None)
    
    if not debit_txn or not credit_txn:
        raise NotFoundError("Transaction", f"{debit_txn_id} or {credit_txn_id}")
    
    created = db.insert_reconciliation(
        debit_txn_id=debit_txn_id,
        credit_txn_id=credit_txn_id,
        debit_account_id=debit_txn.get("bank", ""),
        credit_account_id=credit_txn.get("bank", ""),
        amount=amount,
        date_diff_days=0,
        match_confidence=1.0,
        match_type="manual",
    )
    
    return {"created": created}


@router.post("/api/reconciliations/batch-insert")
def api_batch_insert_reconciliations(matches: List[dict]):
    """Batch insert reconciliations."""
    db = get_db()
    inserted = 0
    
    for match in matches:
        created = db.insert_reconciliation(
            debit_txn_id=match["debit_txn_id"],
            credit_txn_id=match["credit_txn_id"],
            debit_account_id=match.get("debit_account_id", ""),
            credit_account_id=match.get("credit_account_id", ""),
            amount=match["amount"],
            date_diff_days=match.get("date_diff_days", 0),
            match_confidence=match.get("match_confidence", 0.5),
            match_type=match.get("match_type", "auto"),
        )
        if created:
            inserted += 1
    
    log.info("Batch reconciliation: %d matches inserted", inserted)
    return {"inserted": inserted}


@router.post("/api/reconciliations/{reconciliation_id}/confirm")
def api_confirm_reconciliation(reconciliation_id: int):
    """Confirm a reconciliation."""
    db = get_db()
    confirmed = db.confirm_reconciliation(reconciliation_id)
    if not confirmed:
        raise NotFoundError("Reconciliation", reconciliation_id)
    log.info("Reconciliation %d confirmed", reconciliation_id)
    return {"success": True}


@router.post("/api/reconciliations/{reconciliation_id}/reject")
def api_reject_reconciliation(reconciliation_id: int):
    """Reject a reconciliation."""
    db = get_db()
    rejected = db.reject_reconciliation(reconciliation_id)
    if not rejected:
        raise NotFoundError("Reconciliation", reconciliation_id)
    log.info("Reconciliation %d rejected", reconciliation_id)
    return {"success": True}
