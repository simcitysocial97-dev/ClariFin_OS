"""M10-R2 closeout — live execution observability and the three-state leg contract.

Two things are pinned here, and both exist because a CI failure was undiagnosable.

**Observability.** M10-R2-C3 moved task output out of stdout and into per-task evidence
files. That was correct, but it silently removed the only *live* signal: a reconcile leg
printed one line and then went silent, and four of seven legs died leaving 0 bytes with no
indication of which canonical task was executing. So the contract is that
``run_streaming_command`` can emit lifecycle lines (start / heartbeat / terminal) to stderr
while streaming content to files — and that omitting it is byte-identical to before.

**Three-state leg results.** The aggregate must distinguish:

  * no file       — the leg never reached a terminal result (infrastructure)
  * status=failed — the leg ran and failed a verification obligation
  * status=passed — the leg completed

Collapsing the first two into "unreadable" is what made the earlier failure unreadable, and
defaulting a missing ``status`` to a failure is coercion of an uninterpretable document into
a verdict. Both are regressions guarded here.
"""

from __future__ import annotations

import json
from pathlib import Path

from runtime.foundation.verification.parallel_executor import (
    ProgressContext,
    classify_termination,
    run_streaming_command,
)
from runtime.foundation.verification.runtime_shards import (
    LEG_RESULT_SCHEMAS,
    read_shard_results,
)


def _ctx(tmp_path: Path, label: str = "leg", kind: str = "shard") -> ProgressContext:
    return ProgressContext(
        label=label,
        kind=kind,
        log_dir=tmp_path,
        timeout_seconds=30,
    )


# ---------------------------------------------------------------------------
# Default-off is byte-identical
# ---------------------------------------------------------------------------


def test_no_progress_is_byte_identical_to_before(tmp_path, capsys):
    """The pre-closeout behaviour: files written, NOTHING on the console.

    This is what keeps the 2717 existing tests and local runs unaffected.
    """
    out, err = tmp_path / "o.log", tmp_path / "e.log"
    result = run_streaming_command(
        "echo hello", stdout_path=out, stderr_path=err, timeout_seconds=30
    )
    assert result.exit_code == 0
    assert out.read_text().strip() == "hello"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_progress_goes_to_stderr_never_stdout(tmp_path, capsys):
    """stdout is reserved for machine-readable documents. A `[check] boundary=` banner on
    stdout is exactly what corrupted a shard report earlier."""
    run_streaming_command(
        "echo hi",
        stdout_path=tmp_path / "o.log",
        stderr_path=tmp_path / "e.log",
        timeout_seconds=30,
        progress=_ctx(tmp_path),
        heartbeat_seconds=0,
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[leg] start" in captured.err
    assert "[leg] exit=0" in captured.err


# ---------------------------------------------------------------------------
# Lifecycle lines
# ---------------------------------------------------------------------------


def test_fast_command_emits_two_lines_and_no_heartbeat(tmp_path, capsys):
    """A command shorter than one interval never reaches a tick, so a fast obligation
    costs only its start/terminal pair. No extra suppression rule is needed."""
    run_streaming_command(
        "true",
        stdout_path=tmp_path / "o.log",
        stderr_path=tmp_path / "e.log",
        timeout_seconds=30,
        progress=_ctx(tmp_path),
        heartbeat_seconds=5,
    )
    err = capsys.readouterr().err
    assert "running elapsed=" not in err
    assert err.count("\n") == 2


def test_long_command_emits_monotonic_heartbeats(tmp_path, capsys):
    run_streaming_command(
        "sleep 3",
        stdout_path=tmp_path / "o.log",
        stderr_path=tmp_path / "e.log",
        timeout_seconds=30,
        progress=_ctx(tmp_path),
        heartbeat_seconds=1,
    )
    err = capsys.readouterr().err
    beats = [
        int(line.split("elapsed=")[1].rstrip("s"))
        for line in err.splitlines()
        if "running elapsed=" in line
    ]
    assert len(beats) >= 2, err
    assert beats == sorted(beats), "heartbeat elapsed must be monotonic"


def test_terminal_line_reports_the_termination_kind(tmp_path, capsys):
    """`exit=1` alone is not a diagnosis. The line must distinguish a timeout from a
    signal death from an ordinary failure without opening an artifact."""
    run_streaming_command(
        "exit 1",
        stdout_path=tmp_path / "o.log",
        stderr_path=tmp_path / "e.log",
        timeout_seconds=30,
        progress=_ctx(tmp_path),
        heartbeat_seconds=0,
    )
    err = capsys.readouterr().err
    assert "term=EXIT_NONZERO" in err


def test_timeout_terminal_line_says_so(tmp_path, capsys):
    run_streaming_command(
        "sleep 20",
        stdout_path=tmp_path / "o.log",
        stderr_path=tmp_path / "e.log",
        timeout_seconds=1,
        progress=_ctx(tmp_path),
        heartbeat_seconds=0,
    )
    err = capsys.readouterr().err
    assert "timeout=true" in err
    assert "term=WRAPPER_TIMEOUT" in err


def test_terminal_line_agrees_with_classify_termination(tmp_path, capsys):
    """The log and the record must not be able to disagree about how a command ended."""
    result = run_streaming_command(
        "exit 3",
        stdout_path=tmp_path / "o.log",
        stderr_path=tmp_path / "e.log",
        timeout_seconds=30,
        progress=_ctx(tmp_path),
        heartbeat_seconds=0,
    )
    err = capsys.readouterr().err
    expected = classify_termination(
        result.exit_code, result.timed_out, result.infra_error
    )["kind"]
    assert f"term={expected}" in err


def test_heartbeat_can_be_disabled_by_environment(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("VERIFY_HEARTBEAT_SECONDS", "0")
    run_streaming_command(
        "sleep 2",
        stdout_path=tmp_path / "o.log",
        stderr_path=tmp_path / "e.log",
        timeout_seconds=30,
        progress=_ctx(tmp_path),
    )
    assert "running elapsed=" not in capsys.readouterr().err


def test_progress_can_be_silenced_entirely(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("VERIFY_PROGRESS", "0")
    run_streaming_command(
        "sleep 1",
        stdout_path=tmp_path / "o.log",
        stderr_path=tmp_path / "e.log",
        timeout_seconds=30,
        progress=_ctx(tmp_path),
        heartbeat_seconds=1,
    )
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_progress_never_raises_into_the_execution(tmp_path):
    """Instrumentation must not be able to fail a verification run."""
    ctx = ProgressContext(label="x", kind="shard", log_dir=tmp_path, timeout_seconds=5)
    object.__setattr__(ctx, "label", object())  # a label that cannot be formatted
    result = run_streaming_command(
        "echo still-runs",
        stdout_path=tmp_path / "o.log",
        stderr_path=tmp_path / "e.log",
        timeout_seconds=30,
        progress=ctx,
        heartbeat_seconds=0,
    )
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Orchestrator label composition
# ---------------------------------------------------------------------------


def test_progress_prefix_composes_into_per_task_labels(tmp_path):
    """One orchestrator-side change is what gives `verify check` and reconcile shards a
    per-task label carrying BOTH the leg and the canonical task id."""
    from runtime.foundation.verification.execution_orchestrator import (
        ExecutionOrchestrator,
    )

    assert ExecutionOrchestrator()._progress_prefix is None
    assert (
        ExecutionOrchestrator(progress_prefix="reconcile-shard 1/7")._progress_prefix
        == "reconcile-shard 1/7"
    )


# ---------------------------------------------------------------------------
# Three-state leg results
# ---------------------------------------------------------------------------


def _leg(tmp_path: Path, name: str, **over) -> None:
    payload = {
        "schema": "m10r2-leg-result/v1",
        "shard_id": name,
        "status": "passed",
        "exit_code": 0,
        "duration_seconds": 1.0,
        **over,
    }
    (tmp_path / f"shard-{name}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_absent_and_malformed_are_distinct_states(tmp_path):
    """Different owners: absent is infrastructure, malformed is a producer bug."""
    _leg(tmp_path, "a")
    (tmp_path / "shard-b.json").write_text("{ truncated", encoding="utf-8")
    results, absent, malformed, rejected = read_shard_results(tmp_path)
    assert [r.shard_id for r in results] == ["a"]
    assert absent == []
    assert len(malformed) == 1 and "shard-b.json" in malformed[0]
    assert rejected == []


def test_no_files_at_all_is_reported_as_transport_fault(tmp_path):
    """Not 'every leg absent' — a caller must be able to say transport failed."""
    results, absent, malformed, rejected = read_shard_results(tmp_path)
    assert results == []
    assert absent and "no shard-*.json files found" in absent[0]


def test_unknown_schema_is_rejected_not_coerced(tmp_path):
    """A document this build cannot interpret must never read as a passing leg."""
    _leg(tmp_path, "a", schema="some-future-schema/v9")
    results, absent, malformed, rejected = read_shard_results(tmp_path)
    assert results == []
    assert len(rejected) == 1 and "unsupported schema" in rejected[0]
    # Crucially it is NOT classified as malformed-or-ok: it is its own state.
    assert malformed == []


def test_known_schemas_are_accepted():
    assert "m10r2-leg-result/v1" in LEG_RESULT_SCHEMAS


def test_missing_required_key_is_malformed_not_silently_defaulted(tmp_path):
    """Previously `payload.get("status")`-style defaults could turn an uninterpretable
    document into a verdict. A missing key must be malformed."""
    (tmp_path / "shard-x.json").write_text(
        json.dumps({"schema": "m10r2-leg-result/v1"}), encoding="utf-8"
    )
    results, absent, malformed, rejected = read_shard_results(tmp_path)
    assert results == []
    assert len(malformed) == 1


def test_a_failing_leg_is_read_as_failed_not_absent(tmp_path):
    """The regression guard for the whole contract: a shard that RAN and FAILED must
    never be mistaken for a shard that never ran."""
    _leg(tmp_path, "0", status="failed", exit_code=1)
    results, absent, malformed, rejected = read_shard_results(tmp_path)
    assert absent == [] and malformed == [] and rejected == []
    assert len(results) == 1
    assert results[0].status == "failed"
    assert results[0].ok is False


# ---------------------------------------------------------------------------
# run --result-out writes a terminal document
# ---------------------------------------------------------------------------


def _iso_plan(path: Path) -> dict:
    from runtime.foundation.verification.execution_orchestrator import (
        ExecutionPlan,
        ExecutionTaskSpec,
        RepositoryFingerprint,
    )

    plan = ExecutionPlan(
        plan_id="execplan-isotest",
        source_plan_id="cp-isotest",
        repository_fingerprint=RepositoryFingerprint.capture(),
        changed_files=[],
        affected_capabilities=["iso"],
        affected_components=[],
        invalidated_evidence=[],
        reusable_evidence=[],
        tasks=[
            ExecutionTaskSpec(
                task_id=f"exec-{i:04d}",
                source_task_id="iso",
                primary_capability="iso",
                capabilities=("iso",),
                verification_kind="unit",
                command=cmd,
                profile="unit",
                scope="unit",
                is_mandatory=True,
                is_escalation=False,
                reason="iso fixture",
                origin="control_plane",
                prerequisites=(".venv",),
                expected_evidence=("unit_pass",),
                timeout_seconds=60,
            )
            for i, cmd in enumerate(["true", "true", "true"], start=1)
        ],
        escalation_conditions=[],
        measurement_requirements=[],
        certification_requirements=[],
        rationale="iso fixture",
        plan_fingerprint="isotest",
        generated_at="",
        revalidation_sources=[],
        reusable_measurements=[],
    )
    path.write_text(json.dumps(plan.to_dict()), encoding="utf-8")
    return plan.to_dict()


def test_result_out_is_written_on_success(tmp_path):
    from runtime.foundation.verification.control_plane_facade import ControlPlane

    plan_file = tmp_path / "plan.json"
    _iso_plan(plan_file)
    out = tmp_path / "leg.json"
    ControlPlane().run(plan_path=str(plan_file), shard=(0, 3), result_out=str(out))

    payload = json.loads(out.read_text())
    assert payload["schema"] == "m10r2-leg-result/v1"
    assert payload["outcome"] == "terminal"
    assert payload["status"] == "passed"
    assert payload["leg_id"].startswith("reconcile-shard 1/3")
    assert payload["tasks"]


def test_result_out_is_written_on_task_failure(tmp_path):
    """THE regression this whole contract exists for. Previously a *normal* failed
    execution left a 0-byte stdout redirect and was indistinguishable from a kill."""
    from runtime.foundation.verification.control_plane_facade import ControlPlane

    plan_file = tmp_path / "plan.json"
    payload = _iso_plan(plan_file)
    # Fail the task that shard 0 actually owns. With three equal-weight tasks and three
    # shards, LPT places exec-0001 in shard 0 — failing exec-0002 instead would leave
    # shard 0 legitimately green, which is itself the disjointness guarantee working.
    payload["tasks"][0]["command"] = "exit 1"
    plan_file.write_text(json.dumps(payload), encoding="utf-8")

    out = tmp_path / "leg.json"
    ControlPlane().run(plan_path=str(plan_file), shard=(0, 3), result_out=str(out))

    assert out.exists(), "a failing task must still produce a terminal result"
    result = json.loads(out.read_text())
    assert result["outcome"] == "terminal"
    assert result["status"] == "failed"
    assert result["exit_code"] != 0
    # And it must READ as failed, not absent.
    _, absent, malformed, rejected = read_shard_results(_dir_with(out, "shard-0.json"))
    assert absent == [] and malformed == [] and rejected == []


def _dir_with(src: Path, name: str) -> Path:
    d = src.parent / "legs"
    d.mkdir(exist_ok=True)
    (d / name).write_text(src.read_text(), encoding="utf-8")
    return d


def test_result_out_absent_means_no_documented_outcome(tmp_path):
    """Calling `run` without --result-out must not invent a file: absence is the
    signal for 'no terminal result' and it must mean what it says."""
    from runtime.foundation.verification.control_plane_facade import ControlPlane

    plan_file = tmp_path / "plan.json"
    _iso_plan(plan_file)
    ControlPlane().run(plan_path=str(plan_file), shard=(0, 3))
    assert list(tmp_path.glob("*.json")) == [plan_file]
