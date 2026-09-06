# runtime/tests/test_m9_c48_api_schema_governance.py

from __future__ import annotations

import json

from runtime.foundation.verification.api_schema_governance import (
    HISTORICAL_DEFECTS,
    build_governance_report,
    load_contract_evidence,
    workflow_present,
)


def test_historical_defects_recorded():
    assert any(d["id"] == "loan-api-response-shape-c30-c32" for d in HISTORICAL_DEFECTS)


def test_workflow_present_in_real_repo():
    assert workflow_present()


def test_load_contract_evidence_handles_missing(tmp_path):
    rep = load_contract_evidence(tmp_path / "missing.json")
    assert rep is None


def test_build_report_minimal(tmp_path):
    rep = build_governance_report(
        evidence_path=tmp_path / "missing.json",
        workflows_dir=tmp_path / "wf",
    )
    assert rep.state == "UNKNOWN"
    assert rep.historical_defects == HISTORICAL_DEFECTS
    assert rep.current_contract is None


def test_build_report_resolved_with_evidence(tmp_path):
    (tmp_path / "evidence.json").write_text(
        json.dumps({"status": "PASS", "structural": {"status": "PASS"}})
    )
    wf = tmp_path / "wf"
    wf.mkdir()
    (wf / "api-contracts.yml").write_text("name: x\n")
    rep = build_governance_report(
        evidence_path=tmp_path / "evidence.json", workflows_dir=wf
    )
    assert rep.state == "RESOLVED"
    assert rep.enforcement_workflow_present is True
    assert rep.current_contract is not None
    assert rep.current_contract.gate_status == "PASS"
    assert rep.current_contract.dimensions.get("structural") == "PASS"


def test_build_report_unresolved_status(tmp_path):
    (tmp_path / "evidence.json").write_text(json.dumps({"status": "FAIL"}))
    rep = build_governance_report(
        evidence_path=tmp_path / "evidence.json",
        workflows_dir=tmp_path / "wf",
    )
    assert rep.state == "UNRESOLVED"


def test_report_to_dict_schema(tmp_path):
    rep = build_governance_report(
        evidence_path=tmp_path / "missing.json",
        workflows_dir=tmp_path / "wf",
    )
    d = rep.to_dict()
    assert d["schema"] == "m9-c48/api-schema-governance@1"
    assert "repository_sha" in d
    assert d["state"] in {"RESOLVED", "UNRESOLVED", "UNKNOWN"}


def test_real_repo_governance_persisted():
    import os

    rep = build_governance_report()
    os.makedirs("runtime/generated/m9-c48", exist_ok=True)
    with open("runtime/generated/m9-c48/api-schema-governance.json", "w") as f:
        json.dump(rep.to_dict(), f, indent=2)
    # Real repo: gate evidence exists.
    assert rep.current_contract is not None
    assert rep.enforcement_workflow_present is True
