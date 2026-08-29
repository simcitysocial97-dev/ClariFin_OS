# runtime/tests/test_survivor_intel.py
#
# M9-C45.2 — Focused tests for the durable survivor-intel capability.
#
# These validate the pure/introspectable parts of survivor_intel without
# executing any mutation campaign (no mutmut run):
#   * capability attribution (single + multi-capability + unmapped)
#   * component resolution from source paths
#   * evidence-fingerprint determinism
#   * A–E classification reuse (via the C42.17 pure classifier)
#   * structural shape of the durable record built from a synthetic catalog
#
# build_survivor_intel is exercised with build_survivor_catalog / mutmut
# tests-for-mutant monkeypatched so the test is hermetic and fast.

from __future__ import annotations

import json

import pytest


@pytest.fixture
def synthetic_catalog_factory(monkeypatch, tmp_path):
    """Patch survivor_catalog.build_survivor_catalog + _run_tests_for_mutant so
    build_survivor_intel runs purely offline over a synthetic survivor set."""

    class _SurvivorEntry:
        def __init__(self, key, function, source_file, category, old, new):
            self.key = key
            self.function = function
            self.source_file = source_file
            self.category = category
            self.old = old
            self.new = new

    def make(entries):
        catalog = object.__new__(type("Catalog", (), {}))
        catalog.entries = [
            _SurvivorEntry(
                key=e["key"],
                function=e.get("function", "f"),
                source_file=e.get("source_file", "engines/behaviour_engine/x_f"),
                category=e.get("category", "comparison"),
                old=e.get("old", "x > 5"),
                new=e.get("new", "x >= 5"),
            )
            for e in entries
        ]
        monkeypatch.setattr(
            "runtime.foundation.verification.survivor_catalog.build_survivor_catalog",
            lambda meta_dir, backend_dir: catalog,
        )
        monkeypatch.setattr(
            "runtime.foundation.verification.survivor_intel._run_tests_for_mutant",
            lambda survivor_id: (["tests/unit/engines/behaviour/test_x.py::test_1"], "derived_from_tests-for-mutant"),
        )
        return catalog

    return make


def test_component_for_source_maps_engines():
    from runtime.foundation.verification.survivor_intel import component_for_source

    assert component_for_source("engines/financial_intelligence/scenario.py") == "financial_intelligence"
    assert component_for_source("engines/transaction_intelligence/cash_conversion_detector.py") == "transaction_intelligence"
    assert component_for_source("engines/behaviour_engine/core/x_f.py") == "behaviour_engine"


def test_component_for_source_none_when_unmapped():
    from runtime.foundation.verification.survivor_intel import component_for_source

    assert component_for_source("totally/unknown/module.py") is None


def test_capability_for_single():
    from runtime.foundation.verification.survivor_intel import capability_for

    primary, caps = capability_for(
        "SURV_1",
        "engines/financial_intelligence/scenario.py",
    )
    assert primary == "financial-intelligence"
    assert caps == ["financial-intelligence"]


def test_capability_for_multi():
    from runtime.foundation.verification.survivor_intel import capability_for

    primary, caps = capability_for("SURV_2", "common/calculations.py")
    assert primary == "common-calculations"
    assert "loans" in caps and "credit-cards" in caps


def test_capability_unmapped():
    from runtime.foundation.verification.survivor_intel import capability_for

    primary, caps = capability_for("SURV_3", "unmapped/things.py")
    assert primary == "UNMAPPED_CAPABILITY"


def test_evidence_fingerprint_deterministic():
    from runtime.foundation.verification.survivor_intel import _evidence_fingerprint

    a = _evidence_fingerprint({"id": "X", "loc": "a.py", "old": "1", "new": "2"})
    b = _evidence_fingerprint({"id": "X", "loc": "a.py", "old": "1", "new": "2"})
    c = _evidence_fingerprint({"id": "X", "loc": "a.py", "old": "1", "new": "3"})
    assert a == b
    assert a != c


def test_classify_reuse_real_gap_and_equivalent():
    from runtime.foundation.verification.mutation_inventory import classify

    gap = classify("if x > 5:", "if x >= 5:")
    assert gap.classification == "A"

    eq = classify("raise ValueError('bad input')", "raise ValueError('unexpected')")
    assert eq.classification == "B"


def test_build_survivor_intel_shape(synthetic_catalog_factory):
    from runtime.foundation.verification.survivor_intel import (
        build_survivor_intel,
    )

    synthetic_catalog_factory(
        [
            {
                "key": "engines.financial_intelligence.scenario.x_foir__mutmut_1",
                "source_file": "engines/financial_intelligence/scenario.py",
                "category": "comparison",
                "old": "x > 5",
                "new": "x >= 5",
            },
            {
                "key": "common.calculations.x_is_large__mutmut_2",
                "source_file": "common/calculations.py",
                "category": "arithmetic",
                "old": "avg * 250000",
                "new": "avg * 250001",
            },
        ]
    )

    intel = build_survivor_intel(
        __import__("pathlib").Path("/synthetic/meta"),
        __import__("pathlib").Path("/synthetic/backend"),
    )

    assert intel["total_survivors"] == 2
    assert intel["schema"] == "m9-c45-survivor-intel/v1"
    assert intel["tests_enriched_count"] >= 1

    by_id = {s["survivor_id"]: s for s in intel["survivors"]}
    fi = by_id["engines.financial_intelligence.scenario.x_foir__mutmut_1"]
    assert fi["component"] == "financial_intelligence"
    assert fi["capability"] == "financial-intelligence"
    assert fi["classification"] == "A"
    assert fi["covering_tests"] == ["tests/unit/engines/behaviour/test_x.py::test_1"]
    assert len(fi["evidence_fingerprint"]) == 64

    cc = by_id["common.calculations.x_is_large__mutmut_2"]
    assert cc["component"] == "common_calculations"
    assert cc["capability"] == "common-calculations"
    assert "loans" in cc["capabilities"]

    # Fingerprints must differ across distinct survivors.
    assert fi["evidence_fingerprint"] != cc["evidence_fingerprint"]


def test_build_survivor_intel_writes_and_loads(synthetic_catalog_factory, tmp_path):
    from runtime.foundation.verification.survivor_intel import (
        build_survivor_intel,
        load_survivor_intel,
        write_survivor_intel,
    )

    synthetic_catalog_factory(
        [
            {
                "key": "engines.behaviour_engine.utils.x_median__mutmut_9",
                "source_file": "engines/behaviour_engine/utils.py",
                "category": "numeric_literal",
                "old": "2",
                "new": "3",
            }
        ]
    )
    intel = build_survivor_intel(
        __import__("pathlib").Path("/m"),
        __import__("pathlib").Path("/b"),
    )
    out = write_survivor_intel(intel, tmp_path / "intel.json")
    assert out.exists()

    loaded = load_survivor_intel(tmp_path / "intel.json")
    assert loaded["total_survivors"] == 1
    rec = loaded["survivors"][0]
    assert rec["survivor_id"] == "engines.behaviour_engine.utils.x_median__mutmut_9"
    assert rec["capability"] == "behaviour"
    # Durable C45 schema is JSON-serializable.
    json.dumps(loaded)


def test_metric_no_fabricated_investigation_status(synthetic_catalog_factory):
    from runtime.foundation.verification.survivor_intel import build_survivor_intel

    synthetic_catalog_factory([{"key": "K__mutmut_1", "category": "comparison"}])
    intel = build_survivor_intel(
        __import__("pathlib").Path("/m"), __import__("pathlib").Path("/b")
    )
    rec = intel["survivors"][0]
    # Honest default: survivors are flagged as needing investigation, never
    # auto-marked resolved or auto-proposed.
    assert rec["investigation_status"] == "needs_investigation"
    assert rec["previous_proposal_status"] == "not_attempted"
    assert rec["previous_validation_status"] == "not_attempted"


def test_source_path_from_meta_uses_meta_layout():
    """M9-C45.2 lifecycle fix: the mutated-source path is derived from the
    .meta layout (mutants/<source_rel>.meta), independent of the resting
    [tool.mutmut] scope. Without this, post-run diff reconstruction silently
    failed whenever the resting backend scope differed from the last target.
    """
    from pathlib import Path

    from runtime.foundation.verification.survivor_catalog import source_path_from_meta

    meta_dir = Path("/mut")
    meta_file = meta_dir / "src" / "engines" / "financial_intelligence" / "optimization.py.meta"
    assert (
        source_path_from_meta(meta_file, meta_dir)
        == "src/engines/financial_intelligence/optimization.py"
    )

    # Files outside meta_dir (defensive) yield None -> caller falls back.
    assert source_path_from_meta(Path("/elsewhere/optimization.py.meta"), meta_dir) is None


def test_classify_diff_real_gap_vs_control():
    from runtime.foundation.verification.survivor_catalog import _classify_diff

    # Comparison flip in control flow -> comparison (real gap signal).
    cat, old, new = _classify_diff(
        "--- src.py\n+++ src.py\n@@ -1 +1 @@\n-  if x > 5:\n+  if x >= 5:\n"
    )
    assert cat == "comparison"
    # Arithmetic change -> arithmetic.
    cat2, _, _ = _classify_diff(
        "--- src.py\n+++ src.py\n@@ -1 +1 @@\n-  return n * 2\n+  return n * 3\n"
    )
    assert cat2 == "arithmetic"
    # Boolean flip -> boolean.
    cat4, _, _ = _classify_diff(
        "--- src.py\n+++ src.py\n@@ -1 +1 @@\n-  if a and b:\n+  if a or b:\n"
    )
    assert cat4 == "boolean"
    # String/dict-key label changes are NOT falsely escalated: they fall back to
    # control_flow (the classifier deliberately does not manufacture a stronger
    # signal for label-only mutations, preserving honest reporting).
    cat3, _, _ = _classify_diff(
        "--- src.py\n+++ src.py\n@@ -1 +1 @@\n-    d[\"key\"] = 1\n+    d[\"KEY\"] = 1\n"
    )
    assert cat3 == "control_flow"
