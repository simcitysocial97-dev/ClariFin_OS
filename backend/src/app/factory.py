"""FastAPI application factory.

Creates and configures the FastAPI application instance.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.logger import log
from src.dependencies import close_db, DB_PATH, UPLOAD_DIR
from src.startup_checks import StartupValidator
from app.middleware import setup_middleware
from app.exceptions import setup_exception_handlers
from app.router_registry import register_routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    log.info("ClariFin backend starting up")
    
    # Run startup validation checks
    try:
        validator = StartupValidator(db_path=DB_PATH, upload_dir=UPLOAD_DIR)
        validator.run_all_checks()
    except RuntimeError as e:
        log.error("Startup validation failed: %s", str(e))
        raise  # Re-raise to prevent uvicorn from accepting requests
    
    yield
    
    close_db()
    log.info("ClariFin backend shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Personal Finance API",
        description="REST API for personal finance tracker",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Register all routers
    register_routers(app)
    
    # Health check endpoint
    @app.get("/api/health")
    def health_check():
        return {"status": "ok"}
    
    return app
