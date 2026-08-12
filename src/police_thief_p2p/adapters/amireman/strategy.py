"""Simple legal-move brain for the amireman compatibility peer."""

from __future__ import annotations

import random
from typing import Any

_DELTAS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}


def legal_moves(pos: tuple[int, int], barriers: set[tuple[int, int]], size: int) -> list[str]:
    """Return N/S/E/W/STAY tokens that stay in-bounds and off barriers."""
    moves = ["STAY"]
    for token, (dr, dc) in _DELTAS.items():
        cell = (pos[0] + dr, pos[1] + dc)
        if 0 <= cell[0] < size and 0 <= cell[1] < size and cell not in barriers:
            moves.append(token)
    return moves


def apply_move(pos: tuple[int, int], move: str) -> tuple[int, int]:
    """Apply one orthogonal move or STAY."""
    if move == "STAY":
        return pos
    dr, dc = _DELTAS[move]
    return (pos[0] + dr, pos[1] + dc)


def choose_move(
    *,
    role: str,
    pos: tuple[int, int],
    barriers: set[tuple[int, int]],
    size: int,
    scent: dict[tuple[int, int], float],
    known_opp: tuple[int, int] | None,
    rng: random.Random,
    barriers_used: int,
    barriers_max: int,
) -> tuple[str, list[int] | None]:
    """Return (move_token, barrier_placed_or_None). Barrier turns use STAY."""
    moves = legal_moves(pos, barriers, size)
    if role == "thief":
        if known_opp is None:
            return rng.choice(moves), None
        best = max(moves, key=lambda m: _manhattan(apply_move(pos, m), known_opp))
        return best, None
    # police: chase scent peak or known cell; occasionally place a barrier
    target = known_opp or _peak(scent) or (size // 2, size // 2)
    if barriers_used < barriers_max and rng.random() < 0.08:
        cell = _barrier_candidate(pos, barriers, size, rng)
        if cell is not None:
            return "STAY", [cell[0], cell[1]]
    best = min(moves, key=lambda m: _manhattan(apply_move(pos, m), target))
    return best, None


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _peak(scent: dict[tuple[int, int], float]) -> tuple[int, int] | None:
    if not scent:
        return None
    return max(scent.items(), key=lambda item: item[1])[0]


def _barrier_candidate(
    pos: tuple[int, int], barriers: set[tuple[int, int]], size: int, rng: random.Random
) -> tuple[int, int] | None:
    options = []
    for dr, dc in _DELTAS.values():
        cell = (pos[0] + dr, pos[1] + dc)
        if 0 <= cell[0] < size and 0 <= cell[1] < size and cell not in barriers and cell != pos:
            options.append(cell)
    return rng.choice(options) if options else None


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
    if barrier is not None:
        payload["barrier_placed"] = list(barrier)
    if capture_claim is not None:
        payload["capture_claim"] = list(capture_claim)
    if claim_response is not None:
        payload["claim_response"] = dict(claim_response)
    return payload
