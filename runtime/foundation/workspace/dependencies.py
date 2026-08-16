"""Dependency Explorer — Program 9.

Command: python runtime/verify.py deps [file_path]

Input: optional file path
Output: dependency chain from engine to tests.
Uses cross-layer-map.json only.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.workspace.formatter import (
    render_section,
    render_table,
)
from runtime.foundation.workspace.models import DependencyExplorerResult
from runtime.foundation.workspace.workspace import WorkspaceLoader


def render_dependencies(result: DependencyExplorerResult) -> str:
    lines: list[str] = []

    if not result.found or not result.chain:
        lines.append(f"\nNo dependency chain found for: {result.file_path}")
        return "\n".join(lines)

    chain = result.chain
    lines.append(render_section(f"Dependency Chain: {result.file_path}"))

    rows: list[list[Any]] = []
    if chain.engine:
        rows.append(["Engine", chain.engine])
    for svc in chain.services:
        rows.append(["Service", svc])
    for router in chain.routers:
        rows.append(["Router", router])
    for ep in chain.endpoints:
        rows.append(["Endpoint", ep])
    for cap in chain.capabilities:
        rows.append(["Capability", cap])
    for mapper in chain.mappers:
        rows.append(["Mapper", mapper])
    for vm in chain.view_models:
        rows.append(["ViewModel", vm])
    for page in chain.pages:
        rows.append(["Page", page])
    for ws in chain.workspaces:
        rows.append(["Workspace", ws])
    for comp in chain.components:
        rows.append(["Renderer", comp])
    for test in chain.tests:
        rows.append(["Test", test])

    if rows:
        lines.append(render_table(["Layer", "Artifact"], rows))
    else:
        lines.append("  (empty chain)")

    return "\n".join(lines)


def cmd_deps(file_path: str | None = None) -> int:
    if not file_path:
        print("Usage: python runtime/verify.py deps <file_path>", __import__("sys").stderr)
        return 1

    loader = WorkspaceLoader()
    result = loader.load_dependency_chain(file_path)
    print(render_dependencies(result))
    return 0
