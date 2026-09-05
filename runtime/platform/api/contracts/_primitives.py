"""Shared primitives for Platform API contracts.

The Platform API has a small set of cross-cutting primitives that appear
in every domain:

* :class:`Status` — the canonical status enum (``HEALTHY``, ``DEGRAD``,
  ``UNHEALTHY``, ``UNKNOWN``). Used by health, application readiness,
  architecture, and capability health.
* :class:`Timestamp` — ISO-8601 UTC string (``YYYY-MM-DDTHH:MM:SSZ``).
  Pydantic-validated at the boundary.
* :class:`Identity` — opaque content-addressed string (``sha256:<hex>``).

Each primitive is exposed as a Pydantic-validated type so that any
contract field using it gets automatic validation, schema generation, and
JSON serialization. They are exported as concrete classes (rather than
``Annotated[str, ...]``) so that Pydantic v2 picks up the custom
``__get_pydantic_core_schema__`` validator.

These primitives are deliberately tiny — they exist so that the contract
modules do not invent their own status enums or timestamp formats.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

ISO8601_UTC_PATTERN: re.Pattern[str] = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)
SHA256_ID_PATTERN: re.Pattern[str] = re.compile(r"^sha256:[0-9a-f]{64}$")


class Timestamp(str):
    """ISO-8601 UTC timestamp string (``YYYY-MM-DDTHH:MM:SSZ``).

    Implemented as a Pydantic-compatible string subclass so that JSON
    serialization remains a plain string while validation runs at the
    Pydantic boundary.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance),
                return_schema=core_schema.str_schema(),
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _schema: type,
        _handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "pattern": ISO8601_UTC_PATTERN.pattern,
            "description": "ISO-8601 UTC timestamp with Z suffix",
        }

    @staticmethod
    def _validate(value: Any) -> "Timestamp":
        if isinstance(value, Timestamp):
            return value
        if not isinstance(value, str):
            raise TypeError(f"Timestamp must be a string, got {type(value).__name__}")
        if not ISO8601_UTC_PATTERN.match(value):
            raise ValueError(
                "Timestamp must be ISO-8601 UTC with Z suffix "
                f"(e.g. '2026-09-05T03:59:00Z'), got {value!r}"
            )
        return Timestamp(value)


class Identity(str):
    """Content-addressed identity string (``sha256:<64-hex>``)."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance),
                return_schema=core_schema.str_schema(),
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _schema: type,
        _handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "pattern": SHA256_ID_PATTERN.pattern,
            "description": "Content-addressed identity: sha256:<hex>",
        }

    @staticmethod
    def _validate(value: Any) -> "Identity":
        if isinstance(value, Identity):
            return value
        if not isinstance(value, str):
            raise TypeError(f"Identity must be a string, got {type(value).__name__}")
        if not SHA256_ID_PATTERN.match(value):
            raise ValueError(
                f"Identity must match {SHA256_ID_PATTERN.pattern}, got {value!r}"
            )
        return Identity(value)


class Status(str, Enum):
    """Canonical status enum for the Platform API.

    Phase 1 deliberately keeps this enum compact. The values cover:

    * Generic lifecycle states: ``HEALTHY``, ``DEGRAD``, ``UNHEALTHY``,
      ``UNKNOWN``.
    * Domain-specific states taken from ``PLATFORM_API_DESIGN.md`` §5
      concrete examples: ``SAFE`` (architecture), ``CURRENT`` (latest
      verification result), ``VALID`` (evidence), ``READY`` (AI
      runtime), ``OPEN`` (open obligation / task).

    ``UNKNOWN`` is the contract-level "no information yet" state
    (e.g. a capability that has never been run). ``DEGRAD`` is the
    operational "still serving, but with non-critical failures" state.
    """

    HEALTHY = "HEALTHY"
    DEGRAD = "DEGRAD"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"
    SAFE = "SAFE"
    CURRENT = "CURRENT"
    VALID = "VALID"
    READY = "READY"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


__all__ = [
    "Identity",
    "Status",
    "Timestamp",
]
