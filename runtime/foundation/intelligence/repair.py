from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.intelligence.models import RepairSuggestion


@dataclass(frozen=True, slots=True)
class RepairGuidance:
    suggestions: tuple[RepairSuggestion, ...]

    def for_capability(self, capability: str) -> list[RepairSuggestion]:
        return [
            s
            for s in self.suggestions
            if s.change_type == "capability"
            and s.target == capability
        ]

    def for_endpoint(self, endpoint: str) -> list[RepairSuggestion]:
        return [
            s
            for s in self.suggestions
            if s.change_type == "endpoint"
            and s.target == endpoint
        ]

    def for_router(self, router: str) -> list[RepairSuggestion]:
        return [
            s
            for s in self.suggestions
            if s.change_type == "router"
            and s.target == router
        ]

    def for_mapper(self, mapper: str) -> list[RepairSuggestion]:
        return [
            s
            for s in self.suggestions
            if s.change_type == "mapper"
            and s.target == mapper
        ]

    def for_view_model(self, vm: str) -> list[RepairSuggestion]:
        return [
            s
            for s in self.suggestions
            if s.change_type == "view_model"
            and s.target == vm
        ]

    def for_workspace(self, ws: str) -> list[RepairSuggestion]:
        return [
            s
            for s in self.suggestions
            if s.change_type == "workspace"
            and s.target == ws
        ]

    def for_graph_renderer(self, renderer: str) -> list[RepairSuggestion]:
        return [
            s
            for s in self.suggestions
            if s.change_type == "graph_renderer"
            and s.target == renderer
        ]

    def for_component(self, comp: str) -> list[RepairSuggestion]:
        return [
            s
            for s in self.suggestions
            if s.change_type == "component"
            and s.target == comp
        ]

    def all_suggestions(self) -> list[RepairSuggestion]:
        return list(self.suggestions)


def build_repair_guidance(
    dependency_chain: list[dict[str, Any]],
) -> RepairGuidance:
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

    return RepairGuidance(suggestions=tuple(suggestions))