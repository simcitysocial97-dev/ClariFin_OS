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


def _resolve_upload_path(filename: str) -> Path:
    """Return ``filename`` confined to :data:`UPLOAD_DIR`.

    The name is reduced to its final component and the resolved parent is
    compared against the resolved upload root, so neither ``../`` segments nor
    an absolute path can escape. This is the single containment rule for every
    handler in this module.
    """

    safe_name = Path(filename).name
    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    # `filename` is caller-controlled. It is reduced to its final component
    # above and the resolved parent is compared to the resolved upload root
    # below, so neither `../` segments nor an absolute path can escape. CodeQL
    # models neither `PurePath.name` nor the containment comparison as a
    # path-injection sanitizer, so the two sites that touch the derived path
    # carry an explicit, justified suppression.
    candidate = UPLOAD_DIR / safe_name  # codeql[py/path-injection]
    if candidate.resolve().parent != UPLOAD_DIR.resolve():  # codeql[py/path-injection]
        raise HTTPException(status_code=400, detail="Invalid filename")
    return candidate


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
    save_path = _resolve_upload_path(safe_filename)
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
    save_path = _resolve_upload_path(safe_filename)
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
    # `filename` is caller-controlled, so it is confined to UPLOAD_DIR exactly
    # as the two upload handlers above do. Without this check a request could
    # name `../../etc/passwd` and have the importer read a file outside the
    # upload directory (CWE-22). `_resolve_upload_path` is the single
    # containment rule; CodeQL cannot see it, hence the suppression.
    save_path = _resolve_upload_path(data.filename)  # codeql[py/path-injection]

    if not save_path.exists():  # codeql[py/path-injection]
        raise HTTPException(status_code=404, detail="File not found")

    service = ImportService()
    return service.import_csv(
        save_path=str(save_path),
        mapping=data.mapping,
        member=data.member,
    )
