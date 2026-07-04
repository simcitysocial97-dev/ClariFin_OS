"""
Job Worker - Background Job Processing
=======================================

Phase B1: Worker skeleton for durable job queue.

Key Principles:
1. Only starts if CLARIFIN_ENABLE_WORKER=1
2. Polls DB for PENDING jobs atomically
3. Single worker by default (no concurrency)
4. Stub implementation - marks jobs COMPLETED immediately

Usage:
    # In lifespan or main
    from src.workers.job_worker import start_worker, stop_worker
    
    start_worker()
    # ... app runs ...
    stop_worker()

Environment:
    CLARIFIN_ENABLE_WORKER=1  # Required to start worker
    CLARIFIN_WORKER_ID=worker-1  # Optional worker identifier
"""

import os
import threading
import time
from typing import Optional

from src.logger import log
from src.dependencies import get_db
from src.engines.job_engine import claim_pending_job, mark_completed


# ============================================================
# Configuration
# ============================================================

WORKER_ENABLED = os.environ.get("CLARIFIN_ENABLE_WORKER") == "1"
WORKER_ID = os.environ.get("CLARIFIN_WORKER_ID", "worker-1")
POLL_INTERVAL_SECONDS = 5  # Time between polls when no job found


# ============================================================
# Worker State
# ============================================================

_worker_thread: Optional[threading.Thread] = None
_worker_stop_event = threading.Event()


# ============================================================
# Worker Logic
# ============================================================

def _process_job_stub(job: dict) -> None:
    """
    Stub job processor - immediately marks job as COMPLETED.
    
    In production, this would:
    - Parse job_type and payload
    - Execute the actual work
    - Update progress periodically
    - Handle errors and retry logic
    """
    job_id = job["id"]
    job_type = job["job_type"]
    
    log.info("Processing job: %s (type=%s)", job_id, job_type)
    
    # TODO: Implement actual job processing based on job_type
    # For now, just mark as completed
    
    db = get_db()
    mark_completed(db, job_id)
    log.info("Job completed (stub): %s", job_id)


def _worker_loop() -> None:
    """
    Main worker loop.
    
    Continuously polls for PENDING jobs and processes them.
    Stops when _worker_stop_event is set.
    """
    log.info("Worker %s starting...", WORKER_ID)
    
    # Give the app a moment to fully start
    time.sleep(1)
    
    while not _worker_stop_event.is_set():
        try:
            db = get_db()
            
            # Atomically claim one PENDING job
            job = claim_pending_job(db, WORKER_ID)
            
            if job:
                # Process the claimed job
                _process_job_stub(job)
                # Continue immediately to check for more jobs
            else:
                # No jobs available, wait before polling again
                _worker_stop_event.wait(timeout=POLL_INTERVAL_SECONDS)
                
        except Exception as e:
            log.error("Worker error: %s", str(e), exc_info=True)
            # Wait a bit before retrying on error
            _worker_stop_event.wait(timeout=POLL_INTERVAL_SECONDS)
    
    log.info("Worker %s stopped.", WORKER_ID)


# ============================================================
# Public API
# ============================================================

def start_worker() -> bool:
    """
    Start the background worker thread.
    
    Only starts if CLARIFIN_ENABLE_WORKER=1 is set.
    Safe to call multiple times (no-op if already running).
    
    Returns:
        True if worker started (or already running), False if disabled
    """
    global _worker_thread
    
    if not WORKER_ENABLED:
        log.info("Worker not started (CLARIFIN_ENABLE_WORKER != 1)")
        return False
    
    if _worker_thread is not None and _worker_thread.is_alive():
        log.debug("Worker already running")
        return True
    
    _worker_stop_event.clear()
    _worker_thread = threading.Thread(target=_worker_loop, name="JobWorker", daemon=True)
    _worker_thread.start()
    
    log.info("Worker %s started (thread=%s)", WORKER_ID, _worker_thread.name)
    return True


def stop_worker(timeout: float = 5.0) -> bool:
    """
    Stop the background worker thread.
    
    Signals the worker to stop and waits for it to finish.
    Safe to call multiple times.
    
    Args:
        timeout: Maximum time to wait for worker to stop (seconds)
    
    Returns:
        True if worker stopped, False if timeout
    """
    global _worker_thread
    
    if _worker_thread is None or not _worker_thread.is_alive():
        return True
    
    log.info("Stopping worker %s...", WORKER_ID)
    _worker_stop_event.set()
    
    _worker_thread.join(timeout=timeout)
    
    if _worker_thread.is_alive():
        log.warning("Worker did not stop within timeout")
        return False
    
    log.info("Worker %s stopped.", WORKER_ID)
    return True


def is_worker_running() -> bool:
    """Check if worker thread is currently running."""
    return _worker_thread is not None and _worker_thread.is_alive()


# ============================================================
# Lifespan Integration Helper
# ============================================================

def setup_worker_in_lifespan():
    """
    Helper to integrate worker startup/shutdown into FastAPI lifespan.
    
    Usage in api.py lifespan:
        from src.workers.job_worker import setup_worker_in_lifespan
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            worker = setup_worker_in_lifespan()
            if worker:
                worker.start()
            yield
            if worker:
                worker.stop()
    
    Returns:
        WorkerManager with start/stop methods, or None if disabled
    """
    if not WORKER_ENABLED:
        return None
    
    class WorkerManager:
        def start(self):
            return start_worker()
        
        def stop(self):
            return stop_worker()
        
        def is_running(self):
            return is_worker_running()
    
    return WorkerManager()


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Temporarily enable worker for testing
    WORKER_ENABLED = True
    
    print("Starting worker test...")
    
    # Start worker
    started = start_worker()
    print(f"Worker started: {started}")
    
    # Let it run for a bit
    print("Worker running for 10 seconds...")
    time.sleep(10)
    
    # Stop worker
    stopped = stop_worker()
    print(f"Worker stopped: {stopped}")
    
    print("Test completed!")
