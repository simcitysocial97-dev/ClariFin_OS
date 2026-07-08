"""Export endpoints."""
import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.common import clean_description, format_date_display
from src.repositories import TransactionRepository

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/export/csv")
def export_csv(
    search: str | None = None,
    bank: str | None = "All",
    category: str | None = "All",
    type: str | None = "All",
    member: str | None = "All",
):
    """Export transactions to CSV."""
    try:
        repo = TransactionRepository()
        filters = {}
        if search:
            filters["search"] = search
        if bank and bank != "All":
            filters["bank"] = bank
        if category and category != "All":
            filters["category"] = category
        if type and type != "All":
            filters["type"] = type
        if member and member != "All":
            filters["member"] = member

        raw = repo.get_all_transactions_with_bank(filters)

        output = io.StringIO()
        output.write("Date,Bank,Description,Amount,Type,Category\n")

        for txn in raw:
            date = format_date_display(txn.get("date", ""))
            bank_name = txn.get("bank", "")
            desc = (clean_description(txn.get("description", ""))).replace(",", ";").replace('"', '""')
            amount = txn.get("amount", 0)
            txn_type = txn.get("type", "")
            cat = txn.get("category", "")

            output.write(f'"{date}","{bank_name}","{desc}",{amount},"{txn_type}","{cat}"\n')

        csv_data = output.getvalue()
        output.close()

        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transactions.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
