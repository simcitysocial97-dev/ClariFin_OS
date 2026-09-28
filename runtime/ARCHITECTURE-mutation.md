# Mutation Execution Architecture (M9-C45 / M45.23)

This document captures the canonical mutation-execution architecture as of M9-C45.

## Chain of Authority

```
   user/CI
     │
     ▼
┌─────────────────────┐
│ runtime/verify.py   │  ← ONLY user/CI-facing entry point
│   mutation ...      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│ mutation_runner.py          │  ← Canonical runner (single source of truth)
│  - execute_mutation()       │
│  - _MutationSafety context  │
│  - _validate_cache()        │
│  - _write_cache_provenance()│
│  - _restore_source_tree()   │
│  - _restore_config()        │
└────┬───────────────┬────────┘
     │               │
     ▼               ▼
┌─────────┐    ┌──────────────────┐
│ mutmut  │    │ MutationResult   │
│ 3.7.0   │    │  (canonical      │
│(pinned) │    │   dataclass)     │
└─────────┘    └─────────┬────────┘
                         │
                         ▼
              ┌────────────────────┐
              │ mutation-summary-  │  ← Authoritative evidence
              │   .json            │
              │ measurement-truth- │
              │   .json            │
              │ (execution_path=   │
              │  VERIFICATION_     │
              │  CONTROL_PLANE)    │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │ survivor_catalog,  │  ← Post-run analysis
              │ survivor_intel,    │    (libcst reconstruction)
              │ convergence_pipeline│
              └────────────────────┘
```

## Ownership and Contracts

| Layer | Owner | Contract |
|-------|-------|----------|
| `verify.py mutation` | runtime/verify.py | CLI surface (argparse) |
| `execute_mutation()` | mutation_runner.py | Returns `MutationResult` (frozen dataclass) |
| `MutationResult` | mutation_contract.py | Canonical evidence dataclass — every field has a documented source |
| `ENGINE_SELECTION` | mutation_contract.py | Per-engine test/source mapping — single source of truth |
| `parse_mutmut_results()` | mutation_contract.py | mutmut text → `MutationCounts` |
| `_MUTMUT_EXIT_CODE_TO_STATUS` | mutation_contract.py | mutmut exit code → canonical status |
| `execution_path` field | mutation_contract.py | "VERIFICATION_CONTROL_PLANE" (canonical) vs "LEGACY_DIRECT_BACKEND" (legacy) |
| `MutmutAdapter` | mutation_execution/mutmut_adapter.py | Adapter behind `MutationBackendBase` |
| `MutationOrchestrator` | mutation_execution/orchestrator.py | M9-C44 architecture (sharding, retries); NOT yet wired into the canonical `verify.py mutation` path |

## Evidence Surface

Every mutation campaign produces:
- `mutation-summary.json` — counts + classification + score + execution_path
- `measurement-truth.json` — durable evidence record
- `mutation-survivors.json` — per-function survivor catalog (when survivors exist)
- `mutation-survivor-intel.json` — durable survivor intel (opt-in enrichment)
- `backend/.mutmut-cache/provenance.json` — cache fingerprint

All evidence files carry the `execution_path` field. Any file without it, or with `execution_path=LEGACY_DIRECT_BACKEND`, is excluded from certification verdicts.

## Cache Model

- Cache directory: `backend/.mutmut-cache/`
- Fingerprint components: `repository_sha`, `tree_sha`, `config_hash`, `mutmut_version`, `python_version`, `timestamp`
- Validation: `_validate_cache()` runs before every campaign; mismatches trigger `shutil.rmtree(cache_dir, ignore_errors=True)`
- Override: `--no-cache` always bypasses the cache
- Provenance write: only after a successful `MutationResult` is constructed — failed campaigns do not write provenance

## Failure Model

- `_MutationSafety` context manager restores the source tree and `[tool.mutmut]` config on every exit path.
- atexit handler performs the same restoration.
- Signal handlers (SIGTERM, SIGINT) call `_restore_config()` and re-raise.
- Process group: `subprocess.Popen(start_new_session=True)` so a timeout kills the entire tree, not just the parent.

## Recovery Model

- Per M45.6: a campaign interrupted via SIGTERM can be safely resumed by re-running the same command. The cache preserves partial results, the source tree is restored, and the resume run produces identical counts to a clean run.
- Per M45.10: this model is platform-agnostic and applies identically in CI (GitHub Actions ubuntu-latest).

## CI Integration

- Workflow: `.github/workflows/mutation.yml`
- Two jobs: `mutation-smoke` (15 min, infra health gate) and `mutation` (90 min, authoritative).
- Both delegate to `python runtime/verify.py mutation`.
- Concurrency: `cancel-in-progress: false` (mutation is in the Rule 6 exception list).

## Legacy Boundary

- The single legacy direct-mutmut path is `.github/scripts/generate_mutation_report.py` — **deleted in M9-C45.11** because it was orphaned and unused.
- Shell wrapper `.github/scripts/run_mutation_selective.sh` delegates to `verify.py mutation` (no mutmut parsing in the wrapper).
- The only remaining direct-mutmut consumer is `runtime/foundation/verification/mutation_inventory.py` (lines 73-187). The PURE `classify()` function is canonical and consumed by `survivor_intel`; only the `collect_results()` / `show_mutant()` / `_parse_diff()` functions are non-canonical and need migration to canonical artifacts. Migration is deferred to a follow-up milestone.

## Operating Modes

| Mode | Invocation | Runtime | Use |
|------|-----------|---------|-----|
| smoke | `--smoke` | 3-10 s | infra health, PR gate |
| target | `--target <engine>` | 20-120 s | dev incremental |
| full | (no flag) | 60-90 min (CI) | authoritative 80% gate |

## Mutation Scope (ENGINE_SELECTION)

Mutation is restricted to `backend/src/engines/*` (per M9-C42.20). Services, repositories, and API layers are intentionally out of scope (see `cross-layer-qualification.json`).