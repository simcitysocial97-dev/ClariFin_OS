"""Canonical Engineering Intelligence Layer.

The only intelligence implementation inside the runtime. The legacy
``runtime/foundation/intelligence/{affected,diagnostics,risk,repair,
formatter,models}.py`` modules were eliminated in Program 14.1; every runtime
command now resolves ownership, change, blast radius, verification, risk and
repair through this package and its single internal :mod:`api`.
"""

from __future__ import annotations

from runtime.foundation.intelligence.platform.api import (  # noqa: F401
    analyze,
    affected_entities,
    blast_radius,
    engineering_risk,
    repair_plan,
    resolve_entity,
    test_resolution,
    verification_plan,
)
from runtime.foundation.intelligence.platform.cli_format import (  # noqa: F401
    format_affected,
    format_diagnostic,
    format_repair,
    format_risk,
)
from runtime.foundation.intelligence.platform.resolver import (  # noqa: F401
    EntityRef,
    EntityResolver,
    get_resolver,
    reset_resolver,
)

__all__ = [
    "EntityRef",
    "EntityResolver",
    "get_resolver",
    "reset_resolver",
    "resolve_entity",
    "affected_entities",
    "blast_radius",
    "verification_plan",
    "engineering_risk",
    "repair_plan",
    "test_resolution",
    "analyze",
    "format_affected",
    "format_diagnostic",
    "format_repair",
    "format_risk",
]
