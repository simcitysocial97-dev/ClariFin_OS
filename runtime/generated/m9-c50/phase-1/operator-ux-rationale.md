# M9-C50 Phase 1 — Operator UX Rationale & Final Surface Justification

**Generated:** 2026-09-04
**Evidence dir:** `runtime/generated/m9-c50/cli/`

## Final operator surface

The canonical operator surface is **9 top-level commands** (C49) derived from the actual
repository's command classification (`canonical_control_plane.py::_CLASSIFICATION`): 103 tokens
classified, 9 canonical, 9 canonical-alias profiles, 11 compatibility, 74 deprecated.

## Justification against the ≥5 Semantic Intents (GUIDING_DOC §4)

| Required semantic intent | Canonical command(s) | Rationale |
|---|---|---|
| verify | `check plan run` | full lifecycle split: plan-only / explicit-plan execution / end-to-end entrypoint |
| diagnose | `diagnose` | evidence-backed failure/survivor diagnostic |
| strengthen | `strengthen` | capability-aware test strengthening + mutation loop |
| inspect | `inspect` | read-only queries (capabilities/evidence/plan/mutation/workflows/health) |
| govern/certify/operate | `certify ci doctor` | certification evidence-gate; CI reconciliation; framework health |

All 5 required intents are covered. The 9-surface size slightly exceeds the nominal 5–7 target,
but is **architecturally justified** because the repository's evidence demonstrates the internal
verification lifecycle genuinely requires distinct plan/run/diagnose/strengthen/inspect/operate
facets, and the C49 design intentionally keeps `doctor`/`ci`/`certify` as separate operator intents
to avoid conflating health, reconciliation, and certification. This is recorded as an architectural
decision (AD-1.1) per GUIDING_DOC §4 "final command names derived from the repository."

## No-duplicate-authority evidence
`no-duplicate-authority.json` (machine-verifiable): 85 legacy tokens (DEPRECATED/COMPATIBILITY) all
delegate via `migration_map()` to exactly one of 8 canonical operations with a single internal route;
0 tokens have no route; none registers an independent execution path in the facade `main()` dispatcher.

## Deprecation mapping
`deprecation-mapping.json`: 74 DEPRECATED tokens each mapped to a canonical operation.

## Bypass guarantee
`bypass_enforcement` is imported by `canonical_control_plane.py`, `certification.py`,
`evidence_integrity.py`, `cli_surface.py`, `pipeline_enforcement.py`. The single `main()` dispatcher
returns error for any token outside the classification-vocabulary (UNREACHABLE), so no legacy command
can self-execute without passing through `_dispatch_canonical`.