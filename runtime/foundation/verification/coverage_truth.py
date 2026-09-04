# runtime/foundation/verification/coverage_truth.py
#
# M9-C48 F1 — Fresh coverage truth measurement (GAP-016).
#
# Coverage and mutation are SEPARATE dimensions:
#
#   coverage answers:  was the code executed?
#   mutation answers: did tests distinguish incorrect behaviour?
#
# This module produces a fresh coverage measurement with the FULL
# identity spine (repository_sha, tree, configuration, tool versions,
# timestamps, artifact hash). It is the canonical authority for
# "what coverage currently is" and prevents reuse of stale coverage
# evidence.

from __future__ import annotations

import hashlib
import json
import subprocess  # nosec
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CoverageTruth:
    repository_sha: str
    tree_sha: str
    source_scope: str
    test_scope: str
    coverage_tool: str
    coverage_version: str
    pytest_version: str
    python_version: str
    measurement_id: str
    lines_total: int
    lines_covered: int
    line_percent: float | None
    branches_total: int
    branches_covered: int
    branch_percent: float | None
    duration_seconds: int
    exit_code: int
    timestamp: str
    artifact_path: str
    artifact_sha256: str
    configuration: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _git(cwd: str | Path, *args: str) -> str:
    try:
        out = subprocess.run(  # nosec
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip()
    except Exception:
        return ""


def _hash(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _python_version() -> str:
    return (
        subprocess.run(  # nosec
            [".venv/bin/python", "-c", "import sys;print(sys.version.split()[0])"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        or "unknown"
    )


def _tool_version(tool: str) -> str:
    return (
        subprocess.run(  # nosec
            [f".venv/bin/{tool}", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip().split("\n")[0]
        or "unknown"
    )


def measure_coverage(
    *,
    source_scope: str = "backend/src",
    test_scope: str = "tests/unit",
    output_path: str | Path = "runtime/generated/m9-c48/coverage-truth.json",
    max_runtime: int = 600,
) -> CoverageTruth:
    """Run a bounded coverage measurement and persist the truth artifact.

    The scope arguments are pytest paths under backend/. The default
    scope keeps runtime tractable while still exercising the mutation
    engines.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    repo_root = Path.cwd()

    repo_sha = _git(".", "rev-parse", "HEAD")
    tree_sha = _git(".", "rev-parse", "HEAD^{tree}")
    py_ver = _python_version()
    cov_ver = _tool_version("coverage")
    pytest_ver = _tool_version("pytest")

    coverage_data = (repo_root / out.parent / ".coverage-truth").resolve()
    coverage_data.parent.mkdir(parents=True, exist_ok=True)
    coverage_bin = (
        repo_root / ".venv" / "bin" / "coverage"
        if (repo_root / ".venv" / "bin" / "coverage").is_file()
        else "coverage"
    )
    cmd = [
        str(coverage_bin),
        "run",
        "--data-file",
        str(coverage_data),
        "-m",
        "pytest",
        test_scope,
        "-q",
        "--tb=no",
    ]
    start = datetime.now(UTC)
    try:
        proc = subprocess.run(  # nosec
            cmd,
            capture_output=True,
            text=True,
            cwd=str(repo_root / "backend"),
            timeout=max_runtime,
        )
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        rc = 124

    # Parse via the Python coverage API so we work across coverage.py
    # versions (text vs json output formats changed).
    line_total = 0
    line_covered = 0
    line_pct: float | None = None
    br_total = 0
    br_covered = 0
    br_pct: float | None = None
    try:
        import coverage  # type: ignore

        cov = coverage.Coverage(data_file=str(coverage_data))
        cov.load()
        data = cov.get_data()
        for filename in list(data.measured_files()):
            try:
                # cov.analysis() returns (filename, executable, missing, not_found)
                analysis = cov.analysis(filename)
                executable = analysis[1]
                missing = analysis[2]
                line_total += len(executable)
                line_covered += max(0, len(executable) - len(missing))
            except Exception:
                pass
        if line_total > 0:
            line_pct = round(100.0 * line_covered / line_total, 2)
    except Exception:
        pass
    duration = int((datetime.now(UTC) - start).total_seconds())

    measurement_id = "cov-" + hashlib.sha256(
        f"{repo_sha}|{tree_sha}|{test_scope}|{py_ver}|{pytest_ver}|{cov_ver}".encode()
    ).hexdigest()[:12]

    truth = CoverageTruth(
        repository_sha=repo_sha,
        tree_sha=tree_sha,
        source_scope=source_scope,
        test_scope=test_scope,
        coverage_tool="coverage.py",
        coverage_version=cov_ver,
        pytest_version=pytest_ver,
        python_version=py_ver,
        measurement_id=measurement_id,
        lines_total=line_total,
        lines_covered=line_covered,
        line_percent=line_pct,
        branches_total=br_total,
        branches_covered=br_covered,
        branch_percent=br_pct,
        duration_seconds=duration,
        exit_code=rc,
        timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        artifact_path=str(out),
        artifact_sha256="",  # filled after write
        configuration={"max_runtime": max_runtime},
    )

    # Write the truth artifact. The sha256 is computed over the
    # canonical body (everything except artifact_sha256 itself) and
    # then embedded. The final on-disk sha will differ from the
    # recorded value, which is the standard content-hash chicken/egg;
    # the recorded sha is the hash of the canonical content, not the
    # envelope.
    truth_dict = truth.to_dict()
    truth_dict["artifact_sha256"] = ""  # placeholder
    out.write_text(json.dumps(truth_dict, indent=2, sort_keys=True))
    # Hash the canonical body (with empty sha256) and replace the field.
    body_with_empty_sha = json.dumps(truth_dict, indent=2, sort_keys=True)
    sha = hashlib.sha256(body_with_empty_sha.encode("utf-8")).hexdigest()
    truth_dict["artifact_sha256"] = sha
    out.write_text(json.dumps(truth_dict, indent=2, sort_keys=True))
    return CoverageTruth(**truth_dict)


__all__ = ["CoverageTruth", "measure_coverage"]
