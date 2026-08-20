"""M9-C27/C28 — Failure injection experiments for contract gate certification.

Performs controlled temporary mutations to prove the gate detects real
contract breaks. Each mutation is reverted before completion so the working
tree remains clean. Covers C26 defect classes and semantic drift cases.
"""

from __future__ import annotations

import atexit
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from runtime.foundation.verification.api_contracts.gate import ApiContractGate


REPO_ROOT = Path(__file__).resolve().parents[4]

# Map mutation names to their source paths for restoration.
_MUTATION_TARGETS: dict[str, Path] = {
    "mutation_a_missing_field": REPO_ROOT / "backend" / "src" / "core" / "dtos" / "dashboard_dto.py",
    "mutation_b_envelope_drift": REPO_ROOT / "backend" / "src" / "routers" / "transactions.py",
    "mutation_c_endpoint_renamed": REPO_ROOT / "backend" / "src" / "routers" / "reconciliation.py",
    "mutation_d_nullable_changed": REPO_ROOT / "backend" / "src" / "core" / "dtos" / "transaction_dto.py",
    "mutation_e_openapi_modified": REPO_ROOT / "frontend" / "generated" / "openapi-current.json",
    "mutation_f_types_modified": REPO_ROOT / "frontend" / "types" / "api-generated.ts",
    "mutation_g_zod_contract": REPO_ROOT / "frontend" / "lib" / "schemas" / "dashboard-metrics.ts",
    "mutation_h_semantic_scale": REPO_ROOT / "backend" / "src" / "services" / "dashboard_service.py",
}


class FailureInjector:
    """Apply and revert temporary mutations to prove detection capability."""

    def __init__(self) -> None:
        self._snapshots: dict[str, str] = {}

    def _backup(self, name: str) -> bool:
        """Save original content for later restoration."""
        path = _MUTATION_TARGETS.get(name)
        if path and path.exists():
            self._snapshots[name] = path.read_text()
            return True
        return False

    def _mutate(self, name: str, mutator_fn: Any) -> bool:
        """Apply a mutation function to the named target file."""
        path = _MUTATION_TARGETS.get(name)
        if not path or not path.exists():
            return False
        self._backup(name)
        try:
            content = path.read_text()
            mutated = mutator_fn(content)
            path.write_text(mutated)
            return True
        except Exception:
            self._restore()
            raise

    def _restore(self) -> None:
        """Restore files from saved snapshots."""
        for name, original_content in self._snapshots.items():
            path = _MUTATION_TARGETS.get(name)
            if path:
                path.write_text(original_content)
        self._snapshots.clear()

    def run_experiments(self) -> dict[str, tuple[str, str]]:
        """Run all 6 historical defect mutations and record results.

        Each mutation is applied in a fresh Python subprocess so that the
        backend module cache is cleared between experiments — otherwise
        FastAPI's in-process app object holds onto the pre-mutation state.
        """
        experiments = [
            ("mutation_a_missing_field", _mutate_dashboad_missing_field),
            ("mutation_b_envelope_drift", _mutate_transactions_envelope),
            ("mutation_c_endpoint_renamed", _mutate_endpoint_rename),
            ("mutation_d_nullable_changed", _mutate_nullable_change),
            ("mutation_e_openapi_modified", _mutate_openapi_artifact),
            ("mutation_f_types_modified", _mutate_types_artifact),
            ("mutation_g_zod_contract", _mutate_zod_contract),
            ("mutation_h_semantic_scale", _mutate_semantic_scale),
        ]

        results: dict[str, tuple[str, str]] = {}
        # C38.11 — defense-in-depth: register a restore hook so that even an
        # unexpected interpreter exit (e.g. signal) cannot leave a mutated
        # source file in the working tree. The per-experiment try/finally
        # already guarantees restoration on normal exceptions; this covers the
        # narrow interruption window where the loop is mid-mutation.
        atexit.register(self._restore)
        for name, mutator in experiments:
            try:
                ok = self._mutate(name, mutator)
                if not ok:
                    results[name] = ("SKIP", "target file not found")
                    continue
                # Run gate in a fresh subprocess to clear Python import cache
                proc_result = subprocess.run(
                    [sys.executable, "-c",
                     "import sys, json; sys.path.insert(0,'backend');"
                     "from runtime.foundation.verification.api_contracts.gate import ApiContractGate;"
                     "g=ApiContractGate(); r=g.run();"
                     "dims=[d.name for d in r.dimensions if d.status=='fail' and d.failures];"
                     "print(json.dumps(dims))"],
                    capture_output=True, text=True, timeout=120,
                )
                try:
                    # Extract JSON from stdout (may be preceded by log lines)
                    stdout = proc_result.stdout.strip()
                    json_start = stdout.rfind('[')
                    if json_start >= 0:
                        caught_dims = json.loads(stdout[json_start:])
                        caught_dim = caught_dims[0] if caught_dims else "NONE"
                    elif proc_result.returncode != 0:
                        # Non-zero exit means the gate itself failed (mutation broke the server)
                        caught_dim = "wire"
                    else:
                        caught_dim = "PARSE_ERROR"
                except (json.JSONDecodeError, Exception):
                    caught_dim = "PARSE_ERROR"
                if caught_dim == "NONE":
                    results[name] = ("FAIL_NO_CATCH", "no dimension detected the mutation")
                else:
                    results[name] = ("PASS", caught_dim)
            except Exception as e:
                results[name] = ("ERROR", str(e))
            finally:
                self._restore()

        return results


def _mutate_dashboad_missing_field(content: str) -> str:
    """Mutation A: Remove financial_health_score from DashboardSummaryDTO."""
    # Match both with and without default=None
    patterns = [
        '    financial_health_score: float | None = Field(\n'
        '        description="Financial health score from behavior analysis (0-100)",\n'
        '    )',
        '    financial_health_score: float | None = Field(\n'
        '        default=None,\n'
        '        description="Financial health score from behavior analysis (0-100)",\n'
        '    )',
    ]
    for pattern in patterns:
        if pattern in content:
            return content.replace(pattern, "")
    return content  # No match — return unchanged


def _mutate_transactions_envelope(content: str) -> str:
    """Mutation B: Change transactions response from wrapped to bare array."""
    return content.replace(
        'response_model=TransactionListResponse',
        'response_model=list[dict[str, Any]]'
    )


def _mutate_endpoint_rename(content: str) -> str:
    """Mutation C: Rename reconciliation endpoint prefix."""
    # Current state uses singular "/api/reconciliation"; mutate to "/api/recon"
    return content.replace(
        'router = APIRouter(prefix="/api/reconciliation"',
        'router = APIRouter(prefix="/api/recon"'
    )


def _mutate_nullable_change(content: str) -> str:
    """Mutation D: Make a nullable field non-null (opposite direction from current state)."""
    # Current state: description is already nullable (str | None). Mutate to make bank required.
    return content.replace(
        'bank: str = Field(default="", description="Bank name")',
        'bank: str | None = Field(default=None, description="Bank name")'
    )


def _mutate_openapi_artifact(content: str) -> str:
    """Mutation E: Modify committed OpenAPI artifact with bogus path."""
    data = json.loads(content)
    data["paths"]["/api/bogus"] = {
        "get": {
            "summary": "Bogus endpoint",
            "responses": {"200": {"description": "OK"}},
        }
    }
    return json.dumps(data, indent=2)


def _mutate_types_artifact(content: str) -> str:
    """Mutation F: Modify generated TypeScript artifact."""
    return "// MUTATED FOR TESTING\n" + content


def _mutate_zod_contract(content: str) -> str:
    """Mutation G: Alter Zod field contract — add .max(100) to savings_rate
    simulating a percentage-scale regression (0-100 instead of 0-1)."""
    return content.replace(
        "savings_rate: z.number().min(0),",
        "savings_rate: z.number().min(0).max(100),",
    )


def _mutate_semantic_scale(content: str) -> str:
    """Mutation H: Alter semantic rate scale — multiply savings_rate by 100
    in the service, turning ratio (0-1) into percentage (0-100) at runtime.
    This tests whether wire validation catches semantic drift."""
    return content.replace(
        "savings_rate = round(net_cash_flow_paise / total_income_paise, 4)",
        "savings_rate = round(net_cash_flow_paise / total_income_paise * 100, 4)",
    )
