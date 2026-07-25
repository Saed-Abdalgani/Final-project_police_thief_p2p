from dataclasses import dataclass, field
from itertools import pairwise

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.services.orchestration.cancellation import CancellationToken
from police_thief_p2p.services.orchestration.deadlines import DeadlinePolicy, DeadlineTracker
from police_thief_p2p.services.orchestration.orchestrator import PeerOrchestrator
from police_thief_p2p.services.orchestration.phases import GamePhase
from police_thief_p2p.services.orchestration.ports import IntegrityError, RefusalError
from police_thief_p2p.services.orchestration.watchdog import HealthState, Heartbeat


@dataclass
class Workflow:
    terminal_step: int = 2
    fail_phase: GamePhase | None = None
    failure: Exception | None = None
    calls: list[tuple[GamePhase, int, int]] = field(default_factory=list)
    resets: list[int] = field(default_factory=list)

    def execute(
        self,
        phase: GamePhase,
        sub_game_number: int,
        step_number: int,
        deadline: DeadlineTracker,
        _cancellation: CancellationToken,
    ) -> None:
        assert deadline.remaining() > 0
        self.calls.append((phase, sub_game_number, step_number))
        if phase is self.fail_phase and self.failure is not None:
            raise self.failure

    def reset_sub_game(self, sub_game_number: int) -> None:
        self.resets.append(sub_game_number)

    def sub_game_terminal(self, sub_game_number: int, step_number: int) -> bool:
        del sub_game_number
        return step_number >= self.terminal_step


def _policy() -> DeadlinePolicy:
    from police_thief_p2p.services.orchestration.deadlines import Operation

    return DeadlinePolicy(dict.fromkeys(Operation, 10.0), 30)


def test_orchestrator_runs_six_clean_subgames_and_full_handoff() -> None:
    workflow = Workflow()
    result = PeerOrchestrator(workflow, clock=FakeClock(), deadlines=_policy()).run_series()
    assert result.phase is GamePhase.COMPLETED
    assert result.sub_games_completed == 6
    assert result.steps_completed == 12
    assert workflow.resets == [1, 2, 3, 4, 5, 6]
    phases = [phase for phase, _, _ in workflow.calls]
    assert GamePhase.UPDATING_BELIEF in phases
    assert GamePhase.COMPUTING_STRATEGY in phases
    assert GamePhase.COMMITTING in phases
    assert phases[-1] is GamePhase.SHUTTING_DOWN
    assert all(
        right.progress_token > left.progress_token for left, right in pairwise(result.heartbeats)
    )


@pytest.mark.parametrize(
    ("phase", "failure", "terminal"),
    [
        (GamePhase.NEGOTIATING, RefusalError(), GamePhase.REFUSED),
        (GamePhase.VERIFYING, IntegrityError(), GamePhase.TAMPER),
        (GamePhase.WAITING_ACK, TimeoutError(), GamePhase.TECHNICAL_LOSS),
    ],
)
def test_faults_reach_explicit_terminal_without_deadlock(
    phase: GamePhase,
    failure: Exception,
    terminal: GamePhase,
) -> None:
    result = PeerOrchestrator(
        Workflow(fail_phase=phase, failure=failure),
        clock=FakeClock(),
        deadlines=_policy(),
    ).run_series()
    assert result.phase is terminal


def test_sdk_lifecycle_and_redacted_health(
    shared_config_bytes: bytes,
    private_config_bytes: bytes,
) -> None:
    sdk = SimulationSdk()
    effective = sdk.load_configuration(shared_config_bytes, private_config_bytes)
    result = sdk.run_peer_lifecycle(Workflow(terminal_step=1), effective, clock=FakeClock())
    assert result.phase is GamePhase.COMPLETED
    heartbeat = Heartbeat(GamePhase.READY, 0, 1.0, 4)
    ready = sdk.redacted_peer_health(heartbeat, ready=True)
    assert ready.state is HealthState.READY
    assert ready.as_dict() == {
        "status": "ready",
        "phase": "ready",
        "step_number": 0,
        "progress_token": 4,
    }
