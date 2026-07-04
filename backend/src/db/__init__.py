"""Database package for ClariFin.

This package provides database access through the FinanceDB class
and repository modules for specific domains.
"""

# Re-export FinanceDB for backward compatibility
from .core import FinanceDB
from .pagination import PaginatedResult, paginate_query

# Re-export utility functions for backward compatibility
from .core import _parse_date_to_ymd

__all__ = ["FinanceDB", "PaginatedResult", "paginate_query", "_parse_date_to_ymd"]
