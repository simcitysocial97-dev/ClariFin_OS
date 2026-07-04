"""
Bank Detector Module
====================
Deterministic bank detection from extracted text.

This module provides robust keyword-based detection for common Indian banks
without requiring ML or fragile PDF structure parsing.

Usage:
    from extraction.bank_detector import detect_bank_from_text, extract_text_from_pdf
    
    text = extract_text_from_pdf(pdf_path, max_pages=3)
    bank = detect_bank_from_text(text)  # Returns "HDFC Bank" | "Axis Bank" | "SBI Card" | None
"""

import re
from typing import Optional
from pathlib import Path


# Bank detection patterns with keywords and canonical names
BANK_PATTERNS = {
    "HDFC Bank": {
        "keywords": [
            "HDFC Bank",
            "HDFC BANK",
            "Housing Development Finance Corporation",
            "HDFC",
        ],
        "priority": 1,  # Higher priority for specific matches
    },
    "Axis Bank": {
        "keywords": [
            "Axis Bank",
            "AXIS BANK",
            "UTIB",  # Axis Bank's IFSC code prefix
            "AXIS",
        ],
        "priority": 1,
    },
    "SBI Card": {
        "keywords": [
            "State Bank of India",
            "STATE BANK OF INDIA",
            "SBI Card",
            "SBI CARD",
            "SBICARD",
            "SBI",
        ],
        "priority": 1,
    },
    "ICICI Bank": {
        "keywords": [
            "ICICI Bank",
            "ICICI BANK",
            "ICICI",
        ],
        "priority": 1,
    },
    "IDFC First Bank": {
        "keywords": [
            "IDFC FIRST Bank",
            "IDFC First Bank",
            "IDFC FIRST BANK",
            "IDFC FIRST",
            "IDFC",
        ],
        "priority": 1,
    },
    "IndusInd Bank": {
        "keywords": [
            "IndusInd Bank",
            "INDUSIND BANK",
            "IndusInd",
            "INDUSIND",
        ],
        "priority": 1,
    },
}


def normalize_text(text: str) -> str:
    """
    Normalize text for matching:
    - Convert to uppercase
    - Normalize whitespace (multiple spaces/tabs/newlines → single space)
    - Strip leading/trailing whitespace
    """
    if not text:
        return ""
    # Convert to uppercase
    text = text.upper()
    # Normalize whitespace: any whitespace sequence → single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing
    return text.strip()


def detect_bank_from_text(text: str) -> Optional[str]:
    """
    Detect bank name from extracted text using keyword matching.
    
    Args:
        text: Raw or extracted text from PDF (first few pages)
        
    Returns:
        Canonical bank name (e.g., "HDFC Bank", "Axis Bank", "SBI Card") 
        or None if no bank detected
        
    Detection Strategy:
        1. Normalize text (uppercase, collapse whitespace)
        2. For each bank, check if ANY keyword appears as substring
        3. Return the first match (banks are checked in priority order)
        
    Examples:
        >>> detect_bank_from_text("HDFC Bank Statement for July 2025")
        'HDFC Bank'
        >>> detect_bank_from_text("UTIB0001234 - Axis Bank Account")
        'Axis Bank'
        >>> detect_bank_from_text("State Bank of India Credit Card")
        'SBI Card'
        >>> detect_bank_from_text("Random text without bank names")
        None
    """
    if not text or not isinstance(text, str):
        return None
    
    normalized = normalize_text(text)
    if not normalized:
        return None
    
    # Sort banks by priority (higher priority first), then by name for determinism
    sorted_banks = sorted(
        BANK_PATTERNS.items(),
        key=lambda x: (-x[1]["priority"], x[0])
    )
    
    for bank_name, config in sorted_banks:
        for keyword in config["keywords"]:
            # Normalize keyword the same way
            normalized_keyword = normalize_text(keyword)
            if normalized_keyword in normalized:
                return bank_name
    
    return None


def extract_text_from_pdf(pdf_path: str, max_pages: int = 3) -> str:
    """
    Extract text from first N pages of PDF using pdfplumber.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to extract (default 3)
        
    Returns:
        Concatenated text from all extracted pages
        
    Raises:
        ImportError: If pdfplumber is not installed
        FileNotFoundError: If PDF file doesn't exist
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    try:
        import pdfplumber
    except ImportError as e:
        raise ImportError(
            "pdfplumber is required for text extraction. "
            "Install with: pip install pdfplumber"
        ) from e
    
    text_parts = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages[:max_pages]):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return "\n".join(text_parts)


def detect_bank_from_pdf(pdf_path: str, max_pages: int = 3) -> Optional[str]:
    """
    Convenience function: extract text from PDF and detect bank.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum number of pages to extract
        
    Returns:
        Canonical bank name or None if not detected
        
    Raises:
        ImportError: If pdfplumber is not installed
        FileNotFoundError: If PDF file doesn't exist
    """
    text = extract_text_from_pdf(pdf_path, max_pages)
    return detect_bank_from_text(text)


# Backward compatibility alias for existing code
BankDetector = detect_bank_from_text