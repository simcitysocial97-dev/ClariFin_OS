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
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_RECORD = "runtime/generated/m9-c42.28/forensic-execution-record.json"


def _mutmut_tests_for(survivor_id: str, backend_dir: Path | None = None) -> list[str]:
    """Query mutmut's built-in `tests-for-mutant` for the covering test
    surface of a surviving mutant. Returns the list of test node ids.

    Supplements our survivor catalog with mutmut's own result analysis
    (the exact test surface that currently fails to detect the mutant).
    Silent on any error (the analysis is best-effort enrichment).
    """
    import subprocess

    cwd = backend_dir or (REPO_ROOT / "backend")
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "mutmut",
                "tests-for-mutant",
                survivor_id,
            ],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return []
        nodes = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line and "::" in line:
                nodes.append(line)
        return nodes
    except Exception:
        return []


# ---------------------------------------------------------------------------
# forensic-diagnose
# ---------------------------------------------------------------------------


def run_forensic_diagnose(argv: list[str]) -> int:

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
            default_population,
            default_prior_measurements,
            reconcile,
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
            build_ci_bindings,
            load_ci_evidence,
            validate_and_decide,
            verification_bindings,
        )

        records = load_ci_evidence(args.ci_evidence)
        sem_by_task = {}
        for b in verification_bindings(build_ci_bindings()):
            if b.semantics:
                sem_by_task.setdefault(b.command, b.semantics)
        entries = []
        for r in records:
            # Resolve this record's command semantics so observational /
            # infra-health evidence (reusable_evidence=False) is correctly
            # excluded from reuse by ci_reuse_decision (they are NOT reusable
            # measurement). Semantics is wired through to validate_and_decide.
            sem = next(
                (
                    s
                    for _, s in sem_by_task.items()
                    if s.verification_task == r.verification_task
                ),
                None,
            )
            _, decision = validate_and_decide(r, _context_for(r), semantics=sem)
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
        _git_sha,
        collect_repo_fingerprints,
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

    raw = json.loads(Path(args.survivors).read_text())
    survivors = list(raw if isinstance(raw, list) else [raw])

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
    )
    from runtime.foundation.verification.strengthening import (
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
        from dataclasses import dataclass
        from dataclasses import field as _field

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
        from runtime.foundation.verification.evidence_planner import (
            PlannedTask,
        )
        from runtime.foundation.verification.executor_pipeline import (
            adapt_mutation_task,
            execute_mutation_task,
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


# ---------------------------------------------------------------------------
# strengthen-discover
# ---------------------------------------------------------------------------


def run_strengthen_discover(argv: list[str]) -> int:
    """Discover survivors from canonical classification / mutation artifacts
    and emit a clean evidence list suitable for subsequent strengthen-analyze /
    strengthen-propose calls."""

    parser = argparse.ArgumentParser(
        prog="verify.py strengthen-discover", add_help=False
    )
    parser.add_argument(
        "--from-classification",
        default=str(
            REPO_ROOT / "runtime/generated/m9-c44/survivor-classification.json"
        ),
        help="Path to survivor-classification.json (aggregate summary)",
    )
    parser.add_argument(
        "--from-attribution",
        default=str(
            REPO_ROOT / "runtime/generated/m9-c44/survivor-capability-attribution.json"
        ),
        help="Path to survivor-capability-attribution.json",
    )
    parser.add_argument(
        "--from-survivors",
        default=str(
            REPO_ROOT / "backend/tests/generated/mutation/mutation-survivors.json"
        ),
        help="Path to mutation-survivors.json (per-function survivor data)",
    )
    parser.add_argument(
        "--from-intel",
        default=str(
            REPO_ROOT / "backend/tests/generated/mutation/mutation-survivor-intel.json"
        ),
        help="Preferred durable per-mutant intel (M9-C45.2). When present, "
        "per-component records with correct classification/capability are "
        "derived from it; falls back to --from-survivors / aggregators.",
    )
    parser.add_argument("--out", default=None)
    parser.add_argument(
        "--class-filter",
        nargs="*",
        default=["A"],
        help="Which classes to include (default A only)",
    )
    parser.add_argument(
        "--with-tests",
        type=int,
        default=0,
        help="Enrich the first N discovered survivors with their covering test "
        "surface (mutmut tests-for-mutant). 0 disables (default).",
    )
    args, _ = parser.parse_known_args(argv)

    class_filter = set(args.class_filter)
    discovered: list[dict] = []

    # Preferred: derive per-component survivor evidence from the durable
    # M9-C45.2 intel record (backend/tests/generated/mutation/
    # mutation-survivor-intel.json). This carries the correct component,
    # capability, A–E classification, covering tests and recommended action
    # for EVERY surviving mutant, so discovery is not behaviour_engine-only
    # and is not re-derived from a coarser per-function summary.
    intel = None
    try:
        if Path(args.from_intel).exists():
            intel = json.loads(Path(args.from_intel).read_text())
    except Exception:
        intel = None
    if intel:
        for e in intel.get("survivors", []):
            cls = str(e.get("classification", "A")).upper()
            if cls not in class_filter:
                continue
            discovered.append(
                {
                    "survivor_id": e.get("survivor_id", ""),
                    "component": e.get("component", "unknown"),
                    "capability": e.get("capability", "unknown"),
                    "location": f"{e.get('source_file', '')}:{e.get('function', '')}",
                    "mutation_operator": e.get("mutation_type", "unknown"),
                    "original_snippet": e.get("original_expression", ""),
                    "mutated_snippet": e.get("mutated_expression", ""),
                    "status": "survived",
                    "classification": cls,
                    "notes": e.get("classification_evidence", ""),
                    "covering_tests": tuple(e.get("covering_tests", ())),
                    "recommended_action": e.get("recommended_action", ""),
                }
            )

    # Legacy fallback: per-function survivor data from mutation-survivors.json
    # (used only when no durable intel is available).
    if not discovered:
        try:
            surv_data = json.loads(Path(args.from_survivors).read_text())
            entries = surv_data.get("entries", [])
            cat_to_cls: dict[str, str] = {
                "control_flow": "A",
                "arithmetic": "A",
                "comparison": "A",
                "boolean": "A",
                "default_value": "A",
                "dict_key": "A",
                "string_literal": "B",
                "numeric_literal": "B",
                "other": "B",
            }
            for e in entries:
                cat = e.get("category", "other")
                cls = cat_to_cls.get(cat, "B")
                if cls not in class_filter:
                    continue
                discovered.append(
                    {
                        "survivor_id": e.get("key", ""),
                        "component": "behaviour_engine",
                        "capability": "behaviour-analysis",
                        "location": f"src/{e.get('source_file', '')}:{e.get('function', '')}",
                        "mutation_operator": cat,
                        "original_snippet": e.get("old", ""),
                        "mutated_snippet": e.get("new", ""),
                        "status": "survived",
                        "classification": cls,
                        "notes": e.get("signature", ""),
                        "covering_tests": (),
                    }
                )
        except Exception:
            pass

    # Fallback: parse aggregate classification summary
    if not discovered:
        try:
            classifications = json.loads(Path(args.from_classification).read_text())
            attribution = json.loads(Path(args.from_attribution).read_text())
            by_comp = classifications.get("by_component", {})
            attribs = attribution.get("attributions", {})
            cls_key_map = {
                "class_a": "A",
                "a_genuine_behavioral_gap": "A",
                "class_b": "B",
                "b_equivalent": "B",
                "class_c": "C",
                "c_defensive_unreachable": "C",
                "class_d": "D",
                "d_measurement_infrastructure": "D",
                "class_e": "E",
                "e_escalation_possible_defect": "E",
            }
            for comp, stats in by_comp.items():
                for key, count in stats.items():
                    if not isinstance(count, int) or count == 0:
                        continue
                    cls = cls_key_map.get(key.lower(), key.upper())
                    if cls not in class_filter:
                        continue
                    attr = attribs.get(comp, {})
                    cap = attr.get("primary_capability", comp.replace("_", "-"))
                    for i in range(count):
                        discovered.append(
                            {
                                "survivor_id": f"{comp}-{key}-{i}",
                                "component": comp,
                                "capability": cap,
                                "location": f"src/engines/{comp}/...",
                                "mutation_operator": "unknown",
                                "original_snippet": "",
                                "mutated_snippet": "",
                                "status": "survived",
                                "classification": cls,
                                "notes": f"aggregate; {count} {key}",
                                "covering_tests": (),
                            }
                        )
        except Exception:
            pass

    # Enrich the first N survivors with mutmut's covering-test analysis
    # (tests-for-mutant). Makes proposed_test_surface evidence-derived.
    if args.with_tests and discovered:
        import os

        backend_dir = REPO_ROOT / "backend"
        prev = os.getcwd()
        for record in discovered[: args.with_tests]:
            sid = record.get("survivor_id", "")
            if not sid or "::__mutmut_" not in sid:
                continue
            try:
                tests = _mutmut_tests_for(sid, backend_dir)
            except Exception:
                tests = []
            if tests:
                record["covering_tests"] = tuple(tests)
                record["test_surface"] = sorted({t.rsplit("::", 1)[0] for t in tests})
        os.chdir(prev)

    payload = {
        "schema": "m9-strengthening-discover/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "class_filter": list(class_filter),
        "total_discovered": len(discovered),
        "by_class": {
            c: sum(1 for e in discovered if e.get("classification") == c)
            for c in class_filter
        },
        "evidence": discovered[:200],
        "full_count_note": (
            (f"Showing up to 200 of {len(discovered)} records.")
            if len(discovered) > 200
            else None
        ),
    }
    out_path = (
        Path(args.out)
        if args.out
        else REPO_ROOT / "runtime/generated/m9-c44/strengthening-discover.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    return 0


# ---------------------------------------------------------------------------
# strengthen-propose (batch — generates proposals from discover output)
# ---------------------------------------------------------------------------


def run_strengthen_propose(argv: list[str]) -> int:
    """Batch-proposes strengthened tests for all discoverable Class-A
    survivors. Accepts output of strengthen-discover as input and emits
    the canonical strengthening-proposals artifact."""

    parser = argparse.ArgumentParser(
        prog="verify.py strengthen-propose", add_help=False
    )
    parser.add_argument(
        "--discover",
        required=True,
        help="Path to strengthen-discover.json output",
    )
    parser.add_argument("--out", default=None)
    args, _ = parser.parse_known_args(argv)

    discover = json.loads(Path(args.discover).read_text())
    evidence = discover.get("evidence", [])

    proposals = []
    refusals = []
    for ev in evidence:
        from runtime.foundation.verification.strengthening import (
            SurvivorEvidence,
            generate_proposal,
        )

        s = SurvivorEvidence(
            survivor_id=ev.get("survivor_id", ""),
            component=ev.get("component", ""),
            capability=ev.get("capability", ""),
            location=ev.get("location", ""),
            mutation_operator=ev.get("mutation_operator", "unknown"),
            original_snippet=ev.get("original_snippet", ""),
            mutated_snippet=ev.get("mutated_snippet", ""),
            status=ev.get("status", "survived"),
            notes=ev.get("notes", ""),
            covering_tests=tuple(ev.get("covering_tests", ())),
        )
        out = generate_proposal(s)
        if hasattr(out, "to_dict"):
            proposals.append(out.to_dict())
        else:
            refusals.append(
                {"survivor_id": ev.get("survivor_id", ""), "reason": str(out)}
            )

    payload = {
        "schema": "m9-strengthening-proposals/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "input_count": len(evidence),
        "proposals_generated": len(proposals),
        "refusals": refusals,
        "proposals": proposals,
    }
    out_path = (
        Path(args.out)
        if args.out
        else REPO_ROOT / "runtime/generated/m9-c44/strengthening-proposals.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    return 0


# ---------------------------------------------------------------------------
# strengthen-report
# ---------------------------------------------------------------------------


def run_strengthen_report(argv: list[str]) -> int:
    """Produce a concise human-readable report on strengthening progress:
    how many proposals generated, how many accepted, how many killed,
    how many rejected/refused, and the current mutation posture."""

    parser = argparse.ArgumentParser(prog="verify.py strengthen-report", add_help=False)
    parser.add_argument(
        "--proposals",
        default=str(
            REPO_ROOT / "runtime/generated/m9-c44/strengthening-proposals.json"
        ),
    )
    parser.add_argument(
        "--validation",
        default=str(
            REPO_ROOT / "runtime/generated/m9-c44/strengthening-validation.json"
        ),
    )
    parser.add_argument(
        "--mutation-summary",
        default=str(
            REPO_ROOT / "backend/tests/generated/mutation/mutation-summary.json"
        ),
    )
    parser.add_argument("--out", default=None)
    args, _ = parser.parse_known_args(argv)

    proposals = json.loads(Path(args.proposals).read_text())
    validation = json.loads(Path(args.validation).read_text())
    summary = json.loads(Path(args.mutation_summary).read_text())

    total_proposed = proposals.get("proposals_generated", 0)
    accepted = sum(
        1
        for p in proposals.get("proposals", [])
        if p.get("status") == "accepted" or p.get("accepted") is True
    )
    rejected = proposals.get("refusals", [])
    validated = validation.get("validated_count", 0)
    killed_by_validation = validation.get("killed_count", 0)
    regression_free = validation.get("regression_free_count", 0)

    score = summary.get("mutation_score")
    killed = summary.get("killed", 0)
    survived = summary.get("survived", 0)
    generated = summary.get("mutants_generated", 0)
    exec_status = summary.get("execution_status", "UNKNOWN")

    report = {
        "schema": "m9-strengthening-report/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "strengthening_progress": {
            "proposals_generated": total_proposed,
            "accepted": accepted,
            "rejected_or_refused": len(rejected),
            "validated": validated,
            "mutants_killed_by_validation": killed_by_validation,
            "regression_free": regression_free,
        },
        "mutation_posture": {
            "score_pct": score,
            "killed": killed,
            "survived": survived,
            "generated": generated,
            "execution_status": exec_status,
            "threshold_met": score is not None and score >= 80.0,
        },
        "conclusion": (
            "STRENGTHENING_OPERATIONAL"
            if exec_status == "PASS" and score is not None
            else "INCOMPLETE"
        ),
    }
    out_path = (
        Path(args.out)
        if args.out
        else REPO_ROOT / "runtime/generated/m9-c44/strengthening-report.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


# ---------------------------------------------------------------------------
# strengthen-survivor — focused per-survivor analysis via mutmut built-ins
# ---------------------------------------------------------------------------


def run_strengthen_survivor(argv: list[str]) -> int:
    """Focused analysis of ONE surviving mutant using mutmut's built-in result
    analysis (`show` for the exact diff, `tests-for-mutant` for the covering
    test surface) supplemented with capability attribution. Aids the
    Class-A -> capability -> invariant -> test-surface chain."""

    parser = argparse.ArgumentParser(
        prog="verify.py strengthen-survivor", add_help=False
    )
    parser.add_argument(
        "survivor_id",
        help="mutmut mutant name, e.g. "
        "engines.behaviour_engine.core.x_impulsivity_score__mutmut_5",
    )
    parser.add_argument("--attribution", default=None)
    parser.add_argument("--json", action="store_true")
    args, _ = parser.parse_known_args(argv)

    import subprocess

    backend_dir = REPO_ROOT / "backend"

    def run_mutmut(*cmd: str) -> str:
        proc = subprocess.run(
            [sys.executable, "-m", "mutmut", *cmd],
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
            timeout=180,
        )
        return proc.stdout

    diff = run_mutmut("show", args.survivor_id).strip()
    tests = []
    for line in run_mutmut("tests-for-mutant", args.survivor_id).splitlines():
        line = line.strip()
        if line and "::" in line:
            tests.append(line)

    attribution: dict = {}
    if args.attribution:
        try:
            data = json.loads(Path(args.attribution).read_text())
            if isinstance(data, dict):
                attr = data.get("attributions", {})
                attribution = attr.get(args.survivor_id, {}) or {}
        except Exception:
            pass

    payload = {
        "schema": "m9-strengthening-survivor-analysis/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "survivor_id": args.survivor_id,
        "diff": diff,
        "covering_test_surface": tests,
        "capability_attribution": attribution,
        "recommended_action": (
            "Write a behavioral assertion on the covering test surface that "
            "discriminates the mutation; if a production defect is suspected, "
            "escalate for human review (Class-E)."
        ),
    }
    out_path = (
        REPO_ROOT
        / "runtime/generated/m9-c44"
        / f"survivor-analysis-{args.survivor_id.split('__mutmut_')[0].replace('.', '-')}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"# {args.survivor_id}")
        print(diff)
        print(f"\n# Covering test surface ({len(tests)} tests):")
        for t in tests:
            print(f"  {t}")
        if attribution:
            print(f"\n# Capability: {attribution.get('capability', 'unknown')}")
    return 0


__all__ = [
    "run_forensic_diagnose",
    "run_forensic_report",
    "run_strengthen_discover",
    "run_strengthen_analyze",
    "run_strengthen_propose",
    "run_strengthen_validate",
    "run_strengthen_survivor",
    "run_strengthen_report",
]
