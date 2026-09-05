"""History contracts (Phase 1 — ``/platform/v1/history/*``).

Phase 1 defines the JSON shape for history runs, baselines, and the
compare endpoint. Phase 2 services populate these from
``runtime.generated.engineering-history.json`` and
``runtime.system.observability.health_report``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Status, Timestamp


HISTORY_RUNS_KIND: str = "platform.history_runs"
HISTORY_RUN_KIND: str = "platform.history_run"
HISTORY_COMPARE_KIND: str = "platform.history_compare"
HISTORY_BASELINES_KIND: str = "platform.history_baselines"


class HistoryRunSummary(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    started_at: Timestamp
    finished_at: Optional[Timestamp] = None
    duration_ms: Optional[int] = Field(default=None, ge=0)
    status: Status
    capabilities_run: int = Field(ge=0)
    capabilities_passed: int = Field(ge=0)
    capabilities_failed: int = Field(ge=0)


class HistoryRunsData(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    items: list[HistoryRunSummary] = Field(default_factory=list)


class HistoryRunsEnvelope(BaseModel):
    kind: str = Field(default=HISTORY_RUNS_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: HistoryRunsData


class HistoryRunDetailData(BaseModel):
    """Full single-run detail."""

    id: str = Field(min_length=1, max_length=256)
    started_at: Timestamp
    finished_at: Optional[Timestamp] = None
    duration_ms: Optional[int] = Field(default=None, ge=0)
    status: Status
    capabilities_run: int = Field(ge=0)
    capabilities_passed: int = Field(ge=0)
    capabilities_failed: int = Field(ge=0)
    capability_results: list[dict] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class HistoryRunEnvelope(BaseModel):
    kind: str = Field(default=HISTORY_RUN_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: HistoryRunDetailData


class HistoryCompareRequestData(BaseModel):
    current_run_id: str = Field(min_length=1, max_length=256)
    baseline: str = Field(min_length=1, max_length=64)
    include_evidence: bool = False


class HistoryCompareData(BaseModel):
    """Output of ``/history/compare``.

    The ``delta`` dict mirrors the dimensions described in
    ``IMPLEMENTATION_ROADMAP.md`` Phase 8 (repository changes, test
    results, durations, evidence invalidated, obligations,
    capability state changes). Phase 1 only fixes the envelope.
    """

    current_run: dict = Field(default_factory=dict)
    baseline_run: dict = Field(default_factory=dict)
    delta: dict = Field(default_factory=dict)


class HistoryCompareEnvelope(BaseModel):
    kind: str = Field(default=HISTORY_COMPARE_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: HistoryCompareData


class HistoryBaselineItem(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    run_id: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=512)
    recorded_at: Timestamp


class HistoryBaselinesData(BaseModel):
    items: list[HistoryBaselineItem] = Field(default_factory=list)


class HistoryBaselinesEnvelope(BaseModel):
    kind: str = Field(default=HISTORY_BASELINES_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: HistoryBaselinesData


__all__ = [
    "HISTORY_BASELINES_KIND",
    "HISTORY_COMPARE_KIND",
    "HISTORY_RUNS_KIND",
    "HISTORY_RUN_KIND",
    "HistoryBaselineItem",
    "HistoryBaselinesData",
    "HistoryBaselinesEnvelope",
    "HistoryCompareData",
    "HistoryCompareEnvelope",
    "HistoryCompareRequestData",
    "HistoryRunDetailData",
    "HistoryRunEnvelope",
    "HistoryRunsData",
    "HistoryRunsEnvelope",
    "HistoryRunSummary",
]
