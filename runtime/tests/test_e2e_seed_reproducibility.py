# runtime/tests/test_e2e_seed_reproducibility.py
#
# M11 Task 18 — regression coverage for `tools/e2e_seed.py`.
#
# M10 recorded (`docs/audits/m10-agent3-04-remaining-issues.md` #21) that
# `tools/e2e_seed.py` "cannot seed anything": every route it called 404'd,
# because the registered product surface is `/api/v1/*` and the script called
# `/api/*`. A fresh worktree therefore had an empty database, every financial
# workspace rendered in its empty state, and no chart could be validated
# against real data. M10 Agent 3 recorded the manual recipe in
# `docs/audits/m10-agent3-03-ui-and-charts.md` §3.7.
#
# These tests exist so that class of defect cannot come back silently, and so
# that the seed's DETERMINISM is proven rather than asserted in a docstring.
#
# Design notes
# ------------
# * The seed is driven as a SUBPROCESS, never imported. Importing it would
#   pull `src.api` into the runtime suite's interpreter, where module-level
#   singletons and the autouse `reset_registry` fixture live. The runtime
#   suite must not have the product app's import side effects injected into
#   it, and the subprocess form is also exactly what a developer runs.
# * Both seed runs share ONE module-scoped fixture, so the whole file costs
#   two seed runs rather than two per test.
# * Nothing here writes inside the repository: databases and reports go to
#   `tmp_path`.

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_SCRIPT = REPO_ROOT / "tools" / "e2e_seed.py"

# Surfaces whose emptiness is a documented architectural gap rather than a
# seeding failure. Mirrors `tools.e2e_seed.KNOWN_EMPTY_SURFACES`; asserted
# separately below so the two lists cannot drift apart unnoticed.
KNOWN_EMPTY = {"behaviour_patterns"}

# The critical UI surfaces the M11 brief names: dashboard, accounts,
# transactions, cashflow, forecast, net worth, behaviour, charts, and the
# platform console. Each must carry real data after a seed.
CRITICAL_SURFACES = (
    "dashboard",
    "accounts",
    "transactions",
    "cashflow",
    "cashflow_monthly",
    "cashflow_categories",
    "net_worth",
    "forecast",
    "behaviour",
    "behaviour_profile",
    "behaviour_wellness",
    "loans",
    "investments",
    "credit_cards",
    "overview",
    "analytics",
    "categories",
)


def _run_seed(db_path: Path, report_path: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "backend")
    # Keep the run hermetic and offline, matching the runtime gate.
    env["VERIFICATION_OFFLINE"] = "1"
    return subprocess.run(
        [
            sys.executable,
            str(SEED_SCRIPT),
            "--db",
            str(db_path),
            "--reset",
            "--out",
            str(report_path),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )


@pytest.fixture(scope="module")
def two_seed_runs(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict]:
    """Seed two independent fresh databases and return both JSON reports.

    The determinism claim is "identical input produces identical seeded
    state", so the two runs must be genuinely independent: separate
    databases, separate processes, separate interpreter startups. Comparing a
    report against itself would prove nothing.
    """
    base = tmp_path_factory.mktemp("e2e-seed")
    reports: dict[str, dict] = {}
    for label in ("run_a", "run_b"):
        db_path = base / f"{label}.db"
        report_path = base / f"{label}.json"
        result = _run_seed(db_path, report_path)
        assert result.returncode == 0, (
            f"seed run {label} failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout[-2000:]}\n"
            f"--- stderr ---\n{result.stderr[-2000:]}"
        )
        assert report_path.exists(), f"seed run {label} wrote no report"
        reports[label] = json.loads(report_path.read_text())
    return reports


@pytest.mark.timeout(180)
def test_seed_is_deterministic_across_two_fresh_databases(two_seed_runs):
    """Two independent seed runs must produce byte-identical seeded state.

    This is the M11 Task 18 acceptance criterion. It compares the full
    verification payload of both runs, not just a summary count, so any
    drift in a single transaction, account or aggregate is detected.

    `database` is excluded because it is the resolved SQLite path and is
    machine dependent by construction — it is the one field the tool itself
    documents as intentionally varying. `fingerprint` is excluded only
    because it is a pure function of the payload being compared; it is
    asserted equal first, so excluding it cannot hide drift.
    """
    a = dict(two_seed_runs["run_a"])
    b = dict(two_seed_runs["run_b"])

    assert a["fingerprint"] == b["fingerprint"], (
        "seed is not deterministic: fingerprints differ between two "
        f"independent fresh runs ({a['fingerprint']} != {b['fingerprint']})"
    )

    for report in (a, b):
        report.pop("fingerprint")
        report.pop("database")
    assert a == b, "seed reports differ between two independent fresh runs"


@pytest.mark.timeout(180)
def test_seed_writes_the_expected_volume_of_data(two_seed_runs):
    """Guard against a seed that silently degrades to seeding almost nothing.

    A regression here is the exact M10 failure mode in a new disguise: the
    tool exits 0, surfaces read back, and there is simply no data in them.
    """
    written = two_seed_runs["run_a"]["written"]
    assert written["accounts"] == 3, written
    assert written["transactions_imported"] == 37, written
    assert written["loans"] == 1, written
    assert written["credit_cards"] == 1, written
    assert written["investments"] == 2, written


@pytest.mark.timeout(180)
def test_critical_ui_surfaces_are_populated(two_seed_runs):
    """Every critical surface named in the M11 brief must carry real data.

    An unexplained empty surface is the condition that made M10 conclude a
    chart was broken when the data had simply never been seeded.
    """
    report = two_seed_runs["run_a"]
    assert report["surfaces_empty_unexplained"] == [], (
        "these surfaces returned HTTP 200 with no data and are not "
        f"documented as structurally empty: {report['surfaces_empty_unexplained']}"
    )
    empty = set(report["surfaces_empty"])
    assert empty <= KNOWN_EMPTY, (
        f"unexpected empty surfaces {sorted(empty - KNOWN_EMPTY)}; if a "
        "documented gap was closed, remove it from KNOWN_EMPTY here and in "
        "tools/e2e_seed.KNOWN_EMPTY_SURFACES"
    )
    for label in CRITICAL_SURFACES:
        entry = report["verification"][label]
        assert entry["http_status"] == 200, f"{label}: HTTP {entry['http_status']}"
        assert entry["rows"] > 0, f"{label} is empty after a successful seed"


@pytest.mark.timeout(180)
def test_no_surface_or_write_errors(two_seed_runs):
    """No product endpoint may reject a canonical seed write or read.

    A failure here is a backend defect, not a seeding defect: it means a
    surface the frontend renders is unreachable with real data.
    """
    report = two_seed_runs["run_a"]
    assert report["write_errors"] == [], report["write_errors"]
    assert report["surfaces_erroring"] == [], report["surfaces_erroring"]
    assert report["platform_erroring"] == [], report["platform_erroring"]


@pytest.mark.timeout(180)
def test_platform_console_surfaces_are_reachable(two_seed_runs):
    """The platform console must answer, and `status` must be well formed."""
    platform = two_seed_runs["run_a"]["platform"]
    assert platform, "no platform-console surfaces were verified"
    for path, entry in platform.items():
        assert entry["ok"], f"{path} returned an empty body"
    assert platform["/platform/v1/status"]["kind"] == "platform.status"
    assert platform["/ready"]["status"] == "ready"
    assert platform["/health"]["status"] == "healthy"


@pytest.mark.timeout(180)
def test_seed_uses_only_canonical_v1_routes():
    """Regression guard for the M10 defect itself: the `/api` vs `/api/v1` bug.

    The original script hard-coded un-prefixed `/api/...` paths that are not
    registered, so every call 404'd and nothing was seeded while the script
    still looked plausible. This asserts structurally that no request path in
    the module escapes the canonical `/api/v1` (or `/platform/v1`, `/health`,
    `/ready`) namespaces.
    """
    source = SEED_SCRIPT.read_text()
    tree = ast.parse(source)
    api_value = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(t, ast.Name) and t.id == "API" for t in node.targets):
            api_value = ast.literal_eval(node.value)
    assert (
        api_value == "/api/v1"
    ), f"the canonical API prefix must be '/api/v1', found {api_value!r}"

    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        value = node.value
        if not value.startswith("/api"):
            continue
        if not value.startswith("/api/v1"):
            offenders.append(value)
    assert not offenders, (
        "e2e_seed references non-canonical API routes that are not "
        f"registered and will 404: {sorted(set(offenders))}"
    )


@pytest.mark.timeout(180)
def test_seed_does_not_bypass_the_canonical_api():
    """Guard the standing M9 constraint: seed through the API, never raw SQL.

    A direct `sqlite3` write or a hand-issued DDL/DML statement here would
    create the second seeding framework this tool was written to avoid, and
    would let the fixture drift from the product's own validation.
    """
    source = SEED_SCRIPT.read_text()
    tree = ast.parse(source)

    banned_modules = {"sqlite3"}
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not (banned_modules & imported), (
        f"e2e_seed must not import {sorted(banned_modules & imported)}: "
        "fixtures seed through the canonical API, not direct SQL"
    )

    # Match SQL *shapes*, not bare keywords. A bare "startswith('DROP ')"
    # check false-positived on this repository's own prose — a docstring
    # reading "Drop keys whose values legitimately vary..." — which is how a
    # guard like this quietly becomes noise and gets deleted.
    sql_statement = re.compile(
        r"^\s*(?:"
        r"INSERT\s+INTO\s+\w+"
        r"|UPDATE\s+\w+\s+SET\s+\w"
        r"|DELETE\s+FROM\s+\w+"
        r"|DROP\s+TABLE(?:\s+IF\s+EXISTS)?\s+\w+"
        r"|CREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+\w+"
        r"|ALTER\s+TABLE\s+\w+"
        r")\b",
        re.IGNORECASE,
    )
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if sql_statement.match(node.value):
            pytest.fail(
                f"e2e_seed contains raw SQL ({node.value[:60]!r}); fixtures "
                "must seed through the canonical /api/v1 path"
            )


def test_seed_script_exists_and_is_executable():
    """The tool M11 was asked to repair must remain present and runnable."""
    assert SEED_SCRIPT.exists(), f"missing {SEED_SCRIPT}"
    assert SEED_SCRIPT.read_text().startswith("#!"), "seed script lost its shebang"
