"""
M9-C57 — Structured Logging Foundation.

Provides JSON-structured logging for observability while preserving
human-readable output for CLI via click.echo.

Design:
  - File output (runtime/generated/logs/) → JSON lines for machine parsing
  - Console output → Human-readable for operators (if console handler is used)
  - Correlation IDs (run_id) threaded through all log entries for traceability
  - Log levels: DEBUG (internal state), INFO (decisions), WARNING (regressions),
               ERROR (failures), CRITICAL (system failures)

Usage:
    from runtime.foundation.verification.structured_logging import (
        setup_logging, get_logger
    )

    setup_logging(level="INFO", correlation_id="run-123")
    logger = get_logger(__name__)
    logger.info("Verification started", extra={"profile": "backend"})
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Correlation ID context (thread-local)
# ---------------------------------------------------------------------------

_thread_local = threading.local()
_CORRELATION_ID_KEY = "correlation_id"


def _get_correlation_id() -> str | None:
    """Return the current thread's correlation ID if set."""
    return getattr(_thread_local, _CORRELATION_ID_KEY, None)


def set_correlation_id(run_id: str | None) -> None:
    """Set the correlation ID for the current thread."""
    if run_id:
        _thread_local.correlation_id = run_id
    elif hasattr(_thread_local, "correlation_id"):
        delattr(_thread_local, "correlation_id")


class _CorrelationFilter(logging.Filter):
    """Inject correlation_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _get_correlation_id() or ""
        return True


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

_JSON_FORMAT = json.dumps(
    {
        "timestamp": "%(asctime)s",
        "level": "%(levelname)s",
        "logger": "%(name)s",
        "message": "%(message)s",
        "correlation_id": "%(correlation_id)s",
        "module": "%(filename)s",
        "function": "%(funcName)s",
        "line": "%(lineno)d",
    },
    sort_keys=True,
)


class JSONFormatter(logging.Formatter):
    """JSON-lines formatter for file output."""

    def format(self, record: logging.LogRecord) -> str:
        # Ensure correlation_id is present
        if not hasattr(record, "correlation_id"):
            record.correlation_id = _get_correlation_id() or ""
        # Build JSON manually for proper escaping
        entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": record.correlation_id,
            "module": record.filename,
            "function": record.funcName,
            "line": record.lineno,
        }
        # Attach any extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "levelname",
                "levelno",
                "created",
                "relativeCreated",
                "elapsed",
                "stack_info",
                "exc_info",
                "exc_text",
                "correlation_id",
                "issue_number",
            ):
                try:
                    entry[key] = value
                except Exception:
                    entry[key] = str(value)
        return json.dumps(entry, default=str, sort_keys=True)


class HumanFormatter(logging.Formatter):
    """Human-readable formatter for console output."""

    def format(self, record: logging.LogRecord) -> str:
        corr = getattr(record, "correlation_id", "")
        corr_prefix = f"[{corr}] " if corr else ""
        timestamp = self.formatTime(record, self.datefmt)
        return (
            f"{timestamp} | {record.levelname:<8} | "
            f"{corr_prefix}{record.name} | {record.getMessage()}"
        )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

_LOGGING_CONFIGURED = False
_DEFAULT_CONFIG = {
    "level": "INFO",
    "log_dir": Path("runtime/generated/logs"),
    "max_bytes": 50 * 1024 * 1024,  # 50 MB
    "backup_count": 5,
}


def setup_logging(
    level: str = "INFO",
    log_dir: Path | str | None = None,
    correlation_id: str | None = None,
    enable_console: bool = True,
    **overrides: Any,
) -> dict[str, Any]:
    """Configure the root logger with JSON file output.

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory for log files. Defaults to runtime/generated/logs/.
        correlation_id: Optional run ID to prepend to all log entries.
        enable_console: If True, add a human-readable console handler.
        **overrides: Additional config overrides (max_bytes, backup_count).

    Returns:
        Dict of configuration applied.
    """
    global _LOGGING_CONFIGURED
    config = {**_DEFAULT_CONFIG, **overrides}
    config["log_dir"] = Path(log_dir) if log_dir else Path(config["log_dir"])
    config["level"] = level.upper()

    root = logging.getLogger()
    root.setLevel(getattr(logging, config["level"], logging.INFO))

    # Clear existing handlers to avoid duplicates on reconfigure
    root.handlers.clear()

    log_file = config["log_dir"] / f"verification-{datetime.now(UTC).strftime('%Y%m%d')}.log"
    config["log_file"] = str(log_file)
    config["configured_at"] = datetime.now(UTC).isoformat()

    # JSON file handler with rotation
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_file),
        maxBytes=config["max_bytes"],
        backupCount=config["backup_count"],
        encoding="utf-8",
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.addFilter(_CorrelationFilter())
    root.addHandler(file_handler)

    # Console handler (human-readable)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(HumanFormatter())
        console_handler.addFilter(_CorrelationFilter())
        root.addHandler(console_handler)

    _LOGGING_CONFIGURED = True

    if correlation_id:
        set_correlation_id(correlation_id)

    return config


def get_logger(name: str) -> logging.Logger:
    """Get a logger configured with the structured logging setup.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    # Ensure the logger inherits from root (which has our handlers)
    if not logger.handlers and logging.getLogger().handlers:
        logger.propagate = True
    return logger


def add_correlation_id(logger: logging.Logger, run_id: str) -> None:
    """Add a correlation ID to all subsequent log entries from this logger.

    Note: Correlation IDs are thread-local. This sets the ID for the
    current thread only.
    """
    set_correlation_id(run_id)
    # Also attach to logger for documentation
    logger.correlation_id = run_id


def get_config() -> dict[str, Any]:
    """Return the current logging configuration."""
    return {
        "configured": _LOGGING_CONFIGURED,
        "handlers": len(logging.getLogger().handlers),
        "level": logging.getLogger().level,
    }


def reset_logging() -> None:
    """Reset logging configuration (for tests)."""
    global _LOGGING_CONFIGURED
    root = logging.getLogger()
    root.handlers.clear()
    _LOGGING_CONFIGURED = False
    set_correlation_id(None)
