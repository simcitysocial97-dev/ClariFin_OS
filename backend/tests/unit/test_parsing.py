"""
Unit tests for date/time parsing utilities.

Tests cover parsing of various Indian date formats, month key extraction,
and weekday name resolution — all pure functions with no DB dependency.
"""


from src.common.parsing import get_month_key, get_weekday, parse_date

# ============================================================================
# parse_date
# ============================================================================


class TestParseDate:
    """Parse various Indian date formats to datetime."""

    def test_parse_dmy_slash(self) -> None:
        """DD/MM/YYYY should parse correctly."""
        dt = parse_date("15/01/2025")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_dmy_dash(self) -> None:
        """DD-MM-YYYY should parse correctly."""
        dt = parse_date("15-01-2025")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_dmy_short_year(self) -> None:
        """DD/MM/YY should parse correctly."""
        dt = parse_date("15/01/25")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_dmy_dash_short_year(self) -> None:
        """DD-MM-YY should parse correctly."""
        dt = parse_date("15-01-25")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_day_month_abbr_full_year(self) -> None:
        """DD Mon YYYY should parse correctly."""
        dt = parse_date("15 Jan 2025")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_day_month_abbr_short_year(self) -> None:
        """DD Mon YY should parse correctly."""
        dt = parse_date("15 Jan 25")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_day_month_abbr_with_apostrophe(self) -> None:
        """DD Mon 'YY should parse correctly."""
        dt = parse_date("15 Jan '25")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_day_month_full_year(self) -> None:
        """DD Month YYYY should parse correctly."""
        dt = parse_date("15 January 2025")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_iso_format(self) -> None:
        """YYYY-MM-DD should parse correctly."""
        dt = parse_date("2025-01-15")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15

    def test_parse_two_digit_year_50_century(self) -> None:
        """Two-digit year >= 50 should get 1900 prefix."""
        dt = parse_date("15/01/75")
        assert dt is not None
        assert dt.year == 1975

    def test_parse_two_digit_year_under_50(self) -> None:
        """Two-digit year < 50 should get 2000 prefix."""
        dt = parse_date("15/01/25")
        assert dt is not None
        assert dt.year == 2025

    def test_parse_day_month_abbr_short_year_regex(self) -> None:
        """DD Mon YY (short year) via regex branch should parse correctly."""
        dt = parse_date("01 Aug 25")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 8
        assert dt.day == 1

    def test_parse_empty_string(self) -> None:
        """Empty string should return None."""
        assert parse_date("") is None

    def test_parse_invalid_format(self) -> None:
        """Invalid date format should return None."""
        assert parse_date("not-a-date") is None


# ============================================================================
# get_month_key
# ============================================================================


class TestGetMonthKey:
    """Extract YYYY-MM from date strings."""

    def test_get_month_key_dmy(self) -> None:
        """DD/MM/YYYY should produce 'YYYY-MM'."""
        result = get_month_key("15/01/2025")
        assert result == "2025-01"

    def test_get_month_key_iso(self) -> None:
        """YYYY-MM-DD should produce 'YYYY-MM'."""
        result = get_month_key("2025-01-15")
        assert result == "2025-01"

    def test_get_month_key_month_name(self) -> None:
        """DD Mon YYYY should produce 'YYYY-MM'."""
        result = get_month_key("15 Mar 2025")
        assert result == "2025-03"

    def test_get_month_key_empty(self) -> None:
        """Empty string should return empty."""
        assert get_month_key("") == ""

    def test_get_month_key_invalid(self) -> None:
        """Invalid date should return empty."""
        assert get_month_key("invalid") == ""


# ============================================================================
# get_weekday
# ============================================================================


class TestGetWeekday:
    """Get day of week name from date strings."""

    def test_get_weekday_monday(self) -> None:
        """15/01/2025 (Wednesday) should produce 'Wednesday'."""
        result = get_weekday("15/01/2025")
        assert result == "Wednesday"

    def test_get_weekday_sunday(self) -> None:
        """19/01/2025 should produce 'Sunday'."""
        result = get_weekday("19/01/2025")
        assert result == "Sunday"

    def test_get_weekday_iso(self) -> None:
        """ISO format should work."""
        result = get_weekday("2025-01-15")
        assert result == "Wednesday"

    def test_get_weekday_empty(self) -> None:
        """Empty string should return empty."""
        assert get_weekday("") == ""

    def test_get_weekday_invalid(self) -> None:
        """Invalid date should return empty."""
        assert get_weekday("invalid") == ""
