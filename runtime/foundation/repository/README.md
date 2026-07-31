# Repository Intelligence Runtime v1.0

A deterministic, repository-wide intelligence layer that discovers structure, cross-references canonical metadata sources, and exposes a query API for answering questions about capabilities, modules, APIs, components, tests, documentation, dependencies, and change impact.

**Version:** 1.0.0 (Feature Complete)

This package is analysis infrastructure only — no AI planning, orchestration, workflow generation, or autonomous execution.

## Architecture Overview

```
          Scanners
              ↓
       RepositoryBuilder
              ↓
        RepositoryGraph
              ↓
    RepositoryGraphService
              ↓
┌─────────────┼─────────────┐
│             │             │
Impact     Validator      Metrics   Query API     CLI
          (analysis)   (health)  (interface)  (entry)
              │
        Verification Runtime
        Evidence Runtime
```

The Repository Intelligence Runtime is a **feature-complete v1.0** stable infrastructure component. Future changes are limited to bug fixes, additional metadata fields, and compatibility updates. No architectural redesign should be required for Programs 3–10.

## Core Components

### RepositoryGraphService (Phase 1)

The **ONLY** supported interface for graph access. All modules must use this service instead of accessing `graph.nodes` or `graph.edges` directly. It provides:

| Method | Description |
|--------|-------------|
| `get_node(node_id)` | Retrieve a node by ID |
| `get_nodes(node_type=None)` | Get all nodes, optionally filtered by type |
| `find_nodes(predicate)` | Find nodes matching a predicate function |
| `get_edge(edge_id)` | Retrieve an edge by source:target:relationship |
| `successors(node_id, edge_type)` | Get successor node IDs |
| `predecessors(node_id, edge_type)` | Get predecessor node IDs |
| `neighbors(node_id)` | Get both successors and predecessors |
| `find_paths(source, target, max_depth)` | Find all simple paths between two nodes |
| `find_edges(node_id)` | Get outgoing and incoming edges for a node |
| `statistics()` | Compute basic graph statistics |
| `validate()` | Check structural integrity of the graph |
| `get_gaps()` | Retrieve gap detection metadata |

The service supports lazy loading from index.json and in-memory caching for deterministic lookups.

### RepositoryBuilder (Phase 3)

Separates index construction from query/runtime logic. The builder is responsible ONLY for:

1. **Running scanners** — orchestrates all scanner classes
2. **Merging results** — combines ScanResult objects from all scanners
3. **Assigning ownership** — classifies each node by ownership category
4. **Detecting gaps** — identifies missing relationships and unknown files
5. **Validating** — checks structural integrity of the built graph
6. **Generating the graph** — produces a populated RepositoryGraph object
7. **Writing the index** — serializes to index.json with versioned metadata

The builder does NOT perform any traversal, impact analysis, or metrics computation. Those belong in separate consumers using RepositoryGraphService.

### Repository (schema.py)

The core data structure containing:

- **Nodes:** GraphNode objects with id, type, name, path, source, ownership, properties
- **Edges:** GraphEdge objects with source, target, relationship, confidence, evidence, ownership
- **Metadata:** schema_version, generated_at (content hash), repository_root

The Repository supports both legacy flat formats and the new versioned format with separate metadata/graph sections.

### Versioned Index Format (Phase 2)

The index now uses a structured format with explicit versioning:

```json
{
  "metadata": {
    "schema_version": "2.2",
    "generator_version": "1.0.0",
    "generated_at": "<content_hash>",
    "repository_root": "/path/to/repo",
    "python_version": "3.11",
    "scanner_versions": { ... },
    "node_count": 1234,
    "edge_count": 5678,
    "node_types": { "capability": 11, "module": 567, ... },
    "edge_relationships": { "implements": 892, "imports": 1234, ... },
    "ownership_classes": ["capability", "shared_infrastructure", ...],
    "validation_summary": { ... }
  },
  "graph": {
    "nodes": [ ... ],
    "edges": [ ... ]
  },
  "gaps": {
    "missing_modules": [],
    "orphan_modules": [ ... ],
    "no_verification_evidence": [ ... ],
    "no_documentation_evidence": [ ... ],
    "unknown_ownership_modules": [ ... ],
    "missing_dependencies": []
  }
}
```

Backward compatibility is maintained — the service can load legacy flat-format indexes (schema_version 2.1) without the metadata/graph wrapper.

## Query API (repo_intelligence.query.RepositoryIndex)

All query methods consume RepositoryGraphService exclusively. No module duplicates traversal logic or inspects raw graph internals.

### Capability Queries

| Method | Description |
|--------|-------------|
| `list_capabilities()` | List all capability nodes |
| `show_capability(id)` | Show detailed information about a capability (engines, routers, services, repositories, endpoints, tests, docs, deps, tables) |

### Ownership Queries

| Method | Description |
|--------|-------------|
| `list_nodes_by_ownership(ownership)` | Return all nodes with given ownership category |
| `list_modules_with_unknown_ownership()` | List unclassified modules |

### Gap/Evidence Queries

| Method | Description |
|--------|-------------|
| `list_orphan_modules()` | Modules not referenced by any capability |
| `list_endpoints_with_no_verification_evidence()` | Endpoints lacking a verifies edge from capability |
| `list_capabilities_with_no_documentation_evidence()` | Capabilities without documents edge |
| `list_missing_modules()` | Modules referenced by capabilities but not found |
| `list_missing_dependencies()` | Capability dependencies that don't resolve |

### Path & Impact Analysis

| Method | Description |
|--------|-------------|
| `trace(node_id, max_depth)` | Return all paths starting from a node |
| `impact(path, max_depth)` | Compute downstream impact of file changes |
| `search(text)` | Search across entity types by text term |
| `why(path)` | Explain all relationships involving a node |

## CLI Entry Point (`__main__.py`)

All existing CLI commands are preserved and continue to work:

```bash
# Generate the canonical repository index
python -m repo_intelligence --generate

# Show index summary statistics
python -m repo_intelligence --stats

# Query a capability
python -m repo_intelligence --query reconciliation

# List orphan modules
python -m repo_intelligence --orphan-modules

# List endpoints without test coverage (evidence-based)
python -m repo_intelligence --no-verification-evidence

# List capabilities without documentation
python -m repo_intelligence --no-documentation-evidence

# Find owner of a router
python -m repo_intelligence --owner accounts

# Find tests for a module
python -m repo_intelligence --tests-for src/engines/loan_engine/foreclosure.py

# Compute impact of a file change
python -m repo_intelligence --impact src/routers/reconciliation.py

# Trace all paths from a node
python -m repo_intelligence --trace capability:account_management

# Show health metrics
python -m repo_intelligence --health

# Explain relationships for a node
python -m repo_intelligence --why src/routers/reconciliation.py

# Search across entities
python -m repo_intelligence --search loan
```

## Scanner Architecture

Each scanner operates independently and returns nodes + edges tuples that the indexer merges:

| Scanner | Source | Discovers |
|---------|--------|-----------|
| MetadataScanner | `backend/tests/generated/`, `package.json`, `requirements.txt` | Capabilities, generated artifacts, dependencies |
| BackendScanner | `backend/src/` | Python packages, modules, routers, endpoints, imports |
| FrontendScanner | `frontend/` | Routes, components, hooks, modules, API client functions |
| ApiScanner | `api-map.json`, `contract-registry.json`, `api-schema.json` | OpenAPI endpoints, API contracts |
| TestScanner | `backend/tests/`, `frontend/__tests__/` | Test suites, capability-test mappings |
| DocsScanner | `docs/`, `memory-bank/`, root `.md` | Documentation files |
| WorkflowScanner | `.github/workflows/` | GitHub Actions workflows |
| ScriptScanner | `scripts/`, `backend/scripts/`, `frontend/scripts/` | Repository scripts |
| MigrationScanner | `backend/scripts/migration_*.py` | Database migrations |

## Semantic Ownership Model (Phase 2.1)

Every node carries an `ownership` property classifying responsibility:

| Category | Description | Example |
|----------|-------------|---------|
| **capability** | Owned by a specific business capability | Business logic modules, test suites, API documentation |
| **shared_infrastructure** | Cross-cutting components used by multiple capabilities | Common utilities, authentication middleware |
| **generated** | Auto-produced from canonical sources | index.json, endpoint nodes from api-map.json |
| **framework** | Configuration and glue code | package.json, requirements.txt, CI workflows |
| **utility** | General-purpose helper code | Scripts, data transformers |
| **external** | Third-party or external dependency references | External contract integrations |
| **unknown** | Ownership not yet determined — flagged as suspicious | Unclassified modules |

The `unknown` category is the only condition reported as suspicious.

## Validation Model

The `validate()` method on RepositoryGraphService checks:

1. **Node uniqueness** — No duplicate node IDs
2. **Referential integrity** — Every edge references existing nodes
3. **No duplicate edges** — Same (source, target, relationship) pair appears once
4. **Required fields present** — Nodes and edges have all required attributes

Validation output includes errors, warnings, node count, and edge count.

## Backward Compatibility Guarantees

1. **Index format**: Legacy flat-format indexes (schema_version 2.1) are still supported alongside the new versioned format (schema_version 2.2+).

2. **API stability**: The RepositoryIndex query API remains unchanged — all existing methods continue to work.

3. **CLI compatibility**: All command-line options and their behaviors are preserved.

4. **Scanner interfaces**: Scanner base classes and scan() return signatures are unchanged — existing scanners work without modification.

5. **Graph data structures**: GraphNode and GraphEdge dataclasses maintain backward-compatible field layouts.

6. **Module import paths**: All public export symbols remain in their original modules; new additions are exported via `__init__.py`.

## Extension Rules

To extend the Repository Intelligence Runtime:

1. **New scanners**: Inherit from `BaseScanner`, implement `scan()`, register in `scanner/__init__.py`, add to the scanner list in `RepositoryBuilder.build()`.

2. **New node types**: Add to `NODE_TYPES` frozenset in `schema.py`.

3. **New relationship types**: Add to `RELATIONSHIP_TYPES` frozenset in `schema.py`.

4. **New ownership classes**: Add to `OWNERSHIP_CLASSES` frozenset in `schema.py` and extend `_classify_ownership()` in `builder.py`.

5. **New query methods**: Extend `RepositoryIndex` using RepositoryGraphService methods only.

6. **Index schema evolution**: Increment `schema_version` when breaking changes are made; loader maintains support for prior versions.

## Testing

Regression tests are located in `repo_intelligence/tests/` and cover:

- ✅ Graph loading (both legacy and new index formats)
- ✅ Node/edge lookup and filtering
- ✅ Traversal (successors, predecessors, neighbors, paths)
- ✅ Statistics and validation
- ✅ Builder operation and index writing
- ✅ Query API methods (capabilities, ownership, gaps, trace, impact)
- ✅ Impact analysis
- ✅ Health metrics calculation
- ✅ CLI entry point preservation

Tests use synthetic graphs — no actual repository scanning required.

## Known Limitations

1. **Path finding**: The `find_paths()` implementation uses a simplified DFS that may not scale to very large graphs with high branching factors. For production use, consider capping depth or using more sophisticated algorithms.

2. **Memory usage**: The entire graph is loaded into memory. For extremely large repositories (>100k nodes), consider streaming approaches or database-backed storage.

3. **Scanner coverage**: Some third-party tool outputs (e.g., Coverity, SonarQube) are not yet integrated. These would require new scanner implementations.

4. **Ownership classification**: Heuristic-based ownership assignment may produce false negatives. Manual review of `unknown` ownership modules is recommended.

5. **Impact analysis**: Currently follows only outgoing edges from the start node. Bidirectional impact analysis (both upstream and downstream) could be added as an option.

## Migration Guide

If you were previously using `RepositoryIndexer` directly, it now delegates to `RepositoryBuilder`. The interface remains compatible:

```python
from repo_intelligence.index import RepositoryIndexer

indexer = RepositoryIndexer()
graph = indexer.build()  # Works as before
indexer.write_index()    # Works as before
```

For new development, prefer the explicit builder pattern:

```python
from repo_intelligence.builder import RepositoryBuilder

builder = RepositoryBuilder()
graph = builder.build()
builder.validate()
builder.write_index()
```

Query code should use `RepositoryIndex` which internally uses `RepositoryGraphService`:

```python
from repo_intelligence.query import RepositoryIndex

idx = RepositoryIndex()
cap = idx.show_account("reconciliation")
```

## Stability Declaration

The Repository Intelligence Runtime is now **feature complete (v1.0)**. The architecture has been stabilized through:

- **Phase 1**: RepositoryGraphService as single graph access interface ✓
- **Phase 2**: Versioned index format with metadata separation ✓
- **Phase 3**: Builder separated from query/runtime logic ✓
- **Phase 4**: All modules consume RepositoryGraphService ✓
- **Phase 5**: Regression tests covering key functionality ✓
- **Phase 6**: Lazy loading and caching implemented ✓
- **Phase 7**: Updated documentation with architecture diagram ✓

Future contributions should focus on bug fixes, metadata extensions, and compatibility updates rather than architectural redesign.
