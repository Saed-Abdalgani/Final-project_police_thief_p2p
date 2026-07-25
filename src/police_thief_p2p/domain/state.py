"""Immutable local-only game state and validated initialization."""

from dataclasses import dataclass, field
from typing import Self

from police_thief_p2p.domain.board import BarrierSet, Board
from police_thief_p2p.domain.values import Action, Position, Role, TerminalReason
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.coordinates import CoordinateTransform


@dataclass(frozen=True, slots=True)
class GameRules:
    """Outcome-relevant physics limits derived from validated shared config."""

    board: Board
    max_barriers: int
    max_steps: int
    survival_threshold: int

    def __post_init__(self) -> None:
        """Reject booleans and non-positive domain limits."""
        if not isinstance(self.board, Board):
            raise TypeError("game board must be a Board")
        values = (self.max_barriers, self.max_steps, self.survival_threshold)
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise TypeError("game limits must be integers")
        if self.max_barriers < 0 or self.max_steps < 1 or self.survival_threshold < 1:
            raise ValueError("game limits must be non-negative/positive")

    @classmethod
    def from_shared(cls, config: SharedConfig) -> Self:
        """Create domain rules from the authoritative shared constitution."""
        movement = config.movement_and_barriers
        return cls(
            board=Board(config.board_and_agents.grid_size),
            max_barriers=movement.max_barriers,
            max_steps=movement.max_moves,
            survival_threshold=movement.survival_threshold,
        )


@dataclass(frozen=True, slots=True)
class LocalGameState:
    """One peer's truth plus public barriers; opponent truth is absent by design."""

    role: Role
    position: Position
    rules: GameRules
    public_barriers: BarrierSet = field(default_factory=BarrierSet)
    barriers_placed: int = 0
    step_number: int = 0
    visited: frozenset[Position] = field(default_factory=frozenset)
    terminal_reason: TerminalReason | None = None

    def __post_init__(self) -> None:
        """Enforce bounds, quota, local-truth, and terminal-safe invariants."""
        if not isinstance(self.role, Role):
            raise TypeError("local role must be a Role")
        if not isinstance(self.position, Position):
            raise TypeError("local position must be a Position")
        if not isinstance(self.rules, GameRules):
            raise TypeError("local rules must be GameRules")
        if not isinstance(self.public_barriers, BarrierSet):
            raise TypeError("public_barriers must be a BarrierSet")
        if type(self.barriers_placed) is not int or type(self.step_number) is not int:
            raise TypeError("state counters must be integers")
        if not isinstance(self.visited, frozenset) or any(
            not isinstance(cell, Position) for cell in self.visited
        ):
            raise TypeError("visited must be a frozenset of Position")
        if self.terminal_reason is not None and not isinstance(
            self.terminal_reason, TerminalReason
        ):
            raise TypeError("terminal_reason must be a TerminalReason")
        if not self.rules.board.contains(self.position):
            raise ValueError("local position is outside the board")
        if not 0 <= self.barriers_placed <= self.rules.max_barriers:
            raise ValueError("barriers_placed exceeds the configured quota")
        if self.step_number < 0:
            raise ValueError("step_number must be non-negative")
        if self.position in self.public_barriers and self.role is not Role.POLICE:
            raise ValueError("Thief cannot occupy a public barrier")
        if self.position not in self.visited:
            raise ValueError("visited cells must contain the current position")
        if any(not self.rules.board.contains(cell) for cell in self.visited):
            raise ValueError("visited cell is outside the board")
        if any(not self.rules.board.contains(cell) for cell in self.public_barriers.cells):
            raise ValueError("public barrier is outside the board")

    def legal_actions(self) -> tuple[Action, ...]:
        """Return deterministic legal own actions, empty after terminal state."""
        if self.terminal_reason is not None:
            return ()
        movement = self.rules.board.legal_movement_actions(self.position, self.public_barriers)
        if self.role is Role.THIEF or self.barriers_placed >= self.rules.max_barriers:
            return movement
        barrier_actions = tuple(
            Action.barrier(target)
            for target in self.rules.board.barrier_candidates(self.position, self.public_barriers)
        )
        return (*movement, *barrier_actions)


def initial_local_state(config: SharedConfig, role: Role) -> LocalGameState:
    """Create a zero-step local state at the negotiated role-specific start."""
    board_config = config.board_and_agents
    transform = CoordinateTransform(
        board_config.grid_size,
        board_config.axis_origin_corner,
        board_config.axis_start_index,
    )
    external_start = board_config.cop_start if role is Role.POLICE else board_config.thief_start
    start = transform.to_canonical(external_start)
    return LocalGameState(
        role=role,
        position=start,
        rules=GameRules.from_shared(config),
        visited=frozenset({start}),
    )
