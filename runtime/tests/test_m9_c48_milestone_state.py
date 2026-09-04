# runtime/tests/test_m9_c48_milestone_state.py
#
# M9-C48 A1 acceptance tests for the machine-verifiable milestone state engine.

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from runtime.foundation.verification.milestone_state import (
    CompletionGuardError,
    Evidence,
    Milestone,
    MilestoneLedger,
    MilestoneStatus,
    compute_sha256,
)


SAMPLE_ARTIFACT = Path(__file__).resolve()  # self


def _make_artifact(tmp_path: Path) -> Path:
    p = tmp_path / "artifact.txt"
    p.write_text("hello\n")
    return p


def test_defaults_have_expected_ids():
    l = MilestoneLedger.from_default_catalogue()
    ids = l.ids()
    assert "M48-A1" in ids
    assert "M48-A3" in ids
    assert "M48-B2" in ids
    assert "M48-I1" in ids
    assert all(isinstance(m, Milestone) for m in l.all().values())


def test_negative_complete_from_not_started():
    l = MilestoneLedger.from_default_catalogue()
    with pytest.raises(CompletionGuardError):
        l.mark_complete("M48-A1", acceptance=["any"])


def test_negative_complete_without_evidence():
    l = MilestoneLedger.from_default_catalogue()
    l.transition("M48-A1", MilestoneStatus.IN_PROGRESS)
    l.transition("M48-A1", MilestoneStatus.IMPLEMENTED)
    l.set_acceptance_criteria("M48-A1", ["a"])
    with pytest.raises(CompletionGuardError, match="without objective evidence"):
        l.mark_complete("M48-A1", acceptance=["a"])


def test_negative_complete_with_nonzero_exit():
    l = MilestoneLedger.from_default_catalogue()
    l.transition("M48-A1", MilestoneStatus.IN_PROGRESS)
    l.record_command(
        "M48-A1",
        command="false",
        exit_code=1,
        expected_result="0",
        observed_result="1",
    )
    l.add_evidence("M48-A1", artifact_path=str(SAMPLE_ARTIFACT), evidence_id="ev1")
    l.transition("M48-A1", MilestoneStatus.IMPLEMENTED)
    with pytest.raises(CompletionGuardError, match="non-zero exit"):
        l.mark_complete("M48-A1", acceptance=["a"])


def test_negative_complete_with_tampered_sha(tmp_path: Path):
    art = _make_artifact(tmp_path)
    l = MilestoneLedger.from_default_catalogue()
    l.transition("M48-A1", MilestoneStatus.IN_PROGRESS)
    l.record_command(
        "M48-A1", command="true", exit_code=0, expected_result="0", observed_result="0"
    )
    l.add_evidence("M48-A1", artifact_path=str(art), evidence_id="ev1")
    # Tamper the recorded sha after the fact
    m = l.get("M48-A1")
    l._set(
        Milestone._rebuild(
            m,
            evidence=(
                *m.evidence[:-1],
                Evidence(
                    artifact_path=str(art),
                    artifact_sha256="0" * 64,
                    evidence_id="ev1",
                    description="tampered",
                ),
            ),
        )
    )
    l.transition("M48-A1", MilestoneStatus.IMPLEMENTED)
    with pytest.raises(CompletionGuardError, match="sha mismatch"):
        l.mark_complete("M48-A1", acceptance=["a"])


def test_positive_full_lifecycle(tmp_path: Path):
    art = _make_artifact(tmp_path)
    l = MilestoneLedger.from_default_catalogue()
    l.transition("M48-A1", MilestoneStatus.IN_PROGRESS, scope="foundation trust")
    l.add_files_changed("M48-A1", ["runtime/foundation/verification/milestone_state.py"])
    l.record_command(
        "M48-A1", command="true", exit_code=0, expected_result="0", observed_result="0"
    )
    l.add_evidence(
        "M48-A1", artifact_path=str(art), evidence_id="m48-a1-artifact", description="x"
    )
    l.transition("M48-A1", MilestoneStatus.IMPLEMENTED)
    l.set_acceptance_criteria("M48-A1", ["guarded", "sha-verified"])
    m = l.mark_complete("M48-A1", acceptance=["guarded", "sha-verified"])
    assert m.status == MilestoneStatus.COMPLETE
    assert m.final_disposition == "COMPLETE"
    assert m.evidence[0].artifact_sha256 == compute_sha256(art)
    assert m.completed_at
    assert m.review_gate == "passed"


def test_snapshot_roundtrip(tmp_path: Path):
    art = _make_artifact(tmp_path)
    l = MilestoneLedger.from_default_catalogue()
    l.transition("M48-A1", MilestoneStatus.IN_PROGRESS)
    l.record_command(
        "M48-A1", command="true", exit_code=0, expected_result="0", observed_result="0"
    )
    l.add_evidence("M48-A1", artifact_path=str(art), evidence_id="ev1")
    l.transition("M48-A1", MilestoneStatus.IMPLEMENTED)
    l.mark_complete("M48-A1", acceptance=["ok"])
    snap = tmp_path / "snap.json"
    l.save(snap)
    assert snap.exists()
    l2 = MilestoneLedger.from_snapshot(snap)
    assert l2.get("M48-A1").status == MilestoneStatus.COMPLETE
    assert l2.get("M48-A1").evidence[0].artifact_sha256 == compute_sha256(art)


def test_reconciliation_reports_missing_in_progress(tmp_path):
    progress = tmp_path / "progress.md"
    progress.write_text("# M9-C48\n\n## M48-A1\n\n")
    l = MilestoneLedger.from_default_catalogue()
    l.transition("M48-A1", MilestoneStatus.IN_PROGRESS)
    l.add_evidence("M48-A1", artifact_path=str(SAMPLE_ARTIFACT), evidence_id="ev")
    l.record_command(
        "M48-A1", command="true", exit_code=0, expected_result="0", observed_result="0"
    )
    l.transition("M48-A1", MilestoneStatus.IMPLEMENTED)
    l.mark_complete("M48-A1", acceptance=["ok"])
    rep = l.reconciliation_report(progress)
    assert "M48-A1" not in rep["missing_in_progress"]
    assert rep["milestones"]["M48-A1"]["status"] == "COMPLETE"


def test_terminal_status_set():
    from runtime.foundation.verification.milestone_state import TERMINAL_STATUSES
    assert MilestoneStatus.COMPLETE in TERMINAL_STATUSES
    assert MilestoneStatus.FAILED in TERMINAL_STATUSES
    assert MilestoneStatus.SUPERSEDED in TERMINAL_STATUSES
    assert MilestoneStatus.IN_PROGRESS not in TERMINAL_STATUSES


def test_status_enum_values():
    for v in [
        "NOT_STARTED",
        "IN_PROGRESS",
        "BLOCKED",
        "IMPLEMENTED",
        "VALIDATING",
        "COMPLETE",
        "FAILED",
        "SUPERSEDED",
    ]:
        assert MilestoneStatus(v).value == v
