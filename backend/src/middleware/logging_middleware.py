"""App-wide request logging middleware.

Logs method/path/status/duration/correlation-id for every request, closing
the gap where routers with no application-level logging emit nothing.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.logger import log_request


class LoggingMiddleware(BaseHTTPMiddleware):
    """Emit one structured log line per request via ``src.logger.log_request``."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Time the request, propagate/generate X-Correlation-Id, then log."""
        correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())

        # Forward the correlation id downstream so any inner correlation
        # middleware (e.g. platform routes) reuses the same value instead of
        # generating a divergent one.
        raw_headers = [
            (k, v)
            for k, v in request.scope.get("headers", [])
            if k.lower() != b"x-correlation-id"
        ]
        raw_headers.append((b"x-correlation-id", correlation_id.encode("ascii")))
        request.scope["headers"] = raw_headers

        start = time.monotonic()
        response = await call_next(Request(request.scope, request.receive))
        duration_ms = (time.monotonic() - start) * 1000.0

        if "x-correlation-id" not in response.headers:
            response.headers["X-Correlation-Id"] = correlation_id

        log_request(
            request.method,
            request.url.path,
            response.status_code,
            duration_ms=round(duration_ms, 1),
            correlation_id=correlation_id,
        )
        return response
