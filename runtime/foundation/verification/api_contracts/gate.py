"""M9-C27 — Core API contract gate.

Orchestrates all four verification dimensions:
  STRUCTURAL  (freshness of committed OpenAPI artifacts)
  GENERATED   (reproducibility of frontend/types/api-generated.ts)
  CONSUMER    (frontend consumers mapped to backend operations)
  WIRE        (live response validation via TestClient)

Produces a GateReport with structured evidence and failure classifications.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parents[4] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from runtime.foundation.verification.api_contracts.inventory import (
    ContractInventory,
    REPO_ROOT,
)
from runtime.foundation.verification.api_contracts.normalize import (
    canonical_normalize,
    diff_openapi,
    hash_openapi,
)
from runtime.foundation.verification.api_contracts.taxonomy import (
    ContractFailure,
    DimensionResult,
    GateReport,
    InventorySnapshot,
    _failure,
    FailureClassification,
)


class ApiContractGate:
    """Main orchestrator for M9-C27 API contract integrity checks."""

    def __init__(self, run_id: str | None = None) -> None:
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self._repo_root = REPO_ROOT
        self._inventory = ContractInventory()

    # ====================================================================
    # C27.2 — OpenAPI freshness gate
    # ====================================================================

    def check_freshness(self) -> DimensionResult:
        """Compare live OpenAPI against both committed artifact files."""
        try:
            from src.api import app

            live_openapi = app.openapi()
        except Exception as e:
            return DimensionResult(
                name="freshness",
                status="fail",
                failures=(
                    _failure(
                        "OPENAPI_INVALID",
                        operation="N/A",
                        path="app.openapi()",
                        method="",
                        source="freshness",
                        expected="live OpenAPI generation",
                        actual=f"exception: {e}",
                    ),
                ),
                metadata={"error": str(e)},
            )

        live_hash = hash_openapi(live_openapi)
        self._inventory.openapi_hash = live_hash

        artifacts_to_check = [
            ("frontend/generated/openapi-current.json", "FRONTEND"),
            ("backend/tests/generated/openapi-current.json", "BACKEND_TESTS"),
        ]

        failures: list[ContractFailure] = []
        for rel_path, label in artifacts_to_check:
            artifact_path = self._repo_root / rel_path
            if not artifact_path.exists():
                failures.append(
                    _failure(
                        FailureClassification.OPENAPI_STALE,
                        operation="*",
                        path=rel_path,
                        method="",
                        source="freshness",
                        expected=f"committed artifact matching live OpenAPI",
                        actual="artifact missing",
                        details=f"{label} artifact not found at {rel_path}",
                    )
                )
                continue
            # Detect malformed/empty artifacts
            size = artifact_path.stat().st_size
            if size == 0:
                failures.append(
                    _failure(
                        FailureClassification.OPENAPI_INVALID,
                        operation="*",
                        path=rel_path,
                        method="",
                        source="freshness",
                        expected=f"non-empty JSON artifact",
                        actual="artifact is 0 bytes",
                        details=f"{label} artifact is empty",
                    )
                )
                continue
            try:
                with open(artifact_path) as f:
                    committed = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                failures.append(
                    _failure(
                        FailureClassification.OPENAPI_INVALID,
                        operation="*",
                        path=rel_path,
                        method="",
                        source="freshness",
                        expected=f"valid JSON artifact",
                        actual=f"parse error: {e}",
                        details=f"{label} artifact is malformed",
                    )
                )
                continue
            if not isinstance(committed, dict) or "paths" not in committed:
                failures.append(
                    _failure(
                        FailureClassification.OPENAPI_INVALID,
                        operation="*",
                        path=rel_path,
                        method="",
                        source="freshness",
                        expected=f"OpenAPI dict with 'paths' key",
                        actual=f"structure: {type(committed).__name__}, keys={list(committed.keys())[:5] if isinstance(committed, dict) else 'N/A'}",
                        details=f"{label} artifact is not a valid OpenAPI document",
                    )
                )
                continue
            diffs = diff_openapi(live_openapi, committed)
            if diffs:
                for d in diffs[:5]:  # report first 5 diffs per artifact
                    failures.append(
                        _failure(
                            FailureClassification.OPENAPI_STALE,
                            operation="*",
                            path=d["path"],
                            method="",
                            source="freshness",
                            expected=f"{label}: {d.get('expected')!r}",
                            actual=f"{label} LIVE: {d.get('actual')!r}",
                            details=f"Drift: {d['kind']} at {d['path']}",
                        )
                    )
            else:
                self._inventory.committed_artifacts += 1

        status = "pass" if not failures else "fail"
        return DimensionResult(
            name="freshness", status=status, failures=tuple(failures)
        )

    # ====================================================================
    # C27.3 — Generated TypeScript integrity
    # ====================================================================

    def check_generated_types(self) -> DimensionResult:
        """Verify frontend/types/api-generated.ts is reproducible from live OpenAPI."""
        generated_file = self._repo_root / "frontend" / "types" / "api-generated.ts"
        if not generated_file.exists():
            return DimensionResult(
                name="generated_types",
                status="fail",
                failures=(
                    _failure(
                        FailureClassification.GENERATED_TYPES_INVALID,
                        operation="*",
                        path="frontend/types/api-generated.ts",
                        method="",
                        source="generated_types",
                        expected="generated types file exists",
                        actual="file missing",
                    ),
                ),
            )

        current_content = generated_file.read_text()
        try:
            from src.api import app

            live_openapi = app.openapi()
        except Exception:
            return DimensionResult(
                name="generated_types",
                status="skip",
                metadata={"reason": "cannot generate live OpenAPI"},
            )

        # Generate to temp file using openapi-typescript
        with tempfile.NamedTemporaryFile(
            suffix=".ts", mode="w", delete=False, dir="/tmp"
        ) as tmp:
            tmp_path = tmp.name

        try:
            proc = subprocess.run(
                ["npx", "openapi-typescript", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode != 0:
                return DimensionResult(
                    name="generated_types",
                    status="skip",
                    metadata={"reason": "openapi-typescript not available"},
                )

            # Write temp OpenAPI (no sort_keys — preserve insertion order so
            # openapi-typescript output matches what `npm run gen:types` produces).
            oapi_tmp = tempfile.NamedTemporaryFile(
                suffix=".json", mode="w", delete=False, dir="/tmp"
            )
            oapi_tmp.write(json.dumps(live_openapi, indent=2))
            oapi_tmp.close()

            gen_proc = subprocess.run(
                ["npx", "openapi-typescript", oapi_tmp.name, "-o", tmp_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if gen_proc.returncode == 0:
                new_content = Path(tmp_path).read_text()
                self._inventory.generated_types_hash = hashlib.sha256(
                    new_content.encode()
                ).hexdigest()
                if new_content.strip() != current_content.strip():
                    # Find first difference
                    curr_lines = current_content.splitlines()
                    new_lines = new_content.splitlines()
                    diff_line = 1
                    for i, (c, n) in enumerate(zip(curr_lines, new_lines), 1):
                        if c.strip() != n.strip():
                            diff_line = i
                            break
                    failures = [
                        _failure(
                            FailureClassification.GENERATED_TYPES_STALE,
                            operation="*",
                            path="frontend/types/api-generated.ts",
                            method="",
                            source="generated_types",
                            expected=f"types reproducible from live OpenAPI (no diff)",
                            actual=f"differences detected starting line {diff_line}",
                            details="Run `npm run gen:types` while backend is running to regenerate.",
                        )
                    ]
                    return DimensionResult(
                        name="generated_types", status="fail", failures=tuple(failures)
                    )
                else:
                    return DimensionResult(name="generated_types", status="pass")
            else:
                return DimensionResult(
                    name="generated_types",
                    status="fail",
                    failures=(
                        _failure(
                            FailureClassification.GENERATED_TYPES_INVALID,
                            operation="*",
                            path="frontend/types/api-generated.ts",
                            method="",
                            source="generated_types",
                            expected="generation succeeds",
                            actual=f"openapi-typescript failed: {gen_proc.stderr[:200]}",
                        ),
                    ),
                )
        finally:
            import os

            for p in (tmp_path,):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    # ====================================================================
    # C27.4 — Runtime schema compatibility (Zod vs OpenAPI)
    # ====================================================================

    def check_schema_compatibility(self) -> DimensionResult:
        """Validate frontend Zod schemas against OpenAPI response schemas."""
        try:
            from src.api import app

            openapi = app.openapi()
        except Exception:
            return DimensionResult(name="schema_compat", status="skip")

        components = openapi.get("components", {}).get("schemas", {})
        inventory = ContractInventory()
        inventory.extract_frontend_consumers()

        # Build mapping: Zod schema name → OpenAPI component name
        zod_to_openapi = {
            "DashboardMetricsSchema": "DashboardSummaryDTO",
            "TransactionSchema": "TransactionDTO",
            "TransactionsResponseSchema": "TransactionListResponse",
            "BehaviorScoreSchema": "WellnessScoreResponse",
            "ReconciliationMatchSchema": "ReconciliationMatchDTO",
        }

        failures: list[ContractFailure] = []
        checked = 0

        for zod_name, op_api_name in zod_to_openapi.items():
            zod_schema = next(
                (s for s in inventory.runtime_schemas if s.name == zod_name), None
            )
            if not zod_schema:
                continue
            openapi_schema = components.get(op_api_name, {})
            if not openapi_schema:
                continue

            checked += 1
            # Check required fields
            openapi_props = openapi_schema.get("properties", {})
            openapi_required = set(openapi_schema.get("required", []))
            zod_shape = zod_schema.shape

            # Missing fields in Zod that exist in OpenAPI
            for field_name in openapi_props:
                if field_name not in zod_shape:
                    failures.append(
                        _failure(
                            FailureClassification.FIELD_DRIFT,
                            operation=f"schema:{zod_name}",
                            path=f"{op_api_name}.{field_name}",
                            method="",
                            source="schema_compat",
                            expected=f"{field_name} present in Zod schema",
                            actual=f"{field_name} missing from Zod schema",
                            details=f"OpenAPI requires {field_name} but Zod has no such field",
                            boundary=f"Backend {op_api_name} -> frontend {zod_name}",
                        )
                    )
                elif field_name in zod_shape:
                    # Check nullability
                    zod_def = zod_shape[field_name]
                    is_nullable_zod = "nullable" in zod_def.get("expr", "")
                    schema_spec = openapi_props[field_name]
                    is_nullable_openapi = (
                        "null" in str(schema_spec.get("type", ""))
                        or any(
                            t.get("type") == "null"
                            for t in schema_spec.get("anyOf", [])
                        )
                        or schema_spec.get("nullable", False)
                    )
                    if is_nullable_zod != is_nullable_openapi:
                        failures.append(
                            _failure(
                                FailureClassification.NULLABILITY_DRIFT,
                                operation=f"schema:{zod_name}",
                                path=f"{op_api_name}.{field_name}",
                                method="",
                                source="schema_compat",
                                expected=f"{field_name} nullable={is_nullable_openapi}",
                                actual=f"{field_name} nullable={is_nullable_zod}",
                                boundary=f"Backend {op_api_name} -> frontend {zod_name}",
                            )
                        )

                    # Check scalar range / scale drift
                    zod_min = zod_def.get("min")
                    zod_max = zod_def.get("max")
                    # Extract single values from lists if needed
                    zod_min_val = (
                        zod_min[0] if isinstance(zod_min, list) and zod_min else zod_min
                    )
                    zod_max_val = (
                        zod_max[0] if isinstance(zod_max, list) and zod_max else zod_max
                    )
                    openapi_min = schema_spec.get("minimum")
                    openapi_max = schema_spec.get("maximum")
                    if (
                        zod_min_val is not None
                        and openapi_min is not None
                        and zod_min_val != openapi_min
                    ):
                        failures.append(
                            _failure(
                                FailureClassification.SCHEMA_DRIFT,
                                operation=f"schema:{zod_name}",
                                path=f"{op_api_name}.{field_name}",
                                method="",
                                source="schema_compat",
                                expected=f"{field_name} min={openapi_min}",
                                actual=f"{field_name} Zod min={zod_min_val}",
                                details="Scalar range mismatch between backend OpenAPI and frontend Zod schema",
                                boundary=f"Backend {op_api_name} -> frontend {zod_name}",
                            )
                        )
                    if (
                        zod_max_val is not None
                        and openapi_max is not None
                        and zod_max_val != openapi_max
                    ):
                        failures.append(
                            _failure(
                                FailureClassification.SCHEMA_DRIFT,
                                operation=f"schema:{zod_name}",
                                path=f"{op_api_name}.{field_name}",
                                method="",
                                source="schema_compat",
                                expected=f"{field_name} max={openapi_max}",
                                actual=f"{field_name} Zod max={zod_max_val}",
                                details="Scalar range mismatch between backend OpenAPI and frontend Zod schema",
                                boundary=f"Backend {op_api_name} -> frontend {zod_name}",
                            )
                        )
                    # Detect percentage-vs-ratio scale drift:
                    # Flag when OpenAPI description mentions "ratio" or "(0-1)"
                    # AND Zod max >= 100, suggesting the frontend treats it as percentage.
                    op_desc = schema_spec.get("description", "") or ""
                    if (
                        zod_max_val is not None
                        and zod_max_val >= 100
                        and openapi_max is None
                    ):
                        if (
                            "ratio" in op_desc.lower()
                            or "(0-1)" in op_desc
                            or "(0 – 1)" in op_desc
                        ):
                            failures.append(
                                _failure(
                                    FailureClassification.SCHEMA_DRIFT,
                                    operation=f"schema:{zod_name}",
                                    path=f"{op_api_name}.{field_name}",
                                    method="",
                                    source="schema_compat",
                                    expected=f"{field_name} range consistent with backend",
                                    actual=f"{field_name} Zod max={zod_max_val} but OpenAPI description says {op_desc!r} (backend may return ratio 0-1)",
                                    details="Potential percentage-vs-ratio scale mismatch — backend returns a ratio but Zod expects percentages",
                                    boundary=f"Backend {op_api_name} -> frontend {zod_name}",
                                )
                            )

            # Extra optional fields in Zod are acceptable; only flag unexpected required
            for field_name in zod_shape:
                if (
                    field_name not in openapi_props
                    and field_name not in zod_schema.nullable_fields
                ):
                    # Extra field — only flag if it's NOT optional in Zod
                    pass  # Optional extras are acceptable for forward-compat

        self._inventory.runtime_schemas = checked
        status = "pass" if not failures else "fail"
        return DimensionResult(
            name="schema_compat", status=status, failures=tuple(failures)
        )

    # ====================================================================
    # C27.5 — Endpoint consumer integrity
    # ====================================================================

    def _path_matches(self, consumer_path: str, op_path: str) -> bool:
        """Check if a consumer URL path matches a backend operation path.

        Matches are exact for static segments; parameterized segments ({id}) match any value.
        Query strings are ignored (stripped before calling). Trailing slashes are normalized.
        """
        # Normalize trailing slashes
        cp = consumer_path.rstrip("/") or "/"
        op = op_path.rstrip("/") or "/"

        # Exact match
        if cp == op:
            return True

        # Split into segments and compare
        c_parts = [p for p in cp.split("/") if p]
        o_parts = [p for p in op.split("/") if p]

        if len(c_parts) != len(o_parts):
            return False

        for c, o in zip(c_parts, o_parts):
            # Parameterized segment in backend
            if o.startswith("{") and o.endswith("}"):
                continue
            if c != o:
                return False
        return True

    def check_consumer_integrity(self) -> DimensionResult:
        """Map frontend consumers to backend operations and detect drift."""
        try:
            from src.api import app

            openapi = app.openapi()
        except Exception:
            return DimensionResult(name="consumer_integrity", status="skip")

        inventory = ContractInventory()
        consumers = inventory.extract_frontend_consumers()
        operations = inventory.extract_backend_operations(openapi)

        # Build op set: (method, normalized_path_without_trailing_slash)
        op_set = set()
        for op in operations:
            p = op.path.rstrip("/") or "/"
            op_set.add((op.method, p))

        known_deprecated = {"/api/behavior/score"}

        failures: list[ContractFailure] = []

        for consumer in consumers:
            # Normalize URL: strip query params, handle trailing slash
            url_path = consumer.url.split("?")[0].rstrip("/") or "/"
            method = consumer.method

            # Check if endpoint exists in backend using strict parameterized matching
            exists = (method, url_path) in op_set
            if not exists:
                # Try matching against parameterized backend paths
                found = False
                for op_method, op_path in op_set:
                    if op_method == method and self._path_matches(url_path, op_path):
                        found = True
                        break

                if not found:
                    # Check for relative URL (API_BASE_DRIFT)
                    if consumer.api_base_used == "relative":
                        failures.append(
                            _failure(
                                FailureClassification.API_BASE_DRIFT,
                                operation=f"{method} {consumer.url}",
                                path=url_path,
                                method=method,
                                source="consumer_integrity",
                                expected="absolute backend URL or proper proxy config",
                                actual=f"relative fetch URL in {consumer.file} (targets :3000)",
                                details=f"Consumer in {consumer.file} uses relative URL without API_BASE prefix",
                            )
                        )
                    else:
                        failures.append(
                            _failure(
                                FailureClassification.ENDPOINT_DRIFT,
                                operation=f"{method} {consumer.url}",
                                path=url_path,
                                method=method,
                                source="consumer_integrity",
                                expected=f"endpoint {url_path} exists in backend",
                                actual="endpoint not found in OpenAPI",
                                details=f"Consumer in {consumer.file} calls non-existent endpoint",
                            )
                        )
            elif url_path in known_deprecated:
                failures.append(
                    _failure(
                        FailureClassification.DEPRECATED_ENDPOINT_CONSUMER,
                        operation=f"{method} {consumer.url}",
                        path=url_path,
                        method=method,
                        source="consumer_integrity",
                        expected="consumer updated to new endpoint",
                        actual="consumer still uses deprecated endpoint",
                        details=f"Endpoint {url_path} is deprecated; use alternative",
                    )
                )

        status = "pass" if not failures else "fail"
        self._inventory.frontend_consumers = len(consumers)
        return DimensionResult(
            name="consumer_integrity", status=status, failures=tuple(failures)
        )

    # ====================================================================
    # C27.6 — Live wire validation
    # ====================================================================

    def check_wire_validation(self) -> DimensionResult:
        """Make real HTTP requests through TestClient and validate responses."""
        from fastapi.testclient import TestClient
        from src.api import app

        # Critical endpoints from C26 families
        critical_endpoints = [
            ("GET", "/api/dashboard/summary"),
            ("GET", "/api/transactions"),
            ("GET", "/api/reconciliation"),
            ("GET", "/api/v1/behaviour/wellness-score"),
        ]

        # Set up isolated test DB
        from src.config import settings
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_db_path = tmp.name

        original_db = settings._database_path_override
        settings._database_path_override = tmp_db_path

        failures: list[ContractFailure] = []

        try:
            # Initialize DB with deterministic fixture for semantic validation
            from runtime.foundation.verification.api_contracts.fixture import (
                seed_contract_fixture,
            )

            seed_contract_fixture(tmp_db_path)

            client = TestClient(app, raise_server_exceptions=False)

            for method, path in critical_endpoints:
                resp = client.request(method, path)
                if resp.status_code != 200:
                    failures.append(
                        _failure(
                            FailureClassification.WIRE_STATUS_DRIFT,
                            operation=f"{method} {path}",
                            path=path,
                            method=method,
                            source="wire",
                            expected="HTTP 200",
                            actual=f"HTTP {resp.status_code}: {resp.text[:200]}",
                            details="Live wire probe failed",
                        )
                    )
                    continue

                # Validate response shape for key endpoints
                if path == "/api/transactions":
                    data = resp.json()
                    if isinstance(data, list):
                        failures.append(
                            _failure(
                                FailureClassification.RESPONSE_ENVELOPE_DRIFT,
                                operation=f"{method} {path}",
                                path=path,
                                method=method,
                                source="wire",
                                expected="{transactions: [...], total: int}",
                                actual=f"bare array with {len(data)} items",
                                details="Expected wrapped response envelope",
                            )
                        )
                    elif not isinstance(data, dict) or "transactions" not in data:
                        failures.append(
                            _failure(
                                FailureClassification.RESPONSE_ENVELOPE_DRIFT,
                                operation=f"{method} {path}",
                                path=path,
                                method=method,
                                source="wire",
                                expected="{transactions: [...], total: int}",
                                actual=f"unexpected shape: {type(data).__name__}",
                            )
                        )

                elif path == "/api/dashboard/summary":
                    data = resp.json()
                    if "financial_health_score" not in data:
                        failures.append(
                            _failure(
                                FailureClassification.FIELD_DRIFT,
                                operation=f"{method} {path}",
                                path=path,
                                method=method,
                                source="wire",
                                expected="financial_health_score in response",
                                actual="field missing from response",
                                details="C25 historical defect class",
                            )
                        )

                    # Semantic value range validation for ratio fields
                    # OpenAPI documents savings_rate and emi_ratio as "ratio (0-1)"
                    for field_name in ("savings_rate", "emi_ratio"):
                        if field_name in data:
                            val = data[field_name]
                            if isinstance(val, (int, float)) and val > 1.0:
                                failures.append(
                                    _failure(
                                        FailureClassification.SEMANTIC_VALUE_DRIFT,
                                        operation=f"{method} {path}",
                                        path=f"{path}.{field_name}",
                                        method=method,
                                        source="wire",
                                        expected=f"{field_name} in range [0, 1] (ratio convention)",
                                        actual=f"{field_name}={val} (appears to be percentage scale)",
                                        details=(
                                            f"Backend reports {field_name} as 'ratio (0-1)' in OpenAPI "
                                            f"but live response returns value > 1.0 — semantic scale drift"
                                        ),
                                    )
                                )

                    # Validate monetary units are in paise (should be large integers)
                    # A value < 100000 suggests rupees instead of paise
                    for field_name in (
                        "net_cash_flow_paise",
                        "total_income_paise",
                        "total_expenses_paise",
                        "emi_paise",
                    ):
                        if field_name in data:
                            val = data[field_name]
                            if isinstance(val, (int, float)) and 0 < val < 100000:
                                failures.append(
                                    _failure(
                                        FailureClassification.SEMANTIC_VALUE_DRIFT,
                                        operation=f"{method} {path}",
                                        path=f"{path}.{field_name}",
                                        method=method,
                                        source="wire",
                                        expected=f"{field_name} in paise (should be >= 100000 for typical values)",
                                        actual=f"{field_name}={val} (possible rupee-scale value)",
                                        details=(
                                            f"Backend field {field_name} appears to return rupees "
                                            f"instead of paise — monetary unit drift detected"
                                        ),
                                    )
                                )

                    # Validate content-type
                    ct = resp.headers.get("content-type", "")
                    if "application/json" not in ct:
                        failures.append(
                            _failure(
                                FailureClassification.WIRE_RESPONSE_DRIFT,
                                operation=f"{method} {path}",
                                path=path,
                                method=method,
                                source="wire",
                                expected="Content-Type: application/json",
                                actual=f"Content-Type: {ct}",
                                details="Response is not JSON",
                            )
                        )

        finally:
            settings._database_path_override = original_db
            try:
                os.unlink(tmp_db_path)
            except OSError:
                pass

        status = "pass" if not failures else "fail"
        return DimensionResult(name="wire", status=status, failures=tuple(failures))

    # ====================================================================
    # Run full gate
    # ====================================================================

    def run(self) -> GateReport:
        """Execute all dimensions and produce evidence report."""
        # Build inventory
        try:
            from src.api import app

            openapi = app.openapi()
            ops = self._inventory.extract_backend_operations(openapi)
            consumers = self._inventory.extract_frontend_consumers()
            artifacts = self._inventory.index_generated_artifacts()
        except Exception:
            ops, consumers, artifacts = [], [], []

        # Run each dimension
        freshness = self.check_freshness()
        generated = self.check_generated_types()
        schema_compat = self.check_schema_compatibility()
        consumer_integrity = self.check_consumer_integrity()
        wire = self.check_wire_validation()

        dimensions = (freshness, generated, schema_compat, consumer_integrity, wire)
        all_failures = tuple(f for d in dimensions for f in d.failures)

        return GateReport(
            run_id=self.run_id,
            repository_revision=_git_head(),
            backend_revision=_git_head(),
            openapi_hash=self._inventory.openapi_hash,
            generated_types_hash=getattr(self._inventory, "generated_types_hash", ""),
            inventory=InventorySnapshot(
                backend_operations=len(ops),
                frontend_consumers=len(consumers),
                runtime_schemas=self._inventory.runtime_schemas,
                committed_artifacts=self._inventory.committed_artifacts,
                contract_inventory_hash=_compute_inventory_hash(ops, consumers),
            ),
            dimensions=dimensions,
            failures=all_failures,
            passed=all(d.status == "pass" for d in dimensions),
        )


def _git_head() -> str:
    try:
        import subprocess

        r = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip()[:8]
    except Exception:
        return "unknown"


def _compute_inventory_hash(ops, consumers) -> str:
    """Deterministic hash of the contract inventory state."""
    import hashlib

    data = json.dumps(
        {
            "operations": sorted([(op.method, op.path) for op in ops]),
            "consumers": sorted([f"{c.file}:{c.url}" for c in consumers]),
        },
        sort_keys=True,
    )
    return hashlib.sha256(data.encode()).hexdigest()[:16]
