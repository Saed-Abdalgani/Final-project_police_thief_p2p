"""Admitted Gatekeeper attempt, quota, timeout, and retry execution."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from police_thief_p2p.services.gatekeeper.anomaly import AnomalyDetector
from police_thief_p2p.services.gatekeeper.limiter import ContinuousTokenBucket
from police_thief_p2p.services.gatekeeper.metrics import GatekeeperMetrics
from police_thief_p2p.services.gatekeeper.priority import PrioritySemaphore
from police_thief_p2p.services.gatekeeper.profile import GatekeeperProfile
from police_thief_p2p.services.gatekeeper.quota import DurableQuotaManager
from police_thief_p2p.services.orchestration.circuit import CircuitBreaker
from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.services.ports.random_source import RandomSource
from police_thief_p2p.shared.gatekeeper import ExternalCall, ExternalResult

Executor = Callable[[ExternalCall], Awaitable[ExternalResult]]
Sleeper = Callable[[float], Awaitable[None]]


@dataclass(slots=True)
class ServiceControls:
    """All isolated state for one configured provider."""

    profile: GatekeeperProfile
    bucket: ContinuousTokenBucket
    admission: PrioritySemaphore
    circuit: CircuitBreaker


class ProtectedExecutor:
    """Execute attempts after anomaly and queue admission."""

    __slots__ = ("_anomaly", "_clock", "_metrics", "_quota", "_rng", "_sleep")

    def __init__(
        self,
        *,
        clock: ClockPort,
        quota: DurableQuotaManager,
        rng: RandomSource,
        sleep: Sleeper,
        anomaly: AnomalyDetector,
        metrics: GatekeeperMetrics,
    ) -> None:
        """Bind deterministic protection dependencies."""
        self._clock = clock
        self._quota = quota
        self._rng = rng
        self._sleep = sleep
        self._anomaly = anomaly
        self._metrics = metrics

    async def run(
        self,
        call: ExternalCall,
        controls: ServiceControls,
        executor: Executor,
    ) -> ExternalResult:
        """Apply circuit, quotas, token bucket, retries, backoff, and timeout."""
        profile = controls.profile
        if not controls.circuit.allow():
            return ExternalResult("rejected", {"code": "CIRCUIT_OPEN"})
        deadline = self._clock.monotonic() + profile.timeout_sec
        for attempt in range(profile.max_retries + 1):
            if not self._quota.consume(
                call.service,
                daily_limit=profile.daily_quota,
                session_limit=profile.session_quota,
            ):
                return ExternalResult("rejected", {"code": "QUOTA_EXHAUSTED"})
            daily, session = self._quota.usage(call.service)
            self._metrics.gauge(call.service, "quota_daily_used", float(daily))
            self._metrics.gauge(call.service, "quota_session_used", float(session))
            limited = await self._consume_token(call.service, controls, deadline)
            if limited is not None:
                return limited
            result = await self._call_once(call, executor, deadline)
            if result.outcome == "success":
                controls.circuit.success()
                self._metrics.increment(call.service, "successes")
                return result
            retryable = {"retryable", "rate_limited", "timeout", "unavailable"}
            if result.outcome not in retryable:
                self._metrics.increment(call.service, "permanent_failures")
                return result
            self._anomaly.record_error(call.service)
            if attempt >= profile.max_retries:
                controls.circuit.failure()
                self._metrics.increment(call.service, "retry_exhausted")
                return result
            delay = retry_delay(result, profile, attempt + 1, self._rng.random())
            if self._clock.monotonic() + delay >= deadline:
                controls.circuit.failure()
                return ExternalResult("timeout", {"code": "REQUEST_TIMEOUT"})
            self._metrics.increment(call.service, "retries")
            await self._sleep(delay)
        return ExternalResult("unavailable", {"code": "DEPENDENCY_UNAVAILABLE"})

    async def _consume_token(
        self,
        service: str,
        controls: ServiceControls,
        deadline: float,
    ) -> ExternalResult | None:
        delay = controls.bucket.consume_delay()
        if delay <= 0:
            self._metrics.gauge(service, "tokens", controls.bucket.available)
            return None
        if self._clock.monotonic() + delay >= deadline:
            return ExternalResult("timeout", {"code": "REQUEST_TIMEOUT"})
        await self._sleep(delay)
        controls.bucket.consume_after_wait()
        self._metrics.gauge(service, "tokens", controls.bucket.available)
        return None

    async def _call_once(
        self,
        call: ExternalCall,
        executor: Executor,
        deadline: float,
    ) -> ExternalResult:
        remaining = deadline - self._clock.monotonic()
        if remaining <= 0:
            return ExternalResult("timeout", {"code": "REQUEST_TIMEOUT"})
        try:
            result = await asyncio.wait_for(executor(call), timeout=remaining)
        except TimeoutError:
            return ExternalResult("timeout", {"code": "REQUEST_TIMEOUT"})
        except Exception:
            return ExternalResult("unavailable", {"code": "DEPENDENCY_UNAVAILABLE"})
        if self._clock.monotonic() > deadline:
            return ExternalResult("timeout", {"code": "REQUEST_TIMEOUT"})
        return result


def retry_delay(
    result: ExternalResult,
    profile: GatekeeperProfile,
    attempt: int,
    random_value: float,
) -> float:
    """Return positive exponential jitter honoring provider 429 guidance."""
    exponential = profile.retry_backoff_sec * (2 ** (attempt - 1))
    jittered = exponential * (0.8 + 0.4 * random_value)
    guidance = result.payload.get("retry_after_sec", 0)
    retry_after = (
        float(guidance)
        if isinstance(guidance, (int, float)) and not isinstance(guidance, bool)
        else 0.0
    )
    delay: float = max(float(profile.retry_backoff_sec), jittered, retry_after)
    return delay
