"""M9-C61 — Canonical Endpoint Path Normalization Contract.

Provides a single, deterministic normalization function for frontend/backend
endpoint PATH representations so that semantically identical endpoints converge
to the same canonical identity while preserving original provenance.

This is distinct from the OpenAPI schema normalization in api_contracts.normalize.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Normalization Patterns
# ---------------------------------------------------------------------------

# Frontend template variable: ${variable} or ${encodeURIComponent(variable!)}
_DOLLAR_BRACE_RE = re.compile(r"\$\{([^}]+)\}")

# Backend FastAPI path parameter: {param_name}
_BRACE_PARAM_RE = re.compile(r"\{([^}]+)\}")

# Colon parameter (Express-style): :param_name
_COLON_PARAM_RE = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")

# encodeURIComponent wrapper
_ENCODE_URI_COMPONENT_RE = re.compile(r"encodeURIComponent\(([^)]+)\)")

# Query string
_QUERY_RE = re.compile(r"\?.*$")

# Trailing slash (but preserve leading slash)
_TRAILING_SLASH_RE = re.compile(r"/+$")

# Multiple slashes
_MULTI_SLASH_RE = re.compile(r"/{2,}")


@dataclass(frozen=True)
class NormalizedEndpoint:
    """Result of endpoint normalization with full provenance."""

    original: str
    canonical_path: str
    method: str | None = None
    path_params: tuple = ()
    query_params: tuple = ()
    normalization_rules: tuple = ()

    def __str__(self) -> str:
        return self.canonical_path

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NormalizedEndpoint):
            return False
        return (self.canonical_path == other.canonical_path and
                self.method == other.method)

    def __hash__(self) -> int:
        return hash((self.canonical_path, self.method))


def _extract_path_params(path: str) -> list[str]:
    """Extract parameter names from a path in order of appearance."""
    params = []
    for match in _BRACE_PARAM_RE.finditer(path):
        params.append(match.group(1))
    for match in _COLON_PARAM_RE.finditer(path):
        params.append(match.group(1))
    for match in _DOLLAR_BRACE_RE.finditer(path):
        inner = match.group(1)
        # Handle encodeURIComponent(variable!) -> variable
        encode_match = _ENCODE_URI_COMPONENT_RE.match(inner)
        if encode_match:
            params.append(encode_match.group(1).rstrip("!"))
        else:
            params.append(inner)
    return params


def _extract_query_params(path: str) -> list[str]:
    """Extract query parameter names from a path."""
    query_match = _QUERY_RE.search(path)
    if not query_match:
        return []
    query_str = query_match.group(0)[1:]  # Remove leading ?
    params = []
    for pair in query_str.split("&"):
        if "=" in pair:
            key = pair.split("=")[0]
            params.append(key)
        else:
            params.append(pair)
    return params


def normalize_endpoint(
    endpoint: str,
    method: str | None = None,
) -> NormalizedEndpoint:
    """
    Normalize an endpoint to its canonical representation.
    
    Handles:
    - Frontend template variables: ${id}, ${encodeURIComponent(id!)}
    - Backend path parameters: {id}, {account_id}
    - Express-style parameters: :id
    - Query strings: ?limit=10
    - Trailing slashes
    - Multiple slashes
    
    Returns a NormalizedEndpoint with:
    - canonical_path: method-aware canonical path (e.g., "GET:/platform/v1/tasks/{param}/cancel")
    - path_params: tuple of parameter names in order
    - query_params: tuple of query parameter names
    - normalization_rules: tuple of applied rule names
    - original: the original endpoint string
    """
    original = endpoint
    rules = []

    # Extract method if not provided
    if method is None:
        method = "UNKNOWN"

    # Extract query params before stripping
    query_params = tuple(_extract_query_params(endpoint))
    if query_params:
        rules.append("QUERY_PARAMS_EXTRACTED")

    # Check for template variables in query string
    query_match = _QUERY_RE.search(endpoint)
    if query_match:
        query_str = query_match.group(0)
        if _DOLLAR_BRACE_RE.search(query_str):
            rules.append("DOLLAR_BRACE_TEMPLATE")

    # Strip query string for path normalization
    path = _QUERY_RE.sub("", endpoint)

    # Extract path parameters from original (before normalization)
    path_params = tuple(_extract_path_params(endpoint))
    # Deduplicate while preserving order
    seen_params = set()
    unique_params = []
    for p in path_params:
        if p not in seen_params:
            seen_params.add(p)
            unique_params.append(p)
    path_params = tuple(unique_params)

    # First, handle encodeURIComponent specially - replace with unique placeholder
    # that won't be matched by subsequent regex passes
    encode_placeholders = {}
    encode_counter = 0

    def protect_encode_uri(match: re.Match) -> str:
        nonlocal encode_counter
        inner = match.group(1)
        encode_match = _ENCODE_URI_COMPONENT_RE.match(inner)
        if encode_match:
            param_name = encode_match.group(1).rstrip("!")
            placeholder = f"__ENCODE_{encode_counter}__"
            encode_placeholders[placeholder] = param_name
            encode_counter += 1
            rules.append("ENCODE_URI_COMPONENT")
            return placeholder
        return match.group(0)

    path = _DOLLAR_BRACE_RE.sub(protect_encode_uri, path)

    # Normalize remaining template variables: ${...} -> {param}
    def replace_dollar_brace(match: re.Match) -> str:
        rules.append("DOLLAR_BRACE_TEMPLATE")
        return "{param}"

    path = _DOLLAR_BRACE_RE.sub(replace_dollar_brace, path)

    # Normalize backend path parameters: {name} -> {param}
    def replace_brace_param(match: re.Match) -> str:
        rules.append("BRACE_PARAMETER")
        return "{param}"

    path = _BRACE_PARAM_RE.sub(replace_brace_param, path)

    # Normalize colon parameters: :name -> {param}
    def replace_colon_param(match: re.Match) -> str:
        rules.append("COLON_PARAMETER")
        return "{param}"

    path = _COLON_PARAM_RE.sub(replace_colon_param, path)

    # Restore encodeURIComponent placeholders with normalized {param}
    # (canonical form uses {param} for all parameters)
    for placeholder in encode_placeholders:
        path = path.replace(placeholder, "{param}")

    # Collapse multiple slashes
    if _MULTI_SLASH_RE.search(path):
        path = _MULTI_SLASH_RE.sub("/", path)
        rules.append("COLLAPSE_SLASHES")

    # Remove trailing slash (but keep leading slash)
    if path != "/" and path.endswith("/"):
        path = _TRAILING_SLASH_RE.sub("", path)
        rules.append("TRIM_TRAILING_SLASH")

    # Build canonical identity: METHOD:canonical_path
    canonical_path = f"{method.upper()}:{path}" if method != "UNKNOWN" else path

    return NormalizedEndpoint(
        original=original,
        canonical_path=canonical_path,
        method=method if method != "UNKNOWN" else None,
        path_params=path_params,
        query_params=query_params,
        normalization_rules=tuple(rules),
    )


def endpoints_match(
    endpoint1: str,
    endpoint2: str,
    method1: str | None = None,
    method2: str | None = None,
) -> bool:
    """Check if two endpoints are semantically equivalent."""
    norm1 = normalize_endpoint(endpoint1, method1)
    norm2 = normalize_endpoint(endpoint2, method2)
    return norm1.canonical_path == norm2.canonical_path


def get_canonical_key(endpoint: str, method: str | None = None) -> str:
    """Get the canonical key for an endpoint (for use in maps/sets)."""
    return normalize_endpoint(endpoint, method).canonical_path


class EndpointNormalizer:
    """Stateful normalizer for batch processing with consistent rule tracking."""

    def __init__(self) -> None:
        self._cache: dict[str, NormalizedEndpoint] = {}

    def normalize(self, endpoint: str, method: str | None = None) -> NormalizedEndpoint:
        cache_key = f"{method or 'ANY'}:{endpoint}"
        if cache_key not in self._cache:
            self._cache[cache_key] = normalize_endpoint(endpoint, method)
        return self._cache[cache_key]

    def match(
        self,
        frontend_endpoint: str,
        backend_endpoint: str,
        method: str | None = None,
    ) -> tuple[bool, NormalizedEndpoint, NormalizedEndpoint]:
        """Match a frontend endpoint against a backend endpoint."""
        fe_norm = self.normalize(frontend_endpoint, method)
        be_norm = self.normalize(backend_endpoint, method)
        return (fe_norm.canonical_path == be_norm.canonical_path, fe_norm, be_norm)

    def clear_cache(self) -> None:
        self._cache.clear()


# Default normalizer instance for convenience
DEFAULT_NORMALIZER = EndpointNormalizer()
