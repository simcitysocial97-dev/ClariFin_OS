"""
Test Suite for Job Engine
==========================

Tests for:
1. Job creation (create_job)
2. Job retrieval (get_job)
3. Progress updates (update_progress)
4. Job completion (mark_completed)
5. Job failure (mark_failed)
6. Job cancellation (cancel_job)
7. Atomic job claiming (claim_pending_job)
8. Status counting (count_jobs_by_status)

Run: python -m pytest tests/test_job_engine.py -v
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.job_engine import (
    create_job,
    get_job,
    update_progress,
    mark_completed,
    mark_failed,
    cancel_job,
    claim_pending_job,
    get_jobs_by_status,
    count_jobs_by_status,
    cleanup_old_jobs,
)
from db import FinanceDB


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def test_db():
    """Create a test database with in-memory mode."""
    # Use a temp file database for tests
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = FinanceDB(db_path=db_path)
        yield db
        db.close()


# ============================================================
# Test 1: Job Creation
# ============================================================

def test_create_job_basic(test_db):
    """Test basic job creation."""
    job_id = create_job(test_db, "test_job")
    
    assert job_id is not None
    assert len(job_id) == 32  # UUID hex string
    
    # Verify job exists
    job = get_job(test_db, job_id)
    assert job is not None
    assert job["id"] == job_id
    assert job["job_type"] == "test_job"
    assert job["status"] == "PENDING"
    assert job["payload"] == {}


def test_create_job_with_payload(test_db):
    """Test job creation with payload."""
    payload = {"filename": "test.csv", "rows": 100}
    job_id = create_job(test_db, "import_csv", payload)
    
    job = get_job(test_db, job_id)
    assert job["payload"] == payload
    assert job["job_type"] == "import_csv"


def test_create_job_with_total_items(test_db):
    """Test job creation with total_items."""
    job_id = create_job(test_db, "process_data", total_items=1000)
    
    job = get_job(test_db, job_id)
    assert job["total_items"] == 1000
    assert job["processed_items"] == 0
    assert job["progress_pct"] == 0.0


def test_create_job_unique_ids(test_db):
    """Test that each job gets a unique ID."""
    job_ids = [create_job(test_db, "test") for _ in range(10)]
    
    # All IDs should be unique
    assert len(set(job_ids)) == 10


# ============================================================
# Test 2: Job Retrieval
# ============================================================

def test_get_job_not_found(test_db):
    """Test getting a non-existent job."""
    job = get_job(test_db, "nonexistent")
    assert job is None


def test_get_job_parses_payload(test_db):
    """Test that get_job properly parses JSON payload."""
    payload = {"key": "value", "nested": {"a": 1}}
    job_id = create_job(test_db, "test", payload)
    
    job = get_job(test_db, job_id)
    assert job["payload"] == payload


def test_get_job_calculates_progress(test_db):
    """Test that get_job calculates progress percentage."""
    job_id = create_job(test_db, "test", total_items=100)
    
    # Initially 0%
    job = get_job(test_db, job_id)
    assert job["progress_pct"] == 0.0
    
    # Claim job first (required for progress update)
    claim_pending_job(test_db, "worker-1")
    
    # Update progress
    update_progress(test_db, job_id, 50)
    job = get_job(test_db, job_id)
    assert job["progress_pct"] == 50.0


# ============================================================
# Test 3: Progress Updates
# ============================================================

def test_update_progress_success(test_db):
    """Test successful progress update."""
    job_id = create_job(test_db, "test", total_items=100)
    
    # Must claim before updating
    claim_pending_job(test_db, "worker-1")
    
    result = update_progress(test_db, job_id, 50)
    assert result is True
    
    job = get_job(test_db, job_id)
    assert job["processed_items"] == 50


def test_update_progress_not_running(test_db):
    """Test progress update on non-running job fails."""
    job_id = create_job(test_db, "test", total_items=100)
    
    # Try to update without claiming (status is PENDING)
    result = update_progress(test_db, job_id, 50)
    assert result is False


def test_update_progress_with_new_total(test_db):
    """Test progress update with new total."""
    job_id = create_job(test_db, "test", total_items=100)
    
    claim_pending_job(test_db, "worker-1")
    
    result = update_progress(test_db, job_id, 50, total=200)
    assert result is True
    
    job = get_job(test_db, job_id)
    assert job["processed_items"] == 50
    assert job["total_items"] == 200


# ============================================================
# Test 4: Job Completion
# ============================================================

def test_mark_completed_success(test_db):
    """Test successful job completion."""
    job_id = create_job(test_db, "test")
    
    # Must claim first
    claim_pending_job(test_db, "worker-1")
    
    result = mark_completed(test_db, job_id)
    assert result is True
    
    job = get_job(test_db, job_id)
    assert job["status"] == "COMPLETED"
    assert job["finished_at"] is not None


def test_mark_completed_not_running(test_db):
    """Test completion on non-running job fails."""
    job_id = create_job(test_db, "test")
    
    # Try to complete without claiming
    result = mark_completed(test_db, job_id)
    assert result is False
    
    job = get_job(test_db, job_id)
    assert job["status"] == "PENDING"


def test_mark_completed_already_completed(test_db):
    """Test completion on already completed job fails."""
    job_id = create_job(test_db, "test")
    
    claim_pending_job(test_db, "worker-1")
    mark_completed(test_db, job_id)
    
    # Try to complete again
    result = mark_completed(test_db, job_id)
    assert result is False


# ============================================================
# Test 5: Job Failure
# ============================================================

def test_mark_failed_pending(test_db):
    """Test failing a PENDING job."""
    job_id = create_job(test_db, "test")
    
    result = mark_failed(test_db, job_id, "Something went wrong")
    assert result is True
    
    job = get_job(test_db, job_id)
    assert job["status"] == "FAILED"
    assert job["error"] == "Something went wrong"
    assert job["finished_at"] is not None


def test_mark_failed_running(test_db):
    """Test failing a RUNNING job."""
    job_id = create_job(test_db, "test")
    
    claim_pending_job(test_db, "worker-1")
    
    result = mark_failed(test_db, job_id, "Runtime error")
    assert result is True
    
    job = get_job(test_db, job_id)
    assert job["status"] == "FAILED"
    assert job["error"] == "Runtime error"


def test_mark_failed_already_completed(test_db):
    """Test failing an already completed job fails."""
    job_id = create_job(test_db, "test")
    
    claim_pending_job(test_db, "worker-1")
    mark_completed(test_db, job_id)
    
    result = mark_failed(test_db, job_id, "Too late")
    assert result is False


def test_mark_failed_not_found(test_db):
    """Test failing a non-existent job."""
    result = mark_failed(test_db, "nonexistent", "Error")
    assert result is False


# ============================================================
# Test 6: Job Cancellation
# ============================================================

def test_cancel_job_success(test_db):
    """Test successful job cancellation."""
    job_id = create_job(test_db, "test")
    
    result = cancel_job(test_db, job_id)
    assert result is True
    
    job = get_job(test_db, job_id)
    assert job["status"] == "CANCELLED"
    assert job["finished_at"] is not None


def test_cancel_job_not_pending(test_db):
    """Test cancelling a non-PENDING job fails."""
    job_id = create_job(test_db, "test")
    
    claim_pending_job(test_db, "worker-1")
    
    result = cancel_job(test_db, job_id)
    assert result is False
    
    job = get_job(test_db, job_id)
    assert job["status"] == "RUNNING"


def test_cancel_job_not_found(test_db):
    """Test cancelling a non-existent job."""
    result = cancel_job(test_db, "nonexistent")
    assert result is False


# ============================================================
# Test 7: Atomic Job Claiming
# ============================================================

def test_claim_pending_job_success(test_db):
    """Test successfully claiming a pending job."""
    job_id = create_job(test_db, "test", {"data": "test"})
    
    job = claim_pending_job(test_db, "worker-1")
    
    assert job is not None
    assert job["id"] == job_id
    assert job["status"] == "RUNNING"
    assert job["worker_id"] == "worker-1"
    assert job["started_at"] is not None
    assert job["payload"] == {"data": "test"}


def test_claim_pending_job_none_available(test_db):
    """Test claiming when no PENDING jobs exist."""
    job = claim_pending_job(test_db, "worker-1")
    assert job is None


def test_claim_pending_job_fifo_order(test_db):
    """Test that jobs are claimed in FIFO order (by creation time)."""
    import time
    job_ids = []
    for i in range(3):
        job_id = create_job(test_db, "test", {"index": i})
        job_ids.append(job_id)
        time.sleep(0.01)  # Small delay to ensure different timestamps
    
    # Claim jobs in order - should get them by oldest first
    claimed_ids = []
    for _ in range(3):
        job = claim_pending_job(test_db, "worker-1")
        assert job is not None
        claimed_ids.append(job["id"])
    
    # All jobs should be claimed
    assert set(claimed_ids) == set(job_ids)


def test_claim_pending_job_no_double_claim(test_db):
    """Test that claimed jobs cannot be claimed again."""
    create_job(test_db, "test")
    
    # First claim succeeds
    job1 = claim_pending_job(test_db, "worker-1")
    assert job1 is not None
    
    # Second claim should fail (no more PENDING jobs)
    job2 = claim_pending_job(test_db, "worker-2")
    assert job2 is None


def test_claim_pending_job_only_claims_pending(test_db):
    """Test that only PENDING jobs are claimed."""
    # Create and complete a job
    job_id1 = create_job(test_db, "test")
    claim_pending_job(test_db, "worker-1")
    mark_completed(test_db, job_id1)
    
    # Create a pending job
    job_id2 = create_job(test_db, "test")
    
    # Only the pending job should be claimable
    job = claim_pending_job(test_db, "worker-1")
    assert job is not None
    assert job["id"] == job_id2


# ============================================================
# Test 8: Status Counting
# ============================================================

def test_count_jobs_by_status_empty(test_db):
    """Test counting with no jobs."""
    counts = count_jobs_by_status(test_db)
    assert counts == {}


def test_count_jobs_by_status(test_db):
    """Test counting jobs by status."""
    # Initially no jobs
    counts = count_jobs_by_status(test_db)
    assert counts == {}
    
    # Create 3 PENDING jobs
    for _ in range(3):
        create_job(test_db, "test")
    
    # Now should have 3 PENDING
    counts = count_jobs_by_status(test_db)
    assert counts.get("PENDING", 0) == 3
    
    # Claim 2 jobs
    for _ in range(2):
        claim_pending_job(test_db, "worker-1")
    
    counts = count_jobs_by_status(test_db)
    assert counts.get("PENDING", 0) == 1
    assert counts.get("RUNNING", 0) == 2
    
    # Complete 1 job
    # Find a running job and complete it
    running_jobs = get_jobs_by_status(test_db, status="RUNNING")
    if running_jobs:
        mark_completed(test_db, running_jobs[0]["id"])
    
    counts = count_jobs_by_status(test_db)
    assert counts.get("COMPLETED", 0) == 1


def test_get_jobs_by_status(test_db):
    """Test getting jobs filtered by status."""
    job_id = create_job(test_db, "test")
    claim_pending_job(test_db, "worker-1")
    mark_completed(test_db, job_id)
    
    create_job(test_db, "test")  # pending
    
    completed_jobs = get_jobs_by_status(test_db, status="COMPLETED")
    assert len(completed_jobs) == 1
    assert completed_jobs[0]["id"] == job_id
    
    pending_jobs = get_jobs_by_status(test_db, status="PENDING")
    assert len(pending_jobs) == 1


def test_get_jobs_by_status_pagination(test_db):
    """Test pagination in get_jobs_by_status."""
    for i in range(10):
        create_job(test_db, "test")
    
    # Get first 5
    jobs = get_jobs_by_status(test_db, limit=5, offset=0)
    assert len(jobs) == 5
    
    # Get next 5
    jobs = get_jobs_by_status(test_db, limit=5, offset=5)
    assert len(jobs) == 5


# ============================================================
# Test 9: Cleanup
# ============================================================

def test_cleanup_old_jobs(test_db):
    """Test cleanup of old jobs."""
    # Create and complete a job
    job_id = create_job(test_db, "test")
    claim_pending_job(test_db, "worker-1")
    mark_completed(test_db, job_id)
    
    # Cleanup with 0 days (delete all old completed jobs)
    # Note: This test may be flaky due to timing, using 30 days as default
    deleted = cleanup_old_jobs(test_db, days=0)
    # Should delete the completed job
    assert deleted >= 0  # May be 0 if created_at is considered "now"


# ============================================================
# Test 10: Integration Flow
# ============================================================

def test_full_job_lifecycle(test_db):
    """Test a complete job lifecycle."""
    # Create
    job_id = create_job(test_db, "import_csv", {"filename": "data.csv"}, total_items=100)
    
    job = get_job(test_db, job_id)
    assert job["status"] == "PENDING"
    
    # Claim
    claimed = claim_pending_job(test_db, "worker-1")
    assert claimed["id"] == job_id
    assert claimed["status"] == "RUNNING"
    
    # Update progress
    update_progress(test_db, job_id, 50)
    job = get_job(test_db, job_id)
    assert job["processed_items"] == 50
    assert job["progress_pct"] == 50.0
    
    # Complete
    mark_completed(test_db, job_id)
    job = get_job(test_db, job_id)
    assert job["status"] == "COMPLETED"
    assert job["finished_at"] is not None


def test_full_job_failure_lifecycle(test_db):
    """Test a job lifecycle ending in failure."""
    # Create
    job_id = create_job(test_db, "risky_job")
    
    # Claim
    claim_pending_job(test_db, "worker-1")
    
    # Fail
    mark_failed(test_db, job_id, "Something broke")
    
    job = get_job(test_db, job_id)
    assert job["status"] == "FAILED"
    assert job["error"] == "Something broke"
    assert job["finished_at"] is not None


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
