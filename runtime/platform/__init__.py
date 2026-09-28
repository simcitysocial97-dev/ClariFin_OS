"""Platform API — canonical internal contract/service boundary (M9-C57 Phase 1).

The :mod:`runtime.platform.api` package is the single authoritative
contract + adapter boundary between any client (GUI, AI, CLI) and the
underlying platform authorities (C50 control plane, evidence, knowledge,
observability, …).

It is **not** a control plane. It does not introduce a second executor, a
second evidence format, a second capability registry, a second task model,
or a second event store. It delegates to existing C50 subsystems.

Phase 1 (M9-C57) only establishes the canonical contract layer:

* :mod:`runtime.platform.api.envelope` — request/response/error envelopes.
* :mod:`runtime.platform.api.identity` — content-addressed identity primitives.
* :mod:`runtime.platform.api.errors` — PlatformError taxonomy and converter.
* :mod:`runtime.platform.api.contracts` — typed Pydantic models for every
  Phase 1 domain (health, capabilities, tasks, verification, executions,
  evidence, history, errors, architecture, events, application, change).

Service implementations (Phase 2) and the FastAPI mount (Phase 3) are
intentionally not part of this phase. See ``IMPLEMENTATION_ROADMAP.md``.
"""

from __future__ import annotations

__all__ = [
    "envelope",
    "identity",
    "errors",
    "contracts",
]
