"""
Upload Router
=============
Endpoints for file uploads and CSV imports.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form

from src.dependencies import (
    get_db,
    UPLOAD_DIR,
    ImportExecute,
)
from src.categorizer import categorize
from src.statement_extractor import StatementExtractor
from src.metadata_extractor import MetadataExtractor
from src.csv_importer import CSVImporter
from src.logger import log
from src.errors import UploadError, NotFoundError

router = APIRouter()

# Upload configuration
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
CHUNK_SIZE = 64 * 1024  # 64KB chunks


@router.post("/api/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    member: Optional[str] = Form("Self"),
):
    """Upload and process a PDF bank statement."""
    # Validate filename
    if not file.filename:
        raise UploadError("No filename provided")

    if not file.filename.lower().endswith(".pdf"):
        raise UploadError("Only PDF files are accepted")

    # Sanitize filename: strip path components and replace spaces
    filename = Path(file.filename).name
    filename = filename.replace(" ", "_")

    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Save file using chunked streaming
    file_path = UPLOAD_DIR / filename
    total_size = 0

    with tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode="wb") as tmp:
        # Read file in chunks
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)

            # Check file size limit
            if total_size > MAX_UPLOAD_SIZE:
                raise UploadError(f"File exceeds maximum size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB")

            tmp.write(chunk)

        # Copy from temp file to final destination
        tmp.seek(0)
        with open(file_path, "wb") as destination_file:
            shutil.copyfileobj(tmp, destination_file)

    log.info("Uploaded %s (%.1f KB)", filename, total_size / 1024)

    # Extract metadata
    extractor = MetadataExtractor(str(file_path), bank="Unknown")
    metadata = extractor.extract()

    # Extract transactions
    statement_extractor = StatementExtractor(str(file_path))
    extract_result = statement_extractor.extract()
    transactions = extract_result.get("transactions", [])

    # Categorize transactions
    for txn in transactions:
        txn["category"] = categorize(txn.get("description", ""))

    # Save to database
    db = get_db()
    statement_id = db.insert_statement(
        bank=metadata.get("bank", "Unknown"),
        file_name=filename,
        period_from=metadata.get("bill_cycle_start", ""),
        period_to=metadata.get("bill_cycle_end", ""),
        card_last4=metadata.get("card_last4", ""),
    )

    # Insert transactions
    inserted = db.insert_transactions(statement_id, transactions)

    log.info("Processed %s: %d transactions extracted for bank %s", filename, inserted, metadata.get("bank", "Unknown"))

    return {
        "success": True,
        "statement_id": statement_id,
        "transactions_inserted": inserted,
        "metadata": metadata,
    }


@router.post("/api/import/detect")
async def import_detect(
    file: UploadFile = File(...),
):
    """Detect CSV format and return preview."""
    # Validate filename
    if not file.filename:
        raise UploadError("No filename provided")

    # Sanitize filename
    filename = Path(file.filename).name
    filename = filename.replace(" ", "_")

    # Ensure upload directory exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Save file using chunked streaming
    file_path = UPLOAD_DIR / filename
    total_size = 0

    with tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode="wb") as tmp:
        # Read file in chunks
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)

            # Check file size limit
            if total_size > MAX_UPLOAD_SIZE:
                raise UploadError(f"File exceeds maximum size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB")

            tmp.write(chunk)

        # Copy from temp file to final destination
        tmp.seek(0)
        with open(file_path, "wb") as destination_file:
            shutil.copyfileobj(tmp, destination_file)

    log.info("Uploaded %s for import detection (%.1f KB)", filename, total_size / 1024)

    # Detect format using saved file
    importer = CSVImporter(str(file_path))
    preview = importer.detect_format()
    return preview


@router.post("/api/import/execute")
def import_execute(data: ImportExecute):
    """Execute CSV import with mapping."""
    importer = CSVImporter()
    file_path = UPLOAD_DIR / data.filename

    if not file_path.exists():
        raise NotFoundError("File", data.filename)

    transactions = importer.import_csv(
        str(file_path),
        data.mapping,
        member=data.member,
    )

    db = get_db()
    inserted = db.insert_csv_transactions(
        transactions,
        member=data.member,
        source="csv",
        file_name=data.filename,
    )

    log.info("CSV import: %d transactions imported from %s", inserted, data.filename)

    return {
        "success": True,
        "transactions_inserted": inserted,
    }
