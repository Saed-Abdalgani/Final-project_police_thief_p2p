"""Compatibility strategy board graph helpers."""

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


def legal_moves(pos: Cell, barriers: set[Cell], size: int) -> list[str]:
    """Return N/S/E/W/STAY tokens that stay in-bounds and off barriers."""
    moves = ["STAY"]
    for action, (row_delta, col_delta) in DELTAS.items():
        cell = (pos[0] + row_delta, pos[1] + col_delta)
        if passable(cell, barriers, size):
            moves.append(action)
    return moves


def apply_move(pos: Cell, action: str) -> Cell:
    """Apply one orthogonal move or STAY."""
    if action == "STAY":
        return pos
    row_delta, col_delta = DELTAS[action]
    return (pos[0] + row_delta, pos[1] + col_delta)


def peak(scent: dict[Cell, float]) -> Cell | None:
    """Return a deterministic maximum-scent cell."""
    if not scent:
        return None
    return max(scent.items(), key=lambda item: (item[1], -item[0][0], -item[0][1]))[0]


def manhattan(left: Cell, right: Cell) -> int:
    """Return Manhattan distance between cells."""
    return abs(left[0] - right[0]) + abs(left[1] - right[1])


def in_bounds(cell: Cell, size: int) -> bool:
    """Return whether a cell is on the board."""
    return 0 <= cell[0] < size and 0 <= cell[1] < size


def passable(cell: Cell, barriers: set[Cell], size: int) -> bool:
    """Return whether a cell is on-board and not barred."""
    return in_bounds(cell, size) and cell not in barriers


def adjacent_cells(pos: Cell, barriers: set[Cell], size: int) -> list[Cell]:
    """Return passable orthogonal cells."""
    cells: list[Cell] = []
    for row_delta, col_delta in DELTAS.values():
        cell = (pos[0] + row_delta, pos[1] + col_delta)
        if passable(cell, barriers, size):
            cells.append(cell)
    return cells


def degree(pos: Cell, barriers: set[Cell], size: int) -> int:
    """Return passable orthogonal degree."""
    return len(adjacent_cells(pos, barriers, size))


def bfs_parents(start: Cell, barriers: set[Cell], size: int) -> dict[Cell, Cell | None]:
    """Return deterministic BFS parents for one component."""
    if not passable(start, barriers, size):
        return {}
    parents: dict[Cell, Cell | None] = {start: None}
    pending: deque[Cell] = deque([start])
    while pending:
        current = pending.popleft()
        for row_delta, col_delta in DELTAS.values():
            nxt = (current[0] + row_delta, current[1] + col_delta)
            if nxt not in parents and passable(nxt, barriers, size):
                parents[nxt] = current
                pending.append(nxt)
    return parents


def bfs_length(start: Cell, goal: Cell, barriers: set[Cell], size: int) -> int | None:
    """Return shortest path length or None when disconnected."""
    if start == goal:
        return 0
    parents = bfs_parents(start, barriers, size)
    if goal not in parents:
        return None
    length, current = 0, goal
    while current != start:
        parent = parents[current]
        if parent is None:
            return None
        current, length = parent, length + 1
    return length


def path_next(start: Cell, goal: Cell, barriers: set[Cell], size: int) -> Cell | None:
    """Return the next cell on a deterministic shortest path."""
    if start == goal:
        return start
    parents = bfs_parents(start, barriers, size)
    if goal not in parents:
        return None
    current = goal
    while parents[current] is not None and parents[current] != start:
        current = parents[current]  # type: ignore[assignment]
    return current


def reachable_count(start: Cell, barriers: set[Cell], size: int) -> int:
    """Return connected component size."""
    return len(bfs_parents(start, barriers, size)) if passable(start, barriers, size) else 0
