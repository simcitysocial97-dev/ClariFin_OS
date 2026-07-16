"""Capability Registry - Runtime API for capability discovery.

This module loads the YAML capability registry and provides methods for
validating and querying capability metadata. It does NOT own the registry -
only loads and validates it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

# Registry path - single source of truth
REGISTRY_PATH = Path(__file__).parent.parent.parent.parent / "memory-bank" / "capability-registry.yaml"


class CapabilityNotFoundError(Exception):
    """Raised when a capability is not found in the registry."""
    pass


class RegistryValidationError(Exception):
    """Raised when registry validation fails."""
    pass


# Type alias for capability dict
Capability = dict[str, Any]


class CapabilityRegistry:
    """Runtime accessor for capability registry with validation."""

    _instance: CapabilityRegistry | None = None
    _data: dict[str, Any] | None = None

    def __new__(cls) -> CapabilityRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load(self) -> dict[str, Any]:
        """Load registry from YAML. Validates and caches."""
        if self._data is None:
            with open(REGISTRY_PATH) as f:
                loaded = yaml.safe_load(f)
                self._data = loaded if loaded is not None else {"capabilities": []}
            self._validate()
        return self._data

    def _validate(self) -> None:
        """Validate registry schema and detect issues."""
        errors: list[str] = []

        if self._data is None:
            return

        capabilities: list[Capability] = self._data.get("capabilities", [])

        # Validate required fields
        required_fields = ["id", "name", "maturity", "status", "dependencies"]

        for cap in capabilities:
            for field in required_fields:
                if field not in cap:
                    errors.append(f"Capability '{cap.get('id', 'unknown')}' missing '{field}'")

        # Validate maturity values
        valid_maturity = frozenset({"functional", "analytical", "explainable", "optimized"})
        for cap in capabilities:
            mat = cap.get("maturity")
            if mat and mat not in valid_maturity:
                errors.append(f"Capability '{cap.get('id')}' has invalid maturity: {mat}")

        # Validate status values
        valid_status = frozenset({"active", "deprecated", "maintenance"})
        for cap in capabilities:
            status = cap.get("status")
            if status and status not in valid_status:
                errors.append(f"Capability '{cap.get('id')}' has invalid status: {status}")

        # Detect duplicate IDs
        ids: list[str] = []
        for cap in capabilities:
            cap_id_raw = cap.get("id")
            if isinstance(cap_id_raw, str):
                ids.append(cap_id_raw)
        seen_ids: set[str] = set()
        dup_ids: list[str] = []
        for i in ids:
            if i in seen_ids:
                dup_ids.append(i)
            else:
                seen_ids.add(i)
        if dup_ids:
            errors.append(f"Duplicate capability IDs: {set(dup_ids)}")

        # Detect duplicate query keys (frontend)
        query_keys_map: dict[str, str] = {}
        for cap in capabilities:
            cap_id = cap.get("id", "unknown")
            if isinstance(cap_id, str):
                for key in cap.get("query_keys", []):
                    if isinstance(key, str):
                        if key in query_keys_map:
                            errors.append(f"Duplicate query key '{key}' in '{query_keys_map[key]}' and '{cap_id}'")
                        else:
                            query_keys_map[key] = cap_id

        # Detect duplicate backend routes
        backend_routes_map: dict[str, str] = {}
        for cap in capabilities:
            cap_id = cap.get("id", "unknown")
            if isinstance(cap_id, str):
                for route in cap.get("backend_routes", []):
                    if isinstance(route, str):
                        if route in backend_routes_map:
                            errors.append(f"Duplicate backend route '{route}' in '{backend_routes_map[route]}' and '{cap_id}'")
                        else:
                            backend_routes_map[route] = cap_id

        # Validate dependencies exist
        valid_ids = set(ids)
        for cap in capabilities:
            cap_id = cap.get("id", "unknown")
            if isinstance(cap_id, str):
                for dep in cap.get("dependencies", []):
                    if isinstance(dep, str) and dep not in valid_ids:
                        errors.append(f"Capability '{cap_id}' has missing dependency: {dep}")

        # Detect circular dependencies - use global_visited to track all nodes in current path
        all_visited: set[str] = set()

        def has_cycle(cid: str, path: set[str]) -> bool:
            """Check if visiting cid creates a cycle."""
            if cid in path:
                return True
            if cid in all_visited:
                return False  # Already checked this node

            path.add(cid)
            for cap in capabilities:
                if cap.get("id") == cid:
                    for dep in cap.get("dependencies", []):
                        if isinstance(dep, str) and has_cycle(dep, path):
                            return True
                    break
            path.discard(cid)
            all_visited.add(cid)
            return False

        for cap in capabilities:
            cid = cap.get("id", "")
            if isinstance(cid, str) and has_cycle(cid, set()):
                errors.append(f"Circular dependency detected for '{cid}'")

        if errors:
            raise RegistryValidationError("\n".join(errors))

    def get(self, capability_id: str) -> Capability:
        """Get a capability by ID. Raises CapabilityNotFoundError if not found."""
        data = self._load()
        caps = data.get("capabilities", [])
        for cap in caps:
            if cap.get("id") == capability_id:
                return cast(Capability, cap)
        raise CapabilityNotFoundError(f"Capability '{capability_id}' not found")

    def all(self) -> list[Capability]:
        """Get all capabilities."""
        data = self._load()
        caps = data.get("capabilities", [])
        if isinstance(caps, list):
            return cast(list[Capability], caps)
        return []

    def ids(self) -> list[str]:
        """Get all capability IDs."""
        return [cap.get("id", "") for cap in self.all() if isinstance(cap.get("id"), str)]

    def dependencies(self, capability_id: str) -> list[str]:
        """Get dependencies for a capability."""
        cap = self.get(capability_id)
        deps = cap.get("dependencies", [])
        return [d for d in deps if isinstance(d, str)]

    def frontend_routes(self) -> dict[str, list[str]]:
        """Get all frontend routes keyed by capability ID."""
        result: dict[str, list[str]] = {}
        for cap in self.all():
            cid = cap.get("id")
            if isinstance(cid, str):
                routes = cap.get("frontend_routes", [])
                result[cid] = [r for r in routes if isinstance(r, str)]
        return result

    def backend_routes(self) -> dict[str, list[str]]:
        """Get all backend routes keyed by capability ID."""
        result: dict[str, list[str]] = {}
        for cap in self.all():
            cid = cap.get("id")
            if isinstance(cid, str):
                routes = cap.get("backend_routes", [])
                result[cid] = [r for r in routes if isinstance(r, str)]
        return result

    def query_keys(self) -> dict[str, list[str]]:
        """Get all query keys keyed by capability ID."""
        result: dict[str, list[str]] = {}
        for cap in self.all():
            cid = cap.get("id")
            if isinstance(cid, str):
                keys = cap.get("query_keys", [])
                result[cid] = [k for k in keys if isinstance(k, str)]
        return result

    def validate(self) -> list[str]:
        """Validate registry and return list of errors (empty if valid)."""
        try:
            self._load()
            return []
        except RegistryValidationError as e:
            return str(e).split("\n")


# Module-level convenience functions
_registry: CapabilityRegistry | None = None


def get_registry() -> CapabilityRegistry:
    """Get singleton registry instance."""
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry


def get_capability(capability_id: str) -> Capability:
    """Get capability by ID."""
    return get_registry().get(capability_id)


def all_capabilities() -> list[Capability]:
    """Get all capabilities."""
    return get_registry().all()


def capability_ids() -> list[str]:
    """Get all capability IDs."""
    return get_registry().ids()


def capability_dependencies(capability_id: str) -> list[str]:
    """Get dependencies for a capability."""
    return get_registry().dependencies(capability_id)


def frontend_routes() -> dict[str, list[str]]:
    """Get all frontend routes."""
    return get_registry().frontend_routes()


def backend_routes() -> dict[str, list[str]]:
    """Get all backend routes."""
    return get_registry().backend_routes()


def query_keys() -> dict[str, list[str]]:
    """Get all query keys."""
    return get_registry().query_keys()


def validate_registry() -> list[str]:
    """Validate registry and return errors."""
    return get_registry().validate()
