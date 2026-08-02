"""Extraction package for PDF and CSV processing.

This package contains all extraction-related modules:
- camelot_extractor: Camelot-based PDF table extraction
- hybrid_extractor: Hybrid layout-aware PDF extraction
- statement_extractor: Legacy statement extraction (moved from root)
- categorizer: Transaction categorization (moved from root)
- metadata_extractor: Statement metadata extraction (moved from root)
- transaction_parser: Transaction parsing (moved from root)
- column_mapper: CSV column mapping (moved from root)
- validator: Data validation (moved from root)
- table_extractor: Table extraction utilities (moved from root)
- csv_importer: CSV/Excel import pipeline (moved from root)
"""

# Re-export for backward compatibility
from .camelot_extractor import CamelotExtractor
from .categorizer import categorize
from .column_mapper import ColumnMapper
from .csv_importer import CSVImporter
from .hybrid_extractor import HybridExtractor
from .metadata_extractor import MetadataExtractor
from .statement_extractor import StatementExtractor
from .table_extractor import TableExtractor
from .transaction_parser import TransactionParser
from .validator import validate_file_upload, validate_paise_amount

__all__ = [
    "CamelotExtractor",
    "HybridExtractor",
    "StatementExtractor",
    "categorize",
    "MetadataExtractor",
    "TransactionParser",
    "ColumnMapper",
    "validate_file_upload",
    "validate_paise_amount",
    "TableExtractor",
    "CSVImporter",
]
