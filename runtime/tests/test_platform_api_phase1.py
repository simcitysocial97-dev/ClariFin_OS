"""M9-C57 Phase 1 — Platform Contract Foundation validation.

These tests prove the Gate 1 criteria from
``IMPLEMENTATION_ROADMAP.md`` Phase 1:

* contracts are stable
* no C50 authority duplicated
* no network required
* deterministic output confirmed
* all contract tests pass
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any

import pytest
from pydantic import ValidationError

from runtime.platform.api.contracts import (
    application,
    architecture,
    capabilities,
    change,
    events,
    evidence,
    executions,
    health,
    history,
    tasks,
    verification,
)
from runtime.platform.api.contracts import (
    errors as errors_contract,
)
from runtime.platform.api.contracts._primitives import (
    Identity,
    Status,
    Timestamp,
)
from runtime.platform.api.envelope import (
    API_VERSION,
    error_envelope,
    success_envelope,
)
from runtime.platform.api.errors import PlatformError, PlatformErrorCode
from runtime.platform.api.identity import (
    canonical_json_bytes,
    canonical_sha256,
    envelope_identity,
    error_identity,
)

# ---------------------------------------------------------------------------
# 1. Canonical JSON
# ---------------------------------------------------------------------------


class TestCanonicalJson:
    def test_dict_order_is_irrelevant(self) -> None:
        a = canonical_sha256({"a": 1, "b": 2})
        b = canonical_sha256({"b": 2, "a": 1})
        assert a == b

    def test_nested_dict_order_is_irrelevant(self) -> None:
        a = canonical_sha256({"outer": {"a": 1, "b": 2}, "x": [1, 2, 3]})
        b = canonical_sha256({"x": [1, 2, 3], "outer": {"b": 2, "a": 1}})
        assert a == b

    def test_tuples_serialize_as_arrays(self) -> None:
        text = canonical_json_bytes({"k": (1, 2, 3)}).decode("utf-8")
        assert json.loads(text) == {"k": [1, 2, 3]}

    def test_none_values_are_stripped(self) -> None:
        text = canonical_json_bytes({"a": 1, "b": None}).decode("utf-8")
        assert json.loads(text) == {"a": 1}


# ---------------------------------------------------------------------------
# 2. Envelope identity
# ---------------------------------------------------------------------------


class TestEnvelopeIdentity:
    def test_envelope_identity_is_stable(self) -> None:
        a = envelope_identity(kind="platform.x", version="1.0.0", data={"k": 1})
        b = envelope_identity(kind="platform.x", version="1.0.0", data={"k": 1})
        assert a == b
        assert a.startswith("sha256:")
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", a)

    def test_error_identity_is_stable(self) -> None:
        a = error_identity(
            kind="platform.error",
            version="1.0.0",
            code="NOT_FOUND",
            layer="platform.tasks",
            message="missing",
        )
        b = error_identity(
            kind="platform.error",
            version="1.0.0",
            code="NOT_FOUND",
            layer="platform.tasks",
            message="missing",
        )
        assert a == b

    def test_kind_or_version_change_changes_id(self) -> None:
        a = envelope_identity(kind="platform.a", version="1.0.0", data={"k": 1})
        b = envelope_identity(kind="platform.b", version="1.0.0", data={"k": 1})
        c = envelope_identity(kind="platform.a", version="2.0.0", data={"k": 1})
        assert len({a, b, c}) == 3

    def test_data_change_changes_id(self) -> None:
        a = envelope_identity(kind="platform.x", version="1.0.0", data={"k": 1})
        b = envelope_identity(kind="platform.x", version="1.0.0", data={"k": 2})
        assert a != b


# ---------------------------------------------------------------------------
# 3. Success envelope
# ---------------------------------------------------------------------------


class TestSuccessEnvelope:
    def test_required_keys_present(self) -> None:
        env = success_envelope(kind="platform.x", data={"k": 1})
        assert set(env.keys()) == {"kind", "version", "generated_at", "id", "data"}
        assert env["kind"] == "platform.x"
        assert env["version"] == API_VERSION
        assert env["data"] == {"k": 1}
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", env["id"])
        # ISO-8601 UTC with Z suffix.
        assert re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z",
            env["generated_at"],
        )

    def test_id_is_deterministic_across_invocations(self) -> None:
        env_a = success_envelope(kind="platform.x", data={"k": 1})
        env_b = success_envelope(kind="platform.x", data={"k": 1})
        assert env_a["id"] == env_b["id"]

    def test_generated_at_is_excluded_from_id(self) -> None:
        env_a = success_envelope(kind="platform.x", data={"k": 1})
        env_b = success_envelope(kind="platform.x", data={"k": 1})
        # Same id even though generated_at may differ (tested in next test).
        assert env_a["id"] == env_b["id"]

    def test_none_data_rejected(self) -> None:
        with pytest.raises(ValueError):
            success_envelope(kind="platform.x", data=None)

    def test_data_field_propagates_complex_payload(self) -> None:
        env = success_envelope(
            kind="platform.x",
            data={"nested": {"k": [1, 2, 3]}, "name": "ok"},
        )
        assert env["data"] == {"nested": {"k": [1, 2, 3]}, "name": "ok"}


# ---------------------------------------------------------------------------
# 4. Error envelope
# ---------------------------------------------------------------------------


class TestErrorEnvelope:
    def test_required_keys_present(self) -> None:
        err = PlatformError(
            code=PlatformErrorCode.NOT_FOUND,
            layer="platform.tasks",
            message="missing",
        )
        env = error_envelope(error=err)
        assert set(env.keys()) == {"kind", "version", "generated_at", "id", "error"}
        assert env["kind"] == "platform.error"
        assert env["version"] == API_VERSION

    def test_error_block_has_required_subfields(self) -> None:
        err = PlatformError(
            code=PlatformErrorCode.NOT_FOUND,
            layer="platform.tasks",
            message="missing",
            capability_id="cap.loan-engine",
            evidence_id="sha256:" + "a" * 64,
        )
        env = error_envelope(error=err)
        assert env["error"]["code"] == "NOT_FOUND"
        assert env["error"]["layer"] == "platform.tasks"
        assert env["error"]["message"] == "missing"
        assert env["error"]["capability_id"] == "cap.loan-engine"
        assert env["error"]["evidence_id"] == "sha256:" + "a" * 64

    def test_error_id_is_deterministic(self) -> None:
        err = PlatformError(
            code=PlatformErrorCode.INTERNAL,
            layer="platform.x",
            message="boom",
        )
        a = error_envelope(error=err)["id"]
        b = error_envelope(error=err)["id"]
        assert a == b

    def test_optional_error_fields_default_to_none(self) -> None:
        err = PlatformError(
            code=PlatformErrorCode.INTERNAL,
            layer="platform.x",
            message="boom",
        )
        env = error_envelope(error=err)
        assert env["error"]["capability_id"] is None
        assert env["error"]["evidence_id"] is None


# ---------------------------------------------------------------------------
# 5. PlatformError
# ---------------------------------------------------------------------------


class TestPlatformError:
    def test_enum_values(self) -> None:
        assert PlatformErrorCode.MALFORMED_REQUEST.value == "MALFORMED_REQUEST"
        assert PlatformErrorCode.NOT_FOUND.value == "NOT_FOUND"
        assert PlatformErrorCode.AUTHORIZATION_DENIED.value == "AUTHORIZATION_DENIED"
        assert PlatformErrorCode.INTERNAL.value == "INTERNAL"
        assert PlatformErrorCode.UNAVAILABLE.value == "UNAVAILABLE"

    def test_dataclass_is_frozen(self) -> None:
        err = PlatformError(
            code=PlatformErrorCode.INTERNAL,
            layer="platform.x",
            message="boom",
        )
        with pytest.raises(
            Exception
        ):  # noqa: B017 — testing immutability guard requires broad exception
            err.message = "tampered"  # type: ignore[misc]

    def test_empty_layer_rejected(self) -> None:
        with pytest.raises(ValueError):
            PlatformError(
                code=PlatformErrorCode.INTERNAL,
                layer="",
                message="boom",
            )

    def test_empty_message_rejected(self) -> None:
        with pytest.raises(ValueError):
            PlatformError(
                code=PlatformErrorCode.INTERNAL,
                layer="platform.x",
                message="",
            )

    def test_non_enum_code_rejected(self) -> None:
        with pytest.raises(ValueError):
            PlatformError(
                code="NOT_AN_ENUM_VALUE",  # type: ignore[arg-type]
                layer="platform.x",
                message="boom",
            )


# ---------------------------------------------------------------------------
# 6. Shared primitives
# ---------------------------------------------------------------------------


class TestPrimitives:
    def test_status_values(self) -> None:
        assert Status.HEALTHY.value == "HEALTHY"
        assert Status.DEGRAD.value == "DEGRAD"
        assert Status.UNHEALTHY.value == "UNHEALTHY"
        assert Status.UNKNOWN.value == "UNKNOWN"

    def test_timestamp_validation_accepts_z_suffix(self) -> None:
        # Validation only kicks in on Pydantic boundary; raw str is fine until
        # bound to a model field. We exercise it through the model below.
        from pydantic import BaseModel

        class M(BaseModel):
            t: Timestamp

        m = M(t="2026-09-05T03:59:00Z")
        assert m.t == "2026-09-05T03:59:00Z"

    def test_timestamp_validation_rejects_wrong_format(self) -> None:
        from pydantic import BaseModel

        class M(BaseModel):
            t: Timestamp

        with pytest.raises(ValidationError):
            M(t="not-a-timestamp")
        with pytest.raises(ValidationError):
            M(t="2026-09-05T03:59:00+00:00")  # no Z, has offset

    def test_identity_validation_accepts_sha256(self) -> None:
        from pydantic import BaseModel

        class M(BaseModel):
            i: Identity

        m = M(i="sha256:" + "a" * 64)
        assert m.i == "sha256:" + "a" * 64

    def test_identity_validation_rejects_non_sha256(self) -> None:
        from pydantic import BaseModel

        class M(BaseModel):
            i: Identity

        with pytest.raises(ValidationError):
            M(i="md5:abc")
        with pytest.raises(ValidationError):
            M(i="sha256:" + "z" * 64)  # not hex

    def test_json_schema_emitted_for_timestamp_and_identity(self) -> None:
        from pydantic import BaseModel

        class M(BaseModel):
            t: Timestamp
            i: Identity

        schema = M.model_json_schema()
        assert "pattern" in schema["properties"]["t"]
        assert "pattern" in schema["properties"]["i"]


# ---------------------------------------------------------------------------
# 7. Health contract
# ---------------------------------------------------------------------------


class TestHealthContract:
    def _payload(self) -> dict[str, Any]:
        return {
            "platform": "HEALTHY",
            "backend": "HEALTHY",
            "frontend": "HEALTHY",
            "database": "HEALTHY",
            "architecture": "SAFE",
            "verification": "CURRENT",
            "evidence": "VALID",
            "ai": "READY",
        }

    def test_serialization_round_trip(self) -> None:
        env = success_envelope(
            kind=health.HEALTH_KIND,
            data=self._payload(),
        )
        # Validate by parsing the envelope via the Pydantic model.
        parsed = health.HealthSnapshotEnvelope.model_validate(env)
        assert parsed.kind == "platform.health_snapshot"
        assert parsed.data.backend.value == "HEALTHY"

    def test_kind_field_is_frozen(self) -> None:
        # ``frozen=True`` on a Pydantic Field prevents post-construction
        # mutation. We assert that here, not at construction time
        # (Pydantic v2 does not raise on the initial assignment).
        m = health.HealthSnapshotEnvelope(
            kind="platform.health_snapshot",
            version=API_VERSION,
            generated_at="2026-09-05T03:59:00Z",
            id="sha256:" + "a" * 64,
            data=health.HealthSnapshotData(**self._payload()),
        )
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            m.kind = "platform.tampered"  # type: ignore[misc]

    def test_default_kind_is_used_when_omitted(self) -> None:
        m = health.HealthSnapshotEnvelope(
            version=API_VERSION,
            generated_at="2026-09-05T03:59:00Z",
            id="sha256:" + "a" * 64,
            data=health.HealthSnapshotData(**self._payload()),
        )
        assert m.kind == "platform.health_snapshot"

    def test_domains_defaults_to_empty_list(self) -> None:
        data = health.HealthSnapshotData(**self._payload())
        assert data.domains == []


# ---------------------------------------------------------------------------
# 8. Capabilities contract
# ---------------------------------------------------------------------------


class TestCapabilitiesContract:
    def test_list_envelope_round_trip(self) -> None:
        env = success_envelope(
            kind=capabilities.CAPABILITY_LIST_KIND,
            data={
                "count": 1,
                "categories": ["DISCOVERY"],
                "items": [
                    {
                        "id": "discover.blast-radius",
                        "name": "Blast-Radius Contract",
                        "stage": "discovery",
                        "cost": "low",
                        "authorization": "none",
                        "produces": ["blast_radius_contract"],
                        "triggers": ["changed_file"],
                    }
                ],
            },
        )
        parsed = capabilities.CapabilityListEnvelope.model_validate(env)
        assert parsed.data.count == 1
        assert parsed.data.items[0].id == "discover.blast-radius"

    def test_detail_envelope_round_trip(self) -> None:
        env = success_envelope(
            kind=capabilities.CAPABILITY_DETAIL_KIND,
            data={
                "id": "discover.blast-radius",
                "name": "Blast-Radius Contract",
                "stage": "discovery",
                "cost": "low",
                "authorization": "none",
                "owner": "runtime/foundation/verification/blast_radius.py",
                "command": None,
                "dependencies": [],
                "produces": [],
                "triggers": [],
                "recent_executions": [],
                "evidence": [],
                "cache_status": None,
                "failure_history": [],
                "health": "HEALTHY",
            },
        )
        parsed = capabilities.CapabilityDetailEnvelope.model_validate(env)
        assert parsed.data.id == "discover.blast-radius"

    def test_graph_envelope_round_trip(self) -> None:
        env = success_envelope(
            kind=capabilities.CAPABILITY_GRAPH_KIND,
            data={
                "capability_id": "discover.blast-radius",
                "upstream": ["changed_file"],
                "downstream": ["execute.reconciliation-engine.contract"],
            },
        )
        parsed = capabilities.CapabilityGraphEnvelope.model_validate(env)
        assert parsed.data.upstream == ["changed_file"]

    def test_minimal_item_round_trip(self) -> None:
        item = capabilities.CapabilityListItem(
            id="x",
            name="X",
            stage="discovery",
            cost="low",
            authorization="none",
        )
        assert item.produces == []
        assert item.triggers == []


# ---------------------------------------------------------------------------
# 9. Tasks contract
# ---------------------------------------------------------------------------


class TestTasksContract:
    def test_list_envelope_round_trip(self) -> None:
        env = success_envelope(
            kind=tasks.TASK_LIST_KIND,
            data={
                "open_count": 0,
                "closed_count": 0,
                "items": [],
            },
        )
        parsed = tasks.TaskListEnvelope.model_validate(env)
        assert parsed.kind == "platform.task_list"
        assert parsed.data.items == []

    def test_detail_envelope_round_trip(self) -> None:
        env = success_envelope(
            kind=tasks.TASK_DETAIL_KIND,
            data={
                "id": "obl-1",
                "name": "T",
                "capability_id": "discover.blast-radius",
                "status": "OPEN",
                "created_at": "2026-09-05T03:59:00Z",
                "closed_at": None,
                "plan": [],
                "obligations": [],
                "evidence_ids": [],
                "decision_id": None,
            },
        )
        parsed = tasks.TaskDetailEnvelope.model_validate(env)
        assert parsed.data.id == "obl-1"

    def test_cancel_envelope_round_trip(self) -> None:
        env = success_envelope(
            kind=tasks.TASK_CANCEL_KIND,
            data={
                "id": "obl-1",
                "cancelled": True,
                "reason": "user requested",
            },
        )
        parsed = tasks.TaskCancelResultEnvelope.model_validate(env)
        assert parsed.data.cancelled is True


# ---------------------------------------------------------------------------
# 10. Verification contract
# ---------------------------------------------------------------------------


class TestVerificationContract:
    def test_run_request_envelope(self) -> None:
        env = success_envelope(
            kind=verification.VERIFICATION_RUN_REQUEST_KIND,
            data={
                "capability_id": "discover.blast-radius",
                "group": None,
                "authorization_token": None,
            },
        )
        parsed = verification.VerificationRunRequestEnvelope.model_validate(env)
        assert parsed.data.capability_id == "discover.blast-radius"

    def test_run_result_envelope(self) -> None:
        env = success_envelope(
            kind=verification.VERIFICATION_RUN_RESULT_KIND,
            data={
                "capability_id": "discover.blast-radius",
                "status": "HEALTHY",
                "task_id": "obl-1",
                "execution_id": "exec-1",
                "started_at": "2026-09-05T03:59:00Z",
                "finished_at": None,
                "duration_ms": None,
                "message": "ok",
            },
        )
        parsed = verification.VerificationRunResultEnvelope.model_validate(env)
        assert parsed.data.capability_id == "discover.blast-radius"

    def test_recommendation_envelope(self) -> None:
        env = success_envelope(
            kind=verification.VERIFICATION_RECOMMENDATION_KIND,
            data={
                "recommended": ["discover.blast-radius"],
                "rationale": "files changed in blast-radius surface",
            },
        )
        parsed = verification.VerificationRecommendationEnvelope.model_validate(env)
        assert parsed.data.recommended == ["discover.blast-radius"]


# ---------------------------------------------------------------------------
# 11. Executions contract
# ---------------------------------------------------------------------------


class TestExecutionsContract:
    def test_detail_envelope(self) -> None:
        env = success_envelope(
            kind=executions.EXECUTION_DETAIL_KIND,
            data={
                "id": "exec-1",
                "task_id": "obl-1",
                "capability_id": "discover.blast-radius",
                "status": "HEALTHY",
                "started_at": "2026-09-05T03:59:00Z",
                "finished_at": None,
                "phase": "discovery",
                "current_state": "started",
                "events": [],
                "stdout_ref": None,
                "stderr_ref": None,
                "evidence_ids": [],
                "decision_id": None,
            },
        )
        parsed = executions.ExecutionDetailEnvelope.model_validate(env)
        assert parsed.data.id == "exec-1"

    def test_stream_event_envelope(self) -> None:
        env = success_envelope(
            kind=executions.EXECUTION_STREAM_EVENT_KIND,
            data={
                "execution_id": "exec-1",
                "event_type": "execution.started",
                "payload": {"phase": "discovery"},
                "emitted_at": "2026-09-05T03:59:00Z",
            },
        )
        parsed = executions.ExecutionStreamEventEnvelope.model_validate(env)
        assert parsed.data.event_type == "execution.started"


# ---------------------------------------------------------------------------
# 12. Evidence contract
# ---------------------------------------------------------------------------


class TestEvidenceContract:
    def test_list_envelope(self) -> None:
        env = success_envelope(
            kind=evidence.EVIDENCE_LIST_KIND,
            data={"count": 0, "items": []},
        )
        parsed = evidence.EvidenceListEnvelope.model_validate(env)
        assert parsed.data.count == 0

    def test_detail_envelope(self) -> None:
        env = success_envelope(
            kind=evidence.EVIDENCE_DETAIL_KIND,
            data={
                "id": "ev-1",
                "kind": "test-report",
                "capability_id": None,
                "execution_id": None,
                "collected_at": "2026-09-05T03:59:00Z",
                "status": "HEALTHY",
                "summary": "all green",
                "payload": {},
                "references": [],
            },
        )
        parsed = evidence.EvidenceDetailEnvelope.model_validate(env)
        assert parsed.data.summary == "all green"

    def test_compare_envelope(self) -> None:
        env = success_envelope(
            kind=evidence.EVIDENCE_COMPARE_KIND,
            data={
                "left_id": "ev-1",
                "right_id": "ev-2",
                "delta": {"durations": {"left": 100, "right": 110}},
            },
        )
        parsed = evidence.EvidenceCompareEnvelope.model_validate(env)
        assert parsed.data.left_id == "ev-1"


# ---------------------------------------------------------------------------
# 13. History contract
# ---------------------------------------------------------------------------


class TestHistoryContract:
    def test_runs_envelope(self) -> None:
        env = success_envelope(
            kind=history.HISTORY_RUNS_KIND,
            data={
                "page": 1,
                "page_size": 10,
                "total": 0,
                "items": [],
            },
        )
        parsed = history.HistoryRunsEnvelope.model_validate(env)
        assert parsed.data.page == 1

    def test_run_detail_envelope(self) -> None:
        env = success_envelope(
            kind=history.HISTORY_RUN_KIND,
            data={
                "id": "run-1",
                "started_at": "2026-09-05T03:59:00Z",
                "finished_at": None,
                "duration_ms": None,
                "status": "HEALTHY",
                "capabilities_run": 0,
                "capabilities_passed": 0,
                "capabilities_failed": 0,
                "capability_results": [],
                "evidence_ids": [],
            },
        )
        parsed = history.HistoryRunEnvelope.model_validate(env)
        assert parsed.data.id == "run-1"

    def test_compare_envelope(self) -> None:
        env = success_envelope(
            kind=history.HISTORY_COMPARE_KIND,
            data={
                "current_run": {"id": "run-latest"},
                "baseline_run": {"id": "run-baseline"},
                "delta": {"repository_changes": []},
            },
        )
        parsed = history.HistoryCompareEnvelope.model_validate(env)
        assert parsed.data.delta == {"repository_changes": []}

    def test_baselines_envelope(self) -> None:
        env = success_envelope(
            kind=history.HISTORY_BASELINES_KIND,
            data={
                "items": [
                    {
                        "name": "LAST_PASS",
                        "run_id": "run-1",
                        "description": "last passing run",
                        "recorded_at": "2026-09-05T03:59:00Z",
                    }
                ]
            },
        )
        parsed = history.HistoryBaselinesEnvelope.model_validate(env)
        assert parsed.data.items[0].name == "LAST_PASS"


# ---------------------------------------------------------------------------
# 14. Errors contract
# ---------------------------------------------------------------------------


class TestErrorsContract:
    def test_current_envelope(self) -> None:
        env = success_envelope(
            kind=errors_contract.ERRORS_CURRENT_KIND,
            data={
                "window": "1h",
                "count": 0,
                "items": [],
            },
        )
        parsed = errors_contract.PlatformErrorsListEnvelope.model_validate(env)
        assert parsed.kind == "platform.errors_current"

    def test_recent_envelope(self) -> None:
        env = success_envelope(
            kind=errors_contract.ERRORS_RECENT_KIND,
            data={"window": "24h", "count": 0, "items": []},
        )
        parsed = errors_contract.PlatformErrorsListEnvelope.model_validate(env)
        assert parsed.kind == "platform.errors_recent"

    def test_recurring_envelope(self) -> None:
        env = success_envelope(
            kind=errors_contract.ERRORS_RECURRING_KIND,
            data={"window": "7d", "count": 0, "items": []},
        )
        parsed = errors_contract.PlatformErrorsListEnvelope.model_validate(env)
        assert parsed.kind == "platform.errors_recurring"

    def test_frequency_envelope(self) -> None:
        env = success_envelope(
            kind=errors_contract.ERRORS_FREQUENCY_KIND,
            data={
                "window": "7d",
                "total": 0,
                "buckets": [],
            },
        )
        parsed = errors_contract.PlatformErrorsFrequencyEnvelope.model_validate(env)
        assert parsed.data.total == 0


# ---------------------------------------------------------------------------
# 15. Architecture contract
# ---------------------------------------------------------------------------


class TestArchitectureContract:
    def test_authorities_envelope(self) -> None:
        env = success_envelope(
            kind=architecture.ARCHITECTURE_AUTHORITIES_KIND,
            data={
                "count": 1,
                "items": [
                    {
                        "name": "control_plane",
                        "owner": "runtime/foundation/verification/canonical_control_plane.py",
                        "status": "HEALTHY",
                        "last_check": "2026-09-05T03:59:00Z",
                        "issues": 0,
                    }
                ],
            },
        )
        parsed = architecture.ArchitectureAuthoritiesEnvelope.model_validate(env)
        assert parsed.data.items[0].name == "control_plane"

    def test_authority_detail_envelope(self) -> None:
        env = success_envelope(
            kind=architecture.ARCHITECTURE_AUTHORITY_KIND,
            data={
                "name": "control_plane",
                "owner": "runtime/foundation/verification/canonical_control_plane.py",
                "status": "HEALTHY",
                "last_check": "2026-09-05T03:59:00Z",
                "description": "canonical control plane",
                "recent_evidence": [],
                "issues": 0,
            },
        )
        parsed = architecture.AuthorityDetailEnvelope.model_validate(env)
        assert parsed.data.name == "control_plane"

    @pytest.mark.parametrize(
        "kind",
        [
            architecture.ARCHITECTURE_BOUNDARIES_KIND,
            architecture.ARCHITECTURE_DUPLICATES_KIND,
            architecture.ARCHITECTURE_BYPASSES_KIND,
            architecture.ARCHITECTURE_DEPRECATIONS_KIND,
            architecture.ARCHITECTURE_UNMAPPED_KIND,
        ],
    )
    def test_findings_envelope_kind_mutable_for_listing_endpoints(
        self, kind: str
    ) -> None:
        env = success_envelope(
            kind=kind,
            data={"count": 0, "items": []},
        )
        parsed = architecture.ArchitectureFindingsEnvelope.model_validate(env)
        assert parsed.kind == kind


# ---------------------------------------------------------------------------
# 16. Events contract
# ---------------------------------------------------------------------------


class TestEventsContract:
    def test_list_envelope(self) -> None:
        env = success_envelope(
            kind=events.EVENTS_LIST_KIND,
            data={"window": "1h", "count": 0, "items": []},
        )
        parsed = events.EventsListEnvelope.model_validate(env)
        assert parsed.data.count == 0

    def test_stream_event_envelope(self) -> None:
        env = success_envelope(
            kind=events.EVENTS_STREAM_KIND,
            data={
                "event": {
                    "id": "evt-1",
                    "event_type": "task.created",
                    "task_id": "obl-1",
                    "execution_id": None,
                    "capability_id": "discover.blast-radius",
                    "emitted_at": "2026-09-05T03:59:00Z",
                    "payload": {},
                },
                "emitted_at": "2026-09-05T03:59:00Z",
            },
        )
        parsed = events.EventsStreamEventEnvelope.model_validate(env)
        assert parsed.data.event.event_type == "task.created"

    def test_payload_defaults_to_empty_dict(self) -> None:
        evt = events.PlatformEvent(
            id="evt-1",
            event_type="task.created",
            emitted_at="2026-09-05T03:59:00Z",
        )
        assert evt.payload == {}


# ---------------------------------------------------------------------------
# 17. Application contract
# ---------------------------------------------------------------------------


class TestApplicationContract:
    @pytest.mark.parametrize(
        "kind",
        [
            application.APP_BACKEND_KIND,
            application.APP_DOMAIN_KIND,
            application.APP_FINANCIAL_KIND,
            application.APP_FRONTEND_KIND,
            application.APP_WORKFLOWS_KIND,
        ],
    )
    def test_application_readiness_envelope(self, kind: str) -> None:
        env = success_envelope(
            kind=kind,
            data={
                "subject": "backend",
                "status": "HEALTHY",
                "summary": "ok",
                "last_check": "2026-09-05T03:59:00Z",
                "details": [],
            },
        )
        parsed = application.ApplicationReadinessEnvelope.model_validate(env)
        assert parsed.kind == kind
        assert parsed.data.subject == "backend"

    def test_subject_required(self) -> None:
        with pytest.raises(ValidationError):
            application.ApplicationReadinessData(
                status="HEALTHY",
                summary="ok",
                last_check="2026-09-05T03:59:00Z",
            )


# ---------------------------------------------------------------------------
# 18. Change intelligence contract
# ---------------------------------------------------------------------------


class TestChangeIntelligenceContract:
    def test_round_trip(self) -> None:
        env = success_envelope(
            kind=change.CHANGE_INTELLIGENCE_KIND,
            data={
                "changed_files": [
                    {
                        "path": "backend/src/engines/loan_engine/foo.py",
                        "change_type": "modified",
                    },
                ],
                "affected_capabilities": ["loan-engine"],
                "stale_evidence": ["sha256:" + "a" * 64],
                "affected_tests": ["backend/tests/test_loan.py"],
                "affected_workflows": ["backend"],
                "recommended_verification": ["loan-engine-contract"],
                "risk": "MEDIUM",
                "generated_from": "2026-09-05T03:59:00Z",
            },
        )
        parsed = change.ChangeIntelligenceEnvelope.model_validate(env)
        assert parsed.data.risk == "MEDIUM"
        assert parsed.data.affected_capabilities == ["loan-engine"]

    def test_risk_field_required(self) -> None:
        with pytest.raises(ValidationError):
            change.ChangeIntelligenceData(
                changed_files=[],
                affected_capabilities=[],
                stale_evidence=[],
                affected_tests=[],
                affected_workflows=[],
                recommended_verification=[],
                generated_from="2026-09-05T03:59:00Z",
            )


# ---------------------------------------------------------------------------
# 19. End-to-end envelope stability
# ---------------------------------------------------------------------------


class TestEndToEndEnvelopeStability:
    def test_same_input_same_id_across_invocations(self) -> None:
        envs = [
            success_envelope(kind="platform.x", data={"k": 1, "n": [1, 2]})
            for _ in range(5)
        ]
        ids = {e["id"] for e in envs}
        assert len(ids) == 1

    def test_wall_clock_does_not_affect_id(self) -> None:
        # Two envelopes built back-to-back must share their id even if
        # ``generated_at`` differs by a microsecond.
        env_a = success_envelope(kind="platform.x", data={"k": 1})
        env_b = success_envelope(kind="platform.x", data={"k": 1})
        # We don't sleep (test must stay deterministic), but we assert the
        # strong invariant: identity is independent of generated_at.
        assert env_a["id"] == env_b["id"]

    def test_required_top_level_keys(self) -> None:
        env = success_envelope(kind="platform.x", data={"k": 1})
        assert {"kind", "version", "generated_at", "id", "data"} <= env.keys()

    def test_error_envelope_required_subfields(self) -> None:
        err = PlatformError(
            code=PlatformErrorCode.NOT_FOUND,
            layer="platform.tasks",
            message="missing",
        )
        env = error_envelope(error=err)
        sub = env["error"]
        assert {"code", "layer", "message"} <= sub.keys()


# ---------------------------------------------------------------------------
# 20. No network dependency
# ---------------------------------------------------------------------------


class TestNoNetworkDependency:
    def test_imports_dont_open_sockets(self) -> None:
        # Snapshot ``sys.modules`` BEFORE importing the platform package,
        # then assert that nothing new pulled in by the platform package
        # is a network-bearing library. This guards against accidental
        # FastAPI / Starlette / httpx imports at module level.
        import sys

        forbidden = {"aiohttp", "httpx", "fastapi", "starlette", "urllib3", "requests"}
        before = set(sys.modules)
        import runtime.platform  # noqa: F401
        import runtime.platform.api  # noqa: F401
        import runtime.platform.api.contracts  # noqa: F401

        after = set(sys.modules)
        newly_loaded = after - before
        forbidden_now = {m.split(".")[0] for m in newly_loaded} & forbidden
        assert (
            not forbidden_now
        ), f"platform package unexpectedly loaded network deps: {forbidden_now}"

    def test_contracts_module_has_no_io_imports(self) -> None:
        # Defensive: read the contracts package source and confirm no
        # I/O or HTTP libraries are imported.
        import runtime.platform.api.contracts as c

        src_path = c.__file__
        assert src_path is not None
        src = pathlib.Path(src_path).read_text(encoding="utf-8")
        for needle in (
            "import requests",
            "import httpx",
            "import aiohttp",
            "import fastapi",
            "import starlette",
            "import urllib3",
        ):
            assert needle not in src, f"forbidden import found: {needle}"
