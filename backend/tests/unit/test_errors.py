"""
Unit tests for error handling module.

Tests cover error constants, custom exception classes, error hierarchy,
and error response formatting — without requiring FastAPI infrastructure.
"""


from src.errors import (
    AMOUNT_INVALID,
    INVALID_REQUEST,
    LOAN_NOT_FOUND,
    RATE_INVALID,
    TENURE_INVALID,
    VALIDATION_ERROR,
    AppError,
    DatabaseError,
    FileError,
    ImportError,
    NotFoundError,
    ValidationError,
    format_error_response,
)

# ============================================================================
# Error Constants
# ============================================================================


class TestErrorConstants:
    """Standardized error code constants."""

    def test_loan_not_found(self) -> None:
        """LOAN_NOT_FOUND should be a string constant."""
        assert LOAN_NOT_FOUND == "LOAN_NOT_FOUND"

    def test_invalid_request(self) -> None:
        """INVALID_REQUEST should be a string constant."""
        assert INVALID_REQUEST == "INVALID_REQUEST"

    def test_validation_error(self) -> None:
        """VALIDATION_ERROR should be a string constant."""
        assert VALIDATION_ERROR == "VALIDATION_ERROR"

    def test_amount_invalid(self) -> None:
        """AMOUNT_INVALID should be a string constant."""
        assert AMOUNT_INVALID == "AMOUNT_INVALID"

    def test_rate_invalid(self) -> None:
        """RATE_INVALID should be a string constant."""
        assert RATE_INVALID == "RATE_INVALID"

    def test_tenure_invalid(self) -> None:
        """TENURE_INVALID should be a string constant."""
        assert TENURE_INVALID == "TENURE_INVALID"


# ============================================================================
# AppError (Base)
# ============================================================================


class TestAppError:
    """Base application error class."""

    def test_create_with_message_only(self) -> None:
        """AppError with just a message should default to 500."""
        err = AppError("Something went wrong")
        assert err.message == "Something went wrong"
        assert err.status_code == 500
        assert err.details == {}

    def test_create_with_status_code(self) -> None:
        """AppError should accept a custom status code."""
        err = AppError("Not found", status_code=404)
        assert err.message == "Not found"
        assert err.status_code == 404

    def test_create_with_details(self) -> None:
        """AppError should accept optional details dict."""
        err = AppError("Error", details={"field": "amount"})
        assert err.details == {"field": "amount"}

    def test_is_exception_subclass(self) -> None:
        """AppError should be a subclass of Exception."""
        err = AppError("test")
        assert isinstance(err, Exception)

    def test_str_representation(self) -> None:
        """str(err) should return the message."""
        err = AppError("test message")
        assert str(err) == "test message"


# ============================================================================
# Error Hierarchy
# ============================================================================


class TestErrorHierarchy:
    """All custom errors should inherit from AppError."""

    def test_validation_error_is_app_error(self) -> None:
        """ValidationError should be an AppError."""
        err = ValidationError("Invalid input")
        assert isinstance(err, AppError)
        assert isinstance(err, Exception)

    def test_validation_error_status_code(self) -> None:
        """ValidationError should have status 400."""
        err = ValidationError("Invalid input")
        assert err.status_code == 400

    def test_database_error_is_app_error(self) -> None:
        """DatabaseError should be an AppError."""
        err = DatabaseError("DB failure")
        assert isinstance(err, AppError)

    def test_database_error_status_code(self) -> None:
        """DatabaseError should have status 500."""
        err = DatabaseError("DB failure")
        assert err.status_code == 500

    def test_file_error_is_app_error(self) -> None:
        """FileError should be an AppError."""
        err = FileError("File not found")
        assert isinstance(err, AppError)

    def test_file_error_status_code(self) -> None:
        """FileError should have status 400."""
        err = FileError("File not found")
        assert err.status_code == 400

    def test_import_error_is_app_error(self) -> None:
        """ImportError should be an AppError."""
        err = ImportError("Import failed")
        assert isinstance(err, AppError)

    def test_import_error_status_code(self) -> None:
        """ImportError should have status 400."""
        err = ImportError("Import failed")
        assert err.status_code == 400

    def test_not_found_error_is_app_error(self) -> None:
        """NotFoundError should be an AppError."""
        err = NotFoundError("Resource not found")
        assert isinstance(err, AppError)

    def test_not_found_error_status_code(self) -> None:
        """NotFoundError should have status 404."""
        err = NotFoundError("Resource not found")
        assert err.status_code == 404

    def test_not_found_error_with_details(self) -> None:
        """NotFoundError should accept details."""
        err = NotFoundError("Loan not found", details={"loan_id": 123})
        assert err.details == {"loan_id": 123}


# ============================================================================
# format_error_response
# ============================================================================


class TestFormatErrorResponse:
    """Format error response dictionaries."""

    def test_format_with_message_and_status(self) -> None:
        """Should return dict with error key containing message and status_code."""
        result = format_error_response(400, "Bad request")
        assert "error" in result
        assert result["error"]["message"] == "Bad request"
        assert result["error"]["status_code"] == 400

    def test_format_with_details(self) -> None:
        """Should include details when provided."""
        result = format_error_response(422, "Validation failed", {"errors": []})
        assert result["error"]["details"] == {"errors": []}

    def test_format_without_details(self) -> None:
        """Should not include details key when not provided."""
        result = format_error_response(500, "Server error")
        assert "details" not in result["error"]

    def test_format_with_none_details(self) -> None:
        """Should not include details key when None is passed."""
        result = format_error_response(500, "Server error", None)
        assert "details" not in result["error"]
