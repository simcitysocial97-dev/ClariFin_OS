"""
Configuration Module
====================

Central configuration for ClariFin_OS backend.
All environment variables with sensible defaults and validation.

Usage:
    from config import settings
    db_path = settings.database_path
"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """
    Application settings loaded from environment variables.
    
    All values have sensible defaults for local development.
    Missing required values will raise clear errors on startup.
    """
    
    # Database Configuration
    @property
    def database_path(self) -> Path:
        """Path to SQLite database file."""
        return Path(os.getenv("DATABASE_PATH", "data/finance.db"))
    
    @property
    def upload_dir(self) -> Path:
        """Directory for uploaded files."""
        return Path(os.getenv("UPLOAD_DIR", "data/uploads"))
    
    # Server Configuration
    @property
    def backend_port(self) -> int:
        """Port for the backend server."""
        return int(os.getenv("BACKEND_PORT", "8000"))
    
    @property
    def frontend_port(self) -> int:
        """Port for the frontend server."""
        return int(os.getenv("FRONTEND_PORT", "3000"))
    
    @property
    def api_url(self) -> str:
        """Base URL for the API (used by frontend)."""
        return os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")
    
    # CORS Configuration
    @property
    def cors_origins(self) -> list[str]:
        """Allowed CORS origins for the API."""
        origins = os.getenv("CORS_ORIGINS", "")
        if origins:
            return [o.strip() for o in origins.split(",")]
        return [
            f"http://localhost:{self.frontend_port}",
            f"http://localhost:{self.frontend_port + 1}",
        ]
    
    # Logging Configuration
    @property
    def log_level(self) -> str:
        """Log level (DEBUG, INFO, WARNING, ERROR)."""
        return os.getenv("LOG_LEVEL", "INFO").upper()
    
    @property
    def log_format(self) -> str:
        """Log format string."""
        return os.getenv(
            "LOG_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Validation Configuration
    @property
    def max_upload_size_mb(self) -> int:
        """Maximum upload file size in megabytes."""
        return int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload file size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024
    
    # Security Configuration
    @property
    def allowed_file_extensions(self) -> list[str]:
        """Allowed file extensions for upload."""
        return os.getenv("ALLOWED_EXTENSIONS", ".pdf,.csv,.xlsx,.xls").split(",")
    
    # Feature Flags
    @property
    def enable_analytics(self) -> bool:
        """Enable analytics engine."""
        return os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    
    @property
    def enable_behavior_engine(self) -> bool:
        """Enable behavior analysis engine."""
        return os.getenv("ENABLE_BEHAVIOR_ENGINE", "true").lower() == "true"
    
    def validate(self) -> list[str]:
        """
        Validate configuration and return list of errors.
        
        Returns:
            List of error messages. Empty list if all valid.
        """
        errors = []
        
        # Check database directory exists or can be created
        db_dir = self.database_path.parent
        if not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create database directory: {e}")
        
        # Check upload directory
        if not self.upload_dir.exists():
            try:
                self.upload_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create upload directory: {e}")
        
        # Validate port numbers
        if not (1 <= self.backend_port <= 65535):
            errors.append(f"Invalid BACKEND_PORT: {self.backend_port}")
        
        if not (1 <= self.frontend_port <= 65535):
            errors.append(f"Invalid FRONTEND_PORT: {self.frontend_port}")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            errors.append(f"Invalid LOG_LEVEL: {self.log_level}. Must be one of {valid_levels}")
        
        return errors


# Global settings instance
settings = Settings()


def validate_startup() -> None:
    """
    Validate configuration on startup.
    
    Raises:
        RuntimeError: If any required configuration is invalid.
    """
    errors = settings.validate()
    if errors:
        raise RuntimeError(
            "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )