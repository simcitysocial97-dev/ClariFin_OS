"""
Quarantine Router
=================
Endpoints for managing quarantined pages from failed statement validations.

- GET /api/quarantine/pages - List quarantined pages
- GET /api/quarantine/pages/{id} - Get quarantine page details
- PATCH /api/quarantine/pages/{id} - Resolve quarantine page with corrections
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.dependencies import get_db

router = APIRouter()


class QuarantinePageResponse(BaseModel):
    """Response model for a quarantine page."""
    id: str
    statement_id: str
    page_number: int
    reason: Optional[str]
    delta_paise: Optional[int]
    status: str
    created_at: str
    resolved_at: Optional[str]
    resolution_notes: Optional[str]
    source_filename: Optional[str]
    bank: Optional[str]


class QuarantinePageDetailResponse(QuarantinePageResponse):
    """Detailed response including extraction JSON."""
    raw_extraction_json: Optional[str]
    corrected_extraction_json: Optional[str]


class QuarantinePageListResponse(BaseModel):
    """Paginated list response."""
    items: list[QuarantinePageResponse]
    total: int
    page: int
    per_page: int
    has_next: bool


class ResolveQuarantineRequest(BaseModel):
    """Request body for resolving a quarantine page."""
    corrected_extraction_json: str
    resolution_notes: Optional[str] = None


class ResolveQuarantineResponse(BaseModel):
    """Response for resolving a quarantine page."""
    success: bool
    id: str
    status: str
    message: str


@router.get("/api/quarantine/pages")
def list_quarantine_pages(
    status: Optional[str] = "QUARANTINED",
    page: int = 1,
    per_page: int = 50,
) -> QuarantinePageListResponse:
    """
    List quarantine pages with optional status filter.
    
    Args:
        status: Filter by status ('QUARANTINED', 'RESOLVED', omit for all)
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        Paginated list of quarantine pages
    """
    db = get_db()
    
    # Validate status filter
    if status and status not in ('QUARANTINED', 'RESOLVED'):
        raise HTTPException(
            status_code=400,
            detail="Status must be 'QUARANTINED' or 'RESOLVED'"
        )
    
    # Use None for status to get all pages
    status_filter = status if status else None
    
    result = db.list_quarantine_pages(
        status=status_filter,
        page=page,
        per_page=per_page
    )
    
    # Convert items to response model
    items = [
        QuarantinePageResponse(
            id=item['id'],
            statement_id=item['statement_id'],
            page_number=item['page_number'],
            reason=item.get('reason'),
            delta_paise=item.get('delta_paise'),
            status=item['status'],
            created_at=item['created_at'],
            resolved_at=item.get('resolved_at'),
            resolution_notes=item.get('resolution_notes'),
            source_filename=item.get('source_filename'),
            bank=item.get('bank')
        )
        for item in result.items
    ]
    
    return QuarantinePageListResponse(
        items=items,
        total=result.total,
        page=result.page,
        per_page=result.per_page,
        has_next=result.has_next
    )


@router.get("/api/quarantine/pages/{quarantine_id}")
def get_quarantine_page(quarantine_id: str) -> QuarantinePageDetailResponse:
    """
    Get full details of a quarantine page including extraction JSON.
    
    Args:
        quarantine_id: The quarantine page UUID
    
    Returns:
        Full quarantine page details
    """
    db = get_db()
    
    page = db.get_quarantine_page(quarantine_id)
    
    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Quarantine page {quarantine_id} not found"
        )
    
    return QuarantinePageDetailResponse(
        id=page['id'],
        statement_id=page['statement_id'],
        page_number=page['page_number'],
        reason=page.get('reason'),
        delta_paise=page.get('delta_paise'),
        status=page['status'],
        created_at=page['created_at'],
        resolved_at=page.get('resolved_at'),
        resolution_notes=page.get('resolution_notes'),
        source_filename=page.get('source_filename'),
        bank=page.get('bank'),
        raw_extraction_json=page.get('raw_extraction_json'),
        corrected_extraction_json=page.get('corrected_extraction_json')
    )


@router.patch("/api/quarantine/pages/{quarantine_id}")
def resolve_quarantine_page(
    quarantine_id: str,
    request: ResolveQuarantineRequest
) -> ResolveQuarantineResponse:
    """
    Resolve a quarantine page with corrected extraction data.
    
    This marks the quarantine page as RESOLVED and stores the corrected
    extraction JSON. The corrected data will be used when revalidating
    the statement.
    
    Args:
        quarantine_id: The quarantine page UUID
        request: Resolution data with corrected extraction JSON
    
    Returns:
        Success confirmation
    """
    db = get_db()
    
    # Verify the quarantine page exists and is in QUARANTINED status
    page = db.get_quarantine_page(quarantine_id)
    
    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Quarantine page {quarantine_id} not found"
        )
    
    if page['status'] != 'QUARANTINED':
        raise HTTPException(
            status_code=400,
            detail=f"Quarantine page is already {page['status']}"
        )
    
    # Update the quarantine page
    updated = db.update_quarantine_page_resolution(
        quarantine_id,
        corrected_extraction_json=request.corrected_extraction_json,
        resolution_notes=request.resolution_notes
    )
    
    if not updated:
        raise HTTPException(
            status_code=500,
            detail="Failed to resolve quarantine page"
        )
    
    return ResolveQuarantineResponse(
        success=True,
        id=quarantine_id,
        status='RESOLVED',
        message="Quarantine page resolved successfully. Run revalidation to commit."
    )
