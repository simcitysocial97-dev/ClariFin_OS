"""
Unit tests for display formatting utilities.

Tests cover INR formatting with lakh/crore grouping, date display,
and description cleaning — all pure functions with no DB dependency.
"""

from src.common.formatting import clean_description, format_date_display, format_inr

# ============================================================================
# format_inr
# ============================================================================


class TestFormatInr:
    """Format amounts in Indian Rupee notation with lakh/crore grouping."""

    def test_format_zero(self) -> None:
        """Zero should return '₹0.00'."""
        assert format_inr(0) == "₹0.00"

    def test_format_none(self) -> None:
        """None should return '₹0.00'."""
        assert format_inr(None) == "₹0.00"  # type: ignore[arg-type]

    def test_format_small_number(self) -> None:
        """Numbers <= 3 digits should not have grouping."""
        assert format_inr(1.0) == "₹1.00"
        assert format_inr(99.99) == "₹99.99"
        assert format_inr(999.99) == "₹999.99"

    def test_format_thousands(self) -> None:
        """1,234 should group as 1,234."""
        assert format_inr(1234.00) == "₹1,234.00"

    def test_format_lakhs(self) -> None:
        """1,23,456 should group as 1,23,456 (lakh)."""
        assert format_inr(123456.00) == "₹1,23,456.00"

    def test_format_crores(self) -> None:
        """1,23,45,678 should group as 1,23,45,678 (crore)."""
        assert format_inr(12345678.00) == "₹1,23,45,678.00"

    def test_format_hundred_crores(self) -> None:
        """12,34,56,789 should group as 12,34,56,789."""
        assert format_inr(123456789.00) == "₹12,34,56,789.00"

    def test_format_negative(self) -> None:
        """Negative amounts should have a leading minus."""
        result = format_inr(-1234.56)
        assert result.startswith("-₹")
        assert "1,234.56" in result

    def test_format_decimal_preserved(self) -> None:
        """Decimal paise should be preserved."""
        assert format_inr(1.50) == "₹1.50"
        assert format_inr(0.05) == "₹0.05"

    def test_format_large_with_paise(self) -> None:
        """Large amounts with paise should format correctly."""
        assert format_inr(10000000.50) == "₹1,00,00,000.50"


# ============================================================================
# format_date_display
# ============================================================================


class TestFormatDateDisplay:
    """Convert date strings to '15 Jun 2025' format."""

    def test_format_dmy_slash(self) -> None:
        """DD/MM/YYYY should convert to 'DD Mon YYYY'."""
        result = format_date_display("15/01/2025")
        assert result == "15 Jan 2025"

    def test_format_dmy_dash(self) -> None:
        """DD-MM-YYYY should convert correctly."""
        result = format_date_display("01-02-2025")
        assert result == "01 Feb 2025"

    def test_format_dmy_short_year(self) -> None:
        """DD/MM/YY should convert with full year."""
        result = format_date_display("15/01/25")
        assert result == "15 Jan 2025"

    def test_format_month_abbreviation(self) -> None:
        """DD Mon YYYY should parse and reformat."""
        result = format_date_display("15 Jan 2025")
        assert result == "15 Jan 2025"

    def test_format_iso(self) -> None:
        """YYYY-MM-DD should convert correctly."""
        result = format_date_display("2025-01-15")
        assert result == "15 Jan 2025"

    def test_format_full_month_name(self) -> None:
        """DD Month YYYY should convert."""
        result = format_date_display("15 January 2025")
        assert result == "15 Jan 2025"

    def test_format_none_date(self) -> None:
        """Empty string should return as-is."""
        result = format_date_display("")
        assert result == ""

    def test_format_invalid_date(self) -> None:
        """Invalid date string should return unchanged."""
        result = format_date_display("not-a-date")
        assert result == "not-a-date"


# ============================================================================
# clean_description
# ============================================================================


class TestCleanDescription:
    """Clean transaction descriptions for display."""

    def test_clean_empty(self) -> None:
        """Empty string should return empty."""
        assert clean_description("") == ""

    def test_clean_none(self) -> None:
        """None should return empty."""
        assert clean_description(None) == ""  # type: ignore[arg-type]

    def test_clean_leading_datetime(self) -> None:
        """Leading DD/MM/YYYY HH:MM:SS should be stripped."""
        desc = "15/01/2025 14:30:25 MERCHANT NAME PAYMENT"
        result = clean_description(desc)
        assert result == "MERCHANT NAME PAYMENT"

    def test_clean_leading_timestamp(self) -> None:
        """Leading HH:MM:SS should be stripped."""
        desc = "14:30:25 MERCHANT NAME PAYMENT"
        result = clean_description(desc)
        assert result == "MERCHANT NAME PAYMENT"

    def test_clean_multiple_spaces(self) -> None:
        """Multiple spaces should be collapsed."""
        desc = "MERCHANT   NAME   PAYMENT"
        result = clean_description(desc)
        assert result == "MERCHANT NAME PAYMENT"

    def test_clean_no_prefix(self) -> None:
        """Description without prefix should remain unchanged."""
        desc = "MERCHANT NAME"
        result = clean_description(desc)
        assert result == "MERCHANT NAME"

    def test_clean_whitespace_stripped(self) -> None:
        """Leading/trailing whitespace should be stripped."""
        desc = "  MERCHANT NAME  "
        result = clean_description(desc)
        assert result == "MERCHANT NAME"
