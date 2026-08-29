# runtime/tests/test_c43_test_generator.py
#
# M9-C43.5 — Boundary + behavior tests for the evidence-driven test generator.
# These tests PROVE the generator never fabricates evidence, never self-approves,
# and only produces candidates from real evidence items.

from __future__ import annotations

import json

from runtime.foundation.verification.test_generator import TestGenerator


def _write_inventory(tmp_path, records):
    p = tmp_path / "inventory.json"
    p.write_text(json.dumps({"survivors": records}))
    return p


def test_class_b_survivors_are_rejected_not_proposed(tmp_path):
    inv = _write_inventory(
        tmp_path,
        [
            {
                "mutant": "m1",
                "source_file": "src/engines/x.py",
                "line": 10,
                "mutation_operator": "constant_replacement",
                "original_expression": "x = 1",
                "mutated_expression": "x = 2",
                "classification": "B",
                "subclassification": "equivalent_rounding_default",
            }
        ],
    )
    gen = TestGenerator()
    batch = gen.generate_from_survivor_inventory("account_engine", inv, "cap")
    assert len(batch.proposals) == 0
    assert len(batch.rejections) == 1
    assert batch.rejections[0].classification == "B"
    assert len(batch.candidates) == 0


def test_class_a_survivors_produce_proposals_and_candidates(tmp_path):
    inv = _write_inventory(
        tmp_path,
        [
            {
                "mutant": "m2",
                "source_file": "src/engines/loan_engine/amortization.py",
                "line": 15,
                "mutation_operator": "comparison_operator_mutation",
                "original_expression": "if month == 12:",
                "mutated_expression": "if month == 13:",
                "classification": "A",
                "subclassification": "real_gap_comparison",
            }
        ],
    )
    gen = TestGenerator()
    batch = gen.generate_from_survivor_inventory("loan_engine", inv, "loans")
    assert len(batch.proposals) == 1
    assert len(batch.candidates) == 1
    prop = batch.proposals[0]
    assert prop.classification == "A"
    assert prop.proposed_test_surface.startswith("backend/tests/")
    cand = batch.candidates[0]
    assert cand.assertion_form == "DIFFERENTIAL"
    # boundary analysis mechanically extracted the constant discrimination
    assert "12" in cand.input_derivation
    assert "13" in cand.input_derivation
    # generated code never contains computed expected values; it skips until
    # an authorized implementation replaces the skip
    assert "pytest.skip" in cand.code
    assert "never" in cand.code.lower()


def test_equivalent_subclassification_rejected_without_reviewed_class(tmp_path):
    inv = _write_inventory(
        tmp_path,
        [
            {
                "mutant": "m3",
                "source_file": "src/engines/x.py",
                "line": 5,
                "mutation_operator": "rounding",
                "original_expression": "round(v)",
                "mutated_expression": "round(v, 2)",
                # NO reviewed classification -> generator falls back to the
                # C42 classifier; "equivalent_*" subclass seeds the
                # equivalence note so the classifier routes to B.
                "classification": None,
                "subclassification": "equivalent_message",
            }
        ],
    )
    gen = TestGenerator()
    batch = gen.generate_from_survivor_inventory("x_engine", inv, "cap")
    assert len(batch.rejections) == 1
    assert batch.rejections[0].classification == "B"


def test_reviewed_class_a_with_equivalent_subclass_still_proposed(tmp_path):
    """Reviewed forensic classification is authoritative: an explicit 'A' is
    honored even if the subclass label alone would have hinted equivalence."""
    inv = _write_inventory(
        tmp_path,
        [
            {
                "mutant": "m3b",
                "source_file": "src/engines/x.py",
                "line": 5,
                "mutation_operator": "rounding",
                "original_expression": "round(v)",
                "mutated_expression": "round(v, 2)",
                "classification": "A",
                "subclassification": "equivalent_message",
            }
        ],
    )
    gen = TestGenerator()
    batch = gen.generate_from_survivor_inventory("x_engine", inv, "cap")
    assert len(batch.proposals) == 1
    assert len(batch.rejections) == 0


def test_ledger_records_boundary_and_outcomes(tmp_path):
    inv = _write_inventory(
        tmp_path,
        [
            {
                "mutant": "m4",
                "source_file": "src/engines/x.py",
                "line": 3,
                "mutation_operator": "boolean",
                "original_expression": "if flag:",
                "mutated_expression": "if not flag:",
                "classification": "A",
                "subclassification": "real_gap_boolean",
            }
        ],
    )
    gen = TestGenerator()
    gen.generate_from_survivor_inventory("x_engine", inv, "cap")
    out = tmp_path / "ledger.json"
    ledger = gen.emit_ledger(out)
    assert "FORBIDDEN" in ledger["boundary"]["self_approval"]
    assert "FORBIDDEN" in ledger["boundary"]["production_modification"]
    assert "human" in ledger["boundary"]["acceptance_authority"].lower()
    assert len(ledger["entries"]) == 1
    assert ledger["entries"][0]["outcome"] == "proposed"
    assert out.read_text()


def test_coverage_gap_generation_respects_threshold(tmp_path):
    cov = {
        "files": {
            "src/services/small.py": {
                "summary": {"missing_lines": 2, "missing_branches": 0},
                "missing_lines": [10, 11],
            },
            "src/services/big.py": {
                "summary": {"missing_lines": 50, "missing_branches": 20},
                "missing_lines": [1, 2, 3],
            },
        }
    }
    covp = tmp_path / "raw-coverage.json"
    covp.write_text(json.dumps(cov))
    gen = TestGenerator()
    batch = gen.generate_from_coverage_gaps(
        "service_layer",
        covp,
        ("src/services/small.py", "src/services/big.py"),
        "services",
        min_gap_items=10,
    )
    assert len(batch.proposals) == 1
    assert batch.proposals[0].source_location.startswith("src/services/big.py")
    assert batch.candidates[0].assertion_form == "INVARIANT"
