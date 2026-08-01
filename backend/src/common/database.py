"""
Database access utilities.

.. deprecated::
    This module is a legacy compatibility shim. All new code should use
    ``src.core.db`` directly:

    - ``src.core.db.get_db_path`` — canonical path resolution
    - ``src.core.db.get_connection`` — canonical connection factory
    - ``src.core.db.schema.create_all`` — schema initialization

    ``get_db()`` is deprecated with zero production consumers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.db import FinanceDB


def get_db() -> FinanceDB:
    """DEPRECATED: Use repository classes for data access."""
    from src.db import FinanceDB

    return FinanceDB()
