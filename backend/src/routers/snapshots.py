"""
Monthly Snapshots Router
========================
Endpoints for managing monthly financial snapshots.
"""

from typing import Optional
from fastapi import APIRouter, Query

from src.dependencies import get_db, DB_PATH
from src.logger import log
from src.errors import NotFoundError

router = APIRouter()


@router.get("/api/snapshots")
def get_monthly_snapshots(limit: int = Query(24)):
    """Get monthly financial snapshots.
    
    Args:
        limit: Maximum number of snapshots to return (default: 24)
    """
    db = get_db()
    snapshots = db.get_monthly_snapshots(limit=limit)
    return {"snapshots": snapshots, "total": len(snapshots)}


@router.get("/api/snapshots/{month}")
def get_monthly_snapshot(month: str):
    """Get a single monthly snapshot by month.
    
    Args:
        month: Month in YYYY-MM format (e.g., "2025-06")
    """
    db = get_db()
    
    snapshot = db.get_monthly_snapshot(month)
    if not snapshot:
        raise NotFoundError("Monthly snapshot", month)
    
    return snapshot


@router.post("/api/snapshots/generate")
def generate_monthly_snapshot(month: Optional[str] = Query(None)):
    """Generate a monthly snapshot for the specified month.
    
    If no month is specified, generates for the current month.
    
    Args:
        month: Month in YYYY-MM format. If not provided, uses current month.
    """
    from src.engines.snapshot_engine import generate_monthly_snapshot as engine_generate
    
    snapshot = engine_generate(DB_PATH, month)
    log.info("Snapshot generated for %s", snapshot.get("month"))
    return snapshot


@router.post("/api/snapshots/backfill")
def generate_snapshots_backfill():
    """Generate snapshots for all months from earliest to latest transaction.
    
    Returns:
        Dict with count of snapshots generated.
    """
    from src.engines.snapshot_engine import generate_snapshots_backfill as engine_backfill
    
    count = engine_backfill(DB_PATH)
    log.info("Snapshot backfill complete: %d snapshots generated", count)
    return {"generated_count": count, "message": f"Generated {count} snapshots"}
