"""Platform API service adapters (M9-C57 Phase 2).

Each module in this package is a thin **adapter** that aggregates real
data from existing C50 / observability / knowledge / repository
authorities into the typed contracts defined by
:mod:`runtime.platform.api.contracts`.

Phase 2 explicitly forbids:

* New persistent models.
* Mock platform state for production paths.
* Bypassing the canonical control plane / executor / evidence.

All services here are read-only adapters. They consume the existing
authorities and emit validated contract payloads wrapped in the
canonical envelope. Writes go through the canonical control plane (Phase
3+ FastAPI mount will use ``ControlPlaneFacade``).
"""

from __future__ import annotations

__all__: list[str] = []
