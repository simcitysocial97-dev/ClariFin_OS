# Repository Intelligence Runtime — Final Report (Program 2)

## 1. Repository Architecture

The Repository Intelligence Runtime is a deterministic, analysis-only infrastructure layer that discovers repository structure, cross-references canonical metadata sources, and exposes a query API. It is organized into five phases:

- **Phase 1**: Audit of existing repository metadata sources (no code changes)
- **Phase 2**: Canonical repository graph schema design (data structures only)
- **Phase 3**: Repository scanners that discover structure without executing code
- **Phase 4**: Canonical repository index generation with gap detection
- **Phase 5**: Lightweight Python query interface

The runtime follows the constraint of analysis infrastructure only — no AI planning, orchestration, workflow generation, or autonomous execution.

## 2. Files Created

| File | Purpose |
|------|---------|
| `repo_intelligence/__init__.py` | Package init with public API exports |
| `repo_intelligence/schema.py` | Graph data structures: `GraphNode`, `GraphEdge`, `RepositoryGraph` |
| `repo_intelligence/index.py` | `RepositoryIndexer` — orchestrates all scanners, produces canonical index |
| `repo_intelligence/query.py` | `RepositoryIndex` — query API with 10 query methods |
| `repo_intelligence/__main__.py` | CLI entry point with `--generate`, `--query`, `--orphan-modules`, `--untested`, `--undocumented`, `--owner`, `--tests-for`, `--stats` |
| `repo_intelligence/generate_index.py` | Convenience script for index generation |
| `repo_intelligence/scanner/__init__.py` | Scanner package init with all scanner exports |
| `repo_intelligence/scanner/base.py` | `BaseScanner` and `ScanResult` base classes |
| `repo_intelligence/scanner/metadata_scanner.py` | Loads capability registry and generated artifacts |
| `repo_intelligence/scanner/backend_scanner.py` | Discovers Python modules, routers, endpoints, imports |
| `repo_intelligence/scanner/frontend_scanner.py` | Discovers TS/React modules, components, hooks, API client functions |
| `repo_intelligence/scanner/api_scanner.py` | Loads OpenAPI spec and API maps |
| `repo_intelligence/scanner/test_scanner.py` | Discovers test suites and capability-test mappings |
| `repo_intelligence/scanner/docs_scanner.py` | Discovers documentation files and links to capabilities |
| `repo_intelligence/scanner/workflow_scanner.py` | Discovers GitHub Actions workflows |
| `repo_intelligence/scanner/script_scanner.py` | Discovers scripts across the repo |
| `repo_intelligence/scanner/migration_scanner.py` | Discovers database migration scripts |
| `repo_intelligence/index.json` | Generated canonical repository index |
| `repo_intelligence/README.md` | Package documentation |

## 3. Files Modified

| File | Change |
|------|--------|
| `repo_intelligence/scanner/frontend_scanner.py` | Fixed API client discovery regex to handle template literal fetch patterns (`${API_BASE}/api/...`) |
| `repo_intelligence/index.py` | Added `method` and `endpoint_path` fields to untested endpoint gap data |

## 4. Existing Metadata Sources Discovered

### Capability Registry
- `backend/tests/generated/capability-registry.yaml` — Canonical capability registry with 11 capabilities
- `backend/tests/generated/dependency-map.json` — Generated dependency graph with 647 edges
- `backend/tests/generated/capability-registry.yaml` — Capability metadata including engines, services, routers, repositories, tables, tests

### API Specifications
- `backend/tests/generated/api-map.json` — Full endpoint metadata with 103 endpoints and capability mapping
- `backend/tests/generated/contract-registry.json` — Router-level contract registry with request/response schemas
- `frontend/api-schema.json` — OpenAPI 3.1.0 specification (90,909 bytes)

### Generated Artifacts
- `backend/tests/generated/` — 32 generated artifacts including mutation-registry.json, risk-map.json, coverage.json, etc.

### Documentation
- `docs/` — 105 documentation files across multiple stages
- `memory-bank/` — Project brief, active context, architecture map
- Root-level `.md` files — CAPABILITY_AUDIT.md, CAPABILITY_COVERAGE.md, etc.

### CI/CD
- `.github/workflows/` — 10 workflow files (ci.yml, backend.yml, frontend.yml, mutation.yml, etc.)
- `.github/scripts/` — CI helper scripts

### Verification
- `verification/runtime/` — Verification runtime CLI and registries
- `backend/src/verification/intelligence/` — 14 verification intelligence modules

### Scripts
- `scripts/` — Root-level scripts (verify-fast.sh)
- `backend/scripts/` — Migration scripts (migration_002 through migration_007)
- `backend/tools/` — Tool scripts for validation, mutation, coverage

### Frontend
- `frontend/lib/api/client.ts` — API client with 10 fetch functions
- `frontend/hooks/` — 5 custom hooks
- `frontend/components/` — 249 React components
- `frontend/app/` — 12 Next.js app router routes

### Backend
- `backend/src/routers/` — 29 router files
- `backend/src/engines/` — 15+ engine packages
- `backend/src/services/` — 26 service files
- `backend/src/repositories/` — 26 repository files
- `backend/src/models/` — 21 model files

## 5. Canonical Metadata Source Selected for Each Domain

| Domain | Canonical Source | Rationale |
|--------|-----------------|-----------|
| Capabilities | `backend/tests/generated/capability-registry.yaml` | Single source of truth for capability definitions, components, and dependencies |
| API Endpoints | `backend/tests/generated/api-map.json` | Generated from router analysis with full capability mapping |
| API Contracts | `backend/tests/generated/contract-registry.json` | Router-level contract metadata with request/response schemas |
| Dependencies | `backend/tests/generated/dependency-map.json` | Generated dependency graph |
| OpenAPI Spec | `frontend/api-schema.json` | Auto-generated from backend OpenAPI schema |
| Test Structure | `backend/tests/` directory layout | Directory-based test organization with type classification |
| Documentation | `docs/`, `memory-bank/`, root `.md` files | All documentation in dedicated directories |
| Workflows | `.github/workflows/` | GitHub Actions workflow definitions |
| Migrations | `backend/scripts/migration_*.py` | Numbered migration scripts with table effects |
| Frontend API Client | `frontend/lib/api/client.ts` | Single API client file with all fetch functions |

## 6. Repository Graph Overview

The repository graph contains **1,119 nodes** and **1,999 edges** across 17 node types and 9 relationship types.

### Node Type Distribution

| Node Type | Count | Description |
|-----------|-------|-------------|
| `module` | 574 | Python/TypeScript modules |
| `component` | 249 | React components |
| `documentation` | 105 | Documentation files |
| `generated_artifact` | 32 | Generated artifacts |
| `endpoint` | 33 | HTTP endpoints |
| `database_table` | 23 | Database tables |
| `package` | 29 | Python packages |
| `test_suite` | 16 | Test suite directories |
| `workflow` | 10 | GitHub Actions workflows |
| `script` | 10 | Repository scripts |
| `capability` | 11 | Capabilities from registry |
| `frontend_route` | 12 | Next.js app router routes |
| `migration` | 6 | Database migrations |
| `hook` | 5 | Custom React hooks |
| `requirements` | 2 | Python requirements files |
| `api` | 1 | OpenAPI specification |
| `package_json` | 1 | Frontend package.json |

### Relationship Type Distribution

| Relationship | Count | Description |
|-------------|-------|-------------|
| `documents` | 640 | Capability → documentation links |
| `depends_on` | 732 | Capability/module dependencies |
| `implements` | 313 | Capability → module/endpoint implementations |
| `imports` | 261 | Module import relationships |
| `owns` | 58 | Capability → database table ownership |
| `calls` | 51 | Module call relationships |
| `tests` | 73 | Capability → test suite links |
| `verifies` | 36 | Test suite → endpoint verification |
| `consumes` | 6 | API client → endpoint consumption |

## 7. Scanner Coverage

| Scanner | Status | Coverage |
|---------|--------|----------|
| MetadataScanner | Working | Capability registry, generated artifacts, dependencies |
| BackendScanner | Working | Python packages, modules, routers, endpoints, imports |
| FrontendScanner | Working (fixed) | Routes, components, hooks, modules, API client functions |
| ApiScanner | Working | OpenAPI spec, api-map.json, contract-registry.json |
| TestScanner | Working | Test suites, capability-test mappings |
| DocsScanner | Working | Documentation files with keyword-based capability matching |
| WorkflowScanner | Working | GitHub Actions workflows and scripts |
| ScriptScanner | Working | Root, backend, and frontend scripts |
| MigrationScanner | Working | Database migration scripts with table effects |

### Scanner Fix Applied

The `FrontendScanner._discover_api_client` method was fixed to properly handle the template literal fetch pattern used in `frontend/lib/api/client.ts`. The original regex patterns did not match `fetch(\`${API_BASE}/api/...\`)` calls. The fix uses a simpler pattern that captures the path after `${API_BASE}` and associates fetch calls with their containing functions using position-based analysis.

## 8. Repository Index Statistics

- **Total nodes**: 1,119
- **Total edges**: 1,999
- **Node types**: 17
- **Edge types**: 9
- **Capabilities**: 11
- **Endpoints**: 33
- **Orphan modules**: 127
- **Untested endpoints**: 33
- **Undocumented APIs**: 11
- **Missing modules**: 0
- **Missing dependencies**: 0

### Key Findings

1. **All 33 endpoints are untested** — no capability has `verifies` edges to any endpoint node
2. **All 11 capabilities are undocumented** — no `documents` edges from capabilities to documentation nodes
3. **127 orphan modules** — modules not referenced by any capability (mostly utility/helper modules)
4. **0 missing modules** — all capability-referenced modules exist on disk
5. **0 missing dependencies** — all capability dependencies resolve to known capabilities

## 9. Query API Examples

### Show Capability

```python
from repo_intelligence.query import RepositoryIndex
idx = RepositoryIndex()
result = idx.show_capability("reconciliation")
# Returns: capability node, engines, routers, services, repositories, endpoints, tests, documentation, dependencies, tables, frontend_consumers
```

### Find Owner of Router

```python
idx.find_owner_of_router("reconciliation")
# Returns: {"router": {...}, "owners": ["capability:reconciliation"]}
```

### Find Tests for Module

```python
idx.find_tests_for_module("src/engines/loan_engine/foreclosure.py")
# Returns: list of test module nodes with capability association
```

### Find Frontend Consumers of Endpoint

```python
idx.find_frontend_consumers_of_endpoint("/api/v1/accounts")
# Returns: list of frontend components that consume the endpoint
```

### Find Documentation for Capability

```python
idx.find_documentation_for_capability("reconciliation")
# Returns: list of documentation nodes linked to the capability
```

### List Orphan Modules

```python
idx.list_orphan_modules()
# Returns: list of modules not referenced by any capability
```

### List Undocumented APIs

```python
idx.list_undocumented_apis()
# Returns: list of capabilities without documentation
```

### List Untested Endpoints

```python
idx.list_untested_endpoints()
# Returns: list of endpoints without test coverage
```

### List Missing Modules

```python
idx.list_missing_modules()
# Returns: list of modules referenced by capabilities but not found on disk
```

### CLI Usage

```bash
python -m repo_intelligence --generate          # Generate index
python -m repo_intelligence --stats             # Show index statistics
python -m repo_intelligence --query reconciliation  # Show capability details
python -m repo_intelligence --orphan-modules    # List orphan modules
python -m repo_intelligence --untested          # List untested endpoints
python -m repo_intelligence --undocumented      # List undocumented capabilities
python -m repo_intelligence --owner accounts    # Find owner of router
python -m repo_intelligence --tests-for src/engines/loan_engine/foreclosure.py  # Find tests
```

## 10. Remaining Gaps for Program 3

### Query API Enhancements
1. **Change impact analysis** — Given a file path, find all capabilities, endpoints, and tests that would be affected
2. **Dependency chain traversal** — Show full dependency chains between capabilities
3. **Test coverage scoring** — Calculate coverage scores per capability based on test types present
4. **Architecture compliance checks** — Verify that import relationships follow the allowed layer hierarchy

### Scanner Enhancements
1. **Servers scanner** — Discover MCP server structure in `servers/` directory
2. **Configuration scanner** — Discover and index `pyproject.toml`, `setup.cfg`, `tsconfig.json`, etc.
3. **CI target scanner** — Parse CI workflow targets and map them to capabilities
4. **Memory bank scanner** — Index memory-bank documents with structured metadata

### Index Enhancements
1. **Incremental updates** — Support delta updates to the index when files change
2. **Content hashing** — Add content hashes to nodes for change detection
3. **Historical tracking** — Track index changes over time
4. **Export formats** — Support export to GraphML, Neo4j Cypher, and other graph formats

### Verification Integration
1. **Verification matrix integration** — Link test suites to verification matrix entries
2. **Mutation testing integration** — Map mutation targets to capabilities and endpoints
3. **Contract test integration** — Link contract tests to API endpoints and schemas

### Documentation
1. **API documentation generation** — Auto-generate API documentation from the index
2. **Architecture diagram generation** — Produce architecture diagrams from the graph
3. **Capability health dashboard** — Visualize capability health based on test coverage, documentation, and dependencies