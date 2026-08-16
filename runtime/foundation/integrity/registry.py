"""Constitutional Rule Registry — Program 10.

Defines all 28 constitutional rules as immutable metadata.  This registry is
the constitutional document of the Financial OS architecture.  Rules are
categorized into three classes:

  Structural — dependency and layer integrity
  Ownership   — single source of truth enforcement
  Evolution   — prevent architectural drift

No execution logic lives here.  The scanner and rules modules consume this
metadata to perform deterministic checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.foundation.integrity.models import (
    ArchitectureLayer,
    ViolationCategory,
    ViolationSeverity,
)


@dataclass(frozen=True, slots=True)
class IntegrityRule:
    """Metadata for a single constitutional rule.

    The ``check`` field holds the name of the function in ``rules.py``
    that implements this rule's check logic.
    """

    id: str
    name: str
    description: str
    severity: ViolationSeverity
    category: ViolationCategory
    examples: tuple[str, ...]
    check: str
    affected_layers: tuple[ArchitectureLayer, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ConstitutionalRegistry:
    """Immutable registry of all constitutional rules.

    Built once at import time and never mutated.  Provides lookup by rule ID
    and iteration in canonical order.
    """

    rules: tuple[IntegrityRule, ...]

    def get(self, rule_id: str) -> IntegrityRule | None:
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def all_rules(self) -> list[IntegrityRule]:
        return list(self.rules)

    def by_category(self, category: ViolationCategory) -> list[IntegrityRule]:
        return [r for r in self.rules if r.category == category]

    @property
    def rule_ids(self) -> list[str]:
        return [r.id for r in self.rules]

    @property
    def total_count(self) -> int:
        return len(self.rules)


# ===========================================================================
# STRUCTURAL RULES — dependency direction, layer boundaries, forbidden
# imports, circular dependency detection.
# ===========================================================================

_STRUCTURAL_RULES: tuple[IntegrityRule, ...] = (
    IntegrityRule(
        id="ARCH-001",
        name="Router may not import Engine",
        description=(
            "Backend routers must not import engine modules directly. "
            "They must go through the Service layer, which is the only "
            "authorized consumer of Engine logic."
        ),
        severity=ViolationSeverity.HIGH,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "backend/src/routers/loans.py importing backend/src/engines/loan_engine/",
            "backend/src/routers/accounts.py importing backend/src/engines/account_engine/",
        ),
        check="check_router_not_import_engine",
        affected_layers=(
            ArchitectureLayer.BACKEND_ROUTER,
            ArchitectureLayer.BACKEND_ENGINE,
        ),
    ),
    IntegrityRule(
        id="ARCH-002",
        name="Component may not call API directly",
        description=(
            "Frontend components must not call fetch() or import the API "
            "client directly.  All data access must flow through a Capability "
            "hook, which handles caching, error recovery, and contract mapping."
        ),
        severity=ViolationSeverity.HIGH,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "frontend/components/... calling fetch('/api/v1/loans')",
            "frontend/components/... importing from '@/lib/api/client'",
        ),
        check="check_component_not_api_direct",
        affected_layers=(
            ArchitectureLayer.FRONTEND_COMPONENT,
            ArchitectureLayer.FRONTEND_API,
        ),
    ),
    IntegrityRule(
        id="ARCH-003",
        name="Mapper must not import React",
        description=(
            "Frontend mappers are pure data-transformation modules.  They must "
            "not depend on the React runtime, which would couple presentation "
            "concerns to data mapping."
        ),
        severity=ViolationSeverity.LOW,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "frontend/lib/mappers/loans-mapper.ts importing 'react'",
            "frontend/lib/mappers/cashflow-mapper.ts importing @tanstack/react-query",
        ),
        check="check_mapper_not_react",
        affected_layers=(ArchitectureLayer.FRONTEND_MAPPER,),
    ),
    IntegrityRule(
        id="ARCH-004",
        name="Workspace must not perform fetch",
        description=(
            "The workspace layer must not call fetch() directly.  Data fetching "
            "is delegated to Capabilities, which own the API contract."
        ),
        severity=ViolationSeverity.HIGH,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "frontend/lib/workspace/... calling fetch('/api/...')",
            "frontend/lib/runtime/... calling fetch('/api/...')",
        ),
        check="check_workspace_not_fetch",
        affected_layers=(
            ArchitectureLayer.FRONTEND_WORKSPACE,
            ArchitectureLayer.FRONTEND_API,
        ),
    ),
    IntegrityRule(
        id="ARCH-009",
        name="No circular layer dependencies",
        description=(
            "The architectural dependency graph must be a DAG.  No set of layers "
            "may form a cycle, as that indicates the architecture has drifted from "
            "its canonical layered form."
        ),
        severity=ViolationSeverity.CRITICAL,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "Service → Engine → Service cycle",
            "Capability → Mapper → Capability cycle",
        ),
        check="check_no_circular_dependencies",
    ),
    IntegrityRule(
        id="ARCH-011",
        name="Service may not import Router",
        description=(
            "Services must not import router modules.  Routers depend on services, "
            "not vice-versa — this is an inverted dependency."
        ),
        severity=ViolationSeverity.HIGH,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "backend/src/services/loan_service.py importing backend/src/routers/loans.py",
        ),
        check="check_service_not_import_router",
        affected_layers=(
            ArchitectureLayer.BACKEND_SERVICE,
            ArchitectureLayer.BACKEND_ROUTER,
        ),
    ),
    IntegrityRule(
        id="ARCH-012",
        name="DTO may not import Service",
        description=(
            "DTO modules must be pure data definitions.  They must not import "
            "service-layer business logic."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "backend/src/core/dtos/loan_dto.py importing backend/src/services/loan_service.py",
        ),
        check="check_dto_not_import_service",
        affected_layers=(
            ArchitectureLayer.BACKEND_DTO,
            ArchitectureLayer.BACKEND_SERVICE,
        ),
    ),
    IntegrityRule(
        id="ARCH-013",
        name="Mapper must not import Capability",
        description=(
            "Frontend mappers are pure data transformations consumed by "
            "capabilities.  Importing a capability would create an upward "
            "dependency cycle (Capability → Mapper → Capability)."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "frontend/lib/mappers/loans-mapper.ts importing use-loans-capability.ts",
        ),
        check="check_mapper_not_import_capability",
        affected_layers=(
            ArchitectureLayer.FRONTEND_MAPPER,
            ArchitectureLayer.FRONTEND_CAPABILITY,
        ),
    ),
    IntegrityRule(
        id="ARCH-014",
        name="ViewModel must not import Component",
        description=(
            "View model types are pure data contracts.  They must not reference "
            "presentational components."
        ),
        severity=ViolationSeverity.LOW,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "frontend/types/loans-view-model.ts importing from @/components/...",
        ),
        check="check_viewmodel_not_import_component",
        affected_layers=(
            ArchitectureLayer.FRONTEND_VIEWMODEL,
            ArchitectureLayer.FRONTEND_COMPONENT,
        ),
    ),
    IntegrityRule(
        id="ARCH-015",
        name="Workspace must not import Mapper directly",
        description=(
            "The workspace layer must obtain data through capabilities, not by "
            "importing mappers directly.  This preserves the canonical data "
            "flow: Workspace → Capability → Mapper."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "frontend/lib/workspace/... importing from @/lib/mappers/...",
        ),
        check="check_workspace_not_import_mapper",
        affected_layers=(
            ArchitectureLayer.FRONTEND_WORKSPACE,
            ArchitectureLayer.FRONTEND_MAPPER,
        ),
    ),
    IntegrityRule(
        id="ARCH-016",
        name="Component may not import Engine",
        description=(
            "Frontend components must not import backend engine modules.  "
            "All computation must flow through the API contract layer."
        ),
        severity=ViolationSeverity.HIGH,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "frontend/components/... importing backend/src/engines/...",
        ),
        check="check_component_not_import_engine",
        affected_layers=(
            ArchitectureLayer.FRONTEND_COMPONENT,
            ArchitectureLayer.BACKEND_ENGINE,
        ),
    ),
    IntegrityRule(
        id="ARCH-017",
        name="DTO may not import Router",
        description=(
            "DTO modules must be pure data definitions.  They must not create "
            "upward dependencies on the router layer."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "backend/src/core/dtos/... importing backend/src/routers/...",
        ),
        check="check_dto_not_import_router",
        affected_layers=(
            ArchitectureLayer.BACKEND_DTO,
            ArchitectureLayer.BACKEND_ROUTER,
        ),
    ),
    IntegrityRule(
        id="ARCH-018",
        name="Capability must not import Component",
        description=(
            "Capabilities are state-management hooks that must not depend on "
            "presentational components.  This preserves the one-directional "
            "data flow: Component → Workspace → Capability → Mapper."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.STRUCTURAL,
        examples=(
            "frontend/lib/capabilities/... importing from @/components/...",
        ),
        check="check_capability_not_import_component",
        affected_layers=(
            ArchitectureLayer.FRONTEND_CAPABILITY,
            ArchitectureLayer.FRONTEND_COMPONENT,
        ),
    ),
)


# ===========================================================================
# OWNERSHIP RULES — single source of truth enforcement.
# ===========================================================================

_OWNERSHIP_RULES: tuple[IntegrityRule, ...] = (
    IntegrityRule(
        id="ARCH-005",
        name="Capability required for every endpoint",
        description=(
            "Every backend API endpoint must be associated with exactly one "
            "frontend capability in the cross-layer map.  This ensures every "
            "data contract has an owner on the frontend."
        ),
        severity=ViolationSeverity.HIGH,
        category=ViolationCategory.OWNERSHIP,
        examples=(
            "Endpoint GET /api/v1/loans without a mapped capability",
            "Capability useLoansCapability with no associated endpoints",
        ),
        check="check_capability_for_every_endpoint",
    ),
    IntegrityRule(
        id="ARCH-006",
        name="Every capability requires exactly one mapper",
        description=(
            "Each capability in the cross-layer map must reference exactly one "
            "mapper.  Zero mappers means data is unconverted; multiple mappers "
            "means split ownership."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.OWNERSHIP,
        examples=(
            "Capability with empty mappers list in cross-layer map",
            "Capability with two mapper entries in cross-layer map",
        ),
        check="check_capability_has_exactly_one_mapper",
    ),
    IntegrityRule(
        id="ARCH-007",
        name="Every mapper returns ViewModel",
        description=(
            "Every mapper must reference at least one ViewModel type, ensuring "
            "that DTO-to-ViewModel transformation is always present."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.OWNERSHIP,
        examples=(
            "loans-mapper.ts with no import from types/*-view-model",
        ),
        check="check_mapper_returns_viewmodel",
    ),
    IntegrityRule(
        id="ARCH-008",
        name="No duplicate endpoint ownership",
        description=(
            "No API endpoint may appear in more than one cross-layer chain.  "
            "Duplicate ownership causes divergent data contracts."
        ),
        severity=ViolationSeverity.HIGH,
        category=ViolationCategory.OWNERSHIP,
        examples=(
            "GET /api/loans appearing in both loan_engine and cashflow_engine chains",
        ),
        check="check_no_duplicate_endpoint_ownership",
    ),
    IntegrityRule(
        id="ARCH-019",
        name="Every mapper is referenced by exactly one capability",
        description=(
            "Each mapper file must be imported by exactly one capability hook. "
            "Orphaned mappers are dead code; multiply-referenced mappers break "
            "single-source-of-truth."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.OWNERSHIP,
        examples=(
            "accounts-mapper.ts imported by both useAccountsCapability and useLoansCapability",
            "forecast-mapper.ts not imported by any capability",
        ),
        check="check_mapper_referenced_by_capability",
    ),
    IntegrityRule(
        id="ARCH-020",
        name="Every ViewModel is referenced by exactly one mapper",
        description=(
            "Each view-model type file must be imported by exactly one mapper. "
            "This ensures the DTO-to-presentation transformation is centralized."
        ),
        severity=ViolationSeverity.LOW,
        category=ViolationCategory.OWNERSHIP,
        examples=(
            "loans-view-model.ts imported by two different mappers",
            "accounts-view-model.ts not imported by any mapper",
        ),
        check="check_viewmodel_referenced_by_mapper",
    ),
    IntegrityRule(
        id="ARCH-021",
        name="Every component belongs to exactly one workspace",
        description=(
            "Each component must belong to exactly one workspace.  Components "
            "in the components/ directory must be matched to a workspace via the "
            "cross-layer map."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.OWNERSHIP,
        examples=(
            "AmortizationTable component not listed under any workspace",
        ),
        check="check_component_one_workspace",
    ),
    IntegrityRule(
        id="ARCH-022",
        name="Every workspace has at least one component",
        description=(
            "Each workspace in the cross-layer map must own at least one "
            "component.  A workspace with no components is an empty shell."
        ),
        severity=ViolationSeverity.LOW,
        category=ViolationCategory.OWNERSHIP,
        examples=(
            "Workspace with empty components list in cross-layer map",
        ),
        check="check_workspace_has_component",
    ),
)


# ===========================================================================
# EVOLUTION RULES — prevent architectural drift.
# ===========================================================================

_EVOLUTION_RULES: tuple[IntegrityRule, ...] = (
    IntegrityRule(
        id="ARCH-010",
        name="Page must not bypass Workspace registration",
        description=(
            "Every page.tsx under frontend/app/ must call "
            "useWorkspaceRegistration to declare its workspace identity. "
            "Pages that skip registration are invisible to the runtime."
        ),
        severity=ViolationSeverity.HIGH,
        category=ViolationCategory.EVOLUTION,
        examples=(
            "frontend/app/loans/page.tsx without useWorkspaceRegistration call",
        ),
        check="check_page_registers_workspace",
        affected_layers=(ArchitectureLayer.FRONTEND_PAGE,),
    ),
    IntegrityRule(
        id="ARCH-023",
        name="Every endpoint must appear in the cross-layer map",
        description=(
            "Every backend API endpoint discovered via AST scanning must be "
            "represented in the cross-layer map.  Endpoints missing from the "
            "map have no frontend ownership."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.EVOLUTION,
        examples=(
            "Endpoint GET /api/v1/accounts not found in any cross-layer chain",
        ),
        check="check_endpoint_in_cross_layer_map",
    ),
    IntegrityRule(
        id="ARCH-024",
        name="Every graph renderer is owned by a workspace",
        description=(
            "Every graph renderer listed in the cross-layer map must be "
            "associated with a workspace.  Orphaned renderers have no owner."
        ),
        severity=ViolationSeverity.LOW,
        category=ViolationCategory.EVOLUTION,
        examples=(
            "LoanGraphRenderer listed without a workspace in the chain",
        ),
        check="check_graph_renderer_owned_by_workspace",
    ),
    IntegrityRule(
        id="ARCH-025",
        name="Every public API endpoint has verification coverage",
        description=(
            "Every endpoint in the cross-layer map must reference at least one "
            "test file.  Endpoints without tests are unverifiable."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.EVOLUTION,
        examples=(
            "Endpoint with empty tests list in cross-layer map",
        ),
        check="check_endpoint_has_test_coverage",
    ),
    IntegrityRule(
        id="ARCH-026",
        name="Every capability has test coverage",
        description=(
            "Every capability in the cross-layer map must reference at least "
            "one test file.  Capabilities without tests are untested."
        ),
        severity=ViolationSeverity.MEDIUM,
        category=ViolationCategory.EVOLUTION,
        examples=(
            "Capability with empty tests list in cross-layer map",
        ),
        check="check_capability_has_test_coverage",
    ),
    IntegrityRule(
        id="ARCH-027",
        name="Every mapper file is referenced in the cross-layer map",
        description=(
            "Every mapper file discovered on disk must appear in at least one "
            "cross-layer chain.  Unmapped mappers have no architectural ownership."
        ),
        severity=ViolationSeverity.LOW,
        category=ViolationCategory.EVOLUTION,
        examples=(
            "frontend/lib/mappers/orphan-mapper.ts not in any cross-layer chain",
        ),
        check="check_mapper_in_cross_layer_map",
    ),
    IntegrityRule(
        id="ARCH-028",
        name="No orphaned workspace pages",
        description=(
            "Every route directory under frontend/app/ must contain a page.tsx "
            "file.  Directories without pages represent incomplete workspaces."
        ),
        severity=ViolationSeverity.LOW,
        category=ViolationCategory.EVOLUTION,
        examples=(
            "frontend/app/incomplete/ directory without a page.tsx",
        ),
        check="check_no_orphaned_pages",
    ),
)


# ===========================================================================
# Registry singleton
# ===========================================================================

_ALL_RULES: tuple[IntegrityRule, ...] = (
    *_STRUCTURAL_RULES,
    *_OWNERSHIP_RULES,
    *_EVOLUTION_RULES,
)


def get_constitution() -> ConstitutionalRegistry:
    """Return the immutable constitutional registry."""
    return ConstitutionalRegistry(rules=_ALL_RULES)


# Module-level singleton
CONSTELLATION = get_constitution()
