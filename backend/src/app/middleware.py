"""Middleware configuration for the FastAPI application."""

import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.logger import log


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the application."""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        log.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms
        )
        
        return response
