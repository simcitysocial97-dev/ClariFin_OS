# runtime/foundation/verification/capability_discovery.py
#
# M9-C51 — Deterministic Capability Discovery (M51.3 / M51.4 / M51.8).
#
# Given a problem type and optional inputs, return the canonical existing
# capability to use, with exact command, prerequisites, expected evidence,
# and next step. No parallel architecture is created; the resolver
# consumes the catalog built by capability_catalog.py and the C48/C50
# infrastructure directly where applicable.
#
# Problem types (C51.3 closed vocabulary):
#   changed_file | failing_test | mutation_survivor | coverage_drop |
#   workflow_failure | quality_failure | proposed_change | stale_evidence |
#   unknown_failure
#
# For each problem type, the resolver returns:
#   1. Recommended capability (from the catalog)
#   2. Exact command
#   3. Required inputs
#   4. Prerequisite capabilities
#   5. Expected evidence produced
#   6. Next capability after completion
#   7. Reason for selection
#   8. Alternatives (if ambiguity exists)
#   9. Escalation behavior when no safe capability exists

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

from runtime.foundation.verification.capability_catalog import (
    PROBLEM_CHANGED_FILE,
    PROBLEM_COVERAGE_DROP,
    PROBLEM_MUTATION_SURVIVOR,
    PROBLEM_PROPOSED_CHANGE,
    PROBLEM_QUALITY_FAILURE,
    PROBLEM_STALE_EVIDENCE,
    PROBLEM_TEST_FAILURE,
    PROBLEM_UNKNOWN_FAILURE,
    PROBLEM_WORKFLOW_FAILURE,
    get_capability_catalog,
)

# ---------------------------------------------------------------------------
# Discovery result model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Result of a capability discovery query."""

    problem_type: str
    decision: str  # "DISCOVERED" | "NO_CANONICAL_CAPABILITY"
    recommended_capability: str = ""
    command: str = ""
    required_inputs: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    expected_evidence: list[str] = field(default_factory=list)
    next_capability: str = ""
    reason: str = ""
    alternatives: list[str] = field(default_factory=list)
    escalation: str = ""  # When no safe capability exists
    bypass_warning: str = ""  # Anti-pattern warning if applicable
    resolved_blast_radius: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Bypass risk classification (M51.8)
# ---------------------------------------------------------------------------


class BypassVerdict(str):
    CANONICAL_PATH = "CANONICAL_PATH"
    SUBOPTIMAL_PATH = "SUBOPTIMAL_PATH"
    UNSAFE_BYPASS = "UNSAFE_BYPASS"
    NO_CANONICAL_CAPABILITY = "NO_CANONICAL_CAPABILITY"


#: Closed action-kind vocabulary for bypass risk analysis.
_ACTION_DIRECT_TEST_EDIT = "direct_test_edit"
_ACTION_DIRECT_TEST_RUN = "direct_test_run"
_ACTION_DIRECT_TOOL_RUN = "direct_tool_run"
_ACTION_EVIDENCE_REUSE = "evidence_reuse"
_ACTION_DIRECT_RERUN = "direct_rerun"
_ACTION_ENGINE_ONLY = "engine_only"
_ACTION_FULL_CAMPAIGN = "full_campaign"
_ACTION_NO_ACTION = "no_action"

_BYPASS_RULES: tuple[tuple[str, str, str, str], ...] = (
    # (problem_type, action_kind, verdict, reason)
    (
        PROBLEM_MUTATION_SURVIVOR,
        _ACTION_DIRECT_TEST_EDIT,
        BypassVerdict.UNSAFE_BYPASS,
        (
            "Mutation survivor requires durable intel classification before "
            "any test writing. Direct test edit bypasses survivor-intel and "
            "may introduce equivalent mutants or false fixes."
        ),
    ),
    (
        PROBLEM_CHANGED_FILE,
        _ACTION_DIRECT_TEST_RUN,
        BypassVerdict.SUBOPTIMAL_PATH,
        (
            "Changed production file should route through blast-radius "
            "first to identify transitive/shared impact. Direct pytest "
            "may miss transitively affected capabilities."
        ),
    ),
    (
        PROBLEM_COVERAGE_DROP,
        _ACTION_DIRECT_TOOL_RUN,
        BypassVerdict.SUBOPTIMAL_PATH,
        (
            "Coverage drop requires measurement-truth record before reuse. "
            "Raw `coverage run` bypasses the authoritative record."
        ),
    ),
    (
        PROBLEM_WORKFLOW_FAILURE,
        _ACTION_DIRECT_RERUN,
        BypassVerdict.SUBOPTIMAL_PATH,
        (
            "Workflow failure requires failure semantics classification "
            "before rerun. Direct rerun may repeat an infra timeout."
        ),
    ),
    (
        PROBLEM_STALE_EVIDENCE,
        _ACTION_EVIDENCE_REUSE,
        BypassVerdict.UNSAFE_BYPASS,
        (
            "Stale evidence must NOT be reused per C47 governing constraint. "
            "Reuse invalidates certification from incomplete evidence."
        ),
    ),
    (
        PROBLEM_CHANGED_FILE,
        _ACTION_ENGINE_ONLY,
        BypassVerdict.UNSAFE_BYPASS,
        (
            "Shared infrastructure changes require blast-radius expansion. "
            "Engine-only validation ignores transitive impact."
        ),
    ),
    (
        PROBLEM_UNKNOWN_FAILURE,
        _ACTION_NO_ACTION,
        BypassVerdict.NO_CANONICAL_CAPABILITY,
        (
            "No canonical capability identified for this unknown failure. "
            "Escalate to integrity audit + manual review."
        ),
    ),
)


def classify_bypass(problem_type: str, action_kind: str) -> tuple[str, str]:
    """Classify a proposed action against the canonical path.

    Returns (verdict, reason). Unknown combinations default to SUBOPTIMAL_PATH
    with a conservative explanation.
    """
    for pt, ak, verdict, reason in _BYPASS_RULES:
        if pt == problem_type and ak == action_kind:
            return verdict, reason
    return BypassVerdict.SUBOPTIMAL_PATH, (
        f"Action {action_kind!r} for problem {problem_type!r} does not match "
        f"the canonical route; verify against capability-discovery."
    )


# ---------------------------------------------------------------------------
# Discovery resolver (M51.3)
# ---------------------------------------------------------------------------


class CapabilityDiscoveryService:
    """Deterministic resolver over the existing command/capability inventory."""

    def __init__(self) -> None:
        self._catalog = get_capability_catalog()

    def discover(
        self,
        problem_type: str,
        *,
        changed_files: list[str] | None = None,
        test_path: str | None = None,
        survivor_id: str | None = None,
        capability_id: str | None = None,
        engine: str | None = None,
        scope: str | None = None,
        workflow_id: str | None = None,
        error_text: str | None = None,
        measurement_record_path: str | None = None,
    ) -> DiscoveryResult:
        """Resolve a problem type to the canonical capability."""

        # ── changed_file / proposed_change ────────────────────────────────
        if problem_type in (PROBLEM_CHANGED_FILE, PROBLEM_PROPOSED_CHANGE):
            primary = self._catalog.get("discover.blast-radius")
            if primary is None:
                return DiscoveryResult(
                    problem_type=problem_type,
                    decision=BypassVerdict.NO_CANONICAL_CAPABILITY,
                    escalation="Run verify.py integrity + verify.py audit for manual review.",
                )
            # Compute blast radius for provenance
            blast = {}
            if changed_files:
                try:
                    from runtime.foundation.verification.blast_radius import (
                        compute_blast_radius,
                    )

                    contract = compute_blast_radius(explicit_files=changed_files)
                    blast = contract.to_dict()
                except Exception as exc:
                    blast = {"error": str(exc)}

            return DiscoveryResult(
                problem_type=problem_type,
                decision="DISCOVERED",
                recommended_capability="discover.blast-radius",
                command=primary.command,
                required_inputs=["changed_files"],
                prerequisites=[],
                expected_evidence=["blast_radius_contract"],
                next_capability="plan.execution-plan",
                reason=(
                    "Production changes must pass through C50 blast radius "
                    "before execution (certified path)."
                ),
                alternatives=[
                    "plan.control-plane",
                    "plan.execution-plan",
                ],
                resolved_blast_radius=blast,
            )

        # ── failing_test ──────────────────────────────────────────────────
        if problem_type == PROBLEM_TEST_FAILURE:
            if not test_path:
                return DiscoveryResult(
                    problem_type=problem_type,
                    decision="DISCOVERED",
                    command="python runtime/verify.py diagnose-failures",
                    expected_evidence=["diagnostic_report"],
                    reason="Run pipeline failure attribution to classify the test failure.",
                )
            # Try to find the owning capability via the contract registry
            from runtime.foundation.verification.capability_contract import (
                get_capability_contract_registry,
            )

            registry = get_capability_contract_registry()
            for cap in registry.get_all_contracts():
                for tm in cap.test_mappings:
                    if test_path.startswith(tm.test_path) or tm.test_path in test_path:
                        return DiscoveryResult(
                            problem_type=problem_type,
                            decision="DISCOVERED",
                            recommended_capability=f"exec.profile.{cap.id}",
                            command=f"python runtime/verify.py {cap.minimum_verification_profile or 'backend'}",
                            required_inputs=[],
                            prerequisites=[],
                            expected_evidence=["test_pass"],
                            next_capability="diagnose.forensic",
                            reason=f"Test belongs to capability {cap.id}.",
                            alternatives=["diagnose.forensic"],
                        )
            return DiscoveryResult(
                problem_type=problem_type,
                decision="DISCOVERED",
                command="python runtime/verify.py diagnose-failures",
                expected_evidence=["diagnostic_report"],
                reason="Unmapped test — attribute failure to blast radius first.",
            )

        # ── mutation_survivor ─────────────────────────────────────────────
        if problem_type == PROBLEM_MUTATION_SURVIVOR:
            from runtime.foundation.verification.survivor_intel import (
                DEFAULT_INTEL_PATH,
                load_survivor_intel,
            )

            intel_path = DEFAULT_INTEL_PATH
            intel = load_survivor_intel(intel_path)
            survivor = None
            if survivor_id:
                for s in intel.get("survivors", []):
                    if s.get("survivor_id") == survivor_id:
                        survivor = s
                        break

            if survivor:
                cap_name = survivor.get("capability", "")
                return DiscoveryResult(
                    problem_type=problem_type,
                    decision="DISCOVERED",
                    recommended_capability="strengthen.survivor-intel",
                    command=(
                        f"python runtime/verify.py strengthen-survivor "
                        f"{survivor_id}"
                    ),
                    required_inputs=["survivor_id"],
                    prerequisites=["strengthen.survivor-intel"],
                    expected_evidence=["strengthening_proposal"],
                    next_capability="measure.mutation",
                    reason=(
                        f"Survivor {survivor_id} classified as class "
                        f"{survivor.get('classification', '?')} for "
                        f"{cap_name}. Route: intel → classify → propose → validate → revalidate."
                    ),
                    alternatives=["strengthen.forensic"],
                    bypass_warning=(
                        "Anti-pattern: Do not write tests blindly against a "
                        "survivor. The canonical route is: mutation-intel → "
                        "classify → strengthen-capability → targeted revalidation."
                    ),
                )
            # Survivor not in durable intel — escalate to refresh intel first
            return DiscoveryResult(
                problem_type=problem_type,
                decision="DISCOVERED",
                recommended_capability="strengthen.survivor-intel",
                command="python runtime/verify.py mutation-intel",
                required_inputs=[],
                prerequisites=[],
                expected_evidence=["survivor_intel"],
                next_capability="strengthen.capability-pipeline",
                reason=(
                    "Survivor not found in durable intel. Run mutation-intel "
                    "to refresh the record, then strengthen-capability."
                ),
                bypass_warning=(
                    "Anti-pattern: Do not write tests without first loading "
                    "survivor-intel to check classification."
                ),
            )

        # ── coverage_drop ─────────────────────────────────────────────────
        if problem_type == PROBLEM_COVERAGE_DROP:
            scope = scope or "backend"
            return DiscoveryResult(
                problem_type=problem_type,
                decision="DISCOVERED",
                recommended_capability="measure.coverage",
                command=f"python runtime/verify.py measurement coverage {scope}",
                required_inputs=["scope"],
                prerequisites=[],
                expected_evidence=["coverage_measurement"],
                next_capability="measure.truth-report",
                reason=(
                    "Coverage regression requires fresh authoritative "
                    "measurement truth before any reuse or strengthening."
                ),
                alternatives=["measure.truth-report"],
                bypass_warning=(
                    "Anti-pattern: Do not reuse stale coverage data. Run "
                    "measurement coverage first to produce a new record."
                ),
            )

        # ── workflow_failure ──────────────────────────────────────────────
        if problem_type == PROBLEM_WORKFLOW_FAILURE:
            cmd_entry = self._catalog.get("diagnose.failure-attribution")
            if cmd_entry:
                return DiscoveryResult(
                    problem_type=problem_type,
                    decision="DISCOVERED",
                    recommended_capability="diagnose.failure-attribution",
                    command=cmd_entry.command,
                    required_inputs=[],
                    prerequisites=[],
                    expected_evidence=["diagnostic_report"],
                    next_capability="strengthen.forensic",
                    reason=(
                        "Workflow failure requires classification before "
                        "rerun. Failure semantics determine reproduction path."
                    ),
                    alternatives=["execute"],
                )
            return DiscoveryResult(
                problem_type=problem_type,
                decision="DISCOVERED",
                command="python runtime/verify.py execute --dry-run",
                expected_evidence=["execution_report"],
                reason=(
                    "Classify the workflow failure semantics first, then "
                    "reproduce locally with the matching profile."
                ),
            )

        # ── quality_failure ───────────────────────────────────────────────
        if problem_type == PROBLEM_QUALITY_FAILURE:
            # Determine which quality tool failed from error text if available
            tool = "unknown"
            if error_text:
                lower = error_text.lower()
                if "ruff" in lower:
                    tool = "ruff"
                elif "black" in lower:
                    tool = "black"
                elif "mypy" in lower:
                    tool = "mypy"
                elif "pytest" in lower or "assert" in lower:
                    tool = "pytest"
            quality_cap = f"quality.{tool}"
            entry = self._catalog.get(quality_cap)
            if entry:
                return DiscoveryResult(
                    problem_type=problem_type,
                    decision="DISCOVERED",
                    recommended_capability=quality_cap,
                    command=entry.command,
                    required_inputs=[],
                    prerequisites=[],
                    expected_evidence=[
                        entry.produces[0] if entry.produces else "lint_report"
                    ],
                    next_capability="",
                    reason=(
                        f"Quality failure for {tool} — use the canonical "
                        f"command with repository-root configuration authority."
                    ),
                    bypass_warning=(
                        f"Use the canonical {tool} command with root "
                        f"pyproject.toml config; do not run a local copy "
                        f"with ad-hoc settings."
                    ),
                )
            return DiscoveryResult(
                problem_type=problem_type,
                decision="DISCOVERED",
                command="python runtime/verify.py integrity",
                expected_evidence=["certification_report"],
                reason=(
                    "Unknown quality tool failure. Run architecture integrity "
                    "check and review configuration authority."
                ),
            )

        # ── stale_evidence ────────────────────────────────────────────────
        if problem_type == PROBLEM_STALE_EVIDENCE:
            return DiscoveryResult(
                problem_type=problem_type,
                decision="DISCOVERED",
                recommended_capability="measure.truth-report",
                command="python runtime/verify.py measurement-truth-report",
                required_inputs=[],
                prerequisites=[],
                expected_evidence=["certification_report"],
                next_capability="",
                reason=(
                    "Stale evidence cannot be reused. Re-validate measurement "
                    "truth to determine which records are authoritative-complete."
                ),
                bypass_warning=(
                    "Reuse of stale evidence violates C47 governing constraint. "
                    "Never consume partial/derived evidence for certification."
                ),
            )

        # ── unknown_failure ───────────────────────────────────────────────
        return DiscoveryResult(
            problem_type=problem_type,
            decision=BypassVerdict.NO_CANONICAL_CAPABILITY,
            command="python runtime/verify.py integrity",
            required_inputs=[],
            prerequisites=[],
            expected_evidence=["certification_report"],
            escalation=(
                "No canonical capability found. Run integrity audit and "
                "manual review. Escalate to engineering leadership if the "
                "failure persists."
            ),
            reason="Problem type not matched to any existing capability.",
        )


# ---------------------------------------------------------------------------
# CLI handler
# ---------------------------------------------------------------------------


def cmd_capability_for(argv: list[str]) -> int:
    """verify.py capability-for — deterministic problem -> capability resolver.

    Usage:
        verify.py capability-for --type changed-file [--files FILE...]
        verify.py capability-for --type failing-test [--test PATH]
        verify.py capability-for --type mutation-survivor [--survivor ID]
        verify.py capability-for --type coverage-drop [--scope SCOPE]
        verify.py capability-for --type workflow-failure [--workflow ID]
        verify.py capability-for --type quality-failure [--error TEXT]
        verify.py capability-for --type stale-evidence
        verify.py capability-for --type unknown-failure
    """
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py capability-for", add_help=False)
    parser.add_argument("--type", required=True, help="problem type")
    parser.add_argument("--files", nargs="*", default=None)
    parser.add_argument("--test", default=None)
    parser.add_argument("--survivor", default=None)
    parser.add_argument("--capability", default=None)
    parser.add_argument("--engine", default=None)
    parser.add_argument("--scope", default=None)
    parser.add_argument("--workflow", default=None)
    parser.add_argument("--record", default=None)
    parser.add_argument("--error", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    service = CapabilityDiscoveryService()
    result = service.discover(
        args.type,
        changed_files=args.files or [],
        test_path=args.test,
        survivor_id=args.survivor,
        capability_id=args.capability,
        engine=args.engine,
        scope=args.scope,
        workflow_id=args.workflow,
        error_text=args.error,
        measurement_record_path=args.record,
    )

    output = result.to_json() if args.json else _format_discovery(result)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Written to {args.out}")
    else:
        print(output)
    return 0 if result.decision == "DISCOVERED" else 1


def _format_discovery(r: DiscoveryResult) -> str:
    """Human-readable output for the operator."""
    lines = []
    lines.append("=" * 72)
    lines.append("  CAPABILITY DISCOVERY  (M9-C51)")
    lines.append("=" * 72)
    lines.append(f"  PROBLEM TYPE:      {r.problem_type}")
    lines.append(f"  DECISION:          {r.decision}")
    if r.decision == "DISCOVERED":
        lines.append("")
        lines.append("  → USE THIS CAPABILITY")
        lines.append(f"    {r.recommended_capability}")
        lines.append("")
        lines.append("  → COMMAND")
        lines.append(f"    {r.command}")
        lines.append("")
        if r.prerequisites:
            lines.append("  → PREREQUISITES")
            for p in r.prerequisites:
                lines.append(f"    • {p}")
        lines.append("")
        if r.expected_evidence:
            lines.append("  → EVIDENCE PRODUCED")
            for e in r.expected_evidence:
                lines.append(f"    • {e}")
        lines.append("")
        if r.next_capability:
            lines.append("  → NEXT STEP")
            lines.append(f"    {r.next_capability}")
        lines.append("")
        if r.reason:
            lines.append("  → REASON")
            lines.append(f"    {r.reason}")
        if r.bypass_warning:
            lines.append("")
            lines.append("  ⚠  ANTI-PATTERN WARNING")
            lines.append(f"    {r.bypass_warning}")
    else:
        lines.append("")
        lines.append("  → ESCALATION")
        lines.append(f"    {r.escalation}")
    lines.append("")
    if r.alternatives:
        lines.append("  ALTERNATIVES:")
        for a in r.alternatives:
            lines.append(f"    ~ {a}")
    lines.append("=" * 72)
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(cmd_capability_for(sys.argv[1:]))


def cmd_bypass_audit(argv: list[str]) -> int:
    """verify.py bypass-audit — analyze bypass risk for example scenarios."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py bypass-audit", add_help=False)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    from runtime.foundation.verification.capability_discovery import classify_bypass

    scenarios = [
        ("mutation_survivor", "direct_test_edit", "UNSAFE_BYPASS"),
        ("changed_file", "direct_test_run", "SUBOPTIMAL_PATH"),
        ("coverage_drop", "direct_tool_run", "SUBOPTIMAL_PATH"),
        ("workflow_failure", "direct_rerun", "SUBOPTIMAL_PATH"),
        ("stale_evidence", "evidence_reuse", "UNSAFE_BYPASS"),
        ("changed_file", "engine_only", "UNSAFE_BYPASS"),
        ("unknown_failure", "no_action", "NO_CANONICAL_CAPABILITY"),
    ]

    results = []
    for problem, action, expected in scenarios:
        verdict, reason = classify_bypass(problem, action)
        results.append(
            {
                "problem_type": problem,
                "action": action,
                "expected": expected,
                "verdict": verdict,
                "reason": reason,
                "match": verdict == expected,
            }
        )

    output = {"scenarios": results}
    if args.json:
        import json

        print(json.dumps(output, indent=2))
    else:
        print("BYPASS RISK ANALYSIS (M9-C51)")
        print("=" * 60)
        for scenario in results:
            status = "OK" if scenario.get("match") else "MISMATCH"
            prob_type: str = str(scenario.get("problem_type", ""))
            act: str = str(scenario.get("action", ""))
            exp: str = str(scenario.get("expected", ""))
            verd: str = str(scenario.get("verdict", ""))
            reas: str = str(scenario.get("reason", ""))
            line1 = f"[{status}] {prob_type} + {act}"
            line2 = f"  Expected: {exp}"
            line3 = f"  Got:      {verd}"
            line4 = f"  Reason:   {reas[:70]}"
            print(line1)
            print(line2)
            print(line3)
            print(line4)
    return 0
