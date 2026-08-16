"""Grid primitives shared by the compatibility recovery arena."""

from __future__ import annotations

from collections import deque
from typing import Final

Cell = tuple[int, int]
DELTAS: Final[dict[str, Cell]] = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}


def legal_action(
    position: Cell,
    move: str,
    barrier: Cell | None,
    barriers: set[Cell],
    size: int,
    role: str,
) -> bool:
    """Return whether one proposed move or barrier is legal."""
    if barrier is not None:
        return (
            role == "police" and barrier in neighbors(position, barriers, size) and move == "STAY"
        )
    return move in legal_moves(position, barriers, size)


def legal_moves(position: Cell, barriers: set[Cell], size: int) -> list[str]:
    """Return in-bounds orthogonal moves plus STAY."""
    moves = ["STAY"]
    for token, delta in DELTAS.items():
        cell = (position[0] + delta[0], position[1] + delta[1])
        if passable(cell, barriers, size):
            moves.append(token)
    return moves


def move(position: Cell, action: str) -> Cell:
    """Apply one legal move token."""
    if action == "STAY":
        return position
    delta = DELTAS[action]
    return (position[0] + delta[0], position[1] + delta[1])


def neighbors(position: Cell, barriers: set[Cell], size: int) -> list[Cell]:
    """Return passable orthogonal neighboring cells."""
    return [
        move(position, action)
        for action in legal_moves(position, barriers, size)
        if action != "STAY"
    ]


def passable(cell: Cell, barriers: set[Cell], size: int) -> bool:
    """Return whether a cell is on-board and not a barrier."""
    return 0 <= cell[0] < size and 0 <= cell[1] < size and cell not in barriers


def distance(start: Cell, goal: Cell, barriers: set[Cell], size: int) -> int:
    """Return graph distance, or a stable far sentinel if disconnected."""
    if start == goal:
        return 0
    seen = {start}
    pending: deque[tuple[Cell, int]] = deque([(start, 0)])
    while pending:
        current, length = pending.popleft()
        for nxt in neighbors(current, barriers, size):
            if nxt == goal:
                return length + 1
            if nxt not in seen:
                seen.add(nxt)
                pending.append((nxt, length + 1))
    return size * size


def reachable(start: Cell, barriers: set[Cell], size: int) -> int:
    """Count the connected component reachable from one cell."""
    if not passable(start, barriers, size):
        return 0
    seen = {start}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for nxt in neighbors(current, barriers, size):
            if nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return len(seen)


def enclosed(thief: Cell, barriers: set[Cell], size: int) -> bool:
    """Return whether a Thief has no orthogonal escape."""
    return not neighbors(thief, barriers, size)


def other(role: str) -> str:
    """Return the opposing role token."""
    return "thief" if role == "police" else "police"


def cell(value: object) -> Cell:
    """Parse a two-component start cell."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("start cell must be a pair")
    return (int(value[0]), int(value[1]))
