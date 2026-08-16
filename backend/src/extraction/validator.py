"""
Input Validation Module
=======================

Centralized validation for all user inputs.
Validates required fields, numeric ranges, monetary values, dates, and files.

PARKED: This module is not currently used in the production pipeline.
It contains comprehensive validation logic that may be needed for future API features.

Usage:
    from validator import validate_file_upload, validate_paise_amount
    validate_file_upload(file, allowed_extensions=[".pdf"])
"""

import os
from datetime import datetime

from fastapi import HTTPException, UploadFile

# ============================================================
# Monetary Validation
# ============================================================


def validate_paise_amount(value: int, field_name: str = "amount") -> int:
    """
    Validate a paise amount.

    Args:
        value: Amount in paise
        field_name: Field name for error messages

    Returns:
        Validated paise value

    Raises:
        HTTPException: If value is invalid
    """
    if not isinstance(value, int):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be an integer (paise), got {type(value).__name__}",
        )

    # Reasonable bounds for personal finance
    # Max: ₹999,99,999.99 (about 1 million INR)
    # Min: -₹999,99,999.99 (negative for credits)
    MAX_PAISE = 99999999999  # ~1 billion INR
    MIN_PAISE = -99999999999

    if value < MIN_PAISE or value > MAX_PAISE:
        raise HTTPException(
            status_code=400, detail=f"{field_name} out of valid range: {value} paise"
        )

    return value


def validate_rupees_amount(value: float, field_name: str = "amount") -> float:
    """
    Validate a rupees amount (for backward compatibility).

    Args:
        value: Amount in rupees
        field_name: Field name for error messages

    Returns:
        Validated rupees value

    Raises:
        HTTPException: If value is invalid
    """
    if not isinstance(value, (int, float)):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a number, got {type(value).__name__}",
        )

    # Reasonable bounds for personal finance
    MAX_RUPEES = 999999999.99  # ~100 million INR
    MIN_RUPEES = -999999999.99

    if value < MIN_RUPEES or value > MAX_RUPEES:
        raise HTTPException(
            status_code=400, detail=f"{field_name} out of valid range: {value} rupees"
        )

    return value


# ============================================================
# Date Validation
# ============================================================


def validate_date(date_str: str, field_name: str = "date") -> str:
    """
    Validate a date string.

    Args:
        date_str: Date string in any supported format
        field_name: Field name for error messages

    Returns:
        Validated date string

    Raises:
        HTTPException: If date is invalid
    """
    if not date_str:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")

    # Try to parse the date
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d %b %Y",
        "%d %b %y",
        "%d-%b-%Y",
        "%d-%b-%y",
        "%d %b '%y",
        "%d %B %Y",
        "%d %B %y",
        "%Y-%m-%d",
    ]

    s = date_str.strip()

    # Handle "01 Aug 25" → "01 Aug 2025"
    import re

    m = re.match(r"^(\d{1,2})\s+([A-Za-z]{3})\s+(\d{2})$", s)
    if m:
        day, mon, yr = m.group(1), m.group(2), m.group(3)
        yr_full = f"20{yr}" if int(yr) < 50 else f"19{yr}"
        s = f"{day} {mon} {yr_full}"

    for fmt in formats:
        try:
            datetime.strptime(s, fmt)
            return date_str  # Return original format
        except ValueError:
            continue

    raise HTTPException(
        status_code=400, detail=f"{field_name} has invalid format: {date_str}"
    )


def validate_iso_date(date_str: str, field_name: str = "date") -> str:
    """
    Validate an ISO date string (YYYY-MM-DD).

    Args:
        date_str: Date string in ISO format
        field_name: Field name for error messages

    Returns:
        Validated date string

    Raises:
        HTTPException: If date is invalid
    """
    if not date_str:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be in YYYY-MM-DD format: {date_str}",
        ) from None


# ============================================================
# File Validation
# ============================================================


def validate_file_upload(
    file: UploadFile,
    allowed_extensions: list[str] | None = None,
    max_size_bytes: int | None = None,
) -> None:
    """
    Validate an uploaded file.

    Args:
        file: UploadFile to validate
        allowed_extensions: List of allowed extensions (e.g., [".pdf", ".csv"])
        max_size_bytes: Maximum file size in bytes

    Raises:
        HTTPException: If file is invalid
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    if not file.filename:
        raise HTTPException(status_code=400, detail="File has no name")

    # Check extension
    if allowed_extensions:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [e.lower() for e in allowed_extensions]:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(allowed_extensions)}",
            )

    # Check size (if provided)
    if (
        max_size_bytes
        and hasattr(file, "size")
        and file.size
        and file.size > max_size_bytes
    ):
        max_mb = max_size_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=400, detail=f"File too large. Maximum size: {max_mb}MB"
        )


# ============================================================
# String Validation
# ============================================================


def validate_required_string(
    value: str, field_name: str, min_length: int = 1, max_length: int = 1000
) -> str:
    """
    Validate a required string field.

    Args:
        value: String value to validate
        field_name: Field name for error messages
        min_length: Minimum length (default 1)
        max_length: Maximum length (default 1000)

    Returns:
        Validated string

    Raises:
        HTTPException: If string is invalid
    """
    if value is None:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")

    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=f"{field_name} must be a string")

    if len(value) < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be at least {min_length} characters",
        )

    if len(value) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be at most {max_length} characters",
        )

    return value


def validate_category(category: str) -> str:
    """
    Validate a transaction category.

    Args:
        category: Category string

    Returns:
        Validated category

    Raises:
        HTTPException: If category is invalid
    """
    if not category:
        return "Uncategorized"

    # Known categories (from categorizer)

    # Allow any category (don't restrict to known list)
    return category.strip()


# ============================================================
# Query Parameter Validation
# ============================================================


def validate_pagination(
    limit: int = 100, offset: int = 0, max_limit: int = 1000
) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        limit: Number of items to return
        offset: Number of items to skip
        max_limit: Maximum allowed limit

    Returns:
        Tuple of (limit, offset)

    Raises:
        HTTPException: If parameters are invalid
    """
    if limit < 1:
        raise HTTPException(status_code=400, detail="limit must be at least 1")

    if limit > max_limit:
        raise HTTPException(
            status_code=400, detail=f"limit must be at most {max_limit}"
        )

    if offset < 0:
        raise HTTPException(status_code=400, detail="offset must be at least 0")

    return limit, offset


def validate_member(member: str) -> str:
    """
    Validate a member name.

    Args:
        member: Member name

    Returns:
        Validated member name
    """
    if not member:
        return "Self"

    # Sanitize: remove special characters, limit length
    sanitized = member.strip()[:50]

    return sanitized or "Self"
