"""Immutable data models for the Architectural Integrity Engine (Program 10).

No execution logic. Data models only. All dataclasses are frozen with slots,
matching the conventions of the Engineering Runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ViolationSeverity(str, Enum):
    """Severity levels for architectural violations."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ViolationCategory(str, Enum):
    """Categories of constitutional rules."""

    STRUCTURAL = "structural"
    OWNERSHIP = "ownership"
    EVOLUTION = "evolution"


class ArchitectureLayer(str, Enum):
    """Canonical layers in the Financial OS architecture."""

    BACKEND_ENGINE = "backend_engine"
    BACKEND_SERVICE = "backend_service"
    BACKEND_ROUTER = "backend_router"
    BACKEND_DTO = "backend_dto"
    BACKEND_REPOSITORY = "backend_repository"

    FRONTEND_API = "frontend_api"
    FRONTEND_CAPABILITY = "frontend_capability"
    FRONTEND_MAPPER = "frontend_mapper"
    FRONTEND_VIEWMODEL = "frontend_viewmodel"
    FRONTEND_WORKSPACE = "frontend_workspace"
    FRONTEND_COMPONENT = "frontend_component"
    FRONTEND_PAGE = "frontend_page"

    UNKNOWN = "unknown"


# Canonical layer ordering — lower numbers are deeper layers that higher
# layers may depend on.  A layer may depend on any layer with a *lower*
# number in the same stack (backend or frontend).  Importing a higher-numbered
# layer constitutes an upward / bypass violation.
LAYER_ORDER: dict[ArchitectureLayer, int] = {
    # Backend stack
    ArchitectureLayer.BACKEND_ENGINE: 0,
    ArchitectureLayer.BACKEND_REPOSITORY: 1,
    ArchitectureLayer.BACKEND_SERVICE: 2,
    ArchitectureLayer.BACKEND_ROUTER: 3,
    ArchitectureLayer.BACKEND_DTO: 0,
    # Frontend stack
    ArchitectureLayer.FRONTEND_API: 0,
    ArchitectureLayer.FRONTEND_CAPABILITY: 1,
    ArchitectureLayer.FRONTEND_MAPPER: 2,
    ArchitectureLayer.FRONTEND_VIEWMODEL: 3,
    ArchitectureLayer.FRONTEND_WORKSPACE: 4,
    ArchitectureLayer.FRONTEND_COMPONENT: 5,
    ArchitectureLayer.FRONTEND_PAGE: 6,
    ArchitectureLayer.UNKNOWN: -1,
}


@dataclass(frozen=True, slots=True)
class RuleReference:
    """A reference to a constitutional rule that was violated."""

    rule_id: str
    name: str
    category: ViolationCategory
    severity: ViolationSeverity


@dataclass(frozen=True, slots=True)
class Violation:
    """An architectural violation detected by a rule.

    Immutable and comparable.  Two violations are equal when they reference
    the same rule and file path and line number.
    """

    rule_id: str
    rule_name: str
    severity: ViolationSeverity
    category: ViolationCategory
    file_path: str
    description: str
    details: str = ""
    suggested_action: str = ""
    line_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "category": self.category.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "description": self.description,
            "details": self.details,
            "suggested_action": self.suggested_action,
        }


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    """Full integrity evaluation report.

    Produced by ``ArchitecturalIntegrityEngine.evaluate()``.  Immutable and
    deterministic for a given repository state.
    """

    timestamp: str
    rules_evaluated: int
    rules_passed: int
    rules_failed: int
    violations: tuple[Violation, ...]
    files_scanned: int
    cross_layer_entries: int
    graph_nodes: int
    graph_edges: int
    scan_errors: tuple[str, ...] = ()
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0

    @property
    def total_violations(self) -> int:
        return len(self.violations)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    @property
    def severity_counts(self) -> dict[str, int]:
        return {
            "CRITICAL": self.critical_count,
            "HIGH": self.high_count,
            "MEDIUM": self.medium_count,
            "LOW": self.low_count,
            "INFO": self.info_count,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "rules_evaluated": self.rules_evaluated,
            "rules_passed": self.rules_passed,
            "rules_failed": self.rules_failed,
            "violations": [v.to_dict() for v in self.violations],
            "files_scanned": self.files_scanned,
            "cross_layer_entries": self.cross_layer_entries,
            "graph_nodes": self.graph_nodes,
            "graph_edges": self.graph_edges,
            "scan_errors": list(self.scan_errors),
            "severity_counts": self.severity_counts,
            "passed": self.passed,
        }
