"""Central external-call Gatekeeper contract."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ExternalCall:
    """Validated provider-neutral external operation."""

    service: str
    operation: str
    payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ExternalResult:
    """Provider-neutral external result."""

    outcome: str
    payload: Mapping[str, object]


@runtime_checkable
class GatekeeperPort(Protocol):
    """Apply configured limits, retries, queues, and monitoring."""

    async def execute(self, call: ExternalCall) -> ExternalResult:
        """Execute one bounded external operation."""
        ...
