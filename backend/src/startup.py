"""
Startup Validation Module
=========================

Validates configuration and dependencies on application startup.
Fails early with clear diagnostics if critical dependencies are missing.
"""

import sys

from config import settings, validate_startup
from logger import log_error, log_info


def run_startup_validation() -> bool:
    """
    Run all startup validation checks.

    Returns:
        True if all checks pass, raises RuntimeError otherwise.

    Raises:
        RuntimeError: If any critical validation fails
    """
    log_info("Starting ClariFin_OS startup validation...")

    # Validate configuration
    try:
        validate_startup()
        log_info("Configuration validation passed")
    except RuntimeError as e:
        log_error("Configuration validation failed", error=e)
        raise

    # Check required directories
    db_dir = settings.database_path.parent
    if not db_dir.exists():
        log_info(f"Creating database directory: {db_dir}")
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log_error(f"Cannot create database directory: {db_dir}", error=e)
            raise RuntimeError(f"Cannot create database directory: {e}")

    upload_dir = settings.upload_dir
    if not upload_dir.exists():
        log_info(f"Creating upload directory: {upload_dir}")
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log_error(f"Cannot create upload directory: {upload_dir}", error=e)
            raise RuntimeError(f"Cannot create upload directory: {e}")

    # Check database connectivity (if exists)
    if settings.database_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(settings.database_path))
            conn.execute("SELECT 1 FROM transactions LIMIT 1")
            conn.close()
            log_info("Database connectivity verified")
        except Exception as e:
            log_error("Database connectivity check failed", error=e)
            raise RuntimeError(f"Database connectivity check failed: {e}")
    else:
        log_info("Database not found - will be created on first use")

    log_info("Startup validation complete - all systems ready")
    return True


if __name__ == "__main__":
    try:
        run_startup_validation()
        print("✅ All startup checks passed")
        sys.exit(0)
    except RuntimeError as e:
        print(f"❌ Startup validation failed: {e}")
        sys.exit(1)
