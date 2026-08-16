"""Exact compatibility scent physics used by particle hypotheses."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

Cell = tuple[int, int]
Grid = dict[Cell, float]
KERNEL: Final[dict[Cell, float]] = {
    (0, 0): 0.90,
    (0, 1): 0.62,
    (1, 0): 0.62,
    (1, 1): 0.42,
    (0, 2): 0.20,
    (2, 0): 0.20,
    (1, 2): 0.14,
    (2, 1): 0.14,
    (2, 2): 0.04,
}


def decay_value(value: float, rho: float, model: str) -> float:
    """Apply one model-specific decay tick to one value."""
    if model == "subtractive_chebyshev_v1":
        return value - rho
    return (1.0 - rho) * value


def kept(value: float) -> float | None:
    """Clip intensity and remove four-decimal dust."""
    clipped = min(0.9, max(0.0, value))
    return clipped if clipped > 0.0001 else None


def emission(centre: Cell, size: int, model: str) -> Grid:
    """Return a clipped 5-by-5 emission around one position."""
    result: Grid = {}
    for row_delta in range(-2, 3):
        for col_delta in range(-2, 3):
            cell = (centre[0] + row_delta, centre[1] + col_delta)
            if not (0 <= cell[0] < size and 0 <= cell[1] < size):
                continue
            if model == "subtractive_chebyshev_v1":
                value = {0: 0.9, 1: 0.6, 2: 0.3}[max(abs(row_delta), abs(col_delta))]
            else:
                value = KERNEL[(abs(row_delta), abs(col_delta))]
            result[cell] = value
    return result


def decay_only(grid: Mapping[Cell, float], rho: float, model: str) -> Grid:
    """Apply the pre-emission decay served on the compatibility wire."""
    result: Grid = {}
    for cell, value in grid.items():
        retained = kept(decay_value(value, rho, model))
        if retained is not None:
            result[cell] = retained
    return result


def step_update(
    grid: Mapping[Cell, float], centre: Cell, size: int, rho: float, model: str
) -> Grid:
    """Apply decay plus the new post-action emission."""
    delta = emission(centre, size, model)
    result: Grid = {}
    for cell in set(grid) | set(delta):
        old = decay_value(grid[cell], rho, model) if cell in grid else 0.0
        retained = kept(old + delta.get(cell, 0.0))
        if retained is not None:
            result[cell] = retained
    return result
