"""Migrations package (M03)."""

from src.core.db.migrations._registry import MIGRATIONS, apply_pending_migrations

__all__ = ["MIGRATIONS", "apply_pending_migrations"]
