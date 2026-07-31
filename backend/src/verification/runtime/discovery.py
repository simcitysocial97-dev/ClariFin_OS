"""Runtime discovery — delegates to the canonical implementation.

The authoritative discovery logic lives in ``backend/tests/verification_runtime/discovery.py``
(importable as ``runtime.discovery`` when running from ``backend/``).
This module provides the same API surface from the ``src.verification.runtime``
package so that code importing ``src.verification.runtime.discovery`` gets
real data instead of empty stubs.
"""

from __future__ import annotations

from typing import Any, cast


def _delegate(func_name: str) -> Any:
    """Import and call the real implementation from verification_runtime.discovery."""
    try:
        from verification_runtime.discovery import (  # type: ignore[import-not-found]
            discover_capabilities as _real,
        )
        from verification_runtime.discovery import (
            discover_capability_tests as _real_ct,
        )
        from verification_runtime.discovery import (
            discover_contract_tests as _real_ctr,
        )
        from verification_runtime.discovery import (
            discover_dependencies as _real_dep,
        )
        from verification_runtime.discovery import (
            discover_golden_datasets as _real_gd,
        )
        from verification_runtime.discovery import (
            discover_invariant_tests as _real_inv,
        )
        from verification_runtime.discovery import (
            discover_property_tests as _real_pt,
        )
    except ImportError:
        return (
            [] if "dependencies" not in func_name else {"capabilities": {}, "edges": []}
        )

    mapping = {
        "discover_capabilities": _real,
        "discover_capability_tests": _real_ct,
        "discover_contract_tests": _real_ctr,
        "discover_dependencies": _real_dep,
        "discover_golden_datasets": _real_gd,
        "discover_invariant_tests": _real_inv,
        "discover_property_tests": _real_pt,
    }
    func = mapping.get(func_name)
    if func is None:
        return (
            [] if "dependencies" not in func_name else {"capabilities": {}, "edges": []}
        )
    return func()


def discover_capabilities() -> list[dict[str, Any]]:
    """Discover all capabilities in the project."""
    return cast(list[dict[str, Any]], _delegate("discover_capabilities"))


def discover_capability_tests() -> list[dict[str, Any]]:
    """Discover capability test files."""
    return cast(list[dict[str, Any]], _delegate("discover_capability_tests"))


def discover_contract_tests() -> list[dict[str, Any]]:
    """Discover contract test files."""
    return cast(list[dict[str, Any]], _delegate("discover_contract_tests"))


def discover_golden_datasets() -> list[dict[str, Any]]:
    """Discover golden dataset files."""
    return cast(list[dict[str, Any]], _delegate("discover_golden_datasets"))


def discover_invariant_tests() -> list[dict[str, Any]]:
    """Discover invariant test files."""
    return cast(list[dict[str, Any]], _delegate("discover_invariant_tests"))


def discover_property_tests() -> list[dict[str, Any]]:
    """Discover property test files."""
    return cast(list[dict[str, Any]], _delegate("discover_property_tests"))


def discover_dependencies() -> dict[str, Any]:
    """Discover dependency graph for capabilities.

    Generates all 8 required edge types:
    - capability → source (engines)
    - capability → routers
    - capability → services
    - capability → repositories
    - capability → engines
    - capability → unit tests
    - capability → property tests
    - capability → contract tests
    - capability → capability tests
    - capability → golden datasets
    - capability → invariant tests
    """
    return cast(dict[str, Any], _delegate("discover_dependencies"))
