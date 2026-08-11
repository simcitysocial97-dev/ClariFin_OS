# Verification Report

**Profile:** frontend
**Generated:** 2026-08-11T12:50:58.639924+00:00
**Overall Status:** failed

## Changed Files

- `docs/progress.md`
- `frontend/app/layout.tsx`
- `frontend/app/settings/page.tsx`
- `frontend/components/command-palette/command-provider.tsx`
- `frontend/components/dashboard/cashflow-chart.tsx`
- `frontend/components/dashboard/category-spend-chart.tsx`
- `frontend/components/graph/graph-overlay.tsx`
- `frontend/components/intelligence/executive-modal.tsx`
- `frontend/components/intelligence/executive-toast.tsx`
- `frontend/components/intelligence/investigative-insight-panel.tsx`
- `frontend/components/layout/sidebar.tsx`
- `frontend/components/onboarding/tutorial.tsx`
- `frontend/components/os-shell/bottom-intelligence-shelf.tsx`
- `frontend/components/os-shell/left-rail.tsx`
- `frontend/components/os-shell/timeline-controls.tsx`
- `frontend/components/os-shell/top-command-bar.tsx`
- `frontend/components/os-shell/workspace-host.tsx`
- `frontend/components/theme-toggle.tsx`
- `frontend/components/upload/upload-modal.tsx`
- `frontend/components/upload/upload-zone.tsx`
- `frontend/components/visualization/evidence-tree/evidence-tree.tsx`
- `frontend/components/visualization/waterfall/waterfall-engine.tsx`
- `frontend/hooks/use-global-shortcuts.ts`
- `frontend/lib/hooks/use-dashboard-metrics.ts`
- `runtime/foundation/verification/models/scope.py`
- `runtime/foundation/verification/planner/planner.py`
- `runtime/foundation/verification/registry/registry.py`
- `runtime/foundation/verification/verification.yaml`
- `runtime/system/evidence/aggregator.py`
- `runtime/tests/test_cross_layer_planner.py`
- `docs/verification/VEA3_BASELINE.md`
- `docs/verification/VEA3_BL004_AUDIT.md`
- `docs/verification/VEA3_CERTIFICATION.md`
- `docs/verification/VEA3_E4_DESIGN.md`
- `docs/verification/VEA4_BASELINE.md`
- `docs/verification/VEA4_INVENTORY.json`
- `frontend/lib/hooks/use-mounted.ts`
- `runtime/tests/test_e4_graph_attribution.py`
- `runtime/tests/test_verification_module_paths.py`

## Blast Radius

- **affected_engines**: []
- **affected_services**: []
- **affected_capabilities**: []
- **affected_tests**: []

## Verification Plan

- **Plan ID:** plan-20260811-105637
- **Scope:** frontend
- **Targets:** 3
- **Steps:** 3
- **Estimated Duration:** 360s

## Tasks Executed

| Task ID | Name | Status | Duration |
|---------|------|--------|----------|
| step-0001 | bash .github/scripts/run_frontend_verification.sh | passed | 294.9s |
| step-0002 | bash .github/scripts/run_fast_checks.sh | passed | 92.2s |
| step-0003 | bash .github/scripts/run_runtime_verification.sh | failed | 6474.2s |

## Results Summary

- **Passed:** 2
- **Failed:** 1
- **Skipped:** 0
- **Total Duration:** 6861.3s

## Dependency Chains (Program 7A)

No dependency chains available (Program 7A cross-layer map not loaded).

## Evidence Files

No evidence files generated.

## Recommendations

- Investigate failing task: bash .github/scripts/run_runtime_verification.sh
