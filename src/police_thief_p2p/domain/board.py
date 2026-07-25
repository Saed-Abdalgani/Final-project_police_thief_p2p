"""Square board geometry, immutable barriers, and movement legality."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Final

from police_thief_p2p.domain.values import Action, Direction, Position

_DELTAS: Final = {
    Direction.NORTH: (-1, 0),
    Direction.SOUTH: (1, 0),
    Direction.EAST: (0, 1),
    Direction.WEST: (0, -1),
}


@dataclass(frozen=True, slots=True)
class BarrierSet:
    """Persistent public barrier collection with no removal operation."""

    cells: frozenset[Position] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        """Require an immutable collection containing only positions."""
        if not isinstance(self.cells, frozenset) or any(
            not isinstance(position, Position) for position in self.cells
        ):
            raise TypeError("barrier cells must be a frozenset of Position")

    def __contains__(self, position: Position) -> bool:
        """Return whether a cell is permanently blocked."""
        return position in self.cells

    def __len__(self) -> int:
        """Return the number of unique public barriers."""
        return len(self.cells)

    def add(self, position: Position) -> "BarrierSet":
        """Return a set containing the target; duplicate insertion is idempotent."""
        if position in self.cells:
            return self
        return BarrierSet(self.cells | {position})


EMPTY_BARRIERS: Final = BarrierSet()


@dataclass(frozen=True, slots=True)
class Board:
    """Square board with deterministic row-major and cardinal ordering."""

    size: int

    def __post_init__(self) -> None:
        """Reject booleans and non-positive board sizes."""
        if isinstance(self.size, bool) or not isinstance(self.size, int):
            raise TypeError("board size must be an integer")
        if self.size < 1:
            raise ValueError("board size must be positive")

    def contains(self, position: Position) -> bool:
        """Return whether a position lies on this board."""
        return 0 <= position.row < self.size and 0 <= position.col < self.size

    def cells(self) -> Iterator[Position]:
        """Iterate every board cell in stable row-major order."""
        for row in range(self.size):
            for col in range(self.size):
                yield Position(row, col)

    def target(self, origin: Position, direction: Direction) -> Position:
        """Return a direction's target without asserting its legality."""
        row_delta, col_delta = _DELTAS[direction]
        return Position(origin.row + row_delta, origin.col + col_delta)

    def move(
        self,
        origin: Position,
        direction: Direction,
        barriers: BarrierSet = EMPTY_BARRIERS,
    ) -> Position:
        """Apply one legal orthogonal movement or raise safely."""
        if not self.contains(origin):
            raise ValueError("origin is outside the board")
        target = self.target(origin, direction)
        if not self.contains(target):
            raise ValueError("move leaves the board")
        if target in barriers:
            raise ValueError("move enters a public barrier")
        return target

    def neighbors(
        self,
        position: Position,
        barriers: BarrierSet = EMPTY_BARRIERS,
    ) -> tuple[Position, ...]:
        """Return passable orthogonal neighbors in N, S, E, W order."""
        if not self.contains(position):
            raise ValueError("position is outside the board")
        candidates = (self.target(position, direction) for direction in Direction)
        return tuple(
            candidate
            for candidate in candidates
            if self.contains(candidate) and candidate not in barriers
        )

    def legal_movement_actions(
        self,
        position: Position,
        barriers: BarrierSet = EMPTY_BARRIERS,
    ) -> tuple[Action, ...]:
        """Return every legal orthogonal movement followed by STAY."""
        if not self.contains(position):
            raise ValueError("position is outside the board")
        actions = tuple(
            Action.move(direction)
            for direction in Direction
            if self.contains(self.target(position, direction))
            and self.target(position, direction) not in barriers
        )
        return (*actions, Action.stay())

    def action_between(
        self,
        origin: Position,
        target: Position,
        barriers: BarrierSet = EMPTY_BARRIERS,
    ) -> Action:
        """Convert two cells to one legal MOVE/STAY, rejecting jumps and diagonals."""
        if origin == target:
            if not self.contains(origin):
                raise ValueError("position is outside the board")
            return Action.stay()
        delta = (target.row - origin.row, target.col - origin.col)
        direction = next((item for item, offset in _DELTAS.items() if offset == delta), None)
        if direction is None:
            raise ValueError("movement must be exactly one orthogonal cell")
        self.move(origin, direction, barriers)
        return Action.move(direction)

    def barrier_candidates(
        self,
        police_position: Position,
        barriers: BarrierSet = EMPTY_BARRIERS,
    ) -> tuple[Position, ...]:
        """Return current then adjacent unblocked legal barrier targets."""
        if not self.contains(police_position):
            raise ValueError("police position is outside the board")
        candidates = (police_position, *self.neighbors(police_position))
        return tuple(position for position in candidates if position not in barriers)
