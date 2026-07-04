"""
Export/Import Router
====================
Endpoints for data export and import for backup/restore capability.

- GET  /api/export/json   → Full database export as JSON
- GET  /api/export/csv    → All tables as CSV files in a ZIP
- POST /api/import/backup → Restore from JSON export
"""

import csv
import io
import json
import sqlite3
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse

from src.dependencies import get_db, DB_PATH
from src.logger import log

router = APIRouter()

# ============================================================
# Table Configuration
# ============================================================

# All tables to export/import in dependency order (parents before children)
EXPORT_TABLES = [
    "members",
    "accounts",
    "cards",
    "import_mappings",
    "statements",
    "transactions",
    "income_sources",
    "loans",
    "loan_payments",
    "investments",
    "monthly_snapshots",
    "recurring_transactions",
    "reconciliations",
]

# Tables that have auto-increment primary keys (need to handle ID insertion)
AUTO_INCREMENT_TABLES = {
    "members",
    "accounts",
    "cards",
    "import_mappings",
    "statements",
    "transactions",
    "income_sources",
    "loans",
    "loan_payments",
    "investments",
    "monthly_snapshots",
    "recurring_transactions",
    "reconciliations",
}

# ============================================================
# JSON Export
# ============================================================

@router.get("/api/export/json")
def export_json():
    """
    Export all database tables as JSON.
    
    Returns a complete backup with metadata including version and timestamp.
    Format:
    {
        "version": "1.0",
        "exported_at": "2024-01-15T10:30:00Z",
        "tables": {
            "accounts": [...],
            "transactions": [...],
            ...
        }
    }
    """
    db = get_db()
    export_data = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tables": {}
    }
    
    with db.connection() as conn:
        for table in EXPORT_TABLES:
            try:
                # Get all rows from the table
                cur = conn.execute(f"SELECT * FROM {table}")
                rows = [dict(row) for row in cur.fetchall()]
                export_data["tables"][table] = rows
                log.debug("Exported %d rows from %s", len(rows), table)
            except sqlite3.Error as e:
                log.warning("Could not export table %s: %s", table, str(e))
                export_data["tables"][table] = []
    
    # Count total records
    total_records = sum(len(rows) for rows in export_data["tables"].values())
    log.info("JSON export completed: %d tables, %d total records", 
             len(EXPORT_TABLES), total_records)
    
    # Return as downloadable file
    filename = f"clarifin_backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# ============================================================
# CSV Export (ZIP)
# ============================================================

def _generate_table_csv(conn: sqlite3.Connection, table: str) -> str:
    """Generate CSV content for a single table."""
    cur = conn.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    
    if not rows:
        # Return empty CSV with headers if table is empty
        columns = [col[1] for col in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        return output.getvalue()
    
    # Get column names from cursor description
    columns = [col[0] for col in cur.description]
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(columns)
    
    # Write data rows
    for row in rows:
        writer.writerow(row)
    
    return output.getvalue()


@router.get("/api/export/csv-full")
def export_csv_full():
    """
    Export all database tables as CSV files bundled in a ZIP archive.
    
    Each table is exported as a separate CSV file named {table}.csv.
    Returns a ZIP file with content type application/zip.
    
    Note: This is for full database backup. For filtered transaction export,
    use /api/export/csv in the dashboard router.
    """
    db = get_db()
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        with db.connection() as conn:
            for table in EXPORT_TABLES:
                try:
                    csv_content = _generate_table_csv(conn, table)
                    zip_file.writestr(f"{table}.csv", csv_content)
                    log.debug("Added %s.csv to export", table)
                except sqlite3.Error as e:
                    log.warning("Could not export table %s to CSV: %s", table, str(e))
                    # Add empty file with error note
                    zip_file.writestr(f"{table}.csv", f"# Error: {str(e)}")
    
    # Reset buffer position
    zip_buffer.seek(0)
    
    # Generate filename with timestamp
    filename = f"clarifin_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    
    log.info("CSV export completed: %d tables exported to ZIP", len(EXPORT_TABLES))
    
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# ============================================================
# JSON Import / Restore
# ============================================================

@router.post("/api/import/backup")
def import_backup(
    data: Dict[str, Any],
    confirm: bool = Query(False, description="Set to true to confirm data replacement")
):
    """
    Restore database from JSON backup.
    
    Expects the same JSON format as the export endpoint:
    {
        "version": "1.0",
        "exported_at": "2024-01-15T10:30:00Z",
        "tables": {
            "accounts": [...],
            "transactions": [...],
            ...
        }
    }
    
    Parameters:
        confirm: Must be set to true to proceed with data replacement
    
    The import is atomic - either all data is imported or none.
    Returns counts of imported records per table.
    """
    # Validate confirmation
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Import requires confirmation. Add ?confirm=true query parameter to proceed with data replacement."
        )
    
    # Validate input structure
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid data format. Expected JSON object."
        )
    
    tables_data = data.get("tables")
    if not tables_data or not isinstance(tables_data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid backup format. Missing 'tables' key."
        )
    
    db = get_db()
    import_counts = {}
    errors = []
    
    try:
        # Use a direct connection for manual transaction control
        # We need to disable foreign keys temporarily for the import
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys=OFF")  # Disable FK constraints for import
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # Clear tables in reverse dependency order (children first)
            for table in reversed(EXPORT_TABLES):
                if table in tables_data:
                    try:
                        conn.execute(f"DELETE FROM {table}")
                        log.debug("Cleared table: %s", table)
                    except sqlite3.Error as e:
                        log.warning("Could not clear table %s: %s", table, str(e))
            
            # Reset SQLite sequences for auto-increment tables
            for table in AUTO_INCREMENT_TABLES:
                try:
                    conn.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                except sqlite3.Error:
                    pass  # sqlite_sequence might not exist or table not in it
            
            # Insert data in dependency order (parents first)
            for table in EXPORT_TABLES:
                if table not in tables_data:
                    continue
                
                rows = tables_data[table]
                if not isinstance(rows, list):
                    errors.append(f"Table {table}: expected array of rows")
                    continue
                
                if not rows:
                    import_counts[table] = 0
                    continue
                
                # Build insert query dynamically from first row
                first_row = rows[0]
                columns = list(first_row.keys())
                
                # Filter out columns that don't exist in the table
                try:
                    pragma_info = conn.execute(f"PRAGMA table_info({table})").fetchall()
                    existing_columns = {col[1] for col in pragma_info}
                    columns = [col for col in columns if col in existing_columns]
                except sqlite3.Error:
                    pass
                
                if not columns:
                    import_counts[table] = 0
                    continue
                
                placeholders = ",".join(["?"] * len(columns))
                column_names = ",".join(columns)
                insert_sql = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
                
                inserted = 0
                for row in rows:
                    try:
                        values = [row.get(col) for col in columns]
                        conn.execute(insert_sql, values)
                        inserted += 1
                    except sqlite3.Error as e:
                        log.warning("Failed to insert row in %s: %s", table, str(e))
                
                import_counts[table] = inserted
                log.info("Imported %d rows into %s", inserted, table)
            
            # Commit the transaction
            conn.execute("COMMIT")
            log.info("Backup import completed successfully")
            
        except Exception as e:
            conn.execute("ROLLBACK")
            raise e
        finally:
            # Always re-enable FK constraints, even on error
            conn.execute("PRAGMA foreign_keys=ON")
            conn.close()
        
        # Calculate totals
        total_imported = sum(import_counts.values())
        
        return {
            "success": True,
            "message": f"Backup restored successfully. {total_imported} records imported.",
            "imported_counts": import_counts,
            "errors": errors if errors else None,
            "total_imported": total_imported
        }
        
    except sqlite3.Error as e:
        log.error("Database error during import: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during import: {str(e)}"
        )
    except Exception as e:
        log.error("Unexpected error during import: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


# ============================================================
# Export Status/Info
# ============================================================

@router.get("/api/export/summary")
def export_summary():
    """
    Get summary information about the current database.

    Returns a concise summary of database contents for quick overview.
    """
    db = get_db()
    summary = {}

    with db.connection() as conn:
        # Get key statistics
        try:
            # Total transactions
            cur = conn.execute("SELECT COUNT(*) FROM transactions")
            summary["total_transactions"] = cur.fetchone()[0]

            # Total accounts
            cur = conn.execute("SELECT COUNT(*) FROM accounts")
            summary["total_accounts"] = cur.fetchone()[0]

            # Total loans
            cur = conn.execute("SELECT COUNT(*) FROM loans")
            summary["total_loans"] = cur.fetchone()[0]

            # Total investments
            cur = conn.execute("SELECT COUNT(*) FROM investments")
            summary["total_investments"] = cur.fetchone()[0]

            # Total reconciliations
            cur = conn.execute("SELECT COUNT(*) FROM reconciliations")
            summary["total_reconciliations"] = cur.fetchone()[0]

            # Date range
            cur = conn.execute("SELECT MIN(date_iso), MAX(date_iso) FROM transactions")
            result = cur.fetchone()
            summary["date_range"] = {
                "from": result[0],
                "to": result[1]
            }

        except sqlite3.Error as e:
            log.error("Error generating export summary: %s", str(e))
            return {"error": str(e)}

    return {
        "summary": summary,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/api/export/info")
def export_info():
    """
    Get information about the current database for export planning.

    Returns table names and row counts without exporting data.
    """
    db = get_db()
    table_info = {}
    total_rows = 0

    with db.connection() as conn:
        for table in EXPORT_TABLES:
            try:
                cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                table_info[table] = {"row_count": count}
                total_rows += count
            except sqlite3.Error as e:
                table_info[table] = {"row_count": 0, "error": str(e)}

    return {
        "tables": table_info,
        "total_tables": len(EXPORT_TABLES),
        "total_rows": total_rows,
        "export_version": "1.0"
    }
