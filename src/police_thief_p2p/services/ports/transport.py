"""Typed remote transport port."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class TransportRequest:
    """Validated outbound transport request."""

    operation: str
    payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class TransportResponse:
    """Validated inbound transport response."""

    status_code: int
    payload: Mapping[str, object]


@runtime_checkable
class TransportPort(Protocol):
    """Send typed remote requests without owning application state."""

    async def request(self, request: TransportRequest) -> TransportResponse:
        """Send a request and return a validated response."""
        ...
