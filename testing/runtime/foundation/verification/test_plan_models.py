"""Tests for runtime/foundation/verification/planner/plan_models.py.

Covers VerificationPlan.from_changed_files(), to_json/from_json roundtrip,
and to_github_outputs(). No filesystem access — string inputs only.
"""

import json

from runtime.foundation.verification.planner.impact_rules import test_changed as _test_changed
from runtime.foundation.verification.planner.plan_models import (
    MutationDecision,
    TestSuiteDecision,
    VerificationImpact,
    VerificationPlan,
)


class TestFromChangedFilesEngineChange:
    """A loan engine change triggers unit, mutation, property, integration — but NOT golden."""

    def setup_plan(self):
        return VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )

    def test_unit_tests_run_is_true(self):
        assert self.setup_plan().unit_tests.run is True

    def test_unit_tests_paths_contains_loan_path(self):
        paths = self.setup_plan().unit_tests.paths
        assert any("loan" in p for p in paths)

    def test_mutation_run_is_true(self):
        assert self.setup_plan().mutation.run is True

    def test_mutation_targets_contains_loan_engine_path(self):
        targets = self.setup_plan().mutation.targets
        assert any("loan_engine" in t for t in targets)

    def test_golden_tests_run_is_false(self):
        assert self.setup_plan().golden_tests.run is False

    def test_impact_engines_contains_loan(self):
        assert self.setup_plan().impact.engines == ["loan"]


class TestFromChangedFilestRouterChange:
    """A router change triggers contract and unit tests — but NOT mutation."""

    def setup_plan(self):
        return VerificationPlan.from_changed_files(
            ["backend/src/routers/loans.py"]
        )

    def test_contract_tests_run_is_true(self):
        assert self.setup_plan().contract_tests.run is True

    def test_unit_tests_run_is_true(self):
        assert self.setup_plan().unit_tests.run is True

    def test_mutation_run_is_false(self):
        assert self.setup_plan().mutation.run is False

    def test_impact_routers_contains_loans(self):
        assert "loans" in self.setup_plan().impact.routers


class TestFromChangedFilesModelChange:
    """A model change triggers unit tests and mutation with full blast radius."""

    def setup_plan(self):
        return VerificationPlan.from_changed_files(
            ["backend/src/core/domain/ledger.py"]
        )

    def test_unit_tests_run_is_true(self):
        assert self.setup_plan().unit_tests.run is True

    def test_impact_blast_radius_is_full(self):
        assert self.setup_plan().impact.blast_radius == "full"

    def test_mutation_run_is_true(self):
        assert self.setup_plan().mutation.run is True


class TestFromChangedFilesConfigChange:
    """A config change triggers all test suites with full blast radius."""

    def setup_plan(self):
        return VerificationPlan.from_changed_files(
            ["backend/.coveragerc"]
        )

    def test_all_tests_run(self):
        plan = self.setup_plan()
        assert plan.unit_tests.run is True
        assert plan.property_tests.run is True
        assert plan.contract_tests.run is True
        assert plan.integration_tests.run is True
        assert plan.golden_tests.run is True

    def test_impact_blast_radius_is_full(self):
        assert self.setup_plan().impact.blast_radius == "full"


class TestFromChangedFilesGeneratedFile:
    """Generated files in tests/generated/ are NOT treated as test changes."""

    def setup_plan(self):
        gen_path = "backend/tests/" + "generated/synthetic.json"
        return VerificationPlan.from_changed_files([gen_path])

    def test_test_changed_returns_false_for_generated(self):
        gen_path = "backend/tests/" + "generated/synthetic.json"
        assert _test_changed(gen_path) is False

    def test_generated_file_not_in_unit_paths(self):
        gen_path = "backend/tests/" + "generated/synthetic.json"
        paths = self.setup_plan().unit_tests.paths
        assert gen_path not in paths


class TestFromChangedFilesEmpty:
    """An empty change list produces a plan with no tests running."""

    def test_no_tests_run(self):
        plan = VerificationPlan.from_changed_files([])
        assert plan.unit_tests.run is False
        assert plan.property_tests.run is False
        assert plan.contract_tests.run is False
        assert plan.mutation.run is False
        assert plan.integration_tests.run is False
        assert plan.golden_tests.run is False

    def test_no_errors_raised(self):
        plan = VerificationPlan.from_changed_files([])
        assert plan.plan_id is not None
        assert len(plan.changed_files) == 0

    def test_blast_radius_is_low(self):
        assert VerificationPlan.from_changed_files([]).impact.blast_radius == "low"


class TestToJsonFromJson:
    """Round-trip serialization via to_json() and from_json()."""

    def test_roundtrip_preserves_plan_id(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        json_str = plan.to_json()
        parsed = json.loads(json_str)
        assert parsed["plan_id"] == plan.plan_id

    def test_roundtrip_preserves_changed_files(self):
        files = ["backend/src/engines/loan_engine/amortization.py"]
        plan = VerificationPlan.from_changed_files(files)
        parsed = VerificationPlan.from_json(plan.to_json())
        assert parsed.changed_files == files

    def test_roundtrip_preserves_impact_engines(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        parsed = VerificationPlan.from_json(plan.to_json())
        assert parsed.impact.engines == plan.impact.engines

    def test_roundtrip_preserves_unit_tests_run(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        parsed = VerificationPlan.from_json(plan.to_json())
        assert parsed.unit_tests.run == plan.unit_tests.run

    def test_roundtrip_preserves_mutation_targets(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        parsed = VerificationPlan.from_json(plan.to_json())
        assert parsed.mutation.targets == plan.mutation.targets

    def test_json_is_valid_json_string(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        json_str = plan.to_json()
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


class TestToGithubOutputs:
    """GitHub Actions output format."""

    def test_run_unit_key_exists(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        outputs = plan.to_github_outputs()
        assert "run_unit" in outputs

    def test_run_unit_value_is_true_or_false(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        outputs = plan.to_github_outputs()
        assert outputs["run_unit"] in ("true", "false")

    def test_affected_engines_is_json_list(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        outputs = plan.to_github_outputs()
        assert json.loads(outputs["affected_engines"]) == ["loan"]

    def test_affected_routers_is_json_list(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/routers/loans.py"]
        )
        outputs = plan.to_github_outputs()
        assert isinstance(json.loads(outputs["affected_routers"]), list)

    def test_blast_radius_in_outputs(self):
        plan = VerificationPlan.from_changed_files(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        outputs = plan.to_github_outputs()
        assert outputs["blast_radius"] == "medium"
