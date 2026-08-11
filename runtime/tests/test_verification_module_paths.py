"""BL-005 — verification.yaml / registry capability-module path sync.

Regression guard: the capability ``modules`` paths in the verification registry
must point at real source locations, not the pre-VEA-3 drifted paths
(``backend/src/loan_engine`` etc., which never matched ``backend/src/engines/...``).

This test fails if a module path stops corresponding to an existing source
directory/file, so the drift cannot silently return.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.foundation.verification.registry import VerificationRegistry


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "capability_id,expected_module",
    [
        ("loan-engine", "backend/src/engines/loan_engine"),
        ("reconciliation", "backend/src/engines/reconciliation_engine.py"),
        ("ledger", "backend/src/engines/ledger_audit_engine.py"),
    ],
)
def test_capability_module_path_exists(capability_id: str, expected_module: str) -> None:
    registry = VerificationRegistry()
    cap = registry.get_capability(capability_id)
    assert cap is not None, f"capability {capability_id} missing"
    assert expected_module in cap.modules, (
        f"{capability_id} modules {cap.modules} no longer include {expected_module}"
    )
    resolved = REPO_ROOT / expected_module
    assert resolved.exists(), (
        f"BL-005 regression: {expected_module} (capability {capability_id}) "
        f"does not exist on disk"
    )


def test_module_paths_use_engines_layout() -> None:
    """The drifted top-level backend/src/<engine> paths must be gone."""
    registry = VerificationRegistry()
    stale = {"backend/src/loan_engine", "backend/src/reconciliation", "backend/src/ledger"}
    for cap in registry.get_all_capabilities():
        for module in cap.modules:
            assert module not in stale, (
                f"BL-005 regression: stale module path {module!r} in {cap.id}"
            )
