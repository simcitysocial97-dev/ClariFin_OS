"""Household domain — canonical "no household" sentinel (M04).

This module is the single source of truth for the household sentinel,
replacing the split literals (``'default'`` vs ``'primary'``) that caused
DB-002. All routers, repositories, services, and models must import
:data:`DEFAULT_HOUSEHOLD_ID` / :func:`resolve_household_id` from here
instead of hardcoding a literal.
"""

from __future__ import annotations

DEFAULT_HOUSEHOLD_ID: str = "primary"


def resolve_household_id(raw: str | None) -> str:
    """Resolve a possibly-empty household id to the canonical sentinel.

    Args:
        raw: Caller-supplied household id (may be ``None`` or empty).

    Returns:
        ``raw`` when truthy, otherwise :data:`DEFAULT_HOUSEHOLD_ID`.
    """
    return raw or DEFAULT_HOUSEHOLD_ID
