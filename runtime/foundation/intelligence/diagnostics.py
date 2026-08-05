from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.foundation.intelligence.models import DiagnosticReport, RepairSuggestion
from runtime.foundation.intelligence.risk import RiskAnalyzer
from runtime.foundation.verification.planner.planner import (
    CrossLayerImpactPlanner,
)
from runtime.foundation.verification.profiles import get_profile
from runtime.foundation.repository.graph.graph_service import (
    RepositoryGraphService,
)


DEFAULT_CROSS_LAYER_MAP = Path("runtime/generated/cross-layer-map.json")


@dataclass(frozen=True, slots=True)
class DeveloperDiagnostics:
    cross_layer_planner: (
        CrossLayerImpactPlanner | None
    ) = None
    graph_service: RepositoryGraphService | None = None

    @property
    def _planner(self) -> CrossLayerImpactPlanner:
        if self.cross_layer_planner is not None:
            return self.cross_layer_planner
        return CrossLayerImpactPlanner()

    def diagnose(self, changed_files: list[str]) -> DiagnosticReport:
        cross_layer_report = self._planner.analyze_cross_layer_impact(
            changed_files,
        )

        dependency_chain = list(cross_layer_report.dependency_chains)

        affected_capabilities = list(
            cross_layer_report.affected_capabilities,
        )
        affected_workspaces = list(
            cross_layer_report.affected_workspaces,
        )
        affected_endpoints = list(
            cross_layer_report.affected_endpoints,
        )
        affected_tests = list(cross_layer_report.affected_tests)
        affected_engines = list(cross_layer_report.affected_engines)
        affected_services = list(cross_layer_report.affected_services)
        affected_routers = list(cross_layer_report.affected_routers)
        affected_mappers = list(cross_layer_report.affected_mappers)
        affected_view_models = list(
            cross_layer_report.affected_view_models
        )
        affected_pages = list(cross_layer_report.affected_pages)
        affected_components = list(
            cross_layer_report.affected_components
        )
        affected_graph_renderers = list(
            cross_layer_report.affected_graph_renderers
        )

        repair_suggestions = self._build_repair_suggestions(
            cross_layer_report,
            dependency_chain,
        )

        risk_report = RiskAnalyzer().analyze(cross_layer_report)

        profile_name = self._suggest_profile(
            cross_layer_report,
            risk_report,
        )

        estimate_local, estimate_ci = self._estimate_verification(
            profile_name,
            risk_report,
        )

        return DiagnosticReport(
            changed_files=tuple(changed_files),
            dependency_chain=tuple(dependency_chain),
            affected_capabilities=tuple(affected_capabilities),
            affected_workspaces=tuple(affected_workspaces),
            affected_endpoints=tuple(affected_endpoints),
            affected_tests=tuple(affected_tests),
            affected_engines=tuple(affected_engines),
            affected_services=tuple(affected_services),
            affected_routers=tuple(affected_routers),
            affected_mappers=tuple(affected_mappers),
            affected_view_models=tuple(affected_view_models),
            affected_pages=tuple(affected_pages),
            affected_components=tuple(affected_components),
            affected_graph_renderers=tuple(
                affected_graph_renderers
            ),
            suggested_verification_profile=profile_name,
            verification_estimate_local_seconds=estimate_local,
            verification_estimate_ci_minutes=estimate_ci,
            risk_score_reference=risk_report.score,
            repair_suggestions=tuple(repair_suggestions),
        )

    def _build_repair_suggestions(
        self,
        report: Any,
        dependency_chain: list[dict[str, Any]],
    ) -> list[RepairSuggestion]:
        suggestions: list[RepairSuggestion] = []

        for chain in dependency_chain:
            source = chain.get("source", "")
            engine = chain.get("engine", "")

            for cap in chain.get("capabilities", []):
                suggestions.append(
                    RepairSuggestion(
                        target=cap,
                        change_type="capability",
                        reason=f"Capability {cap} is affected by change in {source}",
                        guidance="Run contract tests and workspace validation for this capability",
                        dependency_reference=f"engine={engine}, capability={cap}",
                    ),
                )

            for ep in chain.get("endpoints", []):
                suggestions.append(
                    RepairSuggestion(
                        target=ep,
                        change_type="endpoint",
                        reason=f"Endpoint {ep} is affected by change in {source}",
                        guidance="Verify endpoint contract and capability integration",
                        dependency_reference=f"engine={engine}, endpoint={ep}",
                    ),
                )

            for router in chain.get("routers", []):
                suggestions.append(
                    RepairSuggestion(
                        target=router,
                        change_type="router",
                        reason=f"Router {router} is affected by change in {source}",
                        guidance="Verify endpoint contract and capability",
                        dependency_reference=f"engine={engine}, router={router}",
                    ),
                )

            for mapper in chain.get("mappers", []):
                suggestions.append(
                    RepairSuggestion(
                        target=mapper,
                        change_type="mapper",
                        reason=f"Mapper {mapper} is affected by change in {source}",
                        guidance="Update schema mapping and run contract tests",
                        dependency_reference=f"engine={engine}, mapper={mapper}",
                    ),
                )

            for vm in chain.get("viewModels", []):
                suggestions.append(
                    RepairSuggestion(
                        target=vm,
                        change_type="view_model",
                        reason=f"ViewModel {vm} is affected by change in {source}",
                        guidance="Update ViewModel and verify frontend contract",
                        dependency_reference=f"engine={engine}, view_model={vm}",
                    ),
                )

            for ws in chain.get("workspace", []):
                suggestions.append(
                    RepairSuggestion(
                        target=ws,
                        change_type="workspace",
                        reason=f"Workspace {ws} is affected by change in {source}",
                        guidance="Run workspace validation and capability tests",
                        dependency_reference=f"engine={engine}, workspace={ws}",
                    ),
                )

            for renderer in chain.get("graphRenderers", []):
                suggestions.append(
                    RepairSuggestion(
                        target=renderer,
                        change_type="graph_renderer",
                        reason=f"Graph renderer {renderer} is affected by change in {source}",
                        guidance="Verify graph rendering and data flow contract",
                        dependency_reference=f"engine={engine}, renderer={renderer}",
                    ),
                )

            for comp in chain.get("components", []):
                suggestions.append(
                    RepairSuggestion(
                        target=comp,
                        change_type="component",
                        reason=f"Component {comp} is affected by change in {source}",
                        guidance="Verify component contract and workspace integration",
                        dependency_reference=f"engine={engine}, component={comp}",
                    ),
                )

        return suggestions

    def _suggest_profile(
        self,
        report: Any,
        risk_report: Any,
    ) -> str:
        if risk_report.score >= 75:
            return "full"
        if risk_report.score >= 50:
            return "backend"
        if risk_report.score >= 25:
            return "contracts"
        return "quick"

    def _estimate_verification(
        self,
        profile_name: str,
        risk_report: Any,
    ) -> tuple[int, int]:
        profile = get_profile(profile_name)
        base_seconds = sum(
            t.estimated_duration_seconds for t in profile.tasks
        )
        risk_multiplier = 1 + (risk_report.score / 100.0)
        local_seconds = int(base_seconds * risk_multiplier)
        ci_minutes = max(1, local_seconds // 60)
        return local_seconds, ci_minutes