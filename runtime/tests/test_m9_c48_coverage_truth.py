# runtime/tests/test_m9_c48_coverage_truth.py

from __future__ import annotations

import json
from pathlib import Path

from runtime.foundation.verification.coverage_truth import (
    CoverageTruth,
    measure_coverage,
)


def test_coverage_truth_to_dict_keys():
    t = CoverageTruth(
        repository_sha="abc",
        tree_sha="def",
        source_scope="backend/src",
        test_scope="tests/unit",
        coverage_tool="coverage.py",
        coverage_version="7.0",
        pytest_version="8.0",
        python_version="3.12",
        measurement_id="cov-x",
        lines_total=100,
        lines_covered=80,
        line_percent=80.0,
        branches_total=10,
        branches_covered=8,
        branch_percent=80.0,
        duration_seconds=10,
        exit_code=0,
        timestamp="2026-01-01T00:00:00Z",
        artifact_path="/tmp/x.json",
        artifact_sha256="abc",
        configuration={},
    )
    d = t.to_dict()
    for k in (
        "repository_sha",
        "tree_sha",
        "coverage_tool",
        "lines_total",
        "branch_percent",
        "artifact_sha256",
    ):
        assert k in d


def test_measure_coverage_persists_with_identity(tmp_path):
    out = tmp_path / "cov.json"
    truth = measure_coverage(
        source_scope="backend/src",
        test_scope="tests/unit/engines/credit_card_engine",
        output_path=out,
        max_runtime=300,
    )
    assert Path(out).exists()
    raw_bytes = out.read_bytes()
    data = json.loads(raw_bytes.decode("utf-8"))
    assert data["artifact_sha256"]
    # The recorded sha is the hash of the canonical body (everything
    # except the artifact_sha256 field). Verify the recorded sha
    # matches that canonical body.
    body_minus_sha = json.loads(raw_bytes.decode("utf-8"))
    body_minus_sha["artifact_sha256"] = ""
    canonical = json.dumps(body_minus_sha, indent=2, sort_keys=True).encode("utf-8")
    import hashlib
    actual = hashlib.sha256(canonical).hexdigest()
    assert data["artifact_sha256"] == actual, (
        f"recorded={data['artifact_sha256']} actual={actual}"
    )
    assert truth.measurement_id.startswith("cov-")
    assert data["repository_sha"] == truth.repository_sha


def test_measure_coverage_distinguishes_dimensions():
    """Coverage artifact must NOT include mutation_score.

    Coverage and mutation are distinct dimensions and must not be mixed.
    """
    truth = CoverageTruth(
        repository_sha="abc",
        tree_sha="def",
        source_scope="x",
        test_scope="y",
        coverage_tool="c",
        coverage_version="1",
        pytest_version="1",
        python_version="1",
        measurement_id="m",
        lines_total=0,
        lines_covered=0,
        line_percent=None,
        branches_total=0,
        branches_covered=0,
        branch_percent=None,
        duration_seconds=0,
        exit_code=0,
        timestamp="t",
        artifact_path="a",
        artifact_sha256="s",
        configuration={},
    )
    assert "mutation_score" not in truth.to_dict()
