"""
M9-C55 — Verification configuration loader.

Loads runtime/foundation/verification/verification.yaml and provides
typed accessors for thresholds and other tunable parameters.

All values fall back to documented defaults when absent from the yaml,
so code that reads here never breaks on missing keys.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover — tested in CI where pyyaml is installed
    yaml = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_YAML_PATH = REPO_ROOT / "runtime" / "foundation" / "verification" / "verification.yaml"


@functools.lru_cache(maxsize=1)
def _load_yaml(path: Path | str | None = None) -> dict[str, Any]:
    """Load and cache the verification.yaml contents."""
    yaml_path = Path(path) if path else DEFAULT_YAML_PATH
    if yaml_path.exists() and yaml is not None:
        try:
            with yaml_path.open("r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except Exception:
            return {}
    return {}


def _get_nested(data: dict[str, Any], *keys: str) -> Any:
    """Safely traverse nested dicts, returning None on missing keys."""
    cur: Any = data
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur


def get_threshold(category: str, key: str, default: int | float) -> int | float:
    """Return a named threshold from verification.yaml with fallback.

    Categories and keys that exist in the yaml::

        backend.coverage_threshold
        backend.mutation_threshold
        mutation_thresholds.full_campaign
        mutation_thresholds.incremental
        mutation_thresholds.smoke
        regression_thresholds.coverage_drop_warning
        regression_thresholds.coverage_drop_critical
        regression_thresholds.mutation_drop_warning
        regression_thresholds.mutation_drop_critical
        regression_thresholds.test_count_drop_warning

    Parameters
    ----------
    category : str
        Top-level key in the yaml (e.g. ``"backend"``) or a mapping prefix
        such as ``"mutation_thresholds"`` / ``"regression_thresholds"``.
    key : str
        Leaf key within the category (e.g. ``"coverage_threshold"``).
    default : int | float
        Value returned when the yaml key is missing or non-numeric.
    """
    data = _load_yaml()
    raw = _get_nested(data, category, key)
    if raw is None:
        return default
    try:
        return int(raw) if isinstance(raw, (int, float)) else default
    except (TypeError, ValueError):
        return default


def get_config(*keys: str) -> Any:
    """Return an arbitrary nested value from verification.yaml.

    Usage::

        get_config("backend", "paths", "source")  # → "backend/src"
    """
    data = _load_yaml()
    return _get_nested(data, *keys)


def reload_config() -> None:
    """Clear the YAML cache — useful in tests that patch the yaml file."""
    _load_yaml.cache_clear()
