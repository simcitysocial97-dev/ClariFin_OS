"""
M9-C54 — C53 integration checks (Q14).

Standalone module that verifies the workflow/CI layer does not break
the C53 generation chain without depending on workflow inventory.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import REPO_ROOT


@dataclass(frozen=True, slots=True)
class C53IntegrationCheck:
    check: str
    passed: bool
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "passed": self.passed,
            "evidence": self.evidence,
        }


def verify_c53_integration() -> list[C53IntegrationCheck]:
    """Verify the workflow/CI layer does not break the C53 generation chain."""
    checks: list[C53IntegrationCheck] = []

    c53_modules = [
        "runtime/foundation/verification/gap_classification.py",
        "runtime/foundation/verification/generation_eligibility.py",
        "runtime/foundation/verification/generation_engine.py",
        "runtime/foundation/verification/candidate_validation.py",
        "runtime/foundation/verification/c53_certification.py",
        "runtime/foundation/verification/c53_scenarios.py",
    ]
    for mod in c53_modules:
        p = REPO_ROOT / mod
        checks.append(
            C53IntegrationCheck(
                check=f"C53 module {mod} exists",
                passed=p.exists(),
                evidence=f"exists={p.exists()}",
            )
        )

    c53_test = REPO_ROOT / "runtime/tests/test_m9_c53.py"
    checks.append(
        C53IntegrationCheck(
            check="C53 test file exists",
            passed=c53_test.exists(),
            evidence=f"exists={c53_test.exists()}",
        )
    )

    c53_cert = REPO_ROOT / "runtime/generated/m9-c53/certification.json"
    checks.append(
        C53IntegrationCheck(
            check="C53 certification artifact exists",
            passed=c53_cert.exists(),
            evidence=f"exists={c53_cert.exists()}",
        )
    )

    auth_boundary = (
        REPO_ROOT / "runtime/foundation/verification/authorization_boundary.py"
    )
    checks.append(
        C53IntegrationCheck(
            check="Human authorization boundary module exists",
            passed=auth_boundary.exists(),
            evidence=f"exists={auth_boundary.exists()}",
        )
    )

    try:
        from runtime.foundation.verification import generation_eligibility  # noqa: F401

        checks.append(
            C53IntegrationCheck(
                check="C53 generation_eligibility is importable",
                passed=True,
                evidence="imported successfully",
            )
        )
    except Exception as e:
        checks.append(
            C53IntegrationCheck(
                check="C53 generation_eligibility is importable",
                passed=False,
                evidence=f"import failed: {e}",
            )
        )

    try:
        from runtime.foundation.verification import candidate_validation  # noqa: F401

        checks.append(
            C53IntegrationCheck(
                check="C53 candidate_validation is importable",
                passed=True,
                evidence="imported successfully",
            )
        )
    except Exception as e:
        checks.append(
            C53IntegrationCheck(
                check="C53 candidate_validation is importable",
                passed=False,
                evidence=f"import failed: {e}",
            )
        )

    return checks
