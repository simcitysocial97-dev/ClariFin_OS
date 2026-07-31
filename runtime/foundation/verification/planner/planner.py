"""
Verification Planner — Phase 4

Produces deterministic verification plans from:
- Changed files
- Changed capabilities
- Changed endpoints
- Requested scope

No execution logic. Pure planning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

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
            VerificationScope.FULL: list(VerificationScope),
        }

        result = set(scope_hierarchy.get(requested, [requested]))
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
            for endpoint in changed_endpoints:
                # Would query graph service for capability owning endpoint
                pass

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
        for cap_id in capabilities:
            cap = self._registry.get_capability(cap_id)
            if cap:
                requirements.extend(cap.requirements)

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

        return list(workflows), list(scripts)

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
