"""Statement upload and import endpoints."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.config import settings
from src.services.import_service import ImportService

router = APIRouter(prefix="/api/v1", tags=["import"])

UPLOAD_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ImportExecute(BaseModel):
    """Pydantic model for import execute request."""

    filename: str
    mapping: dict[str, Any]
    member: str = "Self"


@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    member: str = Form("Self"),
) -> dict[str, Any]:
    """Upload and process a PDF statement."""
    filename = file.filename or ""
    if Path(filename).suffix.lower() not in settings.pdf_upload_extensions:
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    safe_filename = Path(filename).name
    save_path = UPLOAD_DIR / safe_filename
    if save_path.resolve().parent != UPLOAD_DIR.resolve():
        raise HTTPException(status_code=400, detail="Invalid filename")
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size")
    with open(save_path, "wb") as f:
        f.write(content)

    service = ImportService()
    return service.upload_statement(
        save_path=str(save_path),
        filename=safe_filename,
        member=member,
    )


@router.post("/import/detect")
async def import_detect(file: UploadFile = File(...)) -> dict[str, Any]:
    """Detect CSV/Excel format."""
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.tabular_upload_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    safe_filename = Path(filename).name or "unknown"
    save_path = UPLOAD_DIR / safe_filename
    if save_path.resolve().parent != UPLOAD_DIR.resolve():
        raise HTTPException(status_code=400, detail="Invalid filename")
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="File exceeds maximum upload size")
    with open(save_path, "wb") as f:
        f.write(content)

    service = ImportService()
    return service.detect_import_format(save_path=str(save_path))


@router.post("/import/execute")
def import_execute(data: ImportExecute) -> dict[str, Any]:
    """Execute CSV/Excel import."""
    save_path = UPLOAD_DIR / data.filename

    if not save_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    service = ImportService()
    return service.import_csv(
        save_path=str(save_path),
        mapping=data.mapping,
        member=data.member,
    )
