"""
Impact Rules Engine for Program 5 — Selective Verification.

Pure functions that classify file changes and extract affected components.
No side effects. No file I/O. Deterministic output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class ChangeClassification:
    """Classification of a file change for verification planning."""

    file_path: str
    change_type: Literal[
        "engine", "service", "router", "model", "test", "config", "other"
    ]
    engine_name: Optional[str] = None
    router_name: Optional[str] = None
    blast_radius: Literal["low", "medium", "high", "full"] = "low"


def engine_changed(file_path: str) -> bool:
    """Rule 1: Returns True if file is in backend/src/engines/"""
    return file_path.startswith("backend/src/engines/")


def service_changed(file_path: str) -> bool:
    """Rule 2: Returns True if file is in backend/src/services/"""
    return file_path.startswith("backend/src/services/")


def router_changed(file_path: str) -> bool:
    """Rule 3: Returns True if file is in backend/src/routers/"""
    return file_path.startswith("backend/src/routers/")


def model_changed(file_path: str) -> bool:
    """Rule 4: Returns True if file is in backend/src/models/, backend/src/core/dtos/, or backend/src/core/domain/"""
    return (
        file_path.startswith("backend/src/models/")
        or file_path.startswith("backend/src/core/dtos/")
        or file_path.startswith("backend/src/core/domain/")
    )


def test_changed(file_path: str) -> bool:
    """Rule 5: Returns True if file is in backend/tests/ (excluding generated artifacts)"""
    if not file_path.startswith("backend/tests/"):
        return False
    if file_path.startswith("backend/tests/generated/"):
        return False
    return True


def config_changed(file_path: str) -> bool:
    """Rule 6: Returns True if file is a config file (pyproject.toml, .coveragerc, ruff.toml, or *.cfg)"""
    return (
        file_path == "backend/pyproject.toml"
        or file_path == "backend/.coveragerc"
        or file_path == "backend/ruff.toml"
        or (file_path.endswith(".cfg") and file_path.startswith("backend/"))
    )


def extract_engine_name(file_path: str) -> Optional[str]:
    if not engine_changed(file_path):
        return None
    parts = file_path.split("/")
    for part in parts:
        if part.endswith("_engine"):
            return part.replace("_engine", "")
    for part in parts:
        name = part.replace(".py", "")
        if name.endswith("_engine"):
            return name.replace("_engine", "")
    return None


def extract_router_name(file_path: str) -> Optional[str]:
    """Extract router name from path. Returns None if not a router file."""
    if not router_changed(file_path):
        return None
    parts = file_path.split("/")
    filename = parts[-1]
    return filename.replace(".py", "")


def classify_change(file_path: str) -> ChangeClassification:
    """Classify a file change using the 6 rules."""
    if engine_changed(file_path):
        engine_name = extract_engine_name(file_path)
        return ChangeClassification(
            file_path=file_path,
            change_type="engine",
            engine_name=engine_name,
            blast_radius="medium",
        )
    elif service_changed(file_path):
        return ChangeClassification(
            file_path=file_path,
            change_type="service",
            blast_radius="medium",
        )
    elif router_changed(file_path):
        router_name = extract_router_name(file_path)
        return ChangeClassification(
            file_path=file_path,
            change_type="router",
            router_name=router_name,
            blast_radius="medium",
        )
    elif model_changed(file_path):
        return ChangeClassification(
            file_path=file_path,
            change_type="model",
            blast_radius="high",
        )
    elif test_changed(file_path):
        return ChangeClassification(
            file_path=file_path,
            change_type="test",
            blast_radius="low",
        )
    elif config_changed(file_path):
        return ChangeClassification(
            file_path=file_path,
            change_type="config",
            blast_radius="full",
        )
    else:
        return ChangeClassification(
            file_path=file_path,
            change_type="other",
            blast_radius="low",
        )
