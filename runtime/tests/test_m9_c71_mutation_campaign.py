# runtime/tests/test_m9_c71_mutation_campaign.py
#
# M9-C71 — Sharded mutation campaign acceptance tests.
#
# Three things are certified here:
#
#   1. The mutation TOOLCHAIN contract. mutmut 3.7.0 strips a leading "src."
#      from path-derived mutant module names while this repository imports
#      production code as "src.<package>". With a pristine install every mutant
#      is dispatched to the ORIGINAL function, so the test suite exercises
#      unmutated code and the campaign reports a structurally impossible 0.0%
#      score with every mutant "survived" (GitHub run 36238247482: 0.0%, 285
#      survivors). The contract makes the declared dependency install and the
#      working toolchain the same thing, locally and in CI.
#
#   2. The SHARDED campaign contract. The single-process full campaign could
#      not complete inside any job window (run 36233136018 cancelled after
#      91m45s with no result), so the campaign is sharded per certified
#      component and reconciled by one aggregate gate that cannot silently
#      exclude a missing or empty shard.
#
#   3. The CLI surface: both new entrypoints are first-class canonical
#      commands and dispatch through the single control plane.

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from runtime.foundation.verification import mutation_shards as ms  # noqa: E402
from runtime.foundation.verification import mutmut_contract as mc  # noqa: E402
from runtime.foundation.verification.env import PINNED_MUTMUT  # noqa: E402
from runtime.foundation.verification.mutation_contract import (  # noqa: E402
    ENGINE_SELECTION,
)

# ── Synthetic trampoline fixtures ────────────────────────────────────────────

_PRISTINE = """from __future__ import annotations

def wrap_in_trampoline(mutants_dict, is_classmethod=False):
    def mutmut_mutated(decorated_func):
        def trampoline(*args, **kwargs):
            mutant_under_test = ""
            if mutant_under_test == "fail":
                raise RuntimeError("boom")
            # mutant under test is {module}.{mutant_name}
            module, _, mutant_name = mutant_under_test.rpartition(".")

            if module != decorated_func.__module__:
                # mutant of another module is active -> call original function
                return orig_func(*args, **kwargs)

            mutated_func = mutants_dict.get(mutant_name)
            if mutated_func is None:
                # No mutant being tested -> call original function
                return orig_func(*args, **kwargs)
            return mutated_func(*args, **kwargs)
        return trampoline
    return mutmut_mutated
"""


def _pristine() -> str:
    return _PRISTINE


def _canonical() -> str:
    return mc.render_contract_source(_pristine())


# ── 1. Toolchain contract ───────────────────────────────────────────────────


class TestMutmutToolchainContract:
    def test_pristine_toolchain_is_reported_as_violated(self, monkeypatch, tmp_path):
        target = tmp_path / "trampoline.py"
        target.write_text(_pristine(), encoding="utf-8")
        monkeypatch.setattr(mc, "resolve_trampoline_path", lambda: target)

        state = mc.inspect("mutmut, version 3.7.0")
        assert state.status == "VIOLATED"
        assert state.satisfied is False
        assert "not applied" in state.detail

    def test_ensure_applies_the_contract_deterministically(self, monkeypatch, tmp_path):
        target = tmp_path / "trampoline.py"
        target.write_text(_pristine(), encoding="utf-8")
        monkeypatch.setattr(mc, "resolve_trampoline_path", lambda: target)

        applied = mc.ensure("mutmut, version 3.7.0")
        assert applied.status == "APPLIED"
        assert applied.applied is True
        assert applied.satisfied is True
        assert target.read_text(encoding="utf-8") == _canonical()
        # The recorded before/after hashes must differ and the after hash must
        # equal the canonical content hash — that is what makes the record
        # auditable rather than decorative.
        assert applied.before_sha256 != applied.after_sha256
        assert applied.after_sha256 == mc._sha256(_canonical())

    def test_ensure_is_idempotent(self, monkeypatch, tmp_path):
        target = tmp_path / "trampoline.py"
        target.write_text(_pristine(), encoding="utf-8")
        monkeypatch.setattr(mc, "resolve_trampoline_path", lambda: target)

        first = mc.ensure("mutmut, version 3.7.0")
        second = mc.ensure("mutmut, version 3.7.0")
        assert first.status == "APPLIED"
        assert second.status == "SATISFIED"
        assert second.applied is False
        assert second.before_sha256 == first.after_sha256

    def test_hand_edited_toolchain_is_detected_and_re_derived(
        self, monkeypatch, tmp_path
    ):
        """A venv carrying a hand edit must be detected, not trusted."""
        hand_edited = _pristine().replace(
            "            if module != decorated_func.__module__:\n",
            "            # hand edit, different wording\n"
            "            func_module = decorated_func.__module__\n"
            '            if func_module.startswith("src."):\n'
            '                func_module = func_module[len("src."):]\n'
            "            if module != func_module:\n",
        )
        assert hand_edited != _pristine()
        target = tmp_path / "trampoline.py"
        target.write_text(hand_edited, encoding="utf-8")
        monkeypatch.setattr(mc, "resolve_trampoline_path", lambda: target)

        state = mc.inspect("mutmut, version 3.7.0")
        assert state.satisfied is False
        assert "not canonical" in state.detail

        applied = mc.ensure("mutmut, version 3.7.0")
        assert applied.satisfied is True
        assert target.read_text(encoding="utf-8") == _canonical()

    def test_unrecognised_toolchain_is_never_patched(self, monkeypatch, tmp_path):
        target = tmp_path / "trampoline.py"
        target.write_text("# a completely different trampoline\n", encoding="utf-8")
        monkeypatch.setattr(mc, "resolve_trampoline_path", lambda: target)

        state = mc.inspect("mutmut, version 3.7.0")
        assert state.status == "VIOLATED"
        assert state.satisfied is False
        with pytest.raises(mc.MutmutContractError):
            mc.ensure("mutmut, version 3.7.0")
        # Untouched.
        assert (
            target.read_text(encoding="utf-8")
            == "# a completely different trampoline\n"
        )

    def test_unpinned_mutmut_version_is_refused(self, monkeypatch, tmp_path):
        target = tmp_path / "trampoline.py"
        target.write_text(_pristine(), encoding="utf-8")
        monkeypatch.setattr(mc, "resolve_trampoline_path", lambda: target)

        with pytest.raises(mc.MutmutContractError) as excinfo:
            mc.ensure("mutmut, version 9.9.9")
        assert PINNED_MUTMUT in str(excinfo.value)

    def test_canonical_region_normalises_the_src_prefix(self):
        """The contract must make mutmut's stripped name match Python's real one."""
        assert 'func_module[len("src.") :]' in mc.CONTRACT_REGION
        assert "if module != func_module:" in mc.CONTRACT_REGION
        # The pristine rejection is what produced the 0.0% false-negative.
        assert "if module != decorated_func.__module__:" not in mc.CONTRACT_REGION

    def test_installed_toolchain_satisfies_the_contract(self):
        """The canonical venv this suite runs against must be in contract."""
        state = mc.inspect(f"mutmut, version {PINNED_MUTMUT}")
        assert state.satisfied is True, (
            "the canonical environment's mutmut trampoline is out of contract: "
            f"{state.detail}"
        )

    def test_evidence_record_is_durable(self, monkeypatch, tmp_path):
        target = tmp_path / "trampoline.py"
        target.write_text(_pristine(), encoding="utf-8")
        monkeypatch.setattr(mc, "resolve_trampoline_path", lambda: target)
        monkeypatch.setattr(mc, "evidence_path", lambda: tmp_path / "contract.json")

        contract = mc.ensure("mutmut, version 3.7.0")
        out = mc.write_evidence(contract)
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["contract_id"] == mc.PATCH_ID
        assert payload["status"] == "APPLIED"
        assert payload["satisfied"] is True
        assert payload["pinned_mutmut"] == PINNED_MUTMUT
        assert payload["before_sha256"] != payload["after_sha256"]
        assert payload["recorded_at"]


# ── 2. Sharded campaign + aggregate gate ────────────────────────────────────


def _summary(
    *,
    killed: int = 90,
    survived: int = 10,
    execution_status: str = "PASS",
    classification_status: str = "PASS",
    evidence_complete: bool = True,
    error: str | None = None,
) -> dict:
    return {
        "killed": killed,
        "survived": survived,
        "no_tests": 0,
        "timeout": 0,
        "suspicious": 0,
        "not_checked": 0,
        "execution_status": execution_status,
        "classification_status": classification_status,
        "evidence_complete": evidence_complete,
        "error": error,
    }


class TestShardPlan:
    def test_plan_covers_every_certified_component(self):
        plan = ms.shard_plan()
        components = {s.component for s in plan}
        assert components == set(ENGINE_SELECTION)

    def test_a_components_shards_partition_its_population_exactly_once(self):
        """The union of a component's shards IS the component — no double
        counting (which would inflate the aggregate) and no gaps (which would
        silently shrink the certified population)."""
        for component in sorted(ENGINE_SELECTION):
            shards = ms.pack_shards(component)
            files: list[str] = []
            for shard in shards:
                assert shard.component == component
                assert shard.tier == ENGINE_SELECTION[component].tier
                assert shard.test_selection == ENGINE_SELECTION[component].test_selection
                assert shard.also_copy == ENGINE_SELECTION[component].also_copy
                files += list(shard.files)
            assert sorted(files) == ms.component_files(component)
            assert len(files) == len(set(files)), f"{component} double-counts a file"

    def test_shards_are_bounded(self):
        for shard in ms.shard_plan():
            oversized = [
                f for f in shard.files if (ms.BACKEND_ROOT / f).stat().st_size > ms.SHARD_BYTE_CAP
            ]
            assert not oversized or len(shard.files) == 1, (
                f"shard {shard.shard_id} packs {len(shard.files)} files with an "
                f"oversize file {oversized}; only a lone oversize file may exceed the cap"
            )
            if not oversized:
                assert shard.byte_size <= ms.SHARD_BYTE_CAP

    def test_a_single_group_component_keeps_its_component_name(self):
        single = [s for s in ms.shard_plan() if len(ms.pack_shards(s.component)) == 1]
        assert single, "at least the small components must stay single-shard"
        for shard in single:
            assert shard.shard_id == shard.component
            assert shard.is_whole_component is True

    def test_multi_group_component_shard_ids_are_disambiguated(self):
        for shard in ms.shard_plan():
            if not shard.is_whole_component:
                assert ms.component_of(shard.shard_id) == shard.component

    def test_shard_plan_is_deterministic(self):
        assert [s.to_dict() for s in ms.shard_plan()] == [
            s.to_dict() for s in ms.shard_plan()
        ]

    def test_threshold_is_the_existing_campaign_threshold(self):
        from runtime.foundation.verification.config_loader import get_threshold

        assert ms.resolve_threshold() == get_threshold(
            "mutation_thresholds", "full_campaign", 80
        )
        assert ms.THRESHOLD_KEY == "full_campaign"

    def test_plan_cli_emits_a_github_matrix(self, capsys, monkeypatch):
        monkeypatch.delenv("MUTATION_COMPONENT", raising=False)
        assert ms.run_plan_cli([]) == 0
        matrix = json.loads(capsys.readouterr().out)
        assert [e["shard"] for e in matrix["include"]] == ms.shard_names()
        ids = {e["shard"] for e in matrix["include"]}
        assert len(ids) == len(matrix["include"]), "shard ids must be unique"
        for entry in matrix["include"]:
            assert entry["component"] in ENGINE_SELECTION
            assert entry["source_paths"]
            assert entry["file_count"] >= 1

    def test_plan_cli_restricts_to_one_component(self, capsys, monkeypatch):
        monkeypatch.setenv("MUTATION_COMPONENT", "balance_engine")
        assert ms.run_plan_cli([]) == 0
        matrix = json.loads(capsys.readouterr().out)
        assert [e["shard"] for e in matrix["include"]] == ["balance_engine"]

    def test_plan_cli_rejects_an_unknown_component(self, monkeypatch):
        monkeypatch.setenv("MUTATION_COMPONENT", "not_a_component")
        assert ms.run_plan_cli([]) == 1

    def test_component_without_mutable_source_is_an_explicit_error(self):
        with pytest.raises(ms.MutmutShardError):
            ms.pack_shards("__no_such_component__")


class TestAggregateGate:
    def test_fully_measured_campaign_passes_at_threshold(self):
        names = ms.shard_names()
        summaries = {n: _summary(killed=95, survived=5) for n in names}
        outcome = ms.aggregate(summaries)
        assert outcome.verdict == "PASS"
        assert outcome.mutation_score == 95.0
        assert outcome.mutants_generated == 100 * len(names)
        assert outcome.evidence_complete is True

    def test_missing_shard_is_an_explicit_failure_not_a_silent_exclusion(self):
        names = ms.shard_names()
        summaries = {n: _summary(killed=100, survived=0) for n in names[1:]}
        outcome = ms.aggregate(summaries)
        assert outcome.verdict.startswith("NOT EVALUABLE")
        assert any(names[0] in f for f in outcome.failures)
        assert outcome.evidence_complete is False

    def test_empty_population_shard_fails_the_gate(self):
        names = ms.shard_names()
        summaries = {n: _summary(killed=100, survived=0) for n in names}
        summaries[names[0]] = _summary(killed=0, survived=0)
        outcome = ms.aggregate(summaries)
        assert outcome.verdict.startswith("NOT EVALUABLE")
        assert "empty mutation population" in " ".join(outcome.failures)

    def test_infrastructure_failure_shard_fails_the_gate(self):
        names = ms.shard_names()
        summaries = {n: _summary(killed=100, survived=0) for n in names}
        summaries[names[3]] = _summary(
            execution_status="INFRASTRUCTURE_FAILURE",
            classification_status="FAIL",
            evidence_complete=False,
            error="mutation run exceeded max_runtime=4200s",
        )
        outcome = ms.aggregate(summaries)
        assert outcome.verdict.startswith("NOT EVALUABLE")
        assert "execution integrity failed" in " ".join(outcome.failures)
        assert "max_runtime" in " ".join(outcome.failures)

    def test_measured_but_low_score_fails_the_quality_gate(self):
        names = ms.shard_names()
        summaries = {n: _summary(killed=70, survived=30) for n in names}
        outcome = ms.aggregate(summaries)
        assert outcome.verdict == "QUALITY FAIL"
        assert outcome.mutation_score == 70.0
        assert outcome.mutation_score < outcome.threshold_percent
        # Measured but below threshold is NOT an infrastructure failure.
        assert outcome.execution_status == "PASS"

    def test_aggregate_score_is_population_weighted(self):
        """A tiny weak shard must not be averaged away by a huge strong shard."""
        outcome = ms.aggregate(
            {
                "big": _summary(killed=9990, survived=10),
                "small": _summary(killed=0, survived=100),
            },
            shards=["big", "small"],
        )
        # Mean-of-scores would be (99.9 + 0) / 2 = 49.95 — the population
        # weighted score must be 9990 / 10100.
        assert outcome.mutation_score == 98.9
        assert outcome.mutants_generated == 10_100
        assert outcome.verdict == "PASS"

    def test_no_silent_score_when_nothing_was_measured(self):
        outcome = ms.aggregate({}, shards=["a", "b"])
        assert outcome.mutation_score is None
        assert outcome.verdict.startswith("NOT EVALUABLE")
        assert outcome.execution_status == "PASS"

    def test_outcome_projects_onto_the_canonical_result_contract(self):
        names = ms.shard_names()
        outcome = ms.aggregate({n: _summary() for n in names})
        result = ms.as_mutation_result(outcome)
        payload = result.to_dict()
        assert payload["mode"] == "aggregate"
        assert payload["threshold_percent"] == outcome.threshold_percent
        assert payload["affected_engines"] == outcome.expected_shards
        assert payload["toolchain_contract"] == "sharded-aggregate"
        # Canonical arithmetic invariant must hold on the projected result.
        assert payload["mutants_generated"] == (
            payload["killed"]
            + payload["survived"]
            + payload["no_tests"]
            + payload["timeout"]
            + payload["suspicious"]
            + payload["not_checked"]
        )

    def test_shard_summaries_are_collected_from_artifact_directories(self, tmp_path):
        names = ms.shard_names()
        for n in names:
            root = tmp_path / f"mutation-shard-{n}"
            root.mkdir()
            (root / f"mutation-summary-{n}.json").write_text(
                json.dumps(_summary()), encoding="utf-8"
            )
        collected = ms.collect_shard_summaries(names, [tmp_path])
        assert sorted(collected) == sorted(names)
        assert collected["balance_engine"]["killed"] == 90

    def test_aggregate_cli_expectation_matches_the_plan_expectation(self, monkeypatch):
        """A shard can never be quietly dropped between planning and aggregation."""
        component = "behaviour_engine"
        planned = [s.shard_id for s in ms.pack_shards(component)]
        assert len(planned) > 1
        monkeypatch.setenv("MUTATION_COMPONENT", component)
        assert ms._expected_from_env() == planned
        monkeypatch.setenv("MUTATION_COMPONENT", "all")
        assert ms._expected_from_env() is None

    def test_aggregate_cli_exit_codes(self, tmp_path, monkeypatch, capsys):
        names = ms.shard_names()

        def _write(payload_by_shard):
            for n, payload in payload_by_shard.items():
                (tmp_path / f"mutation-summary-{n}.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )

        monkeypatch.setattr(ms, "aggregate_summary_path", lambda: tmp_path / "agg.json")
        monkeypatch.setattr(
            ms,
            "write_aggregate",
            lambda outcome: tmp_path / "agg.json",
        )
        monkeypatch.setenv("MUTATION_COMPONENT", "")
        monkeypatch.chdir(tmp_path)

        # (1) nothing measured -> 1 (not evaluable)
        assert ms.run_aggregate_cli(["--shards-dir", str(tmp_path)]) == 1
        capsys.readouterr()

        # (2) measured and at threshold -> 0
        for f in tmp_path.glob("mutation-summary-*.json"):
            f.unlink()
        _write({n: _summary(killed=95, survived=5) for n in names})
        assert ms.run_aggregate_cli(["--shards-dir", str(tmp_path)]) == 0
        capsys.readouterr()

        # (3) measured below threshold -> 2
        for f in tmp_path.glob("mutation-summary-*.json"):
            f.unlink()
        _write({n: _summary(killed=70, survived=30) for n in names})
        assert ms.run_aggregate_cli(["--shards-dir", str(tmp_path)]) == 2
        capsys.readouterr()

    def test_targeted_campaign_is_still_gated_at_the_campaign_threshold(
        self, tmp_path, monkeypatch, capsys
    ):
        """A single-component campaign must not escape the 80% gate."""
        monkeypatch.setattr(ms, "aggregate_summary_path", lambda: tmp_path / "agg.json")
        monkeypatch.setattr(
            ms, "write_aggregate", lambda outcome: tmp_path / "agg.json"
        )
        monkeypatch.setenv("MUTATION_COMPONENT", "balance_engine")
        (tmp_path / "mutation-summary-balance_engine.json").write_text(
            json.dumps(_summary(killed=70, survived=30)), encoding="utf-8"
        )
        assert ms.run_aggregate_cli(["--shards-dir", str(tmp_path)]) == 2
        report = capsys.readouterr().out
        assert "balance_engine" in report
        assert ms.resolve_threshold() == 80


# ── 3. Measurement provenance ───────────────────────────────────────────────


class TestMeasurementProvenance:
    def test_mutation_result_carries_toolchain_and_log_provenance(self):
        from runtime.foundation.verification.mutation_contract import MutationResult

        result = MutationResult(
            run_id="mut-test",
            repository_sha="a",
            tree_sha="b",
            python_version="3.12",
            pytest_version="9.1.1",
            mutmut_version="3.7.0",
            config_hash="c",
            toolchain_contract=f"{mc.PATCH_ID}:SATISFIED",
            execution_log_path="backend/tests/generated/mutation/mutation-logs/x.log",
        )
        payload = result.to_dict()
        assert payload["toolchain_contract"].endswith("SATISFIED")
        assert payload["execution_log_path"].endswith("x.log")

    def test_log_tail_reader_is_bounded(self, tmp_path):
        from runtime.foundation.verification.mutation_runner import _read_log_tail

        path = tmp_path / "big.log"
        path.write_text("x" * 10_000, encoding="utf-8")
        tail = _read_log_tail(path, limit=100)
        assert len(tail) == 100
        assert _read_log_tail(tmp_path / "missing.log") == ""


# ── 4. CLI surface ──────────────────────────────────────────────────────────


class TestCliSurface:
    def test_new_commands_are_canonical(self):
        from runtime.foundation.verification.cli_surface import classification_for

        assert classification_for("mutation-aggregate") == "CANONICAL"
        assert classification_for("mutation-plan") == "CANONICAL"

    def test_new_commands_dispatch_through_the_single_control_plane(self, monkeypatch):
        import sys

        from runtime.foundation.verification import control_plane_facade

        seen: dict[str, list[str]] = {}

        import runtime.foundation.verification.mutation_shards as shard_mod

        monkeypatch.setattr(
            shard_mod,
            "run_aggregate_cli",
            lambda argv: seen.setdefault("aggregate", argv) and 0 or 0,
        )
        monkeypatch.setattr(
            shard_mod,
            "run_plan_cli",
            lambda argv: seen.setdefault("plan", argv) and 0 or 0,
        )
        monkeypatch.setattr(sys, "argv", ["verify.py", "mutation-aggregate", "--json"])
        assert control_plane_facade.main() == 0
        monkeypatch.setattr(sys, "argv", ["verify.py", "mutation-plan"])
        assert control_plane_facade.main() == 0
        assert seen["aggregate"] == ["--json"]
        assert seen["plan"] == []


# ── 5. Workflow topology (sharded campaign on GitHub) ───────────────────────


class TestShardedWorkflowTopology:
    @pytest.fixture
    def mutation_workflow(self):
        import yaml

        return yaml.safe_load(
            (REPO_ROOT / ".github" / "workflows" / "mutation.yml").read_text()
        )

    def test_smoke_first_sharded_topology(self, mutation_workflow):
        jobs = mutation_workflow["jobs"]
        assert set(jobs) == {
            "mutation-smoke",
            "mutation-plan",
            "mutation",
            "mutation-aggregate",
        }
        assert "mutation-smoke" in jobs["mutation"]["needs"]
        assert "mutation-plan" in jobs["mutation"]["needs"]
        assert "mutation" in jobs["mutation-aggregate"]["needs"]

    def test_shards_come_from_the_canonical_plan(self, mutation_workflow):
        matrix = mutation_workflow["jobs"]["mutation"]["strategy"]["matrix"]
        assert "fromJson(needs.mutation-plan.outputs.matrix)" in str(matrix)
        # A hard-coded shard list in YAML would be a second source of truth.
        assert "shard:" not in str(matrix)
        assert "component:" not in str(matrix)

    def test_aggregate_gate_is_the_authoritative_decision(self, mutation_workflow):
        steps = mutation_workflow["jobs"]["mutation-aggregate"]["steps"]
        runs = "\n".join(s.get("run", "") for s in steps)
        assert "runtime.verify mutation-aggregate" in runs
        assert "exit $RC" in runs

    def test_shards_never_cancel_in_progress(self, mutation_workflow):
        assert mutation_workflow["concurrency"]["cancel-in-progress"] is False

    def test_every_shard_uploads_its_evidence_even_on_failure(self, mutation_workflow):
        shard_steps = mutation_workflow["jobs"]["mutation"]["steps"]
        uploads = [
            s for s in shard_steps if "upload-runtime" in str(s.get("uses", ""))
        ]
        assert uploads, "shard evidence must be uploaded"
        # A shard that failed before writing its summary must still be visible to
        # the aggregate gate, otherwise the failure is reported as "missing".
        summary_uploads = [
            s
            for s in uploads
            if "mutation-summary-${{ matrix.shard }}.json" in s["with"]["path"]
        ]
        assert summary_uploads
        for step in summary_uploads:
            assert step.get("if") == "always()"
        # The mutmut transcript is the only witness to how mutants were
        # dispatched, so it must be part of the shard evidence.
        assert any("mutation-logs/" in s["with"]["path"] for s in uploads)
        # The toolchain contract must travel with the measurement.
        assert any("mutmut-toolchain-contract.json" in s["with"]["path"] for s in uploads)
