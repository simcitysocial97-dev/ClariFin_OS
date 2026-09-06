"""Context Pack Builder (Phase 14).

Assembles minimal sufficient context from provenance-aware sources.
Priority order: failing evidence → recent change → capability →
recent run → knowledge → adjacent capability → architecture → documentation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from runtime.platform.ai.context.provenance import (
    PROVENANCE_TRACKER_INSTANCE,
    ProvenanceTracker,
    build_provenance,
)
from runtime.platform.ai.context.ranker import RankedComponent
from runtime.platform.ai.context.serializer import (
    compute_pack_id,
    estimate_tokens,
)
from runtime.platform.ai.context.trimmer import TRIMMER_INSTANCE, Trimmer

logger = logging.getLogger(__name__)

__all__ = ["ContextBuilder", "build_context_pack"]


# ---------------------------------------------------------------------------
# Context Pack schema
# ---------------------------------------------------------------------------

CONTEXT_PACK_KIND = "platform.context_pack"


class ContextBuilder:
    """Builds deterministic, reproducible context packs."""

    def __init__(
        self,
        provenance: ProvenanceTracker | None = None,
        trimmer: Trimmer | None = None,
    ) -> None:
        self.provenance = provenance or PROVENANCE_TRACKER_INSTANCE
        self.trimmer = trimmer or TRIMMER_INSTANCE
        self._default_budget = 8000  # tokens

    def build(
        self,
        *,
        symptom: str,
        capability_id: str | None = None,
        run_id: str | None = None,
        intent_type: str = "diagnose",
        token_budget: int | None = None,
    ) -> dict[str, Any]:
        """Build a context pack from the given inputs.

        Returns a complete context pack envelope with all components.
        """
        budget = token_budget or self._default_budget
        components: list[RankedComponent] = []

        # Priority 1: Failing evidence (highest)
        evidence_comps = self._gather_failing_evidence(capability_id, run_id)
        components.extend(evidence_comps)

        # Priority 2: Recent change
        change_comps = self._gather_recent_change()
        components.extend(change_comps)

        # Priority 3: Capability
        cap_comps = self._gather_capability(capability_id)
        components.extend(cap_comps)

        # Priority 4: Recent run
        run_comps = self._gather_recent_run(run_id, capability_id)
        components.extend(run_comps)

        # Priority 5: Knowledge
        knowledge_comps = self._gather_knowledge(capability_id, intent_type)
        components.extend(knowledge_comps)

        # Priority 6: Adjacent capability
        adj_comps = self._gather_adjacent_capabilities(capability_id)
        components.extend(adj_comps)

        # Priority 7: Architecture
        arch_comps = self._gather_architecture()
        components.extend(arch_comps)

        # Priority 8: Documentation
        doc_comps = self._gather_documentation()
        components.extend(doc_comps)

        # Trim to budget
        result = self.trimmer.trim(components, budget)

        # Build pack
        pack_data = {
            "kind": CONTEXT_PACK_KIND,
            "version": "1.0.0",
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "symptom": symptom,
            "intent_type": intent_type,
            "capability_id": capability_id,
            "run_id": run_id,
            "components": [c.to_dict() for c in result.kept_components],
            "total_tokens_estimate": result.total_tokens,
            "token_budget": budget,
            "status": result.status,
            "omitted": (
                [
                    {"type": o.component_type, "tokens": o.token_estimate}
                    for o in result.omitted_components
                ]
                if result.omitted_components
                else []
            ),
            "sources": [entry.source_ref for entry in self.provenance.list_entries()],
            "pack_id": None,  # computed after serialization
        }

        # Compute deterministic ID
        pack_data["pack_id"] = compute_pack_id(pack_data)

        return pack_data

    # -----------------------------------------------------------------------
    # Data gathering (Phase 14 stubs — populated in later phases)
    # -----------------------------------------------------------------------

    def _gather_failing_evidence(
        self, capability_id: str | None, run_id: str | None
    ) -> list[RankedComponent]:
        """Gather failing evidence for capability/run."""
        comps: list[RankedComponent] = []

        # Query event store for failed verification events
        try:
            from runtime.system.observability.event_store import EngineeringEventStore

            store = EngineeringEventStore()
            for event in store.iter_events():
                if event.event_type != "VerificationCompleted":
                    continue
                failed = (event.payload or {}).get("passed", True)
                if not failed:
                    ref = self.provenance.add(
                        build_provenance(
                            "event",
                            event.event_id,
                            path=(
                                event.execution_context.get("path")
                                if event.execution_context
                                else None
                            ),
                        )
                    )
                    comps.append(
                        RankedComponent(
                            component_type="failing_evidence",
                            source_kind="evidence",
                            data={
                                "event_id": event.event_id,
                                "timestamp": event.timestamp.isoformat(),
                            },
                            provenance_ref=ref,
                            token_estimate=estimate_tokens(str(event.payload or {})),
                            relevance_score=100,
                        )
                    )
        except Exception as exc:
            logger.debug("Evidence gathering failed: %s", exc)

        return comps[:3]  # top 3

    def _gather_recent_change(self) -> list[RankedComponent]:
        """Gather recent repository changes."""
        comps: list[RankedComponent] = []
        try:
            from runtime.foundation.verification.change_surface import (
                discover_working_tree_changes,
            )

            files = discover_working_tree_changes()
            for filepath in files[:5]:  # top 5 changed files
                ref = self.provenance.add(
                    build_provenance("repository", filepath, path=filepath)
                )
                comps.append(
                    RankedComponent(
                        component_type="recent_change",
                        source_kind="repository",
                        data={"path": filepath, "change_type": "modified"},
                        provenance_ref=ref,
                        token_estimate=estimate_tokens(filepath),
                        relevance_score=80,
                    )
                )
        except Exception as exc:
            logger.debug("Change gathering failed: %s", exc)
        return comps

    def _gather_capability(self, capability_id: str | None) -> list[RankedComponent]:
        """Gather capability definition."""
        comps: list[RankedComponent] = []
        if not capability_id:
            return comps
        try:
            from runtime.platform.api.services import capabilities

            detail = capabilities.build_capability_detail(capability_id)
            if detail:
                ref = self.provenance.add(build_provenance("knowledge", capability_id))
                data = detail["data"]
                comps.append(
                    RankedComponent(
                        component_type="capability",
                        source_kind="knowledge",
                        data={
                            "id": capability_id,
                            "name": data.get("name", ""),
                            "stage": data.get("stage", ""),
                            "cost": data.get("cost", ""),
                            "dependencies": data.get("dependencies", [])[:3],
                            "produces": data.get("produces", [])[:3],
                        },
                        provenance_ref=ref,
                        token_estimate=estimate_tokens(str(data)),
                        relevance_score=70,
                    )
                )
        except Exception as exc:
            logger.debug("Capability gathering failed: %s", exc)
        return comps

    def _gather_recent_run(
        self, run_id: str | None, capability_id: str | None
    ) -> list[RankedComponent]:
        """Gather recent verification runs."""
        comps: list[RankedComponent] = []
        try:
            from runtime.system.observability.event_store import EngineeringEventStore

            store = EngineeringEventStore()
            count = 0
            for event in store.iter_events():
                if event.event_type != "VerificationCompleted" or count >= 3:
                    continue
                meta = event.metadata or {}
                if capability_id and meta.get("capability_id") != capability_id:
                    continue
                ref = self.provenance.add(build_provenance("history", event.event_id))
                comps.append(
                    RankedComponent(
                        component_type="recent_run",
                        source_kind="history",
                        data={"run_id": event.event_id, "status": "completed"},
                        provenance_ref=ref,
                        token_estimate=200,
                        relevance_score=60,
                    )
                )
                count += 1
        except Exception as exc:
            logger.debug("Run gathering failed: %s", exc)
        return comps

    def _gather_knowledge(
        self, capability_id: str | None, intent_type: str
    ) -> list[RankedComponent]:
        """Gather knowledge entries for the capability."""
        comps: list[RankedComponent] = []
        if not capability_id:
            return comps
        try:
            ref = self.provenance.add(
                build_provenance("knowledge", f"{capability_id}.intent")
            )
            comps.append(
                RankedComponent(
                    component_type="knowledge",
                    source_kind="knowledge",
                    data={
                        "capability_id": capability_id,
                        "intent_type": intent_type,
                        "description": f"Knowledge context for {capability_id} in {intent_type} mode",
                    },
                    provenance_ref=ref,
                    token_estimate=150,
                    relevance_score=50,
                )
            )
        except Exception as exc:
            logger.debug("Knowledge gathering failed: %s", exc)
        return comps

    def _gather_adjacent_capabilities(
        self, capability_id: str | None
    ) -> list[RankedComponent]:
        """Gather adjacent capabilities from the graph."""
        comps: list[RankedComponent] = []
        if not capability_id:
            return comps
        try:
            from runtime.platform.api.services import capabilities

            graph = capabilities.build_capability_graph(capability_id)
            if graph:
                upstream = graph.get("data", {}).get("upstream", [])[:2]
                downstream = graph.get("data", {}).get("downstream", [])[:2]
                for cap_id in set(upstream + downstream):
                    ref = self.provenance.add(
                        build_provenance("knowledge", f"{cap_id}.adjacent")
                    )
                    comps.append(
                        RankedComponent(
                            component_type="adjacent_capability",
                            source_kind="knowledge",
                            data={"id": cap_id},
                            provenance_ref=ref,
                            token_estimate=100,
                            relevance_score=30,
                        )
                    )
        except Exception as exc:
            logger.debug("Adjacent capability gathering failed: %s", exc)
        return comps

    def _gather_architecture(self) -> list[RankedComponent]:
        """Gather architecture authority state."""
        comps: list[RankedComponent] = []
        try:
            from runtime.platform.api.services import architecture

            auth = architecture.build_architecture_authorities()
            if auth:
                items = auth.get("data", {}).get("items", [])[:2]
                for item in items:
                    ref = self.provenance.add(
                        build_provenance("architecture", item.get("name", ""))
                    )
                    comps.append(
                        RankedComponent(
                            component_type="architecture",
                            source_kind="architecture",
                            data=item,
                            provenance_ref=ref,
                            token_estimate=200,
                            relevance_score=20,
                        )
                    )
        except Exception as exc:
            logger.debug("Architecture gathering failed: %s", exc)
        return comps

    def _gather_documentation(self) -> list[RankedComponent]:
        """Gather relevant documentation references."""
        # Stub: Phase 17+ will populate with actual docs
        return []


def build_context_pack(
    *,
    symptom: str,
    capability_id: str | None = None,
    run_id: str | None = None,
    intent_type: str = "diagnose",
    token_budget: int | None = None,
) -> dict[str, Any]:
    """Convenience function to build a context pack."""
    builder = ContextBuilder()
    return builder.build(
        symptom=symptom,
        capability_id=capability_id,
        run_id=run_id,
        intent_type=intent_type,
        token_budget=token_budget,
    )
