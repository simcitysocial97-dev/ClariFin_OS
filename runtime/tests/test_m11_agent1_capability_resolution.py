# runtime/tests/test_m11_agent1_capability_resolution.py
#
# M11 Agent 1 — regression tests for the exec-0006 capability-resolution fix.
#
# WHY THIS FILE EXISTS
# --------------------
# CI run 37010443180 (PR #16) failed `Plan / Execute / Reconcile` at
#
#     mandatory tasks failed: exec-0006 — run diagnostic path
#     UNMAPPED capabilities require review (6):
#         - frontend:api-client:frontend-api
#         - frontend:component:frontend-command-center:command-center
#         - frontend:component:frontend-dashboard:dashboard
#         - frontend:component:frontend-platform:platform
#         - frontend:hook:frontend-hooks:query-finance
#         - frontend:hook:frontend-platform:platform-health
#
# The exit 1 was CORRECT: `control_plane._build_tasks()` emits
# `task-unmapped-review` precisely when `CapabilityResolver.resolve()` returns a
# non-empty `unmapped_blast_capabilities` (M9-C50 Phase-3 / STOP GATE 3). The
# defect was upstream of the task. Two independent causes, both fixed here:
#
#   A. `capability_resolver._names_resolved_file()` compared the last
#      `:`-segment of a capability id against changed-file STEMS. The cross-layer
#      frontend vocabulary (`frontend_capability_discovery.py:387-407`) never
#      names a file by stem — it mints
#          frontend:api-client:{domain}
#          frontend:hook:{domain}:{stem with a leading "use-" removed}
#          frontend:component:{domain}:{first directory under components/}
#      so the guard that exists to prevent exactly this false positive could
#      never fire for the frontend vocabulary. Three of the six were already
#      claimed by `api-contracts` (their files live under `frontend/lib`).
#
#   B. `frontend/components/**` was claimed by NO capability in
#      `verification.yaml`, so those files produced no verification obligation
#      at all. Fixing (A) alone would have silenced all six while leaving those
#      files with zero coverage — a WEAKENING. (A) and (B) are only correct
#      together.
#
# These tests pin all three properties that must hold: (A) stays fixed, (B)
# stays fixed AND produces a real obligation rather than silence, and the
# fail-closed review obligation still fires for a genuinely unmapped change.
# That third property is the one that would catch a future "fix" that buys
# green by disabling the gate.

from __future__ import annotations

import pytest

from runtime.foundation.verification.capability_contract import (
    get_capability_contract_registry,
)
from runtime.foundation.verification.capability_resolver import CapabilityResolver

# ── registry data: the mapping that (B) added ───────────────────────────────


@pytest.fixture(scope="module")
def registry():
    return get_capability_contract_registry()


@pytest.fixture
def resolver(registry):
    return CapabilityResolver(registry)


def _capability(registry, capability_id: str):
    matches = [c for c in registry.get_all_contracts() if c.id == capability_id]
    assert matches, f"capability {capability_id!r} is not registered"
    return matches[0]


class TestFrontendVerificationCapabilityIsRegistered:
    """(B): the frontend surfaces the frontend profile actually verifies must
    have a registry owner, or a change to them resolves to nothing."""

    @pytest.mark.parametrize(
        "prefix", ["frontend/components", "frontend/hooks", "frontend/__tests__"]
    )
    def test_surface_is_registered(self, registry, prefix):
        owner = _capability(registry, "frontend-verification")
        assert any(
            path.startswith(prefix) for path in owner.affected_by_paths
        ), f"{prefix} is still unregistered: {owner.affected_by_paths}"

    def test_the_capability_names_the_canonical_frontend_verification(self, registry):
        """One authoritative frontend verification meaning.

        The capability must delegate to the `frontend` workflow and the
        `run_frontend_verification` script — the same command
        `frontend-verify.yml` now executes through `runtime.verify frontend`.
        If it named anything else, a `frontend/components` change would be
        verified by a surface other than Frontend Verification, which is the
        split this milestone exists to remove.
        """
        owner = _capability(registry, "frontend-verification")
        workflow_ids = [m.workflow_id for m in owner.workflow_mappings]
        assert workflow_ids == ["frontend", "run_frontend_verification"], workflow_ids
        assert owner.minimum_verification_profile == "frontend"
        assert owner.minimum_verification_command == (
            "bash .github/scripts/run_frontend_verification.sh"
        )

    def test_it_does_not_double_register_surfaces_owned_elsewhere(self, registry):
        """`frontend/lib` belongs to `api-contracts`; registering it twice would
        duplicate obligations and make the plan's obligation count lie."""
        owner = _capability(registry, "frontend-verification")
        others = {
            path
            for c in registry.get_all_contracts()
            if c.id != "frontend-verification"
            for path in c.affected_by_paths
        }
        assert not (set(owner.affected_by_paths) & others)


# ── (A): the stem heuristic must not be the authority for `frontend:` ids ─────


class TestFrontendCapabilityIdsResolveThroughTheCrossLayerGraph:
    def test_hook_capability_under_a_registered_surface_is_not_unmapped(self, resolver):
        """`frontend/lib/hooks/use-query-finance.ts` -> `frontend:hook:frontend-hooks:query-finance`.

        The id's last segment is `query-finance`, but the file stem is
        `use-query-finance`, so the pre-fix stem comparison could never match.
        The file is under `frontend/lib`, owned by `api-contracts`, so the
        capability is reporting an already-mapped change.
        """
        result = resolver.resolve(["frontend/lib/hooks/use-query-finance.ts"])
        assert result.unmapped_blast_capabilities == []
        assert "api-contracts" in result.directly_affected_capabilities

    def test_api_client_capability_has_no_stem_segment_at_all(self, resolver):
        """`frontend:api-client:frontend-api` is a THREE-segment id.

        `entry.rsplit(":", 1)[-1]` yields `frontend-api` — a domain, never a file
        stem — so this form could never be suppressed by the stem fallback
        either.
        """
        result = resolver.resolve(["frontend/lib/api/gateway.ts"])
        assert result.unmapped_blast_capabilities == []

    def test_component_capability_names_a_directory_not_a_file(self, resolver):
        """`frontend/components/dashboard/*.tsx` -> `frontend:component:frontend-dashboard:dashboard`.

        The final segment is the directory under `components/`, not the stem of
        `cashflow-chart.tsx`.
        """
        result = resolver.resolve(["frontend/components/dashboard/cashflow-chart.tsx"])
        assert result.unmapped_blast_capabilities == []

    def test_resolved_frontend_capability_is_not_reported_unmapped(self, resolver):
        """Direct check of the fix: a `frontend:` id whose source files are all
        resolved must be suppressed."""
        changed = ["frontend/lib/hooks/use-platform-health.ts"]
        result = resolver.resolve(changed)
        assert "frontend:hook:frontend-platform:platform-health" in (
            result.blast_radius_report.affected_capabilities
        )
        assert result.unmapped_blast_capabilities == []


# ── the gate itself must still fire ──────────────────────────────────────────


class TestFailClosedReviewStillFires:
    """The property a future 'fix' is most likely to break: silencing the six
    false positives must not have silenced the gate."""

    def test_a_genuinely_unregistered_surface_still_produces_unmapped(self, resolver):
        """`frontend/mocks/**` is deliberately NOT registered (see
        verification.yaml: frontend/app is owned by runtime-verification,
        frontend/lib by api-contracts, and mocks were left as a documented
        residual rather than registered on speculation). A change there must
        still reach the fail-closed review obligation."""
        result = resolver.resolve(["frontend/mocks/handlers/newthing.ts"])
        assert result.unmapped_blast_capabilities == [
            "UNMAPPED:frontend/mocks/handlers/newthing.ts"
        ]

    def test_the_unmapped_set_is_not_simply_always_empty(self, resolver):
        """Guards against a blanket suppression regression: a change set with
        one mapped and one unmapped file must report exactly the unmapped one."""
        result = resolver.resolve(
            [
                "frontend/components/dashboard/cashflow-chart.tsx",
                "frontend/mocks/handlers/other.ts",
            ]
        )
        assert result.unmapped_blast_capabilities == [
            "UNMAPPED:frontend/mocks/handlers/other.ts"
        ]
        assert "frontend-verification" in result.directly_affected_capabilities


# ── the full boundary that failed in CI ──────────────────────────────────────


class TestPR16BoundaryIsClean:
    """The original reproduction, kept as a test.

    131 changed files at PR #16 produced `unmapped:UNMAPPED[6]`; after the fix
    the same boundary produces no unmapped capability at all. The list is
    pinned because a reappearance of ANY one of them means the graph-based
    resolution has stopped working for that id form.
    """

    EXEC_0006_UNMAPPED = {
        "frontend:api-client:frontend-api",
        "frontend:component:frontend-command-center:command-center",
        "frontend:component:frontend-dashboard:dashboard",
        "frontend:component:frontend-platform:platform",
        "frontend:hook:frontend-hooks:query-finance",
        "frontend:hook:frontend-platform:platform-health",
    }

    def test_none_of_the_exec_0006_ids_are_unmapped_any_more(self, resolver):
        changed = [
            "frontend/lib/api/gateway.ts",
            "frontend/lib/hooks/use-query-finance.ts",
            "frontend/lib/hooks/use-platform-health.ts",
            "frontend/components/command-center/metrics/metrics-strip.tsx",
            "frontend/components/dashboard/cashflow-chart.tsx",
            "frontend/components/platform/quick-actions.tsx",
        ]
        result = resolver.resolve(changed)
        assert result.unmapped_blast_capabilities == []
        assert not (self.EXEC_0006_UNMAPPED & set(result.unmapped_blast_capabilities))

    def test_the_six_files_still_generate_real_obligations(self, resolver):
        """Not silence: a `frontend`-workflow obligation."""
        result = resolver.resolve(["frontend/components/dashboard/cashflow-chart.tsx"])
        assert "frontend-verification" in result.directly_affected_capabilities
