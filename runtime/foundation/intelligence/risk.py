from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.intelligence.models import RiskReport, Severity
from runtime.foundation.verification.planner.planner import (
    CrossLayerImpactPlanner,
)


@dataclass(frozen=True, slots=True)
class RiskAnalyzer:
    cross_layer_planner: (
        CrossLayerImpactPlanner | None
    ) = None

    @property
    def _planner(self) -> CrossLayerImpactPlanner:
        if self.cross_layer_planner is not None:
            return self.cross_layer_planner
        return CrossLayerImpactPlanner()

    def analyze(self, report: Any) -> RiskReport:
        factors = self._compute_factors(report)
        score = self._compute_score(factors)
        severity = self._classify_severity(score)
        reasons = self._build_reasons(factors)
        changed_layers = self._identify_layers(report)
        cross_layer_depth = self._compute_cross_layer_depth(report)

        return RiskReport(
            score=score,
            severity=severity,
            reasons=tuple(reasons),
            changed_layers=tuple(changed_layers),
            cross_layer_depth=cross_layer_depth,
            factors=factors,
        )

    def _compute_factors(self, report: Any) -> dict[str, Any]:
        dep_chains = getattr(
            report, "dependency_chains", None
        ) or getattr(report, "dependency_chain", [])
        return {
            "changed_engines": len(report.affected_engines),
            "changed_services": len(report.affected_services),
            "changed_routers": len(report.affected_routers),
            "changed_endpoints": len(report.affected_endpoints),
            "changed_capabilities": len(report.affected_capabilities),
            "changed_mappers": len(report.affected_mappers),
            "changed_view_models": len(report.affected_view_models),
            "changed_pages": len(report.affected_pages),
            "changed_workspaces": len(report.affected_workspaces),
            "changed_components": len(report.affected_components),
            "changed_graph_renderers": len(
                report.affected_graph_renderers
            ),
            "changed_tests": len(report.affected_tests),
            "dependency_chains": len(dep_chains),
        }

    def _compute_score(self, factors: dict[str, Any]) -> int:
        score = 0

        if factors.get("changed_engines", 0) > 0:
            score += 15
        if factors.get("changed_services", 0) > 0:
            score += 10
        if factors.get("changed_routers", 0) > 0:
            score += 12
        if factors.get("changed_endpoints", 0) > 0:
            score += 10
        if factors.get("changed_capabilities", 0) > 0:
            score += 10
        if factors.get("changed_mappers", 0) > 0:
            score += 8
        if factors.get("changed_view_models", 0) > 0:
            score += 6
        if factors.get("changed_pages", 0) > 0:
            score += 5
        if factors.get("changed_workspaces", 0) > 0:
            score += 8
        if factors.get("changed_components", 0) > 0:
            score += 4
        if factors.get("changed_graph_renderers", 0) > 0:
            score += 7
        if factors.get("changed_tests", 0) > 0:
            score += 3

        chain_count = factors.get("dependency_chains", 0)
        if chain_count > 3:
            score += 10
        elif chain_count > 1:
            score += 5

        if score > 100:
            score = 100

        return score

    def _classify_severity(self, score: int) -> Severity:
        if score >= 80:
            return Severity.CRITICAL
        if score >= 60:
            return Severity.HIGH
        if score >= 30:
            return Severity.MEDIUM
        return Severity.LOW

    def _build_reasons(self, factors: dict[str, Any]) -> list[str]:
        reasons: list[str] = []

        if factors.get("changed_engines", 0) > 0:
            reasons.append(
                f"Engine changed ({factors['changed_engines']})"
            )
        if factors.get("changed_services", 0) > 0:
            reasons.append(
                f"Service changed ({factors['changed_services']})"
            )
        if factors.get("changed_routers", 0) > 0:
            reasons.append(
                f"Router changed ({factors['changed_routers']})"
            )
        if factors.get("changed_endpoints", 0) > 0:
            reasons.append(
                f"Endpoint changed ({factors['changed_endpoints']})"
            )
        if factors.get("changed_capabilities", 0) > 0:
            reasons.append(
                f"Capability changed ({factors['changed_capabilities']})"
            )
        if factors.get("changed_mappers", 0) > 0:
            reasons.append(
                f"Mapper changed ({factors['changed_mappers']})"
            )
        if factors.get("changed_view_models", 0) > 0:
            reasons.append(
                f"ViewModel changed ({factors['changed_view_models']})"
            )
        if factors.get("changed_pages", 0) > 0:
            reasons.append(
                f"Page changed ({factors['changed_pages']})"
            )
        if factors.get("changed_workspaces", 0) > 0:
            reasons.append(
                f"Workspace changed ({factors['changed_workspaces']})"
            )
        if factors.get("changed_components", 0) > 0:
            reasons.append(
                f"Component changed ({factors['changed_components']})"
            )
        if factors.get("changed_graph_renderers", 0) > 0:
            reasons.append(
                f"Graph renderer changed ({factors['changed_graph_renderers']})"
            )
        if factors.get("changed_tests", 0) > 0:
            reasons.append(
                f"Test changed ({factors['changed_tests']})"
            )

        return reasons

    def _identify_layers(self, report: Any) -> list[str]:
        layers: list[str] = []
        if report.affected_engines:
            layers.append("engine")
        if report.affected_services:
            layers.append("service")
        if report.affected_routers:
            layers.append("router")
        if report.affected_endpoints:
            layers.append("endpoint")
        if report.affected_capabilities:
            layers.append("capability")
        if report.affected_mappers:
            layers.append("mapper")
        if report.affected_view_models:
            layers.append("view_model")
        if report.affected_pages:
            layers.append("page")
        if report.affected_workspaces:
            layers.append("workspace")
        if report.affected_components:
            layers.append("component")
        if report.affected_graph_renderers:
            layers.append("graph_renderer")
        return layers

    def _compute_cross_layer_depth(self, report: Any) -> int:
        max_depth = 0
        chains = getattr(
            report, "dependency_chains", None
        ) or getattr(report, "dependency_chain", [])
        for chain in chains:
            depth = 0
            if chain.get("engine"):
                depth += 1
            if chain.get("services"):
                depth += 1
            if chain.get("routers"):
                depth += 1
            if chain.get("endpoints"):
                depth += 1
            if chain.get("capabilities"):
                depth += 1
            if chain.get("mappers"):
                depth += 1
            if chain.get("viewModels"):
                depth += 1
            if chain.get("workspace"):
                depth += 1
            if chain.get("components"):
                depth += 1
            if chain.get("graphRenderers"):
                depth += 1
            if depth > max_depth:
                max_depth = depth
        return max_depth