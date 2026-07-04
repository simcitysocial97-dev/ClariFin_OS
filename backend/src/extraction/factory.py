"""
Extractor Factory
=================
Factory module for creating extractor instances.

The factory provides a LegacyExtractor (Camelot-based) for PDF extraction.

Usage:
    from src.extraction.factory import get_extractor, get_extractor_type
    
    # Get extractor instance
    extractor = get_extractor()
    result = extractor.extract("/path/to/statement.pdf")
    
    # Check current extractor type
    extractor_type = get_extractor_type()  # Always "legacy"
"""

import os
import logging
from typing import Union

from .base_extractor import ExtractorProtocol

logger = logging.getLogger(__name__)

# Environment variable name for extractor selection (kept for compatibility)
EXTRACTOR_ENV_VAR = "CLARIFIN_EXTRACTOR"

# Only legacy extractor is supported
DEFAULT_EXTRACTOR = "legacy"


def get_extractor_type() -> str:
    """
    Get the currently configured extractor type.
    
    Returns:
        Always returns "legacy" as the only supported extractor.
    """
    return DEFAULT_EXTRACTOR


def get_extractor(debug: bool = False) -> ExtractorProtocol:
    """
    Factory function to create and return the configured extractor.
    
    Always returns the LegacyExtractor (Camelot-based extraction).
    
    Args:
        debug: Enable debug output for the extractor.
        
    Returns:
        A LegacyExtractor instance implementing ExtractorProtocol.
        
    Example:
        >>> extractor = get_extractor()
        >>> result = extractor.extract("/path/to/statement.pdf")
        >>> print(f"Extracted {len(result.normalized_rows)} transactions")
    """
    logger.info(f"Creating {DEFAULT_EXTRACTOR} extractor")
    
    from .legacy_extractor import LegacyExtractor
    return LegacyExtractor(debug=debug)


def is_extractor_available(extractor_type: str) -> bool:
    """
    Check if a specific extractor type is available.
    
    Only "legacy" extractor is available.
    
    Args:
        extractor_type: The extractor type to check
        
    Returns:
        True if extractor_type is "legacy", False otherwise.
    """
    return extractor_type == "legacy"


def list_available_extractors() -> dict:
    """
    List all available extractors and their status.
    
    Returns:
        Dict mapping extractor name to availability status:
        {
            "legacy": {"available": True, "installed": True, "name": "legacy"}
        }
    """
    from .legacy_extractor import LegacyExtractor
    
    extractor = LegacyExtractor()
    
    return {
        "legacy": {
            "available": True,
            "installed": True,
            "name": extractor.name
        }
    }
