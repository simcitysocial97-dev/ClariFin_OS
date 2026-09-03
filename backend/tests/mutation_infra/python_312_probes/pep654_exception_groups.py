# backend/tests/mutation_infra/python_312_probes/pep654_exception_groups.py
#
# M9-C45 L-ARCH-001 probe — PEP 654 ExceptionGroup / except* (Python 3.11+).

from __future__ import annotations


def raise_group(errors: list[Exception]) -> None:
    """Raise an ExceptionGroup of the supplied errors."""
    if errors:
        raise ExceptionGroup("aggregate", errors)


def handle_group(group: BaseExceptionGroup) -> int:
    """except* handler — returns the number of ValueErrors caught."""
    count = 0
    try:
        raise group
    except* ValueError as eg:
        count = len(eg.exceptions)
    return count