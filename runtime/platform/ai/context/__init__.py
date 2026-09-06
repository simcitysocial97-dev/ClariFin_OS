"""AI Context Engine package (Phase 14).

Deterministic, reproducible, provenance-aware context assembly.
"""

from __future__ import annotations

from runtime.platform.ai.context.builder import ContextBuilder, build_context_pack, CONTEXT_PACK_KIND
from runtime.platform.ai.context.ranker import Ranker, RankedComponent, RANKER_INSTANCE
from runtime.platform.ai.context.trimmer import Trimmer, TrimmerResult, TRIMMER_INSTANCE
from runtime.platform.ai.context.provenance import (
    ProvenanceEntry,
    ProvenanceKind,
    ProvenanceTracker,
    PROVENANCE_TRACKER_INSTANCE,
    build_provenance,
)
from runtime.platform.ai.context.serializer import (
    serialize_context_pack,
    compute_pack_id,
    estimate_tokens,
    compute_pack_checksum,
    _canonical_value,
)
from runtime.platform.ai.context.cache import ContextPackCache, CONTEXT_PACK_CACHE_INSTANCE

__all__ = [
    # Builder
    "ContextBuilder",
    "build_context_pack",
    "CONTEXT_PACK_KIND",
    # Ranker
    "Ranker",
    "RankedComponent",
    "RANKER_INSTANCE",
    # Trimmer
    "Trimmer",
    "TrimmerResult",
    "TRIMMER_INSTANCE",
    # Provenance
    "ProvenanceEntry",
    "ProvenanceKind",
    "ProvenanceTracker",
    "PROVENANCE_TRACKER_INSTANCE",
    "build_provenance",
    # Serializer
    "serialize_context_pack",
    "compute_pack_id",
    "estimate_tokens",
    "compute_pack_checksum",
    "_canonical_value",
    # Cache
    "ContextPackCache",
    "CONTEXT_PACK_CACHE_INSTANCE",
]
