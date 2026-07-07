"""
Logging Module
==============

Consistent logging for ClariFin_OS backend.
All log messages use a standard format with timestamps and context.

Usage:
    from logger import logger
    logger.info("Processing transaction", extra={"txn_id": 123})
"""

import logging
import sys
from typing import Any


def setup_logging(name: str = "clarifin") -> logging.Logger:
    """
    Set up and return a configured logger.

    Args:
        name: Logger name (default: "clarifin")

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured
        return logger

    # Get settings
    try:
        from config import settings
        log_level = settings.log_level
        log_format = settings.log_format
    except ImportError:
        log_level = "INFO"
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))

    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    return logger


# Global logger instance
logger = setup_logging()


def log_request(method: str, path: str, status_code: int, **kwargs: Any) -> None:
    """
    Log an HTTP request with context.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: Response status code
        **kwargs: Additional context to log
    """
    level = logging.WARNING if status_code >= 400 else logging.INFO
    extra = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.log(level, f"{method} {path} - {status_code}" + (f" ({extra})" if extra else ""))


def log_error(message: str, error: Exception | None = None, **kwargs: Any) -> None:
    """
    Log an error with context.

    Args:
        message: Error message
        error: Optional exception
        **kwargs: Additional context to log
    """
    extra = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    if error:
        logger.error(f"{message}: {error}" + (f" ({extra})" if extra else ""))
    else:
        logger.error(f"{message}" + (f" ({extra})" if extra else ""))


def log_warning(message: str, **kwargs: Any) -> None:
    """
    Log a warning with context.

    Args:
        message: Warning message
        **kwargs: Additional context to log
    """
    extra = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.warning(f"{message}" + (f" ({extra})" if extra else ""))


def log_info(message: str, **kwargs: Any) -> None:
    """
    Log an info message with context.

    Args:
        message: Info message
        **kwargs: Additional context to log
    """
    extra = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"{message}" + (f" ({extra})" if extra else ""))
