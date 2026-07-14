"""
Migration 008: Standardize Statement Date Fields to ISO Format
==============================================================

Converts all existing statement date fields (payment_due_date, statement_date,
bill_cycle_start, bill_cycle_end) to canonical YYYY-MM-DD ISO format.

Run: cd backend && ./venv/bin/python3 scripts/migration_008_statement_dates.py
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "src" / "data" / "finance.db")


def _normalize_to_iso(date_str: str) -> str:
    """Convert DD/MM/YYYY or DD-MM-YYYY to YYYY-MM-DD."""
    if not date_str:
        return ""
    for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


def run_migration(db_path: str | None = None) -> None:
    """Backfill and standardize all statement date fields to ISO format."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Check which columns exist
    cursor.execute("PRAGMA table_info(statements)")
    columns = {row[1] for row in cursor.fetchall()}

    date_columns = ["payment_due_date", "statement_date", "bill_cycle_start", "bill_cycle_end"]
    existing_date_cols = [col for col in date_columns if col in columns]

    if not existing_date_cols:
        print("[MIGRATION 008] No date columns found in statements table - skipping.")
        conn.close()
        return

    # Build WHERE clause with parentheses for correct OR grouping
    where_parts = [f"({col} IS NOT NULL AND {col} != '')" for col in existing_date_cols]
    where_clause = " OR ".join(where_parts)

    # Fetch all statements with non-null date values
    col_list = ", ".join(existing_date_cols)
    cursor.execute(f"""
        SELECT id, {col_list}
        FROM statements
        WHERE {where_clause}
    """)
    rows = cursor.fetchall()

    updated_count = 0
    for row in rows:
        stmt_id = row[0]
        updates = {}
        for i, col in enumerate(existing_date_cols):
            raw_val = row[i + 1]
            if raw_val:
                normalized = _normalize_to_iso(raw_val)
                # Only update if normalization changed the value
                if normalized != raw_val:
                    updates[col] = normalized

        if updates:
            set_clause = ", ".join(f"{col} = ?" for col in updates)
            values = list(updates.values()) + [stmt_id]
            cursor.execute(f"UPDATE statements SET {set_clause} WHERE id = ?", values)
            updated_count += 1

    conn.commit()
    conn.close()
    print(f"[MIGRATION 008] Standardized {updated_count} statement records to ISO dates.")


if __name__ == "__main__":
    run_migration()