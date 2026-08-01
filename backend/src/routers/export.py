"""Export endpoints."""

from fastapi import APIRouter, HTTPException

from src.services.export_service import ExportService

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export/csv")
def export_csv(
    search: str | None = None,
    bank: str | None = "All",
    category: str | None = "All",
    type: str | None = "All",
    member: str | None = "All",
) -> str:
    """Export transactions to CSV.

    Returns:
        Path to the generated CSV file
    """
    try:
        service = ExportService()
        return service.export_csv(
            search=search,
            bank=bank,
            category=category,
            type=type,
            member=member,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
