"""
Verification Runtime — Phase 1

Main runtime orchestrator that consumes RepositoryGraphService and provides
verification planning capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.foundation.verification.models import (
    VerificationPlan,
    VerificationScope,
)
from runtime.foundation.verification.planner import (
    VerificationPlanner,
    PlanningContext,
)
from runtime.foundation.verification.registry import (
    VerificationRegistry,
    get_registry,
    reset_registry,
)
from runtime.foundation.verification.models import (
    ScopeResolver,
    get_scope_resolver,
    reset_scope_resolver,
)
from runtime.foundation.verification.validation import (
    ValidationFinding,
    validate_all,
)


@dataclass(frozen=True, slots=True)
class VerificationRuntimeConfig:
    """Configuration for the verification runtime."""

    config_path: Path | None = None
    graph_service: Any | None = None  # RepositoryGraphService
    auto_load: bool = True


class VerificationRuntime:
    """
    Verification Runtime - Main entry point for verification planning.

    Responsibilities:
    - Load RepositoryGraphService
    - Load verification.yaml
    - Load verification registry
    - Resolve verification targets
    - Resolve dependencies
    - Produce verification plans

    Does NOT execute tests. Execution delegated to existing scripts/workflows.
    """

    def __init__(self, config: VerificationRuntimeConfig | None = None):
        self._config = config or VerificationRuntimeConfig()
        self._registry: VerificationRegistry | None = None
        self._scope_resolver: ScopeResolver | None = None
        self._planner: VerificationPlanner | None = None
        self._graph_service = self._config.graph_service
        self._loaded = False

    def load(self) -> None:
        """Load all runtime components."""
        if self._loaded:
            return

        # Load registry
        self._registry = get_registry(self._config.config_path)
        self._registry.load()

        # Initialize scope resolver
        self._scope_resolver = get_scope_resolver()

        # Initialize planner
        self._planner = VerificationPlanner(
            graph_service=self._graph_service,
            registry=self._registry,
        )

        self._loaded = True

    @property
    def registry(self) -> VerificationRegistry:
        """Get the verification registry."""
        if not self._loaded:
            self.load()
        return self._registry

    @property
    def scope_resolver(self) -> ScopeResolver:
        """Get the scope resolver."""
        if not self._loaded:
            self.load()
        return self._scope_resolver

    @property
    def planner(self) -> VerificationPlanner:
        """Get the verification planner."""
        if not self._loaded:
            self.load()
        return self._planner

    @property
    def graph_service(self):
        """Get the repository graph service."""
        return self._graph_service

    def plan(
        self,
        changed_files: list[str] | None = None,
        changed_capabilities: list[str] | None = None,
        changed_endpoints: list[str] | None = None,
        scope: VerificationScope | None = None,
        force_scope: VerificationScope | None = None,
        include_dependencies: bool = True,
        include_dependents: bool = False,
        max_depth: int = 3,
    ) -> VerificationPlan:
        """
        Generate a verification plan.

        Args:
            changed_files: List of changed file paths
            changed_capabilities: List of changed capability IDs
            changed_endpoints: List of changed endpoint paths
            scope: Requested verification scope
            force_scope: Force a specific scope (overrides request)
            include_dependencies: Include upstream dependencies
            include_dependents: Include downstream dependents
            max_depth: Maximum dependency depth

        Returns:
            VerificationPlan with targets, steps, workflows, scripts
        """
        context = PlanningContext(
            changed_files=changed_files or [],
            changed_capabilities=changed_capabilities or [],
            changed_endpoints=changed_endpoints or [],
            requested_scope=scope,
            force_scope=force_scope,
            include_dependencies=include_dependencies,
            include_dependents=include_dependents,
            max_depth=max_depth,
        )

        return self.planner.plan(context)

    def plan_from_files(
        self, file_paths: list[str], scope: VerificationScope | None = None
    ) -> VerificationPlan:
        """Generate a plan from a list of changed files."""
        # Resolve scopes and capabilities from files
        affected_scopes = self.scope_resolver.get_affected_scopes(file_paths)
        affected_capabilities = self.scope_resolver.get_affected_capabilities(
            file_paths
        )
        # Note: get_affected_modules is called but result not used; kept for potential future use
        _ = self.scope_resolver.get_affected_modules(file_paths)

        # Determine scope
        if scope is None:
            if VerificationScope.REPOSITORY in affected_scopes:
                scope = VerificationScope.REPOSITORY
            elif VerificationScope.FULL in affected_scopes:
                scope = VerificationScope.FULL
            else:
                # Use the highest scope affected
                scope_hierarchy = [
                    VerificationScope.QUICK,
                    VerificationScope.BACKEND,
                    VerificationScope.FRONTEND,
                    VerificationScope.CONTRACTS,
                    VerificationScope.PROPERTY,
                    VerificationScope.MUTATION,
                    VerificationScope.INTEGRATION,
                    VerificationScope.MIGRATION,
                    VerificationScope.REPOSITORY,
                    VerificationScope.FULL,
                ]
                max_idx = max(
                    scope_hierarchy.index(s) if s in scope_hierarchy else 0
                    for s in affected_scopes
                )
                scope = scope_hierarchy[max_idx]

        return self.plan(
            changed_files=file_paths,
            changed_capabilities=affected_capabilities,
            scope=scope,
        )

    def plan_for_capability(
        self, capability_id: str, scope: VerificationScope | None = None
    ) -> VerificationPlan:
        """Generate a plan for a specific capability."""
        cap = self.registry.get_capability(capability_id)
        if not cap:
            raise ValueError(f"Unknown capability: {capability_id}")

        # Determine scope from capability if not provided
        if scope is None:
            scope = max(cap.scopes, key=lambda s: list(VerificationScope).index(s))

        return self.plan(
            changed_capabilities=[capability_id],
            scope=scope,
        )

    def plan_for_scope(self, scope: VerificationScope) -> VerificationPlan:
        """Generate a plan for a specific scope."""
        return self.plan(scope=scope)

    def plan_quick(self) -> VerificationPlan:
        """Generate a quick verification plan."""
        return self.plan(scope=VerificationScope.QUICK)

    def plan_backend(self) -> VerificationPlan:
        """Generate a backend verification plan."""
        return self.plan(scope=VerificationScope.BACKEND)

    def plan_frontend(self) -> VerificationPlan:
        """Generate a frontend verification plan."""
        return self.plan(scope=VerificationScope.FRONTEND)

    def plan_contracts(self) -> VerificationPlan:
        """Generate a contracts verification plan."""
        return self.plan(scope=VerificationScope.CONTRACTS)

    def plan_property(self) -> VerificationPlan:
        """Generate a property testing plan."""
        return self.plan(scope=VerificationScope.PROPERTY)

    def plan_mutation(self) -> VerificationPlan:
        """Generate a mutation testing plan."""
        return self.plan(scope=VerificationScope.MUTATION)

    def plan_integration(self) -> VerificationPlan:
        """Generate an integration testing plan."""
        return self.plan(scope=VerificationScope.INTEGRATION)

    def plan_migration(self) -> VerificationPlan:
        """Generate a migration verification plan."""
        return self.plan(scope=VerificationScope.MIGRATION)

    def plan_repository(self) -> VerificationPlan:
        """Generate a full repository verification plan."""
        return self.plan(scope=VerificationScope.REPOSITORY)

    def plan_full(self) -> VerificationPlan:
        """Generate a complete verification plan."""
        return self.plan(scope=VerificationScope.FULL)

    def resolve_file_scopes(self, file_path: str):
        """Resolve scopes for a file path."""
        return self.scope_resolver.resolve_file(file_path)

    def explain_scope(self, scope: VerificationScope, file_paths: list[str]) -> str:
        """Explain why a scope is affected by files."""
        return self.scope_resolver.explain_scope(scope, file_paths)

    def validate(self) -> list[ValidationFinding]:
        """Validate configuration and registry."""
        return validate_all(self._config.config_path)

    def get_registry_summary(self) -> dict[str, Any]:
        """Get a summary of the registry."""
        self.load()
        return {
            "workflows": len(self._registry._workflows),
            "scripts": len(self._registry._scripts),
            "capabilities": len(self._registry._capabilities),
            "categories": len(self._registry._categories),
            "scopes": len(self._registry._scopes),
            "modules": len(self._registry._modules),
        }


# Global runtime instance
_runtime: VerificationRuntime | None = None


def get_runtime(config: VerificationRuntimeConfig | None = None) -> VerificationRuntime:
    """Get the global verification runtime."""
    global _runtime
    if _runtime is None:
        _runtime = VerificationRuntime(config)
    return _runtime


def reset_runtime() -> None:
    """Reset the global runtime (for testing)."""
    global _runtime
    _runtime = None
    reset_registry()
    reset_scope_resolver()
