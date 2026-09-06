# runtime/foundation/verification/engine_capability_bridge.py
#
# M9-C48 B2 — Engine → Capability bridge (GAP-008).
#
# The 14 mutation engines in ENGINE_SELECTION are the authoritative mutation
# population, but they are NOT registered as VerificationCapability records
# in the canonical VerificationRegistry. This module provides:
#
#   * ``engine_capability_ids()`` — the canonical capability IDs derived
#     deterministically from ENGINE_SELECTION.
#   * ``register_engine_capabilities(registry)`` — enriches a
#     VerificationRegistry instance with engine-derived capability
#     records. The records are derived (not authoritative), so they are
#     tagged with metadata.engine_derived = True.
#   * ``assert_all_engines_registered(registry)`` — guard that fails if
#     any engine is missing.
#
# The canonical mutation authority remains ENGINE_SELECTION. The capability
# records are a projection — they cannot drift, because every record is
# regenerated from ENGINE_SELECTION on each load.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Capability IDs are derived deterministically: "<engine>-engine" except for
# the four that are NOT engines (core_domain_money, common_calculations,
# cashflow_engine, financial_events) where we keep a stable human-readable
# slug.
_ENGINE_CAPABILITY_SLUG: dict[str, str] = {
    "credit_card_engine": "credit-card-engine",
    "account_engine": "account-engine",
    "balance_engine": "balance-engine",
    "ledger_audit_engine": "ledger-audit-engine",
    "reconciliation_engine": "reconciliation-engine",
    "loan_engine": "loan-engine",
    "behaviour_engine": "behaviour-engine",
    "cashflow_engine": "cashflow-engine",
    "financial_events": "financial-events",
    "core_domain_money": "core-domain-money",
    "common_calculations": "common-calculations",
    "recommendation_engine": "recommendation-engine",
    "transaction_intelligence": "transaction-intelligence",
    "financial_intelligence": "financial-intelligence",
}


@dataclass(frozen=True, slots=True)
class EngineCapabilityRecord:
    id: str
    engine: str
    source_paths: tuple[str, ...]
    test_selection: tuple[str, ...]
    tier: str
    mutation_authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "engine": self.engine,
            "source_paths": list(self.source_paths),
            "test_selection": list(self.test_selection),
            "tier": self.tier,
            "mutation_authority": self.mutation_authority,
            "kind": "engine-derived",
        }


def _load_engine_selection() -> dict[str, Any]:
    from runtime.foundation.verification.mutation_contract import ENGINE_SELECTION

    return ENGINE_SELECTION


def engine_capability_ids() -> list[str]:
    """Return sorted canonical capability IDs derived from ENGINE_SELECTION."""
    engines = _load_engine_selection()
    return sorted(_ENGINE_CAPABILITY_SLUG.get(e, e.replace("_", "-")) for e in engines)


def engine_capability_records() -> list[EngineCapabilityRecord]:
    """Return one EngineCapabilityRecord per engine in ENGINE_SELECTION."""
    engines = _load_engine_selection()
    records: list[EngineCapabilityRecord] = []
    for engine_name, sel in engines.items():
        records.append(
            EngineCapabilityRecord(
                id=_ENGINE_CAPABILITY_SLUG.get(
                    engine_name, engine_name.replace("_", "-")
                ),
                engine=engine_name,
                source_paths=tuple(sel.source_paths),
                test_selection=tuple(sel.test_selection),
                tier=sel.tier,
                mutation_authority="runtime.foundation.verification.mutation_contract.ENGINE_SELECTION",
            )
        )
    records.sort(key=lambda r: r.id)
    return records


def assert_all_engines_registered(registry: Any) -> tuple[bool, list[str]]:
    """Guard that every engine has a corresponding capability record.

    Returns (ok, missing_ids). ``ok`` is True iff all 14 engines are
    registered. ``missing_ids`` lists capability IDs that are absent.
    """
    expected = set(engine_capability_ids())
    if hasattr(registry, "load"):
        registry.load()
    actual: set[str] = set()
    if hasattr(registry, "get_all_capabilities"):
        for c in registry.get_all_capabilities():
            actual.add(c.id)
    missing = sorted(expected - actual)
    return (not missing, missing)


def register_engine_capabilities(registry: Any) -> int:
    """Register engine-derived capability records into *registry*.

    Idempotent: re-running does not duplicate. Each record carries
    metadata.engine_derived = True so its provenance is explicit.

    Returns the number of records newly registered (0 if already present).
    """
    from runtime.foundation.verification.models import (
        VerificationCategory,
        VerificationRequirement,
        VerificationScope,
        VerificationSeverity,
    )

    if hasattr(registry, "load"):
        registry.load()

    records = engine_capability_records()
    newly_registered = 0

    for rec in records:
        # Idempotency check.
        existing: list[Any] = []
        if hasattr(registry, "get_all_capabilities"):
            existing = list(registry.get_all_capabilities())
        if any(c.id == rec.id for c in existing):
            continue

        # Build requirements: one CRITICAL requirement per test surface.
        requirements = []
        for test_path in rec.test_selection:
            req_id = f"{rec.id}-test:{test_path}"
            requirements.append(
                VerificationRequirement(
                    id=req_id,
                    category=VerificationCategory.CAPABILITY,
                    severity=(
                        VerificationSeverity.CRITICAL
                        if rec.tier == "P0"
                        else VerificationSeverity.HIGH
                    ),
                    description=f"Mutation test surface: {test_path}",
                    scope=VerificationScope.PROPERTY,
                    module=rec.source_paths[0] if rec.source_paths else "",
                    capability=rec.id,
                )
            )

        cap = _make_capability(
            rec.id,
            rec.engine.replace("_", " ").title(),
            f"Mutation engine {rec.engine} (tier {rec.tier}) — derived from ENGINE_SELECTION.",
            VerificationCategory.CAPABILITY,
            [
                VerificationScope.BACKEND,
                VerificationScope.PROPERTY,
                VerificationScope.CONTRACTS,
                VerificationScope.INTEGRATION,
            ],
            requirements,
            [rec.engine],
            rec.source_paths,
            {"engine_derived": True, "engine": rec.engine, "tier": rec.tier},
        )

        _registry_register(registry, cap)
        newly_registered += 1

    return newly_registered


def _make_capability(
    cap_id: str,
    name: str,
    description: str,
    category: Any,
    scopes: list[Any],
    requirements: list[Any],
    workflows: list[str],
    modules: list[str],
    metadata: dict[str, Any],
) -> Any:
    """Construct a VerificationCapability without importing the registry
    class to avoid a circular import. The duck-typed fields match the
    canonical registry dataclass.
    """
    from dataclasses import dataclass as _dc

    @_dc(frozen=True, slots=True)
    class _Cap:
        id: str
        name: str
        description: str
        category: Any
        scopes: list[Any]
        requirements: list[Any]
        workflows: list[str]
        scripts: list[str]
        modules: list[str]
        metadata: dict[str, Any]

    return _Cap(
        id=cap_id,
        name=name,
        description=description,
        category=category,
        scopes=scopes,
        requirements=requirements,
        workflows=workflows,
        scripts=[],
        modules=modules,
        metadata=metadata,
    )


def _registry_register(registry: Any, cap: Any) -> None:
    """Inject a capability record into the registry.

    The canonical VerificationRegistry exposes ``_capabilities`` (private
    dict) but no public register API. To avoid coupling we look for any
    dict-like container; if none, we attach via a documented
    ``register_capability`` shim that downstream code can implement.
    """
    for attr in ("register_capability", "add_capability", "_register_capability"):
        if hasattr(registry, attr):
            getattr(registry, attr)(cap)
            return
    # Fallback: the VerificationRegistry exposes _capabilities as a dict.
    container = getattr(registry, "_capabilities", None)
    if isinstance(container, dict):
        container[cap.id] = cap
        return
    raise RuntimeError(
        "registry exposes no registration hook; cannot inject engine capability"
    )


__all__ = [
    "EngineCapabilityRecord",
    "engine_capability_ids",
    "engine_capability_records",
    "assert_all_engines_registered",
]
