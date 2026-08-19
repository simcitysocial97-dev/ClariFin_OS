"""
Startup Validation Module
=========================

Validates configuration and dependencies on application startup.
Fails early with clear diagnostics if critical dependencies are missing.
"""

import sys

from src.config import settings, validate_startup
from src.core.db.connection import get_connection
from src.logger import log_error, log_info


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
            raise RuntimeError(f"Cannot create database directory: {e}") from e

    upload_dir = settings.upload_dir
    if not upload_dir.exists():
        log_info(f"Creating upload directory: {upload_dir}")
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log_error(f"Cannot create upload directory: {upload_dir}", error=e)
            raise RuntimeError(f"Cannot create upload directory: {e}") from e

    # Initialize the SQLite schema before serving (idempotent):
    # CREATE IF NOT EXISTS tables/indexes/triggers + guarded data/schema
    # migrations. This is the single canonical owner of schema initialization
    # (core/db/schema.py); the test suite and any operator bootstrap must use the
    # same path. Safe to run on an existing populated database.
    try:
        from src.core.db.schema import create_all, run_migrations, verify_schema

        db_path = str(settings.database_path)
        create_all(db_path)
        run_migrations(db_path)
        try:
            verify_schema(db_path)
            log_info("Database schema initialized and verified")
        except RuntimeError as e:
            log_error("Database schema verification failed", error=e)
            raise
    except Exception as e:
        log_error("Database schema initialization failed", error=e)
        raise RuntimeError(f"Database schema initialization failed: {e}") from e

    # Check database connectivity (if exists)
    if settings.database_path.exists():
        try:
            conn = get_connection(str(settings.database_path))
            conn.execute("SELECT 1 FROM transactions LIMIT 1")
            conn.close()
            log_info("Database connectivity verified")
        except Exception as e:
            log_error("Database connectivity check failed", error=e)
            raise RuntimeError(f"Database connectivity check failed: {e}") from e
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
