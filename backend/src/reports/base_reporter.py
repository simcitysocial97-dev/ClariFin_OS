"""Base Reporter Interface

Standard interface for all report generators.
"""

from abc import ABC, abstractmethod
from src.core.models import AuditResult

class BaseReporter(ABC):
    """Abstract base class for all reporters."""

    @abstractmethod
    def render(self, audit_result: AuditResult) -> str:
        """Render the audit result as a report."""
        pass

    @abstractmethod
    def save_to_file(self, audit_result: AuditResult, filename: str) -> None:
        """Save the rendered report to a file."""
        pass