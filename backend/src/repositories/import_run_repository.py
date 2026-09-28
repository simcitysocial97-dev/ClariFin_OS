"""Import run persistence repository (M08).

Stores per-upload pipeline summaries so partial-failure visibility is
available outside the HTTP response envelope.
"""

from __future__ import annotations

import json
from typing import Any

from src.repositories.base import BaseRepository


class ImportRunRepository(BaseRepository):
    """Persist post-upload orchestration summaries to ``import_runs``."""

    def save(self, statement_id: int | None, summary: dict[str, Any]) -> int:
        """Insert a row and return its ``id``.

        Args:
            statement_id: ID of the uploaded statement (``None`` for CSV).
            summary: Pipeline summary dict (will be JSON-encoded).

        Returns:
            The new row's ``id``.
        """
        has_errors = int(any(k.endswith("_error") for k in summary))
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO import_runs (statement_id, has_errors, summary_json)
                VALUES (?, ?, ?)
                """,
                (statement_id, has_errors, json.dumps(summary)),
            )
            conn.commit()
            last = cursor.lastrowid
            assert last is not None, "INSERT must return a row id"
            return int(last)

    def get_by_statement(self, statement_id: int) -> list[dict[str, Any]]:
        """Return all rows for a given statement, newest first."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, statement_id, started_at, completed_at,
                       has_errors, summary_json, created_at
                FROM import_runs
                WHERE statement_id = ?
                ORDER BY id DESC
                """,
                (statement_id,),
            ).fetchall()
        return [
            {
                "id": r[0],
                "statement_id": r[1],
                "started_at": r[2],
                "completed_at": r[3],
                "has_errors": bool(r[4]),
                "summary_json": r[5],
                "created_at": r[6],
            }
            for r in rows
        ]
