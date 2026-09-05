"""Platform API typed contracts (M9-C57 Phase 1).

Phase 1 establishes typed Pydantic models for every Platform API domain:

* :mod:`runtime.platform.api.contracts.health`
* :mod:`runtime.platform.api.contracts.capabilities`
* :mod:`runtime.platform.api.contracts.tasks`
* :mod:`runtime.platform.api.contracts.verification`
* :mod:`runtime.platform.api.contracts.executions`
* :mod:`runtime.platform.api.contracts.evidence`
* :mod:`runtime.platform.api.contracts.history`
* :mod:`runtime.platform.api.contracts.errors`
* :mod:`runtime.platform.api.contracts.architecture`
* :mod:`runtime.platform.api.contracts.events`
* :mod:`runtime.platform.api.contracts.application`
* :mod:`runtime.platform.api.contracts.change`
* :mod:`runtime.platform.api.contracts.ai`

These contracts are the **single source of truth** for the JSON shape of
every Platform API response. They are deliberately thin:

* No service implementations.
* No persistence.
* No network.

They are pydantic ``BaseModel`` subclasses that:

* validate input payloads,
* serialize via ``model_dump(mode="json")``,
* expose ``kind`` constants for envelope assembly.

Phase 2 (Service Aggregators) is responsible for producing these payloads
from C50 / observability / knowledge authorities.
"""

from __future__ import annotations

__all__: list[str] = []
