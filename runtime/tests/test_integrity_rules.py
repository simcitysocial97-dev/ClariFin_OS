"""Rule Check Tests — Program 10.

Tests for individual constitutional rule checks using synthetic
scan results. Deterministic. No network. No git mutation.
"""

from __future__ import annotations

from runtime.foundation.integrity.scanner import (
    ArchitecturalGraph,
    ImportRecord,
    ScannedFile,
)
from runtime.foundation.integrity.models import (
    ArchitectureLayer,
    Violation,
    ViolationCategory,
    ViolationSeverity,
)
from runtime.foundation.integrity.scanner import ArchitecturalGraph
from runtime.foundation.integrity.rules import (
    check_router_not_import_engine,
    check_component_not_api_direct,
    check_mapper_not_react,
    check_workspace_not_fetch,
    check_no_circular_dependencies,
    check_service_not_import_router,
    check_dto_not_import_service,
    check_mapper_not_import_capability,
    check_viewmodel_not_import_component,
    check_workspace_not_import_mapper,
    check_component_not_import_engine,
    check_dto_not_import_router,
    check_capability_not_import_component,
    check_capability_for_every_endpoint,
    check_capability_has_exactly_one_mapper,
    check_mapper_returns_viewmodel,
    check_no_duplicate_endpoint_ownership,
    check_mapper_referenced_by_capability,
    check_viewmodel_referenced_by_mapper,
    check_component_one_workspace,
    check_workspace_has_component,
    check_page_registers_workspace,
    check_endpoint_in_cross_layer_map,
    check_graph_renderer_owned_by_workspace,
    check_endpoint_has_test_coverage,
    check_capability_has_test_coverage,
    check_mapper_in_cross_layer_map,
    check_no_orphaned_pages,
)


def _make_graph(files: list[ScannedFile], cross_layer_map: dict = None) -> ArchitecturalGraph:
    return ArchitecturalGraph(
        files=tuple(files),
        cross_layer_map=cross_layer_map or {},
        graph_nodes=(),
        graph_edges=(),
        files_scanned=len(files),
        repo_root="/tmp/test",
    )


class TestRouterNotImportEngine:
    def test_router_importing_engine_violates(self) -> None:
        f = ScannedFile(
            path="backend/src/routers/loans.py",
            layer=ArchitectureLayer.BACKEND_ROUTER.value,
            file_type="python",
            imports=(
                ImportRecord(
                    module="src.engines.loan_engine.amortization",
                    line_number=10,
                    resolved_path="backend/src/engines/loan_engine/amortization.py",
                    layer=ArchitectureLayer.BACKEND_ENGINE.value,
                ),
            ),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_router_not_import_engine(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-001"
        assert violations[0].severity == ViolationSeverity.HIGH

    def test_router_not_importing_engine_passes(self) -> None:
        f = ScannedFile(
            path="backend/src/routers/loans.py",
            layer=ArchitectureLayer.BACKEND_ROUTER.value,
            file_type="python",
            imports=(
                ImportRecord(
                    module="src.services.loan_service",
                    line_number=10,
                    resolved_path="backend/src/services/loan_service.py",
                    layer=ArchitectureLayer.BACKEND_SERVICE.value,
                ),
            ),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_router_not_import_engine(graph)
        assert len(violations) == 0


class TestComponentNotApiDirect:
    def test_component_with_fetch_violates(self) -> None:
        f = ScannedFile(
            path="frontend/components/dashboard/card.tsx",
            layer=ArchitectureLayer.FRONTEND_COMPONENT.value,
            file_type="typescript",
            imports=(),
            fetch_call_lines=(42,),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_component_not_api_direct(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-002"

    def test_component_importing_api_violates(self) -> None:
        f = ScannedFile(
            path="frontend/components/dashboard/card.tsx",
            layer=ArchitectureLayer.FRONTEND_COMPONENT.value,
            file_type="typescript",
            imports=(
                ImportRecord(
                    module="@/lib/api/client",
                    line_number=5,
                    resolved_path="frontend/lib/api/client.ts",
                    layer=ArchitectureLayer.FRONTEND_API.value,
                ),
            ),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_component_not_api_direct(graph)
        assert len(violations) == 1

    def test_component_clean_passes(self) -> None:
        f = ScannedFile(
            path="frontend/components/dashboard/card.tsx",
            layer=ArchitectureLayer.FRONTEND_COMPONENT.value,
            file_type="typescript",
            imports=(
                ImportRecord(
                    module="@/lib/capabilities/use-dashboard-capability",
                    line_number=5,
                    resolved_path="frontend/lib/capabilities/use-dashboard-capability.ts",
                    layer=ArchitectureLayer.FRONTEND_CAPABILITY.value,
                ),
            ),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_component_not_api_direct(graph)
        assert len(violations) == 0


class TestMapperNotReact:
    def test_mapper_importing_react_violates(self) -> None:
        f = ScannedFile(
            path="frontend/lib/mappers/loans-mapper.ts",
            layer=ArchitectureLayer.FRONTEND_MAPPER.value,
            file_type="typescript",
            imports=(
                ImportRecord(
                    module="react",
                    line_number=3,
                    resolved_path=None,
                    layer=ArchitectureLayer.UNKNOWN.value,
                ),
            ),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_mapper_not_react(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-003"

    def test_mapper_not_importing_react_passes(self) -> None:
        f = ScannedFile(
            path="frontend/lib/mappers/loans-mapper.ts",
            layer=ArchitectureLayer.FRONTEND_MAPPER.value,
            file_type="typescript",
            imports=(
                ImportRecord(
                    module="@/types/loans-view-model",
                    line_number=3,
                    resolved_path="frontend/types/loans-view-model.ts",
                    layer=ArchitectureLayer.FRONTEND_VIEWMODEL.value,
                ),
            ),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_mapper_not_react(graph)
        assert len(violations) == 0


class TestWorkspaceNotFetch:
    def test_workspace_with_fetch_violates(self) -> None:
        f = ScannedFile(
            path="frontend/lib/workspace/workspace-context.ts",
            layer=ArchitectureLayer.FRONTEND_WORKSPACE.value,
            file_type="typescript",
            imports=(),
            fetch_call_lines=(15,),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_workspace_not_fetch(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-004"

    def test_workspace_without_fetch_passes(self) -> None:
        f = ScannedFile(
            path="frontend/lib/workspace/workspace-context.ts",
            layer=ArchitectureLayer.FRONTEND_WORKSPACE.value,
            file_type="typescript",
            imports=(),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_workspace_not_fetch(graph)
        assert len(violations) == 0


class TestNoCircularDependencies:
    def test_no_cycles_passes(self) -> None:
        f1 = ScannedFile(
            path="backend/src/routers/loans.py",
            layer=ArchitectureLayer.BACKEND_ROUTER.value,
            file_type="python",
            imports=(
                ImportRecord(
                    module="src.services.loan_service",
                    line_number=10,
                    resolved_path="backend/src/services/loan_service.py",
                    layer=ArchitectureLayer.BACKEND_SERVICE.value,
                ),
            ),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        f2 = ScannedFile(
            path="backend/src/services/loan_service.py",
            layer=ArchitectureLayer.BACKEND_SERVICE.value,
            file_type="python",
            imports=(),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f1, f2])
        violations = check_no_circular_dependencies(graph)
        assert len(violations) == 0


class TestCapabilityForEveryEndpoint:
    def test_endpoint_without_capability_violates(self) -> None:
        graph = _make_graph(
            [],
            cross_layer_map={
                "backend/src/routers/loans.py": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": [],
                    "mappers": [],
                    "viewModels": [],
                },
            },
        )
        violations = check_capability_for_every_endpoint(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-005"

    def test_endpoint_with_capability_passes(self) -> None:
        graph = _make_graph(
            [],
            cross_layer_map={
                "backend/src/routers/loans.py": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": ["useLoansCapability"],
                    "mappers": ["loansMapper"],
                    "viewModels": ["LoansViewModel"],
                },
            },
        )
        violations = check_capability_for_every_endpoint(graph)
        assert len(violations) == 0


class TestCapabilityHasExactlyOneMapper:
    def test_capability_with_no_mappers_violates(self) -> None:
        graph = _make_graph(
            [],
            cross_layer_map={
                "backend/src/routers/loans.py": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": ["useLoansCapability"],
                    "mappers": [],
                    "viewModels": [],
                },
            },
        )
        violations = check_capability_has_exactly_one_mapper(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-006"

    def test_capability_with_multiple_mappers_violates(self) -> None:
        graph = _make_graph(
            [],
            cross_layer_map={
                "backend/src/routers/loans.py": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": ["useLoansCapability"],
                    "mappers": ["loansMapper", "otherMapper"],
                    "viewModels": [],
                },
            },
        )
        violations = check_capability_has_exactly_one_mapper(graph)
        assert len(violations) == 1

    def test_capability_with_one_mapper_passes(self) -> None:
        graph = _make_graph(
            [],
            cross_layer_map={
                "backend/src/routers/loans.py": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": ["useLoansCapability"],
                    "mappers": ["loansMapper"],
                    "viewModels": ["LoansViewModel"],
                },
            },
        )
        violations = check_capability_has_exactly_one_mapper(graph)
        assert len(violations) == 0


class TestMapperReturnsViewModel:
    def test_mapper_without_viewmodel_violates(self) -> None:
        graph = _make_graph(
            [],
            cross_layer_map={
                "backend/src/routers/loans.py": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": ["useLoansCapability"],
                    "mappers": ["loansMapper"],
                    "viewModels": [],
                },
            },
        )
        violations = check_mapper_returns_viewmodel(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-007"

    def test_mapper_with_viewmodel_passes(self) -> None:
        graph = _make_graph(
            [],
            cross_layer_map={
                "backend/src/routers/loans.py": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": ["useLoansCapability"],
                    "mappers": ["loansMapper"],
                    "viewModels": ["LoansViewModel"],
                },
            },
        )
        violations = check_mapper_returns_viewmodel(graph)
        assert len(violations) == 0


class TestNoDuplicateEndpointOwnership:
    def test_duplicate_endpoint_violates(self) -> None:
        graph = _make_graph(
            [],
            cross_layer_map={
                "chain1": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": ["useLoansCapability"],
                    "mappers": ["loansMapper"],
                    "viewModels": ["LoansViewModel"],
                },
                "chain2": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": ["useCashflowCapability"],
                    "mappers": ["cashflowMapper"],
                    "viewModels": ["CashflowViewModel"],
                },
            },
        )
        violations = check_no_duplicate_endpoint_ownership(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-008"

    def test_unique_endpoints_pass(self) -> None:
        graph = _make_graph(
            [],
            cross_layer_map={
                "chain1": {
                    "endpoints": ["GET /api/loans"],
                    "capabilities": ["useLoansCapability"],
                    "mappers": ["loansMapper"],
                    "viewModels": ["LoansViewModel"],
                },
                "chain2": {
                    "endpoints": ["GET /api/cashflow"],
                    "capabilities": ["useCashflowCapability"],
                    "mappers": ["cashflowMapper"],
                    "viewModels": ["CashflowViewModel"],
                },
            },
        )
        violations = check_no_duplicate_endpoint_ownership(graph)
        assert len(violations) == 0


class TestPageRegistersWorkspace:
    def test_page_without_workspace_registration_violates(self) -> None:
        f = ScannedFile(
            path="frontend/app/loans/page.tsx",
            layer=ArchitectureLayer.FRONTEND_PAGE.value,
            file_type="typescript",
            imports=(),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_page_registers_workspace(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-010"

    def test_page_with_workspace_registration_passes(self) -> None:
        f = ScannedFile(
            path="frontend/app/loans/page.tsx",
            layer=ArchitectureLayer.FRONTEND_PAGE.value,
            file_type="typescript",
            imports=(),
            fetch_call_lines=(),
            has_workspace_registration=True,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_page_registers_workspace(graph)
        assert len(violations) == 0


class TestEngineNotImportedByComponent:
    def test_component_importing_engine_violates(self) -> None:
        f = ScannedFile(
            path="frontend/components/dashboard/card.tsx",
            layer=ArchitectureLayer.FRONTEND_COMPONENT.value,
            file_type="typescript",
            imports=(
                ImportRecord(
                    module="backend/src/engines/loan_engine/amortization",
                    line_number=5,
                    resolved_path=None,
                    layer=ArchitectureLayer.BACKEND_ENGINE.value,
                ),
            ),
            fetch_call_lines=(),
            has_workspace_registration=False,
            class_names=(),
            function_names=(),
        )
        graph = _make_graph([f])
        violations = check_component_not_import_engine(graph)
        assert len(violations) == 1
        assert violations[0].rule_id == "ARCH-016"


class TestAllRuleChecksExist:
    """Verify every rule in the registry has a corresponding check function."""

    def test_all_registry_rules_have_checks(self) -> None:
        from runtime.foundation.integrity.registry import get_constitution
        from runtime.foundation.integrity.rules import _RULE_CHECKS

        registry = get_constitution()
        for rule in registry.all_rules():
            assert rule.id in _RULE_CHECKS, (
                f"Missing check function for {rule.id}: {rule.check}"
            )