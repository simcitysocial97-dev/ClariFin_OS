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

# Program 7A: Cross-layer dependency chain enrichment
# Program 13.3: chains come from the canonical architecture provider, never
# from the legacy cross-layer-map artifact. This override is an explicit
# test-injection seam only; it is ``None`` at runtime.
CROSS_LAYER_MAP_PATH: Path | None = None

# VEA-2 Phase 2, M5. Mirrors the verification registry's UNMAPPED sentinel.
# Defined locally rather than imported so the evidence system stays decoupled from
# the verification package. Kept identical in value so the two are joinable, and
# asserted equal by test.
UNMAPPED_SENTINEL = "UNMAPPED"


def _load_cross_layer_map() -> dict[str, Any]:
    """Provider-derived chain map used for dependency chain enrichment."""
    try:
        if CROSS_LAYER_MAP_PATH is not None and CROSS_LAYER_MAP_PATH.exists():
            with open(CROSS_LAYER_MAP_PATH, encoding="utf-8") as f:
                return json.load(f)
        from runtime.foundation.architecture.chains import get_chain_map

        return get_chain_map()
    except Exception:
        return {}


def _find_dependency_chain(
    test_name: str, cross_map: dict[str, Any]
) -> dict[str, Any] | None:
    """Find the dependency chain for a failing test.

    Matches test names against cross-layer map entries by related keywords.
    Returns the chain info or None.
    """
    if not cross_map:
        return None

    test_lower = test_name.lower()

    for engine_file, chain in cross_map.items():
        # Check if test name matches engine name
        engine_parts = engine_file.split("/")
        for part in engine_parts:
            if part.endswith("_engine"):
                engine_name = part.replace("_engine", "").lower()
                if engine_name in test_lower:
                    return {
                        "engine": engine_file,
                        "chain": chain,
                        "engine_name": engine_name,
                    }

        # Check if test name matches capability name
        for cap in chain.get("capabilities", []):
            cap_lower = cap.lower().replace("use", "").replace("capability", "")
            if cap_lower in test_lower:
                return {
                    "engine": engine_file,
                    "chain": chain,
                    "engine_name": engine_parts[-1].replace(".py", ""),
                }

    return None


@dataclass
class EvidenceSummary:
    summary_id: str = ""
    generated_at: str = ""
    commit: str = ""
    branch: str = ""
    verification_plan: str = "selective"
    overall_status: str = "pass"
    backend: dict[str, Any] = field(default_factory=dict)
    # --- VEA-2 Phase 2, M5 -------------------------------------------------------
    # E-2: the frontend was previously structurally unrepresentable here. The sole
    # occurrence of "frontend" in this module was a synthesized `suggested_layer`
    # string, so a red frontend build could not be expressed at all — and therefore
    # could not force a non-pass overall status.
    #
    # Populated from the M4 `frontend-verification/v1` evidence. Empty dict means
    # "no frontend evidence was found", which resolves to `not_run` — never `pass`.
    frontend: dict[str, Any] = field(default_factory=dict)
    # E-3: failures keyed by verification unit, joined via the M3 run manifest.
    # Each entry carries unit_id, phase, path, diagnostic and provenance, so a
    # failure can be traced back to the impact analysis that selected the unit.
    unit_failures: list[dict[str, Any]] = field(default_factory=list)
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

        # VEA-2 Phase 2, M5 (E-2): the frontend is now representable, so it is
        # reported. Previously a red frontend build left no trace in this report.
        frontend = self.frontend
        if frontend:
            lines.append("### Frontend")
            lines.append("")
            lines.append(f"**Status:** {frontend.get('overall_status', 'unknown')}")
            lines.append("")
            lines.append("| Phase | Status | Exit | Duration |")
            lines.append("|-------|--------|------|----------|")
            for name, phase in frontend.get("phases", {}).items():
                lines.append(
                    f"| {name} | {phase.get('status', 'unknown')} | "
                    f"{phase.get('exit_code')} | {phase.get('duration_seconds')}s |"
                )
            lines.append("")

        # VEA-2 Phase 2, M5 (E-3): failures joined to the unit that selected them.
        if self.unit_failures:
            lines.append("### Failures by Verification Unit")
            lines.append("")
            lines.append("| Unit | Layer | Phase | Diagnostic |")
            lines.append("|------|-------|-------|------------|")
            for failure in self.unit_failures:
                lines.append(
                    f"| {failure.get('unit_id', UNMAPPED_SENTINEL)} "
                    f"| {failure.get('layer', '')} "
                    f"| {failure.get('phase', '')} "
                    f"| {failure.get('diagnostic', '')} |"
                )
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

        # --- VEA-2 Phase 2, M5 ------------------------------------------------
        # E-2: represent the frontend structurally, so a red frontend cannot be
        # reported as an overall pass.
        frontend = self._collect_frontend(evidence_dir)
        # E-3: join failures to the units that justified running them.
        unit_failures = self._collect_unit_failures(evidence_dir, frontend)

        frontend_failed = frontend.get("overall_status") == "fail"
        if frontend_failed:
            failing_phases = ", ".join(
                name
                for name, phase in frontend.get("phases", {}).items()
                if phase.get("status") == "fail"
            )
            attention = attention + [
                {
                    "type": "frontend_verification_failed",
                    "details": f"failing frontend phase(s): {failing_phases}",
                    "action": (
                        "inspect runtime/generated/evidence/frontend/<phase>.log; "
                        "run `python runtime/verify.py diagnose-failures` to check "
                        "whether the failure lies inside this change's blast radius"
                    ),
                }
            ]

        evidence_collected = (
            coverage_collected
            or (mutation_evidence.killed + mutation_evidence.survived > 0)
            or (test_evidence.passed + test_evidence.failed + test_evidence.error + test_evidence.skipped > 0)
            or (contract_evidence.status != "not_run")
            or (property_evidence.passed + property_evidence.failed + property_evidence.error + property_evidence.skipped > 0)
            or bool(frontend)
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
            frontend=frontend,
            unit_failures=unit_failures,
            attention_needed=attention,
            ai_context={
                "ready": True,
                "context_file": "runtime/generated/evidence/ai_context.json",
                "note": "Program 8 will consume this for automated remediation planning",
            },
        )

        return summary

    # ------------------------------------------------------------------
    # VEA-2 Phase 2, M5 — frontend representation (E-2) and unit keying (E-3)
    #
    # NOTE: `_find_chain_for_failure()` / `_find_dependency_chain()` below are the
    # known E-4 keyword-attribution defect. They are deliberately left in place and
    # untouched, and nothing added here calls or extends them. Replacing them with
    # graph traversal is owned by Phase 3 (see VEA_BACKLOG.md BL-003).
    # ------------------------------------------------------------------

    def _frontend_evidence_path(self, evidence_dir: Path) -> Path | None:
        """Locate `frontend-verification.json`, or return None.

        Probes the evidence directory being aggregated and the canonical location
        the M4 script writes to. Returns ``None`` rather than fabricating a result
        when nothing is found.
        """
        candidates = [
            evidence_dir / "frontend" / "frontend-verification.json",
            evidence_dir / "frontend-verification.json",
            self.workspace_root
            / "runtime/generated/evidence/frontend/frontend-verification.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _collect_frontend(self, evidence_dir: Path) -> dict[str, Any]:
        """Build the frontend section from `frontend-verification/v1` evidence.

        Returns an empty dict when no evidence exists. The caller maps that to
        `not_run`; it is never silently upgraded to `pass`.
        """
        path = self._frontend_evidence_path(evidence_dir)
        if path is None:
            return {}

        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

        phases: dict[str, Any] = {}
        for phase in data.get("phases", []):
            name = phase.get("phase")
            if not name:
                continue
            phases[name] = {
                "status": phase.get("status", "unknown"),
                "exit_code": phase.get("exit_code"),
                "duration_seconds": phase.get("duration_seconds"),
                "log": phase.get("log", ""),
            }

        return {
            "schema": data.get("schema", ""),
            "overall_status": data.get("overall_status", "unknown"),
            "unit_id": data.get("unit_id") or "",
            "phases": phases,
            "evidence_path": str(path),
        }

    def _load_run_manifest(self, evidence_dir: Path) -> dict[str, Any]:
        """Load the M3 run manifest, which supplies the unit_id join key."""
        candidates = [
            evidence_dir / "run-manifest.json",
            evidence_dir.parent / "run-manifest.json",
            self.workspace_root / "runtime/generated/evidence/run-manifest.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                try:
                    return json.loads(candidate.read_text())
                except (json.JSONDecodeError, OSError):
                    return {}
        return {}

    def _collect_unit_failures(
        self, evidence_dir: Path, frontend: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Build the unit-keyed failure list (E-3).

        The join key is `unit_id`, taken from the M3 manifest — never from string
        matching against a command or a test name. A failure that cannot be joined
        to a unit is recorded with ``unit_id: "UNMAPPED"`` and is reported, not
        dropped.
        """
        manifest = self._load_run_manifest(evidence_dir)
        entries_by_workflow: dict[str, dict[str, Any]] = {}
        for entry in manifest.get("steps", []):
            workflow = entry.get("workflow")
            if workflow:
                entries_by_workflow[workflow] = entry

        failures: list[dict[str, Any]] = []

        # Frontend: one failure record per failing phase.
        frontend_entry = entries_by_workflow.get("frontend", {})
        for name, phase in frontend.get("phases", {}).items():
            if phase.get("status") != "fail":
                continue
            failures.append(
                {
                    "unit_id": (
                        frontend.get("unit_id")
                        or frontend_entry.get("unit_id")
                        or UNMAPPED_SENTINEL
                    ),
                    "layer": "frontend",
                    "phase": name,
                    "path": phase.get("log", ""),
                    "diagnostic": (
                        f"frontend phase '{name}' failed "
                        f"(exit={phase.get('exit_code')})"
                    ),
                    "provenance": frontend_entry.get("provenance", {}),
                    "contributing_units": frontend_entry.get(
                        "contributing_units", []
                    ),
                }
            )

        # Backend: one failure record per failing suite phase.
        backend_summary_path = self._backend_evidence_path(evidence_dir)
        if backend_summary_path is not None:
            try:
                backend_data = json.loads(backend_summary_path.read_text())
            except (json.JSONDecodeError, OSError):
                backend_data = {}
            backend_entry = entries_by_workflow.get("backend", {})
            for phase in backend_data.get("phases", []):
                if phase.get("status") != "fail":
                    continue
                failures.append(
                    {
                        "unit_id": (
                            backend_data.get("unit_id")
                            or backend_entry.get("unit_id")
                            or UNMAPPED_SENTINEL
                        ),
                        "layer": "backend",
                        "phase": phase.get("phase", ""),
                        "path": phase.get("log", ""),
                        "diagnostic": (
                            f"backend suite '{phase.get('phase')}' failed "
                            f"(exit={phase.get('exit_code')})"
                        ),
                        "provenance": backend_entry.get("provenance", {}),
                        "contributing_units": backend_entry.get(
                            "contributing_units", []
                        ),
                    }
                )

        return failures

    def _backend_evidence_path(self, evidence_dir: Path) -> Path | None:
        candidates = [
            evidence_dir / "backend" / "backend-verification.json",
            evidence_dir / "backend-verification.json",
            self.workspace_root
            / "runtime/generated/evidence/backend/backend-verification.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

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

        # Program 7A: Cross-layer dependency chain enrichment
        cross_map = _load_cross_layer_map()

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
            chain = self._find_chain_for_failure("unit_tests", cross_map)
            attention.append(
                {
                    "type": "unit_test_failures",
                    "count": ut["failed"],
                    "action": "Fix failing unit tests before merging",
                    **chain,
                }
            )

        pt = backend.get("property_tests", {})
        if pt.get("status") == "fail":
            chain = self._find_chain_for_failure("property_tests", cross_map)
            attention.append(
                {
                    "type": "property_test_failures",
                    "counterexamples": pt.get("counterexamples_found", 0),
                    "action": "Address property test counterexamples before merging",
                    **chain,
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
            chain = self._find_chain_for_failure("contract_tests", cross_map)
            attention.append(
                {
                    "type": "contract_test_failures",
                    "failures": contract.get("failures_found", 0),
                    "action": "Fix API contract violations before merging",
                    **chain,
                }
            )

        return attention

    def _find_chain_for_failure(
        self, failure_type: str, cross_map: dict[str, Any]
    ) -> dict[str, Any]:
        """Find dependency chain info for a failing test type.

        Returns dict with dependency_chain, likely_origin, likely_consumer, suggested_layer keys.
        """
        if not cross_map:
            return {}

        # Try to find the most relevant engine chain
        for engine_file, chain in cross_map.items():
            services = chain.get("services", [])
            capabilities = chain.get("capabilities", [])
            endpoints = chain.get("endpoints", [])

            # Determine likely origin and consumer based on failure type
            likely_origin = engine_file
            likely_consumer = None
            if capabilities:
                likely_consumer = capabilities[0]

            if failure_type == "contract_tests" and endpoints:
                likely_origin = endpoints[0]
                likely_consumer = capabilities[0] if capabilities else "API schema"
            elif failure_type == "unit_tests" and services:
                likely_consumer = services[0]

            # Build dependency chain string
            dep_chain = [engine_file]
            if services:
                dep_chain.extend(services[:1])
            if endpoints:
                dep_chain.append(endpoints[0])
            if capabilities:
                dep_chain.append(capabilities[0])
            if chain.get("mappers"):
                dep_chain.append(chain["mappers"][0])
            if chain.get("viewModels"):
                dep_chain.append(chain["viewModels"][0])
            if chain.get("workspace"):
                dep_chain.append(chain["workspace"][0])
            if chain.get("components"):
                dep_chain.append(chain["components"][0])

            # Suggested layer: the lowest-level layer that should be fixed first
            # For DTO changes, this is usually the schema layer
            suggested_layer = None
            if capabilities:
                cap_name = capabilities[0].lower().replace("use", "").replace("capability", "").strip()
                suggested_layer = f"frontend/lib/schemas/{cap_name}s.ts"

            return {
                "dependency_chain": dep_chain,
                "likely_origin": likely_origin,
                "likely_consumer": likely_consumer,
                "suggested_layer": suggested_layer,
            }

        return {}

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