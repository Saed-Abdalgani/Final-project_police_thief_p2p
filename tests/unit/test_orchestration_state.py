import threading

import pytest

from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.services.orchestration.cancellation import CancellationToken
from police_thief_p2p.services.orchestration.circuit import CircuitBreaker, CircuitState
from police_thief_p2p.services.orchestration.deadlines import DeadlinePolicy, DeadlineTracker
from police_thief_p2p.services.orchestration.phases import (
    TERMINAL_PHASES,
    TRANSITIONS,
    GamePhase,
    PhaseMachine,
    TransitionReason,
)
from police_thief_p2p.services.orchestration.retry import (
    BackoffPolicy,
    RetryClass,
    classify_failure,
)
from police_thief_p2p.services.orchestration.tunnel import (
    TunnelPreflight,
    validate_tunnel_url,
)
from police_thief_p2p.services.orchestration.work_queue import (
    BoundedWorkQueue,
    EnqueueOutcome,
    WorkPriority,
)


def test_every_phase_has_reviewed_successors_and_terminals_are_immutable() -> None:
    assert set(TRANSITIONS) == set(GamePhase)
    assert all(TRANSITIONS[phase] == {} for phase in TERMINAL_PHASES)
    for phase in set(GamePhase) - TERMINAL_PHASES:
        assert TRANSITIONS[phase]
    for terminal in TERMINAL_PHASES:
        machine = PhaseMachine(terminal)
        with pytest.raises(ValueError, match="not allowed"):
            machine.transition(terminal, GamePhase.CREATED)


def test_phase_compare_and_set_allows_only_one_concurrent_winner() -> None:
    machine = PhaseMachine()
    outcomes: list[str] = []

    def advance() -> None:
        try:
            machine.transition(GamePhase.CREATED, GamePhase.INITIALIZING)
            outcomes.append("won")
        except RuntimeError:
            outcomes.append("lost")

    threads = [threading.Thread(target=advance) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert outcomes.count("won") == 1
    assert outcomes.count("lost") == 7


def test_reason_specific_transitions_refuse_wrong_target() -> None:
    machine = PhaseMachine(GamePhase.NEGOTIATING)
    with pytest.raises(ValueError, match="reason"):
        machine.transition(
            GamePhase.NEGOTIATING,
            GamePhase.REFUSED,
            TransitionReason.NORMAL,
        )
    assert (
        machine.transition(
            GamePhase.NEGOTIATING,
            GamePhase.REFUSED,
            TransitionReason.REFUSAL,
        ).phase
        is GamePhase.REFUSED
    )


def test_deadline_policy_covers_every_operation_and_fake_clock(
    shared_config_bytes: bytes,
    private_config_bytes: bytes,
) -> None:
    from police_thief_p2p import SimulationSdk

    effective = SimulationSdk().load_configuration(shared_config_bytes, private_config_bytes)
    policy = DeadlinePolicy.from_effective(effective)
    assert len(policy.values) == 8
    clock = FakeClock()
    tracker = DeadlineTracker.after(clock, 2)
    assert tracker.remaining() == 2
    clock.advance(2)
    assert tracker.expired()
    with pytest.raises(ValueError, match="positive"):
        DeadlineTracker.after(clock, 0)


def test_retry_classification_backoff_and_circuit_recovery() -> None:
    assert classify_failure("HTTP_503", 1, 4) is RetryClass.RETRYABLE
    assert classify_failure("BAD_PHASE", 1, 4) is RetryClass.SEMANTIC
    assert classify_failure("TAMPER", 1, 4) is RetryClass.INTEGRITY
    assert classify_failure("HTTP_503", 4, 4) is RetryClass.EXHAUSTED
    policy = BackoffPolicy(100, 500, 0.2)
    delays = [
        policy.delay_seconds(attempt, DeterministicRandomSource(1)) for attempt in range(1, 5)
    ]
    assert all(0 <= delay <= 0.5 for delay in delays)
    clock = FakeClock()
    circuit = CircuitBreaker(clock, threshold=2, cooldown=3)
    circuit.failure()
    assert circuit.state is CircuitState.CLOSED
    circuit.failure()
    assert not circuit.allow()
    clock.advance(3)
    assert str(circuit.state) == CircuitState.HALF_OPEN.value
    circuit.success()
    assert circuit.state is CircuitState.CLOSED


def test_bounded_queue_prioritizes_gameplay_and_reports_backpressure() -> None:
    queue = BoundedWorkQueue(2)
    assert queue.enqueue(WorkPriority.BANTER, "banter", {}) is EnqueueOutcome.ACCEPTED
    queue.enqueue(WorkPriority.REPORTING, "report", {})
    assert queue.enqueue(WorkPriority.GAMEPLAY, "move", {}) is EnqueueOutcome.EVICTED_OPTIONAL
    assert queue.enqueue(WorkPriority.BANTER, "more", {}) is EnqueueOutcome.REJECTED_BACKPRESSURE
    assert queue.dequeue().priority is WorkPriority.GAMEPLAY  # type: ignore[union-attr]


def test_cancellation_and_tunnel_validation_preflight() -> None:
    token = CancellationToken()
    assert not token.cancelled()
    token.cancel()
    with pytest.raises(RuntimeError, match="cancelled"):
        token.raise_if_cancelled()
    assert validate_tunnel_url("http://LOCALHOST:8000/", competition_mode=False) == (
        "http://localhost:8000/mcp"
    )
    for url in (
        "ftp://example.com",
        "https://user:pass@example.com",  # pragma: allowlist secret
        "http://127.0.0.1",
    ):
        with pytest.raises(ValueError, match="tunnel"):
            validate_tunnel_url(url, competition_mode=True)

    class Probe:
        def health(self, url: str, timeout: float) -> bool:
            return bool(url and timeout)

        capabilities = health
        round_trip = health
        payload_limit = health
        bidirectional = health

    results = TunnelPreflight(Probe()).run(
        "https://peer.example/mcp",
        DeadlineTracker.after(FakeClock(), 5),
    )
    assert all(results.values())
