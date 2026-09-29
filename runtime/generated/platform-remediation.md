# Engineering Platform Remediation Plan

**Generated:** 2026-08-06T06:34:08.194921+00:00

## Executive Summary

This document provides deterministic repair instructions for all
certification-blocking root cause clusters identified by the
Engineering Platform Certification Audit.

## Repair Phases

Repairs must be executed in dependency order. Never repair
downstream before upstream.

| Phase | Cluster | Problems | Complexity |
|-------|---------|----------|------------|
| 1 | Repository Graph Integrity | 3 | varies |
| 2 | Cross-Layer Map Completeness | 3 | varies |
| 3 | Dependency Graph Integrity | 4 | varies |
| 4 | Knowledge Base Data Quality | 2 | varies |
| 5 | Executor Command Formatting | 4 | varies |
| 6 | Executor Resilience | 3 | varies |
| 7 | CLI Completeness | 1 | varies |
| 8 | GitHub Actions Completeness | 4 | varies |
| 9 | Artifact Organization | 3 | varies |

## Phase 1: Repository Graph Integrity

**Cluster:** CLUSTER-REPOSITORY_GRAPH_INTEGRITY

### Problems

- Repository index has edge referential integrity violations
- Fresh graph build produces 1362 errors
- Node and edge counts are inconsistent

### Repair Steps

- 1. Inspect `runtime/foundation/repository/builder/builder.py` validate() method
- 2. Fix scanner edge generation to reference valid node IDs
- 3. Ensure builder.build() completes without errors
- 4. Verify index.json edge count matches declared count

### Files

- `runtime/foundation/repository/builder/builder.py`
- `runtime/foundation/repository/scanner/base.py`
- `runtime/generated/repository/index.json`

### Functions

- `RepositoryBuilder.build()`
- `RepositoryBuilder.validate()`
- `BaseScanner.scan()`

### Tests

```bash
python3 -c 'from runtime.foundation.repository.builder.builder import RepositoryBuilder; b=RepositoryBuilder(); b.build(); print(b.validate().is_valid())'
```

### Verification

```bash
python runtime/verify.py graph
```

### Expected Result

Graph builds cleanly with zero structural errors and complete referential integrity

## Phase 2: Cross-Layer Map Completeness

**Cluster:** CLUSTER-CROSS_LAYER_COMPLETENESS

### Problems

- 72 duplicate endpoints across cross-layer chains
- 16 chains missing capabilities
- 5 chains missing routers

### Repair Steps

- 1. Inspect cross-layer map builder
- 2. Add deduplication pass for endpoints
- 3. Ensure all chains have complete field population
- 4. Validate chain completeness before write

### Files

- `runtime/generated/cross-layer-map.json`

### Functions

- `CrossLayerImpactPlanner.analyze_cross_layer_impact()`

### Tests

```bash
python3 -c 'import json; m=json.load(open("runtime/generated/cross-layer-map.json")); print(len(m), "chains")'
```

### Verification

```bash
python runtime/verify.py graph
```

### Expected Result

All chains have unique endpoints and complete ownership fields

## Phase 3: Dependency Graph Integrity

**Cluster:** CLUSTER-DEPENDENCY_GRAPH_INTEGRITY

### Problems

- 194 edges with missing source nodes
- 525 edges with missing target nodes
- 1329 structural errors in graph
- 671 isolated nodes (60% of graph)

### Repair Steps

- 1. Repair repository graph first (Phase 1 dependency)
- 2. Rebuild cross-layer map (Phase 2 dependency)
- 3. Rebuild dependency graph from clean data
- 4. Verify no isolated nodes remain

### Files

- `runtime/foundation/repository/graph/graph_service.py`
- `runtime/generated/repository/index.json`

### Functions

- `RepositoryGraphService.load()`
- `RepositoryGraphService.validate()`

### Tests

```bash
python3 -c 'from runtime.foundation.repository.graph.graph_service import RepositoryGraphService; s=RepositoryGraphService(); print(s.validate())'
```

### Verification

```bash
python runtime/verify.py graph
```

### Expected Result

Graph has zero structural errors, no missing nodes, no isolated nodes

## Phase 4: Knowledge Base Data Quality

**Cluster:** CLUSTER-KNOWLEDGE_DATA_QUALITY

### Problems

- 101 broken links in knowledge index
- Indexer count mismatch for documentation (saved=131, rebuilt=132)

### Repair Steps

- 1. Repair cross-layer map (Phase 2 dependency)
- 2. Rebuild knowledge index from clean artifacts
- 3. Validate all references are resolvable
- 4. Verify indexer count consistency

### Files

- `runtime/foundation/knowledge/indexer.py`
- `runtime/generated/knowledge-index.json`

### Functions

- `KnowledgeIndexer.build_index()`
- `KnowledgeIndexer.validate()`

### Tests

```bash
python3 -c 'from runtime.foundation.knowledge.indexer import build_index; idx=build_index(); print(idx.total_entries, "entries")'
```

### Verification

```bash
python runtime/verify.py knowledge
```

### Expected Result

Zero broken links, indexer count matches rebuilt count

## Phase 5: Executor Command Formatting

**Cluster:** CLUSTER-EXECUTOR_COMMAND_FORMTING

### Problems

- execute_python does not format command correctly
- execute_pytest does not format command correctly
- execute_vitest does not format command correctly
- execute_playwright does not format command correctly

### Repair Steps

- 1. Inspect each execute_* method in runtime/foundation/verification/executor.py
- 2. Fix command string formatting
- 3. Verify commands execute correctly

### Files

- `runtime/foundation/verification/executor.py`

### Functions

- `Executor.execute_python()`
- `Executor.execute_pytest()`
- `Executor.execute_vitest()`
- `Executor.execute_playwright()`

### Tests

```bash
python3 -c 'from runtime.foundation.verification.executor import Executor; e=Executor(); print(e.execute_python("echo test"))'
```

### Verification

```bash
python runtime/verify.py quick
```

### Expected Result

All execute_* methods produce correctly formatted commands

## Phase 6: Executor Resilience

**Cluster:** CLUSTER-EXECUTOR_RESILIENCE

### Problems

- No retry logic for failed commands
- No cancellation support
- No parallel execution support

### Repair Steps

- 1. Add retry decorator to execute() method
- 2. Add cancel() method to Executor
- 3. Add parallel execution support for independent commands

### Files

- `runtime/foundation/verification/executor.py`

### Functions

- `Executor.execute()`
- `Executor.cancel()`

### Tests

```bash
python3 -c 'from runtime.foundation.verification.executor import Executor; e=Executor(); print(hasattr(e, "cancel"))'
```

### Verification

```bash
python runtime/verify.py quick
```

### Expected Result

Executor supports retry, cancellation, and parallel execution

## Phase 7: CLI Completeness

**Cluster:** CLUSTER-CLI_COMPLETENESS

### Problems

- dashboard command is not implemented

### Repair Steps

- 1. Implement cmd_dashboard() in runtime/verify.py
- 2. Register dashboard command in main()
- 3. Verify command executes without error

### Files

- `runtime/verify.py`

### Functions

- `cmd_dashboard()`

### Tests

```bash
python runtime/verify.py dashboard
```

### Verification

```bash
python runtime/verify.py audit
```

### Expected Result

dashboard command is recognized and executes successfully

## Phase 8: GitHub Actions Completeness

**Cluster:** CLUSTER-GITHUB_ACTIONS_COMPLETENESS

### Problems

- verification-runtime workflow missing artifact upload
- quality workflow missing artifact upload
- backend-verify workflow missing artifact upload
- frontend-verify workflow missing artifact upload

### Repair Steps

- 1. Inspect each workflow in .github/workflows/
- 2. Add upload-runtime composite action step
- 3. Verify artifact names are unique

### Files

- `.github/workflows/verification-runtime.yml`
- `.github/workflows/quality.yml`
- `.github/workflows/backend-verify.yml`
- `.github/workflows/frontend-verify.yml`

### Tests

```bash
python3 .github/scripts/validate_actions.py
```

### Verification

```bash
python runtime/verify.py ci-doctor
```

### Expected Result

All workflows have artifact upload steps and validate successfully

## Phase 9: Artifact Organization

**Cluster:** CLUSTER-ARTIFACT_ORGANIZATION

### Problems

- loan-results.txt exists in 3 locations
- mutation-summary.json exists in 3 locations
- junit.xml exists in 2 locations

### Repair Steps

- 1. Consolidate sample artifacts to single canonical location
- 2. Update sample data references
- 3. Verify no overwrites occur

### Files

- `runtime/generated/verification/samples/`

### Tests

```bash
python3 -c 'from pathlib import Path; files=list(Path("runtime/generated").rglob("loan-results.txt")); print(len(files), "loan-results.txt files")'
```

### Verification

```bash
python runtime/verify.py audit
```

### Expected Result

No duplicate artifact names in runtime/generated/

## Validation Criteria

The platform is certified when:

- [ ] `python runtime/verify.py audit` exits 0 with zero critical and high findings
- [ ] `python runtime/verify.py graph` exits 0
- [ ] `python runtime/verify.py knowledge` exits 0
- [ ] `python runtime/verify.py quick` exits 0
- [ ] `python runtime/verify.py ci-doctor` exits 0
- [ ] All GitHub Actions workflows are green
- [ ] No command hangs or requires manual intervention
