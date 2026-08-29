"""
M9-C42.30 / C42.31 — Forensic & Strengthening CLI surface.

Commands (wired into runtime/verify.py):

    verify.py forensic-diagnose [--changed FILE ...] [--ci-evidence PATH]
               [--out PATH] [--json]
        Runs the full diagnostic chain (plan -> expand -> reconcile ->
        forensic record) WITHOUT executing mutation, feeds it through
        the Diagnostic & Forensic Agent, prints the nine-question
        report.

    verify.py forensic-report [--record PATH]
        Renders an existing canonical ForensicExecutionRecord into the
        nine-question summary (no re-planning).

    verify.py strengthen-analyze [--survivors PATH | --record PATH]
               [--out PATH]
        Classifies survivor evidence (A–E), emits bounded Class-A
        proposals and explicit B/C/D/E refusals. Never executes
        anything.

    verify.py strengthen-validate --proposal PATH [--before PATH]
               [--max-runtime N] [--stub]
        Validates ONE proposal through the C42.28 targeted execution
        bridge (never a full campaign) and compares before/after.

Every command consumes or produces canonical framework artifacts.
No command duplicates an existing one: diagnose/diagnose-failures are
the older intelligence-layer diagnostics; these commands are the
forensic-agent surface.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_RECORD = "runtime/generated/m9-c42.28/forensic-execution-record.json"


# ---------------------------------------------------------------------------
# forensic-diagnose
# ---------------------------------------------------------------------------


def run_forensic_diagnose(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py forensic-diagnose", add_help=False)
    parser.add_argument(
        "--changed",
        nargs="*",
        default=[],
        help="changed files (bypasses git detection)",
    )
    parser.add_argument(
        "--ci-evidence",
        default=None,
        help="path to persisted CI evidence records (m9-ci-evidence/v1)",
    )
    parser.add_argument("--out", default=None, help="output JSON path")
    parser.add_argument(
        "--record",
        default=DEFAULT_RECORD,
        help="existing forensic record to diagnose instead of planning",
    )
    args, _ = parser.parse_known_args(argv)

    from runtime.foundation.verification.diagnostic_agent import (
        DiagnosticForensicAgent,
    )

    if args.record and Path(args.record).exists() and not args.changed:
        record = json.loads(Path(args.record).read_text())
    else:
        from runtime.foundation.verification.evidence_planner import (
            default_planner,
        )
        from runtime.foundation.verification.executor_pipeline import (
            build_executable_plan,
            build_forensic_record,
            reconcile,
            default_population,
            default_prior_measurements,
        )

        planner = default_planner()
        plan = planner.plan(tuple(args.changed))
        executable = build_executable_plan(plan)
        # Diagnostic mode never launches mutation implicitly.
        reconciled = reconcile(
            plan,
            {},
            {m.component: m for m in default_prior_measurements()},
            default_population(),
        )
        record = build_forensic_record(plan, executable, {}, reconciled).to_dict()

    ci_correlation = None
    if args.ci_evidence:
        from runtime.foundation.verification.ci_evidence import (
            load_ci_evidence,
            validate_and_decide,
            verification_bindings,
            build_ci_bindings,
        )

        records = load_ci_evidence(args.ci_evidence)
        sem_by_task = {}
        for b in verification_bindings(build_ci_bindings()):
            if b.semantics:
                sem_by_task.setdefault(b.command, b.semantics)
        entries = []
        for r in records:
            sem = None
            for cmd_key, s in sem_by_task.items():
                if s.verification_task == r.verification_task:
                    sem = s
                    break
            _, decision = validate_and_decide(r, _context_for(r))
            entries.append(
                {
                    "record_id": r.record_id,
                    "component": r.component,
                    "executed": True,
                    "reusable": decision.reusable,
                    "disposition": decision.disposition,
                    "failure_classification": decision.failure_classification,
                    "reasons": list(decision.reasons),
                }
            )
        ci_correlation = {"records": entries}

    agent = DiagnosticForensicAgent()
    report = agent.diagnose(record, ci_correlation=ci_correlation)

    out_path = (
        Path(args.out)
        if args.out
        else (REPO_ROOT / "runtime/generated/m9-c42.30/diagnostic-report.json")
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report.to_dict(), indent=2))

    print(json.dumps(report.to_dict(), indent=2))
    verdict = report.q9_verdict["verdict"]
    return 0 if verdict in ("CERTIFIABLE",) else 2


def _context_for(record):
    from runtime.foundation.verification.ci_evidence import (
        CIRepositoryContext,
    )
    from runtime.foundation.verification.evidence_reuse import (
        c42_26_population,
    )
    from runtime.foundation.verification.executor_pipeline import (
        collect_repo_fingerprints,
        _git_sha,
    )

    comp = record.component or ""
    fps = (
        collect_repo_fingerprints(comp)
        if comp
        else collect_repo_fingerprints("credit_card_engine")
    )
    return CIRepositoryContext(
        repository_sha=_git_sha(),
        component_source_fingerprints={comp: fps.source} if comp else {},
        component_test_fingerprints={comp: fps.test} if comp else {},
        configuration_fingerprint=fps.config,
        toolchain_fingerprint=fps.toolchain,
        population_fingerprint=c42_26_population().fingerprint(),
    )


# ---------------------------------------------------------------------------
# forensic-report
# ---------------------------------------------------------------------------


def run_forensic_report(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py forensic-report", add_help=False)
    parser.add_argument("--record", default=DEFAULT_RECORD)
    parser.add_argument("--out", default=None)
    args, _ = parser.parse_known_args(argv)

    from runtime.foundation.verification.diagnostic_agent import (
        DiagnosticForensicAgent,
    )

    record = json.loads(Path(args.record).read_text())
    report = DiagnosticForensicAgent().diagnose(record)
    d = report.to_dict()

    lines = [
        "=" * 72,
        f"FORENSIC DIAGNOSTIC REPORT  ({report.source_record_id})",
        f"repository: {report.repository_sha[:12]}",
        "=" * 72,
        f"Q1  what changed      : {report.q1_what_changed['file_count']} file(s); "
        f"components={report.q1_what_changed['changed_components']}",
        f"Q2  affected          : components="
        f"{report.q2_what_is_affected['components']} capabilities="
        f"{report.q2_what_is_affected['capabilities']}",
        f"Q3  valid evidence    : reused={len(report.q3_valid_evidence['reused'])} "
        f"revalidated={len(report.q3_valid_evidence['revalidated'])} "
        f"invalidated={len(report.q3_valid_evidence['invalidated'])} "
        f"unavailable={len(report.q3_valid_evidence['unavailable'])}",
        f"Q4  required work     : {report.q4_required_execution['task_count']} task(s) "
        f"(planner-authoritative)",
        f"Q5  executed          : {report.q5_actual_execution['executed']} "
        f"failed={report.q5_actual_execution['failed']}",
        f"Q6  outcomes          : {report.q6_what_happened['by_kind']}",
        f"Q7  not tested        : reused-cover="
        f"{len(report.q7_what_was_not_tested['covered_by_reused_evidence'])} "
        f"deferred={report.q7_what_was_not_tested['deferred_components']}",
        "Q8  uncertainties     :",
    ]
    for u in report.q8_uncertainties:
        lines.append(f"     - [{u.kind}] {u.subject}: {u.detail}")
    if not report.q8_uncertainties:
        lines.append("     - none")
    lines += [
        f"Q9  VERDICT           : {report.q9_verdict['verdict']}",
        f"    rationale         : {report.q9_verdict['rationale']}",
        "-" * 72,
        "Explainability:",
    ]
    for k, v in report.explainability.to_dict().items():
        lines.append(f"  {k}: {v}")

    output = "\n".join(lines)
    print(output)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"text": output, "report": d}, indent=2))
    return 0


# ---------------------------------------------------------------------------
# strengthen-analyze
# ---------------------------------------------------------------------------


def run_strengthen_analyze(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="verify.py strengthen-analyze", add_help=False
    )
    parser.add_argument(
        "--survivors",
        required=True,
        help=(
            "JSON file with survivor evidence records "
            "(list of SurvivorEvidence dicts)"
        ),
    )
    parser.add_argument("--out", default=None)
    args, _ = parser.parse_known_args(argv)

    from runtime.foundation.verification.strengthening import (
        generate_proposal,
    )

    raw = json.loads(Path(args.survivors).read_text())
    survivors = [s for s in (raw if isinstance(raw, list) else [raw])]

    proposals = []
    refusals = []
    for s in survivors:
        out = generate_proposal_from_dict(s)
        if isinstance(out, dict):
            proposals.append(out)
        else:
            refusals.append(out.to_dict())

    payload = {
        "schema": "m9-strengthening-analysis/v1",
        "input_count": len(survivors),
        "proposals": proposals,
        "refusals": refusals,
        "policy": {
            "class_a": "bounded proposal generated",
            "class_b_c_d_e": "explicitly refused; reasons recorded",
            "automation_boundary": (
                "detect -> diagnose -> propose -> validate; production "
                "code is never modified autonomously"
            ),
        },
    }
    out_path = (
        Path(args.out)
        if args.out
        else (REPO_ROOT / "runtime/generated/m9-c42.31/strengthening-analysis.json")
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    return 0


def generate_proposal_from_dict(s: dict):
    """Build a SurvivorEvidence from a dict and classify/propose."""
    from runtime.foundation.verification.strengthening import (
        SurvivorEvidence,
        generate_proposal as _gp,
    )

    ev = SurvivorEvidence(
        survivor_id=s["survivor_id"],
        component=s["component"],
        capability=s.get("capability", s["component"].replace("_", "-")),
        location=s.get("location", ""),
        mutation_operator=s.get("mutation_operator", "unknown"),
        original_snippet=s.get("original_snippet", ""),
        mutated_snippet=s.get("mutated_snippet", ""),
        status=s.get("status", "survived"),
        notes=s.get("notes", ""),
        covering_tests=tuple(s.get("covering_tests", ())),
    )
    out = _gp(ev)
    if hasattr(out, "to_dict") and hasattr(out, "schema"):
        return out.to_dict()
    return out


# ---------------------------------------------------------------------------
# strengthen-validate
# ---------------------------------------------------------------------------


def run_strengthen_validate(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="verify.py strengthen-validate", add_help=False
    )
    parser.add_argument(
        "--proposal", required=True, help="path to a StrengtheningProposal JSON"
    )
    parser.add_argument(
        "--before",
        default=None,
        help="JSON file with before counts "
        "(default: derived from proposal evidence)",
    )
    parser.add_argument("--max-runtime", type=int, default=None)
    parser.add_argument(
        "--stub",
        action="store_true",
        help="use deterministic stub executor (tests/dry-run)",
    )
    args, _ = parser.parse_known_args(argv)

    from runtime.foundation.verification.strengthening import (
        StrengtheningProposal,
        targeted_revalidation,
    )

    pdata = json.loads(Path(args.proposal).read_text())
    proposal = StrengtheningProposal(
        schema=pdata["schema"],
        proposal_id=pdata["proposal_id"],
        component=pdata["component"],
        capability=pdata["capability"],
        source_location=pdata["source_location"],
        survivor_evidence=dict(pdata.get("survivor_evidence", {})),
        classification=pdata["classification"],
        behavioral_hypothesis=pdata["behavioral_hypothesis"],
        expected_invariant=pdata["expected_invariant"],
        proposed_test_surface=pdata["proposed_test_surface"],
        proposed_test=pdata["proposed_test"],
        reason=pdata["reason"],
        expected_mutation_discrimination=pdata["expected_mutation_discrimination"],
        regression_risk=pdata["regression_risk"],
        validation_command=pdata["validation_command"],
        acceptance_criteria=tuple(pdata["acceptance_criteria"]),
    )

    before = (
        json.loads(Path(args.before).read_text())
        if args.before
        else {"killed": 0, "generated": 0}
    )

    if args.stub:
        from dataclasses import dataclass, field as _field

        @dataclass
        class _StubResult:
            counts: dict = _field(default_factory=dict)
            mutant_statuses: dict = _field(default_factory=dict)

        sid = str((proposal.survivor_evidence or {}).get("survivor_id", ""))
        before_killed = int(before.get("killed", 0))
        before_generated = int(before.get("generated", 0))

        def executor(component: str):
            # Deterministic dry-run: the proposed test discriminates its
            # own target mutant without regressing anything else.
            return _StubResult(
                counts={
                    "generated": before_generated,
                    "killed": before_killed + 1,
                    "survived": max(0, before_generated - before_killed - 1),
                },
                mutant_statuses={sid: "killed"} if sid else {},
            )

    else:
        from runtime.foundation.verification.executor_pipeline import (
            execute_mutation_task,
            adapt_mutation_task,
        )
        from runtime.foundation.verification.evidence_planner import (
            PlannedTask,
        )

        def executor(component: str):
            planned = PlannedTask(
                task_id=f"task::mutation::{component}",
                task_kind="mutation",
                target=component,
                disposition="selected_fresh",
                cause="strengthen-validate targeted re-measurement",
            )
            fps_fps = __import__(
                "runtime.foundation.verification.executor_pipeline",
                fromlist=["collect_repo_fingerprints"],
            ).collect_repo_fingerprints(component)
            task = adapt_mutation_task(planned, fps_fps)
            return execute_mutation_task(task, max_runtime=args.max_runtime)

    outcome = targeted_revalidation(
        proposal,
        before_counts=before,
        executor=executor,
    )
    out_path = (
        REPO_ROOT
        / "runtime/generated/m9-c42.31"
        / f"revalidation-{proposal.proposal_id.split('::')[-1]}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(outcome.to_dict(), indent=2))
    print(json.dumps(outcome.to_dict(), indent=2))
    return 0 if outcome.accepted else 2


__all__ = [
    "run_forensic_diagnose",
    "run_forensic_report",
    "run_strengthen_analyze",
    "run_strengthen_validate",
]
