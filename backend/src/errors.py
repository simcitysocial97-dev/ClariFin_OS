"""
ClariFin Custom Exceptions
==========================
Custom exception hierarchy for the ClariFin backend.
All exceptions inherit from ClariFinError and include HTTP status codes.
"""


class ClariFinError(Exception):
    """
    Base exception for all ClariFin errors.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code to return
        detail: Optional additional error details
        error_code: Machine-readable error code for frontend handling
    """
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        detail: str | None = None,
        error_code: str = "INTERNAL_ERROR"
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(self.message)


class NotFoundError(ClariFinError):
    """
    Raised when a requested resource is not found.
    Returns HTTP 404.
    """
    
    def __init__(self, resource: str, resource_id: str | int):
        message = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            message=message, 
            status_code=404, 
            error_code="NOT_FOUND"
        )


class ValidationError(ClariFinError):
    """
    Raised when input validation fails.
    Returns HTTP 422.
    """
    
    def __init__(self, message: str):
        super().__init__(
            message=message, 
            status_code=422, 
            error_code="VALIDATION_ERROR"
        )


class DatabaseError(ClariFinError):
    """
    Raised when a database operation fails.
    Returns HTTP 500.
    """
    
    def __init__(self, message: str):
        prefixed_message = f"Database error: {message}"
        super().__init__(
            message=prefixed_message, 
            status_code=500, 
            error_code="DATABASE_ERROR"
        )


class UploadError(ClariFinError):
    """
    Raised when file upload fails or validation fails.
    Returns HTTP 400.
    """
    
    def __init__(self, message: str):
        super().__init__(
            message=message, 
            status_code=400, 
            error_code="UPLOAD_ERROR"
        )
