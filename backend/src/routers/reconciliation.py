"""Reconciliation matching and confirmation endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.core.dtos.reconciliation_dto import ReconciliationDTO
from src.core.mappers.reconciliation_mapper import ReconciliationMapper
from src.services.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/api/reconciliations", tags=["reconciliation"])


@router.get("", response_model=ReconciliationDTO)
def api_get_reconciliations(status: str | None = None) -> ReconciliationDTO:
    """
    Get all reconciliations with transaction details.

    Phase 2B: Metadata-only, no ledger mutation.

    Args:
        status: Optional filter ('pending', 'confirmed', 'rejected')
    """
    try:
        service = ReconciliationService()
        reconciliations = service.get_reconciliations(status)

        result = ReconciliationMapper.to_dto(
            {
                "statements": [],
                "discrepancies": reconciliations,
                "status_overview": {
                    "total_transactions": len(reconciliations),
                    "reconciled": len(
                        [r for r in reconciliations if r.get("status") == "confirmed"]
                    ),
                    "pending": len(
                        [r for r in reconciliations if r.get("status") == "pending"]
                    ),
                    "discrepancies": len(
                        [r for r in reconciliations if r.get("status") == "disputed"]
                    ),
                    "match_rate": 95.0 if reconciliations else 0.0,
                },
                "audit_trail": [],
                "insights": [],
                "evidence_chain": None,
            }
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/pending")
def api_get_pending_reconciliations() -> ReconciliationDTO:
    """Get all pending reconciliations."""
    return api_get_reconciliations(status="pending")


@router.get("/scan", response_model=ReconciliationDTO)
def api_scan_reconciliations() -> ReconciliationDTO:
    """
    Scan for potential transfer matches across accounts.

    Phase 2B.1: Deterministic matching with confidence scoring.

    Returns potential matches that can be saved as reconciliations.
    """
    try:
        service = ReconciliationService()
        matches = service.scan_potential_matches()

        # Transform match data to discrepancy format
        discrepancies = []
        for m in matches:
            discrepancies.append(
                {
                    "id": 0,  # Not yet inserted
                    "transaction_id": m.get("debit_txn_id", 0),
                    "statement_id": 0,
                    "type": "transfer_match",
                    "expected_paise": int(m.get("amount", 0) * 100),
                    "actual_paise": int(m.get("amount", 0) * 100),
                    "difference_paise": 0,
                    "status": "pending",
                    "notes": f"Date diff: {m.get('date_diff_days', 0)} days, Confidence: {m.get('match_confidence', 0):.0%}",
                }
            )

        result = ReconciliationMapper.to_dto(
            {
                "statements": [],
                "discrepancies": discrepancies,
                "status_overview": {
                    "total_transactions": len(matches),
                    "reconciled": 0,
                    "pending": len(matches),
                    "discrepancies": len(matches),
                    "match_rate": 0.0,
                },
                "audit_trail": [],
                "insights": [],
                "evidence_chain": None,
            }
        )
        return result
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
