import asyncio
from dataclasses import dataclass

import pytest

from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.services.orchestration.cancellation import CancellationToken
from police_thief_p2p.services.orchestration.circuit import CircuitBreaker
from police_thief_p2p.services.orchestration.deadlines import DeadlineTracker
from police_thief_p2p.services.orchestration.gateway import OrchestratedGateway
from police_thief_p2p.services.orchestration.phases import GamePhase
from police_thief_p2p.services.orchestration.retry import BackoffPolicy
from police_thief_p2p.services.orchestration.shutdown import (
    ShutdownResources,
    controlled_shutdown,
)
from police_thief_p2p.services.orchestration.watchdog import Heartbeat, Watchdog
from police_thief_p2p.shared.gatekeeper import ExternalCall, ExternalResult


class Gateway:
    def __init__(self, results: list[ExternalResult]) -> None:
        self.results = results
        self.calls: list[ExternalCall] = []

    async def execute(self, call: ExternalCall) -> ExternalResult:
        self.calls.append(call)
        return self.results.pop(0)


@pytest.mark.parametrize(
    "code",
    [
        "TIMEOUT",
        "CONNECTION_RESET",
        "CONNECTION_REFUSED",
        "HTTP_500",
        "HTTP_503",
        "DEPENDENCY_UNAVAILABLE",
    ],
)
def test_network_faults_retry_identical_idempotent_context(code: str) -> None:
    clock = FakeClock()
    gateway = Gateway(
        [ExternalResult("failure", {"code": code}), ExternalResult("success", {"ok": True})]
    )

    async def advance(delay: float) -> None:
        clock.advance(delay)

    wrapper = OrchestratedGateway(
        gateway,
        circuit=CircuitBreaker(clock, threshold=4, cooldown=1),
        backoff=BackoffPolicy(1, 10, 0),
        max_attempts=3,
        rng=DeterministicRandomSource(1),
        sleep=advance,
    )
    result = asyncio.run(
        wrapper.execute(
            "mcp",
            "commit",
            {"bytes": "stable"},
            idempotency_key="message-1",
            deadline=DeadlineTracker.after(clock, 2),
            cancellation=CancellationToken(),
        )
    )
    assert result.outcome == "success"
    assert gateway.calls[0] is gateway.calls[1]
    assert gateway.calls[0].payload["idempotency_key"] == "message-1"


def test_semantic_and_malformed_failures_never_retry() -> None:
    clock = FakeClock()
    gateway = Gateway([ExternalResult("failure", {"code": "MALFORMED_RESPONSE"})])
    wrapper = OrchestratedGateway(
        gateway,
        circuit=CircuitBreaker(clock, threshold=2, cooldown=1),
        backoff=BackoffPolicy(1, 2, 0),
        max_attempts=3,
        rng=DeterministicRandomSource(1),
    )
    result = asyncio.run(
        wrapper.execute(
            "mcp",
            "reveal",
            {},
            idempotency_key="message-2",
            deadline=DeadlineTracker.after(clock, 1),
            cancellation=CancellationToken(),
        )
    )
    assert result.payload["code"] == "MALFORMED_RESPONSE"
    assert len(gateway.calls) == 1


def test_watchdog_detects_absent_and_unchanged_progress() -> None:
    clock = FakeClock()
    watchdog = Watchdog(clock, 3)
    assert watchdog.check(None) is None
    clock.advance(3)
    assert watchdog.check(None) == "heartbeat-absent"

    heartbeat = Heartbeat(GamePhase.WAITING_ACK, 2, clock.monotonic(), 9)
    assert watchdog.check(heartbeat) is None
    clock.advance(3)
    assert watchdog.check(heartbeat) == "progress-stalled"


def test_controlled_shutdown_is_cooperative_and_ordered() -> None:
    closed: list[str] = []

    @dataclass
    class Resource:
        name: str

        def close(self) -> None:
            closed.append(self.name)

    token = CancellationToken()
    resources = ShutdownResources(
        Resource("transport"),
        Resource("journal"),
        Resource("artifact_writer"),
        Resource("gui"),
        Resource("workers"),
    )
    assert controlled_shutdown(resources, token) == (
        "transport",
        "journal",
        "artifact_writer",
        "gui",
        "workers",
    )
    assert token.cancelled()
    assert closed == [
        "transport",
        "journal",
        "artifact_writer",
        "gui",
        "workers",
    ]
