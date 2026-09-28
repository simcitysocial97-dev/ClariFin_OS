"""M08 — orchestrator persistence & has_errors surface (import_runs).

Verifies:
  - process_after_upload computes ``has_errors`` from stage keys.
  - A persisted ``import_runs`` row is created on every call.
  - Forcing one stage to fail yields ``has_errors=True``.
  - Migration 004 is idempotent and registered in version order.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.db.schema import create_all
from src.core.db.migrations._registry import apply_pending_migrations
from src.orchestration.statement_orchestrator import StatementProcessingOrchestrator


def _make_orchestrator(tmp_path: Path, db_path: str) -> StatementProcessingOrchestrator:
    """Create an orchestrator pointing at a freshly migrated scratch DB."""
    create_all(db_path)
    conn = sqlite3.connect(db_path)
    applied = apply_pending_migrations(conn)
    conn.close()
    assert 4 in applied, "Migration 004 (import_runs) must have been applied"
    return StatementProcessingOrchestrator(db_path=db_path)


def test_has_errors_false_on_full_success(tmp_path: Path) -> None:
    """All stages succeed → ``has_errors`` is False."""
    db_path = str(tmp_path / "m08_success.db")
    orch = _make_orchestrator(tmp_path, db_path)

    # Stub every stage so no real service call can raise.
    with patch.object(orch, "_run_behaviour", return_value={"ok": True}), \
         patch.object(orch, "_run_cashflow", return_value={"ok": True}), \
         patch.object(orch, "_run_intelligence", return_value={"ok": True}), \
         patch.object(orch, "_run_recommendations", return_value={"ok": True}), \
         patch.object(orch, "_run_dashboard_refresh", return_value={"ok": True}), \
         patch.object(orch, "_run_transaction_intelligence", return_value={"ok": True}):
        summary = orch.process_after_upload(statement_id=1)

    assert summary["has_errors"] is False
    assert all(k in summary for k in ("behaviour", "cashflow", "intelligence",
                                      "recommendations", "dashboard",
                                      "transaction_intelligence"))
    # Persistence: exactly one row for statement_id=1.
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, statement_id, has_errors FROM import_runs"
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][1] == 1
        assert rows[0][2] == 0
    finally:
        conn.close()


def test_has_errors_true_when_stage_fails(tmp_path: Path) -> None:
    """A single failing stage yields ``has_errors=True``."""
    db_path = str(tmp_path / "m08_fail.db")
    orch = _make_orchestrator(tmp_path, db_path)

    def _raise(_self: object, **_kw: object) -> None:
        raise RuntimeError("boom")

    # Stub successful stages, force behaviour to fail.
    with patch.object(orch, "_run_behaviour", side_effect=_raise), \
         patch.object(orch, "_run_cashflow", return_value={"ok": True}), \
         patch.object(orch, "_run_intelligence", return_value={"ok": True}), \
         patch.object(orch, "_run_recommendations", return_value={"ok": True}), \
         patch.object(orch, "_run_dashboard_refresh", return_value={"ok": True}), \
         patch.object(orch, "_run_transaction_intelligence", return_value={"ok": True}):
        summary = orch.process_after_upload(statement_id=2)

    assert summary["has_errors"] is True
    assert "behaviour_error" in summary
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT has_errors, summary_json FROM import_runs WHERE statement_id = ?",
            (2,),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == 1
        parsed = json.loads(rows[0][1])
        assert parsed["has_errors"] is True
        assert "behaviour_error" in parsed
    finally:
        conn.close()


def test_migration_004_idempotent(tmp_path: Path) -> None:
    """Applying migration 004 twice: no error, identical schema."""
    from src.core.db.migrations.m004_import_runs import migrate as m004

    db_path = str(tmp_path / "m08_mig.db")
    create_all(db_path)
    conn = sqlite3.connect(db_path)
    try:
        first = apply_pending_migrations(conn)
        assert 4 in first
        tables_first = {
            r[1]
            for r in conn.execute(
                "SELECT type, name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        second = apply_pending_migrations(conn)
        assert second == []
        tables_second = {
            r[1]
            for r in conn.execute(
                "SELECT type, name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert tables_first == tables_second
        assert "import_runs" in tables_first
    finally:
        conn.close()
