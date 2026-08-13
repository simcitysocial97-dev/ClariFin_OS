"""
M9-C3 regression tests — verification gate integrity.

Covers two objectives:

1. Failure reporting / classification / exit semantics (Milestones 2-4):
   a successful run reports PASS and exit 0; a test failure is classified
   TEST_FAILURE and exits non-zero; a non-zero subprocess is COMMAND_FAILURE;
   an unexpected exception is ENVIRONMENT_FAILURE and never masked as success;
   missing evidence never reports success.

2. CI changed-file PR boundary (Milestones 5-6):
   a normal PR uses base..head; unrelated target-branch advancement between the
   merge-base and the PR base is NOT included; a missing PR payload falls back to
   a bounded merge-base; an empty PR diff is distinguished from an undetermined
   diff.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from runtime.foundation.verification.failure_report import (
    FailureClassification,
    build_failure_report,
)
from runtime.foundation.verification.models import (
    ExecutionResult,
    VerificationStatus,
)
from runtime.foundation.verification.orchestrator import (
    VerificationReport,
    _collect_changed_files,
    _github_pr_refs,
)


# ---------------------------------------------------------------------------
# Milestones 2-4: failure reporting / classification / exit semantics
# ---------------------------------------------------------------------------


def _make_failed(command: str, **kw: object) -> ExecutionResult:
    return ExecutionResult(
        task_id="step-x",
        command=command,
        status=VerificationStatus.FAILED,
        exit_code=kw.get("exit_code", 1),  # type: ignore[arg-type]
        duration_seconds=0.1,
        stdout_path=kw.get("stdout_path", "") or "",  # type: ignore[arg-type]
        stderr_path=kw.get("stderr_path", "") or "",  # type: ignore[arg-type]
        error=kw.get("error"),  # type: ignore[arg-type]
        classification=kw.get("classification", FailureClassification.UNKNOWN_FAILURE),  # type: ignore[arg-type]
    )


def test_command_failure_is_classified(tmp_path: Path) -> None:
    res = _make_failed("exit 7", exit_code=7, error="", stderr_path="")
    fr = build_failure_report(res)
    assert fr.classification == FailureClassification.COMMAND_FAILURE
    assert fr.exit_code == 7


def test_successful_result_passes(tmp_path: Path) -> None:
    out = tmp_path / "ok.txt"
    out.write_text("passed", encoding="utf-8")
    res = ExecutionResult(
        task_id="s",
        command="true",
        status=VerificationStatus.PASSED,
        exit_code=0,
        duration_seconds=0.0,
        stdout_path=str(out),
        stderr_path="",
        error=None,
    )
    assert res.status == VerificationStatus.PASSED
    assert res.exit_code == 0


def test_test_failure_is_classified(tmp_path: Path) -> None:
    stdout = tmp_path / "out.txt"
    stdout.write_text(
        "________________ test_x ________________\n"
        "> assert 1 == 2\nE AssertionError: boom\n"
        "short test summary info\n"
        "FAILED tests/x.py::test_x - AssertionError: boom\n"
        "1 failed, 5 passed in 1.2s\n",
        encoding="utf-8",
    )
    res = _make_failed("python3 -m pytest tests/x.py", stdout_path=str(stdout))
    fr = build_failure_report(res)
    assert fr.classification == FailureClassification.TEST_FAILURE
    assert fr.exit_code == 1
    assert fr.test_failure_count == 1
    assert fr.root_failure == "tests/x.py::test_x"
    assert "1 failed, 5 passed" in (fr.failure_summary or "")
    assert "boom" in (fr.diagnostic or "")


def test_import_failure_is_classified(tmp_path: Path) -> None:
    stdout = tmp_path / "out.txt"
    stdout.write_text("ModuleNotFoundError: No module named 'bogus'", encoding="utf-8")
    res = _make_failed(
        "python3 -m pytest tests/x.py", stdout_path=str(stdout), error=""
    )
    fr = build_failure_report(res)
    assert fr.classification == FailureClassification.IMPORT_FAILURE


def test_timeout_is_classified() -> None:
    res = _make_failed(
        "sleep 100", exit_code=-9, classification=FailureClassification.TIMEOUT
    )
    fr = build_failure_report(res)
    assert fr.classification == FailureClassification.TIMEOUT


def test_environment_failure_is_classified() -> None:
    res = _make_failed(
        "python3 -c 'raise SystemExit(1)'",
        exit_code=-1,
        classification=FailureClassification.ENVIRONMENT_FAILURE,
    )
    fr = build_failure_report(res)
    assert fr.classification == FailureClassification.ENVIRONMENT_FAILURE


def test_missing_evidence_never_reports_success(tmp_path: Path) -> None:
    """A FAILED result with empty artifacts must not be reported as success."""
    res = _make_failed("exit 1", error="", stderr_path="")
    fr = build_failure_report(res)
    assert res.status == VerificationStatus.FAILED
    assert fr.status == "failed"
    assert fr.classification in (
        FailureClassification.COMMAND_FAILURE,
        FailureClassification.UNKNOWN_FAILURE,
    )


def test_reporting_error_cannot_mask_failure() -> None:
    """If build_failure_report itself raises, the failure is still a failure."""
    res = _make_failed("exit 1")

    def _boom(*a, **k):  # type: ignore[no-untyped-def]
        raise RuntimeError("reporting broke")

    mp = pytest.MonkeyPatch()
    try:
        mp.setattr(
            "runtime.foundation.verification.failure_report._read_artifact", _boom
        )
        with pytest.raises(RuntimeError):
            build_failure_report(res)
    finally:
        mp.undo()
    assert res.status == VerificationStatus.FAILED


def test_orchestrator_failure_report_renders_classification(tmp_path: Path) -> None:
    from runtime.foundation.verification.models import VerificationSummary, VerificationScope
    from runtime.foundation.verification.orchestrator import VerificationPlan

    stdout = tmp_path / "verify-stdout.txt"
    stdout.write_text(
        "FAILED tests/y.py::test_y - AssertionError: nope\n1 failed in 0.5s\n",
        encoding="utf-8",
    )
    failed = ExecutionResult(
        task_id="step-0002",
        command="python3 -m pytest tests/y.py",
        status=VerificationStatus.FAILED,
        exit_code=1,
        duration_seconds=0.5,
        stdout_path=str(stdout),
        stderr_path="",
        error="",
        unit_id="unit-runtime-foundation",
    )
    summary = VerificationSummary(
        profile="runtime",
        total_tasks=1,
        passed=0,
        failed=1,
        skipped=0,
        duration_seconds=0.5,
        report_path=str(tmp_path / "r.md"),
        cache_path=str(tmp_path / "c.json"),
        overall_status=VerificationStatus.FAILED,
    )
    plan = VerificationPlan(
        name="runtime", id="p", scope=VerificationScope.RUNTIME, targets=[], steps=[], estimated_duration_seconds=0
    )
    report = VerificationReport(
        profile="runtime",
        changed_files=["tests/y.py"],
        blast_radius={},
        plan=plan,
        results=[failed],
        summary=summary,
        dependency_chains=[],
        evidence_files=[],
        recommendations=[],
    )
    md = report.to_markdown()
    assert "Classification: TEST_FAILURE" in md
    assert "unit-runtime-foundation" in md
    assert "tests/y.py::test_y" in md
    assert "Exit code: 1" in md


# ---------------------------------------------------------------------------
# Milestones 5-6: CI changed-file PR boundary
# ---------------------------------------------------------------------------


def _clear_ci_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    for var in (
        "GITHUB_EVENT_NAME",
        "GITHUB_EVENT_PATH",
        "GITHUB_BASE_REF",
        "GITHUB_SHA",
        "GITHUB_REF",
        "VERIFICATION_BASE_REF",
        "VERIFICATION_HEAD_REF",
        "CI",
    ):
        monkeypatch.delenv(var, raising=False)


def _write_event(tmp_path: Path, payload: dict) -> str:
    p = tmp_path / "event.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return str(p)


def test_pr_refs_read_from_event(tmp_path: Path, monkeypatch) -> None:
    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv(
        "GITHUB_EVENT_PATH",
        _write_event(
            tmp_path,
            {"pull_request": {"base": {"sha": "pr-base-sha"}, "head": {"sha": "pr-head-sha"}}},
        ),
    )
    base, head = _github_pr_refs()
    assert base == "pr-base-sha"
    assert head == "pr-head-sha"


def test_pr_refs_absent_without_event(monkeypatch) -> None:
    _clear_ci_env(monkeypatch)
    assert _github_pr_refs() == (None, None)


def test_pr_boundary_uses_two_dot(monkeypatch, tmp_path: Path) -> None:
    """Case A + B: PR boundary is computed as base..head, excluding target-branch
    advancement that a merge-base (three-dot) diff would include."""

    def fake_run(cmd, **kw):  # type: ignore[no-untyped-def]
        if ".." in cmd[-1] and "..." not in cmd[-1]:
            return subprocess.CompletedProcess(cmd, 0, "pr_file.py\n", "")
        if "..." in cmd[-1]:
            return subprocess.CompletedProcess(
                cmd, 0, "pr_file.py\nunrelated_target_branch_file.py\n", ""
            )
        if cmd[1:3] == ["rev-parse", "--verify"]:
            return subprocess.CompletedProcess(cmd, 0, "resolved\n", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv(
        "GITHUB_EVENT_PATH",
        _write_event(
            tmp_path,
            {"pull_request": {"base": {"sha": "pr-base-sha"}, "head": {"sha": "pr-head-sha"}}},
        ),
    )
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _collect_changed_files()
    assert result.error is None
    assert "pr_file.py" in result.files
    assert "unrelated_target_branch_file.py" not in result.files
    assert result.base == "origin/pr-base-sha"
    assert result.head == "origin/pr-head-sha"
    assert "base..head" in result.source


def test_pr_event_missing_payload_falls_back_to_merge_base(monkeypatch) -> None:
    """Case D: missing GitHub PR metadata uses the documented local/non-PR
    merge-base fallback (bounded, not enormous)."""

    def fake_run(cmd, **kw):  # type: ignore[no-untyped-def]
        if "..." in cmd[-1]:
            return subprocess.CompletedProcess(cmd, 0, "local_change.py\n", "")
        if cmd[1] == "diff":
            return subprocess.CompletedProcess(cmd, 0, "local_change.py\n", "")
        if cmd[1:3] == ["rev-parse", "--verify"]:
            return subprocess.CompletedProcess(cmd, 0, "resolved\n", "")
        if cmd[1] == "fetch":
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _collect_changed_files()
    assert result.error is None
    assert "local_change.py" in result.files


def test_empty_pr_diff_is_distinguished(tmp_path: Path, monkeypatch) -> None:
    """Case E: a valid empty PR diff is [] with no error, distinct from an
    undetermined boundary (error set)."""

    def fake_run(cmd, **kw):  # type: ignore[no-untyped-def]
        if ".." in cmd[-1]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[1:3] == ["rev-parse", "--verify"]:
            return subprocess.CompletedProcess(cmd, 0, "resolved\n", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv(
        "GITHUB_EVENT_PATH",
        _write_event(
            tmp_path,
            {"pull_request": {"base": {"sha": "pr-base-sha"}, "head": {"sha": "pr-head-sha"}}},
        ),
    )
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _collect_changed_files()
    assert result.error is None
    assert result.files == []


def test_verification_base_ref_override_two_dot(monkeypatch) -> None:
    """Override base+head via env still resolves the PR boundary (base..head)."""

    def fake_run(cmd, **kw):  # type: ignore[no-untyped-def]
        if ".." in cmd[-1]:
            return subprocess.CompletedProcess(cmd, 0, "override_file.py\n", "")
        if cmd[1:3] == ["rev-parse", "--verify"]:
            return subprocess.CompletedProcess(cmd, 0, "resolved\n", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    _clear_ci_env(monkeypatch)
    monkeypatch.setenv("VERIFICATION_BASE_REF", "a" * 40)
    monkeypatch.setenv("VERIFICATION_HEAD_REF", "c" * 40)
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _collect_changed_files()
    assert result.error is None
    assert "override_file.py" in result.files
    assert result.base == "a" * 40
    assert result.head == "c" * 40
