"""
Base service class for business orchestration.
"""

import os
from pathlib import Path

from src.config import settings


class BaseService:
    """
    Base class for service layer.

    Services orchestrate repositories and engines to implement business logic.
    They should NOT contain SQL queries.
    """

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = (
                getattr(settings, "_database_path_override", None)
                or os.getenv("FINANCE_DB_PATH")
                or str(Path(__file__).resolve().parent.parent / "data" / "finance.db")
            )
        self.db_path = str(db_path)
