"""Engineering Intelligence Layer — Program 14.0.

This package answers the *active* engineering questions:

    "What changed?"  "What is broken?"  "What should be verified?"
    "What is the smallest safe validation?"  "What is the engineering risk?"

Constitutional constraints (Programs 13.1-13.3) that every module here obeys:

* Architecture is NEVER rebuilt. Every architectural fact comes from
  :func:`runtime.foundation.architecture.get_architecture`.
* Ownership is NEVER reconstructed. Ownership questions are answered by
  ``Architecture.engine_for_path`` and the canonical ownership graph.
* Filenames are NEVER inferred. Tests, routers, capabilities and workspaces
  are read from provider state, not synthesised from string patterns.
* Discovery is NEVER duplicated. This package performs zero filesystem
  scanning of production code.

The only non-provider inputs are *change* inputs (git diff) and *history*
inputs (recorded runtime events / CI metadata), which are by definition not
architectural facts.
"""

from __future__ import annotations

from runtime.foundation.intelligence.platform.resolver import (  # noqa: F401
    EntityRef,
    EntityResolver,
    get_resolver,
    reset_resolver,
)

__all__ = ["EntityRef", "EntityResolver", "get_resolver", "reset_resolver"]
