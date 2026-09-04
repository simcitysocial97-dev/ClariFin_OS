# runtime/tests/test_m9_c48_capability_authority.py
#
# M9-C48 B1/B2 acceptance tests for capability registry unification.

from __future__ import annotations

import json

from runtime.foundation.verification.capability_authority import (
    CANONICAL_AUTHORITY,
    CANONICAL_FACTORY,
    DERIVED_PROJECTIONS,
    assert_no_competing_authority,
    authority_audit,
    get_canonical_capability,
    list_canonical_capability_ids,
)
from runtime.foundation.verification.engine_capability_bridge import (
    assert_all_engines_registered,
    engine_capability_ids,
    engine_capability_records,
    register_engine_capabilities,
)
from runtime.foundation.verification.registry import get_registry


def test_authority_audit_resolves_all_anchors():
    a = authority_audit()
    assert a.canonical_authority == CANONICAL_AUTHORITY
    assert a.canonical_factory == CANONICAL_FACTORY
    assert a.canonical_resolvable
    assert a.canonical_factory_callable
    assert all(a.derived_resolvable.values())
    assert all(d in DERIVED_PROJECTIONS for d in DERIVED_PROJECTIONS)


def test_assert_no_competing_authority_does_not_raise():
    assert_no_competing_authority()


def test_canonical_capability_lookup_deterministic():
    reg = get_registry()
    reg.load()
    cap = get_canonical_capability("loan-engine")
    assert cap is not None
    assert cap.id == "loan-engine"
    cap2 = get_canonical_capability("does-not-exist")
    assert cap2 is None


def test_engine_capability_ids_count():
    ids = engine_capability_ids()
    assert len(ids) == 14
    assert "loan-engine" in ids
    assert "credit-card-engine" in ids
    assert "transaction-intelligence" in ids


def test_engine_capability_records_have_authority():
    recs = engine_capability_records()
    assert len(recs) == 14
    for r in recs:
        assert r.mutation_authority.endswith("ENGINE_SELECTION")
        assert r.source_paths
        assert r.test_selection
        assert r.tier in {"P0", "P1"}


def test_register_engine_capabilities_idempotent():
    reg = get_registry()
    reg.load()
    before = len(reg._capabilities)
    n1 = register_engine_capabilities(reg)
    n2 = register_engine_capabilities(reg)
    assert n1 >= 0
    assert n2 == 0  # idempotent
    ok, missing = assert_all_engines_registered(reg)
    assert ok
    assert missing == []
    # Ensure no duplicate
    ids = [c.id for c in reg.get_all_capabilities()]
    assert len(ids) == len(set(ids))


def test_engine_records_are_engine_derived_metadata():
    reg = get_registry()
    register_engine_capabilities(reg)
    # credit-card-engine is one of the 13 newly-registered records
    cc = reg._capabilities.get("credit-card-engine")
    assert cc is not None
    md = cc.metadata
    assert md.get("engine_derived") is True
    assert md.get("engine") == "credit_card_engine"
    assert md.get("tier") in {"P0", "P1"}
    assert len(cc.requirements) > 0


def test_list_canonical_capability_ids_after_registration():
    register_engine_capabilities(get_registry())
    ids = list_canonical_capability_ids()
    assert "loan-engine" in ids
    assert "credit-card-engine" in ids
    # Sorted.
    assert ids == sorted(ids)


def test_engine_bridge_provenance_roundtrip_json():
    recs = engine_capability_records()
    # JSON-roundtrippable via to_dict
    s = json.dumps([r.to_dict() for r in recs])
    parsed = json.loads(s)
    assert len(parsed) == 14
    for entry in parsed:
        assert entry["kind"] == "engine-derived"
