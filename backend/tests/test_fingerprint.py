"""
Tests for PDF Layout Fingerprinting Module
============================================
Unit tests for deterministic fingerprint generation.

These tests use mocked pdfplumber or the component-based helper
to avoid needing real PDF files.

Run: python -m pytest tests/test_fingerprint.py -v
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.extraction.fingerprint import (
    compute_fingerprint_from_components,
    compute_fingerprint,
    _extract_header_text,
    _extract_page_dimensions,
)


class TestComputeFingerprintFromComponents:
    """Tests for the component-based fingerprint computation (no PDF needed)."""

    def test_determinism_same_inputs(self):
        """Same inputs should produce the same fingerprint."""
        fp1 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="HDFC BANK STATEMENT",
            bank_hint="HDFC Bank"
        )
        fp2 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="HDFC BANK STATEMENT",
            bank_hint="HDFC Bank"
        )
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA256 hex is 64 chars

    def test_different_inputs_different_fingerprints(self):
        """Different inputs should produce different fingerprints."""
        fp1 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="HDFC BANK STATEMENT",
            bank_hint="HDFC Bank"
        )
        fp2 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="AXIS BANK STATEMENT",
            bank_hint="Axis Bank"
        )
        assert fp1 != fp2

    def test_case_normalization(self):
        """Header text should be normalized to uppercase."""
        fp1 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="hdfc bank statement",
            bank_hint="HDFC Bank"
        )
        fp2 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="HDFC BANK STATEMENT",
            bank_hint="HDFC Bank"
        )
        assert fp1 == fp2

    def test_whitespace_normalization(self):
        """Multiple spaces should be collapsed."""
        fp1 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="HDFC   BANK   STATEMENT",
            bank_hint="HDFC Bank"
        )
        fp2 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="HDFC BANK STATEMENT",
            bank_hint="HDFC Bank"
        )
        assert fp1 == fp2

    def test_header_text_truncation(self):
        """Header text longer than 200 chars should be truncated."""
        long_text = "A" * 500
        fp = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text=long_text,
            bank_hint="HDFC Bank"
        )
        # Should still produce valid fingerprint
        assert len(fp) == 64

    def test_optional_bank_hint(self):
        """Bank hint should be optional."""
        fp1 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="HDFC BANK STATEMENT",
            bank_hint=None
        )
        fp2 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="HDFC BANK STATEMENT",
            bank_hint=""
        )
        # None and empty string should produce same result
        assert fp1 == fp2

    def test_page_dimensions_affect_fingerprint(self):
        """Different page dimensions should change fingerprint."""
        fp1 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="STATEMENT",
            bank_hint="HDFC Bank"
        )
        fp2 = compute_fingerprint_from_components(
            page_width=612.0,
            page_height=792.0,
            header_text="STATEMENT",
            bank_hint="HDFC Bank"
        )
        assert fp1 != fp2

    def test_fingerprint_format(self):
        """Fingerprint should be valid hexadecimal."""
        fp = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="TEST HEADER",
            bank_hint="Test Bank"
        )
        # Should be 64 characters
        assert len(fp) == 64
        # Should only contain hex characters
        assert all(c in '0123456789abcdef' for c in fp)


class TestExtractPageDimensions:
    """Tests for page dimension extraction."""

    def test_extract_dimensions(self):
        """Should extract width and height from page."""
        mock_page = Mock()
        mock_page.width = 595.0
        mock_page.height = 842.0
        
        width, height = _extract_page_dimensions(mock_page)
        
        assert width == 595.0
        assert height == 842.0

    def test_extract_dimensions_integer(self):
        """Should handle integer dimensions."""
        mock_page = Mock()
        mock_page.width = 595
        mock_page.height = 842
        
        width, height = _extract_page_dimensions(mock_page)
        
        assert width == 595.0
        assert height == 842.0


class TestExtractHeaderText:
    """Tests for header text extraction."""

    def test_extract_header_basic(self):
        """Should extract and normalize header text."""
        mock_crop = Mock()
        mock_crop.extract_text.return_value = "HDFC Bank Statement"
        
        mock_page = Mock()
        mock_page.width = 595.0
        mock_page.height = 842.0
        mock_page.crop.return_value = mock_crop
        
        header = _extract_header_text(mock_page)
        
        assert header == "HDFC BANK STATEMENT"
        # Should crop top 15% of page
        mock_page.crop.assert_called_once_with((0, 0, 595.0, 842.0 * 0.15))

    def test_extract_header_empty(self):
        """Should handle empty header text."""
        mock_crop = Mock()
        mock_crop.extract_text.return_value = ""
        
        mock_page = Mock()
        mock_page.width = 595.0
        mock_page.height = 842.0
        mock_page.crop.return_value = mock_crop
        
        header = _extract_header_text(mock_page)
        
        assert header == ""

    def test_extract_header_none(self):
        """Should handle None from extract_text."""
        mock_crop = Mock()
        mock_crop.extract_text.return_value = None
        
        mock_page = Mock()
        mock_page.width = 595.0
        mock_page.height = 842.0
        mock_page.crop.return_value = mock_crop
        
        header = _extract_header_text(mock_page)
        
        assert header == ""

    def test_extract_header_whitespace_normalization(self):
        """Should collapse multiple whitespace characters."""
        mock_crop = Mock()
        mock_crop.extract_text.return_value = "HDFC\t\tBank\n\nStatement"
        
        mock_page = Mock()
        mock_page.width = 595.0
        mock_page.height = 842.0
        mock_page.crop.return_value = mock_crop
        
        header = _extract_header_text(mock_page)
        
        assert header == "HDFC BANK STATEMENT"

    def test_extract_header_truncation(self):
        """Should truncate to max_chars."""
        mock_crop = Mock()
        mock_crop.extract_text.return_value = "A" * 300
        
        mock_page = Mock()
        mock_page.width = 595.0
        mock_page.height = 842.0
        mock_page.crop.return_value = mock_crop
        
        header = _extract_header_text(mock_page, max_chars=200)
        
        assert len(header) == 200


class TestComputeFingerprintWithPDF:
    """Tests for compute_fingerprint with mocked pdfplumber."""

    @patch('src.extraction.fingerprint.pdfplumber')
    def test_compute_fingerprint_success(self, mock_pdfplumber):
        """Should compute fingerprint from PDF."""
        # Setup mock
        mock_page = Mock()
        mock_page.width = 595.0
        mock_page.height = 842.0
        mock_page.crop.return_value = Mock(extract_text=Mock(return_value="HDFC BANK"))
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_pdfplumber.open.return_value.__exit__ = Mock(return_value=False)
        
        # Compute fingerprint
        fp = compute_fingerprint("/path/to/test.pdf", bank_hint="HDFC Bank")
        
        # Should return valid fingerprint
        assert len(fp) == 64
        assert all(c in '0123456789abcdef' for c in fp)

    @patch('src.extraction.fingerprint.pdfplumber')
    def test_compute_fingerprint_file_not_found(self, mock_pdfplumber):
        """Should raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            compute_fingerprint("/nonexistent/path.pdf")

    @patch('src.extraction.fingerprint.pdfplumber')
    def test_compute_fingerprint_empty_pdf(self, mock_pdfplumber):
        """Should raise ValueError for empty PDF."""
        mock_pdf = Mock()
        mock_pdf.pages = []
        mock_pdfplumber.open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_pdfplumber.open.return_value.__exit__ = Mock(return_value=False)
        
        with pytest.raises(ValueError, match="PDF has no pages"):
            compute_fingerprint("/path/to/empty.pdf")


class TestFingerprintDeterminism:
    """Tests to ensure fingerprint determinism across variations."""

    def test_bank_hint_case_insensitive(self):
        """Bank hint case should not affect fingerprint."""
        fp1 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="STATEMENT",
            bank_hint="hdfc bank"
        )
        fp2 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="STATEMENT",
            bank_hint="HDFC BANK"
        )
        assert fp1 == fp2

    def test_page_dimensions_precision(self):
        """Page dimensions should be formatted consistently."""
        fp1 = compute_fingerprint_from_components(
            page_width=595.276,
            page_height=841.89,
            header_text="STATEMENT",
            bank_hint="HDFC Bank"
        )
        fp2 = compute_fingerprint_from_components(
            page_width=595.276,
            page_height=841.89,
            header_text="STATEMENT",
            bank_hint="HDFC Bank"
        )
        assert fp1 == fp2

    def test_trailing_whitespace_ignored(self):
        """Trailing whitespace in header should be stripped."""
        fp1 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="STATEMENT  ",
            bank_hint="HDFC Bank"
        )
        fp2 = compute_fingerprint_from_components(
            page_width=595.0,
            page_height=842.0,
            header_text="STATEMENT",
            bank_hint="HDFC Bank"
        )
        assert fp1 == fp2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])