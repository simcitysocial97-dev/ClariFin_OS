"""
Verification Orchestrator — Program 7B

Deterministic verification runtime that automatically plans, executes,
and reports verification based on changed files.

The orchestrator never performs dependency analysis itself.
It consumes:
- CrossLayerImpactPlanner (Program 7A) for dependency chain enrichment
- VerificationPlanner for verification planning
- VerificationProfiles for deterministic task expansion
- EvidenceAggregator for evidence collection
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.verification.executor import Executor
from runtime.foundation.verification.models import (
    ExecutionResult as ExecutionResultModel,
    VerificationPlan,
    VerificationScope,
    VerificationStatus,
    VerificationSummary,
)
from runtime.foundation.verification.profiles import VerificationProfile, get_profile
from runtime.foundation.verification.planner import VerificationPlanner, PlanningContext
from runtime.foundation.verification.registry import UNMAPPED
from runtime.system.evidence.aggregator import EvidenceAggregator

VERIFICATION_CACHE_PATH = Path("runtime/generated/verification-cache.json")
VERIFICATION_REPORT_PATH = Path("runtime/generated/verification-report.md")


def _find_repo_root() -> Path:
    candidates = [
        Path(__file__).resolve().parents[5],
        Path.cwd(),
    ]
    for candidate in candidates:
        if (candidate / "backend" / "pyproject.toml").exists() or (
            candidate / "runtime"
        ).exists():
            return candidate
    return Path.cwd()


def _filter_changed_files(files: list[str]) -> list[str]:
    """Filter out generated, cache, and binary artifacts."""
    return [
        f
        for f in files
        if not f.startswith("runtime/generated/")
        and not f.startswith("node_modules/")
        and not f.startswith(".pytest_cache/")
        and not f.startswith("__pycache__/")
        and not f.startswith("frontend/node_modules/")
        and not f.endswith(".pyc")
    ]


def _default_branch() -> str | None:
    """Best-effort resolution of the repository default branch ref."""
    repo_root = _find_repo_root()
    for cand in ("origin/main", "origin/develop", "main", "develop"):
        try:
            r = subprocess.run(
                ["git", "rev-parse", "--verify", cand],
                capture_output=True,
                text=True,
                cwd=str(repo_root),
                timeout=10,
            )
        except Exception:
            continue
        if r.returncode == 0 and r.stdout.strip():
            return cand
    return None


def _merge_base_with_default() -> str | None:
    """Return the merge-base SHA of HEAD and the default branch, if resolvable."""
    default = _default_branch()
    if not default:
        return None
    repo_root = _find_repo_root()
    try:
        r = subprocess.run(
            ["git", "merge-base", "HEAD", default],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
    except Exception:
        return None
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    return None


def _resolve_base_ref() -> str | None:
    """Determine the git reference to diff against.

    Priority:
    1. Explicit override via ``VERIFICATION_BASE_REF``.
    2. GitHub Actions PR: ``GITHUB_BASE_REF`` (the PR base branch).
    3. Push / other CI events: the merge-base of HEAD with the default
       branch, so the branch's actual changes are detected. Using the
       branch ref itself (``refs/heads/X...``) yields an empty diff because
       HEAD already equals that ref locally.
    4. Local: merge-base of current branch and origin/main.
    """
    import os

    base_ref = os.environ.get("VERIFICATION_BASE_REF")
    if base_ref:
        return base_ref

    gh_base = os.environ.get("GITHUB_BASE_REF")
    if gh_base:
        return gh_base

    gh_event = os.environ.get("GITHUB_EVENT_NAME")
    gh_sha = os.environ.get("GITHUB_SHA")
    gh_ref = os.environ.get("GITHUB_REF")

    if gh_event == "push":
        mb = _merge_base_with_default()
        if mb:
            return mb
        if gh_ref:
            return f"{gh_ref}..."
        return None
    if gh_sha and gh_event != "push":
        mb = _merge_base_with_default()
        if mb:
            return mb
        return f"{gh_sha}..."

    return None


def _collect_changed_files() -> list[str]:
    repo_root = _find_repo_root()
    base_ref = _resolve_base_ref()

    files: list[str] = []

    def _run_diff(args: list[str]) -> str:
        result = subprocess.run(
            ["git", "diff", "--name-only", *args],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout
        return ""

    def _run_diff_three_dot(base: str) -> str:
        """Three-dot diff: changes on HEAD side since merge-base with base."""
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout
        return ""

    def _resolve_remote_ref(ref: str) -> str:
        """Resolve a ref to a form usable by git diff, fetching from origin if needed."""
        for candidate in (ref, f"origin/{ref}"):
            check = subprocess.run(
                ["git", "rev-parse", "--verify", "--quiet", candidate],
                capture_output=True,
                text=True,
                cwd=str(repo_root),
                timeout=5,
            )
            if check.returncode == 0 and check.stdout.strip():
                return candidate
        fetch_attempt = subprocess.run(
            ["git", "fetch", "origin", ref],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=30,
        )
        if fetch_attempt.returncode == 0:
            return f"origin/{ref}"
        return ref

    if base_ref is not None:
        resolved = _resolve_remote_ref(base_ref)
        combined = _run_diff_three_dot(resolved)
        diff_files = [f.strip() for f in combined.splitlines() if f.strip()]
    else:
        combined = _run_diff(["HEAD"])
        diff_files = [f.strip() for f in combined.splitlines() if f.strip()]

    untracked_result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        timeout=10,
    )
    untracked_files = (
        [f.strip() for f in untracked_result.stdout.splitlines() if f.strip()]
        if untracked_result.returncode == 0
        else []
    )

    files = _filter_changed_files(diff_files + untracked_files)
    return files


def _get_current_commit() -> str:
    repo_root = _find_repo_root()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _is_git_available() -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def _current_branch() -> str:
    """Current branch name, or ``"unknown"``.

    Mirrors :func:`_get_current_commit`: never raises, never blocks a run. An
    unavailable branch is recorded as ``"unknown"`` rather than omitted, so the manifest
    schema stays stable.
    """
    repo_root = _find_repo_root()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


@dataclass(frozen=True, slots=True)
class VerificationReport:
    profile: str
    changed_files: list[str]
    blast_radius: dict[str, Any]
    plan: VerificationPlan
    results: list[ExecutionResultModel]
    summary: VerificationSummary
    dependency_chains: list[dict[str, Any]]
    evidence_files: list[str]
    recommendations: list[str]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_markdown(self) -> str:
        lines: list[str] = []
        lines.append("# Verification Report")
        lines.append("")
        lines.append(f"**Profile:** {self.profile}")
        lines.append(f"**Generated:** {self.generated_at}")
        lines.append(f"**Overall Status:** {self.summary.overall_status.value}")
        lines.append("")

        lines.append("## Changed Files")
        lines.append("")
        if self.changed_files:
            for f in self.changed_files:
                lines.append(f"- `{f}`")
        else:
            lines.append("No changed files detected.")
        lines.append("")

        lines.append("## Blast Radius")
        lines.append("")
        if self.blast_radius:
            for key, value in self.blast_radius.items():
                lines.append(f"- **{key}**: {value}")
        else:
            lines.append("No blast radius data available.")
        lines.append("")

        lines.append("## Verification Plan")
        lines.append("")
        lines.append(f"- **Plan ID:** {self.plan.id}")
        lines.append(f"- **Scope:** {self.plan.scope.value}")
        lines.append(f"- **Targets:** {len(self.plan.targets)}")
        lines.append(f"- **Steps:** {len(self.plan.steps)}")
        lines.append(f"- **Estimated Duration:** {self.plan.estimated_duration_seconds}s")
        lines.append("")

        lines.append("## Tasks Executed")
        lines.append("")
        lines.append("| Task ID | Name | Status | Duration |")
        lines.append("|---------|------|--------|----------|")
        for result in self.results:
            lines.append(
                f"| {result.task_id} | {result.command[:60]} | {result.status.value} | {result.duration_seconds:.1f}s |"
            )
        lines.append("")

        lines.append("## Results Summary")
        lines.append("")
        lines.append(f"- **Passed:** {self.summary.passed}")
        lines.append(f"- **Failed:** {self.summary.failed}")
        lines.append(f"- **Skipped:** {self.summary.skipped}")
        lines.append(f"- **Total Duration:** {self.summary.duration_seconds:.1f}s")
        lines.append("")

        lines.append("## Dependency Chains (Program 7A)")
        lines.append("")
        if self.dependency_chains:
            for chain in self.dependency_chains:
                source = chain.get("source", "unknown")
                engine = chain.get("engine", "unknown")
                lines.append(f"### {source}")
                lines.append(f"- Engine: {engine}")
                services = chain.get("services", [])
                if services:
                    lines.append(f"- Services: {', '.join(services)}")
                endpoints = chain.get("endpoints", [])
                if endpoints:
                    lines.append(f"- Endpoints: {', '.join(endpoints[:5])}")
                capabilities = chain.get("capabilities", [])
                if capabilities:
                    lines.append(f"- Capabilities: {', '.join(capabilities)}")
                tests = chain.get("tests", [])
                if tests:
                    lines.append(f"- Tests: {len(tests)} affected")
                lines.append("")
        else:
            lines.append("No dependency chains available (Program 7A cross-layer map not loaded).")
            lines.append("")

        lines.append("## Evidence Files")
        lines.append("")
        if self.evidence_files:
            for ef in self.evidence_files:
                lines.append(f"- `{ef}`")
        else:
            lines.append("No evidence files generated.")
        lines.append("")

        lines.append("## Recommendations")
        lines.append("")
        if self.recommendations:
            for rec in self.recommendations:
                lines.append(f"- {rec}")
        else:
            lines.append("No recommendations.")
        lines.append("")

        return "\n".join(lines)

    def save_markdown(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(), encoding="utf-8")


class VerificationOrchestrator:
    """
    Verification Orchestrator — Program 7B.

    Responsibilities:
    1. collect_changed_files() — detects changed files via git diff
    2. CrossLayerImpactPlanner.analyze() — dependency chain enrichment (Program 7A)
    3. VerificationPlanner.plan() — deterministic verification planning
    4. execute() — runs verification tasks
    5. EvidenceAggregator.aggregate() — collects evidence
    6. Generates VerificationReport

    The orchestrator never performs dependency analysis itself.
    It always consumes CrossLayerImpactPlanner for that concern.
    """

    def __init__(
        self,
        profile: VerificationProfile | None = None,
        repo_root: Path | None = None,
        map_path: Path | None = None,
    ):
        self._profile = profile or get_profile("quick")
        self._repo_root = repo_root or _find_repo_root()
        self._planner = VerificationPlanner()
        self._executor = Executor(repo_root=self._repo_root)
        self._aggregator = EvidenceAggregator(self._repo_root)
        self._map_path = map_path
        self._changed_files: list[str] = []
        self._cross_layer_report: Any | None = None
        self._plan: VerificationPlan | None = None
        self._results: list[ExecutionResultModel] = []
        self._report: VerificationReport | None = None

    @property
    def changed_files(self) -> list[str]:
        return list(self._changed_files)

    @property
    def plan(self) -> VerificationPlan | None:
        return self._plan

    @property
    def results(self) -> list[ExecutionResultModel]:
        return list(self._results)

    @property
    def report(self) -> VerificationReport | None:
        return self._report

    def collect_changed_files(self) -> list[str]:
        """Collect changed files using git diff."""
        if _is_git_available():
            files = _collect_changed_files()
        else:
            files = []

        self._changed_files = files
        return files

    def analyze_cross_layer(self) -> Any:
        """Run CrossLayerImpactPlanner.analyze() from Program 7A.

        Uses ``self._map_path`` if provided (test-injection seam); otherwise
        falls back to the canonical architecture provider.
        """
        from runtime.foundation.verification.planner.planner import (
            CrossLayerImpactPlanner,
        )

        planner = CrossLayerImpactPlanner(map_path=self._map_path)
        if not self._changed_files:
            self._cross_layer_report = planner.analyze_cross_layer_impact([])
        else:
            self._cross_layer_report = planner.analyze_cross_layer_impact(
                self._changed_files
            )
        return self._cross_layer_report

    def generate_plan(self, scope: VerificationScope | None = None) -> VerificationPlan:
        """Generate a verification plan using VerificationPlanner.

        GAP-002 fix: the blast-radius scopes computed by
        CrossLayerImpactPlanner (impacted capabilities, frontend/UI,
        contracts, runtime) are fed into the planning context so that
        verification selection is driven by actual cross-layer impact
        rather than path-prefix heuristics alone.
        """
        target_scope = scope or self._profile.scope

        changed_capabilities: list[str] = []
        changed_endpoints: list[str] = []
        blast_scopes: list[VerificationScope] = []

        if self._cross_layer_report is not None:
            impact = self._cross_layer_report
            changed_capabilities = list(impact.affected_capabilities)
            changed_endpoints = list(impact.affected_endpoints)
            blast_scopes = self._derive_scopes_from_impact(impact)

        context = PlanningContext(
            changed_files=self._changed_files,
            changed_capabilities=changed_capabilities,
            changed_endpoints=changed_endpoints,
            requested_scope=target_scope,
            force_scope=target_scope,
            include_dependencies=True,
            include_dependents=False,
            max_depth=3,
            blast_radius_scopes=tuple(blast_scopes),
        )

        self._plan = self._planner.plan(context)
        return self._plan

    @staticmethod
    def _derive_scopes_from_impact(impact: Any) -> list[VerificationScope]:
        """Derive additional verification scopes from the cross-layer impact report.

        Maps impact signals to the verification scopes those signals imply,
        regardless of the originally requested profile scope. This is the
        mechanism by which a backend DTO change can escalate to frontend
        verification.
        """
        scopes: list[VerificationScope] = []

        has_frontend = bool(
            impact.affected_capabilities
            or impact.affected_pages
            or impact.affected_components
            or impact.affected_view_models
            or impact.affected_mappers
            or impact.affected_routers
            or impact.affected_endpoints
        )
        if has_frontend:
            scopes.append(VerificationScope.FRONTEND)
            scopes.append(VerificationScope.CONTRACTS)

        if impact.affected_endpoints or impact.affected_routers:
            scopes.append(VerificationScope.CONTRACTS)

        if impact.affected_engines or impact.affected_services:
            scopes.append(VerificationScope.BACKEND)

        return scopes

    def execute(self) -> list[ExecutionResultModel]:
        """Execute all tasks from the verification plan."""
        if self._plan is None:
            raise RuntimeError("No plan generated. Call generate_plan() first.")

        self._results = []
        for step in self._plan.steps:
            if step.command is None:
                result = ExecutionResultModel(
                    task_id=step.id,
                    command=step.workflow or step.script or "no-op",
                    status=VerificationStatus.SKIPPED,
                    exit_code=0,
                    duration_seconds=0.0,
                    stdout_path="",
                    stderr_path="",
                    error="No command configured for this step",
                    # VEA-2 Phase 2 (M3): identity survives even a skipped step, so the
                    # manifest can still report why the step existed.
                    unit_id=step.unit_id,
                    provenance=step.provenance,
                )
                self._results.append(result)
                continue

            exec_result = self._executor.execute(step.command)
            model_result = ExecutionResultModel(
                task_id=step.id,
                command=step.command,
                status=exec_result.status,
                exit_code=exec_result.exit_code,
                duration_seconds=exec_result.duration_seconds,
                stdout_path=exec_result.stdout_path,
                stderr_path=exec_result.stderr_path,
                error=exec_result.error,
                # VEA-2 Phase 2 (M3): copy identity and provenance verbatim from the
                # step. This is the plan → execution link of the identity spine; it is a
                # copy, never a re-derivation, so it cannot drift from the plan.
                unit_id=step.unit_id,
                provenance=step.provenance,
            )
            self._results.append(model_result)

        self.write_run_manifest()

        return self._results

    def write_run_manifest(self, path: Path | None = None) -> Path | None:
        """Emit the per-run manifest that joins planning to execution.

        VEA-2 Phase 2 (M3). The manifest is the durable join-key artifact consumed by
        M5/M6 attribution. Before it existed there was no artifact anywhere that
        connected a planned verification unit to an executed command, which is why
        Phase 1.5 attribution had to be hand-fed from manually parsed logs.

        Units with no mapping decision are recorded as ``UNMAPPED`` and additionally
        collected into a top-level ``unmapped`` list — they are reported, never silently
        dropped.

        Returns the manifest path, or ``None`` if nothing has been executed.
        """
        if not self._results:
            return None

        manifest_path = path or (
            self._repo_root
            / "runtime"
            / "generated"
            / "evidence"
            / "run-manifest.json"
        )

        steps_by_id = {}
        if self._plan is not None:
            steps_by_id = {step.id: step for step in self._plan.steps}

        entries: list[dict[str, Any]] = []
        unmapped: list[dict[str, Any]] = []

        for result in self._results:
            step = steps_by_id.get(result.task_id)
            contributing = list(
                (result.provenance or {}).get("contributing_units") or []
            )
            if not contributing and result.unit_id:
                contributing = [result.unit_id]

            unit_id = result.unit_id or UNMAPPED
            entry = {
                "step_id": result.task_id,
                "unit_id": unit_id,
                "contributing_units": contributing,
                "command": result.command,
                "exit_code": result.exit_code,
                "status": result.status.value,
                "duration_seconds": result.duration_seconds,
                "stdout_path": result.stdout_path,
                "stderr_path": result.stderr_path,
                "workflow": step.workflow if step else None,
                "script": step.script if step else None,
                "provenance": result.provenance or {},
            }
            entries.append(entry)

            if unit_id == UNMAPPED:
                unmapped.append(
                    {
                        "step_id": result.task_id,
                        "command": result.command,
                        "reason": (
                            "no UNIT_TO_WORKFLOW mapping decision resolved for the "
                            "owning registry workflow"
                        ),
                    }
                )

        manifest = {
            "schema": "run-manifest/v1",
            "commit": _get_current_commit(),
            "branch": _current_branch(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "profile": self._profile.name if self._profile else None,
            "steps": entries,
            "unmapped": unmapped,
        }

        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest_path

    def aggregate_evidence(self) -> Any:
        """Aggregate evidence using EvidenceAggregator."""
        evidence_dir = self._repo_root / "runtime" / "generated" / "verification"
        if evidence_dir.exists():
            return self._aggregator.aggregate(evidence_dir)
        return self._aggregator.aggregate(self._repo_root / "runtime" / "generated")

    def generate_report(self) -> VerificationReport:
        """Generate a unified verification report."""
        if self._plan is None:
            raise RuntimeError("No plan generated. Call generate_plan() first.")
        if not self._results:
            raise RuntimeError("No results available. Call execute() first.")

        passed = sum(1 for r in self._results if r.status.value == "passed")
        failed = sum(1 for r in self._results if r.status.value == "failed")
        skipped = sum(1 for r in self._results if r.status.value == "skipped")
        total_duration = sum(r.duration_seconds for r in self._results)

        overall_status = (
            VerificationStatus.FAILED
            if failed > 0
            else VerificationStatus.PASSED
        )

        dependency_chains: list[dict[str, Any]] = []
        if self._cross_layer_report is not None:
            dependency_chains = (
                self._cross_layer_report.dependency_chains
                if hasattr(self._cross_layer_report, "dependency_chains")
                else []
            )

        blast_radius: dict[str, Any] = {}
        if self._cross_layer_report is not None:
            blast_radius = {
                "affected_engines": getattr(
                    self._cross_layer_report, "affected_engines", []
                ),
                "affected_services": getattr(
                    self._cross_layer_report, "affected_services", []
                ),
                "affected_capabilities": getattr(
                    self._cross_layer_report, "affected_capabilities", []
                ),
                "affected_tests": getattr(
                    self._cross_layer_report, "affected_tests", []
                ),
            }

        evidence_files: list[str] = []
        evidence_dir = self._repo_root / "runtime" / "generated" / "verification"
        if evidence_dir.exists():
            for f in evidence_dir.rglob("*"):
                if f.is_file() and f.name not in (
                    "plan.json",
                    "acceptance_planner.py",
                ):
                    evidence_files.append(str(f.relative_to(self._repo_root)))

        recommendations = self._generate_recommendations()

        summary = VerificationSummary(
            profile=self._profile.name,
            total_tasks=len(self._results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=total_duration,
            report_path=str(VERIFICATION_REPORT_PATH),
            cache_path=str(VERIFICATION_CACHE_PATH),
            changed_files=self._changed_files,
            dependency_chains=dependency_chains,
            recommendations=recommendations,
            overall_status=overall_status,
        )

        self._report = VerificationReport(
            profile=self._profile.name,
            changed_files=self._changed_files,
            blast_radius=blast_radius,
            plan=self._plan,
            results=self._results,
            summary=summary,
            dependency_chains=dependency_chains,
            evidence_files=evidence_files,
            recommendations=recommendations,
        )

        return self._report

    def _generate_recommendations(self) -> list[str]:
        recommendations: list[str] = []
        for result in self._results:
            if result.status.value == "failed":
                recommendations.append(
                    f"Investigate failing task: {result.command[:80]}"
                )
        if self._cross_layer_report is not None:
            affected_engines = getattr(
                self._cross_layer_report, "affected_engines", []
            )
            if affected_engines:
                recommendations.append(
                    f"Review changes in affected engines: {', '.join(affected_engines)}"
                )
        return recommendations

    def run(self, scope: VerificationScope | None = None) -> VerificationReport:
        """Run the full verification pipeline."""
        self.collect_changed_files()
        self.analyze_cross_layer()
        self.generate_plan(scope=scope)
        self.execute()
        self.aggregate_evidence()
        return self.generate_report()


def run_verification(profile_name: str = "quick") -> VerificationReport:
    """Convenience function to run verification with a named profile."""
    profile = get_profile(profile_name)
    orchestrator = VerificationOrchestrator(profile=profile)
    return orchestrator.run(scope=profile.scope)