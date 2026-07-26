import asyncio
from pathlib import Path

import pytest

from police_thief_p2p.adapters.persistence import AtomicFileRepository
from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.services.gatekeeper.anomaly import AnomalyDetector
from police_thief_p2p.services.orchestration.cancellation import CancellationToken
from police_thief_p2p.services.orchestration.circuit import CircuitBreaker
from police_thief_p2p.services.orchestration.deadlines import DeadlineTracker
from police_thief_p2p.services.orchestration.gateway import OrchestratedGateway
from police_thief_p2p.services.orchestration.journal import OrchestrationJournal
from police_thief_p2p.services.orchestration.persistence import CrashPoint, persist_before_ack
from police_thief_p2p.services.orchestration.phases import GamePhase
from police_thief_p2p.services.orchestration.retry import BackoffPolicy
from police_thief_p2p.services.orchestration.watchdog import Heartbeat, Watchdog
from police_thief_p2p.services.protocol.inventory import TOOL_VERSIONS
from police_thief_p2p.services.protocol.session import SessionRegistry
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.gatekeeper import ExternalCall, ExternalResult
from tests.helpers.protocol import GROUP_A, GROUP_B, make_proposal

pytestmark = pytest.mark.chaos


class _Gateway:
    def __init__(self) -> None:
        self.calls: list[ExternalCall] = []

    async def execute(self, call: ExternalCall) -> ExternalResult:
        self.calls.append(call)
        if len(self.calls) % 2:
            return ExternalResult("failure", {"code": "CONNECTION_RESET"})
        return ExternalResult("success", {"ok": True})


@pytest.mark.parametrize("tool", sorted(TOOL_VERSIONS))
def test_every_outbound_tool_retains_deadline_and_identity_across_loss(tool: str) -> None:
    clock = FakeClock()
    gateway = _Gateway()

    async def advance(delay: float) -> None:
        clock.advance(delay)

    wrapper = OrchestratedGateway(
        gateway,
        circuit=CircuitBreaker(clock, threshold=4, cooldown=1),
        backoff=BackoffPolicy(1, 5, 0),
        max_attempts=2,
        rng=DeterministicRandomSource(11),
        sleep=advance,
    )
    result = asyncio.run(
        wrapper.execute(
            "mcp",
            tool,
            {"phase": tool},
            idempotency_key=f"m11-{tool}",
            deadline=DeadlineTracker.after(clock, 10),
            cancellation=CancellationToken(),
        )
    )
    assert result.outcome == "success"
    assert gateway.calls[-2] is gateway.calls[-1]
    assert gateway.calls[-1].payload["idempotency_key"] == f"m11-{tool}"
    assert clock.monotonic() <= 10


@pytest.mark.parametrize("point", list(CrashPoint))
def test_every_persist_ack_crash_boundary_has_deterministic_recovery(
    tmp_path: Path,
    point: CrashPoint,
) -> None:
    journal = OrchestrationJournal(AtomicFileRepository(tmp_path / point.value), "journal")
    acknowledged: list[bool] = []

    def crash(observed: CrashPoint) -> None:
        if observed is point:
            raise RuntimeError(point.value)

    with pytest.raises(RuntimeError, match=point.value):
        persist_before_ack(
            journal,
            "mutation",
            {"point": point.value},
            lambda: acknowledged.append(True),
            crash,
        )
    persisted = point is not CrashPoint.BEFORE_JOURNAL
    acked = point is CrashPoint.AFTER_ACK
    assert bool(journal.records) is persisted
    assert bool(acknowledged) is acked


@pytest.mark.parametrize(
    "worker_phase",
    [
        GamePhase.WAITING_FOR_OPPONENT,
        GamePhase.COMPUTING_STRATEGY,
        GamePhase.CHECKPOINTING,
        GamePhase.COMMITTING,
    ],
)
def test_watchdog_detects_each_frozen_worker_family(worker_phase: GamePhase) -> None:
    clock = FakeClock()
    watchdog = Watchdog(clock, 2)
    heartbeat = Heartbeat(worker_phase, 3, clock.monotonic(), 7)
    assert watchdog.check(heartbeat) is None
    clock.advance(2)
    assert watchdog.check(heartbeat) == "progress-stalled"


def test_session_and_anomaly_retention_remain_bounded(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    registry = SessionRegistry(GROUP_B, AtomicFileRepository(tmp_path / "sessions"), 4)
    for number in range(10):
        proposal = make_proposal(shared_config, shared_config_bytes).model_copy(
            update={"game_uid": f"12345678-1234-4234-8234-{number:012d}"}
        )
        registry.create(proposal, GROUP_A)
        assert registry.cached_session_count <= 4

    clock = FakeClock()
    detector = AnomalyDetector(clock, max_signatures=16)
    for number in range(100):
        accepted, _reason = detector.admit(
            "mcp",
            f"signature-{number}",
            burst_limit=1_000,
            repeated_limit=2,
            error_limit=2,
        )
        assert accepted
    assert detector.signature_count == 16
