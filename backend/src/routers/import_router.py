"""Statement upload and import endpoints."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.services.import_service import ImportService

router = APIRouter(prefix="/api", tags=["import"])

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
    try:
        filename = file.filename or ""
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files allowed")

        save_path = UPLOAD_DIR / filename
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        service = ImportService()
        return service.upload_statement(
            save_path=str(save_path),
            filename=filename,
            member=member,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/import/detect")
async def import_detect(file: UploadFile = File(...)) -> dict[str, Any]:
    """Detect CSV/Excel format."""
    try:
        filename = file.filename or ""
        suffix = Path(filename).suffix.lower()
        if suffix not in [".csv", ".xlsx", ".xls"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        save_path = UPLOAD_DIR / filename if filename else UPLOAD_DIR / "unknown"
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        service = ImportService()
        return service.detect_import_format(save_path=str(save_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/import/execute")
def import_execute(data: ImportExecute) -> dict[str, Any]:
    """Execute CSV/Excel import."""
    try:
        save_path = UPLOAD_DIR / data.filename

        if not save_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        service = ImportService()
        return service.import_csv(
            save_path=str(save_path),
            mapping=data.mapping,
            member=data.member,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
