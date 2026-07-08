"""
Base service class for business orchestration.
"""

from src.api_common import DB_PATH


class BaseService:
    """
    Base class for service layer.

    Services orchestrate repositories and engines to implement business logic.
    They should NOT contain SQL queries.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DB_PATH
