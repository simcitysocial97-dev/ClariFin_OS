from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    changed_files: tuple[str, ...]
    dependency_chain: tuple[dict[str, Any], ...]
    affected_capabilities: tuple[str, ...]
    affected_workspaces: tuple[str, ...]
    affected_endpoints: tuple[str, ...]
    affected_tests: tuple[str, ...]
    suggested_verification_profile: str
    verification_estimate_local_seconds: int
    verification_estimate_ci_minutes: int
    risk_score_reference: int
    affected_engines: tuple[str, ...] = ()
    affected_services: tuple[str, ...] = ()
    affected_routers: tuple[str, ...] = ()
    affected_mappers: tuple[str, ...] = ()
    affected_view_models: tuple[str, ...] = ()
    affected_pages: tuple[str, ...] = ()
    affected_components: tuple[str, ...] = ()
    affected_graph_renderers: tuple[str, ...] = ()
    repair_suggestions: tuple["RepairSuggestion", ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_files": list(self.changed_files),
            "dependency_chain": list(self.dependency_chain),
            "affected_capabilities": list(self.affected_capabilities),
            "affected_workspaces": list(self.affected_workspaces),
            "affected_endpoints": list(self.affected_endpoints),
            "affected_tests": list(self.affected_tests),
            "affected_engines": list(self.affected_engines),
            "affected_services": list(self.affected_services),
            "affected_routers": list(self.affected_routers),
            "affected_mappers": list(self.affected_mappers),
            "affected_view_models": list(self.affected_view_models),
            "affected_pages": list(self.affected_pages),
            "affected_components": list(self.affected_components),
            "affected_graph_renderers": list(
                self.affected_graph_renderers
            ),
            "suggested_verification_profile": self.suggested_verification_profile,
            "verification_estimate_local_seconds": self.verification_estimate_local_seconds,
            "verification_estimate_ci_minutes": self.verification_estimate_ci_minutes,
            "risk_score_reference": self.risk_score_reference,
            "repair_suggestions": [s.to_dict() for s in self.repair_suggestions],
        }


@dataclass(frozen=True, slots=True)
class RepairSuggestion:
    target: str
    change_type: str
    reason: str
    guidance: str
    dependency_reference: str

    def to_dict(self) -> dict[str, str]:
        return {
            "target": self.target,
            "change_type": self.change_type,
            "reason": self.reason,
            "guidance": self.guidance,
            "dependency_reference": self.dependency_reference,
        }


@dataclass(frozen=True, slots=True)
class RiskReport:
    score: int
    severity: Severity
    reasons: tuple[str, ...]
    changed_layers: tuple[str, ...]
    cross_layer_depth: int
    factors: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "severity": self.severity.value,
            "reasons": list(self.reasons),
            "changed_layers": list(self.changed_layers),
            "cross_layer_depth": self.cross_layer_depth,
            "factors": self.factors,
        }


@dataclass(frozen=True, slots=True)
class AffectedTestPlan:
    backend_tests: tuple[str, ...]
    frontend_tests: tuple[str, ...]
    runtime_tests: tuple[str, ...]
    playwright: tuple[str, ...]
    contracts: tuple[str, ...]
    total_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend_tests": list(self.backend_tests),
            "frontend_tests": list(self.frontend_tests),
            "runtime_tests": list(self.runtime_tests),
            "playwright": list(self.playwright),
            "contracts": list(self.contracts),
            "total_count": self.total_count,
        }