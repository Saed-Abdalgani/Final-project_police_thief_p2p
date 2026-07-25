"""Central external-call Gatekeeper contract and initial bounded facade."""

import asyncio
from collections.abc import Awaitable, Callable, Mapping
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


class MonotonicSource(Protocol):
    """Minimum clock surface needed for deterministic deadlines."""

    def monotonic(self) -> float:
        """Return monotonically increasing seconds."""
        ...


class InitialGatekeeper:
    """Bound concurrency, deadlines, and stable-byte retries for MCP calls."""

    __slots__ = (
        "_clock",
        "_executor",
        "_max_retries",
        "_semaphore",
        "_sleep",
        "_timeout_sec",
    )

    def __init__(
        self,
        executor: Callable[[ExternalCall], Awaitable[ExternalResult]],
        *,
        clock: MonotonicSource,
        timeout_sec: float,
        max_retries: int,
        concurrent_requests: int,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        """Configure bounded attempts without accepting mutable retry rewrites."""
        if timeout_sec <= 0 or max_retries < 0 or concurrent_requests < 1:
            raise ValueError("Gatekeeper limits are invalid")
        self._executor = executor
        self._clock = clock
        self._timeout_sec = timeout_sec
        self._max_retries = max_retries
        self._semaphore = asyncio.Semaphore(concurrent_requests)
        self._sleep = sleep

    async def execute(self, call: ExternalCall) -> ExternalResult:
        """Execute through one deadline while reusing the identical call object."""
        deadline = self._clock.monotonic() + self._timeout_sec
        async with self._semaphore:
            for attempt in range(self._max_retries + 1):
                remaining = deadline - self._clock.monotonic()
                if remaining <= 0:
                    return self._timeout()
                try:
                    result = await asyncio.wait_for(self._executor(call), timeout=remaining)
                    if self._clock.monotonic() > deadline:
                        return self._timeout()
                    if result.outcome == "success" or attempt == self._max_retries:
                        return result
                except TimeoutError:
                    return self._timeout()
                except Exception:
                    if attempt == self._max_retries:
                        return ExternalResult(
                            "unavailable",
                            {"code": "DEPENDENCY_UNAVAILABLE"},
                        )
                await self._sleep(0)
        return ExternalResult("unavailable", {"code": "DEPENDENCY_UNAVAILABLE"})

    @staticmethod
    def _timeout() -> ExternalResult:
        return ExternalResult("timeout", {"code": "REQUEST_TIMEOUT"})
