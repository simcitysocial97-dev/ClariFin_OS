"""AI Context Engine package (Phase 14).

Deterministic, reproducible, provenance-aware context assembly.
"""

from __future__ import annotations

from runtime.platform.ai.context.builder import (
    CONTEXT_PACK_KIND,
    ContextBuilder,
    build_context_pack,
)
from runtime.platform.ai.context.cache import (
    CONTEXT_PACK_CACHE_INSTANCE,
    ContextPackCache,
)
from runtime.platform.ai.context.provenance import (
    PROVENANCE_TRACKER_INSTANCE,
    ProvenanceEntry,
    ProvenanceKind,
    ProvenanceTracker,
    build_provenance,
)
from runtime.platform.ai.context.ranker import RANKER_INSTANCE, RankedComponent, Ranker
from runtime.platform.ai.context.serializer import (
    _canonical_value,
    compute_pack_checksum,
    compute_pack_id,
    estimate_tokens,
    serialize_context_pack,
)
from runtime.platform.ai.context.trimmer import TRIMMER_INSTANCE, Trimmer, TrimmerResult

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
