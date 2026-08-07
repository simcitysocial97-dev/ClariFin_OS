"""
Verification Planner — Phase 4 + Program 7A Cross-Layer Intelligence

Produces deterministic verification plans from:
- Changed files
- Changed capabilities
- Changed endpoints
- Requested scope

No execution logic. Pure planning.

Program 7A adds CrossLayerImpactPlanner for cross-layer dependency intelligence.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.models import (
    VerificationCategory,
    VerificationPlan,
    VerificationScope,
    VerificationStep,
    VerificationTarget,
    VerificationDependency,
    VerificationStatus,
)
from runtime.foundation.verification.registry import (
    VerificationRegistry,
    VerificationRequirement,
    get_registry,
)
from runtime.foundation.repository.graph.graph_service import RepositoryGraphService


@dataclass(frozen=True, slots=True)
class ScopeImpact:
    """Impact of a file change on verification scopes."""

    file_path: str
    scopes: list[VerificationScope]
    capabilities: list[str]
    modules: list[str]
    reasons: dict[VerificationScope, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PlanningContext:
    """Context for planning."""

    changed_files: list[str] = field(default_factory=list)
    changed_capabilities: list[str] = field(default_factory=list)
    changed_endpoints: list[str] = field(default_factory=list)
    requested_scope: VerificationScope | None = None
    force_scope: VerificationScope | None = None
    include_dependencies: bool = True
    include_dependents: bool = False
    max_depth: int = 3


class VerificationPlanner:
    """
    Verification Planner - deterministic planning engine.

    Given:
    - Changed files
    - Changed capabilities
    - Changed endpoints
    - Requested scope

    Produces:
    - VerificationPlan with targets, steps, dependencies, workflows, scripts
    - No execution logic
    """

    def __init__(
        self,
        graph_service: RepositoryGraphService | None = None,
        registry: VerificationRegistry | None = None,
    ):
        self._graph_service = graph_service
        self._registry = registry or get_registry()

    def plan(self, context: PlanningContext) -> VerificationPlan:
        """Generate a verification plan from context."""
        self._registry.load()

        # Resolve scope
        scope = (
            context.force_scope or context.requested_scope or VerificationScope.QUICK
        )

        # Determine impacted scopes from changed files
        impacted_scopes = self._resolve_scopes_from_files(context.changed_files)

        # Merge with requested scope
        all_scopes = self._merge_scopes(scope, impacted_scopes)

        # Determine impacted capabilities
        impacted_capabilities = self._resolve_capabilities(
            context.changed_files,
            context.changed_capabilities,
            context.changed_endpoints,
            all_scopes,
        )

        # Determine impacted modules
        impacted_modules = self._resolve_modules(
            context.changed_files, impacted_capabilities
        )

        # Get requirements for impacted capabilities/scopes
        requirements = self._collect_requirements(impacted_capabilities, all_scopes)

        # Build verification targets
        targets = self._build_targets(
            impacted_capabilities,
            impacted_modules,
            requirements,
            context.changed_files,
        )

        # Build dependency graph
        targets_with_deps = self._resolve_dependencies(targets)

        # Determine required workflows and scripts
        required_workflows, required_scripts = self._resolve_workflows_and_scripts(
            targets_with_deps, all_scopes
        )

        # Build execution steps (ordered)
        steps = self._build_steps(
            targets_with_deps, required_workflows, required_scripts
        )

        # Estimate duration
        estimated_duration = sum(s.estimated_duration_seconds for s in steps)

        # Create plan
        plan = VerificationPlan(
            id=f"plan-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            name=f"Verification Plan - {scope.value}",
            scope=scope,
            targets=targets_with_deps,
            steps=steps,
            required_workflows=required_workflows,
            required_scripts=required_scripts,
            estimated_duration_seconds=estimated_duration,
            metadata={
                "changed_files": context.changed_files,
                "changed_capabilities": context.changed_capabilities,
                "changed_endpoints": context.changed_endpoints,
                "impacted_scopes": [s.value for s in all_scopes],
                "impacted_capabilities": impacted_capabilities,
                "impacted_modules": impacted_modules,
                "include_dependencies": context.include_dependencies,
                "include_dependents": context.include_dependents,
                "max_depth": context.max_depth,
                "generated_at": datetime.utcnow().isoformat(),
            },
        )

        return plan

    def _resolve_scopes_from_files(
        self, changed_files: list[str]
    ) -> list[VerificationScope]:
        """Determine which scopes are impacted by changed files."""
        scopes = set()

        for file_path in changed_files:
            # Normalize path
            norm_path = file_path.replace("\\", "/")

            # Backend paths
            if norm_path.startswith("backend/src/"):
                scopes.add(VerificationScope.BACKEND)
                scopes.add(VerificationScope.CONTRACTS)

                # Check for loan engine
                if "loan_engine" in norm_path or "reconciliation" in norm_path:
                    scopes.add(VerificationScope.PROPERTY)

                # Check for migrations
                if "migrations" in norm_path or "alembic" in norm_path:
                    scopes.add(VerificationScope.MIGRATION)

                # Check for invariants (ledger, accounting)
                if "ledger" in norm_path or "accounting" in norm_path:
                    scopes.add(VerificationScope.CONTRACTS)

                # Integration tests for API routes
                if "api" in norm_path or "routes" in norm_path:
                    scopes.add(VerificationScope.INTEGRATION)

            # Frontend paths
            elif norm_path.startswith("frontend/src/"):
                scopes.add(VerificationScope.FRONTEND)
                scopes.add(VerificationScope.CONTRACTS)

            # End-to-end tests
            elif norm_path.startswith("e2e/") or norm_path.startswith("frontend/e2e/"):
                scopes.add(VerificationScope.PLAYWRIGHT)
                scopes.add(VerificationScope.FRONTEND)

            # Runtime self-verification
            elif norm_path.startswith("runtime/"):
                scopes.add(VerificationScope.RUNTIME)

            # Contract tests
            elif "contract" in norm_path and norm_path.endswith(".py"):
                scopes.add(VerificationScope.CONTRACTS)

            # Property tests
            elif "property" in norm_path and norm_path.endswith(".py"):
                scopes.add(VerificationScope.PROPERTY)

            # Mutation tests
            elif "mutation" in norm_path and norm_path.endswith(".py"):
                scopes.add(VerificationScope.MUTATION)

            # Integration tests
            elif "integration" in norm_path or "e2e" in norm_path:
                scopes.add(VerificationScope.INTEGRATION)

            # Config changes affect full repo
            elif norm_path.endswith(
                (
                    ".yaml",
                    ".yml",
                    ".toml",
                    ".ini",
                    "pyproject.toml",
                    "package.json",
                    "tsconfig.json",
                )
            ):
                scopes.add(VerificationScope.REPOSITORY)

        return list(scopes)

    def _merge_scopes(
        self,
        requested: VerificationScope,
        impacted: list[VerificationScope],
    ) -> list[VerificationScope]:
        """Merge requested scope with impacted scopes."""
        scope_hierarchy = {
            VerificationScope.QUICK: [VerificationScope.QUICK],
            VerificationScope.BACKEND: [
                VerificationScope.QUICK,
                VerificationScope.BACKEND,
            ],
            VerificationScope.FRONTEND: [
                VerificationScope.QUICK,
                VerificationScope.FRONTEND,
            ],
            VerificationScope.CONTRACTS: [
                VerificationScope.QUICK,
                VerificationScope.CONTRACTS,
            ],
            VerificationScope.PROPERTY: [
                VerificationScope.QUICK,
                VerificationScope.BACKEND,
                VerificationScope.PROPERTY,
            ],
            VerificationScope.MUTATION: [
                VerificationScope.QUICK,
                VerificationScope.BACKEND,
                VerificationScope.MUTATION,
            ],
            VerificationScope.INTEGRATION: [
                VerificationScope.QUICK,
                VerificationScope.BACKEND,
                VerificationScope.INTEGRATION,
            ],
            VerificationScope.MIGRATION: [
                VerificationScope.QUICK,
                VerificationScope.BACKEND,
                VerificationScope.MIGRATION,
            ],
            VerificationScope.REPOSITORY: [
                VerificationScope.QUICK,
                VerificationScope.BACKEND,
                VerificationScope.FRONTEND,
                VerificationScope.CONTRACTS,
                VerificationScope.PROPERTY,
                VerificationScope.MUTATION,
                VerificationScope.INTEGRATION,
                VerificationScope.MIGRATION,
                VerificationScope.REPOSITORY,
            ],
            VerificationScope.RUNTIME: [VerificationScope.RUNTIME],
            VerificationScope.GOLDEN: [VerificationScope.GOLDEN],
            VerificationScope.PLAYWRIGHT: [VerificationScope.PLAYWRIGHT],
            VerificationScope.FULL: list(VerificationScope),
        }

        result = set(scope_hierarchy.get(requested, [requested]))

        if requested != VerificationScope.QUICK:
            result.update(impacted)

        # If repository or full requested, include everything
        if requested in (VerificationScope.REPOSITORY, VerificationScope.FULL):
            result = set(VerificationScope)

        return list(result)

    def _resolve_capabilities(
        self,
        changed_files: list[str],
        changed_capabilities: list[str],
        changed_endpoints: list[str],
        scopes: list[VerificationScope],
    ) -> list[str]:
        """Determine impacted capabilities."""
        capabilities = set(changed_capabilities)

        # From registry
        for cap in self._registry.get_all_capabilities():
            # Check if capability modules are in changed files
            for module in cap.modules:
                for file_path in changed_files:
                    if file_path.startswith(module):
                        capabilities.add(cap.id)
                        break

            # Check if capability is in requested scopes
            if any(scope in cap.scopes for scope in scopes):
                capabilities.add(cap.id)

        # From changed endpoints (via graph service if available)
        if self._graph_service and changed_endpoints:
            # TODO Program 7: implement graph-based capability resolution
            # For now, skip endpoint-based capability resolution.
            # This means verification plans rely on path-based selection only.
            for _endpoint in changed_endpoints:
                ...

        return list(capabilities)

    def _resolve_modules(
        self, changed_files: list[str], capabilities: list[str]
    ) -> list[str]:
        """Determine impacted modules."""
        modules = set()

        for file_path in changed_files:
            # Extract module from path
            parts = file_path.replace("\\", "/").split("/")
            if parts[0] == "backend" and len(parts) >= 3:
                modules.add(f"backend/{parts[1]}/{parts[2]}")
            elif parts[0] == "frontend" and len(parts) >= 3:
                modules.add(f"frontend/{parts[1]}/{parts[2]}")

        # Add capability modules
        for cap_id in capabilities:
            cap = self._registry.get_capability(cap_id)
            if cap:
                modules.update(cap.modules)

        return list(modules)

    def _collect_requirements(
        self,
        capabilities: list[str],
        scopes: list[VerificationScope],
    ) -> list[VerificationRequirement]:
        """Collect all requirements for capabilities and scopes."""
        requirements = []

        # From capabilities
        allowed_scopes = set(scopes)
        for cap_id in capabilities:
            cap = self._registry.get_capability(cap_id)
            if cap:
                for req in cap.requirements:
                    if req.scope in allowed_scopes:
                        requirements.append(req)

        # From scopes
        for scope in scopes:
            requirements.extend(self._registry.get_requirements_by_scope(scope))

        # Deduplicate by ID
        seen = set()
        unique = []
        for req in requirements:
            if req.id not in seen:
                seen.add(req.id)
                unique.append(req)

        return unique

    def _build_targets(
        self,
        capabilities: list[str],
        modules: list[str],
        requirements: list[VerificationRequirement],
        changed_files: list[str],
    ) -> list[VerificationTarget]:
        """Build verification targets from requirements."""
        targets = []
        target_id = 0

        for req in requirements:
            target_id += 1
            target = VerificationTarget(
                id=f"target-{target_id:04d}",
                name=f"{req.category.value}: {req.description}",
                category=req.category,
                scope=req.scope,
                module=req.module,
                capability=req.capability,
                requirements=[req],
                reason=f"Required by {req.category.value} verification for {req.capability or req.module or 'repository'}",
            )
            targets.append(target)

        return targets

    def _resolve_dependencies(
        self, targets: list[VerificationTarget]
    ) -> list[VerificationTarget]:
        """Resolve dependencies between targets."""
        # Build dependency graph
        target_map = {t.id: t for t in targets}
        updated_targets = []

        for target in targets:
            deps = list(target.dependencies)

            # Add dependencies based on category hierarchy
            category_order = [
                VerificationCategory.CONTRACT,
                VerificationCategory.INVARIANT,
                VerificationCategory.PROPERTY,
                VerificationCategory.CAPABILITY,
                VerificationCategory.MUTATION,
                VerificationCategory.INTEGRATION,
                VerificationCategory.MIGRATION,
                VerificationCategory.ARCHITECTURAL,
            ]

            target_idx = (
                category_order.index(target.category)
                if target.category in category_order
                else 999
            )

            for other in targets:
                if other.id == target.id:
                    continue
                other_idx = (
                    category_order.index(other.category)
                    if other.category in category_order
                    else 999
                )

                # Dependencies flow from lower to higher in hierarchy
                if other_idx < target_idx:
                    # Check if same capability or module
                    if (
                        target.capability and target.capability == other.capability
                    ) or (target.module and target.module == other.module):
                        dep = VerificationDependency(
                            target_id=other.id,
                            dependency_type="requires",
                            reason=f"{other.category.value} must pass before {target.category.value}",
                        )
                        deps.append(dep)

            # Also check for explicit dependency requirements
            for req in target.requirements:
                for dep in req.depends_on:
                    if dep.target_id in target_map:
                        deps.append(dep)

            # Deduplicate
            unique_deps = []
            seen_dep_ids = set()
            for dep in deps:
                if dep.target_id not in seen_dep_ids:
                    seen_dep_ids.add(dep.target_id)
                    unique_deps.append(dep)

            updated_targets.append(
                VerificationTarget(
                    id=target.id,
                    name=target.name,
                    category=target.category,
                    scope=target.scope,
                    module=target.module,
                    capability=target.capability,
                    file_path=target.file_path,
                    function_name=target.function_name,
                    class_name=target.class_name,
                    requirements=target.requirements,
                    dependencies=unique_deps,
                    evidence=target.evidence,
                    metadata=target.metadata,
                    reason=target.reason,
                )
            )

        return updated_targets

    def _resolve_workflows_and_scripts(
        self,
        targets: list[VerificationTarget],
        scopes: list[VerificationScope],
    ) -> tuple[list[str], list[str]]:
        """Determine required workflows and scripts."""
        workflows = set()
        scripts = set()

        # From scopes
        for scope in scopes:
            for wf in self._registry.get_workflows_by_scope(scope):
                workflows.add(wf.id)
            for script in self._registry.get_scripts_by_scope(scope):
                scripts.add(script.id)

        # From capabilities
        capabilities = set()
        for target in targets:
            if target.capability:
                capabilities.add(target.capability)

        for cap_id in capabilities:
            cap = self._registry.get_capability(cap_id)
            if cap:
                workflows.update(cap.workflows)
                scripts.update(cap.scripts)

        # From target categories
        categories = {t.category for t in targets}
        for cat in categories:
            for wf in self._registry.get_workflows_by_category(cat):
                workflows.add(wf.id)
            for script in self._registry.get_scripts_by_category(cat):
                scripts.add(script.id)

        return sorted(workflows), sorted(scripts)

    def _build_steps(
        self,
        targets: list[VerificationTarget],
        workflows: list[str],
        scripts: list[str],
    ) -> list[VerificationStep]:
        """Build ordered verification steps."""
        steps = []
        step_id = 0

        # Sort targets by dependency order (topological-ish)
        ordered_targets = self._topological_sort(targets)

        for target in ordered_targets:
            # Find matching workflow
            workflow = None
            for wf_id in workflows:
                wf = self._registry.get_workflow(wf_id)
                if wf and (
                    target.scope in wf.scopes or target.capability in wf.capabilities
                ):
                    workflow = wf
                    break

            # Find matching script
            script = None
            for script_id in scripts:
                scr = self._registry.get_script(script_id)
                if scr and (
                    target.scope == scr.scope or target.capability in scr.capabilities
                ):
                    script = scr
                    break

            # Build command
            command = None
            if workflow and workflow.command:
                command = workflow.command
            elif script and script.path:
                command = f"bash {script.path}"

            # Determine required evidence
            required_evidence = []
            if workflow:
                required_evidence.extend(workflow.required_evidence)
            if script:
                required_evidence.extend(script.required_evidence)
            for req in target.requirements:
                required_evidence.extend(req.evidence_required)

            # Determine dependencies
            dep_step_ids = []
            for dep in target.dependencies:
                dep_step_ids.append(f"step-{dep.target_id.split('-')[-1]}")

            step_id += 1
            step = VerificationStep(
                id=f"step-{step_id:04d}",
                target=target,
                order=step_id,
                command=command,
                workflow=workflow.id if workflow else None,
                script=script.id if script else None,
                estimated_duration_seconds=(
                    workflow.estimated_duration_seconds
                    if workflow
                    else (script.estimated_duration_seconds if script else 0)
                ),
                required_evidence=required_evidence,
                dependencies=dep_step_ids,
                status=target.metadata.get("status", VerificationStatus.PENDING),
            )
            steps.append(step)

        return steps

    def _topological_sort(
        self, targets: list[VerificationTarget]
    ) -> list[VerificationTarget]:
        """Topological sort of targets by dependencies."""
        target_map = {t.id: t for t in targets}
        visited = set()
        temp = set()
        result = []

        def visit(target_id: str):
            if target_id in temp:
                return  # Cycle detected, skip
            if target_id in visited:
                return

            temp.add(target_id)
            target = target_map.get(target_id)
            if target:
                for dep in target.dependencies:
                    if dep.target_id in target_map:
                        visit(dep.target_id)
            temp.remove(target_id)
            visited.add(target_id)
            if target:
                result.append(target)

        for target in targets:
            visit(target.id)

        return result


def plan_verification(
    changed_files: list[str] | None = None,
    changed_capabilities: list[str] | None = None,
    changed_endpoints: list[str] | None = None,
    scope: VerificationScope | None = None,
    graph_service: RepositoryGraphService | None = None,
) -> VerificationPlan:
    """Convenience function to create a verification plan."""
    planner = VerificationPlanner(graph_service=graph_service)
    context = PlanningContext(
        changed_files=changed_files or [],
        changed_capabilities=changed_capabilities or [],
        changed_endpoints=changed_endpoints or [],
        requested_scope=scope,
    )
    return planner.plan(context)


# ============================================================================
# Program 7A: Cross-Layer Impact Planning
# ============================================================================


@dataclass
class ImpactReport:
    """Structured impact report for changed files."""

    changed_files: list[str] = field(default_factory=list)
    affected_engines: list[str] = field(default_factory=list)
    affected_services: list[str] = field(default_factory=list)
    affected_routers: list[str] = field(default_factory=list)
    affected_endpoints: list[str] = field(default_factory=list)
    affected_capabilities: list[str] = field(default_factory=list)
    affected_mappers: list[str] = field(default_factory=list)
    affected_view_models: list[str] = field(default_factory=list)
    affected_pages: list[str] = field(default_factory=list)
    affected_workspaces: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    affected_graph_renderers: list[str] = field(default_factory=list)
    affected_tests: list[str] = field(default_factory=list)
    affected_runtimes: list[str] = field(default_factory=list)
    affected_ui: list[str] = field(default_factory=list)
    dependency_chains: list[dict[str, Any]] = field(default_factory=list)
    verification_plan: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "changed_files": self.changed_files,
            "affected_engines": self.affected_engines,
            "affected_services": self.affected_services,
            "affected_routers": self.affected_routers,
            "affected_endpoints": self.affected_endpoints,
            "affected_capabilities": self.affected_capabilities,
            "affected_mappers": self.affected_mappers,
            "affected_view_models": self.affected_view_models,
            "affected_pages": self.affected_pages,
            "affected_workspaces": self.affected_workspaces,
            "affected_components": self.affected_components,
            "affected_graph_renderers": self.affected_graph_renderers,
            "affected_tests": self.affected_tests,
            "affected_runtimes": self.affected_runtimes,
            "affected_ui": self.affected_ui,
            "dependency_chains": self.dependency_chains,
            "verification_plan": self.verification_plan,
        }


class CrossLayerImpactPlanner:
    """
    Program 7A: Cross-layer dependency intelligence.

    Program 13.3: the blast-radius map is a projection of the canonical
    architecture provider (``runtime.foundation.architecture``). No legacy
    artifact is read at runtime. ``map_path`` remains only as an explicit
    fixture-injection point for isolated tests; it is never a runtime default.
    """

    def __init__(self, map_path: Path | None = None):
        self.map_path = map_path
        self._map: dict[str, dict[str, Any]] = {}
        self._load_map()

    def _load_map(self) -> None:
        """Load chains from the architecture provider (or an injected fixture)."""
        if self.map_path is not None:
            if not self.map_path.exists():
                raise FileNotFoundError(f"Injected chain fixture not found: {self.map_path}")
            with open(self.map_path, encoding="utf-8") as f:
                self._map = json.load(f)
            return

        from runtime.foundation.architecture.chains import get_chain_map

        self._map = get_chain_map()

    def analyze_cross_layer_impact(
        self, changed_files: list[str]
    ) -> ImpactReport:
        """Analyze impact of changed files across all layers."""
        report = ImpactReport(changed_files=list(changed_files))

        for file_path in changed_files:
            norm = file_path.replace("\\", "/")
            chain = self._find_chain(norm)
            if chain:
                self._add_chain_to_report(report, chain, file_path)

        # Build structured verification plan
        report.verification_plan = self._build_minimal_plan(report)

        return report

    def _find_chain(self, file_path: str) -> dict[str, Any] | None:
        """Find the cross-layer chain for a changed file."""
        # Direct engine file match
        if file_path in self._map:
            return self._map[file_path]

        # Provider-resolved ownership (canonical; no filename heuristics).
        if self.map_path is None:
            resolved = self._resolve_via_provider(file_path)
            if resolved is not None:
                return resolved

        # Service file match - find engines that map to this service
        # changed file is a service module
        service_name = self._service_name_from_path(file_path)
        if service_name:
            for chain in self._map.values():
                if service_name in chain.get("services", []):
                    return chain

        # Router file match
        if file_path.startswith("backend/src/routers/"):
            for chain in self._map.values():
                if file_path in chain.get("routers", []):
                    return chain

        # Frontend capability match
        for chain in self._map.values():
            caps = chain.get("capabilities", [])
            for cap in caps:
                # Check if changed file is the capability file
                cap_file = f"frontend/lib/capabilities/{cap.lower()}.ts"
                if file_path == cap_file:
                    return chain

        # Frontend workspace/page match
        for chain in self._map.values():
            pages = chain.get("pages", [])
            for page in pages:
                if file_path.endswith(page) or page in file_path:
                    return chain

        # Component match
        for chain in self._map.values():
            for comp in chain.get("components", []):
                if comp.lower() in file_path.lower():
                    return chain

        return None

    def _resolve_via_provider(self, file_path: str) -> dict[str, Any] | None:
        """Resolve a changed file to its owning engine chain using the provider.

        Ownership evidence only: engine module ownership, router ownership,
        service ownership, capability ownership, workspace/component linkage.
        """
        from runtime.foundation.architecture import get_architecture

        arch = get_architecture()
        norm = file_path.replace("\\", "/")

        engine = arch.engine_for_path(norm)
        if engine is not None:
            return self._map.get(engine.path)

        def chain_for_engines(engine_names: tuple[str, ...] | list[str]):
            for name in engine_names:
                eng = arch.engine(name)
                if eng is not None and eng.path in self._map:
                    return self._map[eng.path]
            return None

        router = arch.routers.get(norm)
        if router is not None:
            found = chain_for_engines(router.engines)
            if found is not None:
                return found

        service = arch.services.get(norm)
        if service is not None:
            found = chain_for_engines(service.engines)
            if found is not None:
                return found

        for cap in arch.capabilities.values():
            if cap.path == norm:
                found = chain_for_engines(cap.engines)
                if found is not None:
                    return found

        for ws in arch.workspaces.values():
            if ws.path and ws.path == norm:
                for cap_name in ws.capabilities:
                    cap = arch.capabilities.get(cap_name)
                    if cap is None:
                        continue
                    found = chain_for_engines(cap.engines)
                    if found is not None:
                        return found

        component = arch.components.get(norm)
        if component is not None:
            for ws_name in component.workspaces:
                ws = arch.workspaces.get(ws_name)
                if ws is None:
                    continue
                for cap_name in ws.capabilities:
                    cap = arch.capabilities.get(cap_name)
                    if cap is None:
                        continue
                    found = chain_for_engines(cap.engines)
                    if found is not None:
                        return found

        return None

    def _service_name_from_path(self, file_path: str) -> str | None:
        """Extract service class name from a service file path."""

        if not file_path.startswith("backend/src/services/"):
            return None
        parts = file_path.split("/")
        filename = parts[-1].replace(".py", "")
        # Convert kebab-case/snake_case to PascalCase
        words = filename.split("_")
        return "".join(w.capitalize() for w in words)

    def _add_chain_to_report(
        self, report: ImpactReport, chain: dict[str, Any], source_file: str
    ) -> None:
        """Add a chain's data to the impact report."""
        engine = chain.get("engine", "")
        if engine and engine not in report.affected_engines:
            report.affected_engines.append(engine)

        for s in chain.get("services", []):
            if s not in report.affected_services:
                report.affected_services.append(s)

        for r in chain.get("routers", []):
            if r not in report.affected_routers:
                report.affected_routers.append(r)

        for e in chain.get("endpoints", []):
            if e not in report.affected_endpoints:
                report.affected_endpoints.append(e)

        for c in chain.get("capabilities", []):
            if c not in report.affected_capabilities:
                report.affected_capabilities.append(c)

        for m in chain.get("mappers", []):
            if m not in report.affected_mappers:
                report.affected_mappers.append(m)

        for v in chain.get("viewModels", []):
            if v not in report.affected_view_models:
                report.affected_view_models.append(v)

        for p in chain.get("pages", []):
            if p not in report.affected_pages:
                report.affected_pages.append(p)
            if p not in report.affected_ui:
                report.affected_ui.append(p)

        for w in chain.get("workspace", []):
            if w not in report.affected_workspaces:
                report.affected_workspaces.append(w)
            if w not in report.affected_ui:
                report.affected_ui.append(w)

        for c in chain.get("components", []):
            if c not in report.affected_components:
                report.affected_components.append(c)
            if c not in report.affected_ui:
                report.affected_ui.append(c)

        for g in chain.get("graphRenderers", []):
            if g not in report.affected_graph_renderers:
                report.affected_graph_renderers.append(g)

        # Add dependency chain
        dep_chain = {
            "source": source_file,
            "engine": engine,
            "services": chain.get("services", []),
            "routers": chain.get("routers", []),
            "endpoints": chain.get("endpoints", []),
            "capabilities": chain.get("capabilities", []),
            "mappers": chain.get("mappers", []),
            "view_models": chain.get("viewModels", []),
            "workspaces": chain.get("workspace", []),
            "components": chain.get("components", []),
            "tests": chain.get("tests", []),
        }
        report.dependency_chains.append(dep_chain)

        # Tests
        for t in chain.get("tests", []):
            if t not in report.affected_tests:
                report.affected_tests.append(t)

    def _build_minimal_plan(self, report: ImpactReport) -> dict[str, Any]:
        """Build a minimal verification plan from the impact report."""
        # Determine which verification types are needed
        run_unit = bool(report.affected_engines or report.affected_services)
        run_contract = bool(report.affected_endpoints or report.affected_routers)
        run_property = any("loan" in e.lower() for e in report.affected_engines)
        run_frontend = bool(
            report.affected_capabilities
            or report.affected_pages
            or report.affected_components
        )
        run_integration = bool(report.affected_routers)

        return {
            "run_unit": run_unit,
            "run_contract": run_contract,
            "run_property": run_property,
            "run_frontend": run_frontend,
            "run_integration": run_integration,
            "unit_paths": report.affected_tests,
            "contract_paths": [
                t for t in report.affected_tests if "contract" in t
            ],
            "capabilities": report.affected_capabilities,
            "engines": report.affected_engines,
            "services": report.affected_services,
            "impact_summary": (
                f"{len(report.affected_engines)} engines, "
                f"{len(report.affected_services)} services, "
                f"{len(report.affected_capabilities)} capabilities, "
                f"{len(report.affected_tests)} tests"
            ),
        }
