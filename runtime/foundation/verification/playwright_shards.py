"""M10-R2 — deterministic sharding of the Playwright E2E suite.

The Playwright workflow ran a 2-leg matrix (one per browser project) and each leg
executed all 301 tests in one process. Sixteen spec files with very uneven weight —
``behavior.spec.ts`` carries 29 tests, ``verification-center.spec.ts`` carries 5 — make
that a poor use of runners.

This module partitions the **functional** specs into deterministic shards, reusing the
same LPT bin-packing primitive as the runtime suite
(:func:`runtime.foundation.verification.runtime_shards.build_test_shards`) rather than
introducing a second partitioner.

Why functional specs can be sharded, and visual ones cannot
------------------------------------------------------------
``run_playwright_tests.sh`` documents, at length, that **every spec shares one SQLite
file and the suite writes to it**. Fourteen POSTs were observed in a single run, so by the
time a visual spec takes its first screenshot the on-screen data depends on which specs
ran before it, how many workers were active, and how many times a test retried. Cashflow
Trend's Y-axis is derived from the data, so one varying label became 1 740 differing
pixels.

That is precisely why the script already excludes visual specs from the functional pass
and runs them last, serial, against a re-seeded database. Sharding does not weaken any of
that:

* **Functional specs shard safely** because each matrix leg is a *separate runner* with its
  own checkout and therefore its own database, freshly seeded by the workflow. That is
  stronger isolation than the single-runner case the script was written for. Within one
  shard the ordering caveats are unchanged, because a shard is still one process against
  one database.
* **Visual specs stay singular and serial.** A shard that narrowed the visual pass would
  silently drop screenshot assertions, and splitting it would reintroduce exactly the
  cross-shard database mutation the script exists to prevent. So the visual pass is one
  leg per project, unfiltered, ``--workers=1``.

Whole spec files, never split mid-file: ``test.describe`` blocks and their fixtures stay
inside one process.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from runtime.foundation.verification.runtime_shards import (
    ShardResult,
    build_test_shards,
    read_shard_results,
)

__all__ = [
    "PLAYWRIGHT_PROJECTS",
    "expected_leg_ids",
    "functional_spec_files",
    "playwright_matrix",
    "spec_test_counts",
    "verify_legs",
]

#: Browser projects, mirroring the existing matrix. Read from the workflow rather than
#: discovered, so the matrix is exactly what the workflow declares.
PLAYWRIGHT_PROJECTS: tuple[str, ...] = ("chromium", "mobile-chrome")

_SPEC_ROOT = Path("frontend/tests/e2e/specs")

#: Specs that must NOT be sharded, because they carry the visual-regression assertions
#: the script runs as its own immutable serial pass.
_VISUAL_MARKER = "Visual Regression"

_TEST_RE = re.compile(r"^\s*(?:test|test\.describe)\(", re.MULTILINE)


def functional_spec_files(spec_root: Path | None = None) -> list[str]:
    """Every E2E spec file, sorted, as repo-relative POSIX paths.

    Sorted so the partition is reproducible. The functional pass additionally filters by
    ``--grep-invert "Visual Regression"`` at run time, so visual specs are excluded from
    the shards here too rather than being handed to a leg that would then skip them.
    """
    root = Path(spec_root or _SPEC_ROOT)
    if not root.is_dir():
        return []
    return sorted(
        p.as_posix() for p in root.glob("*.spec.ts") if _VISUAL_MARKER not in _read(p)
    )


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def spec_test_counts(files: list[str], spec_root: Path | None = None) -> dict[str, int]:
    """Per-file test count, used only to *balance* shards.

    Coverage correctness never depends on it: the gate checks that the shards' file sets
    are disjoint and complete, independently of any weight. A spec whose count cannot be
    read simply weighs 1.
    """
    root = Path(spec_root or _SPEC_ROOT)
    counts: dict[str, int] = {}
    for f in files:
        path = Path(f)
        if not path.is_absolute() and not path.exists():
            path = root / Path(f).name
        counts[f] = len(_TEST_RE.findall(_read(path))) if path.exists() else 1
    return counts


def playwright_matrix(
    spec_root: Path | None = None,
    shard_count: int = 4,
    with_counts: bool = True,
    projects: tuple[str, ...] = PLAYWRIGHT_PROJECTS,
) -> str:
    """Render the Playwright fan-out as a GitHub Actions dynamic-matrix document.

    Two leg *kinds* are produced, and the gate needs to tell them apart:

    * ``kind: functional`` — one leg per (project, shard). Runs the functional pass
      restricted to its assigned spec files.
    * ``kind: visual`` — one leg per project. Runs the visual pass unfiltered and
      serial. Never sharded, per the module docstring.

    Every leg pays the same fixed cost (frontend build, browser install, webServer, DB
    seed), so shards that are too fine waste more than they save. The default of 4 keeps
    the functional critical path near the heaviest spec group without over-provisioning.
    """
    files = functional_spec_files(spec_root)
    if not files:
        raise ValueError(f"no Playwright specs found under {spec_root or _SPEC_ROOT}")
    counts = spec_test_counts(files, spec_root) if with_counts else None
    plan = build_test_shards(files, shard_count, counts)

    include: list[dict[str, Any]] = []
    for i in range(plan.shard_count):
        shard_files = list(plan.shards[i])
        if not shard_files:
            continue
        for project in projects:
            include.append(
                {
                    "kind": "functional",
                    "leg_id": f"{project}-functional-{i}",
                    "project": project,
                    "shard": i,
                    "shard_count": plan.shard_count,
                    # Space-separated: the script word-splits this deliberately, and a
                    # JSON array would need re-encoding in the shell.
                    "spec_files": " ".join(shard_files),
                    "file_count": len(shard_files),
                    "estimated_seconds": plan.estimated_seconds[i],
                }
            )
    for project in projects:
        include.append(
            {
                "kind": "visual",
                "leg_id": f"{project}-visual",
                "project": project,
                # Empty by design: the visual pass is never narrowed.
                "spec_files": "",
                "file_count": 0,
                "estimated_seconds": 0,
            }
        )

    total = sum(plan.estimated_seconds) or 1
    document = {
        "include": include,
        "leg_count": len(include),
        "functional_shards": plan.shard_count,
        "projects": list(projects),
        "spec_file_count": len(files),
        "functional_file_count": sum(len(s) for s in plan.shards),
        "estimated_seconds_total": total,
        "estimated_seconds_critical_path": max(plan.estimated_seconds, default=0),
        "estimated_speedup": round(
            total / max(max(plan.estimated_seconds, default=1), 1), 2
        ),
        # Conservative: each leg forks a browser and a webServer, so this is a cap on
        # concurrency, not a target.
        "suggested_max_parallel": 6,
    }
    return json.dumps(document, indent=2)


def expected_leg_ids(
    shard_count: int = 4,
    projects: tuple[str, ...] = PLAYWRIGHT_PROJECTS,
    spec_root: Path | None = None,
) -> list[str]:
    """Every leg the gate must see before it may certify.

    Derived from the same planner the matrix is built from, so the gate's expectation and
    the matrix cannot drift apart.
    """
    document = json.loads(
        playwright_matrix(spec_root, shard_count, with_counts=False, projects=projects)
    )
    return [leg["leg_id"] for leg in document["include"]]


def verify_legs(
    expected_ids: list[str],
    results: list[ShardResult],
) -> list[str]:
    """Reasons this fan-out must NOT certify. Empty means certified.

    Mirrors the runtime shard gate: every leg reported exactly once, every leg passed,
    and — M10-R3 B2 — every leg ran on a repository state that did not move.

    That last clause matters more here than anywhere else in the repository. A
    Playwright leg is the only obligation that owns mutable per-leg state
    (``FINANCE_DB_PATH`` points at a database it seeds, mutates and re-seeds), so it
    is the topology most likely to change something on disk during its own run. It
    reported only counts and a status before B2, so a leg that rewrote its own
    database and still exited zero was indistinguishable from a clean one.
    """
    problems: list[str] = []
    expected = list(expected_ids)
    seen: dict[str, ShardResult] = {}

    for result in results:
        if result.shard_id in seen:
            problems.append(f"{result.shard_id} reported by more than one leg")
            continue
        seen[result.shard_id] = result

    missing = [leg for leg in expected if leg not in seen]
    if missing:
        problems.append(
            f"expected {len(expected)} leg(s), {len(seen)} reported; missing: "
            + ", ".join(missing)
        )

    unknown = sorted(set(seen) - set(expected))
    if unknown:
        problems.append(f"unknown leg(s) reported: {', '.join(unknown)}")

    for leg in expected:
        result = seen.get(leg)
        if result is None:
            continue
        if not result.ok:
            problems.append(f"{leg} {result.status} (exit={result.exit_code})")
        if not result.fingerprint_stable:
            before = (result.fingerprint_before or {}).get("fingerprint", "")[:12]
            after = (result.fingerprint_after or {}).get("fingerprint", "")[:12]
            problems.append(
                f"{leg} "
                + (
                    f"repository fingerprint changed during the leg "
                    f"({before or 'unknown'} -> {after or 'unknown'})"
                    if before or after
                    else "reported no fingerprint bracket; cannot certify it"
                )
            )

    return problems


def read_leg_results(
    directory: Path,
) -> tuple[list[ShardResult], list[str], list[str], list[str]]:
    """Read every ``leg-*.json``, classifying each leg's outcome.

    Re-exported from the runtime shard module so both fan-outs read their evidence
    identically, and so both get the absent / malformed / rejected split.
    """
    return read_shard_results(Path(directory))
