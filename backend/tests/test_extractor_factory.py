"""
Tests for Extractor Factory
============================
Tests extractor selection and factory behavior.

These tests do NOT require real PDFs - they test the selection mechanism
and basic functionality without actual extraction.

Run: python -m pytest tests/test_extractor_factory.py -v
"""

import os
import sys
import importlib
from pathlib import Path
from unittest import mock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================
# Test 1: Default extractor type is legacy
# ============================================================

def test_default_extractor_type_is_legacy():
    """Test that factory returns legacy extractor type."""
    from src.extraction import factory
    
    # Clear env var (should not affect result)
    with mock.patch.dict(os.environ, {}, clear=True):
        importlib.reload(factory)
        
        assert factory.get_extractor_type() == "legacy"


# ============================================================
# Test 2: Legacy extractor is always available
# ============================================================

def test_legacy_extractor_is_available():
    """Test that legacy extractor is always available."""
    from src.extraction import factory
    
    # Reload with clean env
    with mock.patch.dict(os.environ, {}, clear=True):
        importlib.reload(factory)
        
        assert factory.is_extractor_available("legacy") is True


# ============================================================
# Test 3: Other extractors are not available
# ============================================================

def test_other_extractors_are_not_available():
    """Test that only legacy extractor is available."""
    from src.extraction import factory
    
    with mock.patch.dict(os.environ, {}, clear=True):
        importlib.reload(factory)
        
        assert factory.is_extractor_available("docling") is False
        assert factory.is_extractor_available("invalid") is False
        assert factory.is_extractor_available("") is False


# ============================================================
# Test 4: Legacy extractor returns correct name
# ============================================================

def test_legacy_extractor_name():
    """Test that legacy extractor returns correct name."""
    from src.extraction.legacy_extractor import LegacyExtractor
    
    extractor = LegacyExtractor()
    assert extractor.name == "legacy"


# ============================================================
# Test 5: Legacy extractor returns ExtractedStatement structure
# ============================================================

def test_legacy_extractor_returns_correct_structure():
    """
    Test that LegacyExtractor returns ExtractedStatement with correct fields.
    
    Note: This test uses the actual extraction code but with a minimal
    check that the structure is correct. It may require pdfplumber/camelot
    to be installed.
    """
    from src.extraction.legacy_extractor import LegacyExtractor
    from src.extraction.base_extractor import ExtractedStatement
    
    extractor = LegacyExtractor()
    
    # Just verify the extract method exists and returns correct type
    # We can't test actual extraction without a PDF
    assert hasattr(extractor, 'extract')
    assert hasattr(extractor, 'name')


# ============================================================
# Test 6: List available extractors
# ============================================================

def test_list_available_extractors():
    """Test that list_available_extractors returns status for legacy only."""
    from src.extraction import factory
    
    # Reload with clean env
    with mock.patch.dict(os.environ, {}, clear=True):
        importlib.reload(factory)
        
        result = factory.list_available_extractors()
        
        # Should only have entry for legacy
        assert "legacy" in result
        assert result["legacy"]["available"] is True
        assert result["legacy"]["installed"] is True
        
        # Should not contain other extractors
        assert "docling" not in result


# ============================================================
# Test 7: ExtractorProtocol compliance
# ============================================================

def test_legacy_extractor_implements_protocol():
    """Test that LegacyExtractor implements ExtractorProtocol."""
    from src.extraction.legacy_extractor import LegacyExtractor
    from src.extraction.base_extractor import ExtractorProtocol
    
    extractor = LegacyExtractor()
    
    # Check required methods exist
    assert hasattr(extractor, 'extract')
    assert hasattr(extractor, 'name')


# ============================================================
# Test 8: ExtractedStatement dataclass
# ============================================================

def test_extracted_statement_dataclass():
    """Test ExtractedStatement dataclass creation and conversion."""
    from src.extraction.base_extractor import ExtractedStatement
    
    statement = ExtractedStatement(
        bank="Test Bank",
        pages=[0, 1],
        opening_balance=1000.0,
        closing_balance=500.0,
        normalized_rows=[
            {
                'date': '01/01/2025',
                'date_iso': '2025-01-01',
                'description': 'Test transaction',
                'debit_paise': 10000,
                'credit_paise': 0,
                'balance_paise': 90000,
                'raw': {}
            }
        ],
        metadata={'extractor': 'test'}
    )
    
    # Verify fields
    assert statement.bank == "Test Bank"
    assert statement.pages == [0, 1]
    assert statement.opening_balance == 1000.0
    assert statement.closing_balance == 500.0
    assert len(statement.normalized_rows) == 1
    
    # Test to_staging_format conversion
    staging = statement.to_staging_format()
    assert staging['bank'] == "Test Bank"
    assert staging['opening_balance_paise'] == 100000  # 1000.0 * 100
    assert staging['closing_balance_paise'] == 50000   # 500.0 * 100
    assert staging['extractor'] == 'test'


# ============================================================
# Test 9: ExtractionError exception
# ============================================================

def test_extraction_error_exception():
    """Test ExtractionError can be raised and caught."""
    from src.extraction.base_extractor import ExtractionError
    
    with pytest.raises(ExtractionError):
        raise ExtractionError("Test error")
    
    try:
        raise ExtractionError("Test error message")
    except ExtractionError as e:
        assert "Test error message" in str(e)


# ============================================================
# Test 10: Factory always returns legacy extractor
# ============================================================

def test_factory_always_returns_legacy():
    """
    Test that get_extractor() always returns LegacyExtractor.
    
    Even if an invalid extractor type was previously configured,
    the factory should return the stable legacy extractor.
    """
    from src.extraction import factory
    
    with mock.patch.dict(os.environ, {}, clear=True):
        importlib.reload(factory)
        
        # Should always return LegacyExtractor
        extractor = factory.get_extractor()
        
        assert extractor.name == "legacy"


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
