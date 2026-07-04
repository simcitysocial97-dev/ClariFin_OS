"""Pagination utilities for database queries."""

import sqlite3
from dataclasses import dataclass
from typing import Any, List


@dataclass
class PaginatedResult:
    """Result container for paginated queries."""
    items: list[dict[str, Any]]
    total: int
    page: int
    per_page: int
    has_next: bool


def paginate_query(
    conn: sqlite3.Connection,
    base_query: str,
    count_query: str,
    params: tuple,
    page: int = 1,
    per_page: int = 50,
) -> PaginatedResult:
    """
    Execute a paginated query.
    
    Args:
        conn: SQLite connection
        base_query: SELECT query WITHOUT LIMIT/OFFSET
        count_query: SELECT COUNT(*) query with same WHERE clause
        params: Query parameters for both queries
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        PaginatedResult with items and pagination metadata
    """
    # Get total count
    cur = conn.execute(count_query, params)
    total = cur.fetchone()[0]
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Execute paginated query
    paginated_sql = f"{base_query} LIMIT ? OFFSET ?"
    cur = conn.execute(paginated_sql, params + (per_page, offset))
    items = [dict(row) for row in cur.fetchall()]
    
    # Calculate has_next
    has_next = (offset + per_page) < total
    
    return PaginatedResult(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        has_next=has_next,
    )
