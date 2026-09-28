"""M9-C27 — API Contract Integrity & Drift-Proofing package."""

from __future__ import annotations

from runtime.foundation.verification.api_contracts.gate import (
    ApiContractGate,
    GateReport,
)
from runtime.foundation.verification.api_contracts.inventory import ContractInventory
from runtime.foundation.verification.api_contracts.mutations import FailureInjector
from runtime.foundation.verification.api_contracts.normalize import (
    canonical_normalize,
    diff_openapi,
    hash_openapi,
)
from runtime.foundation.verification.api_contracts.taxonomy import (
    ContractFailure,
    DimensionResult,
    FailureClassification,
    InventorySnapshot,
)

__all__ = [
    "ApiContractGate",
    "ContractFailure",
    "ContractInventory",
    "DimensionResult",
    "FailureClassification",
    "FailureInjector",
    "GateReport",
    "InventorySnapshot",
    "canonical_normalize",
    "diff_openapi",
    "hash_openapi",
]
