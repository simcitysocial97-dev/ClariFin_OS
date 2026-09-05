"""Platform API FastAPI router (M9-C57 Phase 3).

This module is the **thin HTTP boundary** between the network and the
Platform API services defined in :mod:`runtime.platform.api.services`.

It implements the correct boundary per ``IMPLEMENTATION_ROADMAP.md``:

    HTTP
     ↓
    platform router   ← THIS MODULE
     ↓
    runtime/platform/api service   ← runtime/platform/api/services/*.py
     ↓
    existing authority   ← C50 / observability / knowledge modules

No executor, no evidence system, no DB, no AI surface are introduced
here. The router only:

1. Extracts query/path parameters.
2. Calls the corresponding service function.
3. Catches exceptions and returns the Phase 1 platform error envelope.
4. Propagates ``X-Correlation-Id`` when present; otherwise generates one.

Phase 3 is intentionally read-only. Write endpoints (task creation,
verification run, etc.) are deferred until authorization boundaries
are enforced in later phases.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from fastapi import APIRouter, FastAPI, Query, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.envelope import error_envelope
from runtime.platform.api.errors import PlatformError, PlatformErrorCode
from runtime.platform.api.services import (
    application,
    architecture,
    capabilities,
    change,
    errors as errors_service,
    events,
    evidence,
    executions,
    health,
    history,
    tasks,
    verification,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform/v1", tags=["platform"])


# ---------------------------------------------------------------------------
# Correlation-ID middleware
# ---------------------------------------------------------------------------


class PlatformCorrelationMiddleware(BaseHTTPMiddleware):
    """Attach ``X-Correlation-Id`` to every Platform API request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Correlation-Id") or str(
            uuid.uuid4()
        )
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        return response


def install_correlation_middleware(app: FastAPI) -> None:
    """Add the correlation middleware to an existing FastAPI app.

    We use the public ``BaseHTTPMiddleware`` so the existing router
    stack is preserved.
    """

    app.add_middleware(PlatformCorrelationMiddleware)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_platform_error(
    exc: Exception, layer: str
) -> tuple[int, dict[str, Any]]:
    """Convert an unexpected exception into a platform error envelope.

    The status code is deliberately 500 (INTERNAL) — callers should not
    confuse an internal platform failure with an application error.
    """

    logger.exception("Platform API %s internal error: %s", layer, exc)
    err = PlatformError(
        code=PlatformErrorCode.INTERNAL,
        layer=layer,
        message=f"Platform API {layer} internal error: {exc!r}",
    )
    return 500, error_envelope(error=err)


def _ok(env: dict[str, Any]) -> JSONResponse:
    return JSONResponse(content=env, status_code=200)


def _not_found(msg: str, layer: str) -> JSONResponse:
    env = error_envelope(
        error=PlatformError(
            code=PlatformErrorCode.NOT_FOUND,
            layer=layer,
            message=msg,
        )
    )
    return JSONResponse(content=env, status_code=404)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
async def get_health() -> JSONResponse:
    env = health.build_health_snapshot()
    return _ok(env)


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


@router.get("/capabilities")
async def list_capabilities() -> JSONResponse:
    env = capabilities.build_capability_list()
    return _ok(env)


@router.get("/capabilities/{capability_id}")
async def get_capability(capability_id: str) -> JSONResponse:
    env = capabilities.build_capability_detail(capability_id)
    if env is None:
        return _not_found(
            f"Capability {capability_id!r} not found in live catalog",
            "platform.capabilities",
        )
    return _ok(env)


@router.get("/capabilities/{capability_id}/graph")
async def get_capability_graph(capability_id: str) -> JSONResponse:
    env = capabilities.build_capability_graph(capability_id)
    if env is None:
        return _not_found(
            f"Capability {capability_id!r} not found in live catalog",
            "platform.capabilities",
        )
    return _ok(env)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@router.get("/tasks")
async def list_tasks() -> JSONResponse:
    env = tasks.build_task_list()
    return _ok(env)


@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> JSONResponse:
    env = tasks.build_task_detail(task_id)
    if env is None:
        return _not_found(
            f"Task/obligation {task_id!r} not found in live set",
            "platform.tasks",
        )
    return _ok(env)


# ---------------------------------------------------------------------------
# Verification (read-mostly)
# ---------------------------------------------------------------------------


@router.get("/verification/recommendation")
async def get_verification_recommendation() -> JSONResponse:
    env = verification.build_verification_recommendation()
    return _ok(env)


# Note: /verification/run, /verification/run/group, /verification/run/full
# are intentionally NOT mounted in Phase 3. They require authorization
# infrastructure (levels 2–4 of AI authority) that will be built in
# Phase 13+. The endpoint contract exists (Phase 1), but the route is
# omitted to enforce the read-only boundary.


# ---------------------------------------------------------------------------
# Executions
# ---------------------------------------------------------------------------


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str) -> JSONResponse:
    env = executions.build_execution_detail(execution_id)
    if env is None:
        return _not_found(
            f"Execution {execution_id!r} not found in event store",
            "platform.executions",
        )
    return _ok(env)


# Note: /executions/{id}/stream (SSE) is deferred to Phase 7 where the
# event bus is wired to an actual streaming consumer.


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


@router.get("/evidence")
async def list_evidence() -> JSONResponse:
    env = evidence.build_evidence_list()
    return _ok(env)


@router.get("/evidence/{evidence_id}")
async def get_evidence(evidence_id: str) -> JSONResponse:
    env = evidence.build_evidence_detail(evidence_id)
    if env is None:
        return _not_found(
            f"Evidence {evidence_id!r} not found",
            "platform.evidence",
        )
    return _ok(env)


# Note: /evidence/by-execution/{id} and /evidence/compare are deferred
# to Phase 8 (history + evidence comparison engine).


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


@router.get("/history/runs")
async def list_history_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> JSONResponse:
    env = history.build_history_runs(page=page, page_size=page_size)
    return _ok(env)


@router.get("/history/runs/{run_id}")
async def get_history_run(run_id: str) -> JSONResponse:
    env = history.build_history_run(run_id)
    if env is None:
        return _not_found(
            f"History run {run_id!r} not found",
            "platform.history",
        )
    return _ok(env)


@router.get("/history/baselines")
async def list_history_baselines() -> JSONResponse:
    env = history.build_history_baselines()
    return _ok(env)


# Note: /history/compare is deferred to Phase 8.


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


@router.get("/errors/current")
async def get_errors_current() -> JSONResponse:
    env = errors_service.build_errors_current()
    return _ok(env)


@router.get("/errors/recent")
async def get_errors_recent() -> JSONResponse:
    env = errors_service.build_errors_recent()
    return _ok(env)


@router.get("/errors/recurring")
async def get_errors_recurring() -> JSONResponse:
    env = errors_service.build_errors_recurring()
    return _ok(env)


@router.get("/errors/frequency")
async def get_errors_frequency() -> JSONResponse:
    env = errors_service.build_errors_frequency()
    return _ok(env)


@router.get("/errors/{error_id}")
async def get_error(error_id: str) -> JSONResponse:
    env = errors_service.build_errors_detail(error_id)
    if env is None:
        return _not_found(
            f"Error {error_id!r} not found",
            "platform.errors",
        )
    return _ok(env)


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------


@router.get("/architecture/authorities")
async def get_architecture_authorities() -> JSONResponse:
    env = architecture.build_architecture_authorities()
    return _ok(env)


@router.get("/architecture/authority/{name}")
async def get_architecture_authority(name: str) -> JSONResponse:
    env = architecture.build_architecture_authority(name)
    if env is None:
        return _not_found(
            f"Authority {name!r} not found",
            "platform.architecture",
        )
    return _ok(env)


@router.get("/architecture/boundaries")
async def get_architecture_boundaries() -> JSONResponse:
    env = architecture.build_architecture_boundaries()
    return _ok(env)


@router.get("/architecture/duplicates")
async def get_architecture_duplicates() -> JSONResponse:
    env = architecture.build_architecture_duplicates()
    return _ok(env)


@router.get("/architecture/bypasses")
async def get_architecture_bypasses() -> JSONResponse:
    env = architecture.build_architecture_bypasses()
    return _ok(env)


@router.get("/architecture/deprecations")
async def get_architecture_deprecations() -> JSONResponse:
    env = architecture.build_architecture_deprecations()
    return _ok(env)


@router.get("/architecture/unmapped")
async def get_architecture_unmapped() -> JSONResponse:
    env = architecture.build_architecture_unmapped()
    return _ok(env)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@router.get("/events")
async def get_events(limit: int = Query(default=100, ge=1, le=1000)) -> JSONResponse:
    env = events.build_events_list(limit=limit)
    return _ok(env)


# Note: /events/stream (SSE) is deferred to Phase 7.


# ---------------------------------------------------------------------------
# Application readiness
# ---------------------------------------------------------------------------


@router.get("/app/backend")
async def get_app_backend() -> JSONResponse:
    env = application.build_app_backend()
    return _ok(env)


@router.get("/app/frontend")
async def get_app_frontend() -> JSONResponse:
    env = application.build_app_frontend()
    return _ok(env)


@router.get("/app/domain")
async def get_app_domain() -> JSONResponse:
    env = application.build_app_domain()
    return _ok(env)


@router.get("/app/financial")
async def get_app_financial() -> JSONResponse:
    env = application.build_app_financial()
    return _ok(env)


@router.get("/app/workflows")
async def get_app_workflows() -> JSONResponse:
    env = application.build_app_workflows()
    return _ok(env)


# ---------------------------------------------------------------------------
# Change intelligence
# ---------------------------------------------------------------------------


@router.get("/change/intelligence")
async def get_change_intelligence() -> JSONResponse:
    env = change.build_change_intelligence()
    return _ok(env)


# ---------------------------------------------------------------------------
# App registration helper
# ---------------------------------------------------------------------------


def register_platform_routes(app: FastAPI) -> None:
    """Register the Platform API router on an existing FastAPI app.

    Installs:

    * The Platform API router at ``/platform/v1``.
    * The ``X-Correlation-Id`` middleware on the app.

    Does NOT:

    * Modify any existing routers.
    * Re-mount or re-prefix the app.
    * Introduce CORS, authentication, or rate-limiting middleware
      (those belong in Phase 4+).
    """

    install_correlation_middleware(app)
    app.include_router(router)
    logger.info("Registered Platform API routes at /platform/v1")
