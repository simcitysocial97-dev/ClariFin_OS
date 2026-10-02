# M10 Agent 1 — Test Naming Policy

**Baseline:** `main` @ `bfcf336b`
**Status:** proposal. This document defines the convention; it deliberately does **not**
execute a mass rename. Rationale for the restraint is in §5.

## 1. What the codebase already does (derive, do not invent)

Three conventions are already load-bearing, and a new policy must be a *description* of them,
not a replacement:

| Observation | Evidence | Adopt as |
|---|---|---|
| `backend/tests/<category>/` directories are the enforced taxonomy | 13 category dirs holding all 203 `test_*.py`; the 11 declared markers are 9/11 unused | **Directory = category.** Primary axis. |
| Filenames name a **capability or behaviour**, usually | `test_coverage_path_authority.py`, `test_evidence_cleanup_stress.py`, `test_dead_code_detection.py`, `test_repository_identity_resolution.py`, `test_workspace.py` | `test_<capability>_<behaviour>.py` |
| Docstrings state the *purpose* in prose | 20+ files open with a one-line claim, e.g. `"""M9-C65 — Coverage measurement path authority tests.` | Docstring carries the milestone provenance; **filename does not have to.** |
| `test_<subject>.test.ts` for the TS mirror | `testing/runtime/foundation/verification/test_aggregator.py` … | Same axis across languages. |

The single strongest signal: **the repository already prefers capability names.** The
milestone-numbered files are the exception, not the rule, and they cluster in one era (M9-C48
→ M9-C72).

## 2. The convention

```
test_<capability>_<behaviour>[_<qualifier>].py        # preferred
Test<Capability><Behaviour>                            # class, when a class is needed
test_<subject>                                         # allowed when capability == subject
```

Rules, in priority order:

1. **Name the capability, not the milestone.** `test_coverage_path_authority.py`, not
   `test_c65_coverage_path_authority.py`. A milestone number dates the file; it does not
   describe it, and it cannot be searched by intent.
2. **Name the behaviour under test, not the function.** Prefer
   `test_evidence_cleanup_stress.py` over `test_evidence_retention.py`; the second names a
   module, which the file is not.
3. **No orphan qualifiers.** If a file needs `phase10_12` or `15_21` in its name, it is
   really two or seven files, or it is one file about one capability that outgrew its name.
4. **Milestone provenance goes in the docstring, first line, once.** The existing
   `"""M9-C65 — Coverage measurement path authority tests.`` form is correct and already
   common. Keep it; stop repeating the number in the filename.
5. **Categories are directories, not prefixes or markers.** `backend/tests/invariants/`, never
   `test_invariant_*.py` at the tree root.
6. **Match the directory's existing plurality.** `properties/` and `invariants/` are plural;
   if markers are ever adopted they must be `property`/`invariant` consistently — never both
   `properties` and `property` in the same repo.

### Anti-patterns this policy exists to end

| Anti-pattern | Instance | Why it hurts |
|---|---|---|
| Milestone in filename | `test_m9_c55.py`, `test_m9_c50.py`, `test_m9_c51.py` … `test_m9_c72_*` | 67/154 runtime files (43%) say when, not what |
| Inconsistent milestone spelling | `test_m9_c55.py` vs `test_m9c57_*.py` vs `test_c37_*.py` vs `test_vea5_m5_*` | Four spellings for one numbering scheme |
| Merged phase ranges | `test_platform_api_phase10_12.py`, `..._phase15_21.py` | Numeric ranges are the fingerprint of accretion |
| Absent numbering | no `phase5` anywhere, but phases 1-4, 6-21 present | Gaps hide lost tests |
| Tool wearing a test's name | `test_m9_c50_stop_gate9_failure_modes.py` (0 test functions) | Makes 1,263 lines of dead tool look like coverage |

## 3. Measured scale of the problem

| Measure | `runtime/tests` | `backend/tests` |
|---|---:|---:|
| `test_*.py` files | 154 | 203 |
| filenames carrying milestone/task tokens | **67 (43%)** | 12 (6%) |
| distinct milestone spellings in use | `m9_cNN`, `m9cNN`, `cNN`, `m9-cNN`, `vea5_mN`, `phaseN`, `phaseN_M` | same |

Backend is already in good shape. **Runtime is the problem**, and it is concentrated in the
`test_m9_c4*` … `test_m9_c7*` block plus the `platform_api_phase*` family.

## 4. Recommended renames, in priority order

Ordered by (clarity gained) ÷ (reference-surface risk). Every row is a proposal, not an action.

### Tier 1 — do now, zero external references

| Current | Proposed | Why |
|---|---|---|
| `runtime/tests/test_m9_c50_stop_gate9_failure_modes.py` | *delete* (see cleanup ledger) | proven byte-clone of `audit_final_freeze.py`; 0 test functions |

### Tier 2 — high value, blocked on frozen evidence

`test_platform_api_phase*` → capability names. The mapping is exact, taken from each file's
own docstring, not guessed:

| Current | Proposed |
|---|---|
| `test_platform_api_phase1.py` | `test_platform_api_contracts.py` |
| `test_platform_api_phase2.py` | `test_platform_api_service_aggregators.py` |
| `test_platform_api_phase3.py` | `test_platform_api_fastapi_mount.py` |
| `test_platform_api_phase4.py` | `test_platform_api_snapshot_read_path.py` |
| `test_platform_api_phase6.py` | `test_platform_api_verification_center.py` |
| `test_platform_api_phase7.py` | `test_platform_api_execution_live_state.py` |
| `test_platform_api_phase8.py` | `test_platform_api_history_evidence_comparison.py` |
| `test_platform_api_phase9.py` | `test_platform_api_error_architecture_capability.py` |
| `test_platform_api_phase10_12.py` | `test_platform_api_diagnostics.py` |
| `test_platform_api_phase13.py` | `test_ai_control_layer_foundation.py` |
| `test_platform_api_phase14.py` | `test_context_engine.py` |
| `test_platform_api_phase15_21.py` | `test_ai_control_layer_governance.py` |

487 tests across 12 files, 9 in `runtime/tests` and 3 in
`backend/tests/integration/`. `phase13`/`14`/`15_21` are AI-control-layer files, so
`test_ai_*` is a better family name than `test_platform_api_*` for those three.

### Tier 3 — mechanical, large, low value-per-file

The `test_m9_cNN_*.py` block (~34 files). Individually uncontroversial, collectively a large
diff touching frozen evidence. Batch it, do not trickle it.

## 5. Why no rename was executed in this pass

The brief permits renaming "only where the new name is clearly better **AND** references are
safely updatable". For Tier 2 the second condition fails, and it fails on evidence I can point
at:

- **Frozen evidence names these files.** `runtime/generated/**` — which
  `.gitignore` deliberately keeps version-controlled as milestone evidence — references them
  in `m9-c64-runtime-framework-final-convergence/residual-ledger.json` (3 node ids) and
  `m9-c64-r-runtime-pipeline-forensic-validation/pipeline-traces/` (dozens, incl.
  `baseline-inspect-plan.json` and `baseline-diagnose.txt`). Evidence is immutable by the
  repository's own stated policy; a rename would leave the record describing filenames that
  no longer exist.
- **Non-owned docs name them.** `BASELINE.md` (lines 68-72, 76-77, 85-95, 383-387, 472) and
  `docs/audits/m9-c57-runtime-framework/{RUNTIME_FRAMEWORK_DEEP_DIVE_AUDIT.md,
  runtime_loc_breakdown.txt, runtime_largest_files.txt}`. Not my ownership.
- **A live test holds one as a string literal.** `runtime/tests/test_changed_file_parsing.py:158`
  parametrises over `"backend/tests/integration/test_platform_api_phase3.py"`. It never opens
  the file — it feeds `is_generated_or_artifact_path` — so it would still pass, but it would
  become a reference to a path that no longer exists.

`.github/` is **clean**: zero references, so CI is not the blocker. The blocker is exclusively
frozen evidence plus documents I may not edit. A partial rename would be strictly worse than
none: it would make the tree *less* consistent, not more.

**Therefore:** one deletion (Tier 1, provably duplicate, zero references) and a published
mapping (this document). The rename is a single-owner, single-commit operation that must
include the evidence and docs updates, or it should not happen.

## 6. Convention for non-test files

The same "name the capability" rule was applied to the one tool found misfiled as a test:
`test_m9_c50_stop_gate9_failure_modes.py` → the surviving `audit_final_freeze.py` is named for
what it does. Any future audit harness belongs in `tools/` (the repo's existing home for
`development/`, `diagnostics/`, `generators/`), **not** in `runtime/tests/`, and must not carry
a `test_` prefix. A `test_`-prefixed file with no `test_` function is always a defect: it
inflates the apparent test count while contributing nothing, which is exactly how a 1,263-line
tool came to be listed among 154 "tests".
