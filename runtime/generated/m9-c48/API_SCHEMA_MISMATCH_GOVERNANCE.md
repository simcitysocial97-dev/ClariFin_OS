# runtime/generated/m9-c48/API_SCHEMA_MISMATCH_GOVERNANCE.md

**Repository SHA:** 35a31f50a0352e407b0936f50a7d7fe80206c16a
**Generated:** 2026-09-04T02:04:30Z
**Milestone:** M48-D2 (GAP-013)

## 1. Historical Defect

Per the M9-C47 CROSS_LAYER_AUDIT:

> Schema mismatch (loan API response-shape). Backend returned a list of
> loans; the frontend expected a wrapped object `{ loans: [...] }`. The
> fix was applied during M9-C32 / C46 reconciliation.

The specific defect class was:
* **Backend** DTO: `LoanListResponse = list[LoanSchema]`.
* **Frontend** consumer: expected `{ loans: LoanSchema[]; total: number }`.
* **Detection**: M9-C30 contract gate (STRUCTURAL freshness dimension).
* **Resolution**: backend DTO was wrapped into a `LoanListResponse` schema.

## 2. Current Contract (machine-verifiable)

The canonical authority is the API Contract Integrity Gate
(`runtime/foundation/verification/api_contracts/gate.py`). It runs four
dimensions:

* STRUCTURAL — schema shape match.
* GENERATED — reproducibility of generated types.
* CONSUMER — frontend consumer match.
* WIRE — actual HTTP wire shape.

The gate is invoked by `.github/workflows/api-contracts.yml` and from
`runtime/verify.py api-contracts`. Its evidence file is
`runtime/generated/api-contract-evidence.json`.

## 3. Governance Mechanism (M48-D2)

This milestone establishes a machine-verifiable governance report that:

1. Invokes the API contract gate to produce fresh evidence.
2. Records the current loan API shape (canonical).
3. Persists a reconciliation summary that distinguishes the historical
   defect from the current contract from the enforcement.

The reconciliation is implemented by
`runtime/foundation/verification/api_schema_governance.py` and is tested
by `runtime/tests/test_m9_c48_api_schema_governance.py`.

## 4. Distinction

| State | Authority |
| --- | --- |
| Historical defect | This document (provenance only) |
| Current contract | API Contract Integrity Gate evidence (`runtime/generated/api-contract-evidence.json`) |
| Current enforcement | `.github/workflows/api-contracts.yml` + `runtime/verify.py api-contracts` |

The historical defect is recorded for traceability but is NOT used as
an authority for current contract decisions. The current contract is
whatever the gate certifies at the current SHA.
