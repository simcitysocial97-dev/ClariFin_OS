"""Capabilities service adapter (Phase 2 — ``/platform/v1/capabilities*``).

Aggregates the real C50 capability catalog into the Phase 1
``CapabilityList``, ``CapabilityDetail``, and ``CapabilityGraph``
contracts.

No mock state. The adapter reads:

* :func:`runtime.foundation.verification.capability_catalog.get_capability_catalog`

and projects it into the typed contracts. The catalog itself is the
single source of truth (per ``PLATFORM_AI_ARCHITECTURE.md`` §4.1 —
``ADAPT`` not ``BUILD``).
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.verification.capability_catalog import (
    CapabilityCatalog,
    get_capability_catalog,
)
from runtime.platform.api.contracts import capabilities as capabilities_contract
from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.services._helpers import envelope

__all__ = [
    "build_capability_list",
    "build_capability_detail",
    "build_capability_graph",
]


def _entry_to_list_item(entry: Any) -> dict[str, Any]:
    """Project one catalog entry to a Phase 1 ``CapabilityListItem``."""

    return {
        "id": entry.capability_id,
        "name": entry.name,
        "stage": entry.stage.value if hasattr(entry.stage, "value") else str(entry.stage),
        "cost": entry.cost_class.value if hasattr(entry.cost_class, "value") else str(entry.cost_class),
        "authorization": entry.authorization.value if hasattr(entry.authorization, "value") else str(entry.authorization),
        "produces": list(entry.produces or []),
        "triggers": list(entry.trigger_conditions or []),
    }


def build_capability_list() -> dict[str, Any]:
    """Build the ``platform.capability_list`` envelope from the live catalog."""

    catalog: CapabilityCatalog = get_capability_catalog()
    entries = list(catalog.entries)

    # Categories come from the catalog's stage enum values; we expose them
    # as the unique set of stages currently populated by entries. This
    # keeps the surface honest: clients see only stages that actually
    # exist in the repository today.
    seen_stages: set[str] = set()
    items: list[dict[str, Any]] = []
    for entry in entries:
        stage_value = entry.stage.value if hasattr(entry.stage, "value") else str(entry.stage)
        seen_stages.add(stage_value)
        items.append(_entry_to_list_item(entry))

    data = {
        "count": len(items),
        "categories": sorted(seen_stages),
        "items": items,
    }
    return envelope(kind=capabilities_contract.CAPABILITY_LIST_KIND, data=data)


def build_capability_detail(capability_id: str) -> dict[str, Any] | None:
    """Build the ``platform.capability_detail`` envelope for one capability.

    Returns ``None`` when the capability is not present in the live
    catalog — the caller (Phase 3 router) is responsible for converting
    that into a ``NOT_FOUND`` error envelope.
    """

    catalog: CapabilityCatalog = get_capability_catalog()
    entry = catalog.get(capability_id)
    if entry is None:
        return None

    stage_value = entry.stage.value if hasattr(entry.stage, "value") else str(entry.stage)
    cost_value = entry.cost_class.value if hasattr(entry.cost_class, "value") else str(entry.cost_class)
    auth_value = entry.authorization.value if hasattr(entry.authorization, "value") else str(entry.authorization)

    data = {
        "id": entry.capability_id,
        "name": entry.name,
        "stage": stage_value,
        "cost": cost_value,
        "authorization": auth_value,
        "owner": entry.implementation or "capability_catalog",
        "command": entry.command,
        "dependencies": list(entry.consumes or []),
        "produces": list(entry.produces or []),
        "triggers": list(entry.trigger_conditions or []),
        "recent_executions": [],
        "evidence": [],
        "cache_status": None,
        "failure_history": [],
        "health": Status.HEALTHY.value,
    }
    return envelope(kind=capabilities_contract.CAPABILITY_DETAIL_KIND, data=data)


def build_capability_graph(capability_id: str) -> dict[str, Any] | None:
    """Build the ``platform.capability_graph`` envelope for one capability.

    The graph is derived from the catalog's producer/consumer relations:

    * ``upstream`` — capabilities that produce artifacts consumed by
      ``capability_id``.
    * ``downstream`` — capabilities that consume artifacts produced by
      ``capability_id``.
    """

    catalog: CapabilityCatalog = get_capability_catalog()
    if catalog.get(capability_id) is None:
        return None

    upstream_ids: set[str] = set()
    downstream_ids: set[str] = set()

    # ``producers_of`` / ``consumers_of`` take *artifact* names, not
    # capability ids. We walk the catalog twice: once over each artifact
    # ``capability_id`` declares it produces, and once over each
    # artifact it declares it consumes.
    entry = catalog.get(capability_id)
    assert entry is not None
    for artifact in entry.produces or ():
        for consumer in catalog.consumers_of(artifact):
            if consumer.capability_id != capability_id:
                downstream_ids.add(consumer.capability_id)
    for artifact in entry.consumes or ():
        for producer in catalog.producers_of(artifact):
            if producer.capability_id != capability_id:
                upstream_ids.add(producer.capability_id)

    data = {
        "capability_id": capability_id,
        "upstream": sorted(upstream_ids),
        "downstream": sorted(downstream_ids),
    }
    return envelope(kind=capabilities_contract.CAPABILITY_GRAPH_KIND, data=data)
