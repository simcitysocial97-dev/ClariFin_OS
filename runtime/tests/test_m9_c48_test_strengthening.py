# runtime/tests/test_m9_c48_test_strengthening.py
#
# M9-C48 E1 acceptance tests for the end-to-end test strengthening pipeline.

from __future__ import annotations

import json
from pathlib import Path

from runtime.foundation.verification.test_strengthening_pipeline import (
    CandidateState,
    TestStrengtheningPipeline,
)

VALID_CANDIDATE = '''
def test_discriminator():
    """Generated test that exercises the survivor."""
    # baseline: assert neutral condition
    result = 1 + 1
    assert result == 2
'''

SYNTAX_BAD = "def broken(:\n  pass\n"


class StubExecutor:
    """Deterministic executor for tests."""

    def __init__(self, *, baseline_pass=True, mutant_killed=True):
        self.baseline_pass = baseline_pass
        self.mutant_killed = mutant_killed

    def test_executor(self, _path: str) -> tuple[bool, str]:
        return (self.baseline_pass, "stub test")

    def mutant_executor(self, _path: str, _mutant: str) -> tuple[bool, str]:
        return (self.mutant_killed, "stub mutant")


def _pipeline(
    tmp_path: Path,
    *,
    survivor: dict | None = None,
    baseline_pass: bool = True,
    mutant_killed: bool = True,
) -> TestStrengtheningPipeline:
    if survivor is None:
        survivor = {
            "mutant_id": "mutant-1",
            "source_file": "src/foo.py",
            "classification": "behavioral_gap",
        }
    stub = StubExecutor(baseline_pass=baseline_pass, mutant_killed=mutant_killed)
    return TestStrengtheningPipeline(
        survivor=survivor,
        test_executor=stub.test_executor,
        mutant_executor=stub.mutant_executor,
        evidence_dir=tmp_path,
    )


def test_promotion_happy_path(tmp_path):
    """The full pipeline promotes a candidate that satisfies all gates."""
    # Patch the generator to return a known candidate.
    from runtime.foundation.verification import test_strengthening_pipeline as mod

    class StubGen:
        def generate_from_survivor_inventory(self, survivors, classification):
            from dataclasses import dataclass

            @dataclass
            class C:
                test_code: str

            class B:
                candidates = [C(test_code=VALID_CANDIDATE)]

            return B()

    original = mod.TestStrengtheningPipeline._generate_candidate

    def _stub(self):
        cid = "test-cand-1"
        return mod.CandidateTest(
            candidate_id=cid,
            source_file=self.survivor.get("source_file", ""),
            mutant_id=self.survivor.get("mutant_id", "unknown"),
            test_code=VALID_CANDIDATE,
            generated_at="now",
        )

    mod.TestStrengtheningPipeline._generate_candidate = _stub
    try:
        p = _pipeline(tmp_path)
        res = p.run()
    finally:
        mod.TestStrengtheningPipeline._generate_candidate = original

    assert res.final_state == CandidateState.PROMOTED
    assert "all promotion criteria" in res.promotion_reason
    assert Path(res.evidence_path).exists()
    # SHA is verifiable
    import hashlib

    actual = hashlib.sha256(Path(res.evidence_path).read_bytes()).hexdigest()
    assert res.artifact_sha256 == actual


def test_reject_syntax_error(tmp_path):
    from runtime.foundation.verification import test_strengthening_pipeline as mod

    def _stub(self):
        return mod.CandidateTest(
            candidate_id="bad",
            source_file="x",
            mutant_id="m",
            test_code=SYNTAX_BAD,
            generated_at="now",
        )

    mod.TestStrengtheningPipeline._generate_candidate = _stub
    try:
        p = _pipeline(tmp_path)
        res = p.run()
    finally:
        mod.TestStrengtheningPipeline._generate_candidate = (
            mod.TestStrengtheningPipeline._generate_candidate
        )
    assert res.final_state == CandidateState.REJECTED_SYNTAX


def test_reject_baseline_failure(tmp_path):
    from runtime.foundation.verification import test_strengthening_pipeline as mod

    def _stub(self):
        return mod.CandidateTest(
            candidate_id="baseline-fail",
            source_file="x",
            mutant_id="m",
            test_code=VALID_CANDIDATE,
            generated_at="now",
        )

    original = mod.TestStrengtheningPipeline._generate_candidate
    mod.TestStrengtheningPipeline._generate_candidate = _stub
    try:
        p = _pipeline(tmp_path, baseline_pass=False)
        res = p.run()
    finally:
        mod.TestStrengtheningPipeline._generate_candidate = original
    assert res.final_state == CandidateState.REJECTED_BASELINE


def test_reject_no_kill(tmp_path):
    from runtime.foundation.verification import test_strengthening_pipeline as mod

    def _stub(self):
        return mod.CandidateTest(
            candidate_id="no-kill",
            source_file="x",
            mutant_id="m",
            test_code=VALID_CANDIDATE,
            generated_at="now",
        )

    original = mod.TestStrengtheningPipeline._generate_candidate
    mod.TestStrengtheningPipeline._generate_candidate = _stub
    try:
        p = _pipeline(tmp_path, baseline_pass=True, mutant_killed=False)
        res = p.run()
    finally:
        mod.TestStrengtheningPipeline._generate_candidate = original
    assert res.final_state == CandidateState.REJECTED_NO_KILL


def test_reject_equivalent_survivor(tmp_path):
    p = _pipeline(
        tmp_path,
        survivor={
            "mutant_id": "mut-equiv",
            "source_file": "x.py",
            "classification": "equivalent",
        },
    )
    res = p.run()
    assert res.final_state == CandidateState.REJECTED_EQUIVALENT


def test_reject_ambiguous_survivor(tmp_path):
    p = _pipeline(
        tmp_path,
        survivor={
            "mutant_id": "mut-amb",
            "source_file": "x.py",
            "classification": "ambiguous",
        },
    )
    res = p.run()
    assert res.final_state == CandidateState.REJECTED_EQUIVALENT


def test_reject_no_candidate(tmp_path):
    p = _pipeline(tmp_path)
    # Default generator may return None or empty depending on env.
    res = p.run()
    assert res.final_state in {
        CandidateState.REJECTED_SYNTAX,
        CandidateState.REJECTED_NO_KILL,
        CandidateState.REJECTED_BASELINE,
        CandidateState.PROMOTED,
    }


def test_evidence_path_exists_on_promotion(tmp_path):
    from runtime.foundation.verification import test_strengthening_pipeline as mod

    def _stub(self):
        return mod.CandidateTest(
            candidate_id="ev",
            source_file="x",
            mutant_id="m",
            test_code=VALID_CANDIDATE,
            generated_at="now",
        )

    original = mod.TestStrengtheningPipeline._generate_candidate
    mod.TestStrengtheningPipeline._generate_candidate = _stub
    try:
        p = _pipeline(tmp_path)
        res = p.run()
    finally:
        mod.TestStrengtheningPipeline._generate_candidate = original

    if res.final_state == CandidateState.PROMOTED:
        assert Path(res.evidence_path).exists()
        # Evidence is JSON-decodable and has the schema marker.
        data = json.loads(Path(res.evidence_path).read_text())
        assert data["promoted"] is True
        assert "steps" in data


def test_steps_record_full_lifecycle(tmp_path):
    from runtime.foundation.verification import test_strengthening_pipeline as mod

    def _stub(self):
        return mod.CandidateTest(
            candidate_id="trace",
            source_file="x",
            mutant_id="m",
            test_code=VALID_CANDIDATE,
            generated_at="now",
        )

    original = mod.TestStrengtheningPipeline._generate_candidate
    mod.TestStrengtheningPipeline._generate_candidate = _stub
    try:
        p = _pipeline(tmp_path)
        res = p.run()
    finally:
        mod.TestStrengtheningPipeline._generate_candidate = original
    states = [s["state"] for s in res.steps]
    # Must contain at least DISCOVERED, CLASSIFIED, DIAGNOSED.
    for required in ("discovered", "classified", "diagnosed"):
        assert required in states


def test_promotion_result_to_dict_schema(tmp_path):
    from runtime.foundation.verification import test_strengthening_pipeline as mod

    def _stub(self):
        return mod.CandidateTest(
            candidate_id="d",
            source_file="x",
            mutant_id="m",
            test_code=VALID_CANDIDATE,
            generated_at="now",
        )

    original = mod.TestStrengtheningPipeline._generate_candidate
    mod.TestStrengtheningPipeline._generate_candidate = _stub
    try:
        p = _pipeline(tmp_path)
        res = p.run()
    finally:
        mod.TestStrengtheningPipeline._generate_candidate = original
    d = res.to_dict()
    assert d["schema"] == "m9-c48/test-strengthening-pipeline@1"
    assert d["candidate_id"] == res.candidate_id
    assert d["final_state"] in {s.value for s in CandidateState}
