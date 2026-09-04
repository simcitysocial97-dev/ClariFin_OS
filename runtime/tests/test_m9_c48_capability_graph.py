# runtime/tests/test_m9_c48_capability_graph.py
#
# M9-C48 C1–C5 acceptance tests for the capability graph resolver.

from __future__ import annotations

import textwrap

import pytest

from runtime.foundation.verification.capability_graph_resolver import (
    CapabilityEdge,
    CapabilityGraphResolver,
    ChangeKind,
    EndpointCapabilityMap,
    FileChange,
    SeverityTier,
    SymbolResolver,
    UnresolvedSymbol,
    derive_capability_from_path,
    filter_requirements_by_tier,
    parse_git_status_output,
    severity_to_tier,
)


# ── C1 / Symbol resolution ────────────────────────────────────────────────


def test_symbol_function():
    src = textwrap.dedent(
        """
        def calculate_payment(amount, rate):
            return amount * rate
        """
    )
    s, u = SymbolResolver().resolve("loans.py", src)
    assert not u
    funcs = [x for x in s if x.kind == "function"]
    assert any(f.qualified_name == "calculate_payment" for f in funcs)


def test_symbol_class_and_method():
    src = textwrap.dedent(
        """
        class LoanService:
            def calculate_payment(self):
                return 1

            def amortize(self):
                return 2
        """
    )
    s, u = SymbolResolver().resolve("service.py", src)
    assert not u
    classes = [x for x in s if x.kind == "class"]
    methods = [x for x in s if x.kind == "method"]
    assert any(c.qualified_name == "LoanService" for c in classes)
    assert any(m.qualified_name == "LoanService.calculate_payment" for m in methods)
    assert any(m.qualified_name == "LoanService.amortize" for m in methods)


def test_symbol_unresolved_syntax_error():
    s, u = SymbolResolver().resolve("bad.py", "def broken(:\n  pass")
    assert any(x.reason == "syntax_error" for x in u)
    # No false symbols emitted.
    assert all(x.reason != "syntax_error" for x in s)


def test_symbol_imports_recorded():
    src = "import json\nfrom collections import defaultdict\n"
    s, u = SymbolResolver().resolve("mod.py", src)
    assert any(x.kind == "import" for x in s)


def test_symbol_resolve_many_aggregates():
    files = {
        "a.py": "def x(): pass\n",
        "b.py": "def y(): pass\n",
    }
    syms, _ = SymbolResolver().resolve_many(files)
    qnames = sorted(x.qualified_name for x in syms if x.kind == "function")
    assert qnames == ["x", "y"]


def test_symbol_unknown_construct_does_not_silently_drop():
    # Decorators etc. should not crash and should not silently disappear;
    # we only require that the parse produces no unresolved markers for
    # valid Python.
    src = "@staticmethod\ndef foo():\n    return 1\n"
    s, u = SymbolResolver().resolve("m.py", src)
    assert not u


# ── C2 / Endpoint capability resolution ───────────────────────────────────


def test_endpoint_explicit_edge_resolves():
    m = EndpointCapabilityMap()
    m.add("POST", "/loans", "loan-engine")
    cap = m.resolve("POST", "/loans")
    assert cap == "loan-engine"


def test_endpoint_path_rule_falls_back():
    cap = derive_capability_from_path("/credit-cards/123")
    assert cap == "credit-card-engine"


def test_endpoint_path_rule_unknown():
    cap = derive_capability_from_path("/totally-unmapped-thing")
    assert cap is None


# ── C3 / Severity tiers ───────────────────────────────────────────────────


def test_severity_to_tier_mapping():
    assert severity_to_tier("critical") == SeverityTier.BLOCKING
    assert severity_to_tier("high") == SeverityTier.REQUIRED
    assert severity_to_tier("medium") == SeverityTier.PRIORITIZED
    assert severity_to_tier("low") == SeverityTier.OPTIONAL
    assert severity_to_tier("info") == SeverityTier.DIAGNOSTIC
    assert severity_to_tier(None) == SeverityTier.OPTIONAL
    assert severity_to_tier("weird") == SeverityTier.OPTIONAL


def test_filter_requirements_by_tier():
    class Req:
        def __init__(self, severity):
            self.severity = severity

    r_crit = Req("critical")  # BLOCKING
    r_high = Req("high")      # REQUIRED
    r_med = Req("medium")     # PRIORITIZED
    r_low = Req("low")        # OPTIONAL
    r_info = Req("info")      # DIAGNOSTIC
    kept = filter_requirements_by_tier([r_crit, r_high, r_med, r_low, r_info])
    assert r_crit in kept
    assert r_high in kept
    assert r_med in kept
    assert r_low not in kept
    assert r_info not in kept


def test_filter_requirements_with_custom_include():
    class Req:
        def __init__(self, severity):
            self.severity = severity

    r_low = Req("low")
    r_info = Req("info")
    kept = filter_requirements_by_tier(
        [r_low, r_info],
        include=frozenset({SeverityTier.OPTIONAL}),
    )
    assert r_low in kept
    assert r_info not in kept


# ── C4 / Rename & C5 / Deletion ───────────────────────────────────────────


def test_parse_git_status_renamed():
    out = "R100\told/path.py\tnew/path.py\n"
    changes = parse_git_status_output(out)
    assert len(changes) == 1
    assert changes[0].kind == ChangeKind.RENAMED
    assert changes[0].old_path == "old/path.py"
    assert changes[0].new_path == "new/path.py"


def test_parse_git_status_added_modified_deleted():
    out = "A\tnew.py\nM\tmod.py\nD\tgone.py\n"
    changes = parse_git_status_output(out)
    kinds = sorted(c.kind.value for c in changes)
    assert kinds == ["added", "deleted", "modified"]


def test_parse_git_status_unknown():
    out = "X\tmystery.py\n"
    changes = parse_git_status_output(out)
    assert changes[0].kind == ChangeKind.UNKNOWN
    assert changes[0].new_path == "mystery.py"


def test_parse_git_status_empty():
    assert parse_git_status_output("") == []


# ── End-to-end graph resolution ────────────────────────────────────────────


def _build_resolver():
    from runtime.foundation.verification.engine_capability_bridge import (
        engine_capability_records,
    )
    from runtime.foundation.verification.registry import get_registry

    reg = get_registry()
    reg.load()
    return CapabilityGraphResolver(
        registry=reg,
        engine_bridge=_FakeBridge(engine_capability_records()),
    )


class _FakeBridge:
    def __init__(self, records):
        self._records = records

    def engine_capability_records(self):
        return self._records


def test_resolution_function_modification_produces_symbol_edge():
    r = _build_resolver()
    src = textwrap.dedent(
        """
        def calculate_payment(amount):
            return amount
        """
    )
    changes = [FileChange(ChangeKind.MODIFIED, None, "backend/src/engines/loan_engine/loans.py")]
    res = r.resolve(changes, sources={"backend/src/engines/loan_engine/loans.py": src})
    sym_edges = [e for e in res.edges if e.source_kind == "symbol"]
    assert any("calculate_payment" in e.source for e in sym_edges)


def test_resolution_class_modification_includes_method():
    r = _build_resolver()
    src = "class LoanService:\n    def calc(self):\n        return 1\n"
    changes = [FileChange(ChangeKind.MODIFIED, None, "backend/src/engines/loan_engine/svc.py")]
    res = r.resolve(changes, sources={"backend/src/engines/loan_engine/svc.py": src})
    qnames = sorted(e.source for e in res.edges if e.source_kind == "symbol")
    assert any("LoanService.calc" in q for q in qnames)


def test_resolution_endpoint_change_resolves_to_capability():
    r = _build_resolver()
    res = r.resolve([], endpoints=[("POST", "/loans")])
    ep_edges = [e for e in res.edges if e.source_kind == "endpoint"]
    assert any(e.capability_id == "loan-engine" for e in ep_edges)


def test_resolution_unmapped_change_is_fail_closed():
    r = _build_resolver()
    changes = [
        FileChange(ChangeKind.MODIFIED, None, "src/some_truly_unknown_module/orphan.py")
    ]
    res = r.resolve(changes)
    assert any(e.capability_id == "UNMAPPED" for e in res.edges)
    assert any(
        c.new_path == "src/some_truly_unknown_module/orphan.py" for c in res.unmapped
    )


def test_resolution_rename_invalidates_old_and_resolves_new():
    r = _build_resolver()
    changes = [
        FileChange(
            ChangeKind.RENAMED,
            "backend/src/engines/loan_engine/old.py",
            "backend/src/engines/loan_engine/new.py",
        )
    ]
    res = r.resolve(changes)
    new_edges = [e for e in res.edges if e.source == "backend/src/engines/loan_engine/new.py"]
    invalidated = [
        e for e in res.edges if e.source == "backend/src/engines/loan_engine/old.py"
    ]
    assert any(e.capability_id == "loan-engine" for e in new_edges)
    assert any(e.capability_id == "INVALIDATED" for e in invalidated)
    assert ("backend/src/engines/loan_engine/old.py", "backend/src/engines/loan_engine/new.py") in res.renamed_paths


def test_resolution_deletion_marks_capability_deleted():
    r = _build_resolver()
    changes = [
        FileChange(
            ChangeKind.DELETED, None, "backend/src/engines/loan_engine/gone.py"
        )
    ]
    res = r.resolve(changes)
    assert "loan-engine" in res.deleted_capabilities
    assert any(e.capability_id == "DELETED" for e in res.edges)


def test_resolution_unresolved_symbol_recorded_not_dropped():
    r = _build_resolver()
    changes = [FileChange(ChangeKind.MODIFIED, None, "backend/src/engines/loan_engine/bad.py")]
    res = r.resolve(changes, sources={"backend/src/engines/loan_engine/bad.py": "def broken(:\n"})
    assert any(u.reason == "syntax_error" for u in res.unresolved_symbols)


def test_resolution_unmapped_endpoint_fail_closed():
    r = _build_resolver()
    res = r.resolve([], endpoints=[("GET", "/totally-unmapped-route")])
    assert any(e.capability_id == "UNMAPPED" for e in res.edges)


def test_resolution_to_dict_roundtrip():
    r = _build_resolver()
    changes = [
        FileChange(ChangeKind.MODIFIED, None, "backend/src/engines/loan_engine/x.py"),
        FileChange(
            ChangeKind.RENAMED,
            "backend/src/engines/loan_engine/old.py",
            "backend/src/engines/loan_engine/new.py",
        ),
    ]
    res = r.resolve(changes)
    d = res.to_dict()
    assert d["schema"] == "m9-c48/capability-resolution@1"
    assert "loan-engine" in d["affected_capability_ids"]
    assert len(d["edges"]) > 0


def test_resolution_preserves_severity_for_each_edge():
    r = _build_resolver()
    changes = [
        FileChange(ChangeKind.MODIFIED, None, "backend/src/engines/loan_engine/x.py")
    ]
    res = r.resolve(changes)
    for e in res.edges:
        assert e.severity in set(SeverityTier)


def test_resolution_affected_capabilities_deterministic_order():
    r = _build_resolver()
    changes = [
        FileChange(ChangeKind.MODIFIED, None, "backend/src/engines/loan_engine/a.py"),
        FileChange(ChangeKind.MODIFIED, None, "backend/src/engines/credit_card_engine/b.py"),
    ]
    res1 = r.resolve(changes)
    res2 = r.resolve(changes)
    assert res1.affected_capability_ids == res2.affected_capability_ids
