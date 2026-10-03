# runtime/foundation/verification/coverage_measurement.py
#
# M9-C47 — canonical COVERAGE measurement command.
#
# Produces an authoritative, durable, machine-readable `MeasurementTruthRecord`
# with `measurement_kind == "coverage"`. Coverage and mutation are explicitly
# SEPARATE measurements (per C47 governing constraint #2): this command only
# measures coverage; it never conflates coverage with mutation evidence.
#
# Reuses native environment fingerprints (env.py) and the C47 measurement-truth
# contract. It does not create a parallel evidence system.

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from runtime.foundation.verification.env import (
    REPO_ROOT,
    VENV_BIN,
    resolve_environment,
)
from runtime.foundation.verification.measurement_truth import (
    CoverageResult,
    EvidenceClassification,
    FailureClassification,
    MeasurementCompletionStatus,
    MeasurementKind,
    MeasurementTruthRecord,
    assert_authoritative_classification,
    classify_completion,
    set_evidence_fingerprint,
)

BACKEND_DIR = REPO_ROOT / "backend"
COVERAGE_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c47" / "coverage"


def _git_sha() -> str:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=10,
            )
            .stdout.strip()
            .splitlines()[0]
        )
    except Exception:
        return "unknown"


def _git_tree() -> str:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "HEAD^{tree}"],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=10,
            )
            .stdout.strip()
            .splitlines()[0]
        )
    except Exception:
        return "unknown"


def _resolve_scope(scope: str) -> str:
    """Return a pytest path usable from the directory pytest actually runs in.

    The command is documented as taking a scope relative to ``backend/``, and
    pytest runs there. But the verification planner builds its coverage tasks
    from engine module paths, which are repository-root-relative
    (``backend/src/engines/account_engine``). Handed to pytest unchanged that
    resolves to ``backend/backend/src/...`` and the run dies with

        ERROR: file or directory not found: backend/src/engines/account_engine

    — reported as an infrastructure failure of the coverage task rather than as
    a bad argument. Both spellings are accepted here so no caller has to know
    which directory the command happens to start in.
    """
    if scope in {"backend", ".", "full", ""}:
        return "."
    normalized = scope.replace("\\", "/").lstrip("./")
    if normalized.startswith("backend/"):
        normalized = normalized[len("backend/") :]
    return normalized or "."


def _coverage_run(
    *,
    scope: str,
    max_runtime: int = 1800,
) -> tuple[CoverageResult, int, bool, str]:
    """Execute a bounded coverage measurement over the requested scope.

    Returns (coverage_result, rc, timed_out, stderr_tail). Uses .venv coverage.
    """
    coverage_bin = (
        VENV_BIN / "coverage" if (VENV_BIN / "coverage").is_file() else "coverage"
    )
    # M11 (Task 2 — critical path). The data file used to be a FIXED name inside
    # the C47 coverage directory, and the comment above this line claimed it was
    # "isolated per-run". It was not: it was isolated per-DIRECTORY. Two
    # concurrent `_coverage_run` calls — which the runtime suite creates,
    # because several tests measure coverage independently — both ran
    #     coverage run --data-file runtime/generated/m9-c47/coverage/.coverage
    # against the SAME SQLite file, and both then ran
    #     coverage json -o runtime/generated/m9-c47/coverage/raw-coverage.json
    # into the SAME JSON path. Two real failure modes follow, and both are
    # silent:
    #   * `coverage run` appends to the data file. Interleaved writers corrupt
    #     the SQLite database, and `coverage json` then reports a database
    #     error or totals belonging to the other process.
    #   * `raw-coverage.json` is written non-atomically, so a reader can observe
    #     a truncated file, and whichever process finishes last silently
    #     overwrites the other's report.
    # Measured cost of the contention it caused: 73.08 s of the serial group.
    #
    # The data file and the intermediate JSON are now scoped by PID, so each
    # process owns its files for the whole measurement. `raw-coverage.json` is
    # still published at the fixed, documented path via `os.replace`, which is
    # atomic on the same filesystem — so `tools/development/check_coverage.py`
    # and `docs/ENGINEERING_ARTIFACTS.md` keep working, a partially written
    # report is never observable, and last-writer-wins applies to a
    # convenience copy instead of to the measurement itself.
    #
    # `measurement-truth-coverage.json` (written further down) is a separate,
    # fixed, single-writer artifact and is deliberately left alone.
    COVERAGE_DIR.mkdir(parents=True, exist_ok=True)
    data_file = str(COVERAGE_DIR / f".coverage.{os.getpid()}")
    published_json = COVERAGE_DIR / "raw-coverage.json"
    json_out = COVERAGE_DIR / f"raw-coverage.{os.getpid()}.json"
    pytest_scope = _resolve_scope(scope)
    cmd = [
        str(coverage_bin),
        "run",
        "--data-file",
        data_file,
        "-m",
        "pytest",
        pytest_scope,
        "-q",
    ]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
            timeout=max_runtime,
        )
    except subprocess.TimeoutExpired:
        return CoverageResult(), 124, True, "coverage run exceeded max_runtime"

    # Report JSON — use `coverage json` subcommand (not `report --format json`).
    # cwd MUST be BACKEND_DIR so coverage resolves source paths correctly.
    cov_result = CoverageResult()
    rc = res.returncode
    tail = (res.stderr or "")[-2000:]
    json_out = COVERAGE_DIR / "raw-coverage.json"
    try:
        report = subprocess.run(
            [
                str(coverage_bin),
                "json",
                "--data-file",
                data_file,
                "-o",
                str(json_out),
            ],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
            timeout=120,
        )
        if report.returncode == 0 and json_out.exists():
            data = json.loads(json_out.read_text())
            totals = data.get("totals", {})
            cov_result = CoverageResult(
                lines_total=int(totals.get("num_statements", 0)),
                lines_covered=int(totals.get("covered_lines", 0)),
                line_percent=(
                    float(totals.get("percent_covered", 0.0))
                    if totals.get("percent_covered") is not None
                    else None
                ),
                branches_total=int(totals.get("num_branches", 0)),
                branches_covered=int(totals.get("covered_branches", 0)),
                branch_percent=(
                    float(totals.get("percent_covered_branches", 0.0))
                    if totals.get("percent_covered_branches") is not None
                    else None
                ),
            )
        elif json_out.exists():
            # json subcommand wrote output despite non-zero rc (e.g. fail-under)
            data = json.loads(json_out.read_text())
            totals = data.get("totals", {})
            cov_result = CoverageResult(
                lines_total=int(totals.get("num_statements", 0)),
                lines_covered=int(totals.get("covered_lines", 0)),
                line_percent=(
                    float(totals.get("percent_covered", 0.0))
                    if totals.get("percent_covered") is not None
                    else None
                ),
                branches_total=int(totals.get("num_branches", 0)),
                branches_covered=int(totals.get("covered_branches", 0)),
                branch_percent=(
                    float(totals.get("percent_covered_branches", 0.0))
                    if totals.get("percent_covered_branches") is not None
                    else None
                ),
            )
            rc = report.returncode
        else:
            raise RuntimeError(
                f"coverage json exited {report.returncode}: {report.stderr[:200]}"
            )
    except Exception as exc:  # pragma: no cover - defensive
        rc = 2 if rc == 0 else rc
        tail = tail or f"coverage report failed: {exc}"
    finally:
        # Publish the convenience copy atomically, then remove this process's
        # private files. Leaving `raw-coverage.<pid>.json` and
        # `.coverage.<pid>` behind is what put a growing pile of stray coverage
        # databases into the real m9-c47 evidence directory (M10 inventory).
        with contextlib.suppress(OSError):
            if json_out.exists():
                os.replace(str(json_out), str(published_json))
        for leftover in (json_out, Path(data_file)):
            with contextlib.suppress(OSError):
                leftover.unlink()
    return cov_result, rc, False, tail


def measure_coverage_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="verify.py measurement coverage")
    parser.add_argument(
        "scope",
        nargs="?",
        default="tests/unit/engines/credit_card",
        help="pytest path scope to measure (relative to backend/)",
    )
    parser.add_argument(
        "--max-runtime", type=int, default=1800, help="hard subprocess timeout (s)"
    )
    parser.add_argument(
        "--out", default=None, help="explicit measurement-truth output path"
    )
    args = parser.parse_args(argv)

    sha = _git_sha()
    tree = _git_tree()
    env = resolve_environment(config_dir=BACKEND_DIR)
    fp = env.fingerprint if env else {}

    start = time.monotonic()
    cov, rc, timed_out, tail = _coverage_run(
        scope=args.scope, max_runtime=args.max_runtime
    )
    duration = time.monotonic() - start

    failure = FailureClassification.NONE.value
    if timed_out:
        failure = FailureClassification.TIMEOUT.value
    elif rc != 0:
        failure = FailureClassification.INFRASTRUCTURE.value

    out_path = Path(args.out) if args.out else None
    record = MeasurementTruthRecord(
        run_id=f"cov-{uuid.uuid4().hex[:12]}",
        measurement_kind=MeasurementKind.COVERAGE.value,
        repository_sha=sha,
        tree_sha=tree,
        configuration_fingerprint=str(fp.get("config_hash", "")) if fp else "",
        toolchain_fingerprint=str(fp.get("toolchain", "")) if fp else "",
        environment_fingerprint=str(fp) if fp else "",
        command=f"verify.py measurement coverage {args.scope}",
        requested_scope=args.scope,
        actual_scope=args.scope,
        coverage=cov,
        coverage_result_percent=cov.line_percent,
        execution_status="PASS" if rc == 0 else "FAIL",
        completion_status=MeasurementCompletionStatus.UNKNOWN.value,
        failure_classification=failure,
        start_time=datetime.now(UTC).isoformat(),
        duration_seconds=round(duration, 2),
        toolchain_versions={
            "python": getattr(env.python, "version", "unknown") or "unknown",
            "coverage": str(fp.get("coverage", "unknown")) if fp else "unknown",
        },
        artifact_paths=[] if out_path is None else [str(out_path)],
        evidence_classification=EvidenceClassification.AUTHORITATIVE.value,
        mode="coverage",
        error=tail if failure != FailureClassification.NONE.value else None,
        note=(
            "coverage measurement — kept separate from mutation (C47)"
            if rc == 0
            else "coverage measurement failed to complete"
        ),
    )
    record.completion_status = classify_completion(record=record)
    record.evidence_classification = (
        EvidenceClassification.AUTHORITATIVE.value
        if record.completion_status
        == MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
        else EvidenceClassification.DERIVED.value
    )
    set_evidence_fingerprint(record)
    assert_authoritative_classification(record)

    if out_path is None:
        COVERAGE_DIR.mkdir(parents=True, exist_ok=True)
        out_path = COVERAGE_DIR / "measurement-truth-coverage.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record.to_dict(), indent=2) + "\n")

    print(json.dumps(operator_summary(record), indent=2))
    return 0 if rc == 0 else 1


def operator_summary(record: MeasurementTruthRecord) -> dict:
    from runtime.foundation.verification.measurement_truth import operator_report

    return operator_report(record)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(measure_coverage_cli())
