"""
Jobs Router
===========

API endpoints for job management.

Routes:
    POST /api/jobs       - Create a new job
    GET  /api/jobs/{id}  - Get job status/progress
"""

from typing import Optional, Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.dependencies import get_db
from src.engines.job_engine import create_job, get_job


router = APIRouter()


# ============================================================
# Pydantic Models
# ============================================================

class JobCreateRequest(BaseModel):
    job_type: str = Field(..., min_length=1, max_length=100, description="Type of job")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Job-specific data")
    total_items: int = Field(default=0, ge=0, description="Total items for progress tracking")


class JobCreateResponse(BaseModel):
    job_id: str


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    payload: Dict[str, Any]
    total_items: int
    processed_items: int
    progress_pct: float
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None
    worker_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str


# ============================================================
# Routes
# ============================================================

@router.post("/api/jobs", response_model=JobCreateResponse)
def create_new_job(request: JobCreateRequest):
    """
    Create a new job.
    
    Returns the job_id which can be used to track job status.
    """
    db = get_db()
    job_id = create_job(
        db=db,
        job_type=request.job_type,
        payload=request.payload,
        total_items=request.total_items,
    )
    return JobCreateResponse(job_id=job_id)


@router.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str):
    """
    Get job status and progress.
    
    Returns 404 if job not found.
    """
    db = get_db()
    job = get_job(db, job_id)
    
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(**job)
