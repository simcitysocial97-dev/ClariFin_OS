# Engineering Platform API — Version 1.0.0

**Stability:** STABLE  
**Deprecation Policy:** None (v1.0.0 milestone — no deprecations)  
**Future Compatibility:** v1.0.x for patches, v1.1 for additions, v2.0 for breaking changes

---

## CLI Commands

### runtime/verify.py

The primary entry point for Engineering Platform verification.

#### `python runtime/verify.py quick`
**Purpose:** Fast local checks  
**Arguments:** None  
**Output:** Verification report at `runtime/generated/verification-report.md`  
**Execution Time:** ~2-3 minutes

#### `python runtime/verify.py backend`
**Purpose:** Full backend verification suite  
**Arguments:** None  
**Output:** Verification report, cache, cross-layer map artifacts  
**Execution Time:** ~5-10 minutes  
**Steps Executed:**
1. Ruff lint check
2. MyPy type check
3. Backend unit tests
4. Backend integration tests
5. Schemathesis contract tests
6. Evidence aggregation

#### `python runtime/verify.py frontend`
**Purpose:** Full frontend verification suite  
**Arguments:** None  
**Output:** Verification report, cache, cross-layer map artifacts  
**Execution Time:** ~4-8 minutes  
**Steps Executed:**
1. ESLint check
2. TypeScript type check
3. Vitest unit tests
4. Frontend build
5. Evidence aggregation

#### `python runtime/verify.py contracts`
**Purpose:** Contract validation for all capabilities  
**Arguments:** None  
**Output:** Contract verification report  
**Execution Time:** ~3-5 minutes

#### `python runtime/verify.py graph`
**Purpose:** Graph integrity and cross-layer validation  
**Arguments:** None  
**Output:** Graph integrity report  
**Execution Time:** ~1 minute

#### `python runtime/verify.py full`
**Purpose:** Complete verification suite (all profiles combined)  
**Arguments:** None  
**Output:** Full verification report  
**Execution Time:** ~15-20 minutes

---

### Status Commands

#### `python runtime/verify.py status`
**Purpose:** Show verification status  
**Arguments:** None  
**Output:** Current status text to stdout

#### `python runtime/verify.py metrics`
**Purpose:** Show verification metrics  
**Arguments:** None  
**Output:** JSON metrics to stdout

#### `python runtime/verify.py history`
**Purpose:** Show verification history  
**Arguments:** None  
**Output:** Historical run data

#### `python runtime/verify.py deps <file_path>`
**Purpose:** Show dependency graph for a file  
**Arguments:** `<file_path>` - Path to source file  
**Output:** Dependency tree

#### `python runtime/verify.py verify-status`
**Purpose:** Check if verification has run  
**Arguments:** None  
**Output:** Status indicator

---

### Analytics Commands

#### `python runtime/verify.py analytics`
**Purpose:** Generate engineering analytics  
**Arguments:** None  
**Output:** JSON analytics report

#### `python runtime/verify.py health`
**Purpose:** Generate engineering health report  
**Arguments:** None  
**Output:** Markdown health report

---

### Diagnostic Commands

#### `python runtime/verify.py diagnose`
**Purpose:** Diagnose changed files  
**Arguments:** None (uses git diff)  
**Output:** Diagnostic report

#### `python runtime/verify.py affected`
**Purpose:** Show affected tests for changed files  
**Arguments:** None (uses git diff)  
**Output:** Test impact analysis

#### `python runtime/verify.py repair`
**Purpose:** Suggest repairs for issues  
**Arguments:** None (uses git diff)  
**Output:** Repair suggestions

#### `python runtime/verify.py risk`
**Purpose:** Compute risk report  
**Arguments:** None (uses git diff)  
**Output:** Risk assessment

---

### Integrity Commands

#### `python runtime/verify.py integrity`
**Purpose:** Evaluate architectural integrity  
**Arguments:** None  
**Output:** Integrity report (28 rules, 0 violations guaranteed at v1.0.0)  
**Exit Code:** 0 if all rules pass, 1 if violations found

---

### Knowledge Commands

#### `python runtime/verify.py knowledge`
**Purpose:** Build and display knowledge index  
**Arguments:** None  
**Output:** Knowledge index summary

#### `python runtime/verify.py knowledge endpoint <path>`
**Purpose:** Query endpoint by path  
**Arguments:** `<path>` - API endpoint path  
**Output:** Endpoint entry or error

#### `python runtime/verify.py knowledge capability <name>`
**Purpose:** Query capability by name  
**Arguments:** `<name>` - Capability name  
**Output:** Capability entry or error

#### `python runtime/verify.py knowledge workspace <name>`
**Purpose:** Query workspace by name  
**Arguments:** `<name>` - Workspace name  
**Output:** Workspace entry or error

#### `python runtime/verify.py knowledge rule <id>`
**Purpose:** Query integrity rule by ID  
**Arguments:** `<id>` - Rule ID (e.g., ARCH-001)  
**Output:** Rule entry or error

#### `python runtime/verify.py knowledge component <name>`
**Purpose:** Query component by name  
**Arguments:** `<name>` - Component name  
**Output:** Component entry or error

---

## Verification Profiles

| Profile | Scope | Steps | Est. Duration |
|---------|-------|-------|---------------|
| quick | QUICK | Ruff, mypy, unit tests | 3 min |
| backend | BACKEND | Lint, typecheck, unit, integration, contracts, aggregate | 5 min |
| frontend | FRONTEND | Lint, typecheck, vitest, build, aggregate | 4 min |
| contracts | CONTRACTS | Schemathesis, contract tests, aggregate | 3 min |
| graph | REPOSITORY | Graph integrity, cross-layer validation, aggregate | 1 min |
| full | FULL | All profiles combined | 15 min |

---

## Integrity Rule IDs

| ID | Rule Name | Category | Severity |
|----|-----------|----------|----------|
| ARCH-001 | Router may not import Engine | STRUCTURAL | HIGH |
| ARCH-002 | Component may not call API directly | STRUCTURAL | HIGH |
| ARCH-003 | Mapper must not import React | STRUCTURAL | LOW |
| ARCH-004 | Workspace must not perform fetch | STRUCTURAL | HIGH |
| ARCH-005 | Capability required for every endpoint | OWNERSHIP | HIGH |
| ARCH-006 | Every capability requires exactly one mapper | OWNERSHIP | MEDIUM |
| ARCH-007 | Every mapper returns ViewModel | OWNERSHIP | MEDIUM |
| ARCH-008 | No duplicate endpoint ownership | OWNERSHIP | HIGH |
| ARCH-009 | No circular layer dependencies | STRUCTURAL | CRITICAL |
| ARCH-010 | Page must not bypass Workspace registration | EVOLUTION | HIGH |
| ARCH-011 | Service may not import Router | STRUCTURAL | HIGH |
| ARCH-012 | DTO may not import Service | STRUCTURAL | MEDIUM |
| ARCH-013 | Mapper must not import Capability | STRUCTURAL | MEDIUM |
| ARCH-014 | ViewModel must not import Component | STRUCTURAL | LOW |
| ARCH-015 | Workspace must not import Mapper directly | STRUCTURAL | MEDIUM |
| ARCH-016 | Component may not import Engine | STRUCTURAL | HIGH |
| ARCH-017 | DTO may not import Router | STRUCTURAL | MEDIUM |
| ARCH-018 | Capability must not import Component | STRUCTURAL | MEDIUM |
| ARCH-019 | Every mapper is referenced by exactly one capability | OWNERSHIP | MEDIUM |
| ARCH-020 | Every ViewModel is referenced by exactly one mapper | OWNERSHIP | LOW |
| ARCH-021 | Every component belongs to exactly one workspace | OWNERSHIP | MEDIUM |
| ARCH-022 | Every workspace has at least one component | OWNERSHIP | LOW |
| ARCH-023 | Every endpoint must appear in the cross-layer map | EVOLUTION | - |
| ARCH-024 | Every graph renderer is owned by a workspace | EVOLUTION | LOW |
| ARCH-025 | Every public API endpoint has verification coverage | EVOLUTION | MEDIUM |
| ARCH-026 | Every capability has test coverage | EVOLUTION | MEDIUM |
| ARCH-027 | Every mapper file is referenced in the cross-layer map | EVOLUTION | LOW |
| ARCH-028 | No orphaned workspace pages | EVOLUTION | - |

---

## Knowledge Index Entities

### EndpointEntry
- path: string - API endpoint path
- method: string - HTTP method (GET, POST, etc.)
- references: dict - Source file and cross-references
- tags: tuple - Related entry identifiers

### CapabilityEntry
- name: string - Capability name
- references: dict - Source files and dependencies
- tags: tuple - Related endpoints, services, components

### MapperEntry
- name: string - Mapper name
- references: dict - Source files and dependencies
- tags: tuple - Related capabilities, viewModels

### ViewModelEntry
- name: string - ViewModel name
- references: dict - Source files and dependencies
- tags: tuple - Related mappers, components

### WorkspaceEntry
- name: string - Workspace name
- components: list - Owned components
- references: dict - Source files

### ComponentEntry
- name: string - Component name
- workspace: string - Owning workspace
- references: dict - Source files

### GraphRendererEntry
- name: string - Renderer name
- workspace: string - Owning workspace
- references: dict - Source files

### IntegrityRuleEntry
- rule_id: string - Rule identifier (e.g., ARCH-001)
- pass: boolean - Rule compliance status
- violations: list - Any violations found

### VerificationProfileEntry
- name: string - Profile name
- scope: string - Verification scope
- tasks: list - Execution tasks

### RuntimeArtifactEntry
- name: string - Artifact name
- path: string - File path
- type: string - Artifact type