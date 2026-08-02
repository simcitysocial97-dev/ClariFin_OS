"""
Base service class for business orchestration.
"""

from src.core.db.config import get_db_path
from src.repositories.base import BaseRepository


class BaseService:
    """
    Base class for service layer.

    Services orchestrate repositories and engines to implement business logic.
    They should NOT contain SQL queries.
    """

    def __init__(
        self,
        db_path: str | None = None,
        repository: BaseRepository | None = None,
    ):
        self.db_path = get_db_path(db_path)
        self.repository = repository
