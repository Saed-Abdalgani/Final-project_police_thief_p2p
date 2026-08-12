"""Capture cases A/B/C for the amireman wire."""

from __future__ import annotations

Cell = tuple[int, int]
_DELTAS = ((-1, 0), (1, 0), (0, 1), (0, -1))


def claim_captures(claim: list | tuple | None, thief: Cell) -> bool:
    """Case A: capture_claim equals the Thief's true cell."""
    if claim is None:
        return False
    return (int(claim[0]), int(claim[1])) == thief


def barrier_captures(barrier: list | tuple | None, thief: Cell) -> bool:
    """Case B: barrier_placed equals the Thief's true cell."""
    if barrier is None:
        return False
    return (int(barrier[0]), int(barrier[1])) == thief


def thief_trapped(thief: Cell, barriers: set[Cell], size: int) -> bool:
    """Case C: no passable orthogonal neighbour after barriers applied."""
    if thief in barriers:
        return True
    for dr, dc in _DELTAS:
        cell = (thief[0] + dr, thief[1] + dc)
        if 0 <= cell[0] < size and 0 <= cell[1] < size and cell not in barriers:
            return False
    return True


def evaluate_thief_caught(
    *,
    thief: Cell,
    claim: list | tuple | None,
    barrier: list | tuple | None,
    barriers: set[Cell],
    size: int,
) -> bool:
    """Truthful Thief evaluation of Cop claim/barrier (A/B/C)."""
    if claim_captures(claim, thief):
        return True
    if barrier is None:
        return False
    return barrier_captures(barrier, thief) or thief_trapped(thief, barriers, size)
