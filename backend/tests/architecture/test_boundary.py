"""
Boundary Condition Test Suite
===============================

Tests for error handling, validation, and edge cases.
Covers validator.py, errors.py, and boundary conditions.

Run: python -m pytest tests/test_boundary.py -v
"""

import pytest
from fastapi import HTTPException

# Add src to path
from errors import (
    AppError,
    DatabaseError,
    NotFoundError,
    ValidationError,
    format_error_response,
)
from src.extraction.validator import (
    validate_category,
    validate_date,
    validate_iso_date,
    validate_member,
    validate_pagination,
    validate_paise_amount,
    validate_required_string,
    validate_rupees_amount,
)

# ============================================================
# Paise Amount Validation Tests
# ============================================================


class TestPaiseValidation:
    """Tests for validate_paise_amount boundary conditions."""

    def test_valid_paise_amount(self):
        """Test valid paise amounts are accepted."""
        assert validate_paise_amount(0) == 0
        assert validate_paise_amount(100) == 100
        assert validate_paise_amount(100000) == 100000
        assert validate_paise_amount(99999999999) == 99999999999

    def test_negative_paise_amount(self):
        """Test negative paise amounts are accepted (for credits)."""
        assert validate_paise_amount(-100) == -100
        assert validate_paise_amount(-50000) == -50000

    def test_non_integer_paise_rejected(self):
        """Test non-integer paise amounts are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_paise_amount(100.50)
        assert exc_info.value.status_code == 400

    def test_string_paise_rejected(self):
        """Test string paise amounts are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_paise_amount("100")
        assert exc_info.value.status_code == 400

    def test_zero_paise_accepted(self):
        """Test zero paise is valid."""
        result = validate_paise_amount(0)
        assert result == 0


# ============================================================
# Rupees Amount Validation Tests
# ============================================================


class TestRupeesValidation:
    """Tests for validate_rupees_amount boundary conditions."""

    def test_valid_rupees_amount(self):
        """Test valid rupees amounts are accepted."""
        assert validate_rupees_amount(0.0) == 0.0
        assert validate_rupees_amount(100.50) == 100.50
        assert validate_rupees_amount(999999.99) == 999999.99

    def test_negative_rupees_amount(self):
        """Test negative rupees amounts are accepted."""
        assert validate_rupees_amount(-100.0) == -100.0

    def test_non_numeric_rejected(self):
        """Test non-numeric rupees amounts are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_rupees_amount("invalid")
        assert exc_info.value.status_code == 400

    def test_none_rejected(self):
        """Test None rupees amount is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_rupees_amount(None)
        assert exc_info.value.status_code == 400


# ============================================================
# Date Validation Tests
# ============================================================


class TestDateValidation:
    """Tests for validate_date boundary conditions."""

    def test_valid_date_formats(self):
        """Test valid date formats are accepted."""
        assert validate_date("01/01/2025") == "01/01/2025"
        assert validate_date("01-01-2025") == "01-01-2025"
        assert validate_date("01 Jan 2025") == "01 Jan 2025"
        assert validate_date("2025-01-01") == "2025-01-01"

    def test_empty_date_rejected(self):
        """Test empty date string is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_date("")
        assert exc_info.value.status_code == 400

    def test_none_date_rejected(self):
        """Test None date is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_date(None)
        assert exc_info.value.status_code == 400

    def test_invalid_date_rejected(self):
        """Test invalid date format is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_date("not-a-date")
        assert exc_info.value.status_code == 400


# ============================================================
# ISO Date Validation Tests
# ============================================================


class TestIsoDateValidation:
    """Tests for validate_iso_date boundary conditions."""

    def test_valid_iso_date(self):
        """Test valid ISO date format is accepted."""
        assert validate_iso_date("2025-01-15") == "2025-01-15"

    def test_empty_iso_date_rejected(self):
        """Test empty ISO date is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_iso_date("")
        assert exc_info.value.status_code == 400

    def test_invalid_iso_format_rejected(self):
        """Test invalid ISO format is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_iso_date("15/01/2025")
        assert exc_info.value.status_code == 400


# ============================================================
# String Validation Tests
# ============================================================


class TestStringValidation:
    """Tests for validate_required_string boundary conditions."""

    def test_valid_string(self):
        """Test valid string is accepted."""
        assert validate_required_string("test", "field") == "test"

    def test_empty_string_rejected(self):
        """Test empty string is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_required_string("", "field")
        assert exc_info.value.status_code == 400

    def test_none_string_rejected(self):
        """Test None string is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_required_string(None, "field")
        assert exc_info.value.status_code == 400

    def test_min_length_validation(self):
        """Test min_length is enforced."""
        with pytest.raises(HTTPException) as exc_info:
            validate_required_string("ab", "field", min_length=3)
        assert exc_info.value.status_code == 400

    def test_max_length_validation(self):
        """Test max_length is enforced."""
        with pytest.raises(HTTPException) as exc_info:
            validate_required_string("a" * 1001, "field", max_length=1000)
        assert exc_info.value.status_code == 400


# ============================================================
# Pagination Validation Tests
# ============================================================


class TestPaginationValidation:
    """Tests for validate_pagination boundary conditions."""

    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        limit, offset = validate_pagination(limit=100, offset=0)
        assert limit == 100
        assert offset == 0

    def test_invalid_limit_zero(self):
        """Test limit=0 is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_pagination(limit=0)
        assert exc_info.value.status_code == 400

    def test_invalid_limit_negative(self):
        """Test negative limit is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_pagination(limit=-1)
        assert exc_info.value.status_code == 400

    def test_limit_exceeds_max(self):
        """Test limit exceeding max is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_pagination(limit=1001, max_limit=1000)
        assert exc_info.value.status_code == 400

    def test_negative_offset_rejected(self):
        """Test negative offset is rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_pagination(offset=-1)
        assert exc_info.value.status_code == 400


# ============================================================
# Member Validation Tests
# ============================================================


class TestMemberValidation:
    """Tests for validate_member boundary conditions."""

    def test_valid_member(self):
        """Test valid member name is accepted."""
        assert validate_member("John") == "John"

    def test_empty_returns_default(self):
        """Test empty member returns 'Self'."""
        assert validate_member("") == "Self"

    def test_none_returns_default(self):
        """Test None member returns 'Self'."""
        assert validate_member(None) == "Self"

    def test_trimming_applied(self):
        """Test member name is trimmed."""
        assert validate_member("  John  ") == "John"


# ============================================================
# Category Validation Tests
# ============================================================


class TestCategoryValidation:
    """Tests for validate_category boundary conditions."""

    def test_valid_category(self):
        """Test valid category is accepted."""
        assert validate_category("Food") == "Food"

    def test_empty_returns_default(self):
        """Test empty category returns 'Uncategorized'."""
        assert validate_category("") == "Uncategorized"

    def test_none_returns_default(self):
        """Test None category returns 'Uncategorized'."""
        assert validate_category(None) == "Uncategorized"


# ============================================================
# Error Class Tests
# ============================================================


class TestErrorClasses:
    """Tests for custom error classes."""

    def test_app_error_defaults(self):
        """Test AppError has correct defaults."""
        error = AppError("Test message")
        assert error.message == "Test message"
        assert error.status_code == 500
        assert error.details == {}

    def test_validation_error_status_code(self):
        """Test ValidationError has 400 status code."""
        error = ValidationError("Invalid input")
        assert error.status_code == 400

    def test_database_error_status_code(self):
        """Test DatabaseError has 500 status code."""
        error = DatabaseError("DB failed")
        assert error.status_code == 500

    def test_not_found_error_status_code(self):
        """Test NotFoundError has 404 status code."""
        error = NotFoundError("Resource not found")
        assert error.status_code == 404

    def test_error_with_details(self):
        """Test error with additional details."""
        error = AppError("Error", details={"field": "value"})
        assert error.details == {"field": "value"}


class TestFormatErrorResponse:
    """Tests for error response formatting."""

    def test_format_basic_error(self):
        """Test basic error response format."""
        response = format_error_response(400, "Bad request")
        assert response["error"]["status_code"] == 400
        assert response["error"]["message"] == "Bad request"
        assert "details" not in response["error"]

    def test_format_error_with_details(self):
        """Test error response with details."""
        response = format_error_response(400, "Bad request", {"field": "value"})
        assert response["error"]["status_code"] == 400
        assert response["error"]["details"] == {"field": "value"}
