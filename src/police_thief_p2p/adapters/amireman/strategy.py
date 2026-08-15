"""Pursuit/evasion brain for the amireman compatibility peer.

Police closes the wider axis toward the last-seen cell, paths around walls,
and does not drop random spawn walls.

Thief camps the south-east corner in the first two even games and the
south-west corner in game 6, so a cop that learned (6, 6) does not find
the same sit twice.
"""

from __future__ import annotations

import random
from collections import deque
from typing import Any

Cell = tuple[int, int]
_DELTAS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}


def legal_moves(pos: Cell, barriers: set[Cell], size: int) -> list[str]:
    """Return N/S/E/W/STAY tokens that stay in-bounds and off barriers."""
    moves = ["STAY"]
    for token, (dr, dc) in _DELTAS.items():
        cell = (pos[0] + dr, pos[1] + dc)
        if _passable(cell, barriers, size):
            moves.append(token)
    return moves


def apply_move(pos: Cell, move: str) -> Cell:
    """Apply one orthogonal move or STAY."""
    if move == "STAY":
        return pos
    dr, dc = _DELTAS[move]
    return (pos[0] + dr, pos[1] + dc)


def choose_move(
    *,
    role: str,
    pos: Cell,
    barriers: set[Cell],
    size: int,
    scent: dict[Cell, float],
    known_opp: Cell | None,
    rng: random.Random,
    barriers_used: int,
    barriers_max: int,
    last_target: Cell | None = None,
    step: int = 0,
    max_steps: int = 35,
    opp_start: Cell | None = None,
    sub_game: int = 1,
) -> tuple[str, list[int] | None]:
    """Return (move_token, barrier_placed_or_None). Barrier turns use STAY."""
    if role == "thief":
        return (
            _choose_thief(
                pos=pos,
                barriers=barriers,
                size=size,
                known_opp=known_opp,
                last_target=last_target,
                opp_start=opp_start,
                sub_game=sub_game,
            ),
            None,
        )
    target = _belief(known_opp, scent, opp_start, size)
    return _choose_police(
        pos=pos,
        barriers=barriers,
        size=size,
        belief=target,
        last_target=last_target,
        barriers_used=barriers_used,
        barriers_max=barriers_max,
        step=step,
        max_steps=max_steps,
    )


def _thief_camp(sub_game: int, size: int) -> Cell:
    """(6,6) for games 2 and 4; (6,0) for game 6."""
    last = size - 1
    if int(sub_game) >= 6:
        return (last, 0)
    return (last, last)


def _choose_thief(
    *,
    pos: Cell,
    barriers: set[Cell],
    size: int,
    known_opp: Cell | None,
    last_target: Cell | None,
    opp_start: Cell | None,
    sub_game: int,
) -> str:
    """Walk to this sub-game's camp and sit. Do not wander off it."""
    moves = legal_moves(pos, barriers, size)
    threat = known_opp or last_target or opp_start or (0, 0)
    camp = _thief_camp(sub_game, size)
    if camp in barriers:
        camp = (size - 1, size - 1)

    def score(move: str) -> tuple[int, ...]:
        nxt = apply_move(pos, move)
        return (-_manhattan(nxt, camp), _manhattan(nxt, threat), int(move == "STAY"))

    return max(moves, key=score)


def _choose_police(
    *,
    pos: Cell,
    barriers: set[Cell],
    size: int,
    belief: Cell,
    last_target: Cell | None,
    barriers_used: int,
    barriers_max: int,
    step: int,
    max_steps: int,
) -> tuple[str, list[int] | None]:
    intercept = _intercept(belief, pos, last_target, barriers, size)
    moves = legal_moves(pos, barriers, size)
    best_score: tuple[int, ...] | None = None
    best: tuple[str, list[int] | None] = ("STAY", None)

    def consider(score: tuple[int, ...], move: str, barrier: list[int] | None) -> None:
        nonlocal best_score, best
        if best_score is None or score > best_score:
            best_score = score
            best = (move, barrier)

    for move in moves:
        newpos = apply_move(pos, move)
        consider(
            _police_move_score(newpos, move, belief, intercept, barriers, size),
            move,
            None,
        )

    remaining = max_steps - step
    dist_now = _bfs_length(pos, intercept, barriers, size)
    chase_ok = dist_now is not None
    late = dist_now is not None and remaining <= dist_now
    if barriers_used < barriers_max and chase_ok and not late and dist_now > 1:
        occupy_possible = any(
            apply_move(pos, move) in {belief, intercept} for move in moves
        )
        for cell in _legal_barrier_targets(pos, barriers, size):
            if occupy_possible and cell in {belief, intercept}:
                continue
            score = _police_barrier_score(
                pos=pos,
                cell=cell,
                belief=belief,
                intercept=intercept,
                barriers=barriers,
                size=size,
            )
            if score is None:
                continue
            consider(score, "STAY", [cell[0], cell[1]])
    return best


def _police_move_score(
    newpos: Cell,
    move: str,
    belief: Cell,
    intercept: Cell,
    barriers: set[Cell],
    size: int,
) -> tuple[int, ...]:
    captured = int(newpos in (belief, intercept))
    dist = _bfs_length(newpos, intercept, barriers, size)
    if dist is None:
        dist = size * size
    return (
        captured,
        0,
        0,
        0,
        0,
        -dist,
        -max(abs(newpos[0] - intercept[0]), abs(newpos[1] - intercept[1])),
        0 if move == "STAY" else 1,
        _degree(newpos, barriers, size),
        -_manhattan(newpos, intercept),
        -newpos[0],
        -newpos[1],
    )


def _police_barrier_score(
    *,
    pos: Cell,
    cell: Cell,
    belief: Cell,
    intercept: Cell,
    barriers: set[Cell],
    size: int,
) -> tuple[int, ...] | None:
    capture = int(cell == belief)
    new_barriers = set(barriers)
    new_barriers.add(cell)
    if not capture and _bfs_length(pos, intercept, new_barriers, size) is None:
        return None
    if not capture and _reachable_count(pos, new_barriers, size) < 6:
        return None
    old_region = _reachable_count(belief, barriers, size)
    new_region = 0 if capture else _reachable_count(belief, new_barriers, size)
    gain = old_region - new_region
    old_deg = _degree(belief, barriers, size)
    new_deg = 0 if capture else _degree(belief, new_barriers, size)
    enclosed = int(not capture and new_deg == 0)
    dist = _bfs_length(pos, intercept, new_barriers, size)
    if dist is None:
        dist = size * size
    next_chase = _path_next(pos, intercept, barriers, size)
    blocks_path = int(cell == next_chase)
    if not capture and (blocks_path or dist > 4 or (gain < 2 and old_deg - new_deg < 1)):
        return None
    return (
        0,
        capture,
        enclosed,
        gain,
        old_deg - new_deg,
        -(dist + 1),
        -max(abs(pos[0] - intercept[0]), abs(pos[1] - intercept[1])),
        0,
        0,
        -_manhattan(pos, intercept),
        -cell[0],
        -cell[1],
    )


def _belief(
    known: Cell | None,
    scent: dict[Cell, float],
    opp_start: Cell | None,
    size: int,
) -> Cell:
    peak = known or _peak(scent) or opp_start or (size // 2, size // 2)
    if not scent:
        return peak
    top = max(scent.values())
    strong = [cell for cell, value in scent.items() if value >= 0.55 * top]
    if len(strong) >= 2:
        row = round(sum(cell[0] for cell in strong) / len(strong))
        col = round(sum(cell[1] for cell in strong) / len(strong))
        centroid = (row, col)
        if _in_bounds(centroid, size) and _manhattan(centroid, peak) <= 2:
            return centroid
    return peak


def _intercept(
    belief: Cell,
    _cop: Cell,
    last: Cell | None,
    barriers: set[Cell],
    size: int,
) -> Cell:
    if last is not None and last != belief:
        predicted = (belief[0] + (belief[0] - last[0]), belief[1] + (belief[1] - last[1]))
        if _passable(predicted, barriers, size):
            return predicted
    return belief


def _legal_barrier_targets(pos: Cell, barriers: set[Cell], size: int) -> list[Cell]:
    cells: list[Cell] = []
    for dr, dc in _DELTAS.values():
        cell = (pos[0] + dr, pos[1] + dc)
        if _in_bounds(cell, size) and cell not in barriers:
            cells.append(cell)
    return cells


def _peak(scent: dict[Cell, float]) -> Cell | None:
    if not scent:
        return None
    return max(scent.items(), key=lambda item: (item[1], -item[0][0], -item[0][1]))[0]


def _manhattan(left: Cell, right: Cell) -> int:
    return abs(left[0] - right[0]) + abs(left[1] - right[1])


def _in_bounds(cell: Cell, size: int) -> bool:
    return 0 <= cell[0] < size and 0 <= cell[1] < size


def _passable(cell: Cell, barriers: set[Cell], size: int) -> bool:
    return _in_bounds(cell, size) and cell not in barriers


def _adjacent_cells(pos: Cell, barriers: set[Cell], size: int) -> list[Cell]:
    cells: list[Cell] = []
    for dr, dc in _DELTAS.values():
        cell = (pos[0] + dr, pos[1] + dc)
        if _passable(cell, barriers, size):
            cells.append(cell)
    return cells


def _degree(pos: Cell, barriers: set[Cell], size: int) -> int:
    return len(_adjacent_cells(pos, barriers, size))


def _bfs_parents(start: Cell, barriers: set[Cell], size: int) -> dict[Cell, Cell | None]:
    if not _passable(start, barriers, size):
        return {}
    parents: dict[Cell, Cell | None] = {start: None}
    pending: deque[Cell] = deque([start])
    while pending:
        current = pending.popleft()
        for dr, dc in _DELTAS.values():
            nxt = (current[0] + dr, current[1] + dc)
            if nxt in parents or not _passable(nxt, barriers, size):
                continue
            parents[nxt] = current
            pending.append(nxt)
    return parents


def _bfs_length(start: Cell, goal: Cell, barriers: set[Cell], size: int) -> int | None:
    if start == goal:
        return 0
    parents = _bfs_parents(start, barriers, size)
    if goal not in parents:
        return None
    length = 0
    cell: Cell | None = goal
    while cell is not None and cell != start:
        cell = parents[cell]
        length += 1
    return length


def _path_next(start: Cell, goal: Cell, barriers: set[Cell], size: int) -> Cell | None:
    if start == goal:
        return start
    parents = _bfs_parents(start, barriers, size)
    if goal not in parents:
        return None
    cell = goal
    while parents[cell] is not None and parents[cell] != start:
        cell = parents[cell]
    return cell


def _reachable_count(start: Cell, barriers: set[Cell], size: int) -> int:
    if not _passable(start, barriers, size):
        return 0
    return len(_bfs_parents(start, barriers, size))


def build_payload(
    step: int,
    role: str,
    state: str,
    move: str,
    hint: str,
    *,
    barrier: list | None = None,
    capture_claim: list | None = None,
    claim_response: dict | None = None,
    sub_game: int | None = None,
) -> dict[str, Any]:
    """Sealed audit payload matching amireman field conventions."""
    payload: dict[str, Any] = {
        "step": step,
        "role": role,
        "state": state,
        "move": move if move == "STAY" or move.startswith("MOVE:") else f"MOVE:{move}",
        "intent": "truth",
        "hint": hint,
    }
    if sub_game is not None:
        payload["sub_game"] = int(sub_game)
        payload["sub_game_number"] = int(sub_game)
    if barrier is not None:
        payload["barrier_placed"] = list(barrier)
    if capture_claim is not None:
        payload["capture_claim"] = list(capture_claim)
    if claim_response is not None:
        payload["claim_response"] = dict(claim_response)
    return payload
