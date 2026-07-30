"""Verification Runtime — unified registry and discovery for ClariFin_OS.

This package provides:
- Unified registry loaders for all verification metadata
- Automatic discovery of engines, services, routers, capabilities, builders, fixtures
- Simplified orchestrator that uses registry-driven targets
- Self-validation meta-tests for registry integrity

Design principles:
- Registration over hardcoding
- Discovery over manual wiring
- Metadata over duplication
- Capabilities over folders
"""

from __future__ import annotations
