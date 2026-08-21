"""M9-C27 — Deterministic contract inventory builder.

Derives a machine-readable inventory from authoritative sources only:
- Backend FastAPI routes and response_models (via live OpenAPI generation).
- Frontend source files (hooks, capabilities, Zod schemas, API client calls).

This inventory is the baseline for all downstream dimensions. No manual
endpoint registry is maintained — everything is derived.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
BACKEND_SRC = REPO_ROOT / "backend" / "src"
FRONTEND_SRC = REPO_ROOT / "frontend"
GENERATED_DIR = REPO_ROOT / "frontend" / "generated"
TYPES_DIR = FRONTEND_SRC / "types"


@dataclass(frozen=True, slots=True)
class BackendOperation:
    method: str
    path: str
    response_model: str | None
    tags: list[str] = field(default_factory=list)
    deprecated: bool = False


@dataclass(frozen=True, slots=True)
class FrontendConsumer:
    file: str  # relative to frontend/
    url: str  # exact URL literal
    method: str
    schema_name: str | None  # if using safeParse(XSchema, ...)
    api_base_used: str  # full base or 'relative'

    @property
    def origin(self) -> str:
        return f"{self.file}:{self.url}"


@dataclass(frozen=True, slots=True)
class RuntimeSchema:
    name: str
    file: str  # relative to frontend/lib/schemas/
    shape: dict[str, Any] = field(default_factory=dict)
    required_fields: list[str] = field(default_factory=list)
    nullable_fields: list[str] = field(default_factory=list)


class ContractInventory:
    """Deterministic inventory of the backend/frontend contract surface."""

    def __init__(self) -> None:
        self.backend_operations: list[BackendOperation] = []
        self.frontend_consumers: list[FrontendConsumer] = []
        self.runtime_schemas: list[RuntimeSchema] = []
        self.generated_artifacts: list[str] = []
        self.openapi_hash: str = ""
        self.committed_artifacts: int = 0

    # ------------------------------------------------------------------
    # Backend operations — derive from live OpenAPI (authoritative source)
    # ------------------------------------------------------------------

    def extract_backend_operations(
        self, openapi: dict[str, Any]
    ) -> list[BackendOperation]:
        """Build backend operation list directly from live OpenAPI paths."""
        ops: list[BackendOperation] = []
        paths = openapi.get("paths", {})
        components = openapi.get("components", {}).get("schemas", {})

        for path, methods in sorted(paths.items()):
            for method, spec in sorted(methods.items()):
                if method not in ("get", "post", "put", "patch", "delete"):
                    continue
                resp = spec.get("responses", {})
                ok_resp = (
                    resp.get("200", {}).get("content", {}).get("application/json", {})
                )
                resp_schema = ok_resp.get("schema", {})
                model_name: str | None = None
                if "$ref" in resp_schema:
                    model_name = resp_schema["$ref"].split("/")[-1]
                tags = spec.get("tags", [])
                deprecated = bool(spec.get("deprecated", False))
                ops.append(
                    BackendOperation(
                        method=method.upper(),
                        path=path,
                        response_model=model_name,
                        tags=tags,
                        deprecated=deprecated,
                    )
                )
        self.backend_operations = ops
        return ops

    # ------------------------------------------------------------------
    # Frontend consumers — derive by scanning TS/TSX source files
    # ------------------------------------------------------------------

    def extract_frontend_consumers(self) -> list[FrontendConsumer]:
        """Scan frontend hooks/capabilities/client for fetch() call sites."""
        consumers: list[FrontendConsumer] = []
        schema_files = list((FRONTEND_SRC / "lib" / "schemas").glob("*.ts"))
        hook_files = list((FRONTEND_SRC / "lib" / "hooks").glob("*.ts"))
        cap_files = list((FRONTEND_SRC / "lib" / "capabilities").glob("*.ts"))
        client_file = FRONTEND_SRC / "lib" / "api" / "client.ts"
        if client_file.exists():
            hook_files.append(client_file)

        # --- Extract schema exports first ---
        all_schema_imports: dict[str, str] = {}
        for sf in schema_files:
            content = sf.read_text()
            m = re.search(r"export\s+const\s+(\w+Schema)\s*=\s*z\.object", content)
            if m:
                all_schema_imports[m.group(1)] = str(sf.relative_to(FRONTEND_SRC))

        # Index every schema file directly (not via consumer file matching)
        for sf in schema_files:
            rel = str(sf.relative_to(FRONTEND_SRC))
            content = sf.read_text()
            for sname in all_schema_imports:
                if f"export const {sname}" in content:
                    self._index_schema(sname, rel, content)

        # Also index non-object schemas (unions, enums, array-of)
        for sf in schema_files:
            rel = str(sf.relative_to(FRONTEND_SRC))
            content = sf.read_text()
            for m in re.finditer(
                r"export\s+const\s+(\w+)\s*=\s*z\.(enum|string|number|union|array|record|literal)",
                content,
            ):
                sname = m.group(1)
                if sname not in all_schema_imports:
                    all_schema_imports[sname] = rel

        source_files = hook_files + cap_files
        for src in source_files:
            rel = str(src.relative_to(FRONTEND_SRC))
            content = src.read_text()
            # Find API_BASE defaults and fetch calls
            api_base_matches = re.findall(
                r"(?:const|let|var)\s+API_BASE\s*=\s*(.+)", content
            )
            default_base = "http://localhost:8000"
            has_api_base = bool(api_base_matches)
            if api_base_matches:
                raw = api_base_matches[0].strip().rstrip(";")
                if raw.startswith("'") or raw.startswith('"'):
                    default_base = raw.strip("'\"")
                elif "NEXT_PUBLIC_API_URL" in raw:
                    default_base = f"<env:{raw}>"
                else:
                    default_base = raw

            # A file that defines API_BASE (even as env-var) is NOT "relative" —
            # its bare-prefixed paths will be resolved at runtime via the base.
            # Only flag as relative when the file has NO API_BASE definition at all.
            is_relative = not has_api_base

            # Match all fetch(...) calls — handles both single-arg and multi-arg forms.
            for m in re.finditer(r"\bfetch\s*\(", content):
                pos = m.start()
                rest = content[pos + len("fetch(") : pos + len("fetch(") + 400]
                # Extract URL from start of arguments (string, single-quoted, or template literal)
                url_m = re.match(r'\s*(?:"([^"]+)"|\'([^\']+)\'|`([^`]+)`)', rest)
                if not url_m:
                    continue
                url_raw = url_m.group(1) or url_m.group(2) or url_m.group(3)
                # Distinguish base-expression substitutions from path parameters.
                # Known base expressions (${API_BASE}, ${NEXT_PUBLIC_API_URL},
                # ${process.env.*}, ${query}, ${months}) are stripped entirely.
                # Unknown ${...} patterns that look like path params ({id}, {loanId})
                # are preserved as {param} placeholders.
                # Strategy: first strip all known base patterns, then convert remaining
                # ${...} to {param}.
                url_clean = re.sub(
                    r"\$\{(?:API_BASE|NEXT_PUBLIC_API_URL|query|months|process\.env\.[^}]*)\}",
                    "",
                    url_raw,
                )
                url_clean = re.sub(r"\$\{([^}]+)\}", r"{\1}", url_clean)
                url_clean = url_clean.strip()
                # Remove stray query-string markers left by ${query} removal
                url_clean = url_clean.replace("?{", "?").rstrip("?").rstrip("/")

                # Extract HTTP method from options object if present
                method = "GET"
                after_url = rest[url_m.end() :]
                # Stop searching at the next fetch( call to avoid matching
                # method specs from subsequent fetch calls in the same file.
                next_fetch = after_url.find("fetch(")
                if next_fetch > 0:
                    after_url = after_url[:next_fetch]
                mm = re.search(r"method\s*:\s*[\"'](\w+)[\"']", after_url)
                if mm:
                    method = mm.group(1).upper()

                # Reconstruct full URL
                if url_clean.startswith("/"):
                    full_url = url_clean
                    api_base_status = (
                        "bare_relative_in_api_base_file"
                        if not is_relative
                        else "relative"
                    )
                else:
                    full_url = default_base.rstrip("/") + "/" + url_clean.lstrip("/")
                    api_base_status = default_base

                # Find which schema validates the response
                schema_name = None
                ctx = content[pos : pos + 500]
                sm = re.search(r"(\w+Schema)\.safeParse", ctx)
                if sm:
                    schema_name = sm.group(1)

                consumers.append(
                    FrontendConsumer(
                        file=rel,
                        url=full_url,
                        method=method,
                        schema_name=schema_name,
                        api_base_used=api_base_status,
                    )
                )

        self.frontend_consumers = consumers
        return consumers

    def _index_schema(self, name: str, rel_file: str, content: str) -> None:
        """Extract Zod object shape from a schema definition file."""
        req_fields: list[str] = []
        null_fields: list[str] = []
        shape: dict[str, Any] = {}

        # Match fields inside z.object({...}) — one per line.
        # Use a non-greedy match for the value; stop at comma or }.
        for m in re.finditer(r"(\w+)\s*:\s*(z\.[^,}\n]+)", content):
            field_name = m.group(1)
            expr = m.group(2).strip()
            shape[field_name] = {"expr": expr}
            if "nullable" in expr:
                null_fields.append(field_name)
            else:
                req_fields.append(field_name)

        # Extract min/max bounds from expressions like .min(0), .max(100)
        for field_name, info in shape.items():
            expr = info["expr"]
            mins = re.findall(r"\.min\(([\d.]+)\)", expr)
            maxs = re.findall(r"\.max\(([\d.]+)\)", expr)
            info["min"] = [float(v) for v in mins] if mins else None
            info["max"] = [float(v) for v in maxs] if maxs else None

        self.runtime_schemas.append(
            RuntimeSchema(
                name=name,
                file=rel_file,
                shape=shape,
                required_fields=req_fields,
                nullable_fields=null_fields,
            )
        )

    # ------------------------------------------------------------------
    # Generated artifacts
    # ------------------------------------------------------------------

    def index_generated_artifacts(self) -> list[str]:
        """List all generated contract artifacts in the repo."""
        artifacts = []
        candidates = [
            GENERATED_DIR / "openapi-current.json",
            REPO_ROOT / "backend" / "tests" / "generated" / "openapi-current.json",
            TYPES_DIR / "api-generated.ts",
        ]
        for p in candidates:
            if p.exists():
                artifacts.append(str(p.relative_to(REPO_ROOT)))
        self.generated_artifacts = artifacts
        return artifacts
