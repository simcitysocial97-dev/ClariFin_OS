"""
STRUCTURAL LAYOUT ANALYZER - PHASE 1 (FINAL)
Analyzes PDF layout structure without parsing transactions.

Improvements:
- Header validation via transaction page presence
- Column detection from header row characters (gap-based)
- Robust amount structure classification
- Strict transaction page detection
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pdfplumber


class LayoutAnalyzer:
    """Analyze PDF layout structure to detect transaction table geometry."""

    # Anchor keywords for header detection (lowercase)
    HEADER_ANCHORS = [
        "transaction date", "date", "particulars", "description", "narration",
        "details", "amount", "debit", "credit", "dr", "cr", "amount (rs.)",
        "txn amount", "transaction amount", "amount in inr", "debit amount",
        "credit amount", "base neucoins*", "cashback", "reward points",
    ]

    # Stop keywords for bottom boundary and page stopping
    STOP_KEYWORDS = [
        "total", "grand total", "closing balance", "balance c/f",
        "total debit", "total credit", "statement summary", "reward points",
        "value added services", "savings and benefits", "important information",
        "stay ahead", "bring extra joy", "schedule of charges", "neucoins summary",
        "note:", "share the privileges", "payment modes", "congratulations!",
        "now convert your credit card balances", "convert now", "refer now",
        "enjoy the convenience", "apply now", "check eligibility", "flexible tenure",
        "emily now", "avail quick cash", "important message", "contact us",
        "important messages", "loan on card", "promotional messages:",
    ]

    # Bank detection keywords
    BANK_KEYWORDS = {
        "HDFC Bank": ["hdfc bank", "hdfc bank limited", "hdfc bank ltd"],
        "ICICI Bank": ["icici bank", "icici bank limited"],
        "Axis Bank": ["axis bank", "axis bank limited"],
        "SBI Card": ["state bank of india", "sbi card", "sbi bank"],
        "IDFC First Bank": ["idfc first bank", "idfc first", "idfc bank"],
        "IndusInd Bank": ["indusind bank", "indusind bank limited"],
    }

    # Metadata field labels
    METADATA_LABELS = {
        "totalAmountDue": ["total amount due", "total due", "amount payable", "total outstanding", "net amount due"],
        "minimumAmountDue": ["minimum amount due", "minimum due", "min amount due", "minimum payment due"],
        "dueDate": ["payment due date", "due date", "pay by date", "payment date", "due by"],
        "cardNumber": ["card number", "card no", "account number", "credit card no", "card ending"],
        "creditLimit": ["credit limit", "total credit limit", "card limit"],
        "openingBalance": ["opening balance", "previous balance", "last statement balance", "previous statement balance"],
        "closingBalance": ["closing balance", "current balance", "outstanding balance", "total outstanding"],
        "billCycleStart": ["statement from", "statement period", "billing period", "cycle start", "from date"],
        "billCycleEnd": ["statement to", "statement date", "billing date", "cycle end", "to date"],
    }

    Y_TOLERANCE = 15.0  # Increased to merge multi‑line headers

    def __init__(self, pdf_path: str, debug: bool = False):
        self.pdf_path = pdf_path
        self.debug = debug

        # Results
        self.bank: str | None = None
        self.header_info: dict[str, Any] | None = None
        self.table_bbox: tuple[float, float, float, float] | None = None
        self.table_pages: list[int] = []
        self.columns: dict[str, dict[str, Any]] | None = None
        self.column_labels: dict[str, str] | None = None
        self.amount_structure: dict[str, Any] | None = None
        self.metadata_region: dict[str, Any] | None = None
        self.metadata_fields: dict[str, Any] | None = None

    def analyze(self) -> dict[str, Any]:
        with pdfplumber.open(self.pdf_path) as pdf:
            self.bank = self._detect_bank(pdf)
            self._log(f"Detected bank: {self.bank}")

            # Step 2: Find transaction table header (validated)
            self.header_info = self._find_table_header(pdf)
            if self.header_info is None:
                self._log("WARNING: No transaction table header found")
                return self._build_result()

            self._log(f"Header found on page {self.header_info['page']} at Y={self.header_info['y']:.1f}")

            # Step 3: Build table bounding box
            header_page = pdf.pages[self.header_info['page']]
            self.table_bbox = self._build_table_bbox(header_page, self.header_info)
            self._log(f"Table bbox: {self._format_bbox(self.table_bbox)}")

            # Step 4: Detect which pages contain transactions
            self.table_pages = self._detect_table_pages(pdf, self.header_info['page'])
            self._log(f"Table spans pages: {self.table_pages}")

            # Step 5: Detect columns using header row characters
            self.columns, self.column_labels = self._detect_columns_from_header_row(
                header_page, self.table_bbox, self.header_info
            )
            self._log(f"Columns detected: {list(self.columns.keys())}")
            self._log(f"Column labels: {self.column_labels}")

            # Step 6: Analyze amount structure (scan data rows)
            self.amount_structure = self._analyze_amount_structure(
                header_page, self.table_bbox, self.columns
            )
            self._log(f"Amount structure: {self.amount_structure}")

            # Step 7: Detect metadata
            self.metadata_region, self.metadata_fields = self._detect_metadata(pdf)
            self._log(f"Metadata fields found: {list(self.metadata_fields.keys()) if self.metadata_fields else 'None'}")

        return self._build_result()

    # ========== Bank Detection ==========
    def _detect_bank(self, pdf: Any) -> str:
        text = ""
        for page in pdf.pages[:2]:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        text_lower = text.lower()
        for bank_name, keywords in self.BANK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return bank_name
        return "Unknown"

    # ========== Header Detection (Validated) ==========
    def _find_table_header(self, pdf: Any) -> dict[str, Any] | None:
        best_result = None
        best_score = 0

        for page_num, page in enumerate(pdf.pages[:3]):
            anchor_matches = []
            for anchor_text in self.HEADER_ANCHORS:
                results = page.search(anchor_text, case=False)
                for result in results:
                    anchor_matches.append({
                        'text': anchor_text,
                        'x0': result['x0'],
                        'x1': result['x1'],
                        'y': result['top'],
                        'y_bottom': result['bottom'],
                    })

            if not anchor_matches:
                continue

            y_groups = self._group_by_y(anchor_matches)
            for y_center, group_items in y_groups.items():
                distinct = {item['text'].lower() for item in group_items}
                score = len(distinct)
                has_date = any('date' in a for a in distinct)
                has_amount = any(a in distinct for a in ['amount', 'debit', 'credit', 'dr', 'cr', 'amount (rs.)'])
                if has_date and has_amount:
                    score += 5

                # Validate: check if this header leads to transaction pages
                candidate_info = {
                    'page': page_num,
                    'y': y_center,
                    'y_bottom': max(item['y_bottom'] for item in group_items),
                    'anchors': list[Any](distinct),
                    'items': group_items,
                    'score': score,
                }
                if self._header_has_transaction_pages(pdf, candidate_info):
                    score += 10  # strong bonus
                else:
                    continue  # skip if no transaction pages

                if score > best_score:
                    best_score = score
                    best_result = candidate_info

        return best_result

    def _header_has_transaction_pages(self, pdf: Any, header_info: dict[str, Any]) -> bool:
        """Check if starting from this header page, we find transaction pages."""
        pages = self._detect_table_pages(pdf, header_info['page'], stop_on_first=False)
        return len(pages) > 0 and pages[0] == header_info['page']

    def _group_by_y(self, items: list[dict[str, Any]]) -> dict[float, list[dict[str, Any]]]:
        if not items:
            return {}
        sorted_items = sorted(items, key=lambda x: x['y'])
        groups = {}
        current_group = [sorted_items[0]]
        current_y_start = sorted_items[0]['y']
        for item in sorted_items[1:]:
            if abs(item['y'] - current_y_start) <= self.Y_TOLERANCE:
                current_group.append(item)
            else:
                y_center = sum(i['y'] for i in current_group) / len(current_group)
                groups[round(y_center, 1)] = current_group
                current_group = [item]
                current_y_start = item['y']
        if current_group:
            y_center = sum(i['y'] for i in current_group) / len(current_group)
            groups[round(y_center, 1)] = current_group
        return groups

    # ========== Table Bounding Box ==========
    def _build_table_bbox(self, page: Any, header_info: dict[str, Any]) -> tuple[float, float, float, float]:
        page_width = page.width
        page_height = page.height
        y_top = header_info['y_bottom'] + 5
        y_bottom = self._find_stop_boundary(page, y_top, page_height)
        # Safety: ensure y_bottom is always greater than y_top
        if y_bottom <= y_top:
            y_bottom = page_height - 40
        x0 = page_width * 0.02
        x1 = page_width * 0.98
        return (x0, y_top, x1, y_bottom)

    def _find_stop_boundary(self, page: Any, header_y: float, page_height: float) -> float:
        best_y = page_height - 40
        for keyword in self.STOP_KEYWORDS:
            try:
                results = page.search(keyword, case=False)
                for result in results:
                    y = result['top']
                    # Must be BELOW header (at least 20px) and above current best
                    if y > header_y + 20 and y < best_y:
                        best_y = y - 5
            except Exception:
                continue
        # Ensure bottom is always below top
        if best_y <= header_y:
            best_y = page_height - 40
        return best_y

    # ========== Transaction Page Detection (Stricter) ==========
    def _detect_table_pages(self, pdf: Any, header_page: int, stop_on_first: bool = True) -> list[int]:
        table_pages = [header_page]

        for page_num in range(header_page + 1, len(pdf.pages)):
            page = pdf.pages[page_num]
            text_lower = page.extract_text().lower() if page.extract_text() else ""
            has_stop = any(kw in text_lower for kw in self.STOP_KEYWORDS)
            if has_stop:
                break

            if self._page_has_transactions(page):
                table_pages.append(page_num)
            else:
                if stop_on_first:
                    break  # assume table ends

        return table_pages

    def _page_has_transactions(self, page: Any) -> bool:
        """Stricter check: look for multiple rows with date pattern and digits."""
        chars = page.chars
        if not chars:
            return False

        # Group by Y into lines
        lines = defaultdict(list)
        for c in chars:
            lines[round(c['top'])].append(c)

        transaction_line_count = 0
        for _y, line_chars in lines.items():
            # Sort by x
            line_chars.sort(key=lambda x: x['x0'])
            line_text = ''.join(c['text'] for c in line_chars)

            # Date pattern: digits, slash, digits (simple)
            has_date = False
            for i, ch in enumerate(line_text):
                if ch.isdigit() and i+2 < len(line_text) and line_text[i+1] == '/' and line_text[i+2].isdigit():
                    has_date = True
                    break

            # Amount pattern: digits with optional comma/period and maybe Dr/Cr
            has_amount = any(c.isdigit() for c in line_text) and ('dr' in line_text.lower() or 'cr' in line_text.lower() or '.' in line_text)

            if has_date and has_amount:
                transaction_line_count += 1

            # Early exit if enough lines found
            if transaction_line_count >= 3:
                return True

        return transaction_line_count >= 2

    # ========== Column Detection from Header Row ==========
    def _detect_columns_from_header_row(self, page: Any, bbox: tuple[float, float, float, float], header_info: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
        """
        Extract header row characters, detect columns via gaps, then classify.
        """
        x0, y_top, x1, y_bottom = bbox
        header_y = header_info['y']
        header_y_bottom = header_info.get('y_bottom', header_y + 15)

        # Collect characters in header row region
        header_chars = []
        for char in page.chars:
            cx = char['x0']
            cy = char.get('top', char.get('y0', 0))
            if (cx >= x0 and cx <= x1 and
                cy >= header_y - 5 and cy <= header_y_bottom + 5):
                header_chars.append(char)

        if not header_chars:
            # Fallback to default columns
            return self._default_columns(x0, x1), {}

        # Sort by x
        header_chars.sort(key=lambda c: c['x0'])

        # Build density histogram (1px bins) for header row
        width = int(x1 - x0) + 1
        density = [0] * width
        for c in header_chars:
            idx = int(c['x0'] - x0)
            if 0 <= idx < width:
                density[idx] += 1

        # Find gaps (bins with density == 0) of at least 8px
        gaps = []
        in_gap = False
        gap_start = 0
        for i, d in enumerate(density):
            if d == 0:
                if not in_gap:
                    gap_start = i
                    in_gap = True
            else:
                if in_gap:
                    gap_width = i - gap_start
                    if gap_width >= 8:
                        gap_center = x0 + gap_start + gap_width / 2
                        gaps.append(gap_center)
                    in_gap = False
        if in_gap:
            gap_width = width - gap_start
            if gap_width >= 8:
                gap_center = x0 + gap_start + gap_width / 2
                gaps.append(gap_center)

        # Build column boundaries: start at x0, then each gap, then x1
        boundaries = [x0] + gaps + [x1]
        columns: dict[str, dict[str, Any]] = {}
        for i in range(len(boundaries) - 1):
            col_start = boundaries[i]
            col_end = boundaries[i + 1]
            # Extract header text in this column
            col_text = ''
            for c in header_chars:
                if col_start <= c['x0'] <= col_end:
                    col_text += c['text']
            col_text = col_text.strip()

            # Classify column based on text
            col_type = self._classify_header_text(col_text)
            if col_type is None:
                col_type = f'col_{i}'

            columns[col_type] = {
                'x_start': round(col_start, 1),
                'x_end': round(col_end, 1),
                'header_text': col_text
            }

        # Rename duplicate types (e.g., two description columns) by appending _1, _2
        seen: dict[str, int] = defaultdict(int)
        final_columns: dict[str, dict[str, Any]] = {}
        for col_type, col_def in columns.items():
            if col_type in seen:
                new_type = f"{col_type}_{seen[col_type]}"
                seen[col_type] += 1
            else:
                new_type = col_type
                seen[col_type] = 1
            final_columns[new_type] = col_def

        # Build labels
        labels: dict[str, str] = {name: defn['header_text'] for name, defn in final_columns.items()}
        return final_columns, labels

    def _classify_header_text(self, text: str) -> str | None:
        text_lower = text.lower().strip()
        # Priority: more specific first
        if any(k in text_lower for k in ['date', 'txn date', 'transaction date']):
            return 'date'
        if any(k in text_lower for k in ['description', 'particulars', 'narration', 'details', 'transaction details']):
            return 'description'
        if any(k in text_lower for k in ['debit', 'dr', 'withdrawal', 'debit amount']):
            return 'debit'
        if any(k in text_lower for k in ['credit', 'cr', 'deposit', 'credit amount']):
            return 'credit'
        if any(k in text_lower for k in ['amount', 'txn amount', 'transaction amount', 'amount (rs.)', 'amount in inr']):
            return 'amount'
        if any(k in text_lower for k in ['cashback', 'cash back', 'neucoins', 'reward points']):
            return 'cashback'
        return None

    def _default_columns(self, x0: float, x1: float) -> dict[str, Any]:
        width = x1 - x0
        return {
            'date': {'x_start': x0, 'x_end': x0 + width * 0.15},
            'description': {'x_start': x0 + width * 0.15, 'x_end': x0 + width * 0.65},
            'amount': {'x_start': x0 + width * 0.65, 'x_end': x1},
        }

    # ========== Amount Structure Analysis (with data row check) ==========
    def _analyze_amount_structure(self, page: Any, bbox: tuple[float, float, float, float], columns: dict[str, dict[str, float]]) -> dict[str, Any]:
        """
        Determine amount structure by scanning a few data rows.
        """
        x0, y0, x1, y1 = bbox
        has_debit = 'debit' in columns
        has_credit = 'credit' in columns
        has_amount = 'amount' in columns

        result = {
            'type': 'unknown',
            'has_debit_column': has_debit,
            'has_credit_column': has_credit,
            'has_amount_column': has_amount,
            'has_dr_cr_indicators': False,
        }

        # If separate debit/credit columns exist
        if has_debit and has_credit:
            result['type'] = 'separate_debit_credit'
            return result

        # Identify the amount column (could be 'amount', 'debit', or 'credit')
        amount_col = None
        if has_amount:
            amount_col = columns['amount']
        elif has_debit:
            amount_col = columns['debit']
        elif has_credit:
            amount_col = columns['credit']
        else:
            return result

        # Scan a few data rows below header for Dr/Cr indicators
        # Take characters in amount column region within first 200px below header
        header_y = self.header_info['y_bottom'] if self.header_info else y0
        scan_end = min(y0 + 200, y1)
        text_in_amount = ""
        for char in page.chars:
            cx = char['x0']
            cy = char.get('top', char.get('y0', 0))
            if (cx >= amount_col['x_start'] and cx <= amount_col['x_end'] and
                cy >= header_y + 5 and cy <= scan_end):
                text_in_amount += char['text']

        text_lower = text_in_amount.lower()
        has_indicators = ('dr' in text_lower or 'cr' in text_lower)

        result['has_dr_cr_indicators'] = has_indicators
        if has_indicators:
            result['type'] = 'single_with_indicator'
        elif has_amount:
            result['type'] = 'single_amount'
        else:
            # If no indicator but we have a debit/credit column, treat as single amount
            result['type'] = 'single_amount'

        return result

    # ========== Metadata Detection ==========
    def _detect_metadata(self, pdf: Any) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        metadata_fields: dict[str, dict[str, Any]] = {}
        metadata_region = None

        for page_num in range(min(2, len(pdf.pages))):
            page = pdf.pages[page_num]
            for field_name, label_aliases in self.METADATA_LABELS.items():
                if field_name in metadata_fields:
                    continue
                for alias in label_aliases:
                    results = page.search(alias, case=False)
                    if not results:
                        continue
                    result = results[0]
                    label_bbox = {
                        'x0': result['x0'], 'x1': result['x1'],
                        'y_top': result['top'], 'y_bottom': result['bottom'],
                    }
                    value_location = self._find_value_near_label(page, label_bbox)
                    if value_location:
                        metadata_fields[field_name] = {
                            'label': alias,
                            'label_location': label_bbox,
                            'value_location': value_location,
                            'page': page_num,
                        }
                        break
            if metadata_fields:
                all_y = [f['label_location']['y_top'] for f in metadata_fields.values()]
                metadata_region = {
                    'page': 0,
                    'y_top': min(all_y) - 10,
                    'y_bottom': max(all_y) + 30,
                }
        return metadata_region, metadata_fields

    def _find_value_near_label(self, page: Any, label_bbox: dict[str, Any]) -> dict[str, Any] | None:
        label_x1 = label_bbox['x1']
        label_y = label_bbox['y_top']
        label_x0 = label_bbox['x0']
        candidates = []
        for char in page.chars:
            if not char['text'].strip():
                continue
            cx = char['x0']
            cy = char.get('top', char.get('y0', 0))
            # right
            if abs(cy - label_y) <= 5 and cx > label_x1 and cx < label_x1 + 200:
                candidates.append({'x': cx, 'y': cy, 'direction': 'right', 'distance': cx - label_x1})
            # below
            if cy > label_y and cy < label_y + 30 and abs(cx - label_x0) <= 50:
                candidates.append({'x': cx, 'y': cy, 'direction': 'below', 'distance': cy - label_y})
        if not candidates:
            return None
        candidates.sort(key=lambda c: c['distance'])
        closest = candidates[0]
        return {
            'x': closest['x'],
            'y': closest['y'],
            'direction': closest['direction'],
            'approximate_x_range': (closest['x'], closest['x'] + 100)
        }

    # ========== Utility ==========
    def _log(self, message: str) -> None:
        if self.debug:
            print(f"[LayoutAnalyzer] {message}")

    def _format_bbox(self, bbox: tuple[Any, ...] | None) -> str:
        if bbox is None:
            return "None"
        return f"({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f})"

    def _build_result(self) -> dict[str, Any]:
        clean_columns: dict[str, dict[str, Any]] = {}
        if self.columns:
            for name, col_def in self.columns.items():
                clean_columns[name] = {
                    'x_start': round(col_def.get('x_start', 0), 1),
                    'x_end': round(col_def.get('x_end', 0), 1),
                }
        clean_metadata: dict[str, dict[str, Any]] = {}
        if self.metadata_fields:
            for field_name, field_info in self.metadata_fields.items():
                clean_metadata[field_name] = {
                    'label': field_info['label'],
                    'page': field_info['page'],
                    'direction': field_info.get('value_location', {}).get('direction', 'unknown'),
                }
        return {
            "bank": self.bank,
            "table_bbox": [round(v, 1) for v in self.table_bbox] if self.table_bbox else None,
            "table_pages": self.table_pages,
            "columns": clean_columns,
            "column_labels": self.column_labels,
            "amount_structure": self.amount_structure,
            "metadata_region": self.metadata_region,
            "metadata_fields": clean_metadata,
            "header_info": {
                "page": self.header_info['page'],
                "y": round(self.header_info['y'], 1),
                "anchors_found": self.header_info['anchors'],
                "score": self.header_info['score'],
            } if self.header_info else None,
        }

    # ========== Debug Visualization ==========
    def generate_debug_image(self, output_dir: str = 'debug') -> None:
        Path(output_dir).mkdir(exist_ok=True)
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in (self.table_pages or [0]):
                if page_num >= len(pdf.pages):
                    continue
                page = pdf.pages[page_num]
                im = page.to_image(resolution=150)
                if self.table_bbox:
                    x0, y0, x1, y1 = self.table_bbox
                    # Ensure y0 < y1 (swap if inverted)
                    if y1 < y0:
                        y0, y1 = y1, y0
                    if y1 > y0:  # Only draw if valid
                        im.draw_rect((x0, y0, x1, y1), stroke="red", stroke_width=3)
                if self.columns and self.table_bbox:
                    bx0, by0, bx1, by1 = self.table_bbox
                    if by1 < by0:
                        by0, by1 = by1, by0
                    for _col_name, col_def in self.columns.items():
                        x = col_def['x_start']
                        # draw_line expects list of (x, y) coordinate pairs
                        im.draw_line([(x, by0), (x, by1)], stroke="blue", stroke_width=2)
                if self.header_info and page_num == self.header_info['page']:
                    hy = self.header_info['y']
                    im.draw_line([(0, hy), (page.width, hy)], stroke="green", stroke_width=2)
                output_path = f"{output_dir}/{Path(self.pdf_path).stem}_page{page_num + 1}.png"
                im.save(output_path)
                print(f"✅ Debug image saved: {output_path}")


def analyze_pdf(pdf_path: str, debug: bool = False) -> dict[str, Any]:
    analyzer = LayoutAnalyzer(pdf_path, debug=debug)
    result = analyzer.analyze()
    if debug:
        analyzer.generate_debug_image()
    return result


def main() -> None:
    import sys
    if len(sys.argv) < 2:
        print("Usage: python layout_analyzer.py <pdf_path> [--debug]")
        print("       python layout_analyzer.py --all [--debug]")
        sys.exit(1)

    debug = "--debug" in sys.argv

    if sys.argv[1] == "--all":
        test_dir = Path("../backup-core/test/statements")
        if not test_dir.exists():
            print(f"Test directory not found: {test_dir}")
            sys.exit(1)
        results = {}
        for pdf_file in sorted(test_dir.glob("*.pdf")):
            print(f"\n{'='*60}\nAnalyzing: {pdf_file.name}\n{'='*60}")
            result = analyze_pdf(str(pdf_file), debug=debug)
            results[pdf_file.name] = result
            cols = list(result.get('columns', {}).keys())
            pages = result.get('table_pages', [])
            print(f"  Bank: {result['bank']}")
            print(f"  Columns: {cols}")
            print(f"  Pages: {pages}")
            print(f"  Amount: {result.get('amount_structure', {}).get('type', 'unknown')}")
            print(f"  Metadata: {len(result.get('metadata_fields', {}))} fields found")
        with open('layout_analysis_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\n💾 All results saved to layout_analysis_results.json")
    else:
        pdf_path = sys.argv[1]
        result = analyze_pdf(pdf_path, debug=debug)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
