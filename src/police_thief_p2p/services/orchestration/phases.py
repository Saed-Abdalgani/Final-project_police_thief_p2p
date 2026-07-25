"""Thread-safe formal orchestration phase machine."""

from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from threading import Lock


class GamePhase(StrEnum):
    """Every durable lifecycle phase from creation through terminal outcome."""

    CREATED = "created"
    INITIALIZING = "initializing"
    RECOVERING = "recovering"
    READY = "ready"
    NEGOTIATING = "negotiating"
    WAITING_FOR_OPPONENT = "waiting-for-opponent"
    UPDATING_BELIEF = "updating-belief"
    COMPUTING_STRATEGY = "computing-strategy"
    COMMITTING = "committing"
    WAITING_ACK = "waiting-ack"
    REVEALING = "revealing"
    VERIFYING = "verifying"
    CHECKPOINTING = "checkpointing"
    SUBGAME_TERMINAL = "subgame-terminal"
    AUDITING = "auditing"
    AGREEING_RESULT = "agreeing-result"
    FINALIZING_ARTIFACTS = "finalizing-artifacts"
    QUEUEING_REPORT = "queueing-report"
    SHUTTING_DOWN = "shutting-down"
    COMPLETED = "completed"
    REFUSED = "refused"
    TECHNICAL_LOSS = "technical-loss"
    TAMPER = "tamper"


class TransitionReason(StrEnum):
    """Reason classes that constrain allowed transition targets."""

    NORMAL = "normal"
    RECOVERY = "recovery"
    REFUSAL = "refusal"
    FAILURE = "failure"
    INTEGRITY = "integrity"


TERMINAL_PHASES = frozenset(
    {
        GamePhase.COMPLETED,
        GamePhase.REFUSED,
        GamePhase.TECHNICAL_LOSS,
        GamePhase.TAMPER,
    }
)

_NORMAL_CHAIN = (
    GamePhase.CREATED,
    GamePhase.INITIALIZING,
    GamePhase.READY,
    GamePhase.NEGOTIATING,
    GamePhase.WAITING_FOR_OPPONENT,
    GamePhase.UPDATING_BELIEF,
    GamePhase.COMPUTING_STRATEGY,
    GamePhase.COMMITTING,
    GamePhase.WAITING_ACK,
    GamePhase.REVEALING,
    GamePhase.VERIFYING,
    GamePhase.CHECKPOINTING,
)
TRANSITIONS: dict[GamePhase, dict[TransitionReason, frozenset[GamePhase]]] = {
    phase: {
        TransitionReason.NORMAL: frozenset({target}),
        TransitionReason.FAILURE: frozenset({GamePhase.TECHNICAL_LOSS}),
        TransitionReason.INTEGRITY: frozenset({GamePhase.TAMPER}),
    }
    for phase, target in pairwise(_NORMAL_CHAIN)
}
TRANSITIONS[GamePhase.CREATED][TransitionReason.RECOVERY] = frozenset({GamePhase.RECOVERING})
TRANSITIONS[GamePhase.RECOVERING] = {
    TransitionReason.RECOVERY: frozenset({GamePhase.WAITING_FOR_OPPONENT}),
    TransitionReason.FAILURE: frozenset({GamePhase.TECHNICAL_LOSS}),
    TransitionReason.INTEGRITY: frozenset({GamePhase.TAMPER}),
}
TRANSITIONS[GamePhase.NEGOTIATING][TransitionReason.REFUSAL] = frozenset({GamePhase.REFUSED})
TRANSITIONS[GamePhase.VERIFYING][TransitionReason.INTEGRITY] = frozenset({GamePhase.TAMPER})
TRANSITIONS[GamePhase.CHECKPOINTING] = {
    TransitionReason.NORMAL: frozenset(
        {GamePhase.WAITING_FOR_OPPONENT, GamePhase.SUBGAME_TERMINAL}
    ),
    TransitionReason.FAILURE: frozenset({GamePhase.TECHNICAL_LOSS}),
    TransitionReason.INTEGRITY: frozenset({GamePhase.TAMPER}),
}
TRANSITIONS[GamePhase.SUBGAME_TERMINAL] = {
    TransitionReason.NORMAL: frozenset({GamePhase.WAITING_FOR_OPPONENT, GamePhase.AUDITING}),
    TransitionReason.FAILURE: frozenset({GamePhase.TECHNICAL_LOSS}),
    TransitionReason.INTEGRITY: frozenset({GamePhase.TAMPER}),
}
for phase, target in (
    (GamePhase.AUDITING, GamePhase.AGREEING_RESULT),
    (GamePhase.AGREEING_RESULT, GamePhase.FINALIZING_ARTIFACTS),
    (GamePhase.FINALIZING_ARTIFACTS, GamePhase.QUEUEING_REPORT),
    (GamePhase.QUEUEING_REPORT, GamePhase.SHUTTING_DOWN),
    (GamePhase.SHUTTING_DOWN, GamePhase.COMPLETED),
):
    TRANSITIONS[phase] = {
        TransitionReason.NORMAL: frozenset({target}),
        TransitionReason.FAILURE: frozenset({GamePhase.TECHNICAL_LOSS}),
        TransitionReason.INTEGRITY: frozenset({GamePhase.TAMPER}),
    }
TRANSITIONS[GamePhase.AUDITING][TransitionReason.INTEGRITY] = frozenset({GamePhase.TAMPER})
for terminal in TERMINAL_PHASES:
    TRANSITIONS[terminal] = {}


@dataclass(frozen=True, slots=True)
class PhaseSnapshot:
    """One compare-and-set phase revision."""

    phase: GamePhase
    revision: int


class PhaseMachine:
    """Atomic compare-and-set transitions with immutable terminal phases."""

    __slots__ = ("_lock", "_phase", "_revision")

    def __init__(self, initial: GamePhase = GamePhase.CREATED) -> None:
        """Create a machine at one explicit durable phase."""
        self._phase = initial
        self._revision = 0
        self._lock = Lock()

    def snapshot(self) -> PhaseSnapshot:
        """Return an atomic immutable phase view."""
        with self._lock:
            return PhaseSnapshot(self._phase, self._revision)

    def transition(
        self,
        expected: GamePhase,
        target: GamePhase,
        reason: TransitionReason = TransitionReason.NORMAL,
    ) -> PhaseSnapshot:
        """Compare current phase then apply one reason-specific legal target."""
        with self._lock:
            if self._phase is not expected:
                raise RuntimeError("phase compare-and-set conflict")
            allowed = TRANSITIONS[self._phase].get(reason, frozenset())
            if target not in allowed:
                raise ValueError("phase transition is not allowed for this reason")
            self._phase = target
            self._revision += 1
            return PhaseSnapshot(self._phase, self._revision)
