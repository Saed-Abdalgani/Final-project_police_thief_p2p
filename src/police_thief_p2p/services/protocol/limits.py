"""Bounded hostile-JSON parsing for protocol requests."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from police_thief_p2p.services.protocol.envelope import ProtocolEnvelope
from police_thief_p2p.services.protocol.errors import ProtocolErrorCode, ProtocolFailure


@dataclass(frozen=True, slots=True)
class ProtocolLimits:
    """Configurable public request and structure ceilings."""

    max_request_bytes: int = 65_536
    max_json_depth: int = 16
    max_string_length: int = 4_096
    max_collection_items: int = 256
    max_concurrent_requests: int = 2
    reorder_window: int = 8

    def __post_init__(self) -> None:
        """Reject non-positive or nonsensical ceilings."""
        values = (
            self.max_request_bytes,
            self.max_json_depth,
            self.max_string_length,
            self.max_collection_items,
            self.max_concurrent_requests,
            self.reorder_window,
        )
        if any(type(value) is not int or value < 1 for value in values):
            raise ValueError("protocol limits must be positive integers")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key: {key}")
        result[key] = value
    return result


def _bounded(value: Any, limits: ProtocolLimits, depth: int = 0) -> None:
    if depth > limits.max_json_depth:
        raise ValueError("JSON depth limit exceeded")
    if isinstance(value, str) and len(value) > limits.max_string_length:
        raise ValueError("JSON string limit exceeded")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite number")
    if isinstance(value, dict):
        if len(value) > limits.max_collection_items:
            raise ValueError("JSON object item limit exceeded")
        for key, item in value.items():
            _bounded(key, limits, depth + 1)
            _bounded(item, limits, depth + 1)
    elif isinstance(value, list):
        if len(value) > limits.max_collection_items:
            raise ValueError("JSON array item limit exceeded")
        for item in value:
            _bounded(item, limits, depth + 1)


def parse_envelope(document: bytes, limits: ProtocolLimits) -> ProtocolEnvelope:
    """Parse one request with byte, duplicate, depth, and type limits."""
    if len(document) > limits.max_request_bytes:
        raise ProtocolFailure(ProtocolErrorCode.VALIDATION, "request exceeds byte limit")
    try:
        text = document.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite number: {token}")
            ),
        )
        _bounded(value, limits)
        if not isinstance(value, dict):
            raise ValueError("envelope must be an object")
        return ProtocolEnvelope.model_validate(value)
    except (UnicodeDecodeError, ValueError, TypeError, ValidationError) as exc:
        raise ProtocolFailure(
            ProtocolErrorCode.VALIDATION,
            "request is not a valid bounded protocol envelope",
        ) from exc
