"""Policy-free durable lifecycle coordinator over injected service ports."""

from dataclasses import dataclass

from police_thief_p2p.services.orchestration.cancellation import CancellationToken
from police_thief_p2p.services.orchestration.deadlines import (
    DeadlinePolicy,
    Operation,
)
from police_thief_p2p.services.orchestration.phases import (
    GamePhase,
    PhaseMachine,
    TransitionReason,
)
from police_thief_p2p.services.orchestration.ports import (
    IntegrityError,
    PeerWorkflowPort,
    RefusalError,
)
from police_thief_p2p.services.orchestration.watchdog import Heartbeat
from police_thief_p2p.services.ports.clock import ClockPort

_OPERATION = {
    GamePhase.INITIALIZING: Operation.MCP,
    GamePhase.READY: Operation.MCP,
    GamePhase.NEGOTIATING: Operation.NEGOTIATION,
    GamePhase.WAITING_FOR_OPPONENT: Operation.MCP,
    GamePhase.UPDATING_BELIEF: Operation.MCP,
    GamePhase.COMPUTING_STRATEGY: Operation.STRATEGY,
    GamePhase.COMMITTING: Operation.MCP,
    GamePhase.WAITING_ACK: Operation.ACKNOWLEDGEMENT,
    GamePhase.REVEALING: Operation.REVEAL,
    GamePhase.VERIFYING: Operation.MCP,
    GamePhase.CHECKPOINTING: Operation.MCP,
    GamePhase.SUBGAME_TERMINAL: Operation.MCP,
    GamePhase.AUDITING: Operation.AUDIT,
    GamePhase.AGREEING_RESULT: Operation.MCP,
    GamePhase.FINALIZING_ARTIFACTS: Operation.REPORTING,
    GamePhase.QUEUEING_REPORT: Operation.REPORTING,
    GamePhase.SHUTTING_DOWN: Operation.REPORTING,
}


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    """Terminal phase and bounded progress evidence."""

    phase: GamePhase
    sub_games_completed: int
    steps_completed: int
    heartbeats: tuple[Heartbeat, ...]


class PeerOrchestrator:
    """Drive the formal lifecycle without owning game/protocol implementation."""

    __slots__ = (
        "_cancel",
        "_clock",
        "_deadlines",
        "_heartbeats",
        "_machine",
        "_progress",
        "_workflow",
    )

    def __init__(
        self,
        workflow: PeerWorkflowPort,
        *,
        clock: ClockPort,
        deadlines: DeadlinePolicy,
        cancellation: CancellationToken | None = None,
        phase_machine: PhaseMachine | None = None,
    ) -> None:
        """Create a coordinator from injected ports and effective policy."""
        self._workflow = workflow
        self._clock = clock
        self._deadlines = deadlines
        self._cancel = CancellationToken() if cancellation is None else cancellation
        self._machine = PhaseMachine() if phase_machine is None else phase_machine
        self._progress = 0
        self._heartbeats: list[Heartbeat] = []

    def run_series(self, *, sub_games: int = 6, max_steps: int = 35) -> OrchestrationResult:
        """Run readiness, negotiation, six reset sub-games, audit, and handoff."""
        if sub_games < 1 or max_steps < 1:
            raise ValueError("series bounds must be positive")
        completed = 0
        steps = 0
        try:
            self._advance(GamePhase.INITIALIZING, 0, 0)
            self._advance(GamePhase.READY, 0, 0)
            self._advance(GamePhase.NEGOTIATING, 0, 0)
            self._advance(GamePhase.WAITING_FOR_OPPONENT, 1, 0)
            for sub_game in range(1, sub_games + 1):
                self._workflow.reset_sub_game(sub_game)
                terminal = False
                for step in range(1, max_steps + 1):
                    for phase in (
                        GamePhase.UPDATING_BELIEF,
                        GamePhase.COMPUTING_STRATEGY,
                        GamePhase.COMMITTING,
                        GamePhase.WAITING_ACK,
                        GamePhase.REVEALING,
                        GamePhase.VERIFYING,
                        GamePhase.CHECKPOINTING,
                    ):
                        self._advance(phase, sub_game, step)
                    steps += 1
                    terminal = self._workflow.sub_game_terminal(sub_game, step)
                    target = (
                        GamePhase.SUBGAME_TERMINAL if terminal else GamePhase.WAITING_FOR_OPPONENT
                    )
                    self._advance(target, sub_game, step)
                    if terminal:
                        break
                if not terminal:
                    raise RuntimeError("sub-game exceeded bounded steps without terminal")
                completed += 1
                next_phase = (
                    GamePhase.AUDITING if sub_game == sub_games else GamePhase.WAITING_FOR_OPPONENT
                )
                self._advance(next_phase, sub_game, steps)
            for phase in (
                GamePhase.AGREEING_RESULT,
                GamePhase.FINALIZING_ARTIFACTS,
                GamePhase.QUEUEING_REPORT,
                GamePhase.SHUTTING_DOWN,
                GamePhase.COMPLETED,
            ):
                self._advance(phase, sub_games, steps)
        except RefusalError:
            self._terminal(GamePhase.REFUSED, TransitionReason.REFUSAL)
        except IntegrityError:
            self._terminal(GamePhase.TAMPER, TransitionReason.INTEGRITY)
        except Exception:
            self._terminal(GamePhase.TECHNICAL_LOSS, TransitionReason.FAILURE)
        return OrchestrationResult(
            self._machine.snapshot().phase,
            completed,
            steps,
            tuple(self._heartbeats),
        )

    def _advance(self, target: GamePhase, sub_game: int, step: int) -> None:
        current = self._machine.snapshot().phase
        self._machine.transition(current, target)
        if target is not GamePhase.COMPLETED:
            self._workflow.execute(
                target,
                sub_game,
                step,
                self._deadlines.tracker(_OPERATION[target], self._clock),
                self._cancel,
            )
        self._progress += 1
        self._heartbeats.append(Heartbeat(target, step, self._clock.monotonic(), self._progress))

    def _terminal(self, target: GamePhase, reason: TransitionReason) -> None:
        current = self._machine.snapshot().phase
        if current is not target:
            self._machine.transition(current, target, reason)
