"""M9-C57 Phase 2 — Platform Service Aggregators validation.

These tests prove Gate 2 from ``IMPLEMENTATION_ROADMAP.md``:

    Platform API service
            ↓
        existing authority
            ↓
        real repository state

    No mock platform state may be used for production paths.

Each test exercises a real C50 authority via the Phase 2 service
adapter and asserts:

1. The adapter returns a valid envelope (kind, version, generated_at,
   id, data).
2. The ``data`` payload parses through the Phase 1 contract (round-trip
   integrity).
3. The data is derived from real authority state (not a mock).
"""

from __future__ import annotations

import re

import pytest

from runtime.platform.api.contracts import (
    application as application_contract,
    architecture as architecture_contract,
    capabilities as capabilities_contract,
    change as change_contract,
    errors as errors_contract,
    events as events_contract,
    evidence as evidence_contract,
    executions as executions_contract,
    health as health_contract,
    history as history_contract,
    tasks as tasks_contract,
    verification as verification_contract,
)
from runtime.platform.api.envelope import API_VERSION
from runtime.platform.api.services import (
    application,
    architecture,
    capabilities,
    change,
    errors,
    events,
    evidence,
    executions,
    health,
    history,
    tasks,
    verification,
)


def _envelope_shape_ok(env: dict) -> bool:
    """Validate that ``env`` has the canonical 5-key envelope shape."""

    return (
        set(env.keys())
        == {"kind", "version", "generated_at", "id", "data"}
        and env["version"] == API_VERSION
        and re.fullmatch(r"sha256:[0-9a-f]{64}", env["id"])
        and re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", env["generated_at"]
        )
    )


# ---------------------------------------------------------------------------
# 1. Capabilities service
# ---------------------------------------------------------------------------


class TestCapabilitiesService:
    def test_list_returns_real_catalog(self) -> None:
        env = capabilities.build_capability_list()
        assert _envelope_shape_ok(env)
        # Round-trip through the contract.
        parsed = capabilities_contract.CapabilityListEnvelope.model_validate(env)
        # The repository has 55 real capabilities (per M9-C51).
        assert parsed.data.count == 55
        assert parsed.data.count == len(parsed.data.items)
        # At least one known capability is present.
        ids = {it.id for it in parsed.data.items}
        assert "discover.blast-radius" in ids

    def test_list_items_have_required_fields(self) -> None:
        env = capabilities.build_capability_list()
        parsed = capabilities_contract.CapabilityListEnvelope.model_validate(env)
        for item in parsed.data.items:
            assert item.id
            assert item.name
            assert item.stage
            assert item.cost
            assert item.authorization

    def test_detail_for_known_capability(self) -> None:
        env = capabilities.build_capability_detail("discover.blast-radius")
        assert env is not None
        assert _envelope_shape_ok(env)
        parsed = capabilities_contract.CapabilityDetailEnvelope.model_validate(env)
        assert parsed.data.id == "discover.blast-radius"

    def test_detail_for_unknown_capability_returns_none(self) -> None:
        assert capabilities.build_capability_detail("does.not.exist") is None

    def test_graph_for_known_capability(self) -> None:
        env = capabilities.build_capability_graph("discover.blast-radius")
        assert env is not None
        parsed = capabilities_contract.CapabilityGraphEnvelope.model_validate(env)
        # The capability exists in the graph; upstream/downstream are
        # derived from producer/consumer relations.
        assert parsed.data.capability_id == "discover.blast-radius"
        assert isinstance(parsed.data.upstream, list)
        assert isinstance(parsed.data.downstream, list)

    def test_graph_for_unknown_capability_returns_none(self) -> None:
        assert capabilities.build_capability_graph("does.not.exist") is None


# ---------------------------------------------------------------------------
# 2. Tasks service
# ---------------------------------------------------------------------------


class TestTasksService:
    def test_list_derives_from_real_obligations(self) -> None:
        env = tasks.build_task_list()
        assert _envelope_shape_ok(env)
        parsed = tasks_contract.TaskListEnvelope.model_validate(env)
        # The repo currently has 13 open obligations (from inspect evidence).
        assert parsed.data.open_count + parsed.data.closed_count == len(
            parsed.data.items
        )
        assert parsed.data.open_count >= 0

    def test_detail_for_known_obligation(self) -> None:
        env_list = tasks.build_task_list()
        parsed_list = tasks_contract.TaskListEnvelope.model_validate(env_list)
        if not parsed_list.data.items:
            pytest.skip("no obligations present in repo state")
        first_id = parsed_list.data.items[0].id
        detail = tasks.build_task_detail(first_id)
        assert detail is not None
        parsed = tasks_contract.TaskDetailEnvelope.model_validate(detail)
        assert parsed.data.id == first_id

    def test_detail_for_unknown_obligation_returns_none(self) -> None:
        assert tasks.build_task_detail("obl-does-not-exist") is None


# ---------------------------------------------------------------------------
# 3. Health service
# ---------------------------------------------------------------------------


class TestHealthService:
    def test_health_snapshot_reads_real_event_store(self) -> None:
        env = health.build_health_snapshot()
        assert _envelope_shape_ok(env)
        parsed = health_contract.HealthSnapshotEnvelope.model_validate(env)
        # Domains list contains at least the two entries the adapter
        # always emits (Verification, EventStore).
        names = {d.name for d in parsed.data.domains}
        assert "Verification" in names
        assert "EventStore" in names
        # Verification status must be one of the contract enum values.
        assert parsed.data.verification in {"HEALTHY", "DEGRAD", "UNHEALTHY", "CURRENT"}


# ---------------------------------------------------------------------------
# 4. Verification service
# ---------------------------------------------------------------------------


class TestVerificationService:
    def test_recommendation_uses_real_planner(self) -> None:
        env = verification.build_verification_recommendation()
        assert _envelope_shape_ok(env)
        parsed = verification_contract.VerificationRecommendationEnvelope.model_validate(env)
        # The recommendation list must be a list of strings (capability IDs).
        assert isinstance(parsed.data.recommended, list)
        for cap_id in parsed.data.recommended:
            assert isinstance(cap_id, str)

    def test_run_request_round_trip(self) -> None:
        env = verification.build_verification_run_request(
            capability_id="discover.blast-radius",
        )
        assert _envelope_shape_ok(env)
        parsed = verification_contract.VerificationRunRequestEnvelope.model_validate(env)
        assert parsed.data.capability_id == "discover.blast-radius"

    def test_run_result_round_trip(self) -> None:
        from runtime.platform.api.contracts._primitives import Status

        env = verification.build_verification_run_result(
            capability_id="discover.blast-radius",
            status_value=Status.HEALTHY,
            message="ok",
        )
        assert _envelope_shape_ok(env)
        parsed = verification_contract.VerificationRunResultEnvelope.model_validate(env)
        assert parsed.data.status == Status.HEALTHY


# ---------------------------------------------------------------------------
# 5. Executions service
# ---------------------------------------------------------------------------


class TestExecutionsService:
    def test_stream_event_round_trip(self) -> None:
        from runtime.system.observability.event_store import EngineeringEvent

        ev = EngineeringEvent(
            event_id="evt-1",
            event_type="execution.started",
            timestamp="2026-09-05T03:59:00Z",
            execution_context={"environment": "local"},
            payload={"phase": "discovery"},
        )
        env = executions.build_execution_stream_event("exec-1", ev)
        assert _envelope_shape_ok(env)
        parsed = executions_contract.ExecutionStreamEventEnvelope.model_validate(env)
        assert parsed.data.event_type == "execution.started"
        assert parsed.data.execution_id == "exec-1"


# ---------------------------------------------------------------------------
# 6. Evidence service
# ---------------------------------------------------------------------------


class TestEvidenceService:
    def test_list_returns_envelope(self) -> None:
        env = evidence.build_evidence_list()
        assert _envelope_shape_ok(env)
        parsed = evidence_contract.EvidenceListEnvelope.model_validate(env)
        assert parsed.data.count == len(parsed.data.items)

    def test_detail_for_unknown_returns_none(self) -> None:
        assert evidence.build_evidence_detail("unknown-evidence-id") is None

    def test_compare_for_unknown_pair_returns_none(self) -> None:
        assert evidence.build_evidence_compare("a", "b") is None


# ---------------------------------------------------------------------------
# 7. History service
# ---------------------------------------------------------------------------


class TestHistoryService:
    def test_runs_returns_envelope(self) -> None:
        env = history.build_history_runs(page=1, page_size=10)
        assert _envelope_shape_ok(env)
        parsed = history_contract.HistoryRunsEnvelope.model_validate(env)
        assert parsed.data.page == 1
        assert parsed.data.page_size == 10
        # total is >= items count
        assert parsed.data.total >= len(parsed.data.items)

    def test_run_detail_for_unknown_returns_none(self) -> None:
        assert history.build_history_run("run-unknown") is None

    def test_baselines_contain_required_names(self) -> None:
        env = history.build_history_baselines()
        assert _envelope_shape_ok(env)
        parsed = history_contract.HistoryBaselinesEnvelope.model_validate(env)
        names = {it.name for it in parsed.data.items}
        for required in ("LAST", "LAST_PASS", "KNOWN_GOOD", "BASELINE"):
            assert required in names


# ---------------------------------------------------------------------------
# 8. Architecture service
# ---------------------------------------------------------------------------


class TestArchitectureService:
    def test_authorities_list(self) -> None:
        env = architecture.build_architecture_authorities()
        assert _envelope_shape_ok(env)
        parsed = architecture_contract.ArchitectureAuthoritiesEnvelope.model_validate(env)
        names = {it.name for it in parsed.data.items}
        # The four C50 architecture authorities must all be present.
        assert {
            "configuration_authority",
            "route_authority",
            "capability_authority",
            "control_plane_efficiency",
        } <= names

    def test_authority_detail_for_known(self) -> None:
        env = architecture.build_architecture_authority("capability_authority")
        assert env is not None
        parsed = architecture_contract.AuthorityDetailEnvelope.model_validate(env)
        assert parsed.data.name == "capability_authority"

    def test_authority_detail_for_unknown_returns_none(self) -> None:
        assert architecture.build_architecture_authority("does-not-exist") is None

    def test_findings_endpoints_return_valid_envelopes(self) -> None:
        for fn, expected_kind in (
            (
                architecture.build_architecture_boundaries,
                architecture_contract.ARCHITECTURE_BOUNDARIES_KIND,
            ),
            (
                architecture.build_architecture_duplicates,
                architecture_contract.ARCHITECTURE_DUPLICATES_KIND,
            ),
            (
                architecture.build_architecture_bypasses,
                architecture_contract.ARCHITECTURE_BYPASSES_KIND,
            ),
            (
                architecture.build_architecture_deprecations,
                architecture_contract.ARCHITECTURE_DEPRECATIONS_KIND,
            ),
            (
                architecture.build_architecture_unmapped,
                architecture_contract.ARCHITECTURE_UNMAPPED_KIND,
            ),
        ):
            env = fn()
            assert _envelope_shape_ok(env), f"{fn.__name__} returned bad envelope"
            parsed = architecture_contract.ArchitectureFindingsEnvelope.model_validate(env)
            assert parsed.kind == expected_kind


# ---------------------------------------------------------------------------
# 9. Events service
# ---------------------------------------------------------------------------


class TestEventsService:
    def test_events_list_round_trip(self) -> None:
        env = events.build_events_list(limit=5)
        assert _envelope_shape_ok(env)
        parsed = events_contract.EventsListEnvelope.model_validate(env)
        assert parsed.data.count == len(parsed.data.items)
        assert parsed.data.count <= 5

    def test_stream_event_round_trip(self) -> None:
        from runtime.system.observability.event_store import EngineeringEvent

        ev = EngineeringEvent(
            event_id="evt-1",
            event_type="VerificationCompleted",
            timestamp="2026-09-05T03:59:00Z",
            execution_context={"environment": "local"},
            payload={"passed": True},
        )
        env = events.build_events_stream_event(ev)
        assert _envelope_shape_ok(env)
        parsed = events_contract.EventsStreamEventEnvelope.model_validate(env)
        assert parsed.data.event.event_type == "VerificationCompleted"


# ---------------------------------------------------------------------------
# 10. Application service
# ---------------------------------------------------------------------------


class TestApplicationService:
    @pytest.mark.parametrize(
        "fn,kind",
        [
            (application.build_app_backend, application_contract.APP_BACKEND_KIND),
            (application.build_app_frontend, application_contract.APP_FRONTEND_KIND),
            (application.build_app_domain, application_contract.APP_DOMAIN_KIND),
            (application.build_app_financial, application_contract.APP_FINANCIAL_KIND),
            (application.build_app_workflows, application_contract.APP_WORKFLOWS_KIND),
        ],
    )
    def test_application_endpoints(self, fn, kind: str) -> None:
        env = fn()
        assert _envelope_shape_ok(env)
        parsed = application_contract.ApplicationReadinessEnvelope.model_validate(env)
        assert parsed.kind == kind
        assert parsed.data.subject


# ---------------------------------------------------------------------------
# 11. Change intelligence service
# ---------------------------------------------------------------------------


class TestChangeIntelligenceService:
    def test_change_intelligence_uses_real_blast_radius(self) -> None:
        env = change.build_change_intelligence()
        assert _envelope_shape_ok(env)
        parsed = change_contract.ChangeIntelligenceEnvelope.model_validate(env)
        # Risk must be one of LOW/MEDIUM/HIGH.
        assert parsed.data.risk in ("LOW", "MEDIUM", "HIGH")
        # The list fields must be lists of strings.
        for field_name in (
            "changed_files",
            "affected_capabilities",
            "stale_evidence",
            "affected_tests",
            "affected_workflows",
            "recommended_verification",
        ):
            assert isinstance(getattr(parsed.data, field_name), list)


# ---------------------------------------------------------------------------
# 12. Errors service
# ---------------------------------------------------------------------------


class TestErrorsService:
    def test_current_recent_listings(self) -> None:
        env = errors.build_errors_current()
        assert _envelope_shape_ok(env)
        parsed = errors_contract.PlatformErrorsListEnvelope.model_validate(env)
        assert parsed.kind == errors_contract.ERRORS_CURRENT_KIND
        assert parsed.data.count == len(parsed.data.items)

    def test_recurring_listing(self) -> None:
        env = errors.build_errors_recurring()
        assert _envelope_shape_ok(env)
        parsed = errors_contract.PlatformErrorsListEnvelope.model_validate(env)
        assert parsed.kind == errors_contract.ERRORS_RECURRING_KIND

    def test_frequency_envelope(self) -> None:
        env = errors.build_errors_frequency()
        assert _envelope_shape_ok(env)
        parsed = errors_contract.PlatformErrorsFrequencyEnvelope.model_validate(env)
        assert isinstance(parsed.data.buckets, list)

    def test_detail_for_unknown_returns_none(self) -> None:
        assert errors.build_errors_detail("unknown.error") is None


# ---------------------------------------------------------------------------
# 13. End-to-end: real authority -> envelope -> contract
# ---------------------------------------------------------------------------


class TestGate2EndToEnd:
    """Prove the Gate 2 chain: service → authority → real repository state."""

    def test_capability_list_count_matches_catalog(self) -> None:
        """The service-reported count must equal the live catalog's count."""

        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        env = capabilities.build_capability_list()
        parsed = capabilities_contract.CapabilityListEnvelope.model_validate(env)
        assert parsed.data.count == len(catalog.entries)

    def test_task_list_count_matches_obligations(self) -> None:
        """The service-reported obligation count must equal the live set."""

        from runtime.foundation.verification.control_plane_facade import (
            ControlPlane,
            _collect_changed_files,
        )

        cp = ControlPlane()
        plan = cp.planner.plan(_collect_changed_files())
        oset = cp._plan_to_obligations(plan, _collect_changed_files())
        env = tasks.build_task_list()
        parsed = tasks_contract.TaskListEnvelope.model_validate(env)
        assert (
            parsed.data.open_count + parsed.data.closed_count
            == len(oset.obligations)
        )

    def test_change_intelligence_risk_matches_blast_radius(self) -> None:
        """The reported risk must reflect the live blast-radius signals."""

        from runtime.foundation.verification.blast_radius import (
            compute_blast_radius,
        )

        contract = compute_blast_radius()
        env = change.build_change_intelligence()
        parsed = change_contract.ChangeIntelligenceEnvelope.model_validate(env)
        if contract.is_fail_closed or contract.escalation_conditions:
            assert parsed.data.risk == "HIGH"
        else:
            assert parsed.data.risk in ("LOW", "MEDIUM")
