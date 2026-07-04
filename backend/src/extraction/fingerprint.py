"""
PDF Layout Fingerprinting Module
================================
Deterministic fingerprinting for PDF statement layouts.

Used to identify and match similar statement layouts for template reuse.

Example:
    from src.extraction.fingerprint import compute_fingerprint
    
    fingerprint = compute_fingerprint("/path/to/statement.pdf", bank_hint="HDFC Bank")
    # Returns: "a1b2c3d4..." (64-char hex SHA256)
"""

import hashlib
from pathlib import Path
from typing import Optional

from src.logger import log


def _extract_page_dimensions(page) -> tuple[float, float]:
    """Extract page width and height from pdfplumber page."""
    return float(page.width), float(page.height)


def _extract_header_text(page, header_ratio: float = 0.15, max_chars: int = 200) -> str:
    """
    Extract text from the top header region of a page.
    
    Args:
        page: pdfplumber page object
        header_ratio: Percentage of page height to consider as header (default 15%)
        max_chars: Maximum characters to extract (default 200)
    
    Returns:
        Normalized header text string
    """
    # Get page dimensions
    width, height = _extract_page_dimensions(page)
    
    # Define header bbox: full width, top portion
    header_bbox = (0, 0, width, height * header_ratio)
    
    # Crop and extract text
    header_crop = page.crop(header_bbox)
    text = header_crop.extract_text() or ""
    
    # Normalize: uppercase, collapse whitespace
    text = text.upper()
    text = " ".join(text.split())  # Collapse all whitespace to single spaces
    
    return text[:max_chars].strip()


def compute_fingerprint(
    pdf_path: str | Path,
    bank_hint: Optional[str] = None
) -> str:
    """
    Compute a deterministic fingerprint for a PDF statement layout.
    
    The fingerprint is based on:
    - First page width and height (PDF points)
    - Top header text tokens (first N chars from top 15% region)
    - Optional bank hint (e.g., "HDFC Bank")
    
    Args:
        pdf_path: Path to the PDF file
        bank_hint: Optional bank name hint to include in fingerprint
    
    Returns:
        64-character hexadecimal SHA256 hash string
    
    Example:
        >>> compute_fingerprint("statement.pdf", bank_hint="HDFC Bank")
        'a1b2c3d4e5f6...'  # 64 chars
    """
    import pdfplumber
    
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    with pdfplumber.open(str(pdf_path)) as pdf:
        if not pdf.pages:
            raise ValueError(f"PDF has no pages: {pdf_path}")
        
        first_page = pdf.pages[0]
        
        # Extract page dimensions
        page_width, page_height = _extract_page_dimensions(first_page)
        
        # Extract header text
        header_text = _extract_header_text(first_page)
        
        # Build normalized fingerprint input
        components = [
            f"page_width:{page_width:.2f}",
            f"page_height:{page_height:.2f}",
            f"header_text:{header_text}",
            f"bank_hint:{(bank_hint or '').upper()}",
        ]
        
        fingerprint_input = "|".join(components)
        
        # Compute SHA256 hash
        fingerprint = hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
        
        log.debug(
            "Computed fingerprint for %s: %s... (input: %r)",
            pdf_path.name,
            fingerprint[:16],
            fingerprint_input[:100],
        )
        
        return fingerprint


def compute_fingerprint_from_components(
    page_width: float,
    page_height: float,
    header_text: str,
    bank_hint: Optional[str] = None
) -> str:
    """
    Compute fingerprint from raw components (useful for testing).
    
    This allows testing without needing actual PDF files.
    
    Args:
        page_width: Page width in PDF points
        page_height: Page height in PDF points  
        header_text: Header text to include
        bank_hint: Optional bank name hint
    
    Returns:
        64-character hexadecimal SHA256 hash string
    """
    # Normalize inputs
    header_text = header_text.upper()
    header_text = " ".join(header_text.split())[:200].strip()
    
    components = [
        f"page_width:{page_width:.2f}",
        f"page_height:{page_height:.2f}",
        f"header_text:{header_text}",
        f"bank_hint:{(bank_hint or '').upper()}",
    ]
    
    fingerprint_input = "|".join(components)
    fingerprint = hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
    
    return fingerprint


# Export public API
__all__ = [
    "compute_fingerprint",
    "compute_fingerprint_from_components",
]