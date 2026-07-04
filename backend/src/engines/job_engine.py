"""
Job Engine - Durable DB-Backed Job Queue
=========================================

Phase B1: Durable job queue with SQLite persistence.

Key Principles:
1. All job state stored in SQLite (durable)
2. Atomic claim using UPDATE...WHERE (no race conditions)
3. Deterministic timestamps via ISO format
4. Pure functions with explicit db parameter (testable)

Usage:
    from engines.job_engine import create_job, get_job, claim_pending_job
    from dependencies import get_db
    
    db = get_db()
    job_id = create_job(db, "import_csv", {"filename": "data.csv"})
    job = get_job(db, job_id)
    claimed = claim_pending_job(db, worker_id="worker-1")
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.logger import log


# ============================================================
# Constants
# ============================================================

VALID_STATUSES = {"PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"}


# ============================================================
# Timestamp Utilities
# ============================================================

def _now_iso() -> str:
    """Get current timestamp in ISO format (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


# ============================================================
# Job Lifecycle Functions
# ============================================================

def create_job(
    db,
    job_type: str,
    payload: Optional[Dict[str, Any]] = None,
    total_items: int = 0,
) -> str:
    """
    Create a new job in PENDING status.
    
    Args:
        db: FinanceDB instance
        job_type: Type of job (e.g., 'import_csv', 'reconcile', 'generate_report')
        payload: Job-specific data (will be JSON serialized)
        total_items: Total items to process (for progress tracking)
    
    Returns:
        job_id: UUID string for the new job
    
    Example:
        >>> job_id = create_job(db, "import_csv", {"filename": "data.csv"}, total_items=100)
    """
    job_id = uuid.uuid4().hex
    payload_json = json.dumps(payload or {})
    created_at = _now_iso()
    
    with db.transaction() as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, job_type, status, payload_json, total_items, created_at)
            VALUES (?, ?, 'PENDING', ?, ?, ?)
            """,
            (job_id, job_type, payload_json, total_items, created_at),
        )
    
    log.info("Job created: %s (type=%s)", job_id, job_type)
    return job_id


def get_job(db, job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get job by ID.
    
    Args:
        db: FinanceDB instance
        job_id: UUID string
    
    Returns:
        Job dict with parsed payload, or None if not found
    
    Example:
        >>> job = get_job(db, "abc123...")
        >>> print(job["status"], job["progress"])
    """
    with db.connection() as conn:
        cur = conn.execute(
            """
            SELECT id, job_type, status, payload_json, total_items, processed_items,
                   created_at, started_at, finished_at, error, worker_id
            FROM jobs WHERE id = ?
            """,
            (job_id,),
        )
        row = cur.fetchone()
        
        if row is None:
            return None
        
        job = dict(row)
        # Parse JSON payload
        try:
            job["payload"] = json.loads(job.pop("payload_json", "{}"))
        except json.JSONDecodeError:
            job["payload"] = {}
        
        # Calculate progress percentage
        total = job.get("total_items", 0)
        processed = job.get("processed_items", 0)
        job["progress_pct"] = round((processed / total * 100), 2) if total > 0 else 0
        
        return job


def update_progress(db, job_id: str, processed: int, total: Optional[int] = None) -> bool:
    """
    Update job progress.
    
    Args:
        db: FinanceDB instance
        job_id: UUID string
        processed: Number of items processed so far
        total: Optional new total (if changed)
    
    Returns:
        True if updated, False if job not found or not in RUNNING status
    
    Example:
        >>> update_progress(db, "abc123...", processed=50, total=100)
    """
    with db.transaction() as conn:
        if total is not None:
            cur = conn.execute(
                """
                UPDATE jobs 
                SET processed_items = ?, total_items = ?
                WHERE id = ? AND status = 'RUNNING'
                """,
                (processed, total, job_id),
            )
        else:
            cur = conn.execute(
                """
                UPDATE jobs 
                SET processed_items = ?
                WHERE id = ? AND status = 'RUNNING'
                """,
                (processed, job_id),
            )
        
        updated = cur.rowcount > 0
        if updated:
            log.debug("Job progress: %s = %d/%d", job_id, processed, total or 0)
        return updated


def mark_completed(db, job_id: str) -> bool:
    """
    Mark job as COMPLETED.
    
    Args:
        db: FinanceDB instance
        job_id: UUID string
    
    Returns:
        True if updated, False if job not found or not in RUNNING status
    """
    finished_at = _now_iso()
    
    with db.transaction() as conn:
        cur = conn.execute(
            """
            UPDATE jobs 
            SET status = 'COMPLETED', finished_at = ?, error = NULL
            WHERE id = ? AND status = 'RUNNING'
            """,
            (finished_at, job_id),
        )
    
    updated = cur.rowcount > 0
    if updated:
        log.info("Job completed: %s", job_id)
    return updated


def mark_failed(db, job_id: str, error: str) -> bool:
    """
    Mark job as FAILED with error message.
    
    Args:
        db: FinanceDB instance
        job_id: UUID string
        error: Error message
    
    Returns:
        True if updated, False if job not found
    """
    finished_at = _now_iso()
    
    with db.transaction() as conn:
        cur = conn.execute(
            """
            UPDATE jobs 
            SET status = 'FAILED', finished_at = ?, error = ?
            WHERE id = ? AND status IN ('PENDING', 'RUNNING')
            """,
            (finished_at, error, job_id),
        )
    
    updated = cur.rowcount > 0
    if updated:
        log.error("Job failed: %s - %s", job_id, error)
    return updated


def cancel_job(db, job_id: str) -> bool:
    """
    Cancel a PENDING job.
    
    Args:
        db: FinanceDB instance
        job_id: UUID string
    
    Returns:
        True if cancelled, False if job not found or not PENDING
    """
    finished_at = _now_iso()
    
    with db.transaction() as conn:
        cur = conn.execute(
            """
            UPDATE jobs 
            SET status = 'CANCELLED', finished_at = ?
            WHERE id = ? AND status = 'PENDING'
            """,
            (finished_at, job_id),
        )
    
    updated = cur.rowcount > 0
    if updated:
        log.info("Job cancelled: %s", job_id)
    return updated


# ============================================================
# Worker Functions
# ============================================================

def claim_pending_job(db, worker_id: str) -> Optional[Dict[str, Any]]:
    """
    Atomically claim one PENDING job for processing.
    
    Uses UPDATE with RETURNING for atomic claim (no race conditions).
    Only claims jobs in PENDING status.
    
    Args:
        db: FinanceDB instance
        worker_id: Identifier for the worker claiming the job
    
    Returns:
        Job dict if claimed, None if no PENDING jobs available
    
    Example:
        >>> job = claim_pending_job(db, "worker-1")
        >>> if job:
        ...     process_job(job)
        ...     mark_completed(db, job["id"])
    """
    started_at = _now_iso()
    
    with db.transaction() as conn:
        # Atomic claim using CTE with UPDATE...RETURNING
        # This ensures we get the exact row we updated
        cur = conn.execute(
            """
            WITH next_job AS (
                SELECT id FROM jobs 
                WHERE status = 'PENDING' 
                ORDER BY created_at ASC, id ASC
                LIMIT 1
            )
            UPDATE jobs 
            SET status = 'RUNNING', worker_id = ?, started_at = ?
            WHERE id = (SELECT id FROM next_job)
            AND status = 'PENDING'
            RETURNING id, job_type, status, payload_json, total_items, processed_items,
                      created_at, started_at, finished_at, error, worker_id
            """,
            (worker_id, started_at),
        )
        
        row = cur.fetchone()
        
        if row is None:
            return None
        
        job = dict(row)
        # Parse JSON payload
        try:
            job["payload"] = json.loads(job.pop("payload_json", "{}"))
        except json.JSONDecodeError:
            job["payload"] = {}
        
        log.info("Job claimed: %s by %s", job["id"], worker_id)
        return job


def get_jobs_by_status(
    db,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Dict[str, Any]]:
    """
    Get jobs filtered by status.
    
    Args:
        db: FinanceDB instance
        status: Filter by status (None = all statuses)
        limit: Maximum number of jobs to return
        offset: Offset for pagination
    
    Returns:
        List of job dicts with parsed payloads
    """
    with db.connection() as conn:
        if status:
            cur = conn.execute(
                """
                SELECT id, job_type, status, payload_json, total_items, processed_items,
                       created_at, started_at, finished_at, error, worker_id
                FROM jobs 
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (status, limit, offset),
            )
        else:
            cur = conn.execute(
                """
                SELECT id, job_type, status, payload_json, total_items, processed_items,
                       created_at, started_at, finished_at, error, worker_id
                FROM jobs 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        
        rows = cur.fetchall()
        jobs = []
        for row in rows:
            job = dict(row)
            try:
                job["payload"] = json.loads(job.pop("payload_json", "{}"))
            except json.JSONDecodeError:
                job["payload"] = {}
            
            # Calculate progress
            total = job.get("total_items", 0)
            processed = job.get("processed_items", 0)
            job["progress_pct"] = round((processed / total * 100), 2) if total > 0 else 0
            
            jobs.append(job)
        
        return jobs


def count_jobs_by_status(db) -> Dict[str, int]:
    """
    Get count of jobs grouped by status.
    
    Args:
        db: FinanceDB instance
    
    Returns:
        Dict mapping status to count
    """
    with db.connection() as conn:
        cur = conn.execute(
            """
            SELECT status, COUNT(*) as count
            FROM jobs
            GROUP BY status
            """
        )
        return {row["status"]: row["count"] for row in cur.fetchall()}


# ============================================================
# Cleanup Functions
# ============================================================

def cleanup_old_jobs(db, days: int = 30) -> int:
    """
    Delete completed/failed/cancelled jobs older than specified days.
    
    Args:
        db: FinanceDB instance
        days: Age in days for deletion
    
    Returns:
        Number of jobs deleted
    """
    with db.transaction() as conn:
        cur = conn.execute(
            """
            DELETE FROM jobs
            WHERE status IN ('COMPLETED', 'FAILED', 'CANCELLED')
            AND datetime(created_at) < datetime('now', ?)
            """,
            (f"-{days} days",),
        )
        deleted = cur.rowcount
        if deleted > 0:
            log.info("Cleaned up %d old jobs", deleted)
        return deleted


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from src.db import FinanceDB
    
    # Quick test
    db = FinanceDB()
    
    print("Creating test job...")
    job_id = create_job(db, "test_job", {"test": "data"}, total_items=10)
    print(f"Created: {job_id}")
    
    print("\nGetting job...")
    job = get_job(db, job_id)
    print(f"Job: {job}")
    
    print("\nClaiming job...")
    claimed = claim_pending_job(db, "test-worker")
    print(f"Claimed: {claimed}")
    
    print("\nUpdating progress...")
    update_progress(db, job_id, 5)
    job = get_job(db, job_id)
    print(f"Progress: {job['processed_items']}/{job['total_items']}")
    
    print("\nMarking completed...")
    mark_completed(db, job_id)
    job = get_job(db, job_id)
    print(f"Status: {job['status']}")
    
    print("\nCounts by status:")
    counts = count_jobs_by_status(db)
    print(counts)
    
    db.close()
    print("\nTest completed!")
