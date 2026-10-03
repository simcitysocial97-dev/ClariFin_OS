"""M10-R2 (C1b) — Coverage revalidation deduplication.

Before M10-R2, ``_inject_revalidations`` emitted one coverage task per
(capability, measurement-mapping) pair with **no dedup**, and because the ``--out``
path embeds the capability name, N capabilities whose coverage mapping resolved to the
same scope produced N byte-different command strings running the *same* measurement.
Measured on a 40-file boundary (see ``docs/audits/m10-r2-baseline.md``): 4 executions of
``measurement coverage tests/unit/engines`` where 1 suffices.

The contract these tests protect: **same computation, one execution, multiple
legitimate consumers.** No obligation is deleted — ``revalidation_sources`` keeps one
entry per capability, and every requesting capability still resolves a record file.
"""

from __future__ import annotations

import collections
import glob
import json

from runtime.foundation.verification.execution_orchestrator import (
    ExecutionOrchestrator,
)

NARROW = ["backend/src/engines/loan_engine/amortization.py"]


def _broad() -> list[str]:
    return sorted(glob.glob("backend/src/engines/*/*.py"))[:40]


def _scope_of(task) -> str:
    return task.command.split("coverage", 1)[1].split("--out")[0].strip()


def _orch() -> ExecutionOrchestrator:
    return ExecutionOrchestrator()


# ---------------------------------------------------------------------------
# Collapse
# ---------------------------------------------------------------------------


def test_capabilities_sharing_a_scope_produce_one_task():
    orch = _orch()
    plan = orch.build_execution_plan(_broad())
    coverage = [t for t in plan.tasks if t.verification_kind == "coverage"]

    by_scope = collections.Counter(_scope_of(t) for t in coverage)
    # One task per distinct scope — no scope may appear twice.
    assert all(count == 1 for count in by_scope.values()), by_scope

    # The collapsed task must name every capability it serves, so the "why" for each
    # capability survives into the plan rather than being silently dropped.
    for task in coverage:
        assert len(task.capabilities) >= 1
        assert task.primary_capability == sorted(task.capabilities)[0]
        assert f"measurement-truth-{task.primary_capability}-coverage.json" in (
            task.command
        )


def test_redundant_executions_are_eliminated():
    """The measured shape: four identical engine-scope executions collapse to one."""
    orch = _orch()
    plan = orch.build_execution_plan(_broad())
    coverage = [t for t in plan.tasks if t.verification_kind == "coverage"]
    distinct_scopes = {_scope_of(t) for t in coverage}
    assert len(coverage) == len(distinct_scopes)
    # The whole point: one task per distinct scope.
    engine_scope = [t for t in coverage if _scope_of(t) == "tests/unit/engines"]
    if engine_scope:
        assert len(engine_scope) == 1
        assert len(engine_scope[0].capabilities) >= 1


def test_deduped_task_still_uses_the_revalidation_origin():
    """``test_m9_c49.py::ScenarioGCoverageRegression`` asserts this, and it is the
    signal that the task is an evidence revalidation rather than a control-plane
    task. The dedup must not change it."""
    orch = _orch()
    plan = orch.build_execution_plan(_broad())
    for task in plan.tasks:
        if task.verification_kind == "coverage":
            assert task.origin == "revalidation"


# ---------------------------------------------------------------------------
# Nothing is deleted
# ---------------------------------------------------------------------------


def test_revalidation_sources_keep_one_entry_per_capability():
    """The narrative for *why* each capability needed coverage is unchanged. Only the
    task list shrinks; the evidence gap report does not."""
    orch = _orch()
    plan = orch.build_execution_plan(_broad())
    coverage_sources = [
        r for r in plan.revalidation_sources if r.get("kind") == "coverage"
    ]
    assert len(coverage_sources) == len({r["capability"] for r in coverage_sources})

    # Every capability named by a coverage task must also appear in the sources.
    task_caps = set()
    for task in plan.tasks:
        if task.verification_kind == "coverage":
            task_caps |= set(task.capabilities)
    source_caps = {r["capability"] for r in coverage_sources}
    assert task_caps <= source_caps


def test_group_membership_matches_reported_scope():
    orch = _orch()
    orch.build_execution_plan(_broad())
    groups = orch._last_coverage_groups
    assert groups, "expected at least one coverage group"
    for caps in groups.values():
        assert caps == sorted(caps)
        assert len(caps) == len(set(caps))


def test_mutation_revalidation_is_not_deduped():
    """Mutation targets genuinely differ per capability, so collapsing them would
    delete real obligations. ``test_m9_c49.py`` asserts exactly one mutation task for
    loan-engine; that must keep holding."""
    orch = _orch()
    plan = orch.build_execution_plan(
        ["backend/src/engines/loan_engine/amortization.py"]
    )
    mutation = [t for t in plan.tasks if t.verification_kind == "mutation"]
    commands = {t.command for t in mutation}
    # Two mutation tasks for the same capability would be a defect; two for different
    # capabilities are distinct obligations.
    assert len(commands) == len(mutation)


# ---------------------------------------------------------------------------
# Distinct scopes never merge
# ---------------------------------------------------------------------------


def test_distinct_scopes_are_never_collapsed():
    """api-contracts resolves to "." by design; it must stay separate from the
    engine scope rather than being absorbed into it."""
    orch = _orch()
    plan = orch.build_execution_plan(_broad())
    scopes = {_scope_of(t) for t in plan.tasks if t.verification_kind == "coverage"}
    if "api-contracts" in {
        c
        for t in plan.tasks
        if t.verification_kind == "coverage"
        for c in t.capabilities
    }:
        assert "." in scopes


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_dedup_is_deterministic():
    a = _orch().build_execution_plan(_broad())
    b = _orch().build_execution_plan(_broad())
    assert a.plan_fingerprint == b.plan_fingerprint
    assert [t.task_id for t in a.tasks] == [t.task_id for t in b.tasks]
    assert [t.command for t in a.tasks] == [t.command for t in b.tasks]


def test_narrow_boundary_is_unaffected():
    """Two capabilities, two different scopes — nothing to collapse, and the plan
    must be unchanged in shape."""
    plan = _orch().build_execution_plan(NARROW)
    coverage = [t for t in plan.tasks if t.verification_kind == "coverage"]
    assert len({_scope_of(t) for t in coverage}) == len(coverage)


# ---------------------------------------------------------------------------
# Fan-out: one execution, one record per consumer
# ---------------------------------------------------------------------------


def test_fan_out_materialises_a_record_per_requesting_capability(tmp_path):
    """The evidence contract is preserved: after one shared execution, every
    capability that shared the scope has its own record file, so
    ``_find_measurement_record`` and the certification gate resolve per capability
    exactly as they did when each capability ran its own copy."""
    from runtime.foundation.verification.measurement_truth import (
        CoverageResult,
        MeasurementKind,
        MeasurementTruthRecord,
    )

    lead = "zzz-lead-capability"
    others = ["aaa-capability", "mmm-capability"]
    caps = sorted([lead, *others])

    record = MeasurementTruthRecord(
        run_id="m10r2-fanout-fixture",
        measurement_kind=MeasurementKind.COVERAGE.value,
        repository_sha="a" * 40,
        tree_sha="b" * 40,
        toolchain_fingerprint="fixture",
        environment_fingerprint="fixture",
        coverage=CoverageResult(lines_total=200, lines_covered=165),
        coverage_result_percent=82.5,
        requested_scope="tests/unit/engines",
        actual_scope="tests/unit/engines",
    )
    (tmp_path / f"measurement-truth-{lead}-coverage.json").write_text(
        json.dumps(record.to_dict(), indent=2, default=str), encoding="utf-8"
    )

    orch = _orch()
    orch._last_coverage_groups = {"tests/unit/engines": caps}
    written = orch.fan_out_shared_measurement_records(tmp_path)

    assert len(written) == len(others)
    for cap in others:
        path = tmp_path / f"measurement-truth-{cap}-coverage.json"
        assert path.exists(), cap
        payload = json.loads(path.read_text(encoding="utf-8"))
        # The measured scope and score are preserved verbatim — nothing is claimed
        # that the single execution did not support.
        assert payload["actual_scope"] == "tests/unit/engines"
        assert payload["coverage_result_percent"] == 82.5
        assert payload["repository_sha"] == "a" * 40
        # And the sharing is explicit, not hidden.
        provenance = payload["measurement_provenance"]
        assert provenance["shared_from"] == lead
        assert provenance["measured_scope"] == "tests/unit/engines"


def test_fan_out_never_overwrites_an_existing_record(tmp_path):
    """A real per-capability record is authoritative. If one already exists it must
    be left alone — overwriting it would destroy evidence to save a file write.
    """
    lead = "zzz-lead"
    existing = "aaa-consumer"
    caps = sorted([lead, existing])
    (tmp_path / f"measurement-truth-{lead}-coverage.json").write_text(
        json.dumps(
            {
                "run_id": "fixture",
                "measurement_kind": "coverage",
                "requested_scope": "tests/unit/engines",
                "actual_scope": "tests/unit/engines",
            }
        ),
        encoding="utf-8",
    )
    original = {"run_id": "REAL-MEASUREMENT-RUN"}
    (tmp_path / f"measurement-truth-{existing}-coverage.json").write_text(
        json.dumps(original), encoding="utf-8"
    )

    orch = _orch()
    orch._last_coverage_groups = {"tests/unit/engines": caps}
    written = orch.fan_out_shared_measurement_records(tmp_path)

    assert written == []
    assert (
        json.loads(
            (tmp_path / f"measurement-truth-{existing}-coverage.json").read_text()
        )
        == original
    )


def test_fan_out_is_a_noop_without_groups(tmp_path):
    orch = _orch()
    orch._last_coverage_groups = {}
    assert orch.fan_out_shared_measurement_records(tmp_path) == []
