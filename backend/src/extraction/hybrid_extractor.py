"""
HYBRID EXTRACTOR
Combines LayoutAnalyzer (geometry detection) with Camelot (table extraction)
to produce accurate transaction rows from bank statement PDFs.

Pipeline:
  1. LayoutAnalyzer → table_bbox, columns, table_pages, metadata
  2. Camelot (guided by bbox + column separators) → raw rows per page
  3. Post-processing → clean rows, merge multi-line descriptions, Dr/Cr split
  4. Return structured JSON

Constraints:
  - Do NOT modify LayoutAnalyzer
  - No business logic beyond transaction row structuring
  - No heavy regex parsing
  - Falls back to pdfplumber line extraction if Camelot fails
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import camelot
import pdfplumber

from src.structural.layout_analyzer import LayoutAnalyzer

# ============================================================
# Coordinate Conversion
# ============================================================


def _bbox_to_camelot(bbox: tuple[Any, ...], page_height: float) -> str:
    """
    Convert pdfplumber bbox (x0, y0, x1, y1) measured from top-left
    to Camelot table_areas format "x0,y0,x1,y1" measured from bottom-left.

    pdfplumber: y increases downward (top-left origin)
    Camelot:    y increases upward  (bottom-left origin)

    So:
        camelot_y1 = page_height - pdfplumber_y0   (top of table)
        camelot_y0 = page_height - pdfplumber_y1   (bottom of table)
    """
    x0, y0, x1, y1 = bbox
    camelot_y0 = page_height - y1  # bottom of table in camelot coords
    camelot_y1 = page_height - y0  # top of table in camelot coords
    return f"{x0:.1f},{camelot_y0:.1f},{x1:.1f},{camelot_y1:.1f}"


# ============================================================
# Strategy Selection
# ============================================================


def _count_vertical_lines_in_bbox(
    pdf_path: str, page_num: int, bbox: tuple[Any, ...]
) -> int:
    """Count vertical lines inside the table bbox on a given page."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num >= len(pdf.pages):
                return 0
            page = pdf.pages[page_num]
            x0, y0, x1, y1 = bbox
            count = 0
            for ln in page.lines:
                lx0 = ln.get("x0", 0)
                lx1 = ln.get("x1", 0)
                ly0 = ln.get("top", ln.get("y0", 0))
                ly1 = ln.get("bottom", ln.get("y1", 0))
                # Vertical line: x0 ≈ x1
                if (
                    abs(lx0 - lx1) < 2
                    and x0 <= lx0 <= x1
                    and not (ly1 < y0 or ly0 > y1)
                ):
                    # Must be inside bbox horizontally and overlap vertically
                    count += 1
            return count
    except Exception:
        return 0


def _select_flavor(pdf_path: str, page_num: int, bbox: tuple[Any, ...]) -> str:
    """Select Camelot flavor based on vertical line count in bbox."""
    vlines = _count_vertical_lines_in_bbox(pdf_path, page_num, bbox)
    return "lattice" if vlines >= 3 else "stream"


# ============================================================
# Column Separators
# ============================================================


def _get_sorted_x_starts(columns: dict[str, Any], table_x0: float = 0.0) -> list[float]:
    """
    Extract sorted internal column separator x positions from columns dict.
    Excludes the leftmost x_start (table boundary) since Camelot uses
    table_areas to define the left edge — only internal dividers are needed.
    """
    x_starts = []
    for col_def in columns.values():
        x = col_def.get("x_start", 0)
        if x > 0:
            x_starts.append(x)
    sorted_x = sorted(set(x_starts))
    # Remove the leftmost value if it equals (or is very close to) the table x0
    # to avoid creating a zero-width phantom column at the left edge
    if sorted_x and abs(sorted_x[0] - table_x0) < 5:
        sorted_x = sorted_x[1:]
    return sorted_x


# ============================================================
# Row Utilities
# ============================================================


def _is_empty_row(row: list[str]) -> bool:
    return all(str(cell).strip() == "" for cell in row)


def _is_header_row(row: list[str], header_keywords: list[str]) -> bool:
    row_text = " ".join(str(c).strip().lower() for c in row)
    return any(kw in row_text for kw in header_keywords)


def _row_has_date(first_cell: str) -> bool:
    """
    A row starts a new transaction if first cell contains
    a digit at position 0 AND contains '/' or '-'.
    """
    s = str(first_cell).strip()
    if not s:
        return False
    return s[0].isdigit() and ("/" in s or "-" in s)


def _split_amount_dr_cr(amount_str: str) -> tuple[str, str]:
    """
    Split "1,234.56 DR" → ("1,234.56", "DR")
    Split "500.00 CR"   → ("500.00", "CR")
    Returns (amount_str, '') if no indicator found.
    """
    s = amount_str.strip()
    s_upper = s.upper()
    for suffix in [" DR", "\nDR", "DR"]:
        if s_upper.endswith(suffix):
            return s[: len(s) - len(suffix)].strip(), "DR"
    for suffix in [" CR", "\nCR", "CR"]:
        if s_upper.endswith(suffix):
            return s[: len(s) - len(suffix)].strip(), "CR"
    return s, ""


# ============================================================
# pdfplumber Fallback Extractor
# ============================================================


def _pdfplumber_extract(
    pdf_path: str,
    page_num: int,
    bbox: tuple[Any, ...],
    columns: dict[str, Any],
    debug: bool = False,
) -> list[list[str]]:
    """
    Fallback: extract rows using pdfplumber character coordinates.
    - Collect chars inside bbox
    - Cluster by y coordinate (round to nearest 3–5 pixels)
    - Assign text to column bucket based on x coordinate
    """
    rows: list[list[str]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_num >= len(pdf.pages):
                return rows
            page = pdf.pages[page_num]
            x0, y0, x1, y1 = bbox

            chars_in_bbox = [
                c
                for c in page.chars
                if x0 <= c["x0"] <= x1 and y0 <= c.get("top", 0) <= y1
            ]
            if not chars_in_bbox:
                return rows

            # Group by Y (round to nearest 4px)
            lines: dict[int, list[dict[str, Any]]] = defaultdict(list)
            for c in chars_in_bbox:
                y_key = round(c.get("top", 0) / 4) * 4
                lines[y_key].append(c)

            # Sorted column boundaries
            col_boundaries = sorted(
                [
                    (col_def["x_start"], col_def["x_end"])
                    for col_def in columns.values()
                ],
                key=lambda b: b[0],
            )
            if not col_boundaries:
                col_boundaries = [(x0, x1)]

            for y_key in sorted(lines.keys()):
                line_chars = sorted(lines[y_key], key=lambda c: c["x0"])
                row = []
                for cx0, cx1 in col_boundaries:
                    cell_chars = [c for c in line_chars if cx0 <= c["x0"] <= cx1]
                    cell_text = "".join(c["text"] for c in cell_chars).strip()
                    row.append(cell_text)
                if any(cell.strip() for cell in row):
                    rows.append(row)

    except Exception as e:
        if debug:
            print(
                f"[HybridExtractor] pdfplumber fallback error on page {page_num}: {e}"
            )

    return rows


# ============================================================
# HybridExtractor
# ============================================================


class HybridExtractor:
    """
    Hybrid extractor: uses LayoutAnalyzer for coordinates,
    Camelot for table extraction, with pdfplumber fallback.
    """

    # Header keywords: only exact/short tokens that appear ONLY in header rows
    # Avoid broad words like 'transaction', 'amount', 'base' that appear in data
    HEADER_KEYWORDS = [
        "transaction date",
        "transaction description",
        "amount (in rs.)",
        "amount (rs.)",
        "neucoins*",
        "base neucoins",
        "emi eligibility",
        "fx transactions",
        "particulars",
        "narration",
        "withdrawal",
        "deposit",
        "txn date",
        "txn amount",
    ]

    def __init__(self, pdf_path: str, debug: bool = False):
        self.pdf_path = str(pdf_path)
        self.debug = debug
        self._analyzer: LayoutAnalyzer | None = None
        self._layout: dict[str, Any] | None = None

    def _log(self, message: str) -> None:
        if self.debug:
            print(f"[HybridExtractor] {message}")

    # ========== Step 1: Layout Analysis ==========

    def _run_layout_analysis(self) -> dict[str, Any]:
        self._analyzer = LayoutAnalyzer(self.pdf_path, debug=self.debug)
        self._layout = self._analyzer.analyze()
        return self._layout

    # ========== Step 2: Camelot Extraction per Page ==========

    def _extract_page_camelot(
        self,
        page_num: int,
        bbox: tuple[Any, ...],
        columns: dict[str, Any],
        page_height: float,
    ) -> tuple[list[list[str]], str]:
        """
        Extract table from one page using Camelot.
        Returns (rows_as_list_of_lists, strategy_used).
        """
        page_str = str(page_num + 1)  # Camelot is 1-based

        # Coordinate conversion
        pdfplumber_bbox = bbox
        camelot_area = _bbox_to_camelot(bbox, page_height)
        table_x0 = bbox[0]
        col_seps = _get_sorted_x_starts(columns, table_x0=table_x0)

        # Strategy selection
        flavor = _select_flavor(self.pdf_path, page_num, bbox)

        if self.debug:
            self._log(f"Page {page_num}: pdfplumber_bbox={pdfplumber_bbox}")
            self._log(f"Page {page_num}: camelot_area={camelot_area}")
            self._log(f"Page {page_num}: flavor={flavor}, col_seps={col_seps}")

        # Try with column separators first (stream only), then without
        attempts = []
        if flavor == "stream" and col_seps:
            attempts.append({"flavor": "stream", "use_cols": True})
            attempts.append({"flavor": "stream", "use_cols": False})
        elif flavor == "lattice":
            attempts.append({"flavor": "lattice", "use_cols": False})
            attempts.append({"flavor": "stream", "use_cols": True})
            attempts.append({"flavor": "stream", "use_cols": False})
        else:
            attempts.append({"flavor": flavor, "use_cols": False})

        for attempt in attempts:
            try:
                kwargs: dict[str, Any] = {
                    "pages": page_str,
                    "flavor": attempt["flavor"],
                    "suppress_stdout": True,
                    "table_areas": [camelot_area],
                    "split_text": True,
                }
                if attempt["use_cols"] and col_seps:
                    kwargs["columns"] = [",".join(str(x) for x in col_seps)]

                tables = camelot.read_pdf(self.pdf_path, **kwargs)  # type: ignore[attr-defined]
                self._log(
                    f"Page {page_num}: {attempt['flavor']} (cols={attempt['use_cols']}) found {len(tables)} tables"
                )

                if len(tables) == 0:
                    continue

                all_rows: list[list[Any]] = []
                for table in tables:
                    all_rows.extend(table.df.values.tolist())

                if all_rows:
                    self._log(
                        f"Page {page_num}: extracted {len(all_rows)} rows via {attempt['flavor']}"
                    )
                    # Cast to correct return type
                    return [[str(c) for c in row] for row in all_rows], str(
                        attempt["flavor"]
                    )

            except Exception as e:
                self._log(
                    f"Page {page_num}: {attempt['flavor']} (cols={attempt['use_cols']}) failed: {e}"
                )
                continue

        self._log(f"Page {page_num}: all Camelot attempts failed → fallback")
        return [], flavor

    # ========== Step 3: Post-Processing ==========

    def _post_process_rows(
        self,
        raw_rows: list[list[str]],
        columns: dict[str, Any],
        bank: str,
        amount_structure: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Clean raw rows into transaction dicts:
        - Remove empty rows
        - Remove header duplicates
        - Merge multi-line descriptions
        - Split Dr/Cr from amount
        - Include 'raw' field
        """
        col_names = list(columns.keys())
        transactions: list[dict[str, Any]] = []
        pending: dict[str, Any] | None = None

        for row in raw_rows:
            # Normalize row length
            row = [str(c) for c in row]
            while len(row) < len(col_names):
                row.append("")
            row = row[: len(col_names)]

            if _is_empty_row(row):
                continue
            if _is_header_row(row, self.HEADER_KEYWORDS):
                continue

            cell = {col_names[i]: row[i].strip() for i in range(len(col_names))}
            first_cell = cell.get(col_names[0], "")

            if _row_has_date(first_cell):
                # Flush pending
                if pending is not None:
                    transactions.append(pending)
                pending = self._build_transaction(
                    cell, col_names, amount_structure, row
                )
            else:
                # Continuation row: merge description
                if pending is not None:
                    desc_key = self._find_description_key(col_names)
                    if desc_key:
                        addition = cell.get(desc_key, "").strip()
                        if addition and addition not in pending.get("description", ""):
                            pending["description"] = (
                                pending.get("description", "") + " " + addition
                            ).strip()
                # else: orphan row, skip

        if pending is not None:
            transactions.append(pending)

        return transactions

    def _build_transaction(
        self,
        cell: dict[str, Any],
        col_names: list[str],
        amount_structure: dict[str, Any],
        raw_row: list[str],
    ) -> dict[str, Any]:
        txn: dict[str, Any] = {}

        # Date (always first column)
        txn["date"] = cell.get(col_names[0], "").strip()

        # Description
        desc_key = self._find_description_key(col_names)
        txn["description"] = cell.get(desc_key, "").strip() if desc_key else ""

        # Amount
        amt_type = (amount_structure or {}).get("type", "unknown")

        if amt_type == "separate_debit_credit":
            debit_key = self._find_key(col_names, ["debit"])
            credit_key = self._find_key(col_names, ["credit"])
            debit_val = cell.get(debit_key, "").strip() if debit_key else ""
            credit_val = cell.get(credit_key, "").strip() if credit_key else ""
            txn["amount"] = debit_val or credit_val
            txn["type"] = "debit" if debit_val else ("credit" if credit_val else "")

        else:
            amt_key = self._find_key(col_names, ["amount", "credit", "debit"])
            raw_amount = cell.get(amt_key, "").strip() if amt_key else ""
            amount, indicator = _split_amount_dr_cr(raw_amount)
            txn["amount"] = amount
            txn["type"] = indicator.lower() if indicator else ""

        # Extra columns (cashback, neucoins, etc.)
        used_keys = {
            col_names[0],
            desc_key,
            self._find_key(col_names, ["amount", "credit", "debit"]),
            self._find_key(col_names, ["debit"]),
            self._find_key(col_names, ["credit"]),
        }
        for col in col_names:
            if col not in used_keys and col not in txn:
                val = cell.get(col, "").strip()
                if val:
                    txn[col] = val

        # Raw row preserved
        txn["raw"] = raw_row

        return txn

    def _find_key(self, col_names: list[str], candidates: list[str]) -> str | None:
        for candidate in candidates:
            for col in col_names:
                if candidate in col.lower():
                    return col
        return None

    def _find_description_key(self, col_names: list[str]) -> str | None:
        return self._find_key(
            col_names, ["description", "narration", "particulars", "details", "col_1"]
        )

    def _infer_columns_from_rows(
        self, raw_rows: list[list[str]], layout_columns: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Determine effective column structure for post-processing.

        If Camelot rows have a different column count than LayoutAnalyzer,
        generate generic column names based on actual row width.
        Map them semantically: first col = date, last col = amount,
        middle cols = description (and extras).
        """
        if not raw_rows:
            return layout_columns

        # Find the most common row width
        widths = [len(row) for row in raw_rows if not _is_empty_row(row)]
        if not widths:
            return layout_columns

        from collections import Counter

        most_common_width = Counter(widths).most_common(1)[0][0]
        layout_width = len(layout_columns)

        # If widths match, use LayoutAnalyzer columns as-is
        if most_common_width == layout_width:
            return layout_columns

        # Otherwise, generate semantic column names for actual width
        self._log(
            f"Column count mismatch: Camelot={most_common_width}, LayoutAnalyzer={layout_width} → using inferred columns"
        )

        # Check LayoutAnalyzer's amount_structure for debit/credit info
        amt_structure = (self._layout or {}).get("amount_structure", {}) or {}
        has_separate = amt_structure.get("type") == "separate_debit_credit"

        if most_common_width == 1:
            return {"col_0": {"x_start": 0, "x_end": 999}}
        elif most_common_width == 2:
            return {
                "date": {"x_start": 0, "x_end": 100},
                "amount": {"x_start": 100, "x_end": 999},
            }
        elif most_common_width == 3:
            if has_separate:
                return {
                    "date": {"x_start": 0, "x_end": 100},
                    "description": {"x_start": 100, "x_end": 400},
                    "debit": {"x_start": 400, "x_end": 999},
                }
            return {
                "date": {"x_start": 0, "x_end": 100},
                "description": {"x_start": 100, "x_end": 400},
                "amount": {"x_start": 400, "x_end": 999},
            }
        elif most_common_width == 4:
            if has_separate:
                return {
                    "date": {"x_start": 0, "x_end": 100},
                    "description": {"x_start": 100, "x_end": 350},
                    "debit": {"x_start": 350, "x_end": 500},
                    "credit": {"x_start": 500, "x_end": 999},
                }
            return {
                "date": {"x_start": 0, "x_end": 100},
                "description": {"x_start": 100, "x_end": 350},
                "col_2": {"x_start": 350, "x_end": 500},
                "amount": {"x_start": 500, "x_end": 999},
            }
        elif most_common_width == 5:
            if has_separate:
                return {
                    "date": {"x_start": 0, "x_end": 100},
                    "description": {"x_start": 100, "x_end": 300},
                    "col_2": {"x_start": 300, "x_end": 400},
                    "debit": {"x_start": 400, "x_end": 550},
                    "credit": {"x_start": 550, "x_end": 999},
                }
            return {
                "date": {"x_start": 0, "x_end": 100},
                "description": {"x_start": 100, "x_end": 300},
                "col_2": {"x_start": 300, "x_end": 400},
                "col_3": {"x_start": 400, "x_end": 550},
                "amount": {"x_start": 550, "x_end": 999},
            }
        else:
            # Generic: first=date, last=amount, rest=description+extras
            cols = {}
            cols["date"] = {"x_start": 0, "x_end": 100}
            for i in range(1, most_common_width - 1):
                cols[f"col_{i}"] = {"x_start": i * 100, "x_end": (i + 1) * 100}
            cols["amount"] = {"x_start": (most_common_width - 1) * 100, "x_end": 999}
            return cols

    # ========== Step 4: Metadata Value Extraction ==========

    def _extract_metadata_values(
        self, metadata_fields: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract actual text values for metadata fields using pdfplumber."""
        values = {}
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for field_name, field_info in metadata_fields.items():
                    page_num = field_info.get("page", 0)
                    if page_num >= len(pdf.pages):
                        continue
                    page = pdf.pages[page_num]
                    val_loc = field_info.get("value_location", {})
                    if not val_loc:
                        continue
                    vx = val_loc.get("x", 0)
                    vy = val_loc.get("y", 0)
                    region = page.crop((vx, vy - 5, vx + 150, vy + 15))
                    text = region.extract_text()
                    if text:
                        values[field_name] = text.strip()
        except Exception as e:
            self._log(f"Metadata value extraction error: {e}")
        return values

    # ========== Debug Visualization ==========

    def _generate_debug_images(self, output_dir: str = "debug") -> None:
        if self._analyzer is None:
            return
        try:
            self._analyzer.generate_debug_image(output_dir=output_dir)
        except Exception as e:
            self._log(f"Debug image generation error: {e}")

    # ========== Main Entry Point ==========

    def extract(self) -> dict[str, Any]:
        """Full extraction pipeline."""

        # Step 1: Layout analysis
        self._log("Step 1: Running LayoutAnalyzer...")
        layout = self._run_layout_analysis()

        bank = layout.get("bank", "Unknown")
        table_pages = layout.get("table_pages", [])
        table_bbox = layout.get("table_bbox")
        columns = layout.get("columns", {})
        amount_structure = layout.get("amount_structure", {})

        self._log(
            f"Bank: {bank}, Pages: {table_pages}, Columns: {list(columns.keys())}"
        )

        if not table_bbox or not table_pages:
            self._log("WARNING: No table bbox or pages found")
            return {
                "bank": bank,
                "metadata": {},
                "transactions": [],
                "table_pages": [],
                "extraction_method": "hybrid_camelot",
                "error": "No transaction table detected",
            }

        # Step 2: Extract metadata values
        self._log("Step 2: Extracting metadata values...")
        metadata_values = self._extract_metadata_values(
            (self._analyzer and self._analyzer.metadata_fields) or {}
        )

        # Step 3: Extract rows from each page using Camelot
        self._log("Step 3: Extracting rows with Camelot...")
        all_raw_rows: list[list[str]] = []
        strategies_used: set[Any] = set()

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in table_pages:
                if page_num >= len(pdf.pages):
                    continue
                page = pdf.pages[page_num]
                page_height = page.height

                # Bbox: use layout bbox for first page, full page for continuations
                if page_num == table_pages[0]:
                    bbox = tuple(table_bbox)
                else:
                    bbox = (
                        table_bbox[0],
                        20.0,
                        table_bbox[2],
                        page_height - 40.0,
                    )

                rows, strategy = self._extract_page_camelot(
                    page_num, bbox, columns, page_height
                )
                strategies_used.add(strategy)

                if rows:
                    self._log(f"Page {page_num}: {len(rows)} rows via {strategy}")
                    all_raw_rows.extend(rows)
                else:
                    # Fallback to pdfplumber
                    self._log(
                        f"Page {page_num}: Camelot returned 0 rows → pdfplumber fallback"
                    )
                    fallback_rows = _pdfplumber_extract(
                        self.pdf_path, page_num, bbox, columns, self.debug
                    )
                    self._log(
                        f"Page {page_num}: pdfplumber fallback got {len(fallback_rows)} rows"
                    )
                    all_raw_rows.extend(fallback_rows)
                    strategies_used.add("pdfplumber_fallback")

        self._log(f"Total raw rows: {len(all_raw_rows)}")

        # Step 4: Post-process rows
        # Determine effective column count from actual Camelot rows (not LayoutAnalyzer)
        self._log("Step 4: Post-processing rows...")
        effective_columns = self._infer_columns_from_rows(all_raw_rows, columns)
        self._log(
            f"Effective columns for post-processing: {list(effective_columns.keys())}"
        )
        transactions = self._post_process_rows(
            all_raw_rows, effective_columns, bank, amount_structure
        )
        self._log(f"Transactions extracted: {len(transactions)}")

        # Step 5: Debug images
        if self.debug:
            self._generate_debug_images()

        return {
            "bank": bank,
            "metadata": metadata_values,
            "transactions": transactions,
            "table_pages": table_pages,
            "extraction_method": "hybrid_camelot",
            "strategies_used": list[Any](strategies_used),
            "column_names": list[Any](columns.keys()),
            "amount_structure": (amount_structure or {}).get("type", "unknown"),
            "transaction_count": len(transactions),
        }


# ============================================================
# CLI Entry Point
# ============================================================


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python hybrid_extractor.py <pdf_path> [--debug]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    debug = "--debug" in sys.argv

    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    extractor = HybridExtractor(pdf_path, debug=debug)
    result = extractor.extract()

    # Print JSON (truncate transactions for readability)
    output = dict(result)
    txns = output.get("transactions", [])
    if len(txns) > 5:
        output["transactions_preview"] = txns[:5]
        output["transactions"] = f"[{len(txns)} transactions total]"

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
