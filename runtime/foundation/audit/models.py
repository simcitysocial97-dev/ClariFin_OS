"""Audit Models — Program 12.

Immutable dataclasses for the Engineering Platform Certification Audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AuditSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AuditStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


class AuditPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class AuditFinding:
    section: str
    check_id: str
    name: str
    status: AuditStatus
    severity: AuditSeverity
    priority: AuditPriority
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""


@dataclass(frozen=True, slots=True)
class AuditSectionResult:
    section: str
    name: str
    status: AuditStatus
    findings: tuple[AuditFinding, ...] = field(default_factory=tuple)
    duration_seconds: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AuditReport:
    generated_at: str
    overall_status: AuditStatus
    sections: tuple[AuditSectionResult, ...]
    critical_issues: tuple[AuditFinding, ...]
    high_priority_issues: tuple[AuditFinding, ...]
    medium_priority_issues: tuple[AuditFinding, ...]
    low_priority_issues: tuple[AuditFinding, ...]
    total_duration_seconds: float
    certification_status: str
    certification_details: dict[str, AuditStatus]
