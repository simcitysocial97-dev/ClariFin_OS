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
from runtime.system.evidence.aggregator import EvidenceAggregator

CROSS_LAYER_MAP_PATH = Path("runtime/generated/cross-layer-map.json")
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


def _collect_changed_files() -> list[str]:
    repo_root = _find_repo_root()
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception:
        pass
    return []


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
    ):
        self._profile = profile or get_profile("quick")
        self._repo_root = repo_root or _find_repo_root()
        self._planner = VerificationPlanner()
        self._executor = Executor(repo_root=self._repo_root)
        self._aggregator = EvidenceAggregator(self._repo_root)
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
        """Run CrossLayerImpactPlanner.analyze() from Program 7A."""
        from runtime.foundation.verification.planner.planner import (
            CrossLayerImpactPlanner,
        )

        planner = CrossLayerImpactPlanner()
        if not self._changed_files:
            self._cross_layer_report = planner.analyze_cross_layer_impact([])
        else:
            self._cross_layer_report = planner.analyze_cross_layer_impact(
                self._changed_files
            )
        return self._cross_layer_report

    def generate_plan(self, scope: VerificationScope | None = None) -> VerificationPlan:
        """Generate a verification plan using VerificationPlanner."""
        target_scope = scope or self._profile.scope

        planning_context = PlanningContext(
            changed_files=self._changed_files,
            requested_scope=target_scope,
            force_scope=target_scope,
            include_dependencies=True,
            include_dependents=False,
            max_depth=3,
        )

        self._plan = self._planner.plan(planning_context)
        return self._plan

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
            )
            self._results.append(model_result)

        return self._results

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