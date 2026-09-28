# runtime/tests/test_m9_c71_mutation_trust.py
#
# M9-C71 — Mutation measurement trust & survivor forensics.
#
# The milestone exists because this repository twice mistook an INVALID
# MEASUREMENT for a QUALITY PROBLEM:
#
#   * mutmut 3.7.0 strips a leading "src." from path-derived mutant module names
#     while this repository imports production code as "src.<package>", so every
#     mutant was dispatched to the ORIGINAL function. The suite passed for all
#     of them and the campaign reported a structurally impossible 0.0% with 285
#     survivors — while the execution- and evidence-integrity gates reported
#     perfect health. A dispatch failure was read as a test-quality failure.
#
#   * a Platform Console GET implicitly triggered expensive verification
#     planning, so every /platform page failed a networkidle wait regardless of
#     backend health. A timeout was read as a frontend problem.
#
# The principle under test is therefore the one C71 asserts:
#
#     A verification system must verify the validity of its measurement before
#     interpreting the measurement.
#
# What is certified here:
#
#   1. The canary must distinguish a known kill, a known survivor, a reached
#      location and an unreached one. A harness that cannot is not evidence.
#   2. The execution sentinel must resolve function-, dunder- and
#      class-scoped mutants, be inert outside a mutant fork, and never be able
#      to change a mutant's outcome.
#   3. The dispatch check must reproduce mutmut's DEFECTIVE name derivation and
#      verify the normalisation the installed toolchain applies.
#   4. The certification gate must REFUSE to certify an untrustworthy
#      measurement — the trust boundary that did not exist before C71.
#   5. Survivor classification must never label a mutant equivalent merely
#      because no test killed it, and must leave UNKNOWN at zero.
#   6. RAW must be immutable; the certified score must be reported beside it,
#      never instead of it, and never above the unchanged 80% gate by fiat.

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

from runtime.foundation.verification import mutation_shards as ms  # noqa: E402
from runtime.foundation.verification import mutation_trust as mt  # noqa: E402
from runtime.foundation.verification.env import PINNED_MUTMUT  # noqa: E402

CANARY_DIR = REPO_ROOT / "backend" / "tests" / "mutation_trust" / "canary"


def _load_sentinel():
    """Load the sentinel by path, exactly as pytest and mutmut do."""
    path = CANARY_DIR / "sentinel.py"
    spec = importlib.util.spec_from_file_location("c71_test_sentinel", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sentinel = _load_sentinel()
CLASS_SEPARATOR = "ǁ"


# ── 1. the canary proves the harness ─────────────────────────────────────────


class TestCanaryProvesTheHarness:
    def test_canary_module_declares_the_four_required_locations(self):
        source = (CANARY_DIR / "mutation_canary.py").read_text(encoding="utf-8")
        for symbol in (
            "known_kill_value",
            "known_survivor_boundary",
            "known_reached_guard",
            "known_unreached_helper",
        ):
            assert f"def {symbol}(" in source, f"canary is missing {symbol}"

    def test_canary_suite_asserts_the_exact_known_outcomes(self):
        source = (CANARY_DIR / "test_mutation_canary.py").read_text(encoding="utf-8")
        # The kill must be an exact-value assertion, or it would not kill.
        assert "known_kill_value(20) == 21" in source
        # The survivor must be observed on the guard-false side only, which is
        # what makes its survival behavioural rather than a dispatch failure.
        assert "known_survivor_boundary(0) == 0" in source
        assert "known_reached_guard(1) ==" in source
        # known_unreached_helper must have NO assertion anywhere.
        assert "known_unreached_helper(" not in source

    def test_canary_covers_the_classmethod_dispatch_path(self):
        """The @classmethod branch was C71 toolchain defect #2.

        Without a classmethod in the canary, a regression of that defect would
        again surface as a shard with no summary at all rather than as a failed
        canary.
        """
        source = (CANARY_DIR / "test_mutation_canary.py").read_text(encoding="utf-8")
        assert "from_rupees" in source
        assert "CanaryAmount" in source

    def test_evaluate_canary_reports_four_distinguishable_outcomes(
        self, monkeypatch, tmp_path
    ):
        """A canary that cannot tell a kill from a survival proves nothing."""
        mutants = tmp_path / "mutants"
        mutants.mkdir()
        # The canary's real shape: the kill location yields both killed and
        # surviving mutants, the survivor location yields both, and the
        # unreached location yields only `no tests`.
        (mutants / "m.py.meta").write_text(
            json.dumps(
                {
                    "exit_code_by_key": {
                        "m.x_known_kill_value__mutmut_1": 1,  # KILLED
                        "m.x_known_kill_value__mutmut_2": 0,  # SURVIVED
                        "m.x_known_survivor_boundary__mutmut_1": 0,  # SURVIVED
                        "m.x_known_survivor_boundary__mutmut_2": 1,  # KILLED
                        "m.x_known_reached_guard__mutmut_1": 1,  # KILLED
                        "m.x_known_reached_guard__mutmut_2": 0,  # SURVIVED
                        "m.x_known_unreached_helper__mutmut_1": 33,  # no fork
                        "m.x_known_unreached_helper__mutmut_2": 33,  # no fork
                    }
                }
            ),
            encoding="utf-8",
        )
        sink = tmp_path / mt.CANARY_SINK_NAME
        sink.write_text(
            "\n".join(
                json.dumps({"event": "ARMED", "mutant": mutant, "armed": True})
                for mutant in (
                    "m.x_known_kill_value__mutmut_1",
                    "m.x_known_kill_value__mutmut_2",
                    "m.x_known_survivor_boundary__mutmut_1",
                    "m.x_known_survivor_boundary__mutmut_2",
                    "m.x_known_reached_guard__mutmut_1",
                    "m.x_known_reached_guard__mutmut_2",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(mt, "CANARY_DIR", tmp_path)
        result = mt.evaluate_canary()
        assert result["checks"] == {
            "KNOWN_KILL_MUTANT": "KILLED",
            "KNOWN_SURVIVOR_MUTANT": "SURVIVED",
            "KNOWN_REACHED_LOCATION": "REACHED",
            "KNOWN_UNREACHED_LOCATION": "UNREACHED",
        }
        assert result["passed"] is True

    def test_canary_fails_when_a_survivor_is_never_observed(
        self, monkeypatch, tmp_path
    ):
        """A survivor with no sentinel record must not be accepted as a survivor.

        A clean exit code proves only that no test failed. Without the sentinel
        the same verdict is what a never-dispatched mutant produces, so accepting
        it would let the C71 root cause (every mutant dispatched to the original
        function) pass the canary.
        """
        mutants = tmp_path / "mutants"
        mutants.mkdir()
        (mutants / "m.py.meta").write_text(
            json.dumps(
                {
                    "exit_code_by_key": {
                        "m.x_known_kill_value__mutmut_1": 1,  # KILLED
                        "m.x_known_kill_value__mutmut_2": 0,  # SURVIVED
                        "m.x_known_survivor_boundary__mutmut_1": 0,
                        "m.x_known_survivor_boundary__mutmut_2": 1,
                    }
                }
            ),
            encoding="utf-8",
        )
        # Sink exists but omits the survivor, so it was observed-but-unarmed.
        sink = tmp_path / mt.CANARY_SINK_NAME
        sink.write_text(
            "\n".join(
                json.dumps({"event": "ARMED", "mutant": mutant, "armed": True})
                for mutant in (
                    "m.x_known_kill_value__mutmut_1",
                    "m.x_known_survivor_boundary__mutmut_2",
                )
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(mt, "CANARY_DIR", tmp_path)
        result = mt.evaluate_canary()
        assert result["checks"]["KNOWN_SURVIVOR_MUTANT"] == "FAILED"
        assert result["passed"] is False

    def test_canary_accepts_a_kill_without_sentinel_evidence(
        self, monkeypatch, tmp_path
    ):
        """A kill is self-evidencing: mutmut cannot kill unexecuted code.

        This is the asymmetry that makes the sentinel necessary and sufficient:
        execution must be PROVEN for a survival (which is otherwise
        indistinguishable from never having run), but cannot be in doubt for a
        kill.
        """
        mutants = tmp_path / "mutants"
        mutants.mkdir()
        (mutants / "m.py.meta").write_text(
            json.dumps(
                {
                    "exit_code_by_key": {
                        "m.x_known_kill_value__mutmut_1": 1,
                        "m.x_known_kill_value__mutmut_2": 0,
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(mt, "CANARY_DIR", tmp_path)
        result = mt.evaluate_canary()
        assert result["checks"]["KNOWN_KILL_MUTANT"] == "KILLED"


# ── 2. the execution sentinel is independent and inert ──────────────────────


class TestExecutionSentinel:
    def test_sentinel_is_inert_outside_a_mutant_fork(self, monkeypatch):
        monkeypatch.delenv("MUTANT_UNDER_TEST", raising=False)
        assert sentinel.active_mutant() == ""
        assert sentinel.install_import_hook() is False
        assert sentinel.arm(object()) is None

    def test_mutmut_self_check_phases_are_never_treated_as_mutants(self, monkeypatch):
        for phase in ("fail", "stats", "", "  "):
            monkeypatch.setenv("MUTANT_UNDER_TEST", phase)
            assert sentinel.active_mutant() == ""

    def test_resolves_a_plain_function_mutant(self):
        # A module namespace, not a class body: mutmut's generated symbols live
        # in the module's own __dict__, which is what the resolver reads.
        module = type("Module", (), {})()

        def mutant():
            return 1

        module.x_alpha__mutmut_1 = mutant
        found = sentinel.resolve_mutant_symbol(module, "pkg.mod.x_alpha__mutmut_1")
        assert found is not None
        assert found[0] == "x_alpha__mutmut_1"

    def test_resolves_a_class_scoped_mutant_keeping_the_full_mangled_name(self):
        """A silent miss here reported the whole Money value object as unobserved."""
        owner = type("Owner", (), {})()

        def mutant():
            return 2

        setattr(
            owner, f"x{CLASS_SEPARATOR}Owner{CLASS_SEPARATOR}beta__mutmut_2", mutant
        )
        module = type("Module", (), {})()
        # mutmut puts the generated class in the module namespace under its real
        # name; the mangled key embeds that same name.
        module.Owner = owner

        mangled = f"x{CLASS_SEPARATOR}Owner{CLASS_SEPARATOR}beta__mutmut_2"
        found = sentinel.resolve_mutant_symbol(module, mangled)
        assert found is not None, "class-scoped mutant did not resolve"
        assert found[0] == mangled

    def test_resolves_a_dunder_method_mutant(self):
        """``__rmul__`` ends in "__", so a naive split yields "…__rmul____mutmut_1"."""
        owner = type("Owner", (), {})()

        def mutant():
            return 1

        setattr(
            owner, f"x{CLASS_SEPARATOR}Owner{CLASS_SEPARATOR}__rmul____mutmut_1", mutant
        )
        module = type("Module", (), {})()
        module.Owner = owner

        mangled = f"x{CLASS_SEPARATOR}Owner{CLASS_SEPARATOR}__rmul____mutmut_1"
        found = sentinel.resolve_mutant_symbol(module, mangled)
        assert found is not None, "dunder method mutant did not resolve"

    def test_resolution_never_raises_on_an_unexpected_object(self):
        """A sentinel that crashes is worse than one that reports failure."""
        assert sentinel.resolve_mutant_symbol(object(), "pkg.x_f__mutmut_1") is None

    def test_unresolvable_mutant_is_recorded_not_guessed(self, monkeypatch, tmp_path):
        """An unresolvable mutant is exactly the defect the sentinel exists for."""
        sink = tmp_path / "sink.jsonl"
        monkeypatch.setenv("MUTANT_UNDER_TEST", "pkg.mod.x_absent__mutmut_1")
        monkeypatch.setenv(sentinel.SINK_ENV, str(sink))
        assert sentinel.arm(object()) is None
        records = [json.loads(line) for line in sink.read_text().splitlines() if line]
        assert records and records[0]["event"] == "DISPATCH_UNRESOLVED"
        assert records[0]["armed"] is False

    def test_sentinel_failure_can_never_change_a_mutant_outcome(
        self, monkeypatch, tmp_path
    ):
        """Evidence collection must not be able to turn a survivor into a kill."""
        monkeypatch.setenv("MUTANT_UNDER_TEST", "pkg.mod.x_alpha__mutmut_1")
        # An unwritable sink must not raise: the run must continue unaffected.
        monkeypatch.setenv(sentinel.SINK_ENV, "/proc/definitely/not/writable.jsonl")
        sentinel._append_record({"event": "probe"})

        # A monitoring failure is surfaced as SentinelError, never swallowed
        # into a silent pass. The import hook converts it into an ARM_FAILED
        # record, so it cannot alter the mutant's exit code.
        module = type("Module", (), {})()

        def mutant():
            return 1

        module.x_alpha__mutmut_1 = mutant

        class Boom:
            """A monitoring API that refuses every registration."""

            class events:
                LINE = object()

            def register_callback(self, *a, **k):
                raise ValueError("no monitoring here")

            def set_local_events(self, *a, **k):
                raise ValueError("no monitoring here")

            def use_tool_id(self, *a, **k):
                raise ValueError("no monitoring here")

            def get_tool(self, *a, **k):
                return None

        monkeypatch.setattr(sentinel.sys, "monitoring", Boom())
        with pytest.raises(sentinel.SentinelError):
            sentinel.arm(module)

    def test_module_ownership_normalises_the_src_prefix(self, monkeypatch):
        """mutmut's stripped name and Python's real import name must agree."""
        monkeypatch.setenv("MUTANT_UNDER_TEST", "engines.x_alpha__mutmut_1")
        assert sentinel.module_owns_mutant("src.engines") is True
        assert sentinel.module_owns_mutant("engines") is True
        assert sentinel.module_owns_mutant("src.other") is False


# ── 3. dispatch contract ────────────────────────────────────────────────────


class TestDispatchContract:
    def test_reproduces_mutmut_defective_name_derivation(self):
        """The check must reproduce what mutmut ACTUALLY does, defect included.

        Using a corrected derivation would certify a toolchain that is not
        installed and would not detect the defect the check exists to detect.
        """
        assert mt.mutmut_module_name("src/engines/cashflow_engine.py") == (
            "engines.cashflow_engine"
        )
        # mutmut collapses ".__init__." AFTER stripping the src prefix.
        assert mt.mutmut_module_name("src/engines/__init__.py") == "engines"

    def test_normalisation_matches_the_installed_toolchain(self):
        assert mt.normalise_module_name("src.engines.x") == "engines.x"
        assert mt.normalise_module_name("engines.x") == "engines.x"

    def test_config_install_restore_cycle_is_byte_identical(self):
        """The mutation config must not grow on every campaign.

        The installer replaces the `[tool.mutmut]` section, but the renderer's
        provenance comments sit immediately BEFORE that header. Replacing only
        the section left them behind, so each run appended another copy — the
        file in HEAD had accreted 25 stale 'Scope: …' headers describing scopes
        that no longer applied, and restoring never produced a file
        byte-identical to the original.
        """
        from runtime.foundation.verification.mutation_contract import (
            install_mutmut_config_block,
        )

        target = REPO_ROOT / "backend" / "pyproject.toml"
        original = target.read_text(encoding="utf-8")
        try:
            for index in range(3):
                installed = install_mutmut_config_block(
                    f"# c71 probe {index}\n"
                    '[tool.mutmut]\nsource_paths = ["probe"]\nno_progress = true\n',
                    target,
                )
                target.write_text(installed, encoding="utf-8")
            assert target.read_text(encoding="utf-8") == original
            assert "c71 probe" not in target.read_text(encoding="utf-8")
        finally:
            target.write_text(original, encoding="utf-8")

    def test_every_production_source_file_dispatches(self):
        """Dispatch must be provable for the whole population, not a sample."""
        result = mt.validate_dispatch()
        assert result["files_checked"] > 100, "dispatch check covered almost nothing"
        assert (
            result["dispatch_valid"] is True
        ), f"dispatch unprovable for: {[p['source_file'] for p in result['problems'][:5]]}"


# ── 4. the self-certification gate is the point of C71 ──────────────────────


class TestSelfCertificationGate:
    def _canary(self, passed: bool = True) -> dict:
        return {
            "passed": passed,
            "checks": {
                "KNOWN_KILL_MUTANT": "KILLED" if passed else "FAILED",
                "KNOWN_SURVIVOR_MUTANT": "SURVIVED",
                "KNOWN_REACHED_LOCATION": "REACHED",
                "KNOWN_UNREACHED_LOCATION": "UNREACHED",
            },
        }

    def _sentinel(self, proven: bool = True) -> dict:
        return {
            "execution_proven_for_all_survivors": proven,
            "survivors_without_execution_evidence": 0 if proven else 4,
        }

    def _classification(self, unknown: int = 0) -> dict:
        return {"unknown_survivors": unknown}

    def _recon(self) -> mt.ScoreReconciliation:
        return mt.reconcile_scores(
            aggregate={
                "mutants_generated": 1000,
                "killed": 800,
                "survived": 200,
                "mutation_score": 80.0,
            },
            classification={"by_category": {}, "genuine_gap_survivors": 200},
        )

    def _toolchain(self, satisfied: bool = True):
        from runtime.foundation.verification import mutmut_contract as mc

        return mc.MutmutTrampolineContract(
            contract_id=mc.PATCH_ID,
            status="SATISFIED" if satisfied else "VIOLATED",
            mutmut_version=PINNED_MUTMUT or "",
            trampoline_path="",
            before_sha256="",
            after_sha256="",
            canonical_sha256="",
            applied=False,
            unsatisfied_clauses=() if satisfied else ("c71-1",),
            detail="",
        )

    def test_certifies_only_when_every_precondition_holds(self):
        cert = mt.certify(
            canary=self._canary(),
            dispatch={"dispatch_valid": True, "problems": []},
            sentinel=self._sentinel(),
            classification=self._classification(),
            reconciliation=self._recon(),
            toolchain=self._toolchain(),
        )
        assert cert.certified is True
        assert cert.refusals == []

    @pytest.mark.parametrize(
        ("broken", "expected_fragment"),
        [
            ("canary", "canary failed"),
            ("dispatch", "dispatch cannot be proven"),
            ("sentinel", "no independent evidence"),
            ("classification", "UNKNOWN"),
            ("toolchain", "toolchain contract"),
        ],
    )
    def test_each_precondition_can_refuse_certification(
        self, broken, expected_fragment
    ):
        parts = {
            "canary": self._canary(),
            "dispatch": {"dispatch_valid": True, "problems": []},
            "sentinel": self._sentinel(),
            "classification": self._classification(),
            "reconciliation": self._recon(),
            "toolchain": self._toolchain(),
        }
        if broken == "canary":
            parts["canary"] = self._canary(passed=False)
        elif broken == "dispatch":
            parts["dispatch"] = {
                "dispatch_valid": False,
                "problems": [{"source_file": "x"}],
            }
        elif broken == "sentinel":
            parts["sentinel"] = self._sentinel(proven=False)
        elif broken == "classification":
            parts["classification"] = self._classification(unknown=3)
        elif broken == "toolchain":
            parts["toolchain"] = self._toolchain(satisfied=False)

        cert = mt.certify(**parts)
        assert cert.certified is False
        assert any(expected_fragment in r for r in cert.refusals), cert.refusals

    def test_refusal_is_not_a_quality_failure(self):
        """A refused measurement says 'invalid', never '0%' and never 'PASS'."""
        cert = mt.certify(
            canary=self._canary(passed=False),
            dispatch={"dispatch_valid": True, "problems": []},
            sentinel=self._sentinel(),
            classification=self._classification(),
            reconciliation=self._recon(),
            toolchain=self._toolchain(),
        )
        assert cert.certified is False
        # The 80% gate is reported independently and is NOT converted to a pass.
        assert cert.raw_gate == "PASS"
        # A high score with an invalid measurement is still not certified.
        assert cert.raw_score == 80.0

    def test_certification_does_not_depend_on_reaching_the_threshold(self):
        """C71 must not be able to 'pass' only by reaching 80%.

        A trustworthy measurement of a failing score is a successful C71; the
        quality gate is a separate decision.
        """
        low = mt.reconcile_scores(
            aggregate={
                "mutants_generated": 1000,
                "killed": 700,
                "survived": 300,
                "mutation_score": 70.0,
            },
            classification={"by_category": {}, "genuine_gap_survivors": 300},
        )
        cert = mt.certify(
            canary=self._canary(),
            dispatch={"dispatch_valid": True, "problems": []},
            sentinel=self._sentinel(),
            classification=self._classification(),
            reconciliation=low,
            toolchain=self._toolchain(),
        )
        assert cert.raw_gate == "FAIL"
        assert (
            cert.certified is True
        ), "a valid measurement of 70% is still a valid measurement"


# ── 5. survivor taxonomy ────────────────────────────────────────────────────


class TestSurvivorTaxonomy:
    def test_all_required_categories_exist(self):
        required = {
            "MUTATION_INVALID",
            "NOT_REACHED",
            "EQUIVALENT",
            "UNOBSERVABLE_BY_CONTRACT",
            "DEFENSIVE_PATH",
            "REAL_TEST_GAP",
            "TEST_HARNESS_GAP",
            "PRODUCT_CONTRACT_GAP",
            "TOOLING_DEFECT",
            "UNKNOWN",
        }
        assert required <= set(mt.SURVIVOR_CATEGORIES)

    def _record(self, **overrides) -> dict:
        base = {
            "mutant": "engines.x.x_f__mutmut_1",
            "component": "x",
            "source_file": "src/engines/x.py",
            "function": "x_f",
            "operator_class": "control_flow",
        }
        base.update(overrides)
        return base

    def test_unmeasured_mutant_is_invalid_not_a_survivor(self):
        """An unmeasured mutant is a measurement defect, not a quality finding."""
        verdict = mt.classify_survivor(
            self._record(),
            execution="INVALID_MUTANT",
            basis="none",
            dispatch_problems=frozenset(),
            equivalence_proofs={},
        )
        assert verdict.category == "MUTATION_INVALID"

    def test_unproven_execution_is_not_reached_not_a_test_gap(self):
        verdict = mt.classify_survivor(
            self._record(),
            execution="NOT_EXECUTED",
            basis="mutmut-verdict-only",
            dispatch_problems=frozenset(),
            equivalence_proofs={},
        )
        assert verdict.category == "NOT_REACHED"
        assert verdict.category not in mt.GENUINE_GAP_CATEGORIES

    def test_unprovable_dispatch_is_a_tooling_defect(self):
        verdict = mt.classify_survivor(
            self._record(),
            execution="EXECUTED_AND_SURVIVED",
            basis="mutmut-verdict+sentinel",
            dispatch_problems=frozenset({"src/engines/x.py"}),
            equivalence_proofs={},
        )
        assert verdict.category == "TOOLING_DEFECT"

    def test_survival_alone_never_yields_equivalence(self):
        """The circular-reasoning guard: no evidence, no EQUIVALENT."""
        verdict = mt.classify_survivor(
            self._record(),
            execution="EXECUTED_AND_SURVIVED",
            basis="mutmut-verdict+sentinel",
            dispatch_problems=frozenset(),
            equivalence_proofs={},
        )
        assert verdict.category == "REAL_TEST_GAP"
        assert verdict.category != "EQUIVALENT"

    def test_equivalence_requires_a_supplied_proof(self):
        verdict = mt.classify_survivor(
            self._record(),
            execution="EXECUTED_AND_SURVIVED",
            basis="mutmut-verdict+sentinel",
            dispatch_problems=frozenset(),
            equivalence_proofs={
                "engines.x.x_f__mutmut_1": {
                    "category": "EQUIVALENT",
                    "evidence": "dual execution over 8 bounded inputs",
                    "justification": "observables identical",
                }
            },
        )
        assert verdict.category == "EQUIVALENT"
        assert verdict.justification


# ── 6. equivalence must be behavioural, and conservative ────────────────────


class TestEquivalenceIsBehavioural:
    def test_membership_against_a_literal_set_excluding_both_forms_is_sound(self):
        """``event.get("event_type", "") in ("liability_increase", ...)``.

        Neither "" nor None is in the set, so membership cannot distinguish them.
        """
        predicate = (
            "def _is_liability_event(event):\n"
            '    event_type = event.get("event_type", "")\n'
            '    return event_type in ("liability_increase", "emi_payment")\n'
        )
        path = CANARY_DIR / "_equiv_probe.py"
        path.write_text(predicate, encoding="utf-8")
        try:
            proof = mt._prove_expression_equivalence(
                path,
                "x__is_liability_event",
                [
                    {
                        "mutant": "m1",
                        "old": 'event_type = event.get("event_type", "")',
                        "new": 'event_type = event.get("event_type", None)',
                    }
                ],
            )
            assert proof["category"] == "EQUIVALENT"
            assert proof["equivalent_mutants"] == ["m1"]
        finally:
            path.unlink(missing_ok=True)

    def test_membership_against_a_set_containing_one_form_is_refused(self):
        """If "" IS in the tuple, the mutant is observable and must not be proven."""
        predicate = (
            "def _f(event):\n"
            '    event_type = event.get("event_type", "")\n'
            '    return event_type in ("", "repayment")\n'
        )
        path = CANARY_DIR / "_equiv_probe2.py"
        path.write_text(predicate, encoding="utf-8")
        try:
            proof = mt._prove_expression_equivalence(
                path,
                "x__f",
                [
                    {
                        "mutant": "m1",
                        "old": 'event_type = event.get("event_type", "")',
                        "new": 'event_type = event.get("event_type", None)',
                    }
                ],
            )
            assert proof["category"] is None, "proven equivalent although observable"
        finally:
            path.unlink(missing_ok=True)

    def test_a_replaced_literal_is_not_proven_equivalent(self):
        predicate = (
            "def _f(event):\n"
            '    kind = event.get("kind", "debit")\n'
            "    return kind\n"
        )
        path = CANARY_DIR / "_equiv_probe3.py"
        path.write_text(predicate, encoding="utf-8")
        try:
            proof = mt._prove_expression_equivalence(
                path,
                "x__f",
                [
                    {
                        "mutant": "m1",
                        "old": 'kind = event.get("kind", "debit")',
                        "new": 'kind = event.get("kind", "credit")',
                    }
                ],
            )
            assert proof["category"] is None
        finally:
            path.unlink(missing_ok=True)

    def test_a_value_used_in_arithmetic_is_not_proven_equivalent(self):
        """0 and None are NOT interchangeable in arithmetic — the proof must fail."""
        predicate = (
            "def _f(d):\n" '    amount = d.get("amount", 0)\n' "    return amount + 1\n"
        )
        path = CANARY_DIR / "_equiv_probe4.py"
        path.write_text(predicate, encoding="utf-8")
        try:
            proof = mt._prove_expression_equivalence(
                path,
                "x__f",
                [
                    {
                        "mutant": "m1",
                        "old": 'amount = d.get("amount", 0)',
                        "new": 'amount = d.get("amount", None)',
                    }
                ],
            )
            assert (
                proof["category"] is None
            ), "0 -> None proven equivalent in arithmetic"
        finally:
            path.unlink(missing_ok=True)

    def test_dual_execution_compares_the_two_real_implementations(self, tmp_path):
        """The strongest method must actually execute both implementations."""
        pristine = tmp_path / "mod.py"
        pristine.write_text("def f(v):\n    return v + 1\n", encoding="utf-8")
        generated = tmp_path / "gen.py"
        generated.write_text("def f(v):\n    return v + 2\n", encoding="utf-8")
        original = mt._observable(pristine, "f", [(1,), (2,)])
        mutant = mt._observable(generated, "f", [(1,), (2,)])
        assert original != mutant, "observably different implementations compared equal"

        generated.write_text("def f(v):\n    return v + 1\n", encoding="utf-8")
        assert mt._observable(pristine, "f", [(1,)]) == mt._observable(
            generated, "f", [(1,)]
        )

    def test_dual_execution_records_raised_exceptions_as_observations(self, tmp_path):
        path = tmp_path / "boom.py"
        path.write_text("def f(v):\n    raise ValueError('x')\n", encoding="utf-8")
        observed = mt._observable(path, "f", [(1,)])
        assert observed and observed[0][0][0] == "raise"


# ── 7. RAW is immutable; the gate is unchanged ──────────────────────────────


class TestScoreReconciliation:
    def test_raw_score_is_reported_exactly_as_measured(self):
        recon = mt.reconcile_scores(
            aggregate={
                "mutants_generated": 16801,
                "killed": 13233,
                "survived": 3561,
                "mutation_score": 78.8,
            },
            classification={"by_category": {}, "genuine_gap_survivors": 3561},
        )
        assert recon.raw_population == 16801
        assert recon.raw_killed == 13233
        assert recon.raw_score == 78.8
        assert recon.raw_gate == "FAIL"

    def test_threshold_is_read_from_configuration_not_hardcoded(self):
        assert mt.resolve_threshold() == ms.resolve_threshold()
        assert ms.DEFAULT_THRESHOLD == 80, "the campaign threshold was changed"

    def test_effective_score_never_replaces_the_raw_score(self):
        recon = mt.reconcile_scores(
            aggregate={
                "mutants_generated": 1000,
                "killed": 800,
                "survived": 200,
                "mutation_score": 80.0,
            },
            classification={
                "by_category": {"EQUIVALENT": 150},
                "genuine_gap_survivors": 50,
            },
        )
        assert recon.raw_score == 80.0
        assert recon.raw_survived == 200, "raw survivors were filtered"
        assert recon.proven_equivalent == 150
        assert recon.remaining_real_survivors == 50
        assert recon.effective_score is not None and recon.effective_score > 80.0
        # Every denominator adjustment must be individually justified.
        assert recon.adjustments
        assert all(a.get("justification") for a in recon.adjustments)

    def test_genuine_gaps_are_never_removed_from_the_denominator(self):
        recon = mt.reconcile_scores(
            aggregate={
                "mutants_generated": 1000,
                "killed": 800,
                "survived": 200,
                "mutation_score": 80.0,
            },
            classification={"by_category": {}, "genuine_gap_survivors": 200},
        )
        assert recon.valid_population == 1000
        assert recon.remaining_real_survivors == 200

    def test_effective_gate_does_not_silently_pass_the_raw_gate(self):
        recon = mt.reconcile_scores(
            aggregate={
                "mutants_generated": 1000,
                "killed": 780,
                "survived": 220,
                "mutation_score": 78.0,
            },
            classification={
                "by_category": {"EQUIVALENT": 30},
                "genuine_gap_survivors": 190,
            },
        )
        assert recon.raw_gate == "FAIL"
        assert recon.effective_gate == "PASS"
        assert recon.raw_score == 78.0, "raw gate was redefined by the certified score"

    def test_an_impossible_effective_score_is_withheld_not_published(self):
        """>100% proves mismatched shard sets; a certified score is worse than none.

        This is not hypothetical: it is exactly what a partial shard set
        produces, because the population comes from the aggregate while the
        survivor census comes from whichever shards have run.
        """
        recon = mt.reconcile_scores(
            aggregate={
                "mutants_generated": 4150,
                "killed": 3202,
                "survived": 940,
                "mutation_score": 77.2,
            },
            # Excluding 1378 "not reached" from a 4150 population would imply
            # 3202 kills in 2772 mutants = 115%.
            classification={
                "by_category": {"NOT_REACHED": 1378},
                "genuine_gap_survivors": 0,
            },
        )
        assert recon.effective_score is None, "an impossible score was published"
        assert recon.effective_gate == "FAIL"
        assert recon.valid_population == 4150
        assert any(
            "WITHHELD" in a["adjustment"] for a in recon.adjustments
        ), "the inconsistency was not recorded"


# ── 8. prioritisaton targets assurance, not score ────────────────────────────


class TestPrioritisation:
    def test_ranks_only_genuine_test_gaps(self):
        classification = {
            "verdicts": [
                {
                    "mutant": "m1",
                    "component": "loan_engine",
                    "source_file": "src/engines/loan_engine/a.py",
                    "function": "x_f",
                    "operator": "arithmetic",
                    "execution": "EXECUTED_AND_SURVIVED",
                    "category": "REAL_TEST_GAP",
                },
                {
                    "mutant": "m2",
                    "component": "ledger_audit_engine",
                    "source_file": "src/engines/ledger_audit_engine.py",
                    "function": "x_g",
                    "operator": "comparison",
                    "execution": "NOT_EXECUTED",
                    "category": "NOT_REACHED",
                },
            ]
        }
        ranked = mt.prioritise_survivors(classification)["ranked"]
        assert [r["location"].split("::")[-1] for r in ranked] == ["x_f"]

    def test_business_criticality_breaks_ties_between_equal_gaps(self):
        """Criticality must be a real factor, not decoration.

        Two locations with the same survivor count and operator must rank by
        what the behaviour decides: an untested arithmetic rule in a payment
        path matters more than the same gap in a presentation helper.
        """

        def _v(component: str, path: str, function: str, operator: str) -> dict:
            return {
                "mutant": f"{component}-{function}",
                "component": component,
                "source_file": path,
                "function": function,
                "operator": operator,
                "execution": "EXECUTED_AND_SURVIVED",
                "category": "REAL_TEST_GAP",
            }

        ranked = mt.prioritise_survivors(
            {
                "verdicts": [
                    _v(
                        "common_calculations",
                        "src/common/calculations.py",
                        "x_helper",
                        "arithmetic",
                    ),
                    _v(
                        "loan_engine",
                        "src/engines/loan_engine/a.py",
                        "x_prepay",
                        "arithmetic",
                    ),
                ]
            }
        )["ranked"]
        assert ranked[0]["component"] == "loan_engine"

    def test_ranking_is_not_by_survivors_per_mutant(self):
        """The milestone forbids selecting a shard by its survivors/population ratio.

        A location with a very high survivor density but low business value must
        not be selected purely on that ratio.
        """

        def _v(component: str, path: str, function: str, operator: str) -> dict:
            return {
                "mutant": f"{component}-{function}",
                "component": component,
                "source_file": path,
                "function": function,
                "operator": operator,
                "execution": "EXECUTED_AND_SURVIVED",
                "category": "REAL_TEST_GAP",
            }

        ranked = mt.prioritise_survivors(
            {
                "verdicts": [
                    _v(
                        "behaviour_engine",
                        "src/engines/behaviour_engine/a.py",
                        "x_low",
                        "boolean",
                    ),
                    _v(
                        "credit_card_engine",
                        "src/engines/credit_card_engine/b.py",
                        "x_high",
                        "arithmetic",
                    ),
                ]
            }
        )["ranked"]
        assert "business_criticality" in ranked[0]
        assert ranked[0]["component"] == "credit_card_engine"


# ── 9. execution classification ─────────────────────────────────────────────


class TestExecutionClassification:
    def test_survivor_without_sentinel_evidence_is_not_a_test_survivor(self):
        meta = {"m.x_f__mutmut_1": {"status": "SURVIVED", "exit_code": 0}}
        assert mt.classify_execution("m.x_f__mutmut_1", meta, set()) == "NOT_EXECUTED"
        assert (
            mt.classify_execution("m.x_f__mutmut_1", meta, {"m.x_f__mutmut_1"})
            == "EXECUTED_AND_SURVIVED"
        )

    def test_no_tests_exit_code_is_never_a_survivor(self):
        for code in (5, 33):
            meta = {"m.x_f__mutmut_1": {"status": "NO_TESTS", "exit_code": code}}
            assert (
                mt.classify_execution("m.x_f__mutmut_1", meta, set()) == "NOT_EXECUTED"
            )

    def test_unmeasured_mutant_is_invalid(self):
        assert (
            mt.classify_execution("m.absent__mutmut_1", {}, set()) == "INVALID_MUTANT"
        )

    def test_execution_basis_is_reported_not_hidden(self):
        meta = {"m.x_f__mutmut_1": {"status": "SURVIVED", "exit_code": 0}}
        assert (
            mt.execution_basis("m.x_f__mutmut_1", meta, set()) == "mutmut-verdict-only"
        )
        assert (
            mt.execution_basis("m.x_f__mutmut_1", meta, {"m.x_f__mutmut_1"})
            == "mutmut-verdict+sentinel"
        )


# ── 10. CLI surface ─────────────────────────────────────────────────────────


class TestCommandSurface:
    def test_mutation_trust_is_a_canonical_command(self):
        from runtime.foundation.verification.cli_surface import classification_for

        assert classification_for("mutation-trust") == "CANONICAL"

    def test_command_dispatches_through_the_control_plane(self):
        from runtime.foundation.verification import mutation_trust

        assert callable(mutation_trust.run_trust_cli)

    def test_facade_routes_the_command_to_the_trust_cli(self):
        """The CLI must be reachable, not merely declared."""
        import inspect

        from runtime.foundation.verification import control_plane_facade as facade

        source = inspect.getsource(facade.main)
        assert "mutation-trust" in source
        assert "run_trust_cli" in source
