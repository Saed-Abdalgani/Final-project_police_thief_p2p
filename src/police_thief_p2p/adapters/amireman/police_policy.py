"""Posterior-target pursuit and graph-cut barriers for compatibility Police."""

from __future__ import annotations

from police_thief_p2p.adapters.amireman.strategy_grid import (
    DELTAS,
    Cell,
    apply_move,
    bfs_length,
    degree,
    in_bounds,
    legal_moves,
    manhattan,
    passable,
    path_next,
    peak,
    reachable_count,
)


def choose_police(
    pos: Cell,
    barriers: set[Cell],
    size: int,
    scent: dict[Cell, float],
    known_opp: Cell | None,
    last_target: Cell | None,
    opp_start: Cell | None,
    barriers_used: int,
    barriers_max: int,
    step: int,
    max_steps: int,
) -> tuple[str, list[int] | None]:
    """Choose pursuit, posterior capture, or a useful graph cut."""
    target = belief(known_opp, scent, opp_start, size)
    intercept = _intercept(target, last_target, barriers, size)
    moves = legal_moves(pos, barriers, size)
    choices: list[tuple[tuple[int, ...], str, list[int] | None]] = [
        (
            _move_score(apply_move(pos, action), action, target, intercept, barriers, size),
            action,
            None,
        )
        for action in moves
    ]
    remaining = max_steps - step
    distance = bfs_length(pos, intercept, barriers, size)
    if (
        barriers_used < barriers_max
        and distance is not None
        and remaining > distance
        and distance > 1
    ):
        occupy = any(apply_move(pos, action) in {target, intercept} for action in moves)
        for cell in _barrier_targets(pos, barriers, size):
            if occupy and cell in {target, intercept}:
                continue
            score = _barrier_score(pos, cell, target, intercept, barriers, size)
            if score is not None:
                choices.append((score, "STAY", [cell[0], cell[1]]))
    _, action, barrier = max(choices, key=lambda item: item[0])
    return action, barrier


def belief(known: Cell | None, scent: dict[Cell, float], start: Cell | None, size: int) -> Cell:
    """Return a robust centroid/peak target from public evidence."""
    target = known or peak(scent) or start or (size // 2, size // 2)
    if not scent:
        return target
    top = max(scent.values())
    strong = [cell for cell, value in scent.items() if value >= 0.55 * top]
    if len(strong) >= 2:
        centroid = (
            round(sum(cell[0] for cell in strong) / len(strong)),
            round(sum(cell[1] for cell in strong) / len(strong)),
        )
        if in_bounds(centroid, size) and manhattan(centroid, target) <= 2:
            return centroid
    return target


def _intercept(target: Cell, last: Cell | None, barriers: set[Cell], size: int) -> Cell:
    if last is not None and last != target:
        predicted = (target[0] * 2 - last[0], target[1] * 2 - last[1])
        if passable(predicted, barriers, size):
            return predicted
    return target


def _move_score(
    newpos: Cell, action: str, target: Cell, intercept: Cell, barriers: set[Cell], size: int
) -> tuple[int, ...]:
    distance = bfs_length(newpos, intercept, barriers, size)
    distance = size * size if distance is None else distance
    return (
        int(newpos in (target, intercept)),
        0,
        0,
        0,
        0,
        -distance,
        -max(abs(newpos[0] - intercept[0]), abs(newpos[1] - intercept[1])),
        int(action != "STAY"),
        degree(newpos, barriers, size),
        -manhattan(newpos, intercept),
        -newpos[0],
        -newpos[1],
    )


def _barrier_score(
    pos: Cell, cell: Cell, target: Cell, intercept: Cell, barriers: set[Cell], size: int
) -> tuple[int, ...] | None:
    capture = int(cell == target)
    updated = barriers | {cell}
    if not capture and (
        bfs_length(pos, intercept, updated, size) is None or reachable_count(pos, updated, size) < 6
    ):
        return None
    old_region, new_region = (
        reachable_count(target, barriers, size),
        0 if capture else reachable_count(target, updated, size),
    )
    old_degree, new_degree = (
        degree(target, barriers, size),
        0 if capture else degree(target, updated, size),
    )
    distance = bfs_length(pos, intercept, updated, size) or size * size
    blocks_path = int(cell == path_next(pos, intercept, barriers, size))
    gain = old_region - new_region
    if not capture and (blocks_path or distance > 4 or (gain < 2 and old_degree - new_degree < 1)):
        return None
    return (
        0,
        capture,
        int(not capture and new_degree == 0),
        gain,
        old_degree - new_degree,
        -(distance + 1),
        -max(abs(pos[0] - intercept[0]), abs(pos[1] - intercept[1])),
        0,
        0,
        -manhattan(pos, intercept),
        -cell[0],
        -cell[1],
    )


def _barrier_targets(pos: Cell, barriers: set[Cell], size: int) -> list[Cell]:
    return [
        (pos[0] + row_delta, pos[1] + col_delta)
        for row_delta, col_delta in DELTAS.values()
        if in_bounds((pos[0] + row_delta, pos[1] + col_delta), size)
        and (pos[0] + row_delta, pos[1] + col_delta) not in barriers
    ]
