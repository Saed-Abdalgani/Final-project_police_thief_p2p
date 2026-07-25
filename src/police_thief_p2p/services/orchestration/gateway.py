"""Deadline/retry/idempotency context around the central Gatekeeper."""

import asyncio
from collections.abc import Awaitable, Callable, Mapping

from police_thief_p2p.services.orchestration.cancellation import CancellationToken
from police_thief_p2p.services.orchestration.circuit import CircuitBreaker
from police_thief_p2p.services.orchestration.deadlines import DeadlineTracker
from police_thief_p2p.services.orchestration.retry import (
    BackoffPolicy,
    RetryClass,
    classify_failure,
)
from police_thief_p2p.services.ports.random_source import RandomSource
from police_thief_p2p.shared.gatekeeper import (
    ExternalCall,
    ExternalResult,
    GatekeeperPort,
)


class OrchestratedGateway:
    """Supply bounded retry, circuit, deadline, and stable idempotency context."""

    __slots__ = (
        "_backoff",
        "_circuit",
        "_gatekeeper",
        "_max_attempts",
        "_rng",
        "_sleep",
    )

    def __init__(
        self,
        gatekeeper: GatekeeperPort,
        *,
        circuit: CircuitBreaker,
        backoff: BackoffPolicy,
        max_attempts: int,
        rng: RandomSource,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        """Create a bounded wrapper around the central Gatekeeper."""
        if max_attempts < 1:
            raise ValueError("gateway attempt budget must be positive")
        self._gatekeeper = gatekeeper
        self._circuit = circuit
        self._backoff = backoff
        self._max_attempts = max_attempts
        self._rng = rng
        self._sleep = sleep

    async def execute(
        self,
        service: str,
        operation: str,
        payload: Mapping[str, object],
        *,
        idempotency_key: str,
        deadline: DeadlineTracker,
        cancellation: CancellationToken,
    ) -> ExternalResult:
        """Execute stable context until success, non-retryable failure, or expiry."""
        call = ExternalCall(
            service,
            operation,
            {
                **payload,
                "idempotency_key": idempotency_key,
                "deadline_monotonic": format(deadline.deadline, ".9f"),
            },
        )
        for attempt in range(1, self._max_attempts + 1):
            cancellation.raise_if_cancelled()
            if deadline.expired():
                return ExternalResult("timeout", {"code": "TIMEOUT"})
            if not self._circuit.allow():
                return ExternalResult("unavailable", {"code": "CIRCUIT_OPEN"})
            result = await self._gatekeeper.execute(call)
            if result.outcome == "success":
                self._circuit.success()
                return result
            code = str(result.payload.get("code", "SEMANTIC_ERROR"))
            disposition = classify_failure(code, attempt, self._max_attempts)
            if disposition is not RetryClass.RETRYABLE:
                if disposition is RetryClass.INTEGRITY:
                    self._circuit.failure()
                return result
            self._circuit.failure()
            delay = min(
                deadline.remaining(),
                self._backoff.delay_seconds(attempt, self._rng),
            )
            if delay <= 0:
                return ExternalResult("timeout", {"code": "TIMEOUT"})
            await self._sleep(delay)
        return ExternalResult("unavailable", {"code": "RETRY_EXHAUSTED"})
