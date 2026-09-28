"""M9-C27/C29 — API Contract Integrity & Drift-Proofing.

Failure classification taxonomy. Every detected drift is assigned exactly one
primary classification from this set so downstream tooling (CI gates, diagnostics,
progress.md) can route it without ambiguity.

Classifications are partitioned into two guarantee categories:

  STRUCTURAL CONTRACT  — shape, type, path, nullability, envelope compatibility
    OPENAPI_STALE       committed artifact drifted from live OpenAPI
    OPENAPI_INVALID     artifact is empty, malformed, or structurally invalid
    GENERATED_TYPES_STALE generated TypeScript drifted from live OpenAPI
    GENERATED_TYPES_INVALID generation failed or produced invalid output
    SCHEMA_DRIFT        Zod/runtime schema scalar range mismatch with OpenAPI
    NULLABILITY_DRIFT   field nullable-status mismatch between OpenAPI and Zod
    FIELD_DRIFT         required field missing from Zod schema
    ENUM_DRIFT          enum variant mismatch
    RESPONSE_ENVELOPE_DRIFT response wrapped/bare array shape mismatch
    ENDPOINT_DRIFT      frontend calls non-existent backend endpoint
    HTTP_METHOD_DRIFT   endpoint exists but HTTP method mismatch
    API_BASE_DRIFT      consumer uses relative URL without API_BASE context
    DEPRECATED_ENDPOINT_CONSUMER consumer references a known-deprecated URL
    CONTRACT_INVENTORY_DRIFT inventory fingerprint changed unexpectedly

  SEMANTIC CONTRACT    — units, ranges, scales, business meaning at runtime
    WIRE_RESPONSE_DRIFT  response content-type or format mismatch
    WIRE_STATUS_DRIFT    unexpected HTTP status code
    SEMANTIC_VALUE_DRIFT runtime value violates documented semantic constraint
                           (e.g. ratio field returning percentage-scale value)

Structural checks operate on schema-level artifacts (OpenAPI, TypeScript, Zod).
Semantic checks operate on live wire responses with deterministic fixture data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Failure classifications (one per detected defect)
# ---------------------------------------------------------------------------


class FailureClassification(str, Enum):
    """Exact contract-failure class. See M9-C27 §17 for the authoritative list."""

    OPENAPI_STALE = "OPENAPI_STALE"
    OPENAPI_INVALID = "OPENAPI_INVALID"
    GENERATED_TYPES_STALE = "GENERATED_TYPES_STALE"
    GENERATED_TYPES_INVALID = "GENERATED_TYPES_INVALID"
    SCHEMA_DRIFT = "SCHEMA_DRIFT"
    NULLABILITY_DRIFT = "NULLABILITY_DRIFT"
    FIELD_DRIFT = "FIELD_DRIFT"
    ENUM_DRIFT = "ENUM_DRIFT"
    RESPONSE_ENVELOPE_DRIFT = "RESPONSE_ENVELOPE_DRIFT"
    ENDPOINT_DRIFT = "ENDPOINT_DRIFT"
    HTTP_METHOD_DRIFT = "HTTP_METHOD_DRIFT"
    API_BASE_DRIFT = "API_BASE_DRIFT"
    DEPRECATED_ENDPOINT_CONSUMER = "DEPRECATED_ENDPOINT_CONSUMER"
    WIRE_RESPONSE_DRIFT = "WIRE_RESPONSE_DRIFT"
    WIRE_STATUS_DRIFT = "WIRE_STATUS_DRIFT"
    SEMANTIC_VALUE_DRIFT = "SEMANTIC_VALUE_DRIFT"
    CONTRACT_INVENTORY_DRIFT = "CONTRACT_INVENTORY_DRIFT"


# ---------------------------------------------------------------------------
# Evidence model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ContractFailure:
    """A single detected contract violation with full diagnostic context."""

    classification: FailureClassification
    operation: str  # e.g. "GET /api/dashboard/summary"
    path: str
    method: str
    source: str  # where the check lives (freshness | generated_types | schema_compat | consumers | wire)
    expected: str
    actual: str
    details: str = ""
    boundary: str = ""  # e.g. "Backend response -> frontend DashboardMetricsSchema"

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "operation": self.operation,
            "path": self.path,
            "method": self.method,
            "source": self.source,
            "expected": self.expected,
            "actual": self.actual,
            "details": self.details,
            "boundary": self.boundary,
        }


@dataclass(frozen=True, slots=True)
class DimensionResult:
    """Outcome of one gate dimension."""

    name: str
    status: str  # "pass" | "fail" | "skip"
    failures: tuple[ContractFailure, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InventorySnapshot:
    """Deterministic fingerprint of the current contract inventory."""

    backend_operations: int = 0
    frontend_consumers: int = 0
    runtime_schemas: int = 0
    committed_artifacts: int = 0
    contract_inventory_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend_operations": self.backend_operations,
            "frontend_consumers": self.frontend_consumers,
            "runtime_schemas": self.runtime_schemas,
            "committed_artifacts": self.committed_artifacts,
            "contract_inventory_hash": self.contract_inventory_hash,
        }


@dataclass
class GateReport:
    """Complete M9-C27 evidence artifact."""

    run_id: str
    repository_revision: str
    backend_revision: str
    openapi_hash: str
    generated_types_hash: str
    inventory: InventorySnapshot
    dimensions: tuple[DimensionResult, ...]
    failures: tuple[ContractFailure, ...]
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "repository_revision": self.repository_revision,
            "backend_revision": self.backend_revision,
            "openapi_hash": self.openapi_hash,
            "generated_types_hash": self.generated_types_hash,
            "inventory": self.inventory.to_dict(),
            "dimensions": [
                {
                    "name": d.name,
                    "status": d.status,
                    "failures": [f.to_dict() for f in d.failures],
                    "metadata": d.metadata,
                }
                for d in self.dimensions
            ],
            "failures": [f.to_dict() for f in self.failures],
            "passed": self.passed,
        }


# Convenience helpers used across dimensions.


def _classification_for_nullability(
    op: str, spec_nullable: bool, zod_nullable: bool
) -> str:
    """Return the appropriate FailureClassification for nullability mismatch."""
    if spec_nullable != zod_nullable:
        return FailureClassification.NULLABILITY_DRIFT.value
    return FailureClassification.SCHEMA_DRIFT.value


def _failure(classif: FailureClassification | str, **kwargs: Any) -> ContractFailure:
    return ContractFailure(
        classification=(
            FailureClassification(classif) if isinstance(classif, str) else classif
        ),
        **kwargs,
    )
