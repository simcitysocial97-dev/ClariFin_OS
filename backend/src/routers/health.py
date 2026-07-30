"""Health check and readiness endpoints."""

# Re-export from existing health module
from src.health import register_health_routes, router

__all__ = ["router", "register_health_routes"]
