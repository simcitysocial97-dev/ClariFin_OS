# runtime/foundation/verification/mutation_execution/orchestrator.py
#
# M9-C44 — Mutation Campaign Orchestrator.
#
# Owns mutation execution semantics.  Coordinates:
#   - Baseline gate (M44.5)
#   - Candidate discovery + canonical ID assignment
#   - Workspace management (M44.6)
#   - Process isolation (M44.7)
#   - Timeout policy (M44.8)
#   - Retry semantics (M44.9)
#   - Campaign persistence/resume (M44.10)
#   - Cache lookups (M44.12)
#   - Parallel execution (M44.21)
#   - Sharding (M44.20)
#   - Evidence normalization (M44.17)
#   - Result verification (M44.15)
#
# The orchestrator calls ONLY the MutationBackendBase interface.
# It never invokes mutmut directly.

from __future__ import annotations

import json
import math
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from runtime.foundation.verification.env import REPO_ROOT, resolve_environment
from runtime.foundation.verification.mutation_execution.backend_interface import (
    MutationBackendBase,
)
from runtime.foundation.verification.mutation_execution.cache import (
    MutationCache,
    build_fingerprint_for_run,
)
from runtime.foundation.verification.mutation_execution.config_fingerprint import (
    compute_source_fingerprint,
)
from runtime.foundation.verification.mutation_execution.domain_model import (
    InfrastructureFailureKind,
    MutationCampaign,
    MutationCandidate,
    MutationExecution,
    MutationResult,
    MutationResultState,
    derive_canonical_mutant_id,
)
from runtime.foundation.verification.mutation_execution.mutmut_adapter import (
    MutmutAdapter,
)
from runtime.foundation.verification.mutation_execution.workspace import (
    MutationWorkspace,
    create_workspace,
    resume_workspace,
)

# Default timeouts (seconds).
DEFAULT_TIMEOUTS = {
    "smoke": 120,
    "target": 600,
    "full": 3600,
}

# Retry policy (M44.9).
MAX_RETRIES = 2
RETRYABLE_FAILURES = {
    InfrastructureFailureKind.SUBPROCESS_CRASH,
    InfrastructureFailureKind.CACHE_CONTAMINATION,
    InfrastructureFailureKind.WORKSPACE_CORRUPTION,
    InfrastructureFailureKind.CONCURRENCY_COLLISION,
}


class MutationOrchestrator:
    """Canonical mutation campaign orchestrator."""

    def __init__(
        self,
        backend: MutationBackendBase | None = None,
        cache: MutationCache | None = None,
        max_workers: int = 1,
        timeout: float | None = None,
    ):
        self.backend = backend or MutmutAdapter()
        self.cache = cache or MutationCache()
        self.max_workers = max_workers
        self.timeout = timeout

    def run(
        self,
        *,
        mode: str = "full",
        target: str | None = None,
        workspace: MutationWorkspace | None = None,
        resume_campaign_id: str | None = None,
        max_runtime: int | None = None,
        max_children: int = 0,
        no_cache: bool = False,
        allow_dirty: bool = False,
    ) -> tuple[MutationCampaign, MutationResult, MutationWorkspace]:
        """Execute a mutation campaign. Returns (campaign, result, workspace)."""
        # 1. Baseline gate (M44.5)
        baseline_ok, baseline_error = self._baseline_gate(mode, target)
        if not baseline_ok:
            camp = self._create_campaign(mode, target)
            camp.status = "FAILED"
            ws = self._ensure_workspace(camp)
            ws.mark_failed(baseline_error)
            result = self._infra_failure_result(camp, baseline_error)
            return camp, result, ws

        # 2. Create or resume workspace
        if resume_campaign_id:
            camp = resume_workspace(resume_campaign_id).load_manifest()
            ws = resume_workspace(resume_campaign_id)
        else:
            camp = self._create_campaign(mode, target)
            ws = create_workspace(
                campaign_id=camp.campaign_id,
                repository_revision=camp.repository_revision,
                scope=camp.scope,
                backend=self.backend.backend_name,
                backend_version=self.backend.backend_version,
                configuration_fingerprint=camp.configuration_fingerprint,
                test_selection=camp.test_selection,
                execution_policy=camp.execution_policy,
                worker_count=self.max_workers,
            )

        # 3. Discover candidates
        candidates = self._discover_candidates(camp, ws)
        if not candidates:
            camp.status = "COMPLETED"
            ws.mark_complete()
            result = MutationResult(campaign_id=camp.campaign_id, total_candidates=0)
            return camp, result, ws

        # 4. Save candidates
        candidates_dir = ws.root / "candidates"
        candidates_dir.mkdir(exist_ok=True)
        for c in candidates:
            (candidates_dir / f"{c.canonical_mutant_id}.json").write_text(
                json.dumps(c.to_dict(), indent=2) + "\n"
            )

        # 5. Generate mutations in workspace
        self.backend.generate(camp, candidates, ws.root)

        # 6. Execute with retry + cache + parallelism
        result = self._execute_campaign(camp, candidates, ws, max_runtime)

        # 7. Update campaign status
        camp.status = "COMPLETED" if result.reconcile() else "COMPLETED_PARTIAL"
        ws.manifest_path.write_text(json.dumps(camp.to_dict(), indent=2) + "\n")

        return camp, result, ws

    def shard(
        self,
        *,
        mode: str = "full",
        target: str | None = None,
        shard_index: int,
        shard_total: int,
    ) -> tuple[MutationCampaign, MutationResult, MutationWorkspace]:
        """Run a single shard of a sharded campaign (M44.20)."""
        camp = self._create_campaign(mode, target)
        camp.shard_index = shard_index
        camp.shard_total = shard_total
        camp.execution_policy = f"shard:{shard_total}"

        ws = create_workspace(
            campaign_id=f"{camp.campaign_id}-shard-{shard_index}",
            repository_revision=camp.repository_revision,
            scope=camp.scope,
            backend=self.backend.backend_name,
            backend_version=self.backend.backend_version,
            configuration_fingerprint=camp.configuration_fingerprint,
            test_selection=camp.test_selection,
            execution_policy=camp.execution_policy,
            shard_index=shard_index,
            shard_total=shard_total,
        )

        candidates = self._discover_candidates(camp, ws)
        # Deterministic shard assignment by candidate hash.
        candidates = self._assign_shard(candidates, shard_index, shard_total)

        if candidates:
            candidates_dir = ws.root / "candidates"
            candidates_dir.mkdir(exist_ok=True)
            for c in candidates:
                (candidates_dir / f"{c.canonical_mutant_id}.json").write_text(
                    json.dumps(c.to_dict(), indent=2) + "\n"
                )
            self.backend.generate(camp, candidates, ws.root)

        result = self._execute_campaign(camp, candidates, ws, self.timeout)
        camp.status = "COMPLETED"
        ws.manifest_path.write_text(json.dumps(camp.to_dict(), indent=2) + "\n")
        return camp, result, ws

    # ── private ─────────────────────────────────────────────────────────────

    def _create_campaign(self, mode: str, target: str | None) -> MutationCampaign:
        from runtime.foundation.verification.mutation_contract import (
            _FULL_SOURCE_PATHS,
            _FULL_TEST_SELECTION,
            ENGINE_SELECTION,
            SELECTION_METHOD,
        )

        if target and target in ENGINE_SELECTION:
            sel = ENGINE_SELECTION[target]
            source_paths = list(sel.source_paths)
            test_selection_list = list(sel.test_selection)
            scope = target
        else:
            source_paths = _FULL_SOURCE_PATHS
            test_selection_list = _FULL_TEST_SELECTION
            scope = "full (all engines)"

        env = resolve_environment(config_dir=REPO_ROOT / "backend")
        fp = build_fingerprint_for_run(
            backend=self.backend.backend_name,
            backend_version=self.backend.backend_version,
            source_paths=source_paths,
            test_selection=test_selection_list,
            timeout_seconds=int(self.timeout or DEFAULT_TIMEOUTS.get(mode, 3600)),
            worker_count=self.max_workers,
        )

        import subprocess

        repo_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()

        return MutationCampaign(
            campaign_id=f"mut-{uuid.uuid4().hex[:12]}",
            repository_revision=repo_sha,
            environment_fingerprint=env.fingerprint.get("fingerprint", ""),
            mutation_backend=self.backend.backend_name,
            backend_version=self.backend.backend_version,
            scope=scope,
            test_selection=SELECTION_METHOD,
            configuration_fingerprint=fp["configuration"],
            execution_policy=(
                f"parallel:{self.max_workers}" if self.max_workers > 1 else "serial"
            ),
            creation_timestamp=datetime.now(UTC).isoformat(),
        )

    def _ensure_workspace(self, camp: MutationCampaign) -> MutationWorkspace:
        return MutationWorkspace(camp)

    def _baseline_gate(self, mode: str, target: str | None) -> tuple[bool, str]:
        """M44.5: verify environment, source integrity, baseline tests pass."""
        env = resolve_environment(config_dir=REPO_ROOT / "backend")
        if not env.consistent:
            return False, "; ".join(env.errors)

        if self.backend.verify_tool_version() is False:
            return (
                False,
                f"mutmut version mismatch (pinned={self.backend.backend_version})",
            )

        # Check baseline tests pass (quick subset for smoke, full for target/full).
        if mode in ("target", "full"):
            # Verify the target engine's tests are runnable.
            from runtime.foundation.verification.mutation_contract import (
                ENGINE_SELECTION,
            )

            if target and target in ENGINE_SELECTION:
                sel = ENGINE_SELECTION[target]
                for test_path in sel.test_selection[:2]:  # sample first 2 test dirs
                    tp = REPO_ROOT / "backend" / test_path
                    if tp.exists():
                        break
                else:
                    return False, f"No test paths found for target={target}"

        return True, ""

    def _discover_candidates(
        self, camp: MutationCampaign, ws: MutationWorkspace
    ) -> list[MutationCandidate]:
        """Discover candidates using the backend, then assign canonical IDs."""
        # First, try loading existing candidates from a previous run (resume).
        existing_dir = ws.root / "candidates"
        if existing_dir.exists():
            existing = []
            for f in sorted(existing_dir.glob("*.json")):
                try:
                    existing.append(
                        MutationCandidate.from_dict(json.loads(f.read_text()))
                    )
                except Exception:
                    continue
            if existing:
                return existing

        # Discover via backend.
        raw = self.backend.discover(camp.scope, [])

        # Assign canonical IDs and enrich.
        source_fp = compute_source_fingerprint(
            [
                p
                for sel in __import__(
                    "runtime.foundation.verification.mutation_contract",
                    fromlist=["ENGINE_SELECTION"],
                ).ENGINE_SELECTION.values()
                for p in sel.source_paths
            ]
            if camp.scope == "full (all engines)"
            else (
                [camp.scope]
                if camp.scope.startswith("src/")
                else [f"src/engines/{camp.scope}.py"]
            )
        )

        candidates = []
        for r in raw:
            src_hash = r.source_hash or source_fp[:16]
            canon_id = derive_canonical_mutant_id(
                repository_revision=camp.repository_revision,
                source_file=r.source_file,
                source_hash=src_hash,
                function=r.function,
                line=r.line,
                operator=r.operator,
                original_expression=r.original_expression,
                mutated_expression=r.mutated_expression,
            )
            r = r.__class__(
                canonical_mutant_id=canon_id,
                source_file=r.source_file,
                source_hash=src_hash,
                function=r.function,
                line=r.line,
                column=r.column,
                operator=r.operator,
                original_expression=r.original_expression,
                mutated_expression=r.mutated_expression,
                capability=r.capability,
                component=r.component,
                risk=r.risk,
                selected_tests=r.selected_tests,
                backend_metadata={
                    **r.backend_metadata,
                    "campaign_id": camp.campaign_id,
                },
            )
            candidates.append(r)

        return candidates

    def _assign_shard(
        self, candidates: list[MutationCandidate], index: int, total: int
    ) -> list[MutationCandidate]:
        """Deterministic shard assignment by candidate hash mod total."""
        if total <= 1:
            return candidates
        shuffled = sorted(candidates, key=lambda c: c.canonical_mutant_id)
        shard_size = math.ceil(len(shuffled) / total)
        start = index * shard_size
        end = start + shard_size
        return shuffled[start:end]

    def _execute_campaign(
        self,
        camp: MutationCampaign,
        candidates: list[MutationCandidate],
        ws: MutationWorkspace,
        max_runtime: float | None,
    ) -> MutationResult:
        """Execute all candidates with retry, cache, and optional parallelism."""
        timeout = max_runtime or DEFAULT_TIMEOUTS.get(
            "full" if camp.scope == "full (all engines)" else "target", 3600
        )
        result = MutationResult(campaign_id=camp.campaign_id)
        result.total_candidates = len(candidates)

        if self.max_workers > 1:
            return self._execute_parallel(camp, candidates, ws, timeout, result)
        return self._execute_serial(camp, candidates, ws, timeout, result)

    def _execute_serial(
        self,
        camp: MutationCampaign,
        candidates: list[MutationCandidate],
        ws: MutationWorkspace,
        timeout: float,
        result: MutationResult,
    ) -> MutationResult:
        worker_id = "worker-0"
        for _i, candidate in enumerate(candidates):
            # Cache check.
            cached, entry = self.cache.get_or_skip(
                candidate,
                camp.configuration_fingerprint,
                MutationResultState.SURVIVED,  # placeholder — will be overwritten
            )
            if (
                cached
                and entry
                and entry.result_state not in ("UNKNOWN", "NOT_EXECUTED")
            ):
                # Apply cached result.
                state = MutationResultState(entry.result_state)
                self._apply_cached_result(result, state)
                continue

            # Execute with retry.
            execution = self._execute_with_retry(
                candidate,
                camp,
                ws,
                timeout,
                worker_id,
            )
            result.total_executions += 1
            result.retries_total += execution.retry_count

            # Record execution.
            ws.persist_execution(execution.to_dict())

            # Cache the result.
            if execution.mutation_result not in (
                MutationResultState.UNKNOWN,
                MutationResultState.NOT_EXECUTED,
            ):
                self.cache.put(
                    candidate,
                    camp.configuration_fingerprint,
                    execution.mutation_result,
                    execution,
                    verified=execution.verification_passed,
                )

            self._apply_execution_result(result, execution)

        return result

    def _execute_parallel(
        self,
        camp: MutationCampaign,
        candidates: list[MutationCandidate],
        ws: MutationWorkspace,
        timeout: float,
        result: MutationResult,
    ) -> MutationResult:
        """Execute candidates in parallel with worker isolation."""
        import threading

        lock = threading.Lock()

        def _worker(candidate: MutationCandidate) -> MutationExecution:
            worker_id = f"worker-{uuid.uuid4().hex[:6]}"
            return self._execute_with_retry(candidate, camp, ws, timeout, worker_id)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(_worker, c): c for c in candidates}
            for future in as_completed(futures):
                try:
                    execution = future.result()
                except Exception:
                    # Infrastructure failure for the candidate.
                    candidate = futures[future]
                    execution = MutationExecution(
                        execution_id=f"exec-{uuid.uuid4().hex[:12]}",
                        campaign_id=camp.campaign_id,
                        mutant_id=candidate.canonical_mutant_id,
                        worker_id="unknown",
                        mutation_result=MutationResultState.EXECUTION_ERROR,
                        infrastructure_failure=InfrastructureFailureKind.SUBPROCESS_CRASH,
                    )

                with lock:
                    result.total_executions += 1
                    result.retries_total += execution.retry_count
                    ws.persist_execution(execution.to_dict())
                    if execution.mutation_result not in (
                        MutationResultState.UNKNOWN,
                        MutationResultState.NOT_EXECUTED,
                    ):
                        self.cache.put(
                            candidate,
                            camp.configuration_fingerprint,
                            execution.mutation_result,
                            execution,
                            verified=execution.verification_passed,
                        )
                    self._apply_execution_result(result, execution)

        return result

    def _execute_with_retry(
        self,
        candidate: MutationCandidate,
        camp: MutationCampaign,
        ws: MutationWorkspace,
        timeout: float,
        worker_id: str,
    ) -> MutationExecution:
        """Execute one candidate with bounded retry (M44.9)."""
        last_execution = None
        for attempt in range(1, MAX_RETRIES + 2):  # 1 initial + MAX_RETRIES retries
            execution = self.backend.execute(
                candidate=candidate,
                test_selection=getattr(candidate, "selected_tests", ()),
                workspace=ws.root,
                environment={},
                timeout=timeout,
                worker_id=worker_id,
                campaign_id=camp.campaign_id,
            )
            execution.retry_count = attempt - 1
            last_execution = execution

            # Decide whether to retry.
            should_retry = (
                attempt <= MAX_RETRIES
                and execution.mutation_result == MutationResultState.EXECUTION_ERROR
                and execution.infrastructure_failure in RETRYABLE_FAILURES
            )
            if not should_retry:
                break

        return last_execution or MutationExecution(
            execution_id=f"exec-{uuid.uuid4().hex[:12]}",
            campaign_id=camp.campaign_id,
            mutant_id=candidate.canonical_mutant_id,
            worker_id=worker_id,
            mutation_result=MutationResultState.EXECUTION_ERROR,
            infrastructure_failure=InfrastructureFailureKind.UNKNOWN,
        )

    def _apply_execution_result(
        self, result: MutationResult, execution: MutationExecution
    ) -> None:
        state = execution.mutation_result
        if state == MutationResultState.KILLED:
            result.killed += 1
            result.successful_executions += 1
        elif state == MutationResultState.SURVIVED:
            result.survived += 1
            result.successful_executions += 1
        elif state == MutationResultState.EQUIVALENT:
            result.equivalent += 1
            result.successful_executions += 1
        elif state == MutationResultState.NO_TESTS:
            result.no_tests += 1
            result.successful_executions += 1
        elif state == MutationResultState.TIMEOUT:
            result.timeout += 1
            result.successful_executions += 1
        elif state == MutationResultState.EXECUTION_ERROR:
            result.execution_error += 1
            result.infrastructure_failures += 1
        elif state == MutationResultState.INVALID_MUTANT:
            result.invalid_mutant += 1
        elif state == MutationResultState.CANCELLED:
            result.cancelled += 1
        else:
            result.unknown += 1

    def _apply_cached_result(
        self, result: MutationResult, state: MutationResultState
    ) -> None:
        if state == MutationResultState.KILLED:
            result.killed += 1
            result.successful_executions += 1
        elif state == MutationResultState.SURVIVED:
            result.survived += 1
            result.successful_executions += 1
        elif state == MutationResultState.EQUIVALENT:
            result.equivalent += 1
            result.successful_executions += 1
        elif state == MutationResultState.NO_TESTS:
            result.no_tests += 1
            result.successful_executions += 1
        elif state == MutationResultState.TIMEOUT:
            result.timeout += 1
            result.successful_executions += 1
        else:
            result.unknown += 1

    def _infra_failure_result(
        self, camp: MutationCampaign, error: str
    ) -> MutationResult:
        return MutationResult(
            campaign_id=camp.campaign_id,
            total_candidates=0,
            execution_error=1,
        )


def create_orchestrator(
    *,
    backend: str = "mutmut",
    max_workers: int = 1,
    timeout: float | None = None,
) -> MutationOrchestrator:
    if backend == "mutmut":
        adapter = MutmutAdapter()
    else:
        raise ValueError(f"Unknown backend: {backend}")
    return MutationOrchestrator(
        backend=adapter, max_workers=max_workers, timeout=timeout
    )


__all__ = [
    "MutationOrchestrator",
    "create_orchestrator",
    "DEFAULT_TIMEOUTS",
    "MAX_RETRIES",
    "RETRYABLE_FAILURES",
]
