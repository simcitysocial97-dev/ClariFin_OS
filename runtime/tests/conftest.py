"""Shared fixtures for runtime verification tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.planner import CrossLayerImpactPlanner
from runtime.foundation.verification.registry import (
    VerificationRegistry,
    reset_registry,
)

# ---------------------------------------------------------------------------
# M10-R2 (C2) — runtime/tests xdist pilot: MEASURED, AND REJECTED.
# ---------------------------------------------------------------------------
#
# `runtime/tests` is the longest single task in the `runtime` profile (~22 min serial),
# so parallelising it was the cheapest large win available. It was piloted and the
# result is recorded here because the negative is the finding.
#
# Measured on this host (4 cores, loadavg 4.6-6.7 during the run):
#
#   serial          2685 passed, 16 skipped   1601 s (26m41s)
#   -n 4            2584 passed, 16 skipped   1344 s (22m24s)   1.19x, 6 FAILED
#
# Every one of those 6 failures is budget exhaustion under contention, not a logic
# error:
#
#   * `runtime.verify doctor` / `runtime.verify status` timed out after 30 s
#     (they had ~2 s of headroom serially).
#   * nested suites `test_m9_c50.py` / `test_m9_c51.py` timed out after 120 s.
#   * two `test_m9_c49` scenarios asserted `diagnostic` / `awaiting_authorization`
#     and observed `validation_blocked`, because the run exceeded its own budget and
#     the fingerprint check correctly refused to certify a tree that had drifted
#     mid-run.
#
# A 1.19x gain is not worth a gate that fails intermittently. Trading a 22-minute
# deterministic gate for a 22-minute flaky one is strictly worse, so `-n` is NOT
# enabled on this suite.
#
# The cost profile explains why: the suite's time is dominated by a handful of very
# long tests (nested suites, mutation campaigns, coverage measurement), so there is
# little short-test parallelism to win. The remaining headroom here is not in
# pytest distribution at all — it is the C4 reconcile matrix, which shards whole
# verification *tasks* across runners rather than tests within one runner.
#
# These three files additionally cannot be parallelised, independent of the above:
#
# 1. `test_mutation_infra.py` writes and restores the REAL `backend/pyproject.toml`,
#    which `RepositoryFingerprint.capture()` hashes. Observed live during this
#    milestone: an interrupted run left `source_paths` pointing at `loan_engine` in
#    the working tree.
# 2. `test_full_pipeline_integration.py` writes and restores the REAL
#    `backend/src/engines/loan_engine/emi.py`, inside the tree `_hash_tree` walks.
# 3. `test_m9_c55.py::test_g20_backend_repeated_verification` runs
#    `pytest runtime/tests/test_m9_c54.py` twice and asserts both runs agree. The
#    repetition IS the certification claim — it proves reproducibility. Running
#    `test_m9_c54.py` concurrently elsewhere would let the two nested runs
#    legitimately disagree and fail a correct build. `test_g22` additionally writes
#    a shared `.coverage`, and `test_g23` runs a nested mutation smoke campaign.
#
# The guard below is therefore a live trap rather than dead commentary: if anyone
# enables `-n` on this suite later, these files are skipped under xdist only, so a
# serial run still collects everything.
SERIAL_ONLY_TESTS: tuple[str, ...] = (
    "test_mutation_infra.py",
    "test_full_pipeline_integration.py",
    "test_m9_c55.py",
)


def _xdist_active(config) -> bool:
    """True only when this collection is happening inside an xdist worker.

    ``config.option.numprocesses`` is **not** usable here: pytest-xdist strips it in
    the worker process (measured — it reads back as ``None`` with ``dist='no'`` even
    under ``-n 2``), because the worker is told what to do through ``workerinput``,
    not through the option namespace. ``workerinput`` is therefore the signal, with
    the option check kept as a secondary path for the controller.
    """
    if hasattr(config, "workerinput"):
        return True
    if getattr(config.option, "numprocesses", None) not in (None, 0, "0"):
        return True
    return getattr(config.option, "dist", "no") not in ("no", None)


def pytest_collection_modifyitems(config, items):
    """Skip the non-parallelisable files when (and only when) xdist is active.

    Serial collection is deliberately untouched: every test in this suite still runs
    on a normal `pytest runtime/tests/`.
    """
    if not _xdist_active(config):
        return

    skip_files = set(SERIAL_ONLY_TESTS)
    for item in items:
        if str(getattr(item, "fspath", "")).rsplit("/", 1)[-1] in skip_files:
            item.add_marker(
                pytest.mark.skip(reason="serial-only: shared repo/evidence state")
            )


# Test-level progress evidence (M9 stabilization, 2026-09-30).
#
# This suite takes ~29 minutes, and before this the only record of a failing
# run was a summary line. If the process died or was killed mid-run there was
# no way to know which test was executing, so the only way to investigate was
# to run the whole suite again and try to catch it again. The tracker records
# each test's start and report as they happen and keeps a small state file
# naming the last test started, which is exactly the test to look at when a
# run stops mid-test. It observes only: it changes no collection, ordering,
# outcome or assertion, and it can never fail a test run.
try:
    from runtime.foundation.verification.pytest_progress import TestProgressTracker

    _pytest_progress = TestProgressTracker()
except Exception:  # noqa: BLE001 - instrumentation must never break the suite
    _pytest_progress = None

if _pytest_progress is not None:

    def pytest_sessionstart(session):
        _pytest_progress.pytest_sessionstart(session)

    def pytest_sessionfinish(session, exitstatus):
        _pytest_progress.pytest_sessionfinish(session, exitstatus)

    def pytest_runtest_logstart(nodeid, location):
        _pytest_progress.pytest_runtest_logstart(nodeid, location)

    def pytest_runtest_logreport(report):
        _pytest_progress.pytest_runtest_logreport(report)


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Provide an isolated synthetic repo root."""
    return tmp_path


@pytest.fixture
def fixture_dir() -> Path:
    """Return the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture(fixture_dir: Path):
    """Load a fixture scenario by name."""

    def _load(name: str) -> dict:
        base = fixture_dir / name
        expected_path = base / "expected.json"
        map_path = base / "cross-layer-map.json"
        diff_path = base / "diff.json"

        result = {
            "name": name,
            "base": base,
        }
        if expected_path.exists():
            result["expected"] = json.loads(expected_path.read_text())
        if map_path.exists():
            result["cross_layer_map"] = json.loads(map_path.read_text())
        if diff_path.exists():
            result["diff"] = json.loads(diff_path.read_text())
        return result

    return _load


@pytest.fixture
def synthetic_cross_layer_map(tmp_path: Path, repo_root: Path):
    """Create a temporary cross-layer map for isolated testing."""

    def _make_map(data: dict) -> Path:
        map_path = repo_root / "runtime" / "generated" / "cross-layer-map.json"
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return map_path

    return _make_map


@pytest.fixture
def planner_with_map(synthetic_cross_layer_map):
    """Create a CrossLayerImpactPlanner backed by a temporary map."""

    def _make(map_data: dict) -> CrossLayerImpactPlanner:
        map_path = synthetic_cross_layer_map(map_data)
        return CrossLayerImpactPlanner(map_path=map_path)

    return _make


@pytest.fixture
def isolated_registry(tmp_path: Path):
    """Provide a VerificationRegistry with a temporary YAML config."""
    config = {
        "version": "1.0",
        "workflows": {
            "quick": {
                "name": "Quick",
                "description": "Quick checks",
                "category": "capability",
                "scope": "quick",
                "command": "echo quick",
                "estimated_duration_seconds": 10,
                "scopes": ["quick"],
            },
            "backend": {
                "name": "Backend",
                "description": "Backend checks",
                "category": "capability",
                "scope": "backend",
                "command": "echo backend",
                "estimated_duration_seconds": 30,
                "scopes": ["backend", "contracts"],
            },
            "contracts": {
                "name": "Contracts",
                "description": "Contract checks",
                "category": "contract",
                "scope": "contracts",
                "command": "echo contracts",
                "estimated_duration_seconds": 30,
                "scopes": ["contracts"],
            },
        },
        "scripts": {
            "run_fast_checks": {
                "name": "Fast Checks",
                "path": ".github/scripts/run_fast_checks.sh",
                "description": "Fast checks",
                "category": "capability",
                "scope": "quick",
                "estimated_duration_seconds": 10,
            },
        },
        "capabilities": {
            "loan-engine": {
                "name": "Loan Engine",
                "description": "Loan calculations",
                "category": "capability",
                "scopes": [
                    "backend",
                    "property",
                    "contracts",
                    "integration",
                    "repository",
                ],
                "workflows": ["property", "contracts", "backend"],
                "scripts": ["run_fast_checks"],
                "modules": ["backend/src/engines/loan_engine"],
                "requirements": [
                    {
                        "id": "loan-engine-property",
                        "category": "property",
                        "severity": "critical",
                        "description": "Property tests",
                        "scope": "property",
                        "module": "backend/src/engines/loan_engine",
                        "capability": "loan-engine",
                    },
                    {
                        "id": "loan-engine-contract",
                        "category": "contract",
                        "severity": "critical",
                        "description": "Contract tests",
                        "scope": "contracts",
                        "module": "backend/src/engines/loan_engine",
                        "capability": "loan-engine",
                    },
                ],
            },
            "reconciliation": {
                "name": "Reconciliation Engine",
                "description": "Reconciliation",
                "category": "capability",
                "scopes": [
                    "backend",
                    "property",
                    "contracts",
                    "integration",
                    "repository",
                ],
                "workflows": ["property", "contracts", "backend"],
                "scripts": ["run_fast_checks"],
                "modules": ["backend/src/reconciliation"],
                "requirements": [],
            },
            "ledger": {
                "name": "Ledger Service",
                "description": "Ledger",
                "category": "capability",
                "scopes": ["backend", "contracts", "integration", "repository"],
                "workflows": ["contracts", "backend", "integration"],
                "scripts": ["run_fast_checks"],
                "modules": ["backend/src/ledger"],
                "requirements": [
                    {
                        "id": "ledger-invariant",
                        "category": "invariant",
                        "severity": "critical",
                        "description": "Invariant tests",
                        "scope": "contracts",
                        "module": "backend/src/ledger",
                        "capability": "ledger",
                    },
                ],
            },
            "migrations": {
                "name": "Migrations",
                "description": "Migrations",
                "category": "migration",
                "scopes": ["migration", "backend", "repository"],
                "workflows": ["migration"],
                "scripts": [],
                "modules": ["backend/src/migrations"],
                "requirements": [],
            },
        },
        "categories": {
            "capability": {"enabled": True},
            "contract": {"enabled": True},
            "property": {"enabled": True},
            "invariant": {"enabled": True},
            "integration": {"enabled": True},
            "migration": {"enabled": True},
            "architectural": {"enabled": True},
        },
        "scopes": {
            "quick": {"enabled": True},
            "backend": {"enabled": True},
            "frontend": {"enabled": True},
            "contracts": {"enabled": True},
            "property": {"enabled": True},
            "mutation": {"enabled": True},
            "integration": {"enabled": True},
            "migration": {"enabled": True},
            "repository": {"enabled": True},
            "full": {"enabled": True},
        },
        "modules": {
            "backend": {
                "source": "backend/src",
                "tests": "backend/tests",
                "category": "capability",
            },
            "frontend": {
                "source": "frontend/src",
                "tests": "frontend/tests",
                "category": "contract_frontend",
            },
        },
    }

    config_path = tmp_path / "verification.yaml"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    # We need a YAML file, so let's write proper YAML
    import yaml

    config_path.write_text(yaml.dump(config), encoding="utf-8")

    registry = VerificationRegistry(config_path=config_path)
    registry.load()
    return registry


@pytest.fixture(autouse=True)
def reset_global_registry():
    """Reset global registry between tests."""
    reset_registry()
    yield
    reset_registry()
