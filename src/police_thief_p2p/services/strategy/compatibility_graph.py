"""Board graph operations for compatibility pursuit and evasion."""

from __future__ import annotations

from collections import deque
from typing import Any, Final

from police_thief_p2p.services.strategy.compatibility_scent import Cell

DELTAS: Final[dict[str, Cell]] = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}


class _GraphMixin:
    """Supply graph methods to the stateful compatibility session."""

    def _legal_moves(self: Any, cell: Cell) -> list[str]:
        moves = ["STAY"]
        for action, delta in DELTAS.items():
            candidate = (cell[0] + delta[0], cell[1] + delta[1])
            if self._passable(candidate):
                moves.append(action)
        return moves

    def _legal_cells(self: Any, cell: Cell) -> list[Cell]:
        return [move(cell, action) for action in self._legal_moves(cell)]

    def _successors(self: Any, cell: Cell) -> list[Cell]:
        return list(self._legal_cells(cell))

    def _neighbors(self: Any, cell: Cell) -> list[Cell]:
        return [candidate for candidate in self._legal_cells(cell) if candidate != cell]

    def _degree(self: Any, cell: Cell) -> int:
        return len(self._neighbors(cell))

    def _in_bounds(self: Any, cell: Cell) -> bool:
        return bool(0 <= cell[0] < self.size and 0 <= cell[1] < self.size)

    def _passable(self: Any, cell: Cell) -> bool:
        return self._in_bounds(cell) and cell not in self._barriers

    def _reachable(self: Any, start: Cell, barriers: set[Cell]) -> int:
        if start in barriers or not self._in_bounds(start):
            return 0
        seen = {start}
        pending = deque([start])
        while pending:
            current = pending.popleft()
            for delta in DELTAS.values():
                nxt = (current[0] + delta[0], current[1] + delta[1])
                if nxt not in seen and self._in_bounds(nxt) and nxt not in barriers:
                    seen.add(nxt)
                    pending.append(nxt)
        return len(seen)

    def _distance(self: Any, start: Cell, goal: Cell, barriers: set[Cell]) -> int | None:
        if start == goal:
            return 0
        seen = {start}
        pending: deque[tuple[Cell, int]] = deque([(start, 0)])
        while pending:
            current, length = pending.popleft()
            for delta in DELTAS.values():
                nxt = (current[0] + delta[0], current[1] + delta[1])
                if nxt == goal and nxt not in barriers:
                    return length + 1
                if nxt not in seen and self._in_bounds(nxt) and nxt not in barriers:
                    seen.add(nxt)
                    pending.append((nxt, length + 1))
        return None

    def _distance_or_far(self: Any, start: Cell, goal: Cell) -> int:
        distance = self._distance(start, goal, self._barriers)
        return int(self.size * self.size if distance is None else distance)

    def _boundary_penalty(self: Any, cell: Cell) -> int:
        return int(cell[0] in {0, self.size - 1}) + int(cell[1] in {0, self.size - 1})


def as_cell(value: Any) -> Cell:
    """Convert an indexable pair to an integer cell."""
    return (int(value[0]), int(value[1]))


def move(cell: Cell, action: str) -> Cell:
    """Apply one orthogonal action or STAY."""
    if action == "STAY":
        return cell
    delta = DELTAS[action]
    return (cell[0] + delta[0], cell[1] + delta[1])


def manhattan(left: Cell, right: Cell) -> int:
    """Return Manhattan distance between two cells."""
    return abs(left[0] - right[0]) + abs(left[1] - right[1])
