# runtime/tests/test_strengthen_cli.py
#
# M9-C45.6 — Focused tests for the strengthen CLI consume of the durable
# survivor-intel record.
#
# Validates that `verify.py strengthen-discover --from-intel` derives
# per-component, correctly-classified evidence from the durable intel and does
# NOT double-count or fall back to the coarse behaviour_engine survivors file.

from __future__ import annotations

import json

from runtime.foundation.verification.forensic_cli import run_strengthen_discover


def _write_intel(path, survivors):
    path.write_text(
        json.dumps(
            {
                "schema": "m9-c45-survivor-intel/v1",
                "total_survivors": len(survivors),
                "survivors": survivors,
            }
        )
    )


def test_discover_consumes_durable_intel(tmp_path, capsys):
    intel_path = tmp_path / "mutation-survivor-intel.json"
    _write_intel(
        intel_path,
        [
            {
                "survivor_id": "engines.financial_intelligence.x_a__mutmut_1",
                "component": "financial_intelligence",
                "capability": "financial-intelligence",
                "source_file": "src/engines/financial_intelligence/x.py",
                "function": "x_a",
                "mutation_type": "comparison",
                "original_expression": "a > b",
                "mutated_expression": "a >= b",
                "status": "survived",
                "classification": "A",
                "classification_evidence": "genuine gap",
                "covering_tests": [],
                "recommended_action": "add boundary test",
            },
            {
                "survivor_id": "engines.transaction_intelligence.y_b__mutmut_2",
                "component": "transaction_intelligence",
                "capability": "transaction-intelligence",
                "source_file": "src/engines/transaction_intelligence/y.py",
                "function": "y_b",
                "mutation_type": "boolean",
                "original_expression": "if a and b",
                "mutated_expression": "if a or b",
                "status": "survived",
                "classification": "A",
                "classification_evidence": "genuine gap",
                "covering_tests": [],
                "recommended_action": "add boolean boundary test",
            },
        ],
    )

    out = tmp_path / "discover.json"
    rc = run_strengthen_discover(
        [
            "--from-intel",
            str(intel_path),
            "--from-survivors",
            str(tmp_path / "nonexistent.json"),
            "--class-filter",
            "A",
            "B",
            "--out",
            str(out),
        ]
    )

    assert rc == 0
    payload = json.loads(out.read_text())
    # Exactly the 2 durable-intel records; the nonexistent survivors file is
    # not double-counted.
    assert payload["total_discovered"] == 2
    comps = {e["component"] for e in payload["evidence"]}
    assert comps == {"financial_intelligence", "transaction_intelligence"}


def test_discover_filters_by_class(tmp_path):
    intel_path = tmp_path / "intel.json"
    _write_intel(
        intel_path,
        [
            {
                "survivor_id": "S_A__mutmut_1",
                "component": "financial_intelligence",
                "capability": "behaviour",
                "source_file": "f.py",
                "function": "f",
                "mutation_type": "comparison",
                "status": "survived",
                "classification": "A",
                "covering_tests": [],
            },
            {
                "survivor_id": "S_E__mutmut_2",
                "component": "financial_intelligence",
                "capability": "behaviour",
                "source_file": "g.py",
                "function": "g",
                "mutation_type": "comparison",
                "status": "survived",
                "classification": "E",
                "covering_tests": [],
            },
        ],
    )
    out = tmp_path / "discover.json"
    run_strengthen_discover(
        [
            "--from-intel",
            str(intel_path),
            "--class-filter",
            "A",
            "--out",
            str(out),
        ]
    )
    payload = json.loads(out.read_text())
    assert payload["total_discovered"] == 1
    assert payload["evidence"][0]["classification"] == "A"
