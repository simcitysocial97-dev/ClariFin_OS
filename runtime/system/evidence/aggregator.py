"""Evidence Aggregator — combines all evidence artifacts into a summary."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .collectors.coverage import CoverageCollector, CoverageEvidence
from .collectors.mutation import MutationCollector, MutationEvidence
from .collectors.test_results import TestResultCollector, TestResultEvidence
from .collectors.contract import ContractCollector, ContractEvidence


@dataclass
class EvidenceSummary:
    summary_id: str = ""
    generated_at: str = ""
    commit: str = ""
    branch: str = ""
    verification_plan: str = "selective"
    overall_status: str = "pass"
    backend: dict[str, Any] = field(default_factory=dict)
    attention_needed: list[dict] = field(default_factory=list)
    ai_context: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def to_markdown(self) -> str:
        return self._format_markdown()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())

    def save_markdown(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._format_markdown())

    def _format_markdown(self) -> str:
        lines: list[str] = []
        commit_short = self.commit[:7] if self.commit else "unknown"
        lines.append(f"## Verification Evidence — {self.branch} — {commit_short}")
        lines.append("")
        lines.append(f"**Status:** {self.overall_status}")
        lines.append(f"**Plan:** {self.verification_plan}")
        lines.append(f"**Generated:** {self.generated_at}")
        lines.append("")

        backend = self.backend
        lines.append("### Test Results")
        lines.append("")

        ut = backend.get("unit_tests", {})
        pt = backend.get("property_tests", {})
        ct = backend.get("contract_tests", {})

        lines.append("| Check | Status | Details |")
        lines.append("|-------|--------|---------|")

        ut_status = ut.get("status", "unknown")
        ut_detail = f"passed={ut.get('passed', 0)}, failed={ut.get('failed', 0)}"
        lines.append(f"| Unit Tests | {ut_status} | {ut_detail} |")

        pt_status = pt.get("status", "unknown")
        pt_detail = f"passed={pt.get('passed', 0)}, counterexamples={pt.get('counterexamples_found', 0)}"
        lines.append(f"| Property Tests | {pt_status} | {pt_detail} |")

        ct_status = ct.get("status", "unknown")
        ct_detail = f"endpoints={ct.get('endpoints_tested', 0)}, failures={ct.get('failures_found', 0)}"
        lines.append(f"| Contract Tests | {ct_status} | {ct_detail} |")

        lines.append("")

        mut = backend.get("mutation", {})
        if mut:
            lines.append("### Mutation Scores")
            lines.append("")
            lines.append("| Engine | Score | Status |")
            lines.append("|--------|-------|--------|")
            for engine, data in mut.items():
                score = data.get("score_pct", 0.0)
                status = data.get("status", "unknown")
                emoji = "🟢" if status == "pass" else "🔴" if status == "below_target" else "🟡"
                lines.append(f"| {engine} | {score}% | {emoji} {status} |")
            lines.append("")

        cov = backend.get("coverage", {})
        if cov:
            lines.append("### Coverage")
            lines.append("")
            lines.append(f"- Overall: {cov.get('overall_pct', 0):.1f}%")
            lines.append(f"- Engines: {cov.get('engines_pct', 0):.1f}%")
            delta = cov.get("delta_from_last", "")
            if delta:
                lines.append(f"- Delta: {delta}")
            lines.append("")

        attention = self.attention_needed
        if attention:
            lines.append("### Needs Attention")
            lines.append("")
            for item in attention:
                atype = item.get("type", "unknown")
                details = item.get("details", "")
                action = item.get("action", "")
                lines.append(f"- **{atype}**: {details}")
                lines.append(f"  - Action: {action}")
            lines.append("")
        else:
            lines.append("### Needs Attention")
            lines.append("")
            lines.append("No issues found.")
            lines.append("")

        lines.append("---")
        lines.append("Full evidence: `summary.json` (downloaded as CI artifact)")
        lines.append("")

        return "\n".join(lines)


class EvidenceAggregator:
    """Aggregates evidence artifacts from a CI run into a summary."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    @classmethod
    def from_artifact_directory(cls, path: Path) -> EvidenceSummary:
        agg = cls(path.parent.parent if path.is_file() else path)
        return agg.aggregate(path)

    def aggregate(
        self, evidence_dir: Path
    ) -> EvidenceSummary:
        coverage_evidence, coverage_collected = self._collect_coverage(evidence_dir)
        mutation_evidence = self._collect_mutation(evidence_dir)
        test_evidence = self._collect_test_results(evidence_dir)
        contract_evidence = self._collect_contract(evidence_dir)
        property_evidence = self._collect_property_tests(evidence_dir)

        backend: dict[str, Any] = {}

        backend["unit_tests"] = {
            "status": self._test_status(test_evidence),
            "passed": test_evidence.passed,
            "failed": test_evidence.failed,
            "duration_seconds": test_evidence.duration_seconds,
        }

        backend["property_tests"] = {
            "status": self._test_status(property_evidence),
            "passed": property_evidence.passed,
            "counterexamples_found": property_evidence.failed + property_evidence.error,
        }

        backend["contract_tests"] = {
            "status": contract_evidence.status,
            "endpoints_tested": contract_evidence.endpoints_tested,
            "failures_found": len(contract_evidence.failures),
        }

        backend["coverage"] = {
            "overall_pct": coverage_evidence.overall_pct,
            "engines_pct": self._avg_engine_coverage(coverage_evidence),
            "delta_from_last": "0.0",
        }
        backend["coverage"]["collected"] = coverage_collected

        backend_mutation: dict[str, Any] = {}
        for engine, data in mutation_evidence.per_engine.items():
            score = data.get("score_pct", 0.0) if isinstance(data, dict) else 0.0
            killed = data.get("killed", 0) if isinstance(data, dict) else 0
            survived = data.get("survived", 0) if isinstance(data, dict) else 0
            status = "pass" if score >= 60.0 else "below_target"
            backend_mutation[engine] = {
                "score_pct": score,
                "killed": killed,
                "survived": survived,
                "status": status,
            }

        backend["mutation"] = backend_mutation if backend_mutation else {
            "overall": {
                "score_pct": mutation_evidence.score_pct,
                "killed": mutation_evidence.killed,
                "survived": mutation_evidence.survived,
                "status": "not_run" if mutation_evidence.killed + mutation_evidence.survived == 0 else ("pass" if mutation_evidence.score_pct >= 60.0 else "below_target"),
            }
        }

        attention = self._build_attention(backend, mutation_evidence)

        evidence_collected = (
            coverage_collected
            or (mutation_evidence.killed + mutation_evidence.survived > 0)
            or (test_evidence.passed + test_evidence.failed + test_evidence.error + test_evidence.skipped > 0)
            or (contract_evidence.status != "not_run")
            or (property_evidence.passed + property_evidence.failed + property_evidence.error + property_evidence.skipped > 0)
        )

        if not evidence_collected:
            overall_status = "not_run"
        elif attention:
            overall_status = "attention_needed"
        else:
            overall_status = "pass"

        summary = EvidenceSummary(
            summary_id=f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            commit=self._get_git_ref("HEAD"),
            branch=self._get_branch(),
            overall_status=overall_status,
            backend=backend,
            attention_needed=attention,
            ai_context={
                "ready": True,
                "context_file": "runtime/generated/evidence/ai_context.json",
                "note": "Program 8 will consume this for automated remediation planning",
            },
        )

        return summary

    def _collect_coverage(
        self, evidence_dir: Path
    ) -> tuple[CoverageEvidence, bool]:
        coverage_dir = evidence_dir / "coverage"
        if coverage_dir.exists():
            for json_file in coverage_dir.rglob("*.json"):
                if json_file.name == "coverage.json":
                    collector = CoverageCollector(self.workspace_root)
                    return collector.collect(json_file), True

        repo_cov_dir = evidence_dir / "backend" / "tests" / "generated"
        for json_file in sorted((repo_cov_dir).rglob("coverage.json")) if repo_cov_dir.exists() else []:
            collector = CoverageCollector(self.workspace_root)
            return collector.collect(json_file), True

        collector = CoverageCollector(self.workspace_root)
        return collector.collect(), False

    def _collect_mutation(
        self, evidence_dir: Path
    ) -> MutationEvidence:
        mutation_dir = evidence_dir / "mutation"
        if mutation_dir.exists():
            for txt_file in mutation_dir.glob("*-results.txt"):
                collector = MutationCollector(self.workspace_root)
                return collector.collect(txt_file)

        collector = MutationCollector(self.workspace_root)
        return collector.collect()

    def _collect_test_results(
        self, evidence_dir: Path
    ) -> TestResultEvidence:
        candidate_files = []
        test_dir = evidence_dir / "test-results"
        if test_dir.exists():
            candidate_files.extend(sorted(test_dir.rglob("*.xml")))

        repo_test_dir = evidence_dir / "backend" / "tests" / "generated"
        if repo_test_dir.exists():
            for name in ("junit.xml", "test-results.xml", "pytest-results.xml"):
                f = repo_test_dir / name
                if f.exists():
                    candidate_files.append(f)

        for xml_file in candidate_files:
            collector = TestResultCollector(self.workspace_root)
            return collector.collect(xml_file)

        collector = TestResultCollector(self.workspace_root)
        return collector.collect()

    def _collect_property_tests(
        self, evidence_dir: Path
    ) -> TestResultEvidence:
        candidate_files = []
        repo_test_dir = evidence_dir / "backend" / "tests" / "generated"
        if repo_test_dir.exists():
            for name in ("junit-property.xml", "property-results.xml"):
                f = repo_test_dir / name
                if f.exists():
                    candidate_files.append(f)

        prop_dir = evidence_dir / "property-results"
        if prop_dir.exists():
            candidate_files.extend(sorted(prop_dir.rglob("*.xml")))

        for xml_file in candidate_files:
            collector = TestResultCollector(self.workspace_root)
            return collector.collect(xml_file)

        return TestResultEvidence(
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _collect_contract(
        self, evidence_dir: Path
    ) -> ContractEvidence:
        contract_dir = evidence_dir / "contract"
        if contract_dir.exists():
            for json_file in contract_dir.rglob("*.json"):
                collector = ContractCollector(self.workspace_root)
                return collector.collect(json_file)

        collector = ContractCollector(self.workspace_root)
        return collector.collect()

    def _test_status(self, evidence: TestResultEvidence) -> str:
        if evidence.failed > 0 or evidence.error > 0:
            return "fail"
        if evidence.passed > 0:
            return "pass"
        return "unknown"

    def _avg_engine_coverage(
        self, evidence: CoverageEvidence
    ) -> float:
        if not evidence.per_engine:
            return evidence.overall_pct
        vals = list(evidence.per_engine.values())
        return round(sum(vals) / len(vals), 1) if vals else evidence.overall_pct

    def _build_attention(
        self, backend: dict[str, Any], mutation_evidence: MutationEvidence
    ) -> list[dict]:
        attention: list[dict] = []

        mut = backend.get("mutation", {})
        for engine, data in mut.items():
            if engine == "overall":
                continue
            if isinstance(data, dict) and data.get("status") == "below_target":
                attention.append(
                    {
                        "type": "mutation_below_target",
                        "engine": engine,
                        "score": data.get("score_pct", 0.0),
                        "target": 60.0,
                        "surviving_mutants": data.get("survived", 0),
                        "action": f"Review surviving mutants for {engine} in mutation evidence artifact",
                    }
                )

        ut = backend.get("unit_tests", {})
        if ut.get("failed", 0) > 0:
            attention.append(
                {
                    "type": "unit_test_failures",
                    "count": ut["failed"],
                    "action": "Fix failing unit tests before merging",
                }
            )

        pt = backend.get("property_tests", {})
        if pt.get("status") == "fail":
            attention.append(
                {
                    "type": "property_test_failures",
                    "counterexamples": pt.get("counterexamples_found", 0),
                    "action": "Address property test counterexamples before merging",
                }
            )

        cov = backend.get("coverage", {})
        if cov.get("collected", False) and cov.get("overall_pct", 0) < 40.0:
            attention.append(
                {
                    "type": "low_coverage",
                    "overall_pct": cov.get("overall_pct", 0),
                    "action": "Add tests to increase overall coverage above 40%",
                }
            )

        contract = backend.get("contract_tests", {})
        if contract.get("status") == "fail":
            attention.append(
                {
                    "type": "contract_test_failures",
                    "failures": contract.get("failures_found", 0),
                    "action": "Fix API contract violations before merging",
                }
            )

        return attention

    def _get_git_ref(self, ref: str) -> str:
        import subprocess
        try:
            result = subprocess.run(
                ["git", "rev-parse", ref],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def _get_branch(self) -> str:
        gh_ref = os.environ.get("GITHUB_REF_NAME")
        if gh_ref:
            return gh_ref
        import subprocess
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            branch = result.stdout.strip()
            if branch and branch != "HEAD":
                return branch
        except Exception:
            pass
        return "unknown"