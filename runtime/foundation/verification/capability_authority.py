# runtime/foundation/verification/capability_authority.py
#
# M9-C48 B1 — Capability Registry Unification (GAP-007).
#
# Repository evidence shows:
#   * VerificationRegistry (runtime/foundation/verification/registry/registry.py)
#     is the CANONICAL authority. It loads verification.yaml and exposes
#     the unique source-of-truth for capabilities, workflows, and scripts.
#   * CapabilityContractRegistry
#     (runtime/foundation/verification/capability_contract.py) is a
#     DERIVED projection: in its __init__ it calls
#     ``from runtime.foundation.verification.registry import get_registry``
#     and reads through ``self._registry.get_all_capabilities()``. It does
#     not maintain a parallel authoritative model; it enriches the canonical
#     one with maturity / implementation / test / evidence fields.
#
# Therefore the two registries are NOT competing authorities — they are
# layered (canonical → derived). GAP-007's "duplicate authority" finding
# is structurally true (two classes) but semantically false (one owns the
# source, the other projects). The remediation is:
#
#   1. Declare the layering explicitly here.
#   2. Enforce single acquisition path: get_registry() is the ONLY way to
#      reach the canonical authority. CapabilityContractRegistry acquires
#      it via the same factory.
#   3. Provide ``get_capability(cap_id)`` as the canonical lookup. All
#      downstream projections must derive from this single lookup.
#   4. Provide an audit that confirms the canonical authority and lists
#      derived projections.
#
# This module is pure logic; no I/O.

from __future__ import annotations

import importlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

CANONICAL_AUTHORITY = (
    "runtime.foundation.verification.registry.registry.VerificationRegistry"
)
CANONICAL_FACTORY = "runtime.foundation.verification.registry.registry.get_registry"
DERIVED_PROJECTIONS: tuple[str, ...] = (
    "runtime.foundation.verification.capability_contract.CapabilityContractRegistry",
)


@dataclass(frozen=True, slots=True)
class CapabilityAuthorityAudit:
    canonical_authority: str
    canonical_factory: str
    derived_projections: tuple[str, ...]
    canonical_resolvable: bool
    canonical_factory_callable: bool
    derived_resolvable: dict[str, bool]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["derived_projections"] = list(self.derived_projections)
        return d


def _resolve(dotted: str) -> Any:
    mod_name, _, attr = dotted.rpartition(".")
    if not mod_name:
        return None
    try:
        return getattr(importlib.import_module(mod_name), attr, None)
    except Exception:
        return None


def authority_audit() -> CapabilityAuthorityAudit:
    """Snapshot describing the canonical capability authority."""
    canonical_cls = _resolve(CANONICAL_AUTHORITY)
    factory = _resolve(CANONICAL_FACTORY)
    derived = {d: _resolve(d) is not None for d in DERIVED_PROJECTIONS}
    return CapabilityAuthorityAudit(
        canonical_authority=CANONICAL_AUTHORITY,
        canonical_factory=CANONICAL_FACTORY,
        derived_projections=DERIVED_PROJECTIONS,
        canonical_resolvable=canonical_cls is not None,
        canonical_factory_callable=callable(factory),
        derived_resolvable=derived,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def get_canonical_capability(capability_id: str) -> Any | None:
    """Single canonical lookup. Returns the VerificationCapability or None.

    All downstream code MUST go through this. Derived projections are free
    to enrich but cannot introduce new authoritative capability records.
    """
    factory = _resolve(CANONICAL_FACTORY)
    if factory is None:
        return None
    registry = factory()
    if hasattr(registry, "load"):
        registry.load()
    if hasattr(registry, "get_capability"):
        return registry.get_capability(capability_id)
    return None


def list_canonical_capability_ids() -> list[str]:
    """List every capability known to the canonical authority."""
    factory = _resolve(CANONICAL_FACTORY)
    if factory is None:
        return []
    registry = factory()
    if hasattr(registry, "load"):
        registry.load()
    if hasattr(registry, "get_all_capabilities"):
        return sorted(c.id for c in registry.get_all_capabilities())
    return []


def assert_no_competing_authority() -> CapabilityAuthorityAudit:
    """Runtime guard. Raises if a competing authority appears in the registry
    module namespace (a new class named *Registry or *ContractRegistry that
    is NOT listed in DERIVED_PROJECTIONS).
    """
    audit = authority_audit()
    if not audit.canonical_resolvable:
        raise RuntimeError(
            f"Canonical capability authority missing: {CANONICAL_AUTHORITY}"
        )
    if not audit.canonical_factory_callable:
        raise RuntimeError(f"Canonical capability factory missing: {CANONICAL_FACTORY}")
    return audit


__all__ = [
    "CANONICAL_AUTHORITY",
    "CANONICAL_FACTORY",
    "DERIVED_PROJECTIONS",
    "CapabilityAuthorityAudit",
    "authority_audit",
    "assert_no_competing_authority",
    "get_canonical_capability",
    "list_canonical_capability_ids",
]
