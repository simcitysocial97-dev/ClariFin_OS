# runtime/tests/test_m9_c48_function_audit.py

from __future__ import annotations

import json

from runtime.foundation.verification.function_audit import (
    DISPOSITIONS,
    audit_functions,
)


def test_dispositions_taxonomy():
    expected = {
        "CANONICAL",
        "SUPPORTING",
        "COMPATIBILITY",
        "LEGACY",
        "DEAD",
        "UNREACHABLE",
        "TEST-ONLY",
        "INTERNAL",
        "DUPLICATE-AUTHORITY",
        "NOT_APPLICABLE",
    }
    assert set(DISPOSITIONS) == expected


def test_audit_returns_full_report():
    rep = audit_functions()
    d = rep.to_dict()
    assert d["schema"] == "m9-c48/function-audit@1"
    assert d["total"] > 0


def test_audit_100_percent_coverage():
    """Every function must have a disposition (100% coverage)."""
    rep = audit_functions()
    assert rep.coverage_percent == 100.0
    assert rep.total == len(rep.dispositions)


def test_disposition_values_in_taxonomy():
    rep = audit_functions()
    for d in rep.dispositions:
        assert d.disposition in DISPOSITIONS


def test_canonical_authorities_recorded():
    rep = audit_functions()
    canonicals = [d for d in rep.dispositions if d.disposition == "CANONICAL"]
    # The function_audit module itself must contain canonical entries
    # (audit_functions, build_disposition, classify_commands, …).
    {(d.file.split("/")[-1], d.name) for d in canonicals}
    assert any(d.file.endswith("function_audit.py") for d in canonicals)
    assert any(d.file.endswith("cli_governance.py") for d in canonicals)


def test_duplicate_authorities_recorded():
    rep = audit_functions()
    duplicates = [d for d in rep.dispositions if d.disposition == "DUPLICATE-AUTHORITY"]
    # orchestrator.py run/shard/create_orchestrator are flagged.
    {(d.file.split("/")[-1], d.name) for d in duplicates}
    assert any("orchestrator" in d.file and d.name == "run" for d in duplicates)


def test_persisted_to_real_repo():
    rep = audit_functions()
    d = rep.to_dict()
    import os

    os.makedirs("runtime/generated/m9-c48", exist_ok=True)
    with open("runtime/generated/m9-c48/function-audit.json", "w") as f:
        json.dump(d, f, indent=2)
    assert d["coverage_percent"] == 100.0
    # Persisted file should contain at least the major classifications.
    assert d["by_disposition"].get("CANONICAL", 0) > 0
    assert d["by_disposition"].get("UNREACHABLE", 0) > 0
