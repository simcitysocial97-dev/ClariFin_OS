"""Tasks write service — Phase 6.

Implements task cancellation by appending a structured cancellation
event to the ``EngineeringEventStore``. The canonical control plane
will pick up the cancellation on its next iteration (Phase 7 will
wire a proper cancellation path).

For Phase 6, cancellation is a structured record that surfaces in the
GUI and event stream — not a hard kill.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from runtime.foundation.verification.control_plane_facade import (
    ControlPlane,
    _collect_changed_files,
)
from runtime.platform.api.contracts import tasks as tasks_contract
from runtime.platform.api.services._helpers import envelope, now_iso
from runtime.system.observability.event_store import (
    EngineeringEvent,
    EngineeringEventStore,
)

logger = logging.getLogger(__name__)

__all__ = ["build_cancel_result"]


def build_cancel_result(*, task_id: str) -> dict[str, Any] | None:
    """Build a cancellation result envelope.

    Returns ``None`` when the task id is not in the live obligation set.
    Otherwise appends a ``task.cancelled`` event to the event store and
    returns the canonical cancel-result envelope.
    """
    cp = ControlPlane()
    files = _collect_changed_files()
    plan = cp.planner.plan(files)
    oset = cp._plan_to_obligations(plan, files)

    target = None
    for o in oset.obligations:
        if o.obligation_id == task_id:
            target = o
            break

    if target is None:
        return None

    # Mark disposition closed (best-effort — the dataclass is frozen
    # but we can record the cancellation intent in the event store).
    reason = f"cancelled via platform API at {now_iso()}"

    store = EngineeringEventStore()
    store.append(
        EngineeringEvent(
            event_id=f"cancel-{task_id}",
            event_type="task.cancelled",
            timestamp=datetime.now(UTC),
            payload={"task_id": task_id, "reason": reason},
            execution_context={"source": "platform.tasks.cancel"},
            metadata={
                "task_id": task_id,
                "capability_id": (
                    target.capability.capability_id if target.capability else "unknown"
                ),
            },
        )
    )

    data = {
        "id": task_id,
        "cancelled": True,
        "reason": reason,
    }
    return envelope(
        kind=tasks_contract.TASK_CANCEL_KIND,
        data=data,
    )
