"""Diagnostic engine — M9-C57 Phase 11.

Deterministic diagnostic reasoning over the ladder:

    L0 — historical evidence (cheapest)
    L1 — metadata / health inspection
    L2 — targeted inspection
    L3 — affected verification
    L4 — broader verification
    L5 — full verification (most expensive)

The engine selects the lowest-cost sufficient action. No LLM.

Failure signatures are content-addressed (SHA-256 over a canonical
description) and linked to error · capability · execution · evidence ·
history · change · recommended verification.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.platform.api.contracts._primitives import Status, Timestamp
from runtime.platform.api.services._helpers import envelope, now_iso

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Signature store (local JSON file)
# ---------------------------------------------------------------------------

_SIGNATURES_PATH = Path("runtime/generated/diagnostic-signatures.json")

_SIGN_KIND = "platform.diagnostic_signature"
_DIAG_KIND = "platform.diagnostic_result"
_REC_KIND = "platform.diagnostic_recommendation"


def _load_signatures() -> dict[str, Any]:
    """Load the local failure-signature store."""
    if not _SIGNATURES_PATH.exists():
        return {"signatures": [], "index": {}}
    try:
        return json.loads(_SIGNATURES_PATH.read_text())
    except Exception as exc:
        logger.warning("Failed to load diagnostic signatures: %s", exc)
        return {"signatures": [], "index": {}}


def _save_signatures(data: dict[str, Any]) -> None:
    _SIGNATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SIGNATURES_PATH.write_text(json.dumps(data, indent=2, default=str))


def _signature_id(description: str) -> str:
    """Content-addressed ID for a failure description."""
    raw = json.dumps({"description": description}, sort_keys=True).encode()
    return f"sig-{hashlib.sha256(raw).hexdigest()[:12]}"


def register_signature(
    *,
    error_code: str,
    description: str,
    affected_capability: str,
    severity: str = "medium",
) -> str:
    """Register (or deduplicate) a failure signature."""
    data = _load_signatures()
    sid = _signature_id(description)
    for sig in data["signatures"]:
        if sig["id"] == sid:
            return sid
    entry = {
        "id": sid,
        "error_code": error_code,
        "description": description,
        "affected_capability": affected_capability,
        "severity": severity,
        "first_seen": now_iso(),
        "last_seen": now_iso(),
        "occurrences": 1,
        "linked_execution": None,
        "linked_evidence": None,
        "linked_change": None,
        "recommended_verification": [],
    }
    data["signatures"].append(entry)
    idx_key = f"{error_code}:{affected_capability}"
    data.setdefault("index", {}).setdefault(idx_key, []).append(sid)
    _save_signatures(data)
    return sid


def bump_signature_occurrence(sid: str) -> None:
    data = _load_signatures()
    for sig in data["signatures"]:
        if sig["id"] == sid:
            sig["occurrences"] = int(sig.get("occurrences", 0) + 1)
            sig["last_seen"] = now_iso()
            break
    _save_signatures(data)


# ---------------------------------------------------------------------------
# Diagnostic engine
# ---------------------------------------------------------------------------


def diagnose(
    *,
    symptom: str,
    error_code: str | None = None,
    capability_id: str | None = None,
) -> dict[str, Any] | None:
    """Run deterministic diagnostic reasoning for a symptom.

    Returns a ``platform.diagnostic_result`` envelope, or ``None`` when
    no rules matched and no recommendation can be produced.
    """
    from runtime.platform.api.services import errors, change

    # ---- L0: search signature store ----
    sig_data = _load_signatures()
    matched_sigs: list[dict[str, Any]] = []
    if error_code and capability_id:
        idx_key = f"{error_code}:{capability_id}"
        for sid in sig_data.get("index", {}).get(idx_key, []):
            for sig in sig_data["signatures"]:
                if sig["id"] == sid:
                    matched_sigs.append(sig)
                    break
    elif error_code:
        for sig in sig_data["signatures"]:
            if sig["error_code"] == error_code:
                matched_sigs.append(sig)
    elif capability_id:
        for sig in sig_data["signatures"]:
            if sig["affected_capability"] == capability_id:
                matched_sigs.append(sig)

    # ---- L1: pull current errors to classify severity ----
    err_env = errors.build_errors_current()
    current_items = err_env["data"]["items"]

    # ---- Determine diagnosis level ----
    if matched_sigs:
        level = "L0"
        fact = "known_failure_signature_matched"
        evidence = [sig["id"] for sig in matched_sigs]
    else:
        # Check if any current error relates to the symptom.
        related = [
            it for it in current_items
            if error_code and it.get("code") == error_code
        ]
        if related:
            level = "L1"
            fact = "error_present_in_current_window"
            evidence = [it["id"] for it in related[:3]]
        else:
            # L2: target change-intelligence to see if any capability is affected.
            ci_env = change.build_change_intelligence()
            caps = ci_env["data"].get("affected_capabilities", [])
            if caps and capability_id:
                level = "L2"
                fact = "capability_in_blast_radius"
                evidence = caps[:5]
            else:
                level = "L1"
                fact = "no_match"
                evidence = []

    # ---- Build recommendation ----
    recommendation: list[dict[str, Any]] = []
    if matched_sigs:
        rec_sig = matched_sigs[0]
        recs = rec_sig.get("recommended_verification", [])
        if recs:
            recommendation = [{"action": "run_verification", "target": recs[0]}]
        else:
            recommendation = [{"action": "inspect_capability", "target": rec_sig["affected_capability"]}]
    elif level == "L2":
        recommendation = [{"action": "run_affected_verification", "target": capability_id}]
    elif level == "L1" and related:
        recommendation = [{"action": "inspect_error", "target": related[0]["id"]}]
    else:
        recommendation = [{"action": "run_full_verification", "target": "all"}]

    data = {
        "symptom": symptom,
        "error_code": error_code,
        "capability_id": capability_id,
        "level": level,
        "fact": fact,
        "evidence": evidence,
        "affected_capability": capability_id or (matched_sigs[0]["affected_capability"] if matched_sigs else None),
        "recommendation": recommendation,
        "generated_at": now_iso(),
    }
    return envelope(kind=_DIAG_KIND, data=data)


def build_diagnostic_recommendation(
    *,
    error_code: str,
    capability_id: str,
    description: str,
    severity: str = "medium",
) -> dict[str, Any] | None:
    """Register a new failure signature and return the resulting recommendation."""
    sid = register_signature(
        error_code=error_code,
        description=description,
        affected_capability=capability_id,
        severity=severity,
    )
    bump_signature_occurrence(sid)
    return {
        "kind": _REC_KIND,
        "signature_id": sid,
        "severity": severity,
        "recommended_verification": ["execute.contract.api"],
    }
