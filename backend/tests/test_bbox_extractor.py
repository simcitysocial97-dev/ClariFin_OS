"""
Tests for BBox-Based Table Extractor
======================================
Unit tests for bbox coordinate conversion and extraction logic.

Run: python -m pytest tests/test_bbox_extractor.py -v
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open

import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.extraction.bbox_extractor import (
    convert_bbox_norm_to_pdf_coords,
    convert_bbox_pdf_to_norm_coords,
    _detect_columns,
    _parse_amount_to_paise,
    _normalize_row,
    _validate_required_columns,
    BboxExtractionError,
    ColumnValidationError,
)


class TestCoordinateConversion:
    """Tests for bbox coordinate conversion functions."""

    def test_convert_bbox_norm_to_pdf_coords_basic(self):
        """Test basic conversion from normalized to PDF coordinates."""
        # Top-left quadrant of a 595x842 page (A4)
        bbox_norm = [0.0, 0.0, 0.5, 0.5]  # top-left half
        result = convert_bbox_norm_to_pdf_coords(bbox_norm, 595.0, 842.0)
        
        # x0 should be 0, x1 should be 297.5
        # y0 should be 421 (bottom of top half), y1 should be 842 (top of page)
        assert result[0] == 0.0  # x0
        assert result[1] == 421.0  # y0 (bottom of crop area)
        assert result[2] == 297.5  # x1
        assert result[3] == 842.0  # y1 (top of page)

    def test_convert_bbox_norm_to_pdf_coords_full_page(self):
        """Test conversion for full page bbox."""
        bbox_norm = [0.0, 0.0, 1.0, 1.0]
        result = convert_bbox_norm_to_pdf_coords(bbox_norm, 595.0, 842.0)
        
        assert result == (0.0, 0.0, 595.0, 842.0)

    def test_convert_bbox_norm_to_pdf_coords_center(self):
        """Test conversion for center region."""
        bbox_norm = [0.25, 0.25, 0.75, 0.75]
        result = convert_bbox_norm_to_pdf_coords(bbox_norm, 600.0, 800.0)
        
        assert result[0] == 150.0  # x0 = 0.25 * 600
        assert result[2] == 450.0  # x1 = 0.75 * 600
        # y is flipped: ny0=0.25 -> pdf y1 = 800 - 200 = 600
        #               ny1=0.75 -> pdf y0 = 800 - 600 = 200
        assert result[1] == 200.0  # y0
        assert result[3] == 600.0  # y1

    def test_convert_bbox_norm_invalid_length(self):
        """Test error on invalid bbox length."""
        with pytest.raises(ValueError, match="bbox_norm must have 4 elements"):
            convert_bbox_norm_to_pdf_coords([0.1, 0.2, 0.3], 595.0, 842.0)

    def test_convert_bbox_norm_out_of_range(self):
        """Test error on out-of-range values."""
        with pytest.raises(ValueError, match="bbox_norm values must be in range"):
            convert_bbox_norm_to_pdf_coords([0.1, 0.2, 1.5, 0.8], 595.0, 842.0)

    def test_convert_bbox_pdf_to_norm_coords_roundtrip(self):
        """Test that PDF -> norm -> PDF gives approximately same result."""
        original_norm = [0.1, 0.2, 0.9, 0.8]
        page_width, page_height = 595.0, 842.0
        
        # Convert to PDF
        pdf_coords = convert_bbox_norm_to_pdf_coords(original_norm, page_width, page_height)
        
        # Convert back to normalized
        result_norm = convert_bbox_pdf_to_norm_coords(pdf_coords, page_width, page_height)
        
        # Should be approximately equal (rounding to 6 decimal places)
        for orig, result in zip(original_norm, result_norm):
            assert abs(orig - result) < 0.000001

    def test_convert_bbox_pdf_to_norm_coords_basic(self):
        """Test basic PDF to normalized conversion."""
        # Full page in PDF coords
        bbox_pdf = (0.0, 0.0, 595.0, 842.0)
        result = convert_bbox_pdf_to_norm_coords(bbox_pdf, 595.0, 842.0)
        
        assert result == [0.0, 0.0, 1.0, 1.0]


class TestColumnDetection:
    """Tests for column detection from table headers."""

    def test_detect_date_column_from_header(self):
        """Test detection of date column from header text."""
        rows = [
            ['Date', 'Description', 'Debit', 'Credit', 'Balance'],
            ['01/01/2024', 'Test', '100', '', '1000'],
        ]
        column_map = _detect_columns(rows)
        
        assert column_map.get('date') == 0

    def test_detect_description_column_from_header(self):
        """Test detection of description column."""
        rows = [
            ['Date', 'Particulars', 'Amount', 'Balance'],
            ['01/01/2024', 'Test transaction', '100', '1000'],
        ]
        column_map = _detect_columns(rows)
        
        assert column_map.get('description') == 1

    def test_detect_debit_credit_columns(self):
        """Test detection of separate debit and credit columns."""
        rows = [
            ['Date', 'Description', 'Debit', 'Credit'],
            ['01/01/2024', 'Test', '100', ''],
        ]
        column_map = _detect_columns(rows)
        
        assert column_map.get('debit') == 2
        assert column_map.get('credit') == 3

    def test_detect_balance_column(self):
        """Test detection of balance column."""
        rows = [
            ['Date', 'Description', 'Amount', 'Closing Balance'],
            ['01/01/2024', 'Test', '100', '1000'],
        ]
        column_map = _detect_columns(rows)
        
        assert column_map.get('balance') == 3

    def test_detect_date_from_content(self):
        """Test date detection from content when header is unclear."""
        rows = [
            ['', '', '', ''],
            ['01/04/2025', 'Test transaction', '100.00', '1000.00'],
        ]
        column_map = _detect_columns(rows)
        
        # Should detect first column as date based on pattern
        assert column_map.get('date') == 0

    def test_detect_description_by_length(self):
        """Test description detection by content length."""
        rows = [
            ['Col1', 'Col2', 'Col3'],
            ['01/04/2025', 'This is a very long transaction description that stands out', '100'],
        ]
        column_map = _detect_columns(rows)
        
        # Should detect longest text column as description
        assert column_map.get('description') == 1


class TestAmountParsing:
    """Tests for amount parsing to paise."""

    def test_parse_simple_amount(self):
        """Test parsing simple amount."""
        assert _parse_amount_to_paise("100") == 10000  # 100 rupees = 10000 paise

    def test_parse_amount_with_decimal(self):
        """Test parsing amount with decimal - 100.50 rupees = 10050 paise."""
        result = _parse_amount_to_paise("100.50")
        # Note: 100.50 rupees * 100 = 10050 paise
        assert result == 10050, f"Expected 10050 paise for 100.50 rupees, got {result}"

    def test_parse_amount_with_comma(self):
        """Test parsing amount with comma."""
        assert _parse_amount_to_paise("1,000") == 100000  # 1000 rupees = 100000 paise

    def test_parse_amount_with_currency(self):
        """Test parsing amount with currency symbol."""
        assert _parse_amount_to_paise("Rs. 500") == 50000  # 500 rupees
        assert _parse_amount_to_paise("$100") == 10000  # 100 rupees

    def test_parse_negative_with_parentheses(self):
        """Test parsing negative amount in parentheses - (100.50) rupees = 10050 paise."""
        result = _parse_amount_to_paise("(100.50)")
        assert result == 10050, f"Expected 10050 paise for (100.50) rupees, got {result}"

    def test_parse_with_cr_suffix(self):
        """Test parsing amount with CR suffix - returns positive (credit)."""
        result = _parse_amount_to_paise("100CR")
        # CR indicates credit, function returns positive value
        assert result == 10000, f"Expected 10000 for 100CR, got {result}"

    def test_parse_with_dr_suffix(self):
        """Test parsing amount with DR suffix - returns negative (debit)."""
        result = _parse_amount_to_paise("100DR")
        # DR indicates debit, function returns negative value
        assert result == -10000, f"Expected -10000 for 100DR, got {result}"

    def test_parse_empty_and_none(self):
        """Test parsing empty and None values."""
        assert _parse_amount_to_paise("") == 0
        assert _parse_amount_to_paise(None) == 0

    def test_parse_invalid(self):
        """Test parsing invalid amount."""
        assert _parse_amount_to_paise("abc") == 0


class TestRowNormalization:
    """Tests for row normalization."""

    def test_normalize_basic_row(self):
        """Test normalizing a basic row."""
        row = ['01/04/2025', 'Test transaction', '100', '', '500']
        column_map = {'date': 0, 'description': 1, 'debit': 2, 'credit': 3, 'balance': 4}
        
        result = _normalize_row(row, column_map, has_separate_debit_credit=True)
        
        assert result is not None
        assert result['date'] == '01/04/2025'
        assert result['description'] == 'Test transaction'
        assert result['debit_paise'] == 10000
        assert result['credit_paise'] == 0
        assert result['balance_paise'] == 50000

    def test_normalize_credit_row(self):
        """Test normalizing a credit row."""
        row = ['01/04/2025', 'Salary credit', '', '5000', '10000']
        column_map = {'date': 0, 'description': 1, 'debit': 2, 'credit': 3, 'balance': 4}
        
        result = _normalize_row(row, column_map, has_separate_debit_credit=True)
        
        assert result['debit_paise'] == 0
        assert result['credit_paise'] == 500000

    def test_normalize_no_date(self):
        """Test that row with no date returns None."""
        row = ['', 'Test', '100']
        column_map = {'date': 0, 'description': 1, 'debit': 2}
        
        result = _normalize_row(row, column_map, has_separate_debit_credit=False)
        
        assert result is None

    def test_normalize_header_row(self):
        """Test that header-like row returns None."""
        row = ['Date', 'Description', 'Amount']
        column_map = {'date': 0, 'description': 1, 'debit': 2}
        
        result = _normalize_row(row, column_map, has_separate_debit_credit=False)
        
        assert result is None


class TestColumnValidation:
    """Tests for column validation."""

    def test_validate_empty_rows(self):
        """Test validation fails on empty rows."""
        with pytest.raises(ColumnValidationError, match="No rows extracted"):
            _validate_required_columns([])

    def test_validate_missing_date(self):
        """Test validation fails when date is missing."""
        rows = [{'date': '', 'description': 'Test', 'debit_paise': 100}]
        with pytest.raises(ColumnValidationError, match="date"):
            _validate_required_columns(rows)

    def test_validate_missing_description(self):
        """Test validation fails when description is missing."""
        rows = [{'date': '01/04/2025', 'description': '', 'debit_paise': 100}]
        with pytest.raises(ColumnValidationError, match="description"):
            _validate_required_columns(rows)

    def test_validate_missing_amounts(self):
        """Test validation fails when no amounts present."""
        rows = [
            {'date': '01/04/2025', 'description': 'Test', 'debit_paise': 0, 'credit_paise': 0}
        ]
        with pytest.raises(ColumnValidationError, match="amount"):
            _validate_required_columns(rows)

    def test_validate_success(self):
        """Test validation passes with valid rows."""
        rows = [
            {'date': '01/04/2025', 'description': 'Test', 'debit_paise': 100, 'credit_paise': 0}
        ]
        # Should not raise
        _validate_required_columns(rows)


class TestCoordinateConversionEdgeCases:
    """Edge case tests for coordinate conversion."""

    def test_conversion_with_zero_dimensions(self):
        """Test conversion with very small page dimensions."""
        bbox_norm = [0.0, 0.0, 1.0, 1.0]
        result = convert_bbox_norm_to_pdf_coords(bbox_norm, 1.0, 1.0)
        assert result == (0.0, 0.0, 1.0, 1.0)

    def test_conversion_with_large_dimensions(self):
        """Test conversion with large page dimensions."""
        bbox_norm = [0.1, 0.1, 0.9, 0.9]
        result = convert_bbox_norm_to_pdf_coords(bbox_norm, 2000.0, 3000.0)
        
        assert result[0] == 200.0  # 0.1 * 2000
        assert result[2] == 1800.0  # 0.9 * 2000

    def test_roundtrip_preserves_proportions(self):
        """Test that roundtrip conversion preserves relative proportions."""
        test_cases = [
            [0.0, 0.0, 1.0, 1.0],  # full page
            [0.25, 0.25, 0.75, 0.75],  # center quarter
            [0.1, 0.2, 0.9, 0.8],  # typical statement table
        ]
        
        for bbox_norm in test_cases:
            pdf = convert_bbox_norm_to_pdf_coords(bbox_norm, 595.0, 842.0)
            back_to_norm = convert_bbox_pdf_to_norm_coords(pdf, 595.0, 842.0)
            
            for orig, back in zip(bbox_norm, back_to_norm):
                assert abs(orig - back) < 0.00001


class TestErrorHandling:
    """Tests for error conditions."""

    def test_bbox_extraction_error_inheritance(self):
        """Test that ColumnValidationError inherits from BboxExtractionError."""
        assert issubclass(ColumnValidationError, BboxExtractionError)

    @patch('src.extraction.bbox_extractor.Path.exists')
    def test_pdf_not_found(self, mock_exists):
        """Test error when PDF doesn't exist."""
        mock_exists.return_value = False
        
        with pytest.raises(BboxExtractionError, match="PDF not found"):
            from src.extraction.bbox_extractor import extract_with_bbox
            extract_with_bbox("/nonexistent.pdf", [{"page_number": 1, "x0": 0, "y0": 0, "x1": 1, "y1": 1}])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])