"""Complete central Gatekeeper for MCP, Gmail, and external LLM calls."""

import asyncio
from collections.abc import Mapping

from police_thief_p2p.services.gatekeeper.anomaly import AnomalyDetector
from police_thief_p2p.services.gatekeeper.execution import (
    Executor,
    ProtectedExecutor,
    ServiceControls,
    Sleeper,
)
from police_thief_p2p.services.gatekeeper.limiter import ContinuousTokenBucket
from police_thief_p2p.services.gatekeeper.metrics import GatekeeperMetrics
from police_thief_p2p.services.gatekeeper.priority import AdmissionOutcome, PrioritySemaphore
from police_thief_p2p.services.gatekeeper.profile import GatekeeperProfile
from police_thief_p2p.services.gatekeeper.quota import DurableQuotaManager
from police_thief_p2p.services.orchestration.circuit import CircuitBreaker
from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.services.ports.random_source import RandomSource
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.gatekeeper import ExternalCall, ExternalResult


class FullGatekeeper:
    """Apply every configured protection before one provider executor."""

    __slots__ = ("_anomaly", "_controls", "_executors", "_metrics", "_runner")

    def __init__(
        self,
        profiles: Mapping[str, GatekeeperProfile],
        executors: Mapping[str, Executor],
        *,
        clock: ClockPort,
        quota: DurableQuotaManager,
        rng: RandomSource,
        sleep: Sleeper = asyncio.sleep,
    ) -> None:
        """Create provider-isolated limits from configuration only."""
        if set(executors) - set(profiles):
            raise ValueError("executor has no configured Gatekeeper profile")
        self._executors = dict(executors)
        self._anomaly = AnomalyDetector(clock)
        self._metrics = GatekeeperMetrics()
        self._runner = ProtectedExecutor(
            clock=clock,
            quota=quota,
            rng=rng,
            sleep=sleep,
            anomaly=self._anomaly,
            metrics=self._metrics,
        )
        self._controls = {
            service: ServiceControls(
                profile,
                ContinuousTokenBucket(
                    clock,
                    requests_per_minute=profile.requests_per_minute,
                    capacity=profile.burst_capacity,
                ),
                PrioritySemaphore(
                    limit=profile.concurrent_requests,
                    queue_capacity=profile.queue_depth,
                ),
                CircuitBreaker(
                    clock,
                    threshold=profile.circuit_failure_threshold,
                    cooldown=profile.circuit_cooldown_sec,
                ),
            )
            for service, profile in profiles.items()
        }

    async def execute(self, call: ExternalCall) -> ExternalResult:
        """Execute one bounded, classified, metered external operation."""
        controls = self._controls.get(call.service)
        executor = self._executors.get(call.service)
        if controls is None or executor is None:
            return self._reject(call.service, "SERVICE_NOT_CONFIGURED")
        try:
            signature = sha256_digest(
                {"service": call.service, "operation": call.operation, "payload": call.payload}
            )
        except (TypeError, ValueError):
            return self._reject(call.service, "UNSAFE_CALL_PAYLOAD")
        allowed, code = self._anomaly.admit(
            call.service,
            signature,
            burst_limit=controls.profile.burst_capacity,
            repeated_limit=controls.profile.repeated_call_limit,
            error_limit=controls.profile.sustained_error_limit,
        )
        if not allowed:
            return self._reject(call.service, code or "ANOMALY_REJECTED")
        admission = await controls.admission.acquire(_priority(call.payload))
        if admission is AdmissionOutcome.REJECTED_BACKPRESSURE:
            return self._reject(call.service, "QUEUE_BACKPRESSURE")
        self._update_gauges(call.service, controls)
        try:
            result = await self._runner.run(call, controls, executor)
            if result.outcome == "rejected":
                self._metrics.increment(call.service, "rejections")
            return result
        finally:
            await controls.admission.release()
            self._update_gauges(call.service, controls)

    def metrics(self) -> dict[str, dict[str, float]]:
        """Return redacted resource, retry, rejection, and circuit data."""
        for service, controls in self._controls.items():
            self._update_gauges(service, controls)
        return self._metrics.snapshot()

    def manual_reset(self, service: str, *, confirmed: bool) -> None:
        """Safely reset one circuit/anomaly window with explicit confirmation."""
        self._controls[service].circuit.reset(confirmed=confirmed)
        self._anomaly.reset(service, confirmed=confirmed)

    def _reject(self, service: str, code: str) -> ExternalResult:
        self._metrics.increment(service, "rejections")
        return ExternalResult("rejected", {"code": code})

    def _update_gauges(self, service: str, controls: ServiceControls) -> None:
        self._metrics.gauge(service, "queue_depth", float(controls.admission.queued))
        self._metrics.gauge(service, "concurrency", float(controls.admission.active))
        states = {"closed": 0.0, "half-open": 1.0, "open": 2.0}
        self._metrics.gauge(service, "circuit_state", states[controls.circuit.state.value])


def _priority(payload: Mapping[str, object]) -> int:
    value = payload.get("priority", 2)
    return value if type(value) is int and 0 <= value <= 3 else 2
