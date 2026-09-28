"""
CAMELOT-BASED TABLE EXTRACTOR
Extracts transaction tables from bank statement PDFs using Camelot 2.0.

Constraints:
- Uses camelot-py only for table extraction
- No regex-based transaction parsing
- No row merging or business logic
- No debit/credit normalization
- Returns raw table data only
"""

import json
import sys
from pathlib import Path
from typing import Any

import camelot
import pdfplumber
from camelot.core import Table


def _table_to_rows(table: Table) -> list[list[str]]:
    """
    Convert a Camelot 2.0 Table to a list-of-lists using the new ``data`` property
    (preferred over ``df.values.tolist()`` because ``data`` is the canonical,
    type-stable representation: 2-D ``list[str]``).
    """
    return [list(row) for row in table.data]


def _table_shape(table: Table) -> tuple[int, int]:
    """Return (rows, cols) using Table.shape when populated, else derive from data."""
    shape = getattr(table, "shape", None)
    if shape and shape != (0, 0):
        return (int(shape[0]), int(shape[1]))
    data = _table_to_rows(table)
    rows = len(data)
    cols = max((len(r) for r in data), default=0)
    return rows, cols


class CamelotExtractor:
    """Extract transaction tables from bank PDFs using Camelot 2.0."""

    # Bank detection keywords (lowercase)
    BANK_KEYWORDS = {
        "HDFC Bank": ["hdfc bank", "hdfc bank limited", "hdfc bank ltd"],
        "ICICI Bank": ["icici bank", "icici bank limited"],
        "Axis Bank": ["axis bank", "axis bank limited"],
        "SBI Card": ["state bank of india", "sbi card", "sbi bank"],
        "IDFC First Bank": ["idfc first bank", "idfc first", "idfc bank"],
        "IndusInd Bank": ["indusind bank", "indusind bank limited"],
    }

    # Minimum thresholds for a valid transaction table
    MIN_ROWS = 5
    MIN_NUMERIC_RATIO = 0.2

    def __init__(self, pdf_path: str, debug: bool = False):
        self.pdf_path = str(pdf_path)
        self.debug = debug

    def _log(self, message: str) -> None:
        if self.debug:
            print(f"[CamelotExtractor] {message}")

    # ========== Bank Detection ==========

    def detect_bank(self) -> str:
        """Detect bank name by scanning first 2 pages with pdfplumber."""
        text = ""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages[:2]:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            self._log(f"pdfplumber error: {e}")
            return "Unknown"

        text_lower = text.lower()
        for bank_name, keywords in self.BANK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return bank_name
        return "Unknown"

    # ========== Table Extraction ==========

    def extract_tables_from_page(self, page_number: int) -> tuple[list[Table], str]:
        """
        Extract tables from a single page.
        Tries lattice first; falls back to stream if no valid tables found.

        Returns: (list_of_camelot_tables, strategy_used)
        """
        # Camelot uses 1-based page numbers
        page_str = str(page_number + 1)

        # Try lattice first (grid-based PDFs like HDFC)
        try:
            tables = camelot.read_pdf(
                self.pdf_path,
                pages=page_str,
                flavor="lattice",
                suppress_stdout=True,
            )
            valid = [t for t in tables if _table_shape(t)[0] >= self.MIN_ROWS]
            if valid:
                self._log(
                    f"Page {page_number}: lattice found {len(tables)} tables, {len(valid)} valid"
                )
                return list(tables), "lattice"
            else:
                self._log(
                    f"Page {page_number}: lattice found {len(tables)} tables but none valid (< {self.MIN_ROWS} rows) → trying stream"
                )
        except Exception as e:
            self._log(f"Page {page_number}: lattice error: {e} → trying stream")

        # Fallback to stream (gridless PDFs like IDFC)
        try:
            tables = camelot.read_pdf(
                self.pdf_path,
                pages=page_str,
                flavor="stream",
                suppress_stdout=True,
            )
            self._log(f"Page {page_number}: stream found {len(tables)} tables")
            return list(tables), "stream"
        except Exception as e:
            self._log(f"Page {page_number}: stream error: {e}")
            return [], "stream"

    # ========== Table Scoring ==========

    def score_table(self, table: Table) -> float:
        """
        Score a camelot table based on:
        - row_count: more rows = better
        - numeric_cell_ratio: fraction of cells containing numeric content
        - date_col_ratio: fraction of rows where first cell starts with a digit
        - confidence: a bonus for high parser confidence (Camelot 2.0)

        Returns a numeric score (higher = better transaction table).
        Returns -1 if table fails minimum thresholds.
        """
        rows = _table_to_rows(table)
        row_count = len(rows)

        if row_count < self.MIN_ROWS:
            return -1.0

        total_cells = 0
        numeric_cells = 0
        date_start_rows = 0

        for row in rows:
            for j, cell in enumerate(row):
                cell_str = str(cell).strip()
                total_cells += 1
                if any(c.isdigit() for c in cell_str):
                    numeric_cells += 1
                if j == 0 and cell_str and cell_str[0].isdigit():
                    date_start_rows += 1

        if total_cells == 0:
            return -1.0

        numeric_ratio = numeric_cells / total_cells
        date_col_ratio = date_start_rows / row_count

        if numeric_ratio < self.MIN_NUMERIC_RATIO:
            return -1.0

        # Camelot 2.0 exposes a unified confidence score in [0.0, 1.0].
        # Boost scoring for high-confidence parses; missing value defaults to 0.
        confidence: float = 0.0
        parsing_report = getattr(table, "parsing_report", None)
        if isinstance(parsing_report, dict):
            raw_acc = parsing_report.get("accuracy", 0)
            try:
                confidence = float(raw_acc) / 100.0
            except (TypeError, ValueError):
                confidence = 0.0
        if not confidence:
            accuracy = getattr(table, "accuracy", 0.0)
            try:
                confidence = float(accuracy) / 100.0
            except (TypeError, ValueError):
                confidence = 0.0

        score = (
            row_count * 0.4
            + numeric_ratio * 30.0
            + date_col_ratio * 20.0
            + confidence * 5.0
        )

        return round(score, 3)

    # ========== Best Table Selection ==========

    def extract_best_table(self) -> dict[str, Any]:
        """
        Scan pages 0-4, score all candidate tables, return the best one.

        Returns:
        {
            "bank": str,
            "page": int,
            "strategy": str,
            "table_shape": [rows, cols],
            "score": float,
            "data": list_of_lists
        }
        """
        bank = self.detect_bank()
        self._log(f"Detected bank: {bank}")

        best_score = -1.0
        best_result: dict[str, Any] | None = None

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
        except Exception:
            total_pages = 5

        pages_to_check = min(total_pages, 5)

        for page_num in range(pages_to_check):
            self._log(f"--- Checking page {page_num} ---")
            tables, strategy = self.extract_tables_from_page(page_num)

            self._log(f"  Strategy: {strategy}, Tables found: {len(tables)}")

            for i, table in enumerate(tables):
                score = self.score_table(table)
                rows, cols = _table_shape(table)
                self._log(f"  Table {i}: shape=({rows},{cols}), score={score}")

                if score > best_score:
                    best_score = score
                    best_result = {
                        "bank": bank,
                        "page": page_num,
                        "strategy": strategy,
                        "table_shape": [rows, cols],
                        "score": score,
                        "data": _table_to_rows(table),
                    }

        if best_result is None:
            self._log("No valid table found across all pages")
            return {
                "bank": bank,
                "page": None,
                "strategy": None,
                "table_shape": None,
                "score": -1,
                "data": [],
            }

        self._log(
            f"Best table: page={best_result['page']}, "
            f"strategy={best_result['strategy']}, "
            f"shape={best_result['table_shape']}, "
            f"score={best_result['score']}"
        )
        return best_result


# ========== CLI Entry Point ==========


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python camelot_extractor.py <pdf_path> [--debug]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    debug = "--debug" in sys.argv

    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    extractor = CamelotExtractor(pdf_path, debug=debug)
    result = extractor.extract_best_table()

    output = {
        "bank": result["bank"],
        "page": result["page"],
        "strategy": result["strategy"],
        "table_shape": result["table_shape"],
        "score": result["score"],
        "data_preview": result["data"][:5] if result["data"] else [],
        "total_rows": len(result["data"]),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
