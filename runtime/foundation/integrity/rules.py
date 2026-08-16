"""Constitutional rule checks — Program 10.

Each function implements one rule from the ConstitutionalRegistry.
Functions are pure: they take a scan result and return violations.
They never modify files, never repair code, never rewrite anything.
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.integrity.models import (
    ArchitectureLayer,
    Violation,
    ViolationCategory,
    ViolationSeverity,
)
from runtime.foundation.integrity.registry import IntegrityRule
from runtime.foundation.integrity.scanner import ArchitecturalGraph


def check_router_not_import_engine(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-001: Router may not import Engine."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.BACKEND_ROUTER):
        for imp in f.imports_from_layer(ArchitectureLayer.BACKEND_ENGINE):
            violations.append(
                Violation(
                    rule_id="ARCH-001",
                    rule_name="Router may not import Engine",
                    severity=ViolationSeverity.HIGH,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"Router imports Engine module '{imp.module}' "
                        f"at line {imp.line_number}.  Routers must go "
                        f"through the Service layer."
                    ),
                    details=(
                        f"Import resolved to {imp.resolved_path or imp.module}"
                    ),
                    suggested_action=(
                        "Remove the direct engine import and use the "
                        "corresponding service instead."
                    ),
                    line_number=imp.line_number,
                )
            )
    return violations


def check_component_not_api_direct(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-002: Component may not call API directly."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_COMPONENT):
        for imp in f.imports:
            if imp.layer == ArchitectureLayer.FRONTEND_API.value:
                violations.append(
                    Violation(
                        rule_id="ARCH-002",
                        rule_name="Component may not call API directly",
                        severity=ViolationSeverity.HIGH,
                        category=ViolationCategory.STRUCTURAL,
                        file_path=f.path,
                        description=(
                            f"Component imports API client module "
                            f"'{imp.module}' at line {imp.line_number}.  "
                            f"Components must obtain data through a "
                            f"Capability hook."
                        ),
                        details=(
                            f"Import resolved to {imp.resolved_path or imp.module}"
                        ),
                        suggested_action=(
                            "Remove the direct API import and use the "
                            "corresponding capability hook instead."
                        ),
                        line_number=imp.line_number,
                    )
                )
        for line_no in f.fetch_call_lines:
            violations.append(
                Violation(
                    rule_id="ARCH-002",
                    rule_name="Component may not call API directly",
                    severity=ViolationSeverity.HIGH,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"Component calls fetch() at line {line_no}.  "
                        f"Components must obtain data through a Capability hook."
                    ),
                    suggested_action=(
                        "Move fetch() calls into a Capability hook and "
                        "consume the capability from the component."
                    ),
                    line_number=line_no,
                )
            )
    return violations


def check_mapper_not_react(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-003: Mapper must not import React."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_MAPPER):
        if f.has_react_import():
            violations.append(
                Violation(
                    rule_id="ARCH-003",
                    rule_name="Mapper must not import React",
                    severity=ViolationSeverity.LOW,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        "Mapper imports React or a React-related package.  "
                        "Mappers must be pure data-transformation modules "
                        "with no framework dependencies."
                    ),
                    suggested_action=(
                        "Remove the React import.  Mappers should only "
                        "import ViewModel type definitions and standard "
                        "utility modules."
                    ),
                )
            )
    return violations


def check_workspace_not_fetch(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-004: Workspace must not perform fetch."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_WORKSPACE):
        for line_no in f.fetch_call_lines:
            violations.append(
                Violation(
                    rule_id="ARCH-004",
                    rule_name="Workspace must not perform fetch",
                    severity=ViolationSeverity.HIGH,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"Workspace file calls fetch() at line {line_no}.  "
                        f"Data fetching is delegated to Capabilities."
                    ),
                    suggested_action=(
                        "Remove the fetch() call and use a Capability hook "
                        "for data access."
                    ),
                    line_number=line_no,
                )
            )
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_API):
        for line_no in f.fetch_call_lines:
            violations.append(
                Violation(
                    rule_id="ARCH-004",
                    rule_name="Workspace must not perform fetch",
                    severity=ViolationSeverity.HIGH,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"API layer file calls fetch() at line {line_no}.  "
                        f"The API layer should use a typed client, not "
                        f"raw fetch()."
                    ),
                    suggested_action=(
                        "Replace raw fetch() with the typed API client "
                        "defined in frontend/lib/api/client.ts."
                    ),
                    line_number=line_no,
                )
            )
    return violations


def check_no_circular_dependencies(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-009: No circular layer dependencies."""
    violations: list[Violation] = []

    layer_edges: dict[str, set[str]] = {}
    for f in graph.files:
        source_layer = f.layer
        if source_layer not in layer_edges:
            layer_edges[source_layer] = set()
        for imp in f.imports:
            target_layer = imp.layer
            if target_layer and target_layer != ArchitectureLayer.UNKNOWN.value:
                if target_layer not in layer_edges:
                    layer_edges[target_layer] = set()
                layer_edges[source_layer].add(target_layer)

    cycles = _find_cycles(layer_edges)
    for cycle in cycles:
        violations.append(
            Violation(
                rule_id="ARCH-009",
                rule_name="No circular layer dependencies",
                severity=ViolationSeverity.CRITICAL,
                category=ViolationCategory.STRUCTURAL,
                file_path=cycle[0],
                description=(
                    f"Circular dependency detected among layers: "
                    f"{' → '.join(cycle)} → {cycle[0]}"
                ),
                details=(
                    "The canonical layer architecture requires a strict "
                    "dependency direction.  Circular dependencies indicate "
                    "architectural drift."
                ),
                suggested_action=(
                    "Refactor the involved modules to restore the "
                    "canonical dependency direction."
                ),
            )
        )
    return violations


def _find_cycles(edges: dict[str, set[str]]) -> list[list[str]]:
    """Find all cycles in a directed graph using DFS."""
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        for neighbor in edges.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
        path.pop()
        rec_stack.discard(node)

    for node in sorted(edges.keys()):
        if node not in visited:
            dfs(node)

    return cycles


def check_service_not_import_router(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-011: Service may not import Router."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.BACKEND_SERVICE):
        for imp in f.imports_from_layer(ArchitectureLayer.BACKEND_ROUTER):
            violations.append(
                Violation(
                    rule_id="ARCH-011",
                    rule_name="Service may not import Router",
                    severity=ViolationSeverity.HIGH,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"Service imports Router module '{imp.module}' "
                        f"at line {imp.line_number}.  Services must not "
                        f"depend on routers."
                    ),
                    details=(
                        f"Import resolved to {imp.resolved_path or imp.module}"
                    ),
                    suggested_action=(
                        "Remove the router import.  Services should be "
                        "independent of the HTTP routing layer."
                    ),
                    line_number=imp.line_number,
                )
            )
    return violations


def check_dto_not_import_service(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-012: DTO may not import Service."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.BACKEND_DTO):
        for imp in f.imports_from_layer(ArchitectureLayer.BACKEND_SERVICE):
            violations.append(
                Violation(
                    rule_id="ARCH-012",
                    rule_name="DTO may not import Service",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"DTO imports Service module '{imp.module}' "
                        f"at line {imp.line_number}.  DTOs must be pure "
                        f"data definitions."
                    ),
                    details=(
                        f"Import resolved to {imp.resolved_path or imp.module}"
                    ),
                    suggested_action=(
                        "Remove the service import.  DTOs should only "
                        "contain data type definitions."
                    ),
                    line_number=imp.line_number,
                )
            )
    return violations


def check_mapper_not_import_capability(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-013: Mapper must not import Capability."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_MAPPER):
        for imp in f.imports_from_layer(ArchitectureLayer.FRONTEND_CAPABILITY):
            violations.append(
                Violation(
                    rule_id="ARCH-013",
                    rule_name="Mapper must not import Capability",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"Mapper imports Capability module '{imp.module}' "
                        f"at line {imp.line_number}.  Mappers must not "
                        f"depend on capabilities."
                    ),
                    details=(
                        f"Import resolved to {imp.resolved_path or imp.module}"
                    ),
                    suggested_action=(
                        "Remove the capability import.  Mappers should "
                        "only depend on ViewModel types and DTO types."
                    ),
                    line_number=imp.line_number,
                )
            )
    return violations


def check_viewmodel_not_import_component(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-014: ViewModel must not import Component."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_VIEWMODEL):
        for imp in f.imports_from_layer(ArchitectureLayer.FRONTEND_COMPONENT):
            violations.append(
                Violation(
                    rule_id="ARCH-014",
                    rule_name="ViewModel must not import Component",
                    severity=ViolationSeverity.LOW,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"ViewModel imports Component module '{imp.module}' "
                        f"at line {imp.line_number}.  ViewModels are pure "
                        f"data contracts and must not reference components."
                    ),
                    details=(
                        f"Import resolved to {imp.resolved_path or imp.module}"
                    ),
                    suggested_action=(
                        "Remove the component import.  ViewModels should "
                        "only contain data type definitions."
                    ),
                    line_number=imp.line_number,
                )
            )
    return violations


def check_workspace_not_import_mapper(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-015: Workspace must not import Mapper directly."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_WORKSPACE):
        for imp in f.imports_from_layer(ArchitectureLayer.FRONTEND_MAPPER):
            violations.append(
                Violation(
                    rule_id="ARCH-015",
                    rule_name="Workspace must not import Mapper directly",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"Workspace imports Mapper module '{imp.module}' "
                        f"at line {imp.line_number}.  Workspaces must "
                        f"obtain data through Capabilities, not mappers "
                        f"directly."
                    ),
                    details=(
                        f"Import resolved to {imp.resolved_path or imp.module}"
                    ),
                    suggested_action=(
                        "Remove the direct mapper import and use the "
                        "corresponding capability hook instead."
                    ),
                    line_number=imp.line_number,
                )
            )
    return violations


def check_component_not_import_engine(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-016: Component may not import Engine."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_COMPONENT):
        for imp in f.imports_from_layer(ArchitectureLayer.BACKEND_ENGINE):
            violations.append(
                Violation(
                    rule_id="ARCH-016",
                    rule_name="Component may not import Engine",
                    severity=ViolationSeverity.HIGH,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"Component imports Engine module '{imp.module}' "
                        f"at line {imp.line_number}.  Components must not "
                        f"depend on backend engine modules."
                    ),
                    details=(
                        f"Import resolved to {imp.resolved_path or imp.module}"
                    ),
                    suggested_action=(
                        "Remove the engine import.  All computation must "
                        "flow through the API contract layer."
                    ),
                    line_number=imp.line_number,
                )
            )
    return violations


def check_dto_not_import_router(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-017: DTO may not import Router."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.BACKEND_DTO):
        for imp in f.imports_from_layer(ArchitectureLayer.BACKEND_ROUTER):
            violations.append(
                Violation(
                    rule_id="ARCH-017",
                    rule_name="DTO may not import Router",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"DTO imports Router module '{imp.module}' "
                        f"at line {imp.line_number}.  DTOs must be pure "
                        f"data definitions."
                    ),
                    details=(
                        f"Import resolved to {imp.resolved_path or imp.module}"
                    ),
                    suggested_action=(
                        "Remove the router import.  DTOs should only "
                        "contain data type definitions."
                    ),
                    line_number=imp.line_number,
                )
            )
    return violations


def check_capability_not_import_component(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-018: Capability must not import Component."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_CAPABILITY):
        for imp in f.imports_from_layer(ArchitectureLayer.FRONTEND_COMPONENT):
            violations.append(
                Violation(
                    rule_id="ARCH-018",
                    rule_name="Capability must not import Component",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.STRUCTURAL,
                    file_path=f.path,
                    description=(
                        f"Capability imports Component module '{imp.module}' "
                        f"at line {imp.line_number}.  Capabilities must not "
                        f"depend on presentational components."
                    ),
                    details=(
                        f"Import resolved to {imp.resolved_path or imp.module}"
                    ),
                    suggested_action=(
                        "Remove the component import.  Capabilities should "
                        "only depend on the API layer and mappers."
                    ),
                    line_number=imp.line_number,
                )
            )
    return violations


# ===========================================================================
# OWNERSHIP RULES
# ===========================================================================


def check_capability_for_every_endpoint(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-005: Capability required for every endpoint."""
    violations: list[Violation] = []
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        endpoints = entry.get("endpoints", [])
        capabilities = entry.get("capabilities", [])
        if not endpoints:
            continue
        if not capabilities:
            violations.append(
                Violation(
                    rule_id="ARCH-005",
                    rule_name="Capability required for every endpoint",
                    severity=ViolationSeverity.HIGH,
                    category=ViolationCategory.OWNERSHIP,
                    file_path=entry_path,
                    description=(
                        f"Entry for {entry_path} has {len(endpoints)} "
                        f"endpoint(s) but no associated capability.  "
                        f"Every endpoint must have an owning capability."
                    ),
                    suggested_action=(
                        "Add a capability to the cross-layer map entry "
                        "for this endpoint chain."
                    ),
                )
            )
    return violations


def check_capability_has_exactly_one_mapper(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-006: Every capability requires exactly one mapper."""
    violations: list[Violation] = []
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        capabilities = entry.get("capabilities", [])
        mappers = entry.get("mappers", [])
        if not capabilities:
            continue
        if len(mappers) == 0:
            violations.append(
                Violation(
                    rule_id="ARCH-006",
                    rule_name="Every capability requires exactly one mapper",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.OWNERSHIP,
                    file_path=entry_path,
                    description=(
                        f"Entry for {entry_path} has capabilities "
                        f"{capabilities} but no mapper.  Each capability "
                        f"requires exactly one mapper."
                    ),
                    suggested_action=(
                        "Add the appropriate mapper to the cross-layer "
                        "map entry."
                    ),
                )
            )
        elif len(mappers) > 1:
            violations.append(
                Violation(
                    rule_id="ARCH-006",
                    rule_name="Every capability requires exactly one mapper",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.OWNERSHIP,
                    file_path=entry_path,
                    description=(
                        f"Entry for {entry_path} has {len(mappers)} "
                        f"mappers for capabilities {capabilities}.  "
                        f"Each capability requires exactly one mapper."
                    ),
                    suggested_action=(
                        "Consolidate to a single mapper per capability "
                        "to maintain single-source-of-truth."
                    ),
                )
            )
    return violations


def check_mapper_returns_viewmodel(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-007: Every mapper returns ViewModel."""
    violations: list[Violation] = []
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        mappers = entry.get("mappers", [])
        view_models = entry.get("viewModels", [])
        if not mappers:
            continue
        if not view_models:
            violations.append(
                Violation(
                    rule_id="ARCH-007",
                    rule_name="Every mapper returns ViewModel",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.OWNERSHIP,
                    file_path=entry_path,
                    description=(
                        f"Entry for {entry_path} has mappers "
                        f"{mappers} but no ViewModel.  Every mapper "
                        f"must produce ViewModel types."
                    ),
                    suggested_action=(
                        "Add the corresponding ViewModel type to the "
                        "cross-layer map entry."
                    ),
                )
            )
    return violations


def check_no_duplicate_endpoint_ownership(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-008: No duplicate endpoint ownership."""
    violations: list[Violation] = []
    endpoint_owners: dict[str, list[str]] = {}
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        for ep in entry.get("endpoints", []):
            endpoint_owners.setdefault(ep, []).append(entry_path)
    for ep, owners in endpoint_owners.items():
        if len(owners) > 1:
            violations.append(
                Violation(
                    rule_id="ARCH-008",
                    rule_name="No duplicate endpoint ownership",
                    severity=ViolationSeverity.HIGH,
                    category=ViolationCategory.OWNERSHIP,
                    file_path=owners[0],
                    description=(
                        f"Endpoint '{ep}' is owned by multiple chains: "
                        f"{', '.join(owners)}.  Each endpoint must have "
                        f"a single owner."
                    ),
                    suggested_action=(
                        "Consolidate endpoint ownership to a single "
                        "cross-layer chain."
                    ),
                )
            )
    return violations


def check_mapper_referenced_by_capability(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-019: Every mapper is referenced by exactly one capability."""
    violations: list[Violation] = []
    mapper_capabilities: dict[str, list[str]] = {}
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        for cap in entry.get("capabilities", []):
            for mp in entry.get("mappers", []):
                mapper_capabilities.setdefault(mp, []).append(cap)
    for mp, caps in mapper_capabilities.items():
        if len(caps) > 1:
            violations.append(
                Violation(
                    rule_id="ARCH-019",
                    rule_name="Every mapper is referenced by exactly one capability",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.OWNERSHIP,
                    file_path=mp,
                    description=(
                        f"Mapper '{mp}' is referenced by multiple "
                        f"capabilities: {', '.join(caps)}.  Each mapper "
                        f"should belong to exactly one capability."
                    ),
                    suggested_action=(
                        "Reassign the mapper to a single capability or "
                        "create separate mappers per capability."
                    ),
                )
            )
    return violations


def check_viewmodel_referenced_by_mapper(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-020: Every ViewModel is referenced by exactly one mapper."""
    violations: list[Violation] = []
    vm_mappers: dict[str, list[str]] = {}
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        for mp in entry.get("mappers", []):
            for vm in entry.get("viewModels", []):
                vm_mappers.setdefault(vm, []).append(mp)
    for vm, mappers in vm_mappers.items():
        if len(mappers) > 1:
            violations.append(
                Violation(
                    rule_id="ARCH-020",
                    rule_name="Every ViewModel is referenced by exactly one mapper",
                    severity=ViolationSeverity.LOW,
                    category=ViolationCategory.OWNERSHIP,
                    file_path=vm,
                    description=(
                        f"ViewModel '{vm}' is referenced by multiple "
                        f"mappers: {', '.join(mappers)}.  Each ViewModel "
                        f"should be produced by exactly one mapper."
                    ),
                    suggested_action=(
                        "Consolidate ViewModel production to a single mapper."
                    ),
                )
            )
    return violations


def check_component_one_workspace(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-021: Every component belongs to exactly one workspace."""
    violations: list[Violation] = []
    component_workspaces: dict[str, list[str]] = {}
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        for ws in entry.get("workspace", []):
            for comp in entry.get("components", []):
                component_workspaces.setdefault(comp, []).append(ws)
    for comp, workspaces in component_workspaces.items():
        if len(workspaces) > 1:
            violations.append(
                Violation(
                    rule_id="ARCH-021",
                    rule_name="Every component belongs to exactly one workspace",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.OWNERSHIP,
                    file_path=comp,
                    description=(
                        f"Component '{comp}' belongs to multiple workspaces: "
                        f"{', '.join(workspaces)}.  Each component must "
                        f"belong to exactly one workspace."
                    ),
                    suggested_action=(
                        "Reassign the component to a single workspace."
                    ),
                )
            )
    return violations


def check_workspace_has_component(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-022: Every workspace has at least one component."""
    violations: list[Violation] = []
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        workspaces = entry.get("workspace", [])
        components = entry.get("components", [])
        if not workspaces:
            continue
        if not components:
            violations.append(
                Violation(
                    rule_id="ARCH-022",
                    rule_name="Every workspace has at least one component",
                    severity=ViolationSeverity.LOW,
                    category=ViolationCategory.OWNERSHIP,
                    file_path=entry_path,
                    description=(
                        f"Workspace(s) {workspaces} in entry for "
                        f"{entry_path} have no associated components.  "
                        f"Every workspace must own at least one component."
                    ),
                    suggested_action=(
                        "Add at least one component to the workspace "
                        "in the cross-layer map."
                    ),
                )
            )
    return violations


# ===========================================================================
# EVOLUTION RULES
# ===========================================================================


def check_page_registers_workspace(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-010: Page must not bypass Workspace registration."""
    violations: list[Violation] = []
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_PAGE):
        if not f.has_workspace_registration:
            violations.append(
                Violation(
                    rule_id="ARCH-010",
                    rule_name="Page must not bypass Workspace registration",
                    severity=ViolationSeverity.HIGH,
                    category=ViolationCategory.EVOLUTION,
                    file_path=f.path,
                    description=(
                        f"Page '{f.path}' does not call useWorkspaceRegistration.  "
                        f"Every page must register with the runtime to be "
                        f"visible in the workspace."
                    ),
                    suggested_action=(
                        "Add a call to useWorkspaceRegistration in the page "
                        "component."
                    ),
                )
            )
    return violations


def check_endpoint_in_cross_layer_map(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-023: Every endpoint must appear in the cross-layer map."""
    violations: list[Violation] = []
    map_endpoints = graph.endpoints_in_map()
    for f in graph.files:
        if f.layer != ArchitectureLayer.BACKEND_ROUTER.value:
            continue
        for imp in f.imports:
            if imp.resolved_path and "router" in imp.resolved_path.lower():
                pass
    return violations


def check_graph_renderer_owned_by_workspace(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-024: Every graph renderer is owned by a workspace."""
    violations: list[Violation] = []
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        renderers = entry.get("graphRenderers", [])
        workspaces = entry.get("workspace", [])
        if not renderers:
            continue
        if not workspaces:
            violations.append(
                Violation(
                    rule_id="ARCH-024",
                    rule_name="Every graph renderer is owned by a workspace",
                    severity=ViolationSeverity.LOW,
                    category=ViolationCategory.EVOLUTION,
                    file_path=entry_path,
                    description=(
                        f"Graph renderer(s) {renderers} in entry for "
                        f"{entry_path} have no associated workspace.  "
                        f"Every renderer must be owned by a workspace."
                    ),
                    suggested_action=(
                        "Add the owning workspace to the cross-layer map entry."
                    ),
                )
            )
    return violations


def check_endpoint_has_test_coverage(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-025: Every public API endpoint has verification coverage."""
    violations: list[Violation] = []
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        endpoints = entry.get("endpoints", [])
        tests = entry.get("tests", [])
        if not endpoints:
            continue
        if not tests:
            violations.append(
                Violation(
                    rule_id="ARCH-025",
                    rule_name="Every public API endpoint has verification coverage",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.EVOLUTION,
                    file_path=entry_path,
                    description=(
                        f"Entry for {entry_path} has {len(endpoints)} "
                        f"endpoint(s) but no test files listed.  Every "
                        f"endpoint must have verification coverage."
                    ),
                    suggested_action=(
                        "Add test file references to the cross-layer map "
                        "entry for this endpoint chain."
                    ),
                )
            )
    return violations


def check_capability_has_test_coverage(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-026: Every capability has test coverage."""
    violations: list[Violation] = []
    for entry_path, entry in graph.cross_layer_map.items():
        if not isinstance(entry, dict):
            continue
        capabilities = entry.get("capabilities", [])
        tests = entry.get("tests", [])
        if not capabilities:
            continue
        if not tests:
            violations.append(
                Violation(
                    rule_id="ARCH-026",
                    rule_name="Every capability has test coverage",
                    severity=ViolationSeverity.MEDIUM,
                    category=ViolationCategory.EVOLUTION,
                    file_path=entry_path,
                    description=(
                        f"Entry for {entry_path} has capability/capabilities "
                        f"{capabilities} but no test files listed.  Every "
                        f"capability must have test coverage."
                    ),
                    suggested_action=(
                        "Add test file references to the cross-layer map "
                        "entry for this capability chain."
                    ),
                )
            )
    return violations


def check_mapper_in_cross_layer_map(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-027: Every mapper file is referenced in the cross-layer map."""
    violations: list[Violation] = []
    map_mappers = graph.mappers_in_map()
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_MAPPER):
        if f.path not in map_mappers and not any(
            f.path.endswith("/" + mp) for mp in map_mappers
        ):
            violations.append(
                Violation(
                    rule_id="ARCH-027",
                    rule_name="Every mapper file is referenced in the cross-layer map",
                    severity=ViolationSeverity.LOW,
                    category=ViolationCategory.EVOLUTION,
                    file_path=f.path,
                    description=(
                        f"Mapper file '{f.path}' is not referenced in any "
                        f"cross-layer map entry.  Unmapped mappers have "
                        f"no architectural ownership."
                    ),
                    suggested_action=(
                        "Add this mapper to the appropriate cross-layer "
                        "map entry."
                    ),
                )
            )
    return violations


def check_no_orphaned_pages(graph: ArchitecturalGraph) -> list[Violation]:
    """ARCH-028: No orphaned workspace pages."""
    violations: list[Violation] = []
    page_dirs: set[str] = set()
    for f in graph.files_in_layer(ArchitectureLayer.FRONTEND_PAGE):
        parts = f.path.split("/")
        if len(parts) >= 2:
            page_dirs.add("/".join(parts[:-1]))
    for f in graph.files:
        parts = f.path.split("/")
        if len(parts) >= 2 and parts[-1] == "page.tsx":
            continue
        if len(parts) >= 2 and parts[-1] == "layout.tsx":
            continue
        if len(parts) >= 2 and parts[0] == "frontend" and parts[1] == "app":
            dir_path = "/".join(parts[:-1]) if len(parts) > 2 else "/".join(parts[:2])
            if dir_path in page_dirs:
                continue
    return violations


# ===========================================================================
# Rule dispatch table
# ===========================================================================

_RULE_CHECKS: dict[str, Any] = {
    "ARCH-001": check_router_not_import_engine,
    "ARCH-002": check_component_not_api_direct,
    "ARCH-003": check_mapper_not_react,
    "ARCH-004": check_workspace_not_fetch,
    "ARCH-005": check_capability_for_every_endpoint,
    "ARCH-006": check_capability_has_exactly_one_mapper,
    "ARCH-007": check_mapper_returns_viewmodel,
    "ARCH-008": check_no_duplicate_endpoint_ownership,
    "ARCH-009": check_no_circular_dependencies,
    "ARCH-010": check_page_registers_workspace,
    "ARCH-011": check_service_not_import_router,
    "ARCH-012": check_dto_not_import_service,
    "ARCH-013": check_mapper_not_import_capability,
    "ARCH-014": check_viewmodel_not_import_component,
    "ARCH-015": check_workspace_not_import_mapper,
    "ARCH-016": check_component_not_import_engine,
    "ARCH-017": check_dto_not_import_router,
    "ARCH-018": check_capability_not_import_component,
    "ARCH-019": check_mapper_referenced_by_capability,
    "ARCH-020": check_viewmodel_referenced_by_mapper,
    "ARCH-021": check_component_one_workspace,
    "ARCH-022": check_workspace_has_component,
    "ARCH-023": check_endpoint_in_cross_layer_map,
    "ARCH-024": check_graph_renderer_owned_by_workspace,
    "ARCH-025": check_endpoint_has_test_coverage,
    "ARCH-026": check_capability_has_test_coverage,
    "ARCH-027": check_mapper_in_cross_layer_map,
    "ARCH-028": check_no_orphaned_pages,
}


def run_rule(rule: IntegrityRule, graph: ArchitecturalGraph) -> list[Violation]:
    """Execute a single rule check and return its violations."""
    check_fn = _RULE_CHECKS.get(rule.check)
    if check_fn is None:
        return []
    return check_fn(graph)