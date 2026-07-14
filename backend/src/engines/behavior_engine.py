"""
Behavior Engine (Legacy Compatibility Shim)
=========================================

DEPRECATED: All computation moved to BehaviourService.

This module is now a thin wrapper that delegates to BehaviourService.compute_profile().
Maintained for backwards compatibility during migration only.
"""

import warnings
from typing import Any

# Deprecation warning for legacy imports
warnings.warn(
    "behavior_engine is deprecated. Use BehaviourService.compute_profile(db_path) instead.",
    DeprecationWarning,
    stacklevel=2,
)


def invalidate_behavior_cache() -> None:
    """Clear the behavior profile cache. Delegates to BehaviourService."""
    from src.services.behaviour_service import invalidate_behaviour_cache
    invalidate_behaviour_cache()


def get_cached_behavior_profile(db_path: str) -> dict[str, Any] | None:
    """Get behavior profile from cache if available. Delegates to BehaviourService."""
    from src.services.behaviour_service import BehaviourService
    svc = BehaviourService(db_path)
    return svc.get_cached_profile("default")


def set_cached_behavior_profile(db_path: str, profile: dict[str, Any]) -> None:
    """Cache a behavior profile. Delegates to BehaviourService."""
    from src.services.behaviour_service import BehaviourService
    svc = BehaviourService(db_path)
    svc.set_cached_profile("default", profile)


def compute_behavior_profile(db_path: str) -> dict[str, Any]:
    """
    Compute comprehensive behavioral profile.

    DEPRECATED: Use BehaviourService.compute_profile(db_path) instead.

    Delegates to BehaviourService.compute_profile() which uses repositories
    and pure functions from behaviour_engine/ package.

    Returns:
        {
            "temporal_patterns": {...},
            "behavioral_indices": {...},
            "risk_signals": {...},
            "confidence": float (0–1),
            "financial_health_score": float (0–100)
        }
    """
    from src.services.behaviour_service import BehaviourService
    svc = BehaviourService(db_path)
    return svc.compute_profile(db_path)
