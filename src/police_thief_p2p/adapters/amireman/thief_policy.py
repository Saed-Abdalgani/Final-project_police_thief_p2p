"""Thief policy vs ahk-yosi police: hold a 3-cell buffer and stay interior.

Their cop intercepts a straight scent trail and squeezes corners. Dist 2 is
their kill-shot radius; a repeated heading is the velocity they lead onto.
When they bar their own cell, pathing must still treat that cell as the cop.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable

from police_thief_p2p.adapters.amireman.strategy_grid import (
    apply_move,
    legal_moves,
)
from police_thief_p2p.adapters.amireman.strategy_grid import (
    degree as _degree,
)
from police_thief_p2p.adapters.amireman.strategy_grid import (
    manhattan as _manhattan,
)
from police_thief_p2p.adapters.amireman.strategy_grid import (
    passable as _passable,
)
from police_thief_p2p.adapters.amireman.strategy_grid import (
    peak as _peak,
)

Cell = tuple[int, int]


def choose_thief(
    *,
    pos: Cell,
    barriers: set[Cell],
    size: int,
    scent: dict[Cell, float],
    known_opp: Cell | None,
    last_target: Cell | None,
    opp_start: Cell | None,
    last_move: str | None = None,
    step: int = 0,
    barriers_used: int = 0,
    barriers_max: int = 14,
    sub_game: int = 1,
) -> str:
    """Pick one legal thief token. Never returns a barrier."""
    del step, sub_game
    cop = known_opp or _peak(scent) or last_target or opp_start or (0, 0)
    projected = _lead(cop, last_target, barriers, size)
    cop_map = _dists(cop, barriers, size)
    lead_map = _dists(projected, barriers, size)
    options = [(move, apply_move(pos, move)) for move in legal_moves(pos, barriers, size)]
    pool = _prefer(options, lambda item: item[1] != cop)
    pool = _prefer(pool, lambda item: _manhattan(item[1], cop) >= 2)
    pool = _prefer(pool, lambda item: cop_map.get(item[1], 0) >= 2)
    pool = _prefer(pool, lambda item: _edges(item[1], size) < 2)
    pool = _prefer(pool, lambda item: _edges(item[1], size) == 0)
    pool = _prefer(pool, lambda item: item[1] != projected)
    pool = _prefer(pool, lambda item: lead_map.get(item[1], 0) >= 2)
    pool = _prefer(pool, lambda item: item[0] != last_move)
    pool = _prefer(pool, lambda item: item[0] != "STAY")
    center = (size // 2, size // 2)
    gap = cop_map.get(pos, 0)
    quota = max(0, barriers_max - barriers_used)

    def score(item: tuple[str, Cell]) -> tuple[int, ...]:
        move, nxt = item
        dist = cop_map.get(nxt, 0)
        owned = _owned(nxt, cop_map, barriers, size)
        return (
            _manhattan(nxt, cop) >= 2,
            dist >= 2,
            dist >= 3,
            int(dist >= gap) if gap >= 3 else 1,
            -_edges(nxt, size),
            min(dist, 4),
            owned,
            _degree(nxt, barriers, size),
            0 if move == last_move else 1,
            0 if move == "STAY" else 1,
            -_manhattan(nxt, center),
            -quota if _edges(nxt, size) else 0,
        )

    return max(pool or options, key=score)[0]


def _prefer(
    pool: list[tuple[str, Cell]], keep: Callable[[tuple[str, Cell]], bool]
) -> list[tuple[str, Cell]]:
    kept = [item for item in pool if keep(item)]
    return kept or pool


def _dists(start: Cell, barriers: set[Cell], size: int) -> dict[Cell, int]:
    """BFS distances from start, even if the cop is standing on a barred cell."""
    out: dict[Cell, int] = {start: 0}
    pending: deque[Cell] = deque([start])
    while pending:
        current = pending.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, 1), (0, -1)):
            nxt = (current[0] + dr, current[1] + dc)
            if nxt in out or not (0 <= nxt[0] < size and 0 <= nxt[1] < size):
                continue
            if nxt in barriers:
                continue
            out[nxt] = out[current] + 1
            pending.append(nxt)
    return out


def _owned(pos: Cell, cop_map: dict[Cell, int], barriers: set[Cell], size: int) -> int:
    mine = _dists(pos, barriers, size)
    unreachable = size * size
    return sum(1 for cell, dist in mine.items() if dist < cop_map.get(cell, unreachable))


def _edges(cell: Cell, size: int) -> int:
    return int(cell[0] in (0, size - 1)) + int(cell[1] in (0, size - 1))


def _lead(cop: Cell, last: Cell | None, barriers: set[Cell], size: int) -> Cell:
    if last is None or last == cop:
        return cop
    heading = (cop[0] - last[0], cop[1] - last[1])
    if abs(heading[0]) + abs(heading[1]) != 1:
        return cop
    nxt = (cop[0] + heading[0], cop[1] + heading[1])
    return nxt if _passable(nxt, barriers, size) else cop
