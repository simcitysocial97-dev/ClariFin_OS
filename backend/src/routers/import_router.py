"""Statement upload and import endpoints."""
# Import invalidate_cache from behavior_engine
import sys
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from categorizer import categorize
from csv_importer import CSVImporter
from metadata_extractor import MetadataExtractor
from src.common import get_db
from src.statement_extractor import StatementExtractor

sys.path.insert(0, str(Path(__file__).parent.parent))
from engines.behavior_engine import invalidate_behavior_cache as invalidate_cache

router = APIRouter(prefix="/api", tags=["import"])

# Upload directory
UPLOAD_DIR = Path(__file__).parent.parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ImportExecute(BaseModel):
    """Pydantic model for import execute request."""
    filename: str
    mapping: dict
    member: str = "Self"


@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    member: str = Form("Self"),
):
    """Upload and process a PDF statement."""
    try:
        db = get_db()
        log = []

        # Save file
        filename = file.filename
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files allowed")

        save_path = UPLOAD_DIR / filename
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        log.append(f"📄 Processing: {filename}")

        # Check duplicate
        if db.get_duplicate_check_by_filename(filename):
            return {
                "success": False,
                "error": "File already imported",
                "log": log + ["⚠️ Already imported, skipping"],
            }

        # Extract
        extractor = StatementExtractor(str(save_path))
        result = extractor.extract()
        bank = result.get("bank", "Unknown")
        transactions = result.get("transactions", [])

        log.append(f"✅ Bank: {bank}")
        log.append(f"✅ Extracted {len(transactions)} transactions")

        # Categorize
        for txn in transactions:
            amount_paise = int(txn.get("amount_paise") or 0)
            amount_float = amount_paise / 100.0 if amount_paise else None
            cat, subcat = categorize(txn.get("description", ""), amount_float)
            txn["category"] = cat
            txn["subcategory"] = subcat
            txn["member"] = member

        # Insert
        period = result.get("statement_period", {})
        statement_id = db.insert_statement(
            bank=bank,
            file_name=filename,
            period_from=period.get("from", ""),
            period_to=period.get("to", ""),
        )
        db.insert_transactions(statement_id, transactions)

        # Metadata
        metadata = {}
        try:
            meta_extractor = MetadataExtractor(str(save_path), bank=bank)
            metadata = meta_extractor.extract()
            db.update_statement_metadata(statement_id, metadata)
            if metadata.get("total_amount_due"):
                log.append(f"✅ Total Due: ₹{metadata['total_amount_due']:,.2f}")
        except Exception as e:
            log.append(f"⚠️ Metadata: {str(e)[:60]}")

        # Validation
        total_due = metadata.get("total_amount_due")
        if total_due and total_due > 0:
            # Use amount_paise (canonical integer) for computation
            total_due_paise = int(round(total_due * 100))
            debit_sum_paise = sum(
                int(t.get("amount_paise") or 0)
                for t in transactions if t.get("type") == "debit"
            )
            credit_sum_paise = sum(
                int(t.get("amount_paise") or 0)
                for t in transactions if t.get("type") == "credit"
            )
            net_paise = debit_sum_paise - credit_sum_paise
            diff_paise = abs(net_paise - total_due_paise)
            diff_rupees = diff_paise / 100.0

            if diff_paise < 100:  # < ₹1.00
                val_status = "exact_match"
                log.append("✅ Validation: exact match")
            elif diff_paise < 5000:  # < ₹50.00
                val_status = "close_match"
                log.append(f"⚠️ Validation: close match (₹{diff_rupees:.2f} off)")
            else:
                val_status = "mismatch"
                log.append(f"❌ Validation: mismatch (₹{diff_rupees:.2f} off)")

            db.update_validation_status(statement_id, val_status, round(diff_rupees, 2))
        else:
            db.update_validation_status(statement_id, "no_metadata", 0.0)
            log.append("⚠️ Validation: total due not found")

        log.append(f"✅ Saved (Member: {member})")

        # Invalidate behavior cache after data changes
        invalidate_cache()

        return {
            "success": True,
            "bank": bank,
            "transaction_count": len(transactions),
            "validation_status": val_status if total_due and total_due > 0 else "no_metadata",
            "metadata": metadata,
            "log": log,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/detect")
async def import_detect(file: UploadFile = File(...)):
    """Detect CSV/Excel format."""
    try:
        # Save file
        filename = file.filename
        suffix = Path(filename).suffix.lower()
        if suffix not in [".csv", ".xlsx", ".xls"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        save_path = UPLOAD_DIR / filename
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # Detect format
        importer = CSVImporter(str(save_path))
        detected = importer.detect_format()

        return {
            "filename": filename,
            "columns": detected.get("columns", []),
            "sample_rows": detected.get("sample_rows", []),
            "detected_mapping": detected.get("detected_mapping", {}),
            "row_count": detected.get("row_count", 0),
            "date_format": detected.get("date_format", "%d/%m/%Y"),
            "skip_rows": detected.get("skip_rows", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/execute")
def import_execute(data: ImportExecute):
    """Execute CSV/Excel import."""
    try:
        db = get_db()
        save_path = UPLOAD_DIR / data.filename

        if not save_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        importer = CSVImporter(str(save_path))
        transactions, warnings = importer.import_transactions(data.mapping)

        if not transactions:
            return {
                "success": False,
                "error": "No valid transactions found",
                "warnings": warnings,
            }

        # Insert
        inserted = db.insert_csv_transactions(
            transactions=transactions,
            member=data.member,
            source="csv",
            bank=data.mapping.get("bank", "Manual Import"),
            file_name=data.filename,
        )

        # Invalidate behavior cache after data changes
        invalidate_cache()

        return {
            "success": True,
            "count": inserted,
            "skipped": len(transactions) - inserted,
            "errors": warnings,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
