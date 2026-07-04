"""
BBox-Based Table Extractor
==========================
Extracts transaction tables from PDF statements using bounding box coordinates.

Supports:
- Normalized bbox coordinates (0-1 range, top-left origin)
- PDF coordinate conversion (bottom-left origin)
- Multi-page extraction with apply_to_all_pages option
- Column validation for required fields

Example:
    from src.extraction.bbox_extractor import extract_with_bbox
    
    result = extract_with_bbox(
        pdf_path="statement.pdf",
        bboxes_norm=[{"page_number": 1, "x0": 0.1, "y0": 0.2, "x1": 0.9, "y1": 0.8}],
        apply_to_all_pages=True
    )
    # Returns list of normalized transaction rows
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import pdfplumber

from src.logger import log
from src.utils import parse_date_to_iso


class BboxExtractionError(Exception):
    """Raised when bbox extraction fails."""
    pass


class ColumnValidationError(BboxExtractionError):
    """Raised when required columns are not detected."""
    pass


def convert_bbox_norm_to_pdf_coords(
    bbox_norm: List[float],
    page_width: float,
    page_height: float
) -> Tuple[float, float, float, float]:
    """
    Convert normalized bbox (top-left origin) to PDF coordinates (bottom-left origin).
    
    Normalized coordinates (top-left origin):
        - x0, y0: top-left corner (0,0 = top-left, 1,1 = bottom-right)
        - x1, y1: bottom-right corner
    
    PDF coordinates (bottom-left origin):
        - (0, 0) = bottom-left of page
        - y increases upward
    
    Args:
        bbox_norm: Normalized bbox [x0, y0, x1, y1] in range [0, 1]
        page_width: Page width in PDF points
        page_height: Page height in PDF points
    
    Returns:
        Tuple of (x0, y0, x1, y1) in PDF coordinates
    
    Example:
        >>> convert_bbox_norm_to_pdf_coords([0.1, 0.2, 0.9, 0.8], 595, 842)
        (59.5, 168.4, 535.5, 673.6)
    """
    if len(bbox_norm) != 4:
        raise ValueError(f"bbox_norm must have 4 elements, got {len(bbox_norm)}")
    
    nx0, ny0, nx1, ny1 = bbox_norm
    
    # Validate normalized coordinates
    if not all(0 <= v <= 1 for v in bbox_norm):
        raise ValueError(f"bbox_norm values must be in range [0, 1], got {bbox_norm}")
    
    # Convert x coordinates (same in both systems, just scale)
    x0 = nx0 * page_width
    x1 = nx1 * page_width
    
    # Convert y coordinates (flip for top-left to bottom-left)
    # ny0 is distance from top, so pdf_y1 = page_height - (ny0 * page_height)
    # ny1 is distance from top to bottom, so pdf_y0 = page_height - (ny1 * page_height)
    y1 = page_height - (ny0 * page_height)  # top becomes bottom
    y0 = page_height - (ny1 * page_height)  # bottom becomes top
    
    # Ensure proper ordering (x0 < x1, y0 < y1)
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    
    return (x0, y0, x1, y1)


def convert_bbox_pdf_to_norm_coords(
    bbox_pdf: Tuple[float, float, float, float],
    page_width: float,
    page_height: float
) -> List[float]:
    """
    Convert PDF coordinates (bottom-left origin) to normalized bbox (top-left origin).
    
    Args:
        bbox_pdf: PDF bbox (x0, y0, x1, y1) in points
        page_width: Page width in PDF points
        page_height: Page height in PDF points
    
    Returns:
        Normalized bbox [x0, y0, x1, y1] in range [0, 1]
    
    Example:
        >>> convert_bbox_pdf_to_norm_coords((59.5, 168.4, 535.5, 673.6), 595, 842)
        [0.1, 0.2, 0.9, 0.8]
    """
    x0, y0, x1, y1 = bbox_pdf
    
    # Convert x coordinates
    nx0 = x0 / page_width
    nx1 = x1 / page_width
    
    # Convert y coordinates (flip for bottom-left to top-left)
    ny0 = (page_height - y1) / page_height  # pdf y1 (top) becomes norm y0 (top)
    ny1 = (page_height - y0) / page_height  # pdf y0 (bottom) becomes norm y1 (bottom)
    
    return [round(nx0, 6), round(ny0, 6), round(nx1, 6), round(ny1, 6)]


def _detect_columns(rows: List[List[Any]]) -> Dict[str, int]:
    """
    Detect column indices for date, description, debit, credit, balance.
    
    Args:
        rows: List of table rows (each row is a list of cell values)
    
    Returns:
        Dict mapping column name to index, e.g., {'date': 0, 'description': 1, ...}
    """
    if not rows:
        return {}
    
    # Use first row as header for detection
    header = [str(cell).lower().strip() if cell else "" for cell in rows[0]]
    
    column_map = {}
    
    # Date column detection
    date_patterns = ['date', 'dt', 'day', 'transaction date', 'txn date', 'value date']
    for i, col in enumerate(header):
        if any(pattern in col for pattern in date_patterns):
            column_map['date'] = i
            break
    
    # If no header match, try first column for date
    if 'date' not in column_map and len(rows) > 1:
        # Check if first column looks like dates
        sample = str(rows[1][0]) if len(rows[1]) > 0 else ""
        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', sample):
            column_map['date'] = 0
    
    # Description column detection - do this BEFORE debit/credit to avoid 'cr' matching Description
    desc_patterns = ['description', 'particulars', 'details', 'narration', 'transaction details', 'particular']
    for i, col in enumerate(header):
        if any(pattern in col for pattern in desc_patterns):
            column_map['description'] = i
            break
    
    # If no header match, try to find longest text column
    if 'description' not in column_map and len(rows) > 1:
        max_len_idx = 0
        max_len = 0
        for i in range(len(header)):
            if i < len(rows[1]):
                cell_len = len(str(rows[1][i]))
                if cell_len > max_len:
                    max_len = cell_len
                    max_len_idx = i
        column_map['description'] = max_len_idx
    
    # Debit column detection - use word boundaries to avoid partial matches
    debit_patterns = ['debit', 'withdrawal', 'dr', 'out', 'outflow', 'debit amount']
    for i, col in enumerate(header):
        # Skip if already assigned to description
        if i == column_map.get('description'):
            continue
        # Use word boundary matching for short patterns like 'dr'
        for pattern in debit_patterns:
            if pattern in col:
                if len(pattern) <= 2:
                    # For short patterns, require word boundaries or exact match
                    if col == pattern or f' {pattern} ' in f' {col} ' or col.startswith(pattern + ' ') or col.endswith(' ' + pattern):
                        column_map['debit'] = i
                        break
                else:
                    column_map['debit'] = i
                    break
        if 'debit' in column_map:
            break
    
    # Credit column detection - use word boundaries to avoid partial matches
    credit_patterns = ['credit', 'deposit', 'cr', 'in', 'inflow', 'credit amount']
    for i, col in enumerate(header):
        # Skip if already assigned
        if i == column_map.get('description') or i == column_map.get('debit'):
            continue
        # Use word boundary matching for short patterns like 'cr'
        for pattern in credit_patterns:
            if pattern in col:
                if len(pattern) <= 2:
                    # For short patterns, require word boundaries or exact match
                    if col == pattern or f' {pattern} ' in f' {col} ' or col.startswith(pattern + ' ') or col.endswith(' ' + pattern):
                        column_map['credit'] = i
                        break
                else:
                    column_map['credit'] = i
                    break
        if 'credit' in column_map:
            break
    
    # Balance column detection (optional)
    balance_patterns = ['balance', 'closing', 'running', 'balance amount']
    for i, col in enumerate(header):
        # Skip if already assigned
        if i == column_map.get('description') or i == column_map.get('debit') or i == column_map.get('credit'):
            continue
        if any(pattern in col for pattern in balance_patterns):
            column_map['balance'] = i
            break
    
    return column_map


def _parse_amount_to_paise(amount_str: Any) -> int:
    """
    Parse amount string to paise (integer).
    
    Args:
        amount_str: Amount as string, number, or None
    
    Returns:
        Amount in paise (integer)
    """
    if amount_str is None:
        return 0
    
    # Convert to string and clean
    amount_str = str(amount_str).strip()
    
    # Handle CR/DR suffixes first (before removing other letters)
    amount_lower = amount_str.lower()
    is_credit = 'cr' in amount_lower
    is_debit = 'dr' in amount_lower
    
    # Remove currency symbols and text patterns (NOTE: preserve decimal point!)
    # Remove: Rs., Rs, $, €, £, commas, whitespace, and CR/DR suffixes
    amount_str = re.sub(r'Rs\.|Rs|[$€£,\s]', '', amount_str, flags=re.IGNORECASE)
    amount_str = re.sub(r'[crCRdrDR]', '', amount_str)
    
    # Handle parentheses for negative (e.g., "(100.50)")
    if amount_str.startswith('(') and amount_str.endswith(')'):
        amount_str = '-' + amount_str[1:-1]
    
    try:
        amount_float = float(amount_str) if amount_str else 0.0
        paise = int(round(abs(amount_float) * 100))
        
        # Return negative for debits if marked
        if is_debit and not is_credit:
            return -paise
        return paise
    except (ValueError, TypeError):
        return 0


def _normalize_row(
    row: List[Any],
    column_map: Dict[str, int],
    has_separate_debit_credit: bool
) -> Optional[Dict[str, Any]]:
    """
    Normalize a single row to standard format.
    
    Args:
        row: Raw row data
        column_map: Column name to index mapping
        has_separate_debit_credit: Whether debit and credit are separate columns
    
    Returns:
        Normalized row dict or None if invalid
    """
    if not row:
        return None
    
    # Get date
    date_idx = column_map.get('date')
    if date_idx is None or date_idx >= len(row):
        return None
    
    date_str = str(row[date_idx]).strip()
    if not date_str or date_str.lower() in ['date', '']:
        return None
    
    # Get description
    desc_idx = column_map.get('description', 1)
    description = str(row[desc_idx]).strip() if desc_idx < len(row) else ""
    
    # Get amounts
    debit_paise = 0
    credit_paise = 0
    
    if has_separate_debit_credit:
        # Separate debit and credit columns
        debit_idx = column_map.get('debit')
        credit_idx = column_map.get('credit')
        
        if debit_idx is not None and debit_idx < len(row):
            amount = _parse_amount_to_paise(row[debit_idx])
            if amount < 0:
                debit_paise = abs(amount)
            else:
                debit_paise = amount
        
        if credit_idx is not None and credit_idx < len(row):
            amount = _parse_amount_to_paise(row[credit_idx])
            if amount < 0:
                credit_paise = abs(amount)
            else:
                credit_paise = amount
    else:
        # Single amount column with type indicator or sign
        amount_idx = column_map.get('debit') or column_map.get('credit')
        if amount_idx is not None and amount_idx < len(row):
            amount = _parse_amount_to_paise(row[amount_idx])
            if amount < 0:
                credit_paise = abs(amount)
            else:
                debit_paise = amount
    
    # Get balance (optional)
    balance_paise = None
    balance_idx = column_map.get('balance')
    if balance_idx is not None and balance_idx < len(row):
        balance_paise = abs(_parse_amount_to_paise(row[balance_idx]))
    
    return {
        'date': date_str,
        'date_iso': parse_date_to_iso(date_str),
        'description': description,
        'debit_paise': debit_paise,
        'credit_paise': credit_paise,
        'balance_paise': balance_paise,
        'raw': [str(cell) for cell in row],
    }


def _validate_required_columns(normalized_rows: List[Dict[str, Any]]) -> None:
    """
    Validate that extracted rows have required columns.
    
    Required:
    - date
    - description
    - Either debit or credit (at least one must be non-zero)
    
    Raises:
        ColumnValidationError: If required columns are missing
    """
    if not normalized_rows:
        raise ColumnValidationError("No rows extracted from bbox")
    
    # Check for date and description
    sample = normalized_rows[0]
    if not sample.get('date'):
        raise ColumnValidationError("Could not detect date column; adjust bbox")
    
    if not sample.get('description'):
        raise ColumnValidationError("Could not detect description column; adjust bbox")
    
    # Check that at least some rows have amounts
    has_amounts = any(
        r.get('debit_paise', 0) > 0 or r.get('credit_paise', 0) > 0
        for r in normalized_rows
    )
    
    if not has_amounts:
        raise ColumnValidationError("Could not detect amount columns (debit/credit); adjust bbox")


def _is_valid_extraction(rows: List[List[Any]]) -> bool:
    """Check if extracted rows look like transaction data."""
    if not rows or len(rows) < 2:  # At least header + 1 data row
        return False
    
    # Check for date pattern in first column
    date_pattern = re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}')
    data_rows = rows[1:]  # Skip header
    
    date_matches = sum(1 for row in data_rows if row and date_pattern.search(str(row[0])))
    return date_matches >= len(data_rows) * 0.3  # At least 30% have dates


def _extract_with_camelot(
    pdf_path: str,
    page_number: int,
    bbox_pdf: Tuple[float, float, float, float],
    flavor: str = "lattice"
) -> List[List[Any]]:
    """
    Try to extract table using Camelot with bbox constraint.
    
    Args:
        pdf_path: Path to PDF file
        page_number: 1-indexed page number
        bbox_pdf: Bounding box in PDF coordinates (x0, y0, x1, y1)
        flavor: "lattice" for grid-based or "stream" for gridless
    
    Returns:
        List of table rows or empty list if extraction fails
    """
    try:
        import camelot
        
        # Convert bbox to table_areas format: x1,y1,x2,y2
        x0, y0, x1, y1 = bbox_pdf
        table_area = f"{x0},{y0},{x1},{y1}"
        
        tables = camelot.read_pdf(
            pdf_path,
            pages=str(page_number),
            flavor=flavor,
            table_areas=[table_area],
            suppress_stdout=True
        )
        
        if tables and len(tables) > 0:
            # Return the first table's data as list of lists
            return tables[0].df.values.tolist()
            
    except ImportError:
        log.debug("Camelot not installed, skipping %s extraction", flavor)
    except Exception as e:
        log.debug("Camelot %s extraction failed: %s", flavor, str(e))
    
    return []


def extract_table_from_page(
    page,
    bbox_pdf: Tuple[float, float, float, float],
    pdf_path: Optional[str] = None
) -> List[List[Any]]:
    """
    Extract table from a PDF page within the given bbox.
    
    Fallback order:
    1. pdfplumber "lines" strategy (fastest, good for structured tables)
    2. Camelot "lattice" flavor (best for grid-based bank PDFs)
    3. Camelot "stream" flavor (best for gridless PDFs)
    4. pdfplumber "text" strategy (fallback for messy layouts)
    5. Simple text splitting (last resort)
    
    Args:
        page: pdfplumber page object
        bbox_pdf: Bounding box in PDF coordinates (x0, y0, x1, y1)
        pdf_path: Optional PDF path for Camelot fallback
    
    Returns:
        List of table rows (each row is a list of cell values)
    """
    # Crop to bbox
    cropped = page.crop(bbox_pdf)
    
    # 1. Try pdfplumber with lines strategy
    table = cropped.extract_table({
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "intersection_tolerance": 5,
        "snap_tolerance": 3,
        "join_tolerance": 3,
    })
    
    if table and _is_valid_extraction(table):
        log.debug("Extracted using pdfplumber lines strategy")
        return table
    
    # 2. Try Camelot lattice (grid-based PDFs)
    if pdf_path:
        camelot_rows = _extract_with_camelot(pdf_path, page.page_number, bbox_pdf, flavor="lattice")
        if camelot_rows and _is_valid_extraction(camelot_rows):
            log.debug("Extracted using Camelot lattice")
            return camelot_rows
    
    # 3. Try Camelot stream (gridless PDFs)
    if pdf_path:
        camelot_rows = _extract_with_camelot(pdf_path, page.page_number, bbox_pdf, flavor="stream")
        if camelot_rows and _is_valid_extraction(camelot_rows):
            log.debug("Extracted using Camelot stream")
            return camelot_rows
    
    # 4. Fallback: pdfplumber text strategy
    table = cropped.extract_table({
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
        "intersection_tolerance": 5,
        "snap_tolerance": 3,
    })
    
    if table and _is_valid_extraction(table):
        log.debug("Extracted using pdfplumber text strategy")
        return table
    
    # If we have any table from earlier attempts, use it even if validation fails
    if table:
        return table
    
    # 5. Final fallback: extract text and split by lines
    text = cropped.extract_text()
    if text:
        lines = text.strip().split('\n')
        # Try to split each line by common delimiters
        rows = []
        for line in lines:
            # Split by 2+ spaces or tabs
            cells = re.split(r'\s{2,}|\t', line.strip())
            if cells:
                rows.append(cells)
        if rows:
            log.debug("Extracted using text splitting fallback")
            return rows
    
    return []


def extract_with_bbox(
    pdf_path: str,
    bboxes_norm: List[Dict[str, Any]],
    apply_to_all_pages: bool = False
) -> List[Dict[str, Any]]:
    """
    Extract transactions from PDF using bounding box(es).
    
    Args:
        pdf_path: Path to the PDF file
        bboxes_norm: List of bbox dicts with keys:
            - page_number: int (1-indexed)
            - x0, y0, x1, y1: float (normalized 0-1 coordinates, top-left origin)
        apply_to_all_pages: If True, apply the bbox from page 1 to all pages
    
    Returns:
        List of normalized transaction rows
    
    Raises:
        BboxExtractionError: If PDF cannot be opened
        ColumnValidationError: If required columns not detected
    
    Example:
        >>> result = extract_with_bbox(
        ...     "statement.pdf",
        ...     [{"page_number": 1, "x0": 0.1, "y0": 0.2, "x1": 0.9, "y1": 0.8}],
        ...     apply_to_all_pages=True
        ... )
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise BboxExtractionError(f"PDF not found: {pdf_path}")
    
    if not bboxes_norm:
        raise BboxExtractionError("No bboxes provided")
    
    all_normalized_rows = []
    
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            if not pdf.pages:
                raise BboxExtractionError(f"PDF has no pages: {pdf_path}")
            
            # Get first bbox for template (for apply_to_all_pages)
            first_bbox = bboxes_norm[0]
            
            for page_num, page in enumerate(pdf.pages, start=1):
                # Determine which bbox to use for this page
                bbox_norm = None
                
                if apply_to_all_pages:
                    # Use first bbox template for all pages
                    bbox_norm = [
                        first_bbox['x0'],
                        first_bbox['y0'],
                        first_bbox['x1'],
                        first_bbox['y1']
                    ]
                else:
                    # Find bbox for this specific page
                    for bb in bboxes_norm:
                        if bb.get('page_number') == page_num:
                            bbox_norm = [bb['x0'], bb['y0'], bb['x1'], bb['y1']]
                            break
                
                if bbox_norm is None:
                    log.debug("No bbox defined for page %d, skipping", page_num)
                    continue
                
                # Convert to PDF coordinates
                page_width = float(page.width)
                page_height = float(page.height)
                bbox_pdf = convert_bbox_norm_to_pdf_coords(bbox_norm, page_width, page_height)
                
                log.debug(
                    "Extracting from page %d with bbox PDF coords: %s",
                    page_num, bbox_pdf
                )
                
                # Extract table (pass pdf_path for Camelot fallback)
                rows = extract_table_from_page(page, bbox_pdf, str(pdf_path))
                
                if not rows:
                    log.warning("No table extracted from page %d", page_num)
                    continue
                
                # Detect columns from first row (header)
                column_map = _detect_columns(rows)
                log.debug("Detected columns: %s", column_map)
                
                # Determine if we have separate debit/credit columns
                has_separate = 'debit' in column_map and 'credit' in column_map
                
                # Normalize rows (skip header)
                for row in rows[1:]:
                    normalized = _normalize_row(row, column_map, has_separate)
                    if normalized:
                        normalized['page_number'] = page_num
                        all_normalized_rows.append(normalized)
        
        # Validate we got required columns
        _validate_required_columns(all_normalized_rows)
        
        log.info(
            "BBox extraction complete: %d rows from %d pages",
            len(all_normalized_rows),
            len(set(r.get('page_number', 1) for r in all_normalized_rows))
        )
        
        return all_normalized_rows
        
    except pdfplumber.PDFSyntaxError as e:
        raise BboxExtractionError(f"Invalid PDF format: {e}") from e
    except Exception as e:
        if isinstance(e, (BboxExtractionError, ColumnValidationError)):
            raise
        raise BboxExtractionError(f"Extraction failed: {e}") from e


def get_page_dimensions(pdf_path: str) -> List[Dict[str, float]]:
    """
    Get dimensions of all pages in a PDF.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of dicts with page_number, width, height
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise BboxExtractionError(f"PDF not found: {pdf_path}")
    
    dimensions = []
    
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                dimensions.append({
                    'page_number': page_num,
                    'width': float(page.width),
                    'height': float(page.height),
                })
    except Exception as e:
        raise BboxExtractionError(f"Failed to read PDF dimensions: {e}") from e
    
    return dimensions


# Export public API
__all__ = [
    'convert_bbox_norm_to_pdf_coords',
    'convert_bbox_pdf_to_norm_coords',
    'extract_with_bbox',
    'get_page_dimensions',
    'BboxExtractionError',
    'ColumnValidationError',
]