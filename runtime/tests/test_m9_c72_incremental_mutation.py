# runtime/tests/test_m9_c72_incremental_mutation.py
#
# M9-C72 — Tests for incremental mutation selection and derived shard budgets.
#
# WHY THIS EXISTS
# ---------------
# The campaign re-measured all 26 shards on every run regardless of what
# changed. That is the waste M9-C72 removes, and removing it introduces a new
# and dangerous failure mode: a selection bug that measures NOTHING looks
# exactly like a correct no-op.
#
# So these tests are weighted toward the ways incremental selection can be
# WRONG rather than the ways it is right:
#
#   * a path-normalisation mismatch that silently matches nothing;
#   * scoping a TEST change to one shard, when a new test can kill mutants in
#     any shard that selects it;
#   * treating a failed diff as an empty diff.
#
# A quiet bug here would not raise. It would report 80.1% and mean nothing.
#
# The budget tests exist because the shard timeout was hard-coded to 90 minutes
# while the slowest shard measured 693 s — a bound that could not fail usefully.

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from runtime.foundation.verification import mutation_shards as ms

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ── path normalisation: the failure that would match nothing ─────────────────


class TestPathNormalisation:
    def test_git_paths_are_reduced_to_the_shard_form(self):
        """Shards are backend-relative; git is repo-relative."""
        assert ms.normalise_repo_path("backend/src/engines/x.py") == (
            "src/engines/x.py"
        )

    def test_backend_relative_paths_pass_through_unchanged(self):
        assert ms.normalise_repo_path("src/engines/x.py") == "src/engines/x.py"

    @pytest.mark.parametrize("prefix", ["./", "./backend/"])
    def test_leading_dot_slash_is_stripped(self, prefix):
        assert ms.normalise_repo_path(f"{prefix}src/engines/x.py") == (
            "src/engines/x.py"
        )

    def test_windows_separators_are_normalised(self):
        assert ms.normalise_repo_path("backend\\src\\engines\\x.py") == (
            "src/engines/x.py"
        )

    def test_a_path_outside_backend_is_untouched(self):
        """A frontend change must stay a frontend change, not become a
        backend-relative path that could match a shard by accident."""
        assert ms.normalise_repo_path("frontend/src/app.ts") == ("frontend/src/app.ts")


# ── affected selection: the ways it can be wrong ─────────────────────────────


class TestAffectedSelection:
    @pytest.fixture(scope="class")
    def plan(self):
        return ms.shard_plan()

    def test_a_source_change_selects_the_owning_shard(self, plan):
        shard = next(s for s in plan if s.component == "loan_engine")
        target = shard.files[0]

        affected, _ = ms.affected_shards([f"backend/{target}"], plan)

        assert shard.shard_id in [s.shard_id for s in affected]

    def test_a_source_change_does_not_select_unrelated_shards(self, plan):
        """Over-selection wastes compute; the point is to measure less."""
        shard = next(s for s in plan if s.component == "loan_engine")

        affected, _ = ms.affected_shards([f"backend/{shard.files[0]}"], plan)

        selected = {s.shard_id for s in affected}
        assert not selected & {s.shard_id for s in plan if s.component != "loan_engine"}

    def test_a_test_change_selects_every_shard_that_selects_those_tests(self, plan):
        """The critical asymmetry.

        A new test under a component's test selection can kill a mutant in ANY
        shard of that component. Scoping it to one shard would let the mutants
        the new test was written to kill go unmeasured, while the gate still
        reported a passing score.
        """
        component = next(s for s in plan if "-" in s.shard_id)
        test_dir = component.test_selection[0]

        affected, reasons = ms.affected_shards([f"backend/{test_dir}/test_x.py"], plan)

        owning = {s.shard_id for s in plan if test_dir in s.test_selection}
        assert owning, "fixture has no sharded component sharing a test selection"
        assert owning <= {s.shard_id for s in affected}
        assert all(reasons[sid] for sid in owning)

    def test_reasons_name_the_path_that_caused_the_selection(self, plan):
        shard = next(s for s in plan if s.component == "loan_engine")
        path = f"backend/{shard.files[0]}"

        _, reasons = ms.affected_shards([path], plan)

        assert reasons[shard.shard_id] == [path]

    def test_a_documentation_change_selects_nothing(self, plan):
        """Not every commit is worth 15 minutes of compute."""
        affected, _ = ms.affected_shards(["README.md", "docs/architecture.md"], plan)

        assert affected == []

    def test_a_frontend_only_change_selects_nothing(self, plan):
        affected, _ = ms.affected_shards(
            ["frontend/src/App.tsx", "frontend/package.json"], plan
        )

        assert affected == []

    def test_an_empty_change_set_selects_nothing(self, plan):
        assert ms.affected_shards([], plan)[0] == []

    def test_a_directory_change_selects_its_shards(self, plan):
        """Editing anything inside a shard's directory affects that shard."""
        shard = next(s for s in plan if s.component == "loan_engine")
        directory = shard.files[0].rsplit("/", 1)[0]

        affected, _ = ms.affected_shards([f"backend/{directory}/new_file.py"], plan)

        assert shard.shard_id in [s.shard_id for s in affected]

    def test_a_new_file_in_a_component_directory_selects_its_shards(self, plan):
        """A file that does not exist yet still selects the shard that would own it.

        Exact-path matching alone would report no affected shard for a PR that
        adds a new engine file, and the gate would go green having measured
        nothing.
        """
        shard = next(s for s in plan if s.component == "loan_engine")
        directory = shard.files[0].rsplit("/", 1)[0]

        affected, _ = ms.affected_shards(
            [f"backend/{directory}/feature_added_this_pr.py"], plan
        )

        assert shard.shard_id in [s.shard_id for s in affected]

    def test_a_top_level_single_file_shard_stays_isolated(self, plan):
        """Single-file shards live directly in `src/engines/`.

        Widening to a file's directory without checking that the directory
        belongs to one component makes `balance_engine`, `cashflow_engine`,
        `ledger_audit_engine` and `reconciliation_engine` all share
        `src/engines/`, so a change to any of them would select all four. That
        was measured, not theorised: the first implementation did exactly that.
        """
        single = next(
            (
                s
                for s in plan
                if s.shard_id
                in {
                    "balance_engine",
                    "cashflow_engine",
                    "ledger_audit_engine",
                    "reconciliation_engine",
                }
            ),
            None,
        )
        if single is None:
            pytest.skip("fixture has no top-level single-file shard")

        affected, _ = ms.affected_shards([f"backend/{single.files[0]}"], plan)
        selected = {s.shard_id for s in affected}

        assert selected == {single.shard_id}, (
            f"a change to {single.files[0]} selected {sorted(selected)}; "
            "shards sharing a parent directory must not select each other"
        )


# ── the diff lookup: a failure must never read as "no changes" ───────────────


class TestChangedPathsLookup:
    def test_a_real_ref_produces_paths(self):
        paths = ms.changed_paths_between("HEAD")

        assert isinstance(paths, list)

    def test_an_unusable_ref_returns_empty_rather_than_raising(self):
        """The caller treats empty as unsafe, so returning empty is correct.

        Raising would abort the plan; returning a wrong non-empty list would be
        worse than either.
        """
        assert ms.changed_paths_between("definitely-not-a-ref-0000") == []

    def test_an_unusable_ref_makes_the_plan_fall_back_to_everything(self):
        """The load-bearing guarantee.

        A diff that cannot be computed is indistinguishable from an empty diff.
        Reading it as "nothing changed" would run ZERO shards and report a
        green gate, which is the worst possible outcome: a passing gate that
        measured nothing.
        """
        out = subprocess.run(
            [
                str(REPO_ROOT / ".venv/bin/python"),
                "-m",
                "runtime.verify",
                "mutation-plan",
                "--affected-from",
                "definitely-not-a-ref-0000",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert out.returncode == 0, out.stderr
        matrix = json.loads(out.stdout)

        assert matrix["diff_safe"] is False
        assert (
            matrix["shard_count"] == matrix["total_shards"]
        ), "an unusable diff must fall back to the full plan, never to none"
        assert matrix["shard_count"] > 20


# ── the derived budget ───────────────────────────────────────────────────────


class TestDerivedShardTimeout:
    def test_it_is_derived_from_measurements_not_hardcoded(self):
        """The whole point of WS-6: the budget must track observed behaviour."""
        minutes = ms.recommended_shard_timeout_minutes()

        assert isinstance(minutes, int)
        assert minutes >= ms.MIN_SHARD_TIMEOUT_MINUTES
        assert minutes <= ms.DEFAULT_SHARD_TIMEOUT_MINUTES, (
            "a derived budget that exceeds the old flat default means the "
            "measurement is being ignored"
        )

    def test_the_measured_campaign_fits_inside_the_derived_budget(self):
        """Every recorded shard duration must fit, or the gate would time out
        on work that has already been shown to complete."""
        budget = ms.recommended_shard_timeout_minutes() * 60
        recorded = [
            json.loads(path.read_text()).get("duration_seconds")
            for path in (REPO_ROOT / "backend/tests/generated/mutation").glob(
                "mutation-summary-*.json"
            )
        ]
        durations = [d for d in recorded if isinstance(d, (int, float)) and d > 0]

        if not durations:
            pytest.skip("no recorded shard durations yet")
        assert max(durations) <= budget, (
            f"slowest recorded shard is {max(durations)}s but the derived "
            f"budget is only {budget}s; the margin is not a margin"
        )

    def test_it_falls_back_to_the_flat_default_without_measurements(
        self, monkeypatch, tmp_path
    ):
        """A first run has no measurements and must behave as before."""
        monkeypatch.setattr(ms, "_load_summary", lambda path: None, raising=True)
        monkeypatch.setattr(
            "runtime.foundation.verification.mutation_trust.MUTATION_EVIDENCE_DIR",
            tmp_path,
        )

        assert ms.recommended_shard_timeout_minutes() == (
            ms.DEFAULT_SHARD_TIMEOUT_MINUTES
        )


# ── the evidence cache: reuse must be provable, not trusted ─────────────────


class TestEvidenceFingerprint:
    def test_it_covers_source_tests_toolchain_and_selection(self):
        shard = next(s for s in ms.shard_plan() if s.component == "balance_engine")

        fingerprint = ms.shard_fingerprint(shard, "3.7.0")

        assert set(fingerprint) == {
            "source_hash",
            "test_hash",
            "mutmut_version",
            "engine_selection_hash",
        }
        assert all(
            v.startswith("sha256:")
            for k, v in fingerprint.items()
            if k != "mutmut_version"
        )

    def test_it_changes_when_the_toolchain_version_changes(self):
        """Same code, different mutmut = a different measurement."""
        shard = next(s for s in ms.shard_plan() if s.component == "balance_engine")

        a = ms.shard_fingerprint(shard, "3.7.0")["engine_selection_hash"]
        b = ms.shard_fingerprint(shard, "9.9.9")["engine_selection_hash"]

        assert a == b, "only the mutmut_version field should differ"
        assert (
            ms.shard_fingerprint(shard, "3.7.0")["mutmut_version"]
            != ms.shard_fingerprint(shard, "9.9.9")["mutmut_version"]
        )


class TestEvidenceCacheValidity:
    def _seed(self, tmp_path: Path, shard_id: str, **overrides) -> Path:
        """Write one cached evidence file and return ITS path.

        The fingerprint is stamped with the INSTALLED mutmut version, which is
        what `read_cached_evidence` recomputes against. Seeding with a different
        version is not a test convenience — it is exactly the mismatch that
        makes reuse unsafe, and the rejection tests below rely on it.
        """
        plan = {s.shard_id: s for s in ms.shard_plan()}
        payload = {
            "shard": shard_id,
            "mutants_generated": 100,
            "killed": 90,
            "survived": 10,
            "no_tests": 0,
            "timeout": 0,
            "suspicious": 0,
            "not_checked": 0,
            "mutation_score": 90.0,
            "fingerprint": ms.shard_fingerprint(
                plan[shard_id], ms._installed_mutmut_version()
            ),
        }
        payload.update(overrides)
        path = tmp_path / f"mutation-summary-{shard_id}.json"
        path.write_text(json.dumps(payload))
        return path

    def test_a_matching_fingerprint_is_reused(self, tmp_path):
        shard = next(s for s in ms.shard_plan() if s.component == "balance_engine")
        self._seed(tmp_path, shard.shard_id)

        reused, rejections = ms.read_cached_evidence(tmp_path)

        assert shard.shard_id in reused
        assert rejections == []

    def test_a_stale_fingerprint_is_rejected_and_named(self, tmp_path):
        """A cache entry whose source changed must never be used.

        Using it would report a score for code that is not the code under test —
        the exact C71 failure class, where a number looks authoritative and
        describes nothing.
        """
        shard = next(s for s in ms.shard_plan() if s.component == "balance_engine")
        self._seed(
            tmp_path,
            shard.shard_id,
            fingerprint={"source_hash": "sha256:stale", "test_hash": "sha256:stale"},
        )

        reused, rejections = ms.read_cached_evidence(tmp_path)

        assert shard.shard_id not in reused
        assert any(shard.shard_id in r and "stale" in r for r in rejections)

    def test_an_entry_with_no_fingerprint_is_rejected(self, tmp_path):
        """Validity that cannot be proven is not validity."""
        shard = next(s for s in ms.shard_plan() if s.component == "balance_engine")
        path = self._seed(tmp_path, shard.shard_id)
        payload = json.loads(path.read_text())
        payload.pop("fingerprint")
        path.write_text(json.dumps(payload))

        reused, rejections = ms.read_cached_evidence(tmp_path)

        assert shard.shard_id not in reused
        assert any("fingerprint" in r for r in rejections)

    def test_no_cache_dir_yields_nothing(self):
        assert ms.read_cached_evidence(None) == ({}, [])

    def test_stale_cache_entries_become_aggregate_failures(self, tmp_path):
        """A rejected entry must FAIL the gate, not degrade it to a warning.

        Silently ignoring a stale cache is how a green gate ends up describing
        a commit that was never measured.
        """
        shard = next(s for s in ms.shard_plan() if s.component == "balance_engine")
        self._seed(
            tmp_path,
            shard.shard_id,
            fingerprint={"source_hash": "sha256:stale", "test_hash": "sha256:stale"},
        )
        _, rejections = ms.read_cached_evidence(tmp_path)

        outcome = ms.aggregate({}, ms.shard_names(), extra_failures=rejections)

        assert outcome.execution_status == "PASS"  # arithmetic is fine
        assert outcome.verdict.startswith("NOT EVALUABLE")
        assert any(shard.shard_id in f for f in outcome.failures)


# ── the plan output contract the job graph depends on ────────────────────────


class TestPlanOutputContract:
    @pytest.fixture(scope="class")
    def full_matrix(self) -> dict:
        out = subprocess.run(
            [
                str(REPO_ROOT / ".venv/bin/python"),
                "-m",
                "runtime.verify",
                "mutation-plan",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert out.returncode == 0, out.stderr
        return json.loads(out.stdout)

    def test_it_still_emits_the_full_matrix_by_default(self, full_matrix):
        """Existing consumers must not break."""
        assert full_matrix["shard_count"] > 20
        assert full_matrix["diff_safe"] is True

    def test_every_entry_carries_what_the_job_graph_needs(self, full_matrix):
        """The workflow reads shard/component/tier/file_count/source_paths.

        A missing field here fails at matrix-expansion time in CI, long after
        the runtime was the only thing that could have reported it.
        """
        for entry in full_matrix["include"]:
            for field in ("shard", "component", "tier", "file_count", "source_paths"):
                assert field in entry, f"{entry.get('shard')} is missing {field}"

    def test_it_reports_a_recommended_timeout(self, full_matrix):
        assert full_matrix["recommended_timeout_minutes"] > 0

    def test_shard_ids_are_unique(self, full_matrix):
        """A duplicate shard id would double-measure one shard and leave
        another unmeasured, while the plan reported success."""
        ids = [e["shard"] for e in full_matrix["include"]]

        assert len(ids) == len(set(ids))
