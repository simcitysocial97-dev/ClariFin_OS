"""Date Consistency Invariants — ISO format, month bucket alignment, chronology."""
from __future__ import annotations

import re
from typing import Any

ISO_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_BUCKET_REGEX = re.compile(r"^\d{4}-\d{2}$")


def assert_date_iso_format(date_str: str, field_name: str = "date_iso") -> None:
    """Validate date string is ISO 8601 YYYY-MM-DD.

    INVARIANT: All date strings must be ISO 8601 format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate
        field_name: Human-readable field name for error messages

    Raises:
        AssertionError: If date format is invalid
    """
    if not date_str:
        raise AssertionError(f"{field_name} is empty or None")
    if not ISO_DATE_REGEX.match(date_str):
        raise AssertionError(
            f"{field_name}={date_str} is not ISO 8601 (YYYY-MM-DD)"
        )
    # Validate month range
    parts = date_str.split("-")
    month = int(parts[1])
    day = int(parts[2])
    if month < 1 or month > 12:
        raise AssertionError(f"{field_name}={date_str}: month {month} out of range [1,12]")
    if day < 1 or day > 31:
        raise AssertionError(f"{field_name}={date_str}: day {day} out of range [1,31]")


def assert_month_bucket_alignment(date_iso: str, month_bucket: str) -> None:
    """Validate that month_bucket aligns with date_iso.

    INVARIANT: month_bucket (YYYY-MM) must match the year-month of date_iso.

    Args:
        date_iso: ISO date string (YYYY-MM-DD)
        month_bucket: Month bucket string (YYYY-MM)

    Raises:
        AssertionError: If month bucket does not align
    """
    if not MONTH_BUCKET_REGEX.match(month_bucket):
        raise AssertionError(
            f"month_bucket={month_bucket} is not valid format (YYYY-MM)"
        )
    expected_bucket = date_iso[:7]  # First 7 chars = YYYY-MM
    if month_bucket != expected_bucket:
        raise AssertionError(
            f"month_bucket={month_bucket} does not match date_iso={date_iso} "
            f"(expected {expected_bucket})"
        )


def assert_date_sequence_ordered(dates: list[str]) -> None:
    """Validate sequence of dates is monotonically non-decreasing.

    INVARIANT: Dates are sorted ascending (chronological order).

    Args:
        dates: List of ISO date strings

    Raises:
        AssertionError: If dates are not ordered
    """
    for i in range(len(dates) - 1):
        if dates[i] > dates[i + 1]:
            raise AssertionError(
                f"Date sequence not ordered at index {i}: {dates[i]} > {dates[i + 1]}"
            )


def assert_date_in_range(date_iso: str, start: str, end: str) -> None:
    """Validate date falls within expected range.

    INVARIANT: date_iso >= start and date_iso <= end.

    Args:
        date_iso: Date to validate
        start: Start of range (inclusive)
        end: End of range (inclusive)

    Raises:
        AssertionError: If date is out of range
    """
    if date_iso < start:
        raise AssertionError(f"date_iso={date_iso} < start={start}")
    if date_iso > end:
        raise AssertionError(f"date_iso={date_iso} > end={end}")


def assert_data_has_required_dates(data: dict[str, Any], date_fields: list[str]) -> None:
    """Validate that required date fields are present and valid.

    INVARIANT: All required date fields are non-empty ISO 8601 strings.

    Args:
        data: Dictionary with date fields
        date_fields: List of field names that must be valid dates

    Raises:
        AssertionError: If any required date field is missing or invalid
    """
    for field in date_fields:
        value = data.get(field)
        if not value:
            raise AssertionError(f"Required date field '{field}' is missing or empty")
        assert_date_iso_format(str(value), field_name=field)
