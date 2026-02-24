"""Services module for finance dashboard.

This module provides clean imports to the extraction pipeline
without requiring sys.path manipulation.
"""

from .db import FinanceDB, get_db_path
from .extractors import StatementExtractor, categorize, MetadataExtractor

__all__ = [
    "FinanceDB",
    "get_db_path",
    "StatementExtractor",
    "categorize",
    "MetadataExtractor",
]