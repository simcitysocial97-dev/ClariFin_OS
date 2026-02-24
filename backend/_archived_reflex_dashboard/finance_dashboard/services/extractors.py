"""Extractors service wrapper.

Provides clean import path to extraction modules from the src directory.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
_SRC_DIR = str(Path(__file__).resolve().parent.parent.parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from statement_extractor import StatementExtractor as _StatementExtractor
from categorizer import categorize as _categorize
from metadata_extractor import MetadataExtractor as _MetadataExtractor

# Re-export
StatementExtractor = _StatementExtractor
categorize = _categorize
MetadataExtractor = _MetadataExtractor