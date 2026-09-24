"""M06: forced internal exceptions surface generic hidden-internals messages.

Each case forces a RuntimeError carrying a sentinel string inside one swept
router and asserts the client-visible response hides the sentinel and shows
the generic hidden-internals message. The sentinel must still be recorded
server-side via the centralized ``log_error()`` path (M06-T4).
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient

SENTINEL = "SENTINEL_m06_secret_detail_do_not_leak"


class _Boom:
    """Stand-in service whose construction raises with a secret message."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError(SENTINEL)


# (module, service symbol, http method, url) — one entry per swept router.
_SWEPT_ROUTERS = [
    ("src.routers.audit", "AuditService", "get", "/api/v1/audit/report"),
    ("src.routers.dashboard", "DashboardService", "get", "/api/v1/dashboard/summary"),
    ("src.routers.export", "ExportService", "get", "/api/v1/export/csv"),
    ("src.routers.transactions", "TransactionService", "get", "/api/v1/transactions"),
    ("src.routers.cashflow", "CashflowService", "get", "/api/v1/cashflow"),
    (
        "src.routers.financial_events",
        "FinancialEventsService",
        "get",
        "/api/v1/financial-events/",
    ),
    (
        "src.routers.reconciliation",
        "ReconciliationService",
        "get",
        "/api/v1/reconciliation",
    ),
    ("src.routers.cards_statements", "StatementService", "get", "/api/v1/statements"),
]


def _make_client(seeded_db: Any) -> TestClient:
    """Bind a TestClient to the isolated seeded DB, allowing 500 responses."""
    from src.api import app

    app.state.db_path = str(seeded_db.db_path)
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("module_name,service_name,method,url", _SWEPT_ROUTERS)
def test_forced_exception_returns_generic_message(
    seeded_db: Any,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    module_name: str,
    service_name: str,
    method: str,
    url: str,
) -> None:
    """A forced internal exception hides its details behind the generic message."""
    module = importlib.import_module(module_name)
    monkeypatch.setattr(module, service_name, _Boom)

    client = _make_client(seeded_db)
    with caplog.at_level(logging.ERROR):
        response = getattr(client, method)(url)

    assert response.status_code == 500, response.text
    assert SENTINEL not in response.text, response.text
    assert "Internal server error" in response.text, response.text
    # M06-T4: centralized log_error() still records the raw exception server-side
    assert SENTINEL in caplog.text


def test_managed_accounts_banned_pattern_removed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """managed_accounts: banned catch-and-500 is gone; the raw error propagates.

    NOTE: ``backend/src/routers/managed_accounts.py`` is not registered in
    ``backend/src/api.py`` (pre-existing, discovered during M06), so its
    routes are unreachable over HTTP. The function-level assertion proves the
    banned ``except Exception -> HTTPException(500, str(e))`` wrapper no
    longer intercepts the exception; once the router is mounted (outside M06
    scope), it will flow to the generic hidden-internals handler like the
    other swept routers.
    """
    from src.routers import managed_accounts

    monkeypatch.setattr(managed_accounts, "AccountService", _Boom)

    with pytest.raises(RuntimeError, match=SENTINEL):
        managed_accounts.api_get_managed_accounts()


def test_import_router_forced_exception_returns_generic_message(
    seeded_db: Any,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    tmp_path: Any,
) -> None:
    """import_router upload hides internals and logs them centrally (M06-T4)."""
    from src.routers import import_router

    monkeypatch.setattr(import_router, "ImportService", _Boom)
    monkeypatch.setattr(import_router, "UPLOAD_DIR", tmp_path)

    client = _make_client(seeded_db)
    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/api/v1/upload",
            files={
                "file": ("statement.pdf", b"%PDF-1.4 forced-error", "application/pdf")
            },
        )

    assert response.status_code == 500, response.text
    assert SENTINEL not in response.text, response.text
    assert "Internal server error" in response.text, response.text
    assert SENTINEL in caplog.text


def test_platform_forced_exception_returns_generic_message(
    seeded_db: Any,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """platform diagnose hides internals behind 'Internal platform error'."""
    from runtime.platform.ai import agents as ai_agents

    class _BoomAgent:
        def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
            raise RuntimeError(SENTINEL)

    monkeypatch.setattr(ai_agents, "get_agent", lambda name: _BoomAgent())

    client = _make_client(seeded_db)
    with caplog.at_level(logging.WARNING):
        response = client.post(
            "/platform/v1/ai/diagnose", json={"symptom": "forced error"}
        )

    assert response.status_code == 500, response.text
    assert SENTINEL not in response.text, response.text
    assert "Internal platform error" in response.text, response.text
    # centralized warning log keeps the raw exception server-side
    assert SENTINEL in caplog.text
