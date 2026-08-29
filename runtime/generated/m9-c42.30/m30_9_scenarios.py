"""
M9-C42.30 — M30.x Forensic Agent scenarios (FA … FH).

Drives the real C42.27 planner / C42.28 executor bridge (with the
deterministic stub executor so no mutmut runs), produces canonical
ForensicExecutionRecords, and runs the Diagnostic & Forensic Agent on
them:

  FA — no repository change        -> reuse + derived aggregate,
                                      CERTIFIABLE, zero execution
  FB — one engine source change    -> affected identified, only required
                                      verification executed, rest reused,
                                      aggregate reconciled
  FC — test change                 -> correct test evidence invalidation;
                                      mutation fingerprints respected;
                                      no population-wide execution
  FD — verification config change  -> exact invalidation scope; no
                                      silent expansion
  FE — CI failure                  -> infrastructure vs verification
                                      distinction preserved
  FF — discovery drift             -> CERTIFICATION_BLOCKED
  FG — insufficient test surface   -> behavioral weakness diagnosed;
                                      NO automatic score-chasing;
                                      strengthening recommended
  FH — equivalent survivor         -> classified, preserved, never
                                      artificially targeted

Run with:
    .venv/bin/python runtime/generated/m9-c42.30/m30_9_scenarios.py
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c42.30"
OUT_DIR.mkdir(parents=True, exist_ok=True)

from runtime.foundation.verification.diagnostic_agent import (  # noqa: E402
    DiagnosticForensicAgent,
)
from runtime.foundation.verification.evidence_planner import (  # noqa: E402
    EvidenceAwarePlanner,
    default_planner,
)
from runtime.foundation.verification.evidence_reuse import (  # noqa: E402
    c42_24_b_measurements,
    c42_25_measurements,
    c42_26_population,
)
from runtime.foundation.verification.executor_pipeline import (  # noqa: E402
    ExecutionEvidence,
    FailureKind,
    build_executable_plan,
    build_forensic_record,
    collect_repo_fingerprints,
    reconcile,
)

_POP = c42_26_population()
_PRIOR = {m.component: m for m in c42_24_b_measurements() + c42_25_measurements()}
_AGENT = DiagnosticForensicAgent()


# ---------------------------------------------------------------------------
# Deterministic stub executor (mirrors the C42.28 scenario pattern)
# ---------------------------------------------------------------------------

def stub_execute(
    component: str,
    *,
    outcome: str = "pass",
    counts: dict | None = None,
    notes: str = "",
) -> ExecutionEvidence:
    fps = collect_repo_fingerprints(component)
    now = datetime.now(UTC).isoformat()
    fk: FailureKind | None = None
    msg = ""
    exit_code = 0
    base_counts = {"generated": 50, "killed": 45, "survived": 5,
                   "no_tests": 0, "timeout": 0, "suspicious": 0, "not_checked": 0}
    effective = dict(counts or base_counts)
    if outcome == "verification_failure":
        fk = FailureKind.VERIFICATION
        msg = "mutmut reported survived mutants beyond tolerance"
        exit_code = 2
    elif outcome == "infrastructure_failure":
        fk = FailureKind.INFRASTRUCTURE
        msg = "runner lost power mid-job"
        exit_code = -1
    elif outcome == "evidence_failure":
        fk = FailureKind.EVIDENCE
        msg = "mutation summary artifact incomplete"
        exit_code = 3
    return ExecutionEvidence(
        execution_id=f"stub-{component}-{outcome}",
        task_id=f"exec::task::mutation::{component}",
        component=component,
        capability=component.replace("_engine", "").replace("_", "-"),
        verification_kind="mutation",
        started_at=now,
        completed_at=now,
        duration_seconds=0.01,
        command=f".venv/bin/python runtime/verify.py mutation --target {component}",
        exit_code=exit_code,
        failure_kind=fk,
        failure_message=msg,
        counts=effective,
        source_fingerprint=fps.source,
        test_fingerprint=fps.test,
        config_fingerprint=fps.config,
        toolchain_fingerprint=fps.toolchain,
        repository_sha="084359346b3b",
        notes=notes,
    )


def _run_pipeline(changed_files: tuple[str, ...], *, fresh_outcomes: dict[str, dict] | None = None):
    """Plan → expand → (stub) execute → reconcile → forensic record."""
    planner = default_planner()
    plan = planner.plan(changed_files)
    executable = build_executable_plan(plan)
    fresh: dict[str, ExecutionEvidence] = {}
    for t in executable.tasks:
        spec = (fresh_outcomes or {}).get(t.component, {"outcome": "pass"})
        fresh[t.component] = stub_execute(t.component, **spec)
    reconciled = reconcile(plan, fresh, _PRIOR, _POP)
    forensic = build_forensic_record(plan, executable, fresh, reconciled)
    return plan, executable, fresh, reconciled, forensic


def _drifted_planner() -> EvidenceAwarePlanner:
    """A planner whose graph claims coverage the surface cannot reach."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_graph_inv_drift",
        REPO_ROOT / "runtime/generated/m9-c42.27/m27_2_graph_inventory.py",
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    g, _ = mod.build_graph()
    # Remove all source bindings for the cashflow capability while
    # leaving its test-surface links intact — the C42.24 shape.
    cap_key = "cap::cashflow-engine"
    broken = {
        s: tuple(c for c in caps if c != cap_key)
        for s, caps in g.source_to_capability.items()
    }
    g.source_to_capability = {s: c for s, c in broken.items() if c}
    return EvidenceAwarePlanner(g, _POP, list(_PRIOR.values()))


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def scenario_fa() -> dict:
    plan, _, fresh, reconciled, forensic = _run_pipeline(())
    report = _AGENT.diagnose(forensic.to_dict())
    v = report.q9_verdict["verdict"]
    ok = (
        len(fresh) == 0
        and len(report.q3_valid_evidence["reused"]) == 14
        and v == "CERTIFIABLE"
        and bool(reconciled.aggregate)
        and reconciled.aggregate.label == "MATHEMATICALLY_RECONCILED"
    )
    return {
        "scenario": "FA",
        "name": "no_repository_change",
        "expected": (
            "no unnecessary execution; evidence reuse; derived aggregate; "
            "certifiable"
        ),
        "executed": len(fresh),
        "reused": len(report.q3_valid_evidence["reused"]),
        "aggregate_label": reconciled.aggregate.label if reconciled.aggregate else None,
        "verdict": v,
        "pass": ok,
    }


def scenario_fb() -> dict:
    plan, _, fresh, reconciled, forensic = _run_pipeline(
        ("backend/src/engines/credit_card_engine/risk.py",),
        fresh_outcomes={"credit_card_engine": {"outcome": "pass"}},
    )
    report = _AGENT.diagnose(forensic.to_dict())
    v = report.q9_verdict["verdict"]
    agg = reconciled.aggregate.label if reconciled.aggregate else None
    ok = (
        report.q2_what_is_affected["components"] == ["credit_card"]
        and len(fresh) == 1
        and len(report.q3_valid_evidence["reused"]) == 13
        and v == "CERTIFIABLE"
        and agg == "AUTHORITATIVE_TARGETED"
    )
    return {
        "scenario": "FB",
        "name": "one_engine_source_change",
        "expected": (
            "affected component identified; only required verification "
            "executed; unaffected reused; aggregate reconciled"
        ),
        "affected": report.q2_what_is_affected["components"],
        "executed": sorted(fresh.keys()),
        "reused": len(report.q3_valid_evidence["reused"]),
        "aggregate_label": agg,
        "verdict": v,
        "pass": ok,
    }


def scenario_fc() -> dict:
    plan, _, fresh, reconciled, forensic = _run_pipeline(
        ("backend/tests/unit/engines/credit_card_engine/test_risk.py",),
        fresh_outcomes={"credit_card_engine": {"outcome": "pass"}},
    )
    report = _AGENT.diagnose(forensic.to_dict())
    v = report.q9_verdict["verdict"]
    sel = [t.disposition for t in plan.selected_tasks]
    ok = (
        len(fresh) <= 1
        and len(report.q3_valid_evidence["reused"]) >= 13
        and v == "CERTIFIABLE"
        and all(d != "selected_fresh" or t.target == "credit_card_engine"
                for t, d in zip(plan.selected_tasks, sel, strict=False))
    )
    return {
        "scenario": "FC",
        "name": "test_change",
        "expected": (
            "correct test evidence invalidation; mutation evidence "
            "handled per fingerprints; no population-wide execution"
        ),
        "selected_dispositions": [
            f"{t.target}:{t.disposition}" for t in plan.selected_tasks
        ],
        "executed": sorted(fresh.keys()),
        "reused": len(report.q3_valid_evidence["reused"]),
        "verdict": v,
        "pass": ok,
    }


def scenario_fd() -> dict:
    plan, _, fresh, reconciled, forensic = _run_pipeline(("backend/pyproject.toml",))
    report = _AGENT.diagnose(forensic.to_dict())
    v = report.q9_verdict["verdict"]
    ok = (
        len(fresh) == 0
        and len(plan.selected_tasks) == 0
        and len(report.q3_valid_evidence["reused"]) == 14
        and v == "CERTIFIABLE"
    )
    return {
        "scenario": "FD",
        "name": "verification_configuration_change",
        "expected": "exact invalidation scope; no silent expansion",
        "selected_count": len(plan.selected_tasks),
        "invalidated": report.q3_valid_evidence["invalidated"],
        "reused": len(report.q3_valid_evidence["reused"]),
        "verdict": v,
        "pass": ok,
    }


def scenario_fe() -> dict:
    """CI failure: infra vs verification distinction must survive into
    the diagnostic verdicts (machine-readable). CI evidence enters via
    the C42.29 ingestion/correlation boundary."""
    plan, _, fresh, reconciled, forensic = _run_pipeline(
        ("backend/src/engines/cashflow_engine/flow.py",),
        fresh_outcomes={"cashflow_engine": {"outcome": "verification_failure"}},
    )
    # Two CI records correlated alongside local execution: one genuine
    # verification failure, one pure infrastructure failure.
    ci_correlation = {
        "records": [
            {
                "record_id": "ci-loan-verify-fail",
                "component": "loan_engine",
                "executed": True,
                "reusable": False,
                "disposition": "invalidated_evidence_only",
                "failure_classification": "verification_failure",
                "reasons": ["exit_status=2; classified verification_failure"],
            },
            {
                "record_id": "ci-account-runner-loss",
                "component": "account_engine",
                "executed": True,
                "reusable": False,
                "disposition": "invalidated_evidence_only",
                "failure_classification": "infrastructure_failure",
                "reasons": ["runner lost power; classified infrastructure_failure"],
            },
        ]
    }
    report = _AGENT.diagnose(forensic.to_dict(), ci_correlation=ci_correlation)
    by_kind = report.q6_what_happened["by_kind"]
    explain = report.explainability.to_dict()
    # A genuine verification failure anywhere in scope is definitive:
    # NOT_CERTIFIABLE, while the infrastructure failure remains
    # machine-readably distinct in the classification map.
    ok = (
        set(by_kind.get("verification_failure", [])) == {"cashflow_engine", "loan_engine"}
        and set(by_kind.get("infrastructure_failure", [])) == {"account_engine"}
        and report.q9_verdict["verdict"] == "NOT_CERTIFIABLE"
        and "infrastructure" in explain["was_the_failure_actually_a_verification_failure"]
    )
    return {
        "scenario": "FE",
        "name": "ci_failure_distinction",
        "expected": (
            "infrastructure vs verification distinction preserved; "
            "definitive defect => NOT_CERTIFIABLE"
        ),
        "by_kind": by_kind,
        "verdict": report.q9_verdict["verdict"],
        "failure_answer": explain["was_the_failure_actually_a_verification_failure"],
        "pass": ok,
    }


def scenario_ff() -> dict:
    planner = _drifted_planner()
    plan = planner.plan(())
    executable = build_executable_plan(plan)
    reconciled = reconcile(plan, {}, _PRIOR, _POP)
    forensic = build_forensic_record(plan, executable, {}, reconciled)
    report = _AGENT.diagnose(forensic.to_dict())
    v = report.q9_verdict["verdict"]
    drift_kinds = [u.kind for u in report.q8_uncertainties]
    ok = (
        len(plan.drift_blockers) > 0
        and v == "CERTIFICATION_BLOCKED"
        and "unmapped_capability" in drift_kinds
    )
    return {
        "scenario": "FF",
        "name": "discovery_drift",
        "expected": "CERTIFICATION BLOCKED (C42.24 lesson)",
        "drift_blockers": list(plan.drift_blockers)[:2],
        "verdict": v,
        "pass": ok,
    }


def scenario_fg() -> dict:
    plan, _, fresh, reconciled, forensic = _run_pipeline(
        ("backend/src/engines/behaviour_engine/pattern.py",),
        fresh_outcomes={
            "behaviour_engine": {
                "outcome": "pass",
                "counts": {
                    "generated": 200, "killed": 150, "survived": 38,
                    "no_tests": 12, "timeout": 0, "suspicious": 0,
                    "not_checked": 0,
                },
            },
        },
    )
    report = _AGENT.diagnose(forensic.to_dict())
    gaps = [u for u in report.q8_uncertainties if u.kind == "insufficient_test_surface"]
    recs = " ".join(u.recommendation.lower() for u in gaps)
    # No score-chasing: the agent must not emit any autonomous
    # strengthening *action*; only a bounded recommendation.
    autonomous_actions = [
        u for u in report.q8_uncertainties
        if "automatically run" in u.recommendation.lower()
    ]
    v = report.q9_verdict["verdict"]
    ok = (
        gaps
        and all(not g.gates_certification for g in gaps)
        and "strengthening" in recs
        and not autonomous_actions
        and v in ("CERTIFIABLE", "NOT_CERTIFIABLE")
    )
    return {
        "scenario": "FG",
        "name": "insufficient_test_surface",
        "expected": (
            "behavioral weakness diagnosed; no automatic score-chasing; "
            "strengthening recommended"
        ),
        "gaps": [g.to_dict() for g in gaps],
        "verdict": v,
        "pass": ok,
    }


def scenario_fh() -> dict:
    plan, _, fresh, reconciled, forensic = _run_pipeline(
        ("backend/src/engines/balance_engine/ledger.py",),
        fresh_outcomes={
            "balance_engine": {
                "outcome": "pass",
                "counts": {
                    "generated": 285, "killed": 270, "survived": 15,
                    "no_tests": 0, "timeout": 0, "suspicious": 3,
                    "not_checked": 0,
                },
                "notes": "survivors include mutants classified "
                         "equivalent (observable-equivalent behavior)",
            },
        },
    )
    report = _AGENT.diagnose(forensic.to_dict())
    eq = [u for u in report.q8_uncertainties if u.kind == "equivalent_mutant"]
    nondet = [u for u in report.q8_uncertainties if u.kind == "nondeterministic_mutation"]
    ok = bool(
        eq
        and all(not e.gates_certification for e in eq)
        and all("do not target" in e.recommendation.lower() for e in eq)
        and nondet  # suspicious count also surfaced
    )
    return {
        "scenario": "FH",
        "name": "equivalent_nondeterministic_survivor",
        "expected": "classified; preserved; not artificially targeted",
        "equivalent": [e.to_dict() for e in eq],
        "nondeterministic": [n.to_dict() for n in nondet],
        "pass": ok,
    }


def main() -> int:
    results = [
        scenario_fa(),
        scenario_fb(),
        scenario_fc(),
        scenario_fd(),
        scenario_fe(),
        scenario_ff(),
        scenario_fg(),
        scenario_fh(),
    ]

    # Determinism check: same input -> identical decision fields.
    _, _, _, _, forensic = _run_pipeline(
        ("backend/src/engines/credit_card_engine/risk.py",),
        fresh_outcomes={"credit_card_engine": {"outcome": "pass"}},
    )
    r1 = _AGENT.diagnose(forensic.to_dict())
    r2 = _AGENT.diagnose(forensic.to_dict())
    deterministic = r1.decision_fingerprint() == r2.decision_fingerprint()

    out_payload = {
        "scenarios": results,
        "determinism_check_pass": deterministic,
    }
    (OUT_DIR / "m9-c42.30-scenarios.json").write_text(
        json.dumps(out_payload, indent=2)
    )

    passed = sum(1 for r in results if r["pass"])
    print(f"C42.30 forensic scenarios: {passed}/{len(results)} pass; "
          f"determinism={'PASS' if deterministic else 'FAIL'}")
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['scenario']} — {r['name']} → {r.get('verdict', '')}")
    return 0 if passed == len(results) and deterministic else 1


if __name__ == "__main__":
    sys.exit(main())
