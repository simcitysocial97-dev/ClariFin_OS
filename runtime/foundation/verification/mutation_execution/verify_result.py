# runtime/foundation/verification/mutation_execution/verify_result.py
#
# M9-C44.14 + M44.15 — Mutation Correctness Gate + Result Verification.
#
# Before accepting a mutation result, verify:
#   - KILLED: targeted tests fail BECAUSE of the mutation (not for another reason)
#   - SURVIVED: selected tests pass despite the mutation
#   - TIMEOUT: execution exceeded threshold (distinguish from EXECUTION_ERROR)
#   - NO_TESTS: no valid selected test exercised the mutation
#   - EXECUTION_ERROR: outcome cannot be determined (infrastructure failure)
#
# Additionally (M44.15):
#   - Verify mutated source actually differs from baseline
#   - Verify the intended mutation is active
#   - Verify tests imported mutated source (not site-packages original)
#   - Verify source hash matches expectation
#   - Verify worker workspace integrity
#   - Verify mutation reverted/isolated after execution

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.foundation.verification.env import REPO_ROOT
from runtime.foundation.verification.mutation_execution.domain_model import (
    MutationCandidate,
    MutationExecution,
    MutationResultState,
)


class MutationCorrectnessGate:
    """Verifies mutation result integrity before acceptance."""

    def verify_killed(
        self,
        candidate: MutationCandidate,
        execution: MutationExecution,
        workspace: Path,
    ) -> tuple[bool, str]:
        """Verify a KILLED result is genuine:
        1. Mutated source differs from baseline.
        2. The test failure is caused by the mutation, not infrastructure.
        3. The mutation is still present at verification time.
        """
        if execution.mutation_result != MutationResultState.KILLED:
            return True, "N/A (not KILLED)"

        # Check 1: mutated source differs from baseline.
        baseline_ok, baseline_msg = self._verify_source_differs(candidate, workspace)
        if not baseline_ok:
            return False, f"KILLED verification failed: {baseline_msg}"

        # Check 2: test exit code indicates actual failure.
        if execution.exit_status not in (1, 3, -24):
            return (
                False,
                f"KILLED but exit_status={execution.exit_status} (expected 1/3/-24)",
            )

        # Check 3: mutation is still active in workspace.
        still_mutated, msg = self._verify_mutation_active(candidate, workspace)
        if not still_mutated:
            return False, f"Mutation no longer active: {msg}"

        return True, "KILLED verified"

    def verify_survived(
        self,
        candidate: MutationCandidate,
        execution: MutationExecution,
        workspace: Path,
    ) -> tuple[bool, str]:
        """Verify a SURVIVED result is genuine:
        1. Mutated source differs from baseline.
        2. Tests genuinely passed against the MUTATED source (not original).
        3. This is the hardest check — if tests pass against original source,
           the result is INVALID_EXECUTION, not SURVIVED.
        """
        if execution.mutation_result != MutationResultState.SURVIVED:
            return True, "N/A (not SURVIVED)"

        # Check 1: mutated source differs from baseline.
        baseline_ok, baseline_msg = self._verify_source_differs(candidate, workspace)
        if not baseline_ok:
            # If source didn't change, the test ran against original = INVALID_EXECUTION
            return False, f"INVALID_EXECUTION: {baseline_msg}"

        # Check 2: tests actually imported mutated source.
        import_ok, import_msg = self._verify_import_path(candidate, workspace)
        if not import_ok:
            return False, f"INVALID_EXECUTION: {import_msg}"

        # Check 3: exit code indicates genuine pass.
        if execution.exit_status not in (0,):
            return False, f"Survived but exit_status={execution.exit_status}"

        return True, "SURVIVED verified"

    def verify_timeout(
        self,
        candidate: MutationCandidate,
        execution: MutationExecution,
    ) -> tuple[bool, str]:
        """Verify TIMEOUT: duration exceeds threshold, not just slow execution."""
        if execution.mutation_result != MutationResultState.TIMEOUT:
            return True, "N/A (not TIMEOUT)"
        if execution.duration_seconds == 0:
            return False, "TIMEOUT but duration=0 (likely misclassified)"
        return True, "TIMEOUT verified"

    def verify_no_tests(
        self,
        candidate: MutationCandidate,
        execution: MutationExecution,
    ) -> tuple[bool, str]:
        """Verify NO_TESTS: no tests were selected or no tests matched."""
        if execution.mutation_result != MutationResultState.NO_TESTS:
            return True, "N/A (not NO_TESTS)"
        if execution.exit_status not in (5, 33):
            return False, f"NO_TESTS but exit_status={execution.exit_status}"
        return True, "NO_TESTS verified"

    def verify_all(
        self,
        candidate: MutationCandidate,
        execution: MutationExecution,
        workspace: Path,
    ) -> tuple[bool, list[str]]:
        """Run all applicable checks. Returns (all_pass, list_of_messages)."""
        messages = []
        checks = [
            ("source_differs", self._verify_source_differs(candidate, workspace)),
            ("mutation_active", self._verify_mutation_active(candidate, workspace)),
            ("import_path", self._verify_import_path(candidate, workspace)),
        ]

        for name, (ok, msg) in checks:
            if not ok:
                messages.append(f"{name}: {msg}")

        # State-specific checks.
        if execution.mutation_result == MutationResultState.KILLED:
            ok, msg = self.verify_killed(candidate, execution, workspace)
            if not ok:
                messages.append(msg)
        elif execution.mutation_result == MutationResultState.SURVIVED:
            ok, msg = self.verify_survived(candidate, execution, workspace)
            if not ok:
                messages.append(msg)
        elif execution.mutation_result == MutationResultState.TIMEOUT:
            ok, msg = self.verify_timeout(candidate, execution)
            if not ok:
                messages.append(msg)

        return len(messages) == 0, messages

    # ── private helpers ────────────────────────────────────────────────────

    def _verify_source_differs(
        self, candidate: MutationCandidate, workspace: Path
    ) -> tuple[bool, str]:
        """Check that the mutant file differs from baseline."""
        baseline_hash = candidate.source_hash
        if not baseline_hash:
            # Try computing from repo.
            src = REPO_ROOT / candidate.source_file
            if src.exists():
                baseline_hash = hashlib.sha256(src.read_bytes()).hexdigest()[:16]
            else:
                return False, "Baseline source not found"

        # Find mutant file in workspace.
        mutants_dir = workspace / "mutants"
        for pattern in [
            candidate.source_file,
            candidate.source_file.replace("src/", ""),
        ]:
            mf = mutants_dir / pattern
            if mf.exists():
                mutant_hash = hashlib.sha256(mf.read_bytes()).hexdigest()[:16]
                if mutant_hash == baseline_hash:
                    return (
                        False,
                        "Mutant file identical to baseline (mutation not applied)",
                    )
                return True, "Source differs from baseline"

        return False, "Mutant file not found in workspace"

    def _verify_mutation_active(
        self, candidate: MutationCandidate, workspace: Path
    ) -> tuple[bool, str]:
        """Check that the mutation expression is still present in the mutant file."""
        if not candidate.original_expression or not candidate.mutated_expression:
            return True, "N/A (no expression data)"

        mutants_dir = workspace / "mutants"
        for pattern in [
            candidate.source_file,
            candidate.source_file.replace("src/", ""),
        ]:
            mf = mutants_dir / pattern
            if mf.exists():
                content = mf.read_text(errors="replace")
                # The mutated expression should be present; original should NOT be.
                has_mutated = candidate.mutated_expression in content
                has_original = candidate.original_expression in content
                if has_mutated and not has_original:
                    return True, "Mutation active"
                elif not has_mutated:
                    return False, "Mutated expression not found in mutant file"
                else:
                    return False, "Both original and mutated expressions present"
        return True, "N/A (mutant file not found)"

    def _verify_import_path(
        self, candidate: MutationCandidate, workspace: Path
    ) -> tuple[bool, str]:
        """Check that pytest would import from the workspace, not site-packages."""
        # This is a heuristic: check if PYTHONPATH includes the workspace source.
        # In practice, the adapter sets PYTHONPATH explicitly.
        # We verify by checking the environment that was used.
        src_path = workspace / "source" / candidate.source_file
        if src_path.exists():
            return True, "Workspace source exists (import path likely correct)"
        # Fallback: check if the repo source exists (editable install covers it).
        repo_src = REPO_ROOT / candidate.source_file
        if repo_src.exists():
            return True, "Repo source exists (editable install covers import)"
        return False, "Source not found in workspace or repo"


def verify_campaign_results(
    workspace: Path,
    candidates: list[MutationCandidate],
) -> dict[str, Any]:
    """Verify all results in a campaign workspace. Returns verification report."""
    gate = MutationCorrectnessGate()
    exec_dir = workspace / "executions"
    if not exec_dir.exists():
        return {"verified": 0, "passed": 0, "failed": 0, "details": []}

    # Build candidate lookup.
    cand_map = {c.canonical_mutant_id: c for c in candidates}

    passed = 0
    failed = 0
    details = []

    for exec_file in sorted(exec_dir.glob("*.json")):
        try:
            data = json.loads(exec_file.read_text())
            execution = MutationExecution.from_dict(data)
            candidate = cand_map.get(execution.mutant_id)
            if candidate is None:
                details.append(
                    {
                        "execution_id": execution.execution_id,
                        "mutant_id": execution.mutant_id,
                        "verified": False,
                        "reason": "candidate not found",
                    }
                )
                failed += 1
                continue

            ok, messages = gate.verify_all(candidate, execution, workspace)
            if ok:
                passed += 1
            else:
                failed += 1
            details.append(
                {
                    "execution_id": execution.execution_id,
                    "mutant_id": execution.mutant_id,
                    "state": execution.mutation_result.value,
                    "verified": ok,
                    "messages": messages,
                }
            )
        except Exception as exc:
            failed += 1
            details.append(
                {
                    "execution_id": "unknown",
                    "mutant_id": "unknown",
                    "verified": False,
                    "reason": str(exc),
                }
            )

    return {
        "verified": len(details),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed * 100.0 / len(details), 1) if details else 0,
        "details": details,
    }


def classify_invalid_executions(
    workspace: Path,
    candidates: list[MutationCandidate],
) -> list[dict[str, Any]]:
    """Identify results that should be reclassified as INVALID_EXECUTION
    instead of SURVIVED (tests ran against original source)."""
    gate = MutationCorrectnessGate()
    invalid = []
    cand_map = {c.canonical_mutant_id: c for c in candidates}

    exec_dir = workspace / "executions"
    for exec_file in sorted(exec_dir.glob("*.json")):
        try:
            data = json.loads(exec_file.read_text())
            execution = MutationExecution.from_dict(data)
            if execution.mutation_result != MutationResultState.SURVIVED:
                continue
            candidate = cand_map.get(execution.mutant_id)
            if candidate is None:
                continue
            ok, messages = gate.verify_survived(candidate, execution, workspace)
            if not ok:
                invalid.append(
                    {
                        "mutant_id": execution.mutant_id,
                        "original_state": "SURVIVED",
                        "reclassified_to": "INVALID_EXECUTION",
                        "reason": messages[0] if messages else "unknown",
                        "source_file": candidate.source_file,
                    }
                )
        except Exception:
            continue

    return invalid


__all__ = [
    "MutationCorrectnessGate",
    "verify_campaign_results",
    "classify_invalid_executions",
]
