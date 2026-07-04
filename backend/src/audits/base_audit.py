"""Base Audit Class

Standard interface for all audit modules.
"""

from abc import ABC, abstractmethod
from core.models import AuditResult

class BaseAudit(ABC):
    """Abstract base class for all audits."""

    @abstractmethod
    def run(self) -> AuditResult:
        """Run the audit and return results."""
        pass