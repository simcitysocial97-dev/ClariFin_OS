"""
M9-C54 — Artifact generation utilities.

Provides get_repository_sha() and generate_all_artifacts() which orchestrate
the full C54 artifact pipeline by composing all analysis modules.
"""
from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import (
    REPO_ROOT,
    C54_SCHEMA,
    C54_ARTIFACT_DIR,
    inventory_workflows,
)
from runtime.foundation.verification.workflow_convergence.mapping import map_workflows_to_capabilities
from runtime.foundation.verification.workflow_convergence.greenness import audit_workflow_greenness
from runtime.foundation.verification.workflow_convergence.evidence_contract import build_evidence_contract
from runtime.foundation.verification.workflow_convergence.emission import assess_ci_emission
from runtime.foundation.verification.workflow_convergence.bypass import analyze_workflow_bypass
from runtime.foundation.verification.workflow_convergence.failure_semantics import build_failure_semantics
from runtime.foundation.verification.workflow_convergence.coverage import build_coverage_matrix
from runtime.foundation.verification.workflow_convergence.measurement_integrity import assess_measurement_integrity
from runtime.foundation.verification.workflow_convergence.duplication import analyze_duplication
from runtime.foundation.verification.workflow_convergence.environment import build_environment_contract
from runtime.foundation.verification.workflow_convergence.scenarios import execute_scenarios
from runtime.foundation.verification.workflow_convergence.c53_integration import verify_c53_integration
from runtime.foundation.verification.workflow_convergence.failure_injection import build_failure_injection_matrix
from runtime.foundation.verification.workflow_convergence.efficiency import measure_efficiency
from runtime.foundation.verification.workflow_convergence.certification_gates import evaluate_certification_gates


def get_repository_sha() -> str:
    """Get the current repository SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def generate_all_artifacts(output_dir: Path | None = None) -> dict[str, Any]:
    """Generate all C54 artifacts and return the certification result."""
    out_dir = Path(output_dir) if output_dir else C54_ARTIFACT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    sha = get_repository_sha()
    timestamp = datetime.now(UTC).isoformat()

    # 1. Workflow inventory
    inventories = inventory_workflows()
    inventory_data = {
        "schema": C54_SCHEMA,
        "generated_at": timestamp,
        "repository_sha": sha,
        "workflow_count": len(inventories),
        "workflows": [inv.to_dict() for inv in inventories],
    }
    (out_dir / "workflow-inventory.json").write_text(
        json.dumps(inventory_data, indent=2, default=str)
    )

    # 2. Workflow capability matrix
    mappings = map_workflows_to_capabilities(inventories)
    capability_matrix = {
        "schema": C54_SCHEMA,
        "generated_at": timestamp,
        "repository_sha": sha,
        "mapping_count": len(mappings),
        "mappings": [m.to_dict() for m in mappings],
    }
    (out_dir / "capability-matrix.json").write_text(
        json.dumps(capability_matrix, indent=2, default=str)
    )

    # 3. Greenness audit
    audits = audit_workflow_greenness(inventories)
    greenness_data = {
        "schema": C54_SCHEMA,
        "generated_at": timestamp,
        "repository_sha": sha,
        "audit_count": len(audits),
        "audits": [a.to_dict() for a in audits],
    }
    (out_dir / "greenness-audit.json").write_text(
        json.dumps(greenness_data, indent=2, default=str)
    )

    # 4. Evidence contract
    evidence_contract = build_evidence_contract(inventories)
    (out_dir / "evidence-contract.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "entry_count": len(evidence_contract),
                "entries": evidence_contract,
            },
            indent=2,
            default=str,
        )
    )

    # 5. CI emission assessment
    emission = assess_ci_emission(inventories)
    (out_dir / "ci-emission.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                **emission.to_dict(),
            },
            indent=2,
            default=str,
        )
    )

    # 6. Bypass analysis
    bypasses = analyze_workflow_bypass(inventories)
    (out_dir / "bypass-analysis.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "finding_count": len(bypasses),
                "findings": [b.to_dict() for b in bypasses],
            },
            indent=2,
            default=str,
        )
    )

    # 7. Failure semantics
    semantics = build_failure_semantics()
    (out_dir / "failure-semantics.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "semantics_count": len(semantics),
                "semantics": [s.to_dict() for s in semantics],
            },
            indent=2,
            default=str,
        )
    )

    # 8. Coverage matrix
    coverage = build_coverage_matrix(inventories)
    (out_dir / "coverage-matrix.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "row_count": len(coverage),
                "rows": [r.to_dict() for r in coverage],
            },
            indent=2,
            default=str,
        )
    )

    # 9. Measurement integrity
    measurements = assess_measurement_integrity(inventories)
    (out_dir / "measurement-integrity.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "metric_count": len(measurements),
                "metrics": [m.to_dict() for m in measurements],
            },
            indent=2,
            default=str,
        )
    )

    # 10. Duplication analysis
    duplications = analyze_duplication(inventories)
    (out_dir / "duplication-analysis.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "finding_count": len(duplications),
                "findings": [d.to_dict() for d in duplications],
            },
            indent=2,
            default=str,
        )
    )

    # 11. Environment contract
    env_contract = build_environment_contract(inventories)
    (out_dir / "environment-contract.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "parameter_count": len(env_contract),
                "parameters": [e.to_dict() for e in env_contract],
            },
            indent=2,
            default=str,
        )
    )

    # 12. Scenarios
    scenarios = execute_scenarios(inventories)
    (out_dir / "scenarios.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "scenario_count": len(scenarios),
                "scenarios": [s.to_dict() for s in scenarios],
            },
            indent=2,
            default=str,
        )
    )

    # 13. C53 integration
    c53_checks = verify_c53_integration()
    (out_dir / "c53-integration.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "check_count": len(c53_checks),
                "checks": [c.to_dict() for c in c53_checks],
            },
            indent=2,
            default=str,
        )
    )

    # 14. Failure injection matrix
    failure_matrix = build_failure_injection_matrix()
    (out_dir / "failure-injection-matrix.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "row_count": len(failure_matrix),
                "rows": [r.to_dict() for r in failure_matrix],
            },
            indent=2,
            default=str,
        )
    )

    # 15. Efficiency metrics
    efficiency = measure_efficiency(inventories)
    (out_dir / "efficiency-metrics.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "metric_count": len(efficiency),
                "metrics": [e.to_dict() for e in efficiency],
            },
            indent=2,
            default=str,
        )
    )

    # 16. Certification gates
    gates = evaluate_certification_gates(
        inventories, bypasses, c53_checks, scenarios, failure_matrix, sha
    )
    all_passed = all(g.passed for g in gates)
    (out_dir / "certification-gates.json").write_text(
        json.dumps(
            {
                "schema": C54_SCHEMA,
                "generated_at": timestamp,
                "repository_sha": sha,
                "gate_count": len(gates),
                "all_passed": all_passed,
                "gates": [g.to_dict() for g in gates],
            },
            indent=2,
            default=str,
        )
    )

    # Baseline
    baseline = {
        "schema": C54_SCHEMA,
        "generated_at": timestamp,
        "repository_sha": sha,
        "workflow_count": len(inventories),
        "total_jobs": sum(len(inv.jobs) for inv in inventories),
        "total_steps": sum(inv.total_steps for inv in inventories),
        "verification_steps": sum(inv.verification_steps for inv in inventories),
        "certified_modules_preserved": [
            "runtime/foundation/verification/ci_evidence.py",
            "runtime/foundation/verification/evidence_contract.py",
            "runtime/foundation/verification/gap_classification.py",
            "runtime/foundation/verification/generation_engine.py",
            "runtime/foundation/verification/candidate_validation.py",
            "runtime/foundation/verification/blast_radius.py",
            "runtime/foundation/verification/capability_discovery.py",
            "runtime/foundation/verification/measurement_truth.py",
            "runtime/foundation/verification/authorization_boundary.py",
        ],
    }
    (out_dir / "m9-c54-baseline.json").write_text(
        json.dumps(baseline, indent=2, default=str)
    )

    return {
        "schema": C54_SCHEMA,
        "generated_at": timestamp,
        "repository_sha": sha,
        "all_gates_passed": all_passed,
        "workflows_inventoried": len(inventories),
        "gates_evaluated": len(gates),
        "artifacts_written": [
            "workflow-inventory.json",
            "capability-matrix.json",
            "greenness-audit.json",
            "evidence-contract.json",
            "ci-emission.json",
            "bypass-analysis.json",
            "failure-semantics.json",
            "coverage-matrix.json",
            "measurement-integrity.json",
            "duplication-analysis.json",
            "environment-contract.json",
            "scenarios.json",
            "c53-integration.json",
            "failure-injection-matrix.json",
            "efficiency-metrics.json",
            "certification-gates.json",
            "m9-c54-baseline.json",
        ],
    }


if __name__ == "__main__":
    result = generate_all_artifacts()
    print(json.dumps(result, indent=2, default=str))
