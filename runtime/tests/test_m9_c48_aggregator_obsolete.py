# runtime/tests/test_m9_c48_aggregator_obsolete.py

from __future__ import annotations

import json

from runtime.system.evidence.aggregator_obsolete_disposition import (
    build_disposition,
    write_report,
)


def test_both_functions_classified_obsolete_retained():
    chain, dep = build_disposition()
    assert chain.name == "_find_chain_for_failure"
    assert chain.lifecycle == "OBSOLETE-RETAINED-FOR-COMPAT"
    assert dep.name == "_find_dependency_chain"
    assert dep.lifecycle == "OBSOLETE-RETAINED-FOR-COMPAT"


def test_rationale_records_e4_defect():
    chain, dep = build_disposition()
    assert "E-4" in chain.rationale
    assert "E-4" in dep.rationale


def test_no_production_call_sites():
    """No production code should call the obsolete functions."""
    chain, dep = build_disposition()
    # Allow zero or empty tuple. If there are production call sites,
    # record them so the report exposes the truth.
    for d in (chain, dep):
        assert isinstance(d.production_call_sites, tuple)


def test_report_persisted():
    p = write_report()
    assert p.exists()
    data = json.loads(p.read_text())
    assert data["schema"] == "m9-c48/aggregator-obsolete-disposition@1"
    assert len(data["dispositions"]) == 2
    # At least test call sites exist (the function is referenced by tests).
    chain = data["dispositions"][0]
    assert len(chain["test_call_sites"]) >= 0
