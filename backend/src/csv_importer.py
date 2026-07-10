"""
csv_importer.py
===============
Import transactions from CSV and Excel files with varying header structures.

Supports:
  - CSV files (.csv)
  - Excel files (.xlsx, .xls)
  - Auto-detection of column mappings
  - Multiple date formats
  - Indian number format (commas, ₹, Rs)
  - Separate debit/credit columns or unified amount column

Usage:
    from csv_importer import CSVImporter

    importer = CSVImporter("transactions.csv")
    detected = importer.detect_format()
    print(detected)

    transactions = importer.import_transactions(mapping, member="Self")
    # Then save to db with db.insert_csv_transactions(transactions, member="Self")

CLI:
    python csv_importer.py <file_path> [--debug]
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas openpyxl")
    sys.exit(1)


# ============================================================
# Date Format Detection
# ============================================================

DATE_FORMATS = [
    # Indian formats (most common)
    "%d/%m/%Y",  # 01/06/2025
    "%d-%m-%Y",  # 01-06-2025
    "%d/%m/%y",  # 01/06/25
    "%d-%m-%y",  # 01-06-25
    # ISO format
    "%Y-%m-%d",  # 2025-06-01
    # Month name formats
    "%d %b %Y",  # 01 Jun 2025
    "%d %B %Y",  # 01 June 2025
    "%d-%b-%Y",  # 01-Jun-2025
    "%d-%B-%Y",  # 01-June-2025
    "%d %b %y",  # 01 Jun 25
    "%d-%b-%y",  # 01-Jun-25
    # US formats (less common in India)
    "%m/%d/%Y",  # 06/01/2025
    "%m-%d-%Y",  # 06-01-2025
]

# Common column name patterns
DATE_COLUMN_NAMES = [
    "date", "transaction date", "txn date", "posting date", "value date",
    "trans date", "tran date", "dt", "txn_dt", "trans_dt"
]

DESCRIPTION_COLUMN_NAMES = [
    "description", "narration", "particulars", "details", "transaction details",
    "merchant", "merchant name", "trans details", "txn details", "narration",
    "reference", "ref", "remarks"
]

AMOUNT_COLUMN_NAMES = [
    "amount", "transaction amount", "txn amount", "trans amount", "amt",
    "debit amount", "credit amount", "withdrawal", "deposit"
]

TYPE_COLUMN_NAMES = [
    "type", "dr/cr", "transaction type", "txn type", "trans type", "d/c",
    "debit/credit", "cr/dr"
]

DEBIT_COLUMN_NAMES = [
    "debit", "dr", "withdrawal", "withdrawal amt", "debit amount", "dr amt",
    "outflow", "paid out"
]

CREDIT_COLUMN_NAMES = [
    "credit", "cr", "deposit", "deposit amt", "credit amount", "cr amt",
    "inflow", "paid in", "received"
]


# ============================================================
# CSVImporter Class
# ============================================================

class CSVImporter:
    """
    Import transactions from CSV and Excel files.

    Usage:
        importer = CSVImporter("transactions.csv")
        detected = importer.detect_format()
        transactions = importer.import_transactions(mapping, member="Self")
    """

    def __init__(self, file_path: str, debug: bool = False):
        self.file_path = Path(file_path)
        self.debug = debug
        self._df: pd.DataFrame | None = None
        self._detected_format: dict[str, Any] | None = None

    def _read_file(self, skip_rows: int = 0) -> pd.DataFrame:
        """Read the file into a pandas DataFrame."""
        suffix = self.file_path.suffix.lower()

        if suffix == ".csv":
            # Try different encodings for CSV
            for encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                try:
                    df = pd.read_csv(self.file_path, skiprows=skip_rows, encoding=encoding)
                    if self.debug:
                        print(f"Read CSV with encoding: {encoding}")
                    return df
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Could not read CSV file with any encoding: {self.file_path}")

        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(self.file_path, skiprows=skip_rows)
            if self.debug:
                print(f"Read Excel file: {self.file_path}")
            return df

        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _detect_skip_rows(self, df: pd.DataFrame) -> int:
        """Detect how many rows to skip before the header."""
        # Check if first row looks like headers
        if df.empty:
            return 0

        first_row = df.iloc[0]
        # Headers typically have string values
        string_count = sum(1 for v in first_row if isinstance(v, str) and v)

        if string_count >= len(first_row) * 0.5:
            return 0  # First row looks like headers

        # Try reading with skiprows
        for skip in range(1, 10):
            try:
                test_df = self._read_file(skip)
                if not test_df.empty:
                    first_row = test_df.iloc[0]
                    string_count = sum(1 for v in first_row if isinstance(v, str) and v)
                    if string_count >= len(first_row) * 0.5:
                        return skip
            except Exception:
                continue

        return 0

    def _find_column_by_names(self, columns: list[str], names: list[str]) -> str | None:
        """Find a column by matching against common names."""
        columns_lower = [c.lower().strip() for c in columns]
        for name in names:
            if name.lower() in columns_lower:
                idx = columns_lower.index(name.lower())
                return columns[idx]
            # Partial match
            for i, col in enumerate(columns_lower):
                if name.lower() in col or col in name.lower():
                    return columns[i]
        return None

    def _is_date_value(self, value: Any) -> bool:
        """Check if a value looks like a date."""
        if pd.isna(value):
            return False

        value_str = str(value).strip()
        if not value_str:
            return False

        # Try parsing with known formats
        for fmt in DATE_FORMATS:
            try:
                datetime.strptime(value_str, fmt)
                return True
            except ValueError:
                continue

        # Check for date-like patterns
        date_patterns = [
            r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$",  # DD/MM/YYYY or DD-MM-YY
            r"^\d{4}[/-]\d{1,2}[/-]\d{1,2}$",  # YYYY-MM-DD
            r"^\d{1,2}\s+\w{3,9}\s+\d{2,4}$",  # DD Mon YYYY
        ]
        for pattern in date_patterns:
            if re.match(pattern, value_str):
                return True

        return False

    def _is_numeric_value(self, value: Any) -> bool:
        """Check if a value is numeric (after cleaning)."""
        if pd.isna(value):
            return False

        # Already a number
        if isinstance(value, (int, float)):
            return True

        value_str = str(value).strip()
        if not value_str:
            return False

        # Clean the value
        cleaned = value_str.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("INR", "").strip()

        try:
            float(cleaned)
            return True
        except ValueError:
            return False

    def _parse_amount(self, value: Any) -> float | None:
        """Parse an amount value to float."""
        if pd.isna(value):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        value_str = str(value).strip()
        if not value_str:
            return None

        # Clean the value
        cleaned = value_str.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("INR", "").strip()

        # Handle negative values in parentheses (accounting format)
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]

        try:
            return float(cleaned)
        except ValueError:
            return None

    def _detect_date_column(self, df: pd.DataFrame) -> str | None:
        """Detect which column contains dates."""
        columns = df.columns.tolist()

        # First, try matching by column name
        date_col = self._find_column_by_names(columns, DATE_COLUMN_NAMES)
        if date_col:
            return date_col

        # Then, try detecting by content
        for col in columns:
            values = df[col].dropna().head(20)
            if len(values) == 0:
                continue

            date_count = sum(1 for v in values if self._is_date_value(v))
            if date_count / len(values) > 0.5:
                return str(col)

        return None

    def _detect_description_column(self, df: pd.DataFrame, exclude_cols: list[str]) -> str | None:
        """Detect which column contains descriptions."""
        columns = [c for c in df.columns.tolist() if c not in exclude_cols]

        # First, try matching by column name
        desc_col = self._find_column_by_names(columns, DESCRIPTION_COLUMN_NAMES)
        if desc_col:
            return desc_col

        # Then, find column with longest average string length
        best_col = None
        best_avg_len = 0.0

        for col in columns:
            values = df[col].dropna().head(20)
            if len(values) == 0:
                continue

            # Skip numeric columns
            numeric_count = sum(1 for v in values if self._is_numeric_value(v))
            if numeric_count / len(values) > 0.5:
                continue

            # Calculate average string length
            avg_len = sum(len(str(v)) for v in values) / len(values)
            if avg_len > best_avg_len:
                best_avg_len = avg_len
                best_col = col

        return str(best_col) if best_col else None

    def _detect_amount_column(self, df: pd.DataFrame, exclude_cols: list[str]) -> str | None:
        """Detect which column contains amounts."""
        columns = [c for c in df.columns.tolist() if c not in exclude_cols]

        # First, try matching by column name
        amount_col = self._find_column_by_names(columns, AMOUNT_COLUMN_NAMES)
        if amount_col:
            return amount_col

        # Then, find column with most numeric values
        for col in columns:
            values = df[col].dropna().head(20)
            if len(values) == 0:
                continue

            numeric_count = sum(1 for v in values if self._is_numeric_value(v))
            if numeric_count / len(values) > 0.5:
                return str(col)

        return None

    def _detect_type_column(self, df: pd.DataFrame, exclude_cols: list[str]) -> str | None:
        """Detect which column contains transaction type (DR/CR)."""
        columns = [c for c in df.columns.tolist() if c not in exclude_cols]

        # First, try matching by column name
        type_col = self._find_column_by_names(columns, TYPE_COLUMN_NAMES)
        if type_col:
            return type_col

        # Then, find column with DR/CR values
        type_values = {"dr", "cr", "debit", "credit", "d", "c", "w"}

        for col in columns:
            values = df[col].dropna().head(20)
            if len(values) == 0:
                continue

            # Check if values are type indicators
            type_count = sum(1 for v in values if str(v).lower().strip() in type_values)
            if type_count / len(values) > 0.5:
                return str(col)

        return None

    def _detect_debit_credit_columns(self, df: pd.DataFrame, exclude_cols: list[str]) -> tuple[str | None, str | None]:
        """Detect separate debit and credit columns.

        Only returns columns if BOTH debit and credit columns exist and are DIFFERENT.
        This prevents false positives when there's a unified amount column with a type column.
        """
        columns = [c for c in df.columns.tolist() if c not in exclude_cols]

        debit_col = self._find_column_by_names(columns, DEBIT_COLUMN_NAMES)
        credit_col = self._find_column_by_names(columns, CREDIT_COLUMN_NAMES)

        # Only return if both exist and are different columns
        if debit_col and credit_col and debit_col != credit_col:
            return debit_col, credit_col

        return None, None

    def _detect_date_format(self, df: pd.DataFrame, date_col: str) -> str:
        """Detect the date format used in the date column."""
        values = df[date_col].dropna().head(20)

        for fmt in DATE_FORMATS:
            matches = 0
            for v in values:
                try:
                    datetime.strptime(str(v).strip(), fmt)
                    matches += 1
                except ValueError:
                    continue

            if matches / len(values) > 0.5:
                return fmt

        # Default to Indian format
        return "%d/%m/%Y"

    def detect_format(self) -> dict[str, Any]:
        """
        Auto-detect file structure.

        Returns:
            dict with:
                - columns: list[Any] of column names
                - row_count: number of data rows
                - sample_rows: first 5 rows as list of dicts
                - detected_mapping: best guess for column mapping
                - date_format: detected date format
                - skip_rows: number of header rows to skip
        """
        # Initial read to detect skip rows
        df_initial = self._read_file()
        skip_rows = self._detect_skip_rows(df_initial)

        # Read with correct skip rows
        if skip_rows > 0:
            df = self._read_file(skip_rows)
        else:
            df = df_initial

        self._df = df

        if self.debug:
            print(f"Columns: {df.columns.tolist()}")
            print(f"Shape: {df.shape}")
            print(f"Skip rows: {skip_rows}")

        # Detect columns
        date_col = self._detect_date_column(df)
        exclude_cols = [date_col] if date_col else []

        desc_col = self._detect_description_column(df, exclude_cols)
        if desc_col:
            exclude_cols.append(desc_col)

        amount_col = self._detect_amount_column(df, exclude_cols)
        if amount_col:
            exclude_cols.append(amount_col)

        type_col = self._detect_type_column(df, exclude_cols)

        # Check for separate debit/credit columns
        # Only detect if there's NO type column (unified amount + type is preferred)
        if not type_col:
            debit_col, credit_col = self._detect_debit_credit_columns(df, [])
        else:
            debit_col, credit_col = None, None

        # If no unified amount column but have debit/credit columns
        if not amount_col and (debit_col or credit_col):
            amount_col = debit_col or credit_col  # Use one of them as reference

        # Detect date format
        date_format = "%d/%m/%Y"
        if date_col:
            date_format = self._detect_date_format(df, date_col)

        # Build sample rows
        sample_rows = []
        for _, row in df.head(5).iterrows():
            sample_rows.append({col: str(row.get(col, ""))[:50] for col in df.columns})

        result = {
            "columns": df.columns.tolist(),
            "row_count": len(df),
            "sample_rows": sample_rows,
            "detected_mapping": {
                "date_column": date_col,
                "description_column": desc_col,
                "amount_column": amount_col,
                "type_column": type_col,
                "debit_column": debit_col,
                "credit_column": credit_col,
            },
            "date_format": date_format,
            "skip_rows": skip_rows,
        }

        self._detected_format = result
        return result

    def import_transactions(
        self,
        mapping: dict[str, Any],
        member: str = "Self",
        bank: str = "Manual Import",
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Import transactions using the provided column mapping.

        Args:
            mapping: dict[str, Any] with:
                - date_column: str
                - description_column: str
                - amount_column: str (optional if debit/credit columns)
                - type_column: str or None
                - debit_column: str or None
                - credit_column: str or None
                - date_format: str
                - skip_rows: int
                - bank: str (optional, default from arg)
            member: family member name
            bank: bank name for the import

        Returns:
            Tuple of (transactions list, warnings list)
        """
        if self._df is None:
            skip_rows = mapping.get("skip_rows", 0)
            self._df = self._read_file(skip_rows)

        df = self._df
        transactions = []
        warnings = []

        date_col = mapping.get("date_column")
        desc_col = mapping.get("description_column")
        amount_col = mapping.get("amount_column")
        type_col = mapping.get("type_column")
        debit_col = mapping.get("debit_column")
        credit_col = mapping.get("credit_column")
        date_format = mapping.get("date_format", "%d/%m/%Y")

        if not date_col:
            warnings.append("No date column specified")
            return [], warnings

        if not desc_col:
            warnings.append("No description column specified")
            return [], warnings

        # Import categorizer
        from src.categorizer import categorize

        for idx, row in df.iterrows():
            try:
                # Parse date
                date_val = row.get(date_col)
                if pd.isna(date_val):
                    warnings.append(f"Row {idx}: Empty date, skipping")
                    continue

                date_str = str(date_val).strip()
                try:
                    parsed_date = datetime.strptime(date_str, date_format)
                    formatted_date = parsed_date.strftime("%d/%m/%Y")
                except ValueError:
                    warnings.append(f"Row {idx}: Could not parse date '{date_str}', skipping")
                    continue

                # Get description
                desc_val = row.get(desc_col)
                if pd.isna(desc_val):
                    desc_val = ""
                description = str(desc_val).strip()

                # Determine amount and type
                amount = None
                txn_type = ""

                # Case 1: Separate debit/credit columns
                if debit_col or credit_col:
                    debit_amt = self._parse_amount(row.get(debit_col)) if debit_col else None
                    credit_amt = self._parse_amount(row.get(credit_col)) if credit_col else None

                    if debit_amt and debit_amt > 0:
                        amount = debit_amt
                        txn_type = "debit"
                    elif credit_amt and credit_amt > 0:
                        amount = credit_amt
                        txn_type = "credit"
                    else:
                        warnings.append(f"Row {idx}: No valid amount in debit/credit columns, skipping")
                        continue

                # Case 2: Unified amount column
                elif amount_col:
                    amount = self._parse_amount(row.get(amount_col))
                    if amount is None:
                        warnings.append(f"Row {idx}: Could not parse amount, skipping")
                        continue

                    # Determine type from type column or amount sign
                    if type_col:
                        type_val = str(row.get(type_col, "")).lower().strip()
                        if type_val in ["dr", "debit", "d", "w"]:
                            txn_type = "debit"
                            amount = abs(amount)
                        elif type_val in ["cr", "credit", "c"]:
                            txn_type = "credit"
                            amount = abs(amount)
                        else:
                            # Default based on sign
                            txn_type = "debit" if amount > 0 else "credit"
                            amount = abs(amount)
                    else:
                        # Use sign: positive = debit, negative = credit
                        if amount < 0:
                            txn_type = "credit"
                            amount = abs(amount)
                        else:
                            txn_type = "debit"

                else:
                    warnings.append(f"Row {idx}: No amount column specified, skipping")
                    continue

                # Skip zero amounts
                if amount == 0:
                    continue

                # Categorize
                category, subcategory = categorize(description, amount)

                transactions.append({
                    "date": formatted_date,
                    "description": description,
                    "original_description": description,
                    "amount_paise": int(round(amount * 100)),
                    "type": txn_type,
                    "category": category,
                    "subcategory": subcategory,
                })

            except Exception as e:
                warnings.append(f"Row {idx}: Error processing - {str(e)}")

        if self.debug:
            print(f"Imported {len(transactions)} transactions")
            if warnings:
                print(f"Warnings ({len(warnings)}):")
                for w in warnings[:10]:
                    print(f"  - {w}")

        return transactions, warnings


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import transactions from CSV/Excel files")
    parser.add_argument("file_path", help="Path to CSV or Excel file")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    importer = CSVImporter(args.file_path, debug=args.debug)

    print(f"\n{'='*60}")
    print(f"File: {args.file_path}")
    print(f"{'='*60}\n")

    detected = importer.detect_format()

    print("Detected Format:")
    print(f"  Columns: {detected['columns']}")
    print(f"  Row count: {detected['row_count']}")
    print(f"  Skip rows: {detected['skip_rows']}")
    print(f"  Date format: {detected['date_format']}")

    print("\nDetected Mapping:")
    mapping = detected["detected_mapping"]
    print(f"  Date column: {mapping['date_column']}")
    print(f"  Description column: {mapping['description_column']}")
    print(f"  Amount column: {mapping['amount_column']}")
    print(f"  Type column: {mapping['type_column']}")
    print(f"  Debit column: {mapping['debit_column']}")
    print(f"  Credit column: {mapping['credit_column']}")

    print("\nSample Rows:")
    for i, row in enumerate(detected["sample_rows"]):
        print(f"  Row {i+1}: {row}")

    # Try importing with detected mapping
    print("\n" + "="*60)
    print("Testing Import with Detected Mapping")
    print("="*60 + "\n")

    full_mapping = {
        **mapping,
        "date_format": detected["date_format"],
        "skip_rows": detected["skip_rows"],
    }

    transactions, warnings = importer.import_transactions(full_mapping)

    print(f"Imported: {len(transactions)} transactions")
    if warnings:
        print(f"Warnings: {len(warnings)}")

    if transactions:
        print("\nFirst 5 transactions:")
        for txn in transactions[:5]:
            amount_rupees = txn.get('amount_paise', 0) / 100.0
            print(f"  {txn['date']} | {txn['description'][:30]:<30} | ₹{amount_rupees:>10,.2f} | {txn['type']} | {txn['category']}")
