"""
statement_extractor.py
======================
Production-grade single-file extractor for Indian credit card statements.

Supports: HDFC, ICICI, Axis, SBI, IDFC First, IndusInd

Pipeline:
  1. detect_bank()               — pdfplumber keyword scan
  2. extract_tables_from_page()  — Camelot lattice → stream fallback
  3. score_table()               — row/numeric/date/consistency scoring
  4. select_best_table()         — scan pages 0-5, pick highest score
  5. clean_rows()                — strip, remove empty/header rows
  6. merge_multiline_rows()      — group continuation rows
  7. normalize_transactions()    — build structured dicts
  8. extract()                   — full pipeline → JSON dict

CLI:
  python statement_extractor.py <pdf_path> [--debug]
"""

import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import camelot
import pdfplumber

# ============================================================
# Constants
# ============================================================

BANK_KEYWORDS: dict[str, list[str]] = {
    "HDFC Bank":       ["HDFC Bank", "HDFC BANK"],
    "ICICI Bank":      ["ICICI Bank", "ICICI BANK"],
    "Axis Bank":       ["Axis Bank", "AXIS BANK"],
    "SBI Card":        ["State Bank of India", "SBI Card", "SBICARD"],
    "IDFC First Bank": ["IDFC FIRST Bank", "IDFC First Bank", "IDFC FIRST BANK"],
    "IndusInd Bank":   ["IndusInd Bank", "INDUSIND BANK"],
}

SCORE_THRESHOLD = 25.0
MAX_PAGES_TO_SCAN = 6

# Header row keywords — multi-word phrases that only appear in header rows
HEADER_PHRASES = [
    "transaction date", "transaction description", "amount (in rs.)",
    "amount (rs.)", "neucoins*", "base neucoins", "emi eligibility",
    "fx transactions", "particulars", "narration", "withdrawal (dr.)",
    "deposit (cr.)", "txn date", "txn amount", "value date",
    "chq./ref.no.", "chq/ref number", "loan on card",
    "merchant category", "cashback earned",
    # Additional phrases (Indian bank statements)
    "posting date", "transaction details", "billing date", "ref no",
    "reference number", "reward points", "sr no", "sl no", "serial no",
    "domestic transactions", "international transactions", "retail transactions",
    "date of transaction", "amount in inr", "amount (inr)",
]


# ============================================================
# Custom Exception
# ============================================================

class ExtractionError(Exception):
    pass


# ============================================================
# Utility Functions
# ============================================================

def _cell_str(cell: Any) -> str:
    """Safely convert a cell value to stripped string."""
    return str(cell).strip() if cell is not None else ""


def _is_empty_row(row: list[str]) -> bool:
    return all(c == "" for c in row)


def _is_header_row(row: list[str]) -> bool:
    row_text = " ".join(c.lower() for c in row)
    return any(phrase in row_text for phrase in HEADER_PHRASES)


# Compiled date regex patterns (Fix 1: strict anchored patterns, no false positives)
_DATE_PATTERNS = re.compile(
    r"""^(?:
        \d{1,2}/\d{1,2}/(?:\d{4}|\d{2})   |  # DD/MM/YYYY or DD/MM/YY
        \d{1,2}-\d{1,2}-(?:\d{4}|\d{2})   |  # DD-MM-YYYY or DD-MM-YY
        \d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(?:\d{4}|\d{2})  |  # DD Mon YYYY/YY
        \d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(?:\d{4}|\d{2})       # DD-Mon-YYYY/YY
    )$""",
    re.IGNORECASE | re.VERBOSE,
)


def _cell_has_date(cell: str) -> bool:
    """
    Returns True if cell strictly matches an Indian statement date format:
      - DD/MM/YYYY or DD/MM/YY
      - DD-MM-YYYY or DD-MM-YY
      - DD Mon YYYY or DD Mon YY  (e.g., 15 Jun 2025)
      - DD-Mon-YYYY or DD-Mon-YY  (e.g., 15-Jun-2025)
    Uses anchored regex to avoid false positives on ref numbers, card numbers, etc.
    """
    s = cell.strip()
    if not s or not s[0].isdigit():
        return False
    return bool(_DATE_PATTERNS.match(s))


def _cell_has_digits(cell: str) -> bool:
    return any(ch.isdigit() for ch in cell)


# Compiled DR/CR pattern (Fix 2: word boundary — avoids matching ALEXANDR, SUCRE)
_DR_CR_PATTERN = re.compile(r'^(.*?)\s+(DR|CR|Dr|Cr)\s*$', re.DOTALL)


def _split_dr_cr(amount: str) -> tuple[str, str]:
    """
    Split "1,234.56 DR" → ("1,234.56", "debit")
    Split "500.00 CR"   → ("500.00", "credit")
    DR/CR must be a separate whitespace-delimited token at the end.
    Returns (amount, "") if no indicator.
    """
    s = amount.strip()
    m = _DR_CR_PATTERN.match(s)
    if m:
        val = m.group(1).strip()
        indicator = m.group(2).upper()
        txn_type = "debit" if indicator == "DR" else "credit"
        return val, txn_type
    return s, ""


def _parse_amount_paise(amount_str) -> int:
    """
    Parse amount to integer paise (1 rupee = 100 paise).
    Raises ValueError on invalid input (no silent failures).

    Accepts:
        - String amounts: "Rs 1,234.56", "₹1234.56", "1234"
        - Numeric amounts: 1234, 1234.56, 1234.0

    Examples:
        "Rs 1,234.56" -> 123456
        "₹1234.56"    -> 123456
        "1234"        -> 123400
        1234          -> 123400
        1234.56       -> 123456
    """
    # Convert to string if numeric
    if isinstance(amount_str, (int, float)):
        # For integers, treat as rupees
        if isinstance(amount_str, int):
            return amount_str * 100
        # For floats, use Decimal to avoid precision loss
        paise = Decimal(str(amount_str)) * Decimal('100')
        return int(paise.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    # Handle string input
    cleaned = (str(amount_str)
               .replace("Rs", "")
               .replace("₹", "")
               .replace(",", "")
               .strip())

    if not cleaned:
        raise ValueError(f"Empty amount string: {amount_str!r}")

    try:
        rupees = Decimal(cleaned)
        # Financial Standard: Use quantization to guarantee safe integer conversion
        paise = (rupees * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return int(paise)
    except (ValueError, InvalidOperation) as e:
        raise ValueError(f"Invalid amount format '{amount_str}': {e}") from e


# ============================================================
# StatementExtractor
# ============================================================

class StatementExtractor:
    """
    Unified Camelot-based extractor for Indian credit card statements.
    No LayoutAnalyzer. No manual bounding boxes. Score-based table selection.
    """

    def __init__(self, pdf_path: str, debug: bool = False):
        self.pdf_path = str(pdf_path)
        self.debug = debug
        self._bank: str | None = None
        self._num_pages: int = 0
        self._best_page: int | None = None
        self._best_strategy: str | None = None
        self._best_score: float = 0.0
        self._date_col_idx: int = 0   # detected date column index
        self._desc_col_idx: int = 1   # detected description column index
        self._amount_col_idx: int | None = None   # Fix 2B: single amount col
        self._debit_col_idx: int | None = None    # Fix 2B: debit col (separate)
        self._credit_col_idx: int | None = None   # Fix 2B: credit col (separate)
        self._header_row: list[str] | None = None  # Fix 9: captured header row

    def _log(self, msg: str) -> None:
        if self.debug:
            print(f"[StatementExtractor] {msg}")

    # ----------------------------------------------------------
    # Step 1: Bank Detection
    # ----------------------------------------------------------

    def detect_bank(self) -> str:
        """Scan first 2 pages for bank name keywords."""
        text = ""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self._num_pages = len(pdf.pages)
                for page in pdf.pages[:2]:
                    t = page.extract_text() or ""
                    text += t + "\n"
        except Exception as e:
            self._log(f"Bank detection error: {e}")
            return "Unknown"

        for bank_name, keywords in BANK_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    self._log(f"Bank detected: {bank_name} (keyword: {kw!r})")
                    self._bank = bank_name
                    return bank_name

        self._log("Bank not detected → Unknown")
        self._bank = "Unknown"
        return "Unknown"

    # ----------------------------------------------------------
    # Step 2: Extract Tables from Page
    # ----------------------------------------------------------

    def extract_tables_from_page(self, page_number: int) -> list[dict]:
        """
        Extract all tables from a single page using Camelot.
        Fix 15: Try lattice first. If lattice returns a usable table (>=3 cols, >=5 rows),
        skip stream to avoid spawning a second Ghostscript process.
        Returns list of dicts: {table, strategy, page}.
        """
        results = []
        page_str = str(page_number + 1)  # Camelot is 1-based

        # Try lattice first
        lattice_usable = False
        try:
            tables = camelot.read_pdf(
                self.pdf_path,
                pages=page_str,
                flavor="lattice",
                split_text=True,
                strip_text="\n",
                suppress_stdout=True,
            )
            if tables and len(tables) > 0:
                self._log(f"  Page {page_number}: lattice → {len(tables)} table(s)")
                for t in tables:
                    results.append({"table": t, "strategy": "lattice", "page": page_number})
                # Fix 15: Skip stream only if lattice has >=3 cols, >=5 rows AND has dates
                for t in tables:
                    rows = t.df.values.tolist()
                    if len(rows) >= 5 and len(rows[0]) >= 3:
                        date_count = sum(
                            1 for row in rows
                            if any(_cell_has_date(_cell_str(c)) for c in row)
                        )
                        if date_count >= 1:
                            lattice_usable = True
                            break
        except Exception as e:
            self._log(f"  Page {page_number}: lattice failed: {e}")

        # Only run stream if lattice didn't yield a usable table
        if not lattice_usable:
            try:
                tables = camelot.read_pdf(
                    self.pdf_path,
                    pages=page_str,
                    flavor="stream",
                    split_text=True,
                    strip_text="\n",
                    suppress_stdout=True,
                )
                if tables and len(tables) > 0:
                    self._log(f"  Page {page_number}: stream → {len(tables)} table(s)")
                    for t in tables:
                        results.append({"table": t, "strategy": "stream", "page": page_number})
            except Exception as e:
                self._log(f"  Page {page_number}: stream failed: {e}")

        if not results:
            self._log(f"  Page {page_number}: no tables found")

        return results

    # ----------------------------------------------------------
    # Step 3: Score Table
    # ----------------------------------------------------------

    def score_table(self, table_entry: dict[str, Any]) -> float:
        """
        Score a table candidate to determine if it's the transaction table.

        Scoring components:
          row_score        = min(row_count, 100) * 1.5
          numeric_score    = (cells_with_digits / total_cells) * 20
          date_score       = (rows_with_date_in_any_col / row_count) * 30
          consistency_score = (avg_non_empty_cells / col_count) * 10

        Returns 0.0 if table is too small.
        """
        table = table_entry["table"]
        rows = table.df.values.tolist()

        row_count = len(rows)
        col_count = len(rows[0]) if rows else 0

        # Hard reject
        if row_count < 2 or col_count < 2:
            return 0.0

        # Fix 7: Rebalanced weights — row_score capped lower so date_score dominates
        row_score = min(row_count, 60) * 0.5          # max 30 (was 150)

        # numeric_score
        total_cells = row_count * col_count
        cells_with_digits = sum(
            1 for row in rows for cell in row if _cell_has_digits(_cell_str(cell))
        )
        numeric_ratio = cells_with_digits / total_cells if total_cells > 0 else 0
        numeric_score = numeric_ratio * 25             # max 25 (was 20)

        # date_score — check ALL columns for date pattern
        date_rows = 0
        for row in rows:
            for cell in row:
                if _cell_has_date(_cell_str(cell)):
                    date_rows += 1
                    break
        # Fix 8: Require >= 1 date row (was 2) and >= 3% density (was 5%)
        date_ratio = date_rows / row_count if row_count > 0 else 0
        if date_rows < 1 or date_ratio < 0.03:
            return 0.0
        date_score = date_ratio * 40                   # max 40 (was 30)

        # consistency_score
        non_empty_per_row = [
            sum(1 for cell in row if _cell_str(cell)) for row in rows
        ]
        avg_non_empty = sum(non_empty_per_row) / row_count if row_count > 0 else 0
        fill_ratio = avg_non_empty / col_count if col_count > 0 else 0
        consistency_score = fill_ratio * 15            # max 15 (was 10)

        # Fix 7: Column count bonus/penalty
        if 3 <= col_count <= 7:
            col_bonus = 5
        elif col_count < 3 or col_count > 10:
            col_bonus = -5
        else:
            col_bonus = 0

        total = row_score + numeric_score + date_score + consistency_score + col_bonus

        self._log(
            f"    Score: {total:.1f} "
            f"(rows={row_count}, cols={col_count}, "
            f"row={row_score:.1f}, num={numeric_score:.1f}, "
            f"date={date_score:.1f}, cons={consistency_score:.1f}, col_bonus={col_bonus})"
        )

        return total

    # ----------------------------------------------------------
    # Step 4: Select Best Table
    # ----------------------------------------------------------

    def select_best_table(self) -> dict[str, Any]:
        """
        Scan first MAX_PAGES_TO_SCAN pages.
        Score all tables. Return the highest-scoring one.
        Raises ExtractionError if no table scores above threshold.
        """
        if self._num_pages == 0:
            with pdfplumber.open(self.pdf_path) as pdf:
                self._num_pages = len(pdf.pages)

        pages_to_scan = min(MAX_PAGES_TO_SCAN, self._num_pages)
        best_entry = None
        best_score = 0.0

        for page_num in range(pages_to_scan):
            self._log(f"Scanning page {page_num}...")
            candidates = self.extract_tables_from_page(page_num)
            for entry in candidates:
                score = self.score_table(entry)
                if score > best_score:
                    best_score = score
                    best_entry = entry

        if best_entry is None or best_score < SCORE_THRESHOLD:
            raise ExtractionError(
                f"No transaction table found (best score: {best_score:.1f}, "
                f"threshold: {SCORE_THRESHOLD})"
            )

        self._best_page = best_entry["page"]
        self._best_strategy = best_entry["strategy"]
        self._best_score = best_score

        self._log(
            f"Best table: page={self._best_page}, "
            f"strategy={self._best_strategy}, score={best_score:.1f}"
        )

        return best_entry

    # ----------------------------------------------------------
    # Step 5: Clean Rows + Header Capture
    # ----------------------------------------------------------

    def _extract_header_row(self, rows: list[list]) -> list[str] | None:
        """
        Fix 9: Scan first 5 rows for the one that best matches HEADER_PHRASES.
        Returns the header row as a list of strings, or None if not found.
        Stores result in self._header_row for use by column detection methods.
        """
        for raw_row in rows[:5]:
            row = [_cell_str(cell) for cell in raw_row]
            if _is_header_row(row):
                self._header_row = row
                self._log(f"Header row captured: {row}")
                return row
        return None

    def clean_rows(self, rows: list[list]) -> list[list[str]]:
        """
        Convert raw Camelot rows to clean string lists.
        Remove: fully empty rows, header rows.
        Trim whitespace from each cell.
        Fix 9: Captures header row before stripping it.
        """
        # Capture header before stripping
        self._extract_header_row(rows)

        cleaned = []
        for raw_row in rows:
            row = [_cell_str(cell) for cell in raw_row]
            if _is_empty_row(row):
                continue
            if _is_header_row(row):
                continue
            cleaned.append(row)
        return cleaned

    # ----------------------------------------------------------
    # Step 6: Detect Date Column + Description Column + Amount Columns
    # ----------------------------------------------------------

    def _detect_date_column(self, rows: list[list[str]]) -> int:
        """
        Find which column index has the highest density of date-like values.
        Returns the column index (default 0).
        """
        if not rows:
            return 0

        col_count = max(len(row) for row in rows)
        date_counts = [0] * col_count

        for row in rows:
            for i, cell in enumerate(row):
                if i < col_count and _cell_has_date(cell):
                    date_counts[i] += 1

        best_idx = date_counts.index(max(date_counts))
        self._log(f"Date column detection: counts={date_counts}, best_idx={best_idx}")
        return best_idx

    def _detect_description_column(self, rows: list[list[str]], date_col_idx: int) -> int:
        """
        Fix 3: Find the description column by scanning the header row first,
        then falling back to the column with the longest average text length
        among non-date, non-numeric columns.
        """
        col_count = max(len(row) for row in rows) if rows else 0
        if col_count == 0:
            return 1 if date_col_idx == 0 else 0

        # Try header row first
        if self._header_row:
            header = [c.lower() for c in self._header_row]
            desc_keywords = ["description", "particulars", "narration",
                             "transaction details", "details", "remarks"]
            for kw in desc_keywords:
                for i, h in enumerate(header):
                    if kw in h and i != date_col_idx:
                        self._log(f"Description column from header: idx={i} ({header[i]!r})")
                        return i

        # Fallback: column with longest average text (excluding date and numeric cols)
        avg_lengths = []
        for col_idx in range(col_count):
            if col_idx == date_col_idx:
                avg_lengths.append(0)
                continue
            texts = [row[col_idx] for row in rows if col_idx < len(row) and row[col_idx]]
            if not texts:
                avg_lengths.append(0)
                continue
            # Penalize columns that are mostly numeric
            numeric_count = sum(1 for t in texts if _cell_has_digits(t) and len(t) < 15)
            if numeric_count / len(texts) > 0.7:
                avg_lengths.append(0)
            else:
                avg_lengths.append(sum(len(t) for t in texts) / len(texts))

        if max(avg_lengths) > 0:
            best = avg_lengths.index(max(avg_lengths))
            self._log(f"Description column from avg length: idx={best}")
            return best

        # Last resort: index 1 if date is 0, else 0
        return 1 if date_col_idx == 0 else 0

    def _detect_amount_columns(self, rows: list[list[str]], date_col_idx: int) -> dict[str, Any]:
        """
        Fix 4: Find amount column(s) by scanning for the rightmost column(s)
        where >50% of cells match a currency/number pattern.
        Returns dict with keys: 'amount_col', 'debit_col', 'credit_col', 'structure'.
        """
        col_count = max(len(row) for row in rows) if rows else 0
        if col_count == 0:
            return {"amount_col": col_count - 1, "debit_col": None,
                    "credit_col": None, "structure": "single_amount"}

        # Currency pattern: digits with optional commas, dots, minus
        _CURRENCY_RE = re.compile(r'^-?[\d,]+\.?\d*$')

        def is_currency(cell: str) -> bool:
            c = cell.strip().replace(" ", "")
            # Remove common suffixes
            for sfx in ("DR", "CR", "Dr", "Cr"):
                if c.upper().endswith(sfx):
                    c = c[:-len(sfx)].strip()
            return bool(_CURRENCY_RE.match(c)) if c else False

        # Count currency cells per column
        currency_counts = [0] * col_count
        total_counts = [0] * col_count
        for row in rows:
            for i, cell in enumerate(row):
                if i < col_count and i != date_col_idx:
                    total_counts[i] += 1
                    if is_currency(_cell_str(cell)):
                        currency_counts[i] += 1

        # Find columns where >50% of cells are currency
        threshold = 0.5
        currency_cols = [
            i for i in range(col_count)
            if total_counts[i] > 0
            and currency_counts[i] / total_counts[i] > threshold
            and i != date_col_idx
        ]

        # Check header for debit/credit keywords
        debit_keywords = {"debit", "withdrawal", "dr", "debit amount"}
        credit_keywords = {"credit", "deposit", "cr", "credit amount"}
        header_debit_col = None
        header_credit_col = None
        if self._header_row:
            for i, h in enumerate(self._header_row):
                hl = h.lower().strip()
                if hl in debit_keywords:
                    header_debit_col = i
                elif hl in credit_keywords:
                    header_credit_col = i

        if header_debit_col is not None and header_credit_col is not None:
            self._log(f"Amount cols from header: debit={header_debit_col}, credit={header_credit_col}")
            return {"amount_col": None, "debit_col": header_debit_col,
                    "credit_col": header_credit_col, "structure": "separate_debit_credit"}

        if len(currency_cols) >= 2:
            # Take the two rightmost currency columns
            debit_col = sorted(currency_cols)[-2]
            credit_col = sorted(currency_cols)[-1]
            self._log(f"Amount cols detected: debit={debit_col}, credit={credit_col}")
            return {"amount_col": None, "debit_col": debit_col,
                    "credit_col": credit_col, "structure": "separate_debit_credit"}

        if currency_cols:
            amount_col = sorted(currency_cols)[-1]
            self._log(f"Amount col detected: {amount_col}")
            return {"amount_col": amount_col, "debit_col": None,
                    "credit_col": None, "structure": "single_amount"}

        # Fallback: last column — mark as fallback so _row_has_standalone_amount
        # does NOT use it (avoids treating running-balance cells as new transactions)
        self._log(f"Amount col fallback: last col {col_count - 1} (not used for standalone detection)")
        return {"amount_col": None, "debit_col": None,
                "credit_col": None, "structure": "single_amount"}

    # ----------------------------------------------------------
    # Step 7: Merge Multi-line Rows
    # ----------------------------------------------------------

    # Fix 6: Summary/total row keywords — skip these during continuation merge
    # NOTE: igst, cgst, sgst REMOVED — they are legitimate transaction line items
    # (tax charges billed as separate transactions in Indian credit card statements)
    _SUMMARY_KEYWORDS = {
        "total", "sub total", "subtotal", "service tax", "gst", "cess",
        "interest", "late payment", "finance charge",
        "opening balance", "closing balance", "minimum amount due", "total due",
        "payment due", "credit limit", "available limit", "grand total",
        "brought forward", "carried forward",
    }

    def _is_summary_row(self, row: list[str]) -> bool:
        """Returns True if the row looks like a fee/tax/total summary row."""
        row_text = " ".join(c.lower() for c in row)
        return any(kw in row_text for kw in self._SUMMARY_KEYWORDS)

    def _row_has_standalone_amount(self, row: list[str], date_col_idx: int) -> bool:
        """
        Fix 2C: Returns True if a no-date row looks like a standalone transaction
        (has a currency-formatted amount) rather than a description continuation.

        Conditions (ALL must be true):
        1. No date in the date column
        2. Has a value in the detected amount column(s) matching currency format
        3. The row is not a summary row
        4. Amount must be >= 1.0 (reject page/serial numbers)
        """
        # Must not have a date
        while len(row) <= date_col_idx:
            row.append("")
        if _cell_has_date(row[date_col_idx]):
            return False

        # Must not be a summary row
        if self._is_summary_row(row):
            return False

        # Collect EXPLICITLY detected amount column indices only.
        # Do NOT fall back to last column — running-balance cells in the last
        # column would be incorrectly treated as standalone transactions.
        amount_cols = []
        if self._amount_col_idx is not None:
            amount_cols.append(self._amount_col_idx)
        if self._debit_col_idx is not None:
            amount_cols.append(self._debit_col_idx)
        if self._credit_col_idx is not None:
            amount_cols.append(self._credit_col_idx)

        # If no amount columns were explicitly detected, cannot determine
        # standalone status — treat as continuation row (safe default)
        if not amount_cols:
            return False

        _CURRENCY_RE = re.compile(r'^-?[\d,]+\.?\d*$')
        for col_idx in amount_cols:
            if col_idx < len(row):
                val = row[col_idx].strip()
                # Strip DR/CR suffix
                for sfx in ("DR", "CR", "Dr", "Cr"):
                    if val.upper().endswith(sfx):
                        val = val[:-len(sfx)].strip()
                val_clean = val.replace(",", "")
                if val_clean and _CURRENCY_RE.match(val_clean):
                    try:
                        if abs(float(val_clean)) >= 1.0:
                            return True
                    except ValueError:
                        pass

        return False

    def merge_multiline_rows(
        self, rows: list[list[str]], date_col_idx: int
    ) -> list[list[str]]:
        """
        Group continuation rows into their parent transaction row.
        A new transaction starts when the date column contains a date-like value.
        Fix 2D: A no-date row with a standalone amount starts a NEW transaction
                that inherits the date from the previous transaction.
        Fix 5: Correct duplicate text detection (superset check).
        Fix 6: Skip summary/total rows during merge.
        """
        merged: list[list[str]] = []
        current: list[str] | None = None

        # Use detected description column (set by _detect_description_column in extract())
        desc_col = self._desc_col_idx

        for row in rows:
            # Pad row to at least date_col_idx + 1
            while len(row) <= date_col_idx:
                row.append("")

            date_cell = row[date_col_idx]

            if _cell_has_date(date_cell):
                # New transaction with its own date
                if current is not None:
                    merged.append(current)
                current = list(row)

            elif self._row_has_standalone_amount(row, date_col_idx):
                # Fix 2D: No-date row with a standalone amount → new transaction
                # inheriting the date from the previous transaction
                if current is not None:
                    merged.append(current)
                    inherited_date = current[date_col_idx]
                else:
                    inherited_date = ""
                new_row = list(row)
                new_row[date_col_idx] = inherited_date
                current = new_row

            else:
                # Continuation row — merge into current transaction's description
                if current is not None:
                    # Fix 6: Skip summary/total rows
                    if self._is_summary_row(row):
                        continue
                    # Append non-empty cells to description column
                    continuation_text = " ".join(
                        cell for i, cell in enumerate(row)
                        if cell and i != date_col_idx
                    ).strip()
                    if continuation_text:
                        while len(current) <= desc_col:
                            current.append("")
                        existing = current[desc_col].strip()
                        # Fix 5: Correct duplicate/superset check
                        if continuation_text in existing:
                            pass  # already contained, skip
                        elif existing in continuation_text:
                            current[desc_col] = continuation_text  # superset replaces
                        else:
                            current[desc_col] = (
                                existing + " " + continuation_text
                            ).strip()
                # else: orphan row before first transaction, skip

        if current is not None:
            merged.append(current)

        return merged

    # ----------------------------------------------------------
    # Step 8: Normalize Transactions
    # ----------------------------------------------------------

    def _detect_amount_structure(self, rows: list[list[str]]) -> str:
        """
        Detect if the table has separate debit/credit columns or single amount.
        Returns: "separate_debit_credit" or "single_amount"
        """
        if not rows:
            return "single_amount"

        col_count = max(len(row) for row in rows)

        # Count columns that are mostly numeric (excluding date col)
        numeric_col_counts = [0] * col_count
        for row in rows:
            for i, cell in enumerate(row):
                if i < col_count and _cell_has_digits(cell) and not _cell_has_date(cell):
                    numeric_col_counts[i] += 1

        # If 2+ columns are heavily numeric (>30% of rows), likely separate debit/credit
        threshold = len(rows) * 0.3
        heavy_numeric = [i for i, cnt in enumerate(numeric_col_counts) if cnt > threshold]

        # Exclude date column
        heavy_numeric = [i for i in heavy_numeric if i != self._date_col_idx]

        if len(heavy_numeric) >= 2:
            return "separate_debit_credit"
        return "single_amount"

    @staticmethod
    def _normalize_amount(raw: str) -> str:
        """
        Fix 12: Normalize Indian currency amount strings.
        - Strips whitespace
        - Removes currency symbols (₹, Rs., Rs, INR)
        - Strips trailing DR/CR/C/D/M suffixes (e.g. "10.00 DR" → "10.00", "42,381.87C" → "42,381.87")
        - Removes all commas (handles lakh/crore format: 1,23,456.78)
        - Validates it's a valid float string
        Returns cleaned string (kept as string to preserve precision).
        """
        s = raw.strip()
        # Remove currency symbols
        for sym in ("₹", "Rs.", "Rs", "INR"):
            s = s.replace(sym, "").strip()
        # Strip trailing DR/CR suffix (with or without space)
        for sfx in (" DR", " CR", " Dr", " Cr", "DR", "CR", "Dr", "Cr"):
            if s.upper().endswith(sfx.upper()):
                s = s[:-len(sfx)].strip()
                break
        # Strip SBI Card style suffixes: C (Credit), D (Debit), M (EMI)
        # These are attached directly to the amount without space
        if s and s[-1].upper() in ("C", "D", "M"):
            s = s[:-1].strip()
        # Remove commas
        s = s.replace(",", "").strip()
        # Remove spaces within number (e.g., "1 234.56")
        s = s.replace(" ", "")
        # Validate: must be a valid float (with optional leading minus)
        try:
            float(s)
            return s
        except (ValueError, TypeError):
            return raw.strip()  # Return original if not parseable

    @staticmethod
    def _detect_type_from_amount(raw: str) -> str:
        """
        Detect transaction type from amount suffix.
        SBI Card uses: C = Credit, D = Debit, M = EMI (treated as debit)
        Other banks use: CR = Credit, DR = Debit
        Returns: "credit", "debit", or "" if no indicator found.
        """
        s = raw.strip().upper()
        if not s:
            return ""
        # Check for DR/CR suffix (with or without space)
        if s.endswith(" CR") or s.endswith("CR"):
            return "credit"
        if s.endswith(" DR") or s.endswith("DR"):
            return "debit"
        # Check for SBI Card style C/D/M suffix
        if s.endswith("C"):
            return "credit"
        if s.endswith("D") or s.endswith("M"):
            return "debit"
        return ""

    def _validate_transaction(self, txn: dict[str, Any]) -> bool:
        """
        Fix 13: Validate a transaction dict before including in output.
        A valid transaction must have:
          - Non-empty date that passes _cell_has_date()
          - Non-empty amount that contains at least one digit
        Description may be empty (some banks omit it for payment rows).
        Logs a warning in debug mode for filtered transactions.
        """
        if not txn.get("date") or not _cell_has_date(txn["date"]):
            self._log(f"  Filtered (bad date): {txn.get('date')!r}")
            return False
        if not txn.get("amount") or not _cell_has_digits(txn["amount"]):
            self._log(f"  Filtered (no amount): {txn.get('amount')!r}")
            return False
        return True

    def _extract_embedded_amount(self, txn: dict[str, Any]) -> dict[str, Any]:
        """
        Fix 16: Extract amount from description when amount column is missing/empty.

        Axis Bank pattern: "BBPS PAYMENT RECEIVED - 19,688.00 Cr"
        The amount and Cr/Dr indicator are embedded in the description.

        Pattern: DESCRIPTION AMOUNT Cr/Dr
        - Amount: numeric with optional commas and decimal
        - Suffix: Cr (credit) or Dr (debit)
        """
        desc = txn.get("description", "")
        amount = txn.get("amount", "")
        txn.get("type", "")

        # Only process if amount is missing, empty, or "0"
        if amount and amount != "0" and amount != "0.00":
            return txn

        if not desc:
            return txn

        # Pattern: amount followed by Cr/Dr at end of description
        # Examples: "BBPS PAYMENT RECEIVED - 19,688.00 Cr", "CASHBACK CREDIT 994.00 Cr"
        embedded_pattern = re.compile(
            r'([\d,]+\.?\d*)\s*(Cr|Dr|CR|DR)\s*$'
        )

        match = embedded_pattern.search(desc)
        if match:
            embedded_amount = match.group(1).replace(",", "")
            embedded_type = match.group(2).upper()

            # Validate the extracted amount
            try:
                float(embedded_amount)
            except (ValueError, TypeError):
                return txn

            # Update transaction
            txn["amount"] = embedded_amount
            txn["type"] = "credit" if embedded_type == "CR" else "debit"

            # Clean description - remove the embedded amount suffix
            txn["description"] = desc[:match.start()].strip()

            self._log(f"  Extracted embedded amount: {embedded_amount} {embedded_type} from '{desc}'")

        return txn

    def normalize_transactions(
        self, rows: list[list[str]], date_col_idx: int
    ) -> list[dict]:
        """
        Build structured transaction dicts from merged rows.

        {
            "date": str,
            "description": str,
            "amount": str,
            "type": "debit" | "credit" | "",
            "raw": original_row
        }
        Fix 12: Normalize amount strings.
        Fix 13: Validate and filter invalid transactions.
        """
        if not rows:
            return []

        col_count = max(len(row) for row in rows)
        amount_structure = self._detect_amount_structure(rows)
        self._log(f"Amount structure: {amount_structure}")

        # Determine column roles — use detected description column (Fix 3)
        desc_col = self._desc_col_idx

        # Amount columns: last 1 or 2 columns
        if amount_structure == "separate_debit_credit" and col_count >= 4:
            debit_col = col_count - 2
            credit_col = col_count - 1
        else:
            debit_col = None
            credit_col = None
            amount_col = col_count - 1

        transactions = []

        for row in rows:
            # Pad row
            while len(row) < col_count:
                row.append("")

            date = row[date_col_idx].strip()
            if not date:
                continue

            desc = row[desc_col].strip() if desc_col < len(row) else ""

            if amount_structure == "separate_debit_credit" and debit_col is not None:
                debit_val = row[debit_col].strip() if debit_col < len(row) else ""
                credit_val = row[credit_col].strip() if credit_col < len(row) else ""

                if debit_val and _cell_has_digits(debit_val):
                    # Apply _split_dr_cr so "10.00 DR" in debit_col → type=debit
                    split_val, split_type = _split_dr_cr(debit_val)
                    amount = self._normalize_amount(split_val)
                    txn_type = split_type if split_type else "debit"
                elif credit_val and _cell_has_digits(credit_val):
                    # Apply _split_dr_cr so "10.00 DR" in credit_col → type=debit (not credit)
                    split_val, split_type = _split_dr_cr(credit_val)
                    amount = self._normalize_amount(split_val)
                    txn_type = split_type if split_type else "credit"
                else:
                    amount = debit_val or credit_val
                    txn_type = ""
            else:
                raw_amount = row[amount_col].strip() if amount_col < len(row) else ""
                split_amount, txn_type = _split_dr_cr(raw_amount)
                amount = self._normalize_amount(split_amount)
                # If no type from DR/CR, check for SBI Card style C/D/M suffix
                if not txn_type:
                    txn_type = self._detect_type_from_amount(raw_amount)

            txn = {
                "date": date,
                "description": desc,
                "amount": amount,
                "type": txn_type,
                "raw": row,
            }

            # Fix 16: Extract embedded amount from description (Axis Bank pattern)
            txn = self._extract_embedded_amount(txn)

            # Add amount_paise (canonical integer representation)
            try:
                txn["amount_paise"] = _parse_amount_paise(txn.get("amount", "0"))
            except ValueError:
                txn["amount_paise"] = 0

            # Fix 13: Validate before including
            if self._validate_transaction(txn):
                transactions.append(txn)

        return transactions

    # ----------------------------------------------------------
    # Step 9: Collect All Pages
    # ----------------------------------------------------------

    def _find_actual_start_page(self, best_page: int, strategy: str) -> int:
        """
        Fix 10: Scan ALL pages from 0 to best_page-1 and collect those with dates.
        The actual start is the minimum page index that has dates.
        (Old code stopped on first gap — missed pages 1,2 if page 0 had no dates.)
        """
        if best_page == 0:
            return 0

        pages_with_dates = []
        for page_num in range(best_page):
            page_str = str(page_num + 1)
            found_dates = False

            for flavor in (strategy, "stream" if strategy == "lattice" else "lattice"):
                try:
                    tables = camelot.read_pdf(
                        self.pdf_path,
                        pages=page_str,
                        flavor=flavor,
                        split_text=True,
                        strip_text="\n",
                        suppress_stdout=True,
                    )
                    for t in tables:
                        rows = t.df.values.tolist()
                        date_count = sum(
                            1 for row in rows
                            if any(_cell_has_date(_cell_str(c)) for c in row)
                        )
                        if date_count >= 1:
                            found_dates = True
                            break
                    if found_dates:
                        break
                except Exception:
                    pass

            if found_dates:
                self._log(f"  Backward scan: page {page_num} has transaction data")
                pages_with_dates.append(page_num)
            else:
                self._log(f"  Backward scan: page {page_num} has no date rows")

        if pages_with_dates:
            return min(pages_with_dates)
        return best_page

    def _score_continuation(self, table) -> float:
        """
        Looser scoring for continuation pages.
        Requires only 1 date row (not 2), col_count >= 2, row_count >= 2.
        Returns score >= 0.
        """
        rows = table.df.values.tolist()
        row_count = len(rows)
        col_count = len(rows[0]) if rows else 0
        if row_count < 2 or col_count < 2:
            return 0.0
        date_rows = sum(
            1 for row in rows
            if any(_cell_has_date(_cell_str(c)) for c in row)
        )
        if date_rows < 1:
            return 0.0
        # Simple score: prefer more rows and more dates
        return (min(row_count, 100) * 1.5) + (date_rows / row_count * 30)

    def _collect_all_pages(self, start_page: int, strategy: str) -> list[list]:
        """
        After finding the best table on start_page, collect rows from
        all subsequent pages. Uses strict scoring first; falls back to
        looser continuation scoring. Stops when no table with dates found.
        """
        all_rows: list[list] = []
        consecutive_no_dates = 0

        for page_num in range(start_page, self._num_pages):
            page_str = str(page_num + 1)
            page_tables = []

            for flavor in (strategy, "stream" if strategy == "lattice" else "lattice"):
                try:
                    tables = camelot.read_pdf(
                        self.pdf_path,
                        pages=page_str,
                        flavor=flavor,
                        split_text=True,
                        strip_text="\n",
                        suppress_stdout=True,
                    )
                    if tables:
                        page_tables.extend(list(tables))
                except Exception:
                    pass

            if not page_tables:
                self._log(f"  Page {page_num}: no tables found, stopping")
                break

            # Try strict scoring first
            best_t, best_s = None, 0.0
            for t in page_tables:
                s = self.score_table({"table": t, "strategy": strategy, "page": page_num})
                if s > best_s:
                    best_s, best_t = s, t

            # Fall back to loose continuation scoring
            if best_s == 0.0:
                for t in page_tables:
                    s = self._score_continuation(t)
                    if s > best_s:
                        best_s, best_t = s, t

            if best_t is not None and best_s > 0:
                page_rows = best_t.df.values.tolist()
                self._log(f"  Page {page_num}: {len(page_rows)} rows (score={best_s:.1f})")
                all_rows.extend(page_rows)
                consecutive_no_dates = 0
            else:
                consecutive_no_dates += 1
                self._log(f"  Page {page_num}: no date table (#{consecutive_no_dates})")
                # Fix 11: Increased threshold from 2 to 3 (handles T&C pages between txn pages)
                if consecutive_no_dates >= 3:
                    self._log("  Stopping: 3 consecutive pages with no date rows")
                    break

        return all_rows

    # ----------------------------------------------------------
    # Step 10: Text-based Fallback (for PDFs where Camelot finds no table)
    # ----------------------------------------------------------

    def _extract_via_text_fallback(self, bank: str) -> dict[str, Any]:
        """
        Fallback for PDFs where Camelot cannot detect a transaction table.
        Uses pdfplumber text extraction to find lines starting with dates.

        Handles multiple formats:
        - Standard: DATE DESCRIPTION AMOUNT Cr/Dr
        - Axis Bank: DATE DESCRIPTION Cr_AMOUNT Cr Dr_AMOUNT Dr
        """
        self._log("Using pdfplumber text fallback...")
        transactions = []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    for line in text.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        tokens = line.split()
                        if not tokens:
                            continue
                        # Check if line starts with a date token
                        if not _cell_has_date(tokens[0]):
                            continue
                        # Skip header-like lines
                        if _is_header_row([line]):
                            continue

                        date = tokens[0]

                        # Detect Axis Bank format: DATE ... AMOUNT Cr/Dr CASHBACK Cr/Dr
                        # Example: "01/04/2025 BBPS PAYMENT RECEIVED - 19,688.00 Cr 0.00 Dr"
                        # The LAST Cr/Dr pair is CASHBACK EARNED (should be ignored)
                        # The SECOND-TO-LAST Cr/Dr pair is the main transaction amount

                        # Find all Cr/Dr positions from the end
                        cr_dr_positions = []
                        i = len(tokens) - 1
                        while i >= 1:
                            token = tokens[i].upper()
                            if token in ("CR", "DR") and i > 1:
                                prev_token = tokens[i-1].replace(",", "").replace("(", "").replace(")", "")
                                # Check if it's a valid number
                                try:
                                    float(prev_token)
                                    cr_dr_positions.append((i-1, i, token))  # (amount_idx, crdr_idx, type)
                                    i -= 2
                                    continue
                                except ValueError:
                                    pass
                            i -= 1

                        # Axis Bank format: has 2 Cr/Dr pairs (main amount + cashback earned)
                        # We only want the FIRST pair (main transaction)
                        if len(cr_dr_positions) >= 2:
                            # Take the second-to-last pair (main amount, not cashback)
                            amount_idx, crdr_idx, txn_type = cr_dr_positions[1]
                            amount = tokens[amount_idx].replace(",", "")
                            desc_end = amount_idx
                            desc = " ".join(tokens[1:desc_end]).strip()

                            if amount and amount != "0.00" and amount != "0":
                                transactions.append({
                                    "date": date,
                                    "description": desc,
                                    "amount": self._normalize_amount(amount),
                                    "type": "credit" if txn_type == "CR" else "debit",
                                    "raw": tokens,
                                })
                            continue

                        # Single Cr/Dr pair (standard format)
                        if len(cr_dr_positions) == 1:
                            amount_idx, crdr_idx, txn_type = cr_dr_positions[0]
                            amount = tokens[amount_idx].replace(",", "")
                            desc_end = amount_idx
                            desc = " ".join(tokens[1:desc_end]).strip()

                            if amount and amount != "0.00" and amount != "0":
                                transactions.append({
                                    "date": date,
                                    "description": desc,
                                    "amount": self._normalize_amount(amount),
                                    "type": "credit" if txn_type == "CR" else "debit",
                                    "raw": tokens,
                                })
                            continue

                        # Standard format: DATE ... AMOUNT Cr/Dr
                        amount = ""
                        txn_type = ""
                        desc_end = len(tokens)

                        # Check for Cr/Dr suffix
                        if len(tokens) >= 2:
                            last = tokens[-1].upper()
                            second_last = tokens[-2].upper() if len(tokens) >= 2 else ""
                            if last in ("CR", "DR"):
                                txn_type = "credit" if last == "CR" else "debit"
                                # Amount is second-to-last token
                                if len(tokens) >= 3 and _cell_has_digits(tokens[-2]):
                                    amount = tokens[-2]
                                    desc_end = len(tokens) - 2
                                else:
                                    desc_end = len(tokens) - 1
                            elif second_last in ("CR", "DR"):
                                txn_type = "credit" if second_last == "CR" else "debit"
                                if _cell_has_digits(tokens[-1]):
                                    amount = tokens[-1]
                                    desc_end = len(tokens) - 2
                            else:
                                # No Cr/Dr — last numeric token is amount
                                for i in range(len(tokens) - 1, 0, -1):
                                    if _cell_has_digits(tokens[i]):
                                        amount = tokens[i]
                                        desc_end = i
                                        break

                        desc = " ".join(tokens[1:desc_end]).strip()

                        # Detect type from description keywords if no explicit Cr/Dr
                        # HDFC uses "CREDIT" in description for payments/refunds
                        if not txn_type and amount:
                            desc_lower = desc.lower()
                            # Credit keywords: payment received, refund, cashback, reversal
                            if any(kw in desc_lower for kw in ['credit', 'payment received', 'refund', 'cashback', 'reversal', 'transfer credit']):
                                txn_type = "credit"
                            else:
                                txn_type = "debit"

                        if date and (amount or desc):
                            txn = {
                                "date": date,
                                "description": desc,
                                "amount": self._normalize_amount(amount) if amount else "",
                                "type": txn_type,
                                "raw": tokens,
                            }
                            # Add amount_paise (canonical integer representation)
                            try:
                                txn["amount_paise"] = _parse_amount_paise(txn.get("amount", "0"))
                            except ValueError:
                                txn["amount_paise"] = 0
                            transactions.append(txn)
        except Exception as e:
            self._log(f"Text fallback error: {e}")

        self._log(f"Text fallback found {len(transactions)} transactions")
        return {
            "bank": bank,
            "transactions": transactions,
            "selected_page": 0,
            "strategy": "text_fallback",
            "extraction_method": "pdfplumber_text",
            "transaction_count": len(transactions),
        }

    # ----------------------------------------------------------
    # Step 11: Full Extract Pipeline
    # ----------------------------------------------------------

    def extract(self) -> dict[str, Any]:
        """
        Full extraction pipeline.
        Returns structured dict with bank, transactions, metadata.
        """
        # Step 1: Detect bank
        bank = self.detect_bank()
        self._log(f"Bank: {bank}, Total pages: {self._num_pages}")

        # Step 2-4: Find best table
        try:
            self.select_best_table()
        except ExtractionError as e:
            self._log(f"ExtractionError: {e}")
            # Fallback: try pdfplumber text extraction
            return self._extract_via_text_fallback(bank)

        start_page = self._best_page
        strategy = self._best_strategy

        # Step 5: Scan backwards from best_page to find the true first page
        # with transaction data (handles cases where earlier pages also have txns)
        actual_start = self._find_actual_start_page(start_page, strategy)
        self._log(f"Best page={start_page}, actual start={actual_start}")

        # Collect rows from actual start page onwards
        self._log(f"Collecting rows from page {actual_start} onwards...")
        all_raw_rows = self._collect_all_pages(actual_start, strategy)
        self._log(f"Total raw rows collected: {len(all_raw_rows)}")

        # Step 6: Clean rows
        cleaned = self.clean_rows(all_raw_rows)
        self._log(f"Rows after cleaning: {len(cleaned)}")

        # Step 7: Detect date column + description column
        date_col_idx = self._detect_date_column(cleaned)
        self._date_col_idx = date_col_idx
        self._log(f"Date column index: {date_col_idx}")

        # Fix 3: Detect description column using header + avg-length heuristic
        desc_col_idx = self._detect_description_column(cleaned, date_col_idx)
        self._desc_col_idx = desc_col_idx
        self._log(f"Description column index: {desc_col_idx}")

        # Fix 2E: Detect amount columns BEFORE merge (needed by _row_has_standalone_amount)
        amount_info = self._detect_amount_columns(cleaned, date_col_idx)
        self._amount_col_idx = amount_info.get("amount_col")
        self._debit_col_idx = amount_info.get("debit_col")
        self._credit_col_idx = amount_info.get("credit_col")
        self._log(f"Amount cols: amount={self._amount_col_idx}, debit={self._debit_col_idx}, credit={self._credit_col_idx}")

        # Step 8: Merge multi-line rows
        merged = self.merge_multiline_rows(cleaned, date_col_idx)
        self._log(f"Rows after merge: {len(merged)}")

        # Step 9: Normalize
        transactions = self.normalize_transactions(merged, date_col_idx)
        self._log(f"Transactions extracted: {len(transactions)}")

        # Fix 14: Compute statement period from min/max dates
        statement_period: dict[str, Any] = {}
        if transactions:
            dates = [t["date"] for t in transactions if t.get("date")]
            if dates:
                statement_period = {"from": min(dates), "to": max(dates)}

        return {
            "bank": bank,
            "transactions": transactions,
            "selected_page": start_page,
            "strategy": strategy,
            "extraction_method": "camelot_unified",
            "transaction_count": len(transactions),
            "statement_period": statement_period,
        }


# ============================================================
# CLI Entry Point
# ============================================================

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python statement_extractor.py <pdf_path> [--debug]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    debug = "--debug" in sys.argv

    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    extractor = StatementExtractor(pdf_path, debug=debug)
    result = extractor.extract()

    # Truncate transactions for CLI readability
    output = dict(result)
    txns = output.get("transactions", [])
    if len(txns) > 5:
        output["transactions_preview"] = txns[:5]
        output["transactions"] = f"[{len(txns)} transactions total]"

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
