"""Adapter ABC and per-kind adapter registry."""

from __future__ import annotations


def __getattr__(name: str):
    if name == "ADAPTERS":
        from runtime.foundation.verification.executor_pipeline import (  # noqa: PLC0415
            ADAPTERS as _adapters,
        )
        return _adapters
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
