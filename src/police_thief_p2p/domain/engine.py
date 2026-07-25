"""Single deterministic own-state transition API."""

from dataclasses import dataclass, replace
from typing import cast

from police_thief_p2p.domain.events import BarrierPlaced
from police_thief_p2p.domain.state import LocalGameState
from police_thief_p2p.domain.terminal import maximum_step_reached, survival_reached
from police_thief_p2p.domain.values import (
    Action,
    ActionType,
    Direction,
    Position,
    Role,
    TerminalReason,
)


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """Immutable next local state and exact public event sequence."""

    state: LocalGameState
    public_events: tuple[BarrierPlaced, ...] = ()


def transition(state: LocalGameState, action: Action) -> TransitionResult:
    """Apply one legal own action with exactly-once immutable effects."""
    if state.terminal_reason is not None:
        raise ValueError("terminal state cannot transition")
    if action not in state.legal_actions():
        raise ValueError("action is not legal in the current local state")

    position = state.position
    barriers = state.public_barriers
    barriers_placed = state.barriers_placed
    next_step = state.step_number + 1
    events: tuple[BarrierPlaced, ...] = ()

    if action.action_type is ActionType.MOVE:
        position = state.rules.board.move(
            position,
            cast(Direction, action.direction),
            barriers,
        )
    elif action.action_type is ActionType.BARRIER:
        target = cast(Position, action.target)
        barriers = barriers.add(target)
        barriers_placed += 1
        events = (BarrierPlaced(Role.POLICE, next_step, target),)

    terminal_reason: TerminalReason | None = None
    if survival_reached(next_step, state.rules.survival_threshold):
        terminal_reason = TerminalReason.SURVIVAL
    elif maximum_step_reached(next_step, state.rules.max_steps):
        terminal_reason = TerminalReason.STEP_CEILING

    next_state = replace(
        state,
        position=position,
        public_barriers=barriers,
        barriers_placed=barriers_placed,
        step_number=next_step,
        visited=state.visited | {position},
        terminal_reason=terminal_reason,
    )
    return TransitionResult(next_state, events)
