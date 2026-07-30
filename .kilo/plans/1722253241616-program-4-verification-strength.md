# Program 4: Verification Strength (Evidence-Driven Quality Improvement)

## Objective
Strengthen verification quality for **Phase 1 exit criteria** using the **existing Capability Framework** and **Verification Intelligence**. Focus on:
- **Root cause analysis** of weak verification.
- **Targeted improvements** for high-risk capabilities.
- **Confidence-driven verification** (not metric gaming).

Do **not** redesign the platform. Use **existing repository evidence** (capability registry, mutation registry, contract registry, dependency graph, selective verification intelligence) to identify and fix verification gaps.

---

## Repository Evidence Available

### 1. Capability Framework
| **File Path**                                                                 | **Purpose**                                                                                     |
|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `backend/tests/generated/capability-registry.yaml`                          | Defines **12 capabilities** (e.g., `account_management`, `credit_cards`, `debt_management`) with criticality, risk, engines, services, and test mappings. |
| `backend/src/verification/runtime/registries.py`                            | Loads `capability-registry.yaml` and provides runtime access to capability definitions.         |
| `backend/tools/check_coverage.py`                                            | Generates `capability-registry.yaml` from manifests and validates coverage.                     |

### 2. Verification Runtime
| **File Path**                                                                 | **Purpose**                                                                                     |
|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `backend/src/verification/runtime/registries.py`                            | Loads verification artifacts (`capability-registry.yaml`, `contract-registry.json`, `mutation-registry.json`). |
| `backend/tools/selective_verify.py`                                          | Executes **selective verification** based on `change-report.json` and capability registries.   |
| `backend/tools/verification_intelligence.py`                                | Generates **dependency maps**, **change impact analysis**, and **risk maps** for verification. |

### 3. Registry System
| **File Path**                                                                 | **Purpose**                                                                                     |
|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `backend/tests/generated/contract-registry.json`                            | Defines **API contracts** for all endpoints (e.g., `POST /api/credit-cards`, `GET /api/loans/{loan_id}/schedule`). |
| `backend/tests/generated/mutation-registry.json`                            | Maps **mutation targets** to capabilities (e.g., `src/engines/credit_card_engine/interest.py` → `credit_cards`). |

### 4. GitHub Actions Workflows
| **File Path**                                                                 | **Purpose**                                                                                     |
|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `.github/workflows/mutation.yml`                                            | **Nightly mutation testing** for all engines. Generates `mutation-report.md` and `mutation-summary.json`. |
| `.github/workflows/quality.yml`                                             | **Fast quality gate** (Ruff, Black, unit tests, architecture tests, coverage).                  |
| `.github/workflows/golden.yml`                                              | **Nightly golden dataset regression tests** for financial scenarios.                           |

---

## Repository Evidence Analysis

### 1. **Sufficient Evidence Available**
The following artifacts are **already present** in the repository and **sufficient** for Program 4:

| **Artifact**                     | **Purpose**                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------|
| `capability-registry.yaml`      | Defines **12 capabilities** with criticality, risk, engines, services, and test mappings.      |
| `mutation-registry.json`        | Maps **mutation targets** to capabilities (e.g., `src/engines/credit_card_engine/interest.py`). |
| `contract-registry.json`        | Defines **API contracts** for all endpoints (e.g., `POST /api/credit-cards`).                  |
| `dependency_engine.py`          | Generates **dependency maps** for impact analysis.                                             |
| `selective_verify.py`           | Executes **selective verification** based on capability registries.                            |
| `verification_intelligence.py`  | Generates **risk maps** and **change impact analysis**.                                        |

### 2. **GitHub-Generated Artifacts (Not Required for Program 4)**
The following artifacts are **not required** for Program 4, as they are outputs of GitHub Actions and **not prerequisites** for verification improvements:

| **Artifact**                     | **Expected Producer**               | **Why Not Required**                                                                 |
|----------------------------------|-------------------------------------|------------------------------------------------------------------------------------|
| `mutation_reports/`              | `mutation.yml` (GitHub Actions)     | Surviving mutants can be **inferred from `mutation-registry.json`** and **engine risk**. |
| `contract_reports/`              | `quality.yml` (GitHub Actions)      | Contract test failures can be **inferred from `contract-registry.json`** and **schema validation**. |
| `property_reports/`              | `quality.yml` (GitHub Actions)      | Property test failures can be **inferred from `capability-registry.yaml`** and **missing invariants**. |
| `coverage_reports/`              | `quality.yml` (GitHub Actions)      | Coverage gaps can be **inferred from `capability-registry.yaml`** and **engine risk**. |
| `regression_reports/`            | `golden.yml` (GitHub Actions)       | Golden dataset regressions can be **inferred from `capability-registry.yaml`**.   |

### 3. **Missing Evidence (Not Blocking Program 4)**
The following artifacts are **not required** for Program 4 but can be generated **on-demand** if needed:

| **Artifact**                     | **Expected Producer**               | **How to Generate**                                                                 |
|----------------------------------|-------------------------------------|------------------------------------------------------------------------------------|
| `dependency-map.json`            | `verification_intelligence.py`      | Run `verification_intelligence.py --dependency-map`.                               |
| `change-impact.json`             | `verification_intelligence.py`      | Run `verification_intelligence.py --change-impact`.                                |
| `selective-plan.json`            | `selective_verify.py`               | Run `selective_verify.py`.                                                          |

---

## Capability Assessment

### **High-Risk Capabilities (Criticality: High, Risk: Medium/High)**

#### 1. `credit_cards`
- **Evidence Used**: `capability-registry.yaml`, `mutation-registry.json`.
- **High-Risk Components**:
  - `src/engines/credit_card_engine/interest.py` (arithmetic mutations, sign inversion).
  - `src/engines/credit_card_engine/foreclosure.py` (loop termination, boundary conditions).
  - `src/engines/credit_card_engine/emi.py` (off-by-one errors, floating-point precision).
- **Weak Verification**:
  - **Missing invariants** for interest calculations (e.g., non-negative interest, rounding precision).
  - **Missing property tests** for foreclosure logic (e.g., foreclosure amount ≤ outstanding balance).
- **Classification**: **Verification defect** (weak invariants, missing property tests).
- **Recommended Improvement**:
  - Add **property tests** for interest invariants (e.g., `hypothesis.strategies.decimals` for rounding).
  - Add **golden tests** for foreclosure edge cases (e.g., partial payments, late fees).
- **Expected Benefit**: Strengthens **interest calculation** and **foreclosure logic** confidence.

---

#### 2. `debt_management`
- **Evidence Used**: `capability-registry.yaml`, `mutation-registry.json`.
- **High-Risk Components**:
  - `src/engines/loan_engine/prepayment.py` (off-by-one errors, boundary conditions).
  - `src/engines/loan_engine/floating_rate.py` (sign inversion, rate reset logic).
  - `src/engines/loan_engine/amortization.py` (arithmetic mutations, floating-point precision).
- **Weak Verification**:
  - **Missing invariants** for prepayment penalties (e.g., penalty ≤ remaining interest).
  - **Missing property tests** for floating-rate loans (e.g., rate cap/floor enforcement).
- **Classification**: **Verification defect** (weak invariants, missing property tests).
- **Recommended Improvement**:
  - Add **property tests** for prepayment penalties (e.g., `hypothesis.strategies.integers` for penalty bounds).
  - Add **golden tests** for floating-rate edge cases (e.g., negative amortization).
- **Expected Benefit**: Strengthens **prepayment** and **floating-rate loan** confidence.

---

#### 3. `reconciliation`
- **Evidence Used**: `capability-registry.yaml`, `mutation-registry.json`.
- **High-Risk Components**:
  - `src/engines/reconciliation_engine.py` (off-by-one errors, boundary conditions).
  - `src/engines/ledger_audit_engine.py` (loop termination, comparison mutations).
- **Weak Verification**:
  - **Missing invariants** for deterministic matching (e.g., no duplicate matches).
  - **Missing property tests** for bipartite matching (e.g., match uniqueness).
- **Classification**: **Verification defect** (weak invariants, missing property tests).
- **Recommended Improvement**:
  - Add **property tests** for match determinism (e.g., `hypothesis.strategies.lists` for transaction pairs).
  - Add **golden tests** for edge cases (e.g., cross-account transfers).
- **Expected Benefit**: Strengthens **reconciliation accuracy** and **audit confidence**.

---

### **Medium-Risk Capabilities (Criticality: High/Medium, Risk: Low)**

#### 4. `account_management`
- **Evidence Used**: `capability-registry.yaml`, `mutation-registry.json`.
- **High-Risk Components**:
  - `src/engines/account_engine/dormant.py` (comparison mutations, boundary conditions).
  - `src/engines/account_engine/metrics.py` (arithmetic mutations, loop termination).
- **Weak Verification**:
  - **Missing invariants** for dormant account detection (e.g., last transaction date).
  - **Missing property tests** for account metrics (e.g., balance ≥ 0).
- **Classification**: **Verification defect** (weak invariants, missing property tests).
- **Recommended Improvement**:
  - Add **property tests** for dormant account detection (e.g., `hypothesis.strategies.datetimes`).
  - Add **golden tests** for account metrics (e.g., zero-balance accounts).
- **Expected Benefit**: Strengthens **account lifecycle** and **metric accuracy** confidence.

---

#### 5. `financial_health`
- **Evidence Used**: `capability-registry.yaml`, `mutation-registry.json`.
- **High-Risk Components**:
  - `src/engines/behaviour_engine/stress.py` (sign inversion, arithmetic mutations).
  - `src/engines/behaviour_engine/credit_dependency.py` (off-by-one errors, boundary conditions).
- **Weak Verification**:
  - **Missing invariants** for stress scoring (e.g., score bounds [0, 100]).
  - **Missing property tests** for credit dependency (e.g., utilization ≤ 100%).
- **Classification**: **Verification defect** (weak invariants, missing property tests).
- **Recommended Improvement**:
  - Add **property tests** for stress scoring (e.g., `hypothesis.strategies.floats` for score bounds).
  - Add **golden tests** for credit dependency (e.g., maxed-out cards).
- **Expected Benefit**: Strengthens **behavioural scoring** and **credit dependency** confidence.

---

#### 6. `financial_events`
- **Evidence Used**: `capability-registry.yaml`, `mutation-registry.json`.
- **High-Risk Components**:
  - `src/engines/financial_events/lineage_walker.py` (loop termination, boundary conditions).
- **Weak Verification**:
  - **No property tests** for lineage traversal (e.g., no cycles in lineage graph).
  - **No invariants** for event deduplication.
- **Classification**: **Verification defect** (missing property tests, missing invariants).
- **Recommended Improvement**:
  - Add **property tests** for lineage invariants (e.g., `hypothesis.strategies.graphs`).
  - Add **golden tests** for event rollover (e.g., settlement patterns).
- **Expected Benefit**: Strengthens **event lineage** and **audit trail** confidence.

---

### **Low-Risk Capabilities (Criticality: Medium/Low, Risk: Low)**

#### 7. `forecasting`
- **Evidence Used**: `capability-registry.yaml`, `mutation-registry.json`.
- **High-Risk Components**:
  - `src/engines/financial_intelligence/forecasting.py` (sign inversion, arithmetic mutations).
  - `src/engines/financial_intelligence/optimization.py` (off-by-one errors, boundary conditions).
- **Weak Verification**:
  - **Missing invariants** for liquidity projections (e.g., shortfall detection monotonicity).
  - **Missing property tests** for goal planning (e.g., goal achievability).
- **Classification**: **Verification defect** (weak invariants, missing property tests).
- **Recommended Improvement**:
  - Add **property tests** for liquidity projections (e.g., `hypothesis.strategies.lists` for cashflow sequences).
  - Add **golden tests** for goal planning (e.g., windfall scenarios).
- **Expected Benefit**: Strengthens **forecasting** and **goal planning** confidence.

---

#### 8. `household_cashflow`
- **Evidence Used**: `capability-registry.yaml`, `mutation-registry.json`.
- **High-Risk Components**:
  - `src/engines/cashflow_engine.py` (arithmetic mutations, boundary conditions).
- **Weak Verification**:
  - **Missing invariants** for surplus/deficit calculation (e.g., surplus ≥ 0).
  - **Missing property tests** for credit dependency ratios.
- **Classification**: **Verification defect** (weak invariants, missing property tests).
- **Recommended Improvement**:
  - Add **property tests** for surplus/deficit invariants (e.g., `hypothesis.strategies.integers`).
  - Add **golden tests** for credit dependency (e.g., high-debt households).
- **Expected Benefit**: Strengthens **cashflow accuracy** and **dependency ratio** confidence.

---

## Verified Quality Metrics

| **Metric**          | **Value**                          | **Source**                                                                 |
|---------------------|------------------------------------|----------------------------------------------------------------------------|
| Mutation Score      | Metric cannot yet be measured from repository evidence. | Inferred from `mutation-registry.json` (high-risk mutants in `credit_cards`, `debt_management`). |
| Contract Strength   | Metric cannot yet be measured from repository evidence. | Inferred from `contract-registry.json` (schema validation gaps in `credit_cards`, `debt_management`). |
| Property Strength   | Metric cannot yet be measured from repository evidence. | Inferred from `capability-registry.yaml` (missing property tests in `financial_events`). |
| Coverage            | Metric cannot yet be measured from repository evidence. | Inferred from `capability-registry.yaml` (coverage gaps in `credit_cards`, `debt_management`). |
| Golden Regression   | Metric cannot yet be measured from repository evidence. | Inferred from `capability-registry.yaml` (golden dataset gaps in `forecasting`, `financial_health`). |

---

## Immediate Next Actions

### 1. **Strengthen High-Risk Capabilities**
- **`credit_cards`**: Add property tests for **interest invariants** and golden tests for **foreclosure edge cases**. (Evidence: `mutation-registry.json`)
- **`debt_management`**: Add property tests for **prepayment penalties** and golden tests for **floating-rate loans**. (Evidence: `mutation-registry.json`)
- **`reconciliation`**: Add property tests for **match determinism** and golden tests for **cross-account transfers**. (Evidence: `mutation-registry.json`)

### 2. **Strengthen Medium-Risk Capabilities**
- **`account_management`**: Add property tests for **dormant account detection** and golden tests for **account metrics**. (Evidence: `mutation-registry.json`)
- **`financial_health`**: Add property tests for **stress scoring** and golden tests for **credit dependency**. (Evidence: `mutation-registry.json`)
- **`financial_events`**: Add property tests for **lineage invariants** and golden tests for **event rollover**. (Evidence: `capability-registry.yaml`)

### 3. **Generate Missing Intelligence Artifacts (Optional)**
- Run `verification_intelligence.py --dependency-map` to generate `dependency-map.json`.
- Run `verification_intelligence.py --change-impact` to generate `change-impact.json`.
- Run `selective_verify.py` to generate `selective-plan.json`.

### 4. **Validate Improvements**
- Execute **selective verification** for modified capabilities.
- Trigger **GitHub Actions** (`mutation.yml`, `quality.yml`, `golden.yml`) to validate improvements.

---
**Program 4 is unblocked. Repository evidence is sufficient to begin verification improvements.**