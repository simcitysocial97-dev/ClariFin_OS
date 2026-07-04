"""
Imports Router - Staging-based PDF Import Pipeline
====================================================
New endpoints for atomic statement import.

These endpoints do NOT modify the existing /api/upload behavior.
They provide a new staging pipeline with validation before commit.
"""

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.dependencies import get_db, UPLOAD_DIR
from src.extraction.factory import get_extractor, get_extractor_type
from src.extraction.base_extractor import ExtractionError
from src.extraction.fingerprint import compute_fingerprint
from src.extraction.bbox_extractor import extract_with_bbox, BboxExtractionError, ColumnValidationError
from src.extraction.bank_detector import detect_bank_from_pdf
from src.categorizer import categorize
from src.logger import log
from src.engines.statement_validator import validate_staged_statement, commit_staged_statement, revalidate_staged_statement
from src.utils import parse_date_to_iso
from src.utils.money import to_paise
from decimal import Decimal

router = APIRouter()


class SetBalancesRequest(BaseModel):
    """Request body for setting opening/closing balances."""
    opening_balance_paise: int = Field(..., ge=0, description="Opening balance in paise (must be >= 0)")
    closing_balance_paise: int = Field(..., ge=0, description="Closing balance in paise (must be >= 0)")


class BboxNormInput(BaseModel):
    """Normalized bbox input for a specific page."""
    page_number: int = Field(..., ge=1, description="Page number (1-indexed)")
    x0: float = Field(..., ge=0.0, le=1.0, description="Left edge (0-1 normalized)")
    y0: float = Field(..., ge=0.0, le=1.0, description="Top edge (0-1 normalized)")
    x1: float = Field(..., ge=0.0, le=1.0, description="Right edge (0-1 normalized)")
    y1: float = Field(..., ge=0.0, le=1.0, description="Bottom edge (0-1 normalized)")


class ReextractRequest(BaseModel):
    """Request body for re-extraction with bbox."""
    apply_to_all_pages: bool = Field(True, description="Apply page 1 bbox to all pages")
    bboxes_norm: List[BboxNormInput] = Field(..., min_items=1, description="List of normalized bboxes")
    save_as_template: bool = Field(False, description="Save bbox as new template")
    template_notes: Optional[str] = Field(None, description="Optional notes for template")


# Upload configuration
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
CHUNK_SIZE = 64 * 1024  # 64KB chunks


def _try_bbox_extraction_with_template(
    db,
    file_path: Path,
    fingerprint: str,
    bank_hint: str
) -> tuple[Optional[list], Optional[str], Optional[str], Optional[list]]:
    """
    Try to extract using a matching template's bbox.
    
    Returns:
        Tuple of (normalized_rows, template_id, bbox_norm_json, preview_rows) or (None, None, None, None)
    """
    # Look up template by fingerprint
    template = db.get_layout_template_by_fingerprint(fingerprint)
    
    if not template:
        return None, None, None, None
    
    if not template.get('bbox_norm'):
        log.debug("Template found but no bbox_norm defined")
        return None, None, None, None
    
    template_id = template['id']
    bbox_norm = template['bbox_norm']
    
    log.info("Found matching template %s for fingerprint, attempting bbox extraction", template_id[:8])
    
    try:
        # Convert bbox_norm to input format
        bboxes_norm = [{
            'page_number': 1,
            'x0': bbox_norm[0],
            'y0': bbox_norm[1],
            'x1': bbox_norm[2],
            'y1': bbox_norm[3],
        }]
        
        # Extract with bbox
        normalized_rows = extract_with_bbox(
            str(file_path),
            bboxes_norm,
            apply_to_all_pages=True
        )
        
        # Mark template as used
        db.mark_layout_template_used(template_id)
        
        # Generate preview (first 10 rows)
        preview_rows = [
            {
                'date': r.get('date'),
                'description': r.get('description'),
                'debit_paise': r.get('debit_paise'),
                'credit_paise': r.get('credit_paise'),
                'balance_paise': r.get('balance_paise'),
            }
            for r in normalized_rows[:10]
        ]
        
        return normalized_rows, template_id, json.dumps(bbox_norm), preview_rows
        
    except (BboxExtractionError, ColumnValidationError) as e:
        log.warning("Template bbox extraction failed: %s", str(e))
        return None, None, None, None


@router.post("/api/imports/pdf")
async def import_pdf_staged(
    file: UploadFile = File(...),
    member: Optional[str] = Form("Self"),
    auto_commit: Optional[bool] = Form(True),
):
    """
    Upload and process PDF bank statement with staging.
    
    Flow:
    1. Save PDF to uploads/
    2. Compute fingerprint and check for matching template
    3. If template exists with bbox: use bbox extraction
    4. Else: fall back to legacy/docling extractor
    5. Stage: Create statement_imports record + staged_transactions
    6. Validate: Compute delta_paise
    7. If valid AND auto_commit=True: Commit to ledger
    8. Return statement_id, status, delta_paise, counts, fingerprint, template info
    
    If validation fails: status='NEEDS_REVIEW', nothing committed
    If extraction fails: status='FAILED' with error message
    
    Environment:
        CLARIFIN_EXTRACTOR: Set to "legacy" (default) or "docling"
    """
    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Sanitize filename
    filename = Path(file.filename).name
    filename = filename.replace(" ", "_")

    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Save file using chunked streaming
    file_path = UPLOAD_DIR / filename
    total_size = 0

    with tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode="wb") as tmp:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File exceeds maximum size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB"
                )
            tmp.write(chunk)

        tmp.seek(0)
        with open(file_path, "wb") as destination_file:
            shutil.copyfileobj(tmp, destination_file)

    log.info("Staged upload: %s (%.1f KB)", filename, total_size / 1024)

    # Generate import ID
    import_id = str(uuid.uuid4())
    
    db = get_db()
    
    try:
        # Detect bank for fingerprint and template matching
        bank_hint = detect_bank_from_pdf(str(file_path), max_pages=3) or "Unknown"
        
        # Compute fingerprint
        fingerprint = compute_fingerprint(str(file_path), bank_hint=bank_hint)
        log.info("Computed fingerprint: %s...", fingerprint[:16])
        
        # Try template-based bbox extraction first
        normalized_rows, template_id, bbox_norm_json, preview_rows = _try_bbox_extraction_with_template(
            db, file_path, fingerprint, bank_hint
        )
        
        template_applied = normalized_rows is not None
        extractor_name = "bbox"
        suggested_bbox_norm = None
        
        if not normalized_rows:
            # Fall back to legacy/docling extractor
            log.info("No matching template with bbox, using legacy extractor")
            extractor = get_extractor()
            result = extractor.extract(str(file_path))
            normalized_rows = result.normalized_rows
            extractor_name = extractor.name
            
            # Generate preview for legacy extraction
            preview_rows = [
                {
                    'date': r.get('date'),
                    'description': r.get('description'),
                    'debit_paise': r.get('debit_paise'),
                    'credit_paise': r.get('credit_paise'),
                    'balance_paise': r.get('balance_paise'),
                }
                for r in normalized_rows[:10]
            ]
            
            # Check if template exists (without bbox) to suggest
            template = db.get_layout_template_by_fingerprint(fingerprint)
            if template and template.get('bbox_norm'):
                suggested_bbox_norm = template['bbox_norm']
        else:
            # Get balances from template extraction (may be None)
            result = None
        
        # Convert balances to paise
        if result:
            opening_paise = to_paise(Decimal(str(result.opening_balance))) if result.opening_balance else None
            closing_paise = to_paise(Decimal(str(result.closing_balance))) if result.closing_balance else None
            bank = result.bank
        else:
            opening_paise = None
            closing_paise = None
            bank = bank_hint
        
        # Stage in database
        db.insert_statement_import({
            'id': import_id,
            'source_filename': filename,
            'source_path': str(file_path.relative_to(UPLOAD_DIR.parent)),
            'bank': bank,
            'status': 'STAGED',
            'opening_balance_paise': opening_paise,
            'closing_balance_paise': closing_paise,
        })
        
        # Store fingerprint and template info
        db.update_statement_import_fingerprint(
            import_id,
            fingerprint,
            template_id=template_id,
            bbox_norm_json=bbox_norm_json
        )
        
        # Insert staged transactions
        db.insert_staged_transactions(import_id, normalized_rows)
        
        # Validate
        validation = validate_staged_statement(db, import_id)
        
        response = {
            'success': True,
            'statement_id': import_id,
            'status': 'STAGED',
            'fingerprint': fingerprint,
            'template_applied': template_applied,
            'suggested_bbox_norm': suggested_bbox_norm,
            'preview_rows': preview_rows,
            'delta_paise': validation['delta_paise'],
            'transaction_count': len(normalized_rows),
            'bank': bank,
            'filename': filename,
            'extractor': extractor_name,
            'validation': {
                'valid': validation['valid'],
                'reason': validation['reason'],
                'opening_balance_paise': validation['opening_balance_paise'],
                'closing_balance_paise': validation['closing_balance_paise'],
            }
        }
        
        # Auto-commit if valid and requested
        if auto_commit and validation['valid']:
            commit_result = commit_staged_statement(db, import_id, member=member)
            if commit_result['success']:
                response['status'] = 'COMMITTED'
                response['committed'] = {
                    'inserted': commit_result['inserted'],
                    'skipped': commit_result['skipped']
                }
            else:
                response['status'] = 'FAILED'
                response['error'] = commit_result['error']
                db.update_statement_import_status(
                    import_id,
                    'FAILED',
                    error=commit_result['error']
                )
        elif not validation['valid']:
            db.update_statement_import_status(
                import_id,
                'NEEDS_REVIEW',
                delta_paise=validation['delta_paise']
            )
            response['status'] = 'NEEDS_REVIEW'
        
        return response
        
    except RuntimeError as e:
        error_msg = str(e)
        log.error("Extraction configuration error: %s", error_msg)
        
        if file_path.exists():
            file_path.unlink()
        
        try:
            db.insert_statement_import({
                'id': import_id,
                'source_filename': filename,
                'source_path': str(file_path.relative_to(UPLOAD_DIR.parent)) if file_path.exists() else filename,
                'bank': 'Unknown',
                'status': 'FAILED',
                'opening_balance_paise': None,
                'closing_balance_paise': None,
            })
            db.update_statement_import_status(import_id, 'FAILED', error=error_msg)
        except Exception:
            pass
        
        raise HTTPException(status_code=500, detail=f"Extraction failed: {error_msg}")
        
    except ExtractionError as e:
        error_msg = str(e)
        log.error("Extraction failed for %s: %s", filename, error_msg)
        
        if file_path.exists():
            file_path.unlink()
        
        try:
            # Create import record with FAILED status
            db.insert_statement_import({
                'id': import_id,
                'source_filename': filename,
                'source_path': str(file_path.relative_to(UPLOAD_DIR.parent)) if file_path.exists() else filename,
                'bank': 'Unknown',
                'status': 'FAILED',
                'opening_balance_paise': None,
                'closing_balance_paise': None,
            })
            # Set FAILED status with EXTRACTION_FAILED reason
            db.update_statement_import_status(
                import_id, 
                'FAILED', 
                error=f"EXTRACTION_FAILED: {error_msg}"
            )
        except Exception:
            pass
        
        raise HTTPException(status_code=422, detail=f"PDF extraction failed: {error_msg}")
    
    except BboxExtractionError as e:
        error_msg = str(e)
        log.error("BBox extraction failed for %s: %s", filename, error_msg)
        
        if file_path.exists():
            file_path.unlink()
        
        try:
            # Create import record with FAILED status
            db.insert_statement_import({
                'id': import_id,
                'source_filename': filename,
                'source_path': str(file_path.relative_to(UPLOAD_DIR.parent)) if file_path.exists() else filename,
                'bank': 'Unknown',
                'status': 'FAILED',
                'opening_balance_paise': None,
                'closing_balance_paise': None,
            })
            # Set FAILED status with BBOX_REQUIRED reason
            db.update_statement_import_status(
                import_id, 
                'FAILED', 
                error=f"BBOX_REQUIRED: {error_msg}"
            )
        except Exception:
            pass
        
        raise HTTPException(status_code=422, detail=f"PDF extraction failed: {error_msg}")
    
    except ColumnValidationError as e:
        error_msg = str(e)
        log.error("Column validation failed for %s: %s", filename, error_msg)
        
        if file_path.exists():
            file_path.unlink()
        
        try:
            # Create import record with NEEDS_REVIEW status
            db.insert_statement_import({
                'id': import_id,
                'source_filename': filename,
                'source_path': str(file_path.relative_to(UPLOAD_DIR.parent)) if file_path.exists() else filename,
                'bank': 'Unknown',
                'status': 'NEEDS_REVIEW',
                'opening_balance_paise': None,
                'closing_balance_paise': None,
            })
            # Set NEEDS_REVIEW status with BBOX_REQUIRED reason
            db.update_statement_import_status(
                import_id, 
                'NEEDS_REVIEW', 
                error=f"BBOX_REQUIRED: {error_msg}"
            )
        except Exception:
            pass
        
        raise HTTPException(status_code=422, detail=f"PDF extraction failed: {error_msg}")
        
    except Exception as e:
        log.error("Error processing staged import: %s", str(e))
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/api/imports/{statement_id}/reextract")
def reextract_with_bbox(
    statement_id: str,
    body: ReextractRequest,
    member: Optional[str] = Form("Self"),
):
    """
    Re-extract statement using user-provided bbox coordinates.
    
    This endpoint:
    1. Loads the original PDF from the statement import
    2. Runs bbox extraction with the provided bboxes_norm
    3. Clears existing staged_transactions
    4. Inserts newly extracted transactions
    5. Re-runs validation
    6. If save_as_template=True and extraction successful, stores template
    7. Returns updated preview + validation results
    
    Args:
        statement_id: The statement import UUID
        body: ReextractRequest with bboxes_norm and options
        member: Member name for transactions (if auto-commit occurs)
    
    Returns:
        {
            'success': bool,
            'statement_id': str,
            'status': str,
            'fingerprint': str,
            'template_applied': bool,
            'template_saved': bool,
            'preview_rows': list,
            'delta_paise': int,
            'transaction_count': int,
            'validation': dict,
            'error': str | None
        }
    """
    db = get_db()
    
    # Check if import exists
    import_record = db.get_statement_import_with_fingerprint(statement_id)
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Check if already committed
    if import_record['status'] == 'COMMITTED':
        return {
            'success': False,
            'statement_id': statement_id,
            'status': 'COMMITTED',
            'fingerprint': import_record.get('fingerprint', ''),
            'template_applied': False,
            'template_saved': False,
            'preview_rows': [],
            'delta_paise': 0,
            'transaction_count': 0,
            'validation': {'valid': True, 'reason': None},
            'error': 'Import already committed'
        }
    
    # Get source PDF path
    source_path = import_record.get('source_path')
    if not source_path:
        raise HTTPException(status_code=400, detail="Source PDF not available for this import")
    
    # Build absolute path
    try:
        file_path = UPLOAD_DIR.parent / source_path
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Source PDF file not found")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Source PDF path error: {str(e)}")
    
    try:
        # Convert bboxes_norm to extraction format
        bboxes_norm = [
            {
                'page_number': bb.page_number,
                'x0': bb.x0,
                'y0': bb.y0,
                'x1': bb.x1,
                'y1': bb.y1,
            }
            for bb in body.bboxes_norm
        ]
        
        log.info(
            "Re-extracting %s with %d bbox(es), apply_to_all_pages=%s",
            statement_id, len(bboxes_norm), body.apply_to_all_pages
        )
        
        # Run bbox extraction
        normalized_rows = extract_with_bbox(
            str(file_path),
            bboxes_norm,
            apply_to_all_pages=body.apply_to_all_pages
        )
        
        # Generate preview
        preview_rows = [
            {
                'date': r.get('date'),
                'description': r.get('description'),
                'debit_paise': r.get('debit_paise'),
                'credit_paise': r.get('credit_paise'),
                'balance_paise': r.get('balance_paise'),
            }
            for r in normalized_rows[:10]
        ]
        
        # Replace staged transactions
        db.clear_and_insert_staged_transactions(statement_id, normalized_rows)
        
        # Re-validate
        validation = validate_staged_statement(db, statement_id)
        
        # Save as template if requested
        template_saved = False
        if body.save_as_template and normalized_rows:
            fingerprint = import_record.get('fingerprint')
            if fingerprint:
                # Get page dimensions from first bbox
                import pdfplumber
                with pdfplumber.open(str(file_path)) as pdf:
                    if pdf.pages:
                        page_width = float(pdf.pages[0].width)
                        page_height = float(pdf.pages[0].height)
                
                # Use first bbox as the template
                first_bbox = bboxes_norm[0]
                bbox_norm = [first_bbox['x0'], first_bbox['y0'], first_bbox['x1'], first_bbox['y1']]
                
                template_id = db.upsert_layout_template(
                    fingerprint=fingerprint,
                    bank=import_record.get('bank', 'Unknown'),
                    page_width=page_width,
                    page_height=page_height,
                    bbox_norm=bbox_norm,
                    notes=body.template_notes or f"Template created from re-extraction of {import_record.get('source_filename', 'unknown')}"
                )
                
                # Update import with template reference
                db.update_statement_import_fingerprint(
                    statement_id,
                    fingerprint,
                    template_id=template_id,
                    bbox_norm_json=json.dumps(bbox_norm)
                )
                
                template_saved = True
                log.info("Saved template %s for fingerprint %s...", template_id[:8], fingerprint[:16])
        
        response = {
            'success': True,
            'statement_id': statement_id,
            'status': 'STAGED',
            'fingerprint': import_record.get('fingerprint', ''),
            'template_applied': True,
            'template_saved': template_saved,
            'preview_rows': preview_rows,
            'delta_paise': validation['delta_paise'],
            'transaction_count': len(normalized_rows),
            'validation': {
                'valid': validation['valid'],
                'reason': validation['reason'],
                'opening_balance_paise': validation['opening_balance_paise'],
                'closing_balance_paise': validation['closing_balance_paise'],
            },
            'error': None
        }
        
        # Update status based on validation
        if validation['valid']:
            # Optionally auto-commit valid re-extractions
            pass  # Keep as STAGED for user review
        else:
            db.update_statement_import_status(
                statement_id,
                'NEEDS_REVIEW',
                delta_paise=validation['delta_paise']
            )
            response['status'] = 'NEEDS_REVIEW'
        
        return response
        
    except ColumnValidationError as e:
        error_msg = str(e)
        log.warning("Column validation failed for re-extraction: %s", error_msg)
        
        db.update_statement_import_status(
            statement_id,
            'NEEDS_REVIEW',
            error=error_msg
        )
        
        return {
            'success': False,
            'statement_id': statement_id,
            'status': 'NEEDS_REVIEW',
            'fingerprint': import_record.get('fingerprint', ''),
            'template_applied': False,
            'template_saved': False,
            'preview_rows': [],
            'delta_paise': None,
            'transaction_count': 0,
            'validation': {'valid': False, 'reason': error_msg},
            'error': error_msg
        }
        
    except BboxExtractionError as e:
        error_msg = str(e)
        log.error("BBox extraction failed for re-extraction: %s", error_msg)
        
        return {
            'success': False,
            'statement_id': statement_id,
            'status': import_record['status'],
            'fingerprint': import_record.get('fingerprint', ''),
            'template_applied': False,
            'template_saved': False,
            'preview_rows': [],
            'delta_paise': import_record.get('delta_paise'),
            'transaction_count': 0,
            'validation': {'valid': False, 'reason': error_msg},
            'error': error_msg
        }
        
    except Exception as e:
        error_msg = str(e)
        log.error("Unexpected error in re-extraction: %s", error_msg)
        
        return {
            'success': False,
            'statement_id': statement_id,
            'status': import_record['status'],
            'fingerprint': import_record.get('fingerprint', ''),
            'template_applied': False,
            'template_saved': False,
            'preview_rows': [],
            'delta_paise': import_record.get('delta_paise'),
            'transaction_count': 0,
            'validation': {'valid': False, 'reason': error_msg},
            'error': error_msg
        }


@router.get("/api/imports/{statement_id}")
def get_import_status(statement_id: str):
    """
    Get status of a staged import.
    
    Returns:
        {
            'id': str,
            'status': str,
            'source_filename': str,
            'bank': str,
            'delta_paise': int,
            'opening_balance_paise': int,
            'closing_balance_paise': int,
            'transaction_count': int,
            'created_at': str,
            'committed_at': str | None,
            'error': str | None
        }
    """
    db = get_db()
    import_record = db.get_statement_import(statement_id)
    
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    
    return {
        'id': import_record['id'],
        'status': import_record['status'],
        'source_filename': import_record['source_filename'],
        'bank': import_record['bank'],
        'delta_paise': import_record.get('delta_paise'),
        'opening_balance_paise': import_record.get('opening_balance_paise'),
        'closing_balance_paise': import_record.get('closing_balance_paise'),
        'transaction_count': import_record.get('transaction_count', 0),
        'created_at': import_record['created_at'],
        'committed_at': import_record.get('committed_at'),
        'error': import_record.get('error'),
    }


@router.get("/api/statements/{statement_id}/file")
def get_statement_file(statement_id: str):
    """
    Get the PDF file for a statement import.
    
    Security:
    - Path is resolved using realpath to prevent path traversal
    - Only serves files under UPLOAD_DIR
    - Returns 404 for any error (does not leak file existence)
    
    Args:
        statement_id: The statement import UUID
        
    Returns:
        FileResponse with PDF content-type
        
    Raises:
        HTTPException 404: If statement not found, file not found, or path traversal detected
    """
    db = get_db()
    
    # Lookup statement import
    import_record = db.get_statement_import(statement_id)
    if not import_record:
        raise HTTPException(status_code=404, detail="Statement not found")
    
    # Get source path
    source_path = import_record.get('source_path')
    if not source_path:
        raise HTTPException(status_code=404, detail="Statement file not available")
    
    # Build absolute path - source_path is relative to UPLOAD_DIR.parent (data/)
    # source_path format: "uploads/filename.pdf"
    try:
        file_path = UPLOAD_DIR.parent / source_path
    except Exception:
        raise HTTPException(status_code=404, detail="Statement file not found")
    
    # Resolve to absolute path and check for path traversal
    try:
        resolved_path = os.path.realpath(file_path)
        upload_dir_resolved = os.path.realpath(UPLOAD_DIR)
    except Exception:
        raise HTTPException(status_code=404, detail="Statement file not found")
    
    # Security check: ensure resolved path is under upload directory
    # Use path separator to prevent partial matches (e.g., /uploads vs /uploads_malicious)
    if not resolved_path.startswith(upload_dir_resolved + os.sep) and resolved_path != upload_dir_resolved:
        log.warning("Path traversal attempt blocked: %s (resolved: %s, upload_dir: %s)",
                    source_path, resolved_path, upload_dir_resolved)
        raise HTTPException(status_code=404, detail="Statement not found")
    
    # Check file exists and is a file
    if not os.path.isfile(resolved_path):
        raise HTTPException(status_code=404, detail="Statement file not found")
    
    # Return file
    return FileResponse(
        path=resolved_path,
        media_type="application/pdf",
        filename=import_record.get('source_filename', 'statement.pdf')
    )


@router.post("/api/imports/{statement_id}/set-balances")
def set_statement_balances(
    statement_id: str, 
    body: SetBalancesRequest,
    member: Optional[str] = Form("Self")
):
    """
    Set opening/closing balances for a NEEDS_REVIEW import.
    
    This endpoint:
    1. Validates inputs (>=0, integers)
    2. Updates statement_imports.opening_balance_paise / closing_balance_paise
    3. Calls the existing revalidate flow to revalidate and potentially commit
    
    The endpoint does NOT directly modify immutable transactions; it only
    enables the standard revalidate+commit path.
    
    Args:
        statement_id: The statement import UUID
        body: SetBalancesRequest with opening_balance_paise and closing_balance_paise
        member: Member name for transactions (if commit occurs)
    
    Returns:
        {
            'success': bool,
            'delta_paise': int,
            'valid': bool,
            'committed': bool,
            'inserted': int,
            'skipped': int,
            'error': str | None
        }
    """
    db = get_db()
    
    # Check if exists
    import_record = db.get_statement_import(statement_id)
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Check if already committed
    if import_record['status'] == 'COMMITTED':
        return {
            'success': False,
            'delta_paise': 0,
            'valid': True,
            'committed': True,
            'inserted': 0,
            'skipped': 0,
            'error': 'Import already committed'
        }
    
    # Update balances
    updated = db.update_statement_import_balances(
        statement_id,
        body.opening_balance_paise,
        body.closing_balance_paise
    )
    
    if not updated:
        return {
            'success': False,
            'delta_paise': 0,
            'valid': False,
            'committed': False,
            'inserted': 0,
            'skipped': 0,
            'error': 'Failed to update balances'
        }
    
    # Revalidate and potentially commit
    result = revalidate_staged_statement(db, statement_id, member=member)
    return result


@router.post("/api/imports/{statement_id}/commit")
def commit_staged_import(statement_id: str, member: Optional[str] = Form("Self")):
    """
    Manually commit a staged import (if validation passes).
    
    Returns:
        {
            'success': bool,
            'inserted': int,
            'skipped': int,
            'error': str | None
        }
    """
    db = get_db()
    
    # Check if exists
    import_record = db.get_statement_import(statement_id)
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Check if already committed
    if import_record['status'] == 'COMMITTED':
        return {
            'success': False,
            'inserted': 0,
            'skipped': 0,
            'error': 'Import already committed'
        }
    
    # Commit
    result = commit_staged_statement(db, statement_id, member=member)
    return result


@router.post("/api/imports/{statement_id}/discard")
def discard_staged_import(statement_id: str):
    """
    Discard a staged import (deletes staging records, not PDF).
    
    Returns:
        {'success': bool}
    """
    db = get_db()
    
    # Check if exists
    import_record = db.get_statement_import(statement_id)
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Check if already committed
    if import_record['status'] == 'COMMITTED':
        raise HTTPException(status_code=400, detail="Cannot discard committed import")
    
    # Delete (cascades to staged_transactions)
    deleted = db.delete_statement_import(statement_id)
    
    return {'success': deleted}


@router.get("/api/imports")
def list_imports(
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
):
    """List staged imports with pagination."""
    db = get_db()
    result = db.list_statement_imports(status=status, page=page, per_page=per_page)
    
    return {
        'items': result.items,
        'total': result.total,
        'page': result.page,
        'per_page': result.per_page,
        'has_next': result.has_next,
    }


@router.post("/api/imports/{statement_id}/revalidate")
def revalidate_import(statement_id: str, member: Optional[str] = Form("Self")):
    """
    Revalidate a statement and commit if valid.
    
    This endpoint:
    1. Revalidates the staged transactions
    2. If delta == 0, atomically commits staged_transactions to immutable ledger
    3. Updates statement_imports status accordingly
    
    Args:
        statement_id: The statement import UUID
        member: Member name for transactions
    
    Returns:
        {
            'success': bool,
            'delta_paise': int,
            'valid': bool,
            'committed': bool,
            'inserted': int,
            'skipped': int,
            'error': str | None
        }
    """
    db = get_db()
    
    # Check if exists
    import_record = db.get_statement_import(statement_id)
    if not import_record:
        raise HTTPException(status_code=404, detail="Import not found")
    
    # Check if already committed
    if import_record['status'] == 'COMMITTED':
        return {
            'success': False,
            'delta_paise': 0,
            'valid': True,
            'committed': True,
            'inserted': 0,
            'skipped': 0,
            'error': 'Import already committed'
        }
    
    # Revalidate and potentially commit
    result = revalidate_staged_statement(db, statement_id, member=member)
    return result
