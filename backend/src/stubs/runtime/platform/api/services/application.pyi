from __future__ import annotations

from typing import Any

__all__ = [
    "build_app_backend",
    "build_app_frontend",
    "build_app_domain",
    "build_app_financial",
    "build_app_workflows",
]

def build_app_backend() -> dict[str, Any]: ...
def build_app_frontend() -> dict[str, Any]: ...
def build_app_domain() -> dict[str, Any]: ...
def build_app_financial() -> dict[str, Any]: ...
def build_app_workflows() -> dict[str, Any]: ...
