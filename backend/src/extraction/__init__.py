"""
Extraction Module
=================
Pluggable PDF extraction for bank statements.

This module provides a common interface for extracting transaction data
from bank statement PDFs using different backends (legacy Camelot-based
or Docling AI-powered).

Quick Start:
    from src.extraction import get_extractor
    
    extractor = get_extractor()
    result = extractor.extract("/path/to/statement.pdf")
    
    print(f"Bank: {result.bank}")
    print(f"Transactions: {len(result.normalized_rows)}")

Configuration:
    Set CLARIFIN_EXTRACTOR environment variable:
    - "legacy" (default): Camelot-based extraction
    - "docling": AI-powered extraction (requires docling package)
"""

from .base_extractor import (
    ExtractedStatement,
    ExtractorProtocol,
    ExtractionError,
)

from .factory import (
    get_extractor,
    get_extractor_type,
    is_extractor_available,
    list_available_extractors,
    EXTRACTOR_ENV_VAR,
    DEFAULT_EXTRACTOR,
)

__all__ = [
    # Base types
    "ExtractedStatement",
    "ExtractorProtocol",
    "ExtractionError",
    
    # Factory functions
    "get_extractor",
    "get_extractor_type",
    "is_extractor_available",
    "list_available_extractors",
    
    # Balance extraction helpers
    "extract_opening_closing_from_text",
    "extract_opening_balance_from_text",
    "extract_closing_balance_from_text",
    
    # Constants
    "EXTRACTOR_ENV_VAR",
    "DEFAULT_EXTRACTOR",
]

# Import balance extraction helpers for convenient access
from .balance_extractor import (
    extract_opening_closing_from_text,
    extract_opening_balance_from_text,
    extract_closing_balance_from_text,
)
